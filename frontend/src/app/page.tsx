'use client';

import {
  ChangeEvent,
  DragEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import HomeView from '../components/HomeView';
import PricingModal from '../components/PricingModal';
import ProcessingPage from '../components/ProcessingPage';
import LoginModal from '../components/LoginModal';
import RegisterModal from '../components/RegisterModal';
import ForgotPasswordModal from '../components/ForgotPasswordModal';
import { ProcessingMethod } from '../lib/processing';
import {
  authenticate,
  clearPersistedSession,
  createAuthenticatedState,
  createAuthenticatingState,
  createLoggedOutState,
  fetchUserProfile,
  isAuthenticated,
  persistSession,
  restoreSession,
  toAccountSummary,
} from '../lib/auth';
import {
  ApiSuccessResponse,
  UserProfile,
  createProcessingTask,
  CreditBalanceResponse,
  getProcessingStatus,
  getCreditBalance,
  ProcessingRequestPayload,
  ProcessingStatusData,
  register,
  RegisterPayload,
  RegisterResult,
  sendPasswordResetCode,
  resetPasswordByPhone,
  ResetPasswordByPhonePayload,
} from '../lib/api';
import {
  clearAuthTokens,
  registerTokenUpdateHandler,
  setInitialAuthTokens,
  unregisterTokenUpdateHandler,
} from '../lib/tokenManager';

type PageState = 'home' | ProcessingMethod;

type ExpandEdgeKey = 'top' | 'bottom' | 'left' | 'right';

type ExpandEdgesState = Record<ExpandEdgeKey, string>;

const EXPAND_EDGE_MAX: Record<ExpandEdgeKey, number> = {
  top: 0.5,
  bottom: 0.5,
  left: 1,
  right: 1,
};

const AUTH_DEMO_CREDENTIALS = {
  identifier: '13800138000', // Demo phone number
  password: 'password123',
  rememberMe: true,
};

const POLLING_INTERVAL_MS = 3000;
const ACTIVE_TASK_STORAGE_KEY = 'loomai:active-processing-task';

type PersistedProcessingTaskEntry = {
  taskId: string;
  userId: string;
  createdAt: string;
};

type PersistedProcessingTaskMap = Partial<Record<ProcessingMethod, PersistedProcessingTaskEntry>>;

type MethodViewState = {
  processedImage: string | null;
  successMessage: string;
  errorMessage: string;
};

type MethodUiStateMap = Partial<Record<ProcessingMethod, MethodViewState>>;

const readPersistedProcessingTasks = (): PersistedProcessingTaskMap => {
  if (typeof window === 'undefined') {
    return {};
  }
  const raw = window.localStorage.getItem(ACTIVE_TASK_STORAGE_KEY);
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw) as PersistedProcessingTaskMap;
  } catch (error) {
    console.warn('无法解析缓存的任务状态，已清理', error);
    window.localStorage.removeItem(ACTIVE_TASK_STORAGE_KEY);
    return {};
  }
};

const persistProcessingTasks = (tasks: PersistedProcessingTaskMap) => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(ACTIVE_TASK_STORAGE_KEY, JSON.stringify(tasks));
};

const clearPersistedProcessingTasks = () => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.removeItem(ACTIVE_TASK_STORAGE_KEY);
};

export default function Home() {
  const [authState, setAuthState] = useState(createLoggedOutState());
  const [accountProfile, setAccountProfile] = useState<UserProfile | undefined>(undefined);
  const [creditBalance, setCreditBalance] = useState<CreditBalanceResponse | undefined>(undefined);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [authError, setAuthError] = useState<string>('');
  const [registerError, setRegisterError] = useState<string>('');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageState>('home');
  const [promptInstruction, setPromptInstruction] = useState<string>('');
  const [patternType, setPatternType] = useState<string>('general1');
  const [upscaleEngine, setUpscaleEngine] = useState<'meitu_v2' | 'runninghub_vr2'>('meitu_v2');
  const [aspectRatio, setAspectRatio] = useState<string>('');
  const [expandRatio, setExpandRatio] = useState<string>('original');
  const [expandEdges, setExpandEdges] = useState<ExpandEdgesState>({
    top: '0.00',
    bottom: '0.00',
    left: '0.00',
    right: '0.00',
  });
  const [expandPrompt, setExpandPrompt] = useState<string>('');
  const [seamDirection, setSeamDirection] = useState<number>(0);
  const [seamFit, setSeamFit] = useState<number>(0.5);
  const [historyRefreshToken, setHistoryRefreshToken] = useState(0);
  const [activeTasks, setActiveTasks] = useState<PersistedProcessingTaskMap>({});

  const methodUiStateRef = useRef<MethodUiStateMap>({});
  const pollingRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({});
  const hasLoadedPersistedTasksRef = useRef(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const rememberMeRef = useRef(false);

  const isLoggedIn = isAuthenticated(authState);
  const accessToken = isLoggedIn ? authState.accessToken : null;
  const authenticatedUserId = authState.status === 'authenticated' ? authState.user.userId : null;
  const currentMethod = currentPage === 'home' ? null : currentPage;
  const currentMethodTask = currentMethod ? activeTasks[currentMethod] : undefined;
  const isCurrentMethodProcessing = Boolean(currentMethodTask);
  const currentTaskId = currentMethodTask?.taskId ?? null;
  const applyStoredMethodUiState = useCallback((method: ProcessingMethod) => {
    const stored = methodUiStateRef.current[method];
    setProcessedImage(stored?.processedImage ?? null);
    setSuccessMessage(stored?.successMessage ?? '');
    setErrorMessage(stored?.errorMessage ?? '');
  }, []);

  const clearTaskPolling = useCallback((taskId: string) => {
    const poller = pollingRefs.current[taskId];
    if (poller) {
      clearInterval(poller);
      delete pollingRefs.current[taskId];
    }
  }, []);

  const clearAllPolling = useCallback(() => {
    Object.values(pollingRefs.current).forEach((poller) => {
      clearInterval(poller);
    });
    pollingRefs.current = {};
  }, []);

  const updateActiveTasks = useCallback(
    (updater: (prev: PersistedProcessingTaskMap) => PersistedProcessingTaskMap) => {
      setActiveTasks((prev) => {
        const next = updater(prev);
        persistProcessingTasks(next);
        return next;
      });
    },
    [],
  );

  const updateMethodUiState = useCallback(
    (method: ProcessingMethod, partial: Partial<MethodViewState>) => {
      const previous = methodUiStateRef.current[method] ?? {
        processedImage: null,
        successMessage: '',
        errorMessage: '',
      };
      const next: MethodViewState = {
        processedImage:
          partial.processedImage !== undefined ? partial.processedImage : previous.processedImage,
        successMessage:
          partial.successMessage !== undefined ? partial.successMessage : previous.successMessage,
        errorMessage:
          partial.errorMessage !== undefined ? partial.errorMessage : previous.errorMessage,
      };
      methodUiStateRef.current[method] = next;

      if (currentMethod === method) {
        if (partial.processedImage !== undefined) {
          setProcessedImage(partial.processedImage);
        }
        if (partial.successMessage !== undefined) {
          setSuccessMessage(partial.successMessage);
        }
        if (partial.errorMessage !== undefined) {
          setErrorMessage(partial.errorMessage);
        }
      }
    },
    [currentMethod],
  );

  useEffect(() => {
    if (!currentMethod) {
      return;
    }
    methodUiStateRef.current[currentMethod] = {
      processedImage,
      successMessage,
      errorMessage,
    };
  }, [currentMethod, processedImage, successMessage, errorMessage]);

  const hydrateAccount = useCallback(
    async (token: string) => {
      const [profileResponse, balanceResponse] = await Promise.all([
        fetchUserProfile(token),
        getCreditBalance(token),
      ]);
      setAccountProfile(profileResponse.data);
      setCreditBalance(balanceResponse.data);
    },
    [],
  );

  useEffect(() => {
    registerTokenUpdateHandler((tokens) => {
      setAuthState((prev) => {
        if (prev.status !== 'authenticated') {
          return prev;
        }

        const updatedState = {
          ...prev,
          accessToken: tokens.accessToken,
          refreshToken: tokens.refreshToken,
        };

        persistSession({
          user: prev.user,
          accessToken: tokens.accessToken,
          refreshToken: tokens.refreshToken,
          rememberMe: rememberMeRef.current,
        });

        return updatedState;
      });
    });

    return () => {
      unregisterTokenUpdateHandler();
    };
  }, [rememberMeRef]);

  useEffect(() => {
    const restored = restoreSession();
    if (!restored) {
      clearAuthTokens();
      rememberMeRef.current = false;
      return;
    }

    rememberMeRef.current = restored.rememberMe;
    setInitialAuthTokens(
      {
        accessToken: restored.accessToken,
        refreshToken: restored.refreshToken,
      },
      { rememberMe: restored.rememberMe },
    );

    const authenticated = createAuthenticatedState(restored.user, {
      accessToken: restored.accessToken,
      refreshToken: restored.refreshToken,
    });

    setAuthState(authenticated);

    hydrateAccount(restored.accessToken)
      .then(() => {
        persistSession({ ...restored, rememberMe: restored.rememberMe });
      })
      .catch(() => {
        clearPersistedSession();
        setAuthState(createLoggedOutState());
        setAccountProfile(undefined);
        setCreditBalance(undefined);
        clearAuthTokens();
        rememberMeRef.current = false;
      });
  }, [hydrateAccount]);

  const authenticateAndLoad = useCallback(
    async (credentials: { identifier: string; password: string; rememberMe: boolean }) => {
      setAuthError('');
      setAuthState(createAuthenticatingState());

      try {
        const loginResult = await authenticate(credentials);
        rememberMeRef.current = credentials.rememberMe;
        setInitialAuthTokens(
          {
            accessToken: loginResult.accessToken,
            refreshToken: loginResult.refreshToken,
          },
          { rememberMe: credentials.rememberMe },
        );
        setAuthState(createAuthenticatedState(loginResult.user, loginResult));
        persistSession({
          user: loginResult.user,
          accessToken: loginResult.accessToken,
          refreshToken: loginResult.refreshToken,
          rememberMe: credentials.rememberMe,
        });

        await hydrateAccount(loginResult.accessToken);
        setShowLoginModal(false);
      } catch (error) {
        clearPersistedSession();
        setAuthState(createLoggedOutState());
        setAccountProfile(undefined);
        setCreditBalance(undefined);
        setAuthError((error as Error)?.message ?? '登录失败，请检查配置后重试');
        clearAuthTokens();
        rememberMeRef.current = false;
        throw error;
      }
    },
    [hydrateAccount],
  );

  const registerAndLoad = useCallback(
    async (credentials: RegisterPayload) => {
      console.log('page.tsx: registerAndLoad called with', { phone: credentials.phone, password: '***' });
      setRegisterError('');
      setAuthState(createAuthenticatingState());

      try {
        console.log('page.tsx: Calling register API');
        const registerResult = await register(credentials);
        console.log('page.tsx: Register API response', registerResult);
        
        // After successful registration, automatically log in
        console.log('page.tsx: Calling authenticate API');
        const loginResult = await authenticate({
          identifier: credentials.phone, // Use phone for login after registration
          password: credentials.password,
          rememberMe: true
        });
        console.log('page.tsx: Authenticate API response', loginResult);
        
        rememberMeRef.current = true;
        setInitialAuthTokens(
          {
            accessToken: loginResult.accessToken,
            refreshToken: loginResult.refreshToken,
          },
          { rememberMe: true },
        );
        setAuthState(createAuthenticatedState(loginResult.user, loginResult));
        persistSession({
          user: loginResult.user,
          accessToken: loginResult.accessToken,
          refreshToken: loginResult.refreshToken,
          rememberMe: true,
        });

        await hydrateAccount(loginResult.accessToken);
        setShowRegisterModal(false);
        console.log('page.tsx: Registration flow completed successfully');
      } catch (error) {
        console.error('page.tsx: Registration flow failed', error);
        setAuthState(createLoggedOutState());
        setAccountProfile(undefined);
        setCreditBalance(undefined);
        
        // Handle specific registration errors
        const errorMessage = (error as Error)?.message;
        if (errorMessage?.includes("该手机号已被注册") || errorMessage?.includes("该邮箱已被注册")) {
          setRegisterError(errorMessage);
        } else if (errorMessage?.includes("密码长度至少8位")) {
          setRegisterError("密码长度至少需要8位字符");
        } else if (errorMessage?.includes("密码确认不一致")) {
          setRegisterError("两次输入的密码不一致");
        } else {
          setRegisterError('注册失败，请检查输入信息后重试');
        }
        
        clearAuthTokens();
        rememberMeRef.current = false;
        throw error;
      }
    },
    [hydrateAccount],
  );

  const requestPasswordResetCode = useCallback(
    async (phone: string) => {
      await sendPasswordResetCode({ phone });
    },
    [],
  );

  const resetPasswordViaPhone = useCallback(
    async (payload: ResetPasswordByPhonePayload) => {
      await resetPasswordByPhone(payload);
    },
    [],
  );

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    if (isCurrentMethodProcessing) {
      setErrorMessage('当前任务正在处理中，请等待完成后再上传新图片');
      if (event.target) {
        event.target.value = '';
      }
      return;
    }

    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedImage(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (isCurrentMethodProcessing) {
      setErrorMessage('当前任务正在处理中，请等待完成后再上传新图片');
      return;
    }
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleStatusResponse = useCallback(
    (
      statusResponse: ApiSuccessResponse<ProcessingStatusData>,
      taskId: string,
      method: ProcessingMethod,
    ) => {
      const statusData = statusResponse.data;

      if (statusData.status === 'completed' && statusData.result?.processedImage) {
        updateMethodUiState(method, {
          processedImage: statusData.result.processedImage,
          successMessage: '处理完成，可以下载结果',
          errorMessage: '',
        });
        setHistoryRefreshToken((token) => token + 1);
        if (accessToken) {
          hydrateAccount(accessToken).catch(() => {
            /* 静默忽略刷新错误 */
          });
        }
        clearTaskPolling(taskId);
        updateActiveTasks((prev) => {
          const next = { ...prev };
          delete next[method];
          return next;
        });
        return;
      }

      if (statusData.status === 'failed') {
        updateMethodUiState(method, {
          errorMessage: '服务器火爆，重试一下。',
          successMessage: '',
        });
        setHistoryRefreshToken((token) => token + 1);
        clearTaskPolling(taskId);
        updateActiveTasks((prev) => {
          const next = { ...prev };
          delete next[method];
          return next;
        });
      }
    },
    [hydrateAccount, accessToken, clearTaskPolling, updateActiveTasks, updateMethodUiState],
  );

  const startStatusPolling = useCallback(
    (taskId: string, method: ProcessingMethod) => {
      if (!accessToken) {
        return;
      }

      clearTaskPolling(taskId);

      const poller = setInterval(() => {
        getProcessingStatus(taskId, accessToken)
          .then((statusResponse) => handleStatusResponse(statusResponse, taskId, method))
          .catch((error) => {
            const message = error?.message ?? '无法获取任务状态，请稍后重试';
            updateMethodUiState(method, {
              errorMessage: message,
              successMessage: '',
            });
            clearTaskPolling(taskId);
            updateActiveTasks((prev) => {
              const next = { ...prev };
              delete next[method];
              return next;
            });
          });
      }, POLLING_INTERVAL_MS);

      pollingRefs.current[taskId] = poller;

      getProcessingStatus(taskId, accessToken)
        .then((statusResponse) => handleStatusResponse(statusResponse, taskId, method))
        .catch((error) => {
          const message = error?.message ?? '无法获取任务状态，请稍后重试';
          updateMethodUiState(method, {
            errorMessage: message,
            successMessage: '',
          });
          clearTaskPolling(taskId);
          updateActiveTasks((prev) => {
            const next = { ...prev };
            delete next[method];
            return next;
          });
        });
    },
    [accessToken, clearTaskPolling, handleStatusResponse, updateActiveTasks, updateMethodUiState],
  );

  useEffect(() => {
    if (!authenticatedUserId || !accessToken || hasLoadedPersistedTasksRef.current) {
      return;
    }

    hasLoadedPersistedTasksRef.current = true;
    const persistedTasks = readPersistedProcessingTasks();
    const userTasks = Object.entries(persistedTasks).reduce<PersistedProcessingTaskMap>(
      (acc, [methodKey, entry]) => {
        if (entry?.userId === authenticatedUserId) {
          acc[methodKey as ProcessingMethod] = entry;
        }
        return acc;
      },
      {},
    );

    if (Object.keys(userTasks).length === 0) {
      return;
    }

    setActiveTasks(userTasks);
    persistProcessingTasks(userTasks);

    Object.entries(userTasks).forEach(([methodKey, entry]) => {
      if (entry) {
        startStatusPolling(entry.taskId, methodKey as ProcessingMethod);
      }
    });

    if (currentPage === 'home' && Object.keys(userTasks).length === 1) {
      const [singleMethod] = Object.keys(userTasks) as ProcessingMethod[];
      setCurrentPage(singleMethod);
      applyStoredMethodUiState(singleMethod);
    }
  }, [authenticatedUserId, accessToken, currentPage, startStatusPolling, applyStoredMethodUiState]);

  const handleProcessImage = () => {
    if (!accessToken) {
      setErrorMessage('正在建立会话，请稍候再试');
      return;
    }

    if (!uploadedImage) {
      setErrorMessage('请先上传图片');
      return;
    }

    if (currentPage === 'home') {
      setErrorMessage('请选择处理方式');
      return;
    }

    if (isCurrentMethodProcessing) {
      setErrorMessage('当前任务正在处理中，请等待完成后再上传新图片');
      return;
    }

    let trimmedInstruction = '';
    if (currentPage === 'prompt_edit') {
      trimmedInstruction = promptInstruction.trim();
      if (!trimmedInstruction) {
        setErrorMessage('请输入要执行的修改指令');
        return;
      }
    }

    setErrorMessage('');
    setSuccessMessage('');
    setProcessedImage(null);

    const processingMethod = currentPage as ProcessingMethod;
    const payload: ProcessingRequestPayload = {
      method: processingMethod,
      image: uploadedImage,
      accessToken,
    };

    if (currentPage === 'prompt_edit') {
      payload.instruction = trimmedInstruction;
    }

    if (currentPage === 'extract_pattern') {
      payload.patternType = patternType;
    }

    if (currentPage === 'upscale') {
      payload.upscaleEngine = upscaleEngine;
    }

    // 添加分辨率参数
    if (aspectRatio) {
      payload.aspectRatio = aspectRatio;
    }

    if (currentPage === 'expand_image') {
      const clampValue = (edge: ExpandEdgeKey, value: string) => {
        const parsed = parseFloat(value);
        if (!Number.isFinite(parsed)) {
          return 0;
        }
        const normalized = Math.max(0, parsed);
        return Math.min(EXPAND_EDGE_MAX[edge], Number(normalized.toFixed(2)));
      };

      const top = clampValue('top', expandEdges.top);
      const bottom = clampValue('bottom', expandEdges.bottom);
      const left = clampValue('left', expandEdges.left);
      const right = clampValue('right', expandEdges.right);

      payload.expandRatio = expandRatio !== 'original' ? expandRatio : undefined;
      payload.expandTop = top;
      payload.expandBottom = bottom;
      payload.expandLeft = left;
      payload.expandRight = right;

      setExpandEdges({
        top: top.toFixed(2),
        bottom: bottom.toFixed(2),
        left: left.toFixed(2),
        right: right.toFixed(2),
      });

      const trimmedExpandPrompt = expandPrompt.trim();
      if (trimmedExpandPrompt) {
        payload.expandPrompt = trimmedExpandPrompt;
      }
    }

    if (currentPage === 'seamless_loop') {
      payload.seamDirection = seamDirection;
      payload.seamFit = Number(seamFit.toFixed(2));
    }

    createProcessingTask(payload)
      .then((response) => {
        const task = response.data;
        setHistoryRefreshToken((token) => token + 1);
        if (authenticatedUserId) {
          updateActiveTasks((prev) => ({
            ...prev,
            [processingMethod]: {
              taskId: task.taskId,
              userId: authenticatedUserId,
              createdAt: task.createdAt ?? new Date().toISOString(),
            },
          }));
        }
        startStatusPolling(task.taskId, processingMethod);
      })
      .catch((error: Error) => {
        setErrorMessage(error.message ?? '任务创建失败');
      });
  };

  const renderPricingModal = () =>
    showPricingModal ? (
      <PricingModal
        onClose={() => setShowPricingModal(false)}
        isLoggedIn={isLoggedIn}
        onLogin={() => {
          setShowPricingModal(false);
          setShowLoginModal(true);
        }}
        accessToken={accessToken || undefined}
      />
    ) : null;

  const accountSummary = useMemo(() => toAccountSummary(accountProfile), [accountProfile]);

  const handleExpandEdgeChange = useCallback(
    (edge: ExpandEdgeKey, value: string) => {
      setExpandEdges((prev) => ({
        ...prev,
        [edge]: value,
      }));
    },
    [],
  );

  return (
    <div className="notranslate">
      {currentPage !== 'home' ? (
        <ProcessingPage
          method={currentPage}
          imagePreview={imagePreview}
          processedImage={processedImage}
          currentTaskId={currentTaskId || undefined}
          isProcessing={isCurrentMethodProcessing}
          hasUploadedImage={Boolean(uploadedImage)}
          onBack={() => {
            setCurrentPage('home');
            setPromptInstruction('');
            setPatternType('general1');
            setUpscaleEngine('meitu_v2');
            setAspectRatio('');
            setExpandRatio('original');
            setExpandEdges({ top: '0.00', bottom: '0.00', left: '0.00', right: '0.00' });
            setExpandPrompt('');
            setSeamDirection(0);
            setSeamFit(0.5);
          }}
          onOpenPricingModal={() => setShowPricingModal(true)}
          onProcessImage={handleProcessImage}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          fileInputRef={fileInputRef}
          onFileInputChange={handleImageUpload}
          errorMessage={errorMessage}
          successMessage={successMessage}
          accessToken={accessToken || undefined}
          promptInstruction={promptInstruction}
          onPromptInstructionChange={setPromptInstruction}
          patternType={patternType}
          onPatternTypeChange={(value) => {
            setPatternType(value);
            if (currentPage === 'extract_pattern') {
              setProcessedImage(null);
              setErrorMessage('');
              setSuccessMessage('');
            }
            // 当从通用模式切换到其他模式时，清除分辨率设置
            if (value !== 'general2') {
              setAspectRatio('');
            }
          }}
          upscaleEngine={upscaleEngine}
          onUpscaleEngineChange={setUpscaleEngine}
          aspectRatio={aspectRatio}
          onAspectRatioChange={setAspectRatio}
          expandRatio={expandRatio}
          onExpandRatioChange={setExpandRatio}
          expandEdges={expandEdges}
          onExpandEdgeChange={handleExpandEdgeChange}
          expandPrompt={expandPrompt}
          onExpandPromptChange={setExpandPrompt}
          seamDirection={seamDirection}
          onSeamDirectionChange={setSeamDirection}
          seamFit={seamFit}
          onSeamFitChange={setSeamFit}
          historyRefreshToken={historyRefreshToken}
        />
      ) : (
        <HomeView
          onSelectMethod={(method) => {
            if (!isLoggedIn) {
              setShowLoginModal(true);
              return;
            }
            setCurrentPage(method);
            applyStoredMethodUiState(method);
            setImagePreview(null);
            setUploadedImage(null);
            if (method === 'prompt_edit') {
              setPromptInstruction('');
            }
            if (method === 'extract_pattern') {
              setPatternType('general1');
            }
            if (method === 'expand_image') {
              setExpandRatio('original');
              setExpandEdges({ top: '0.00', bottom: '0.00', left: '0.00', right: '0.00' });
              setExpandPrompt('');
            }
            if (method === 'seamless_loop') {
              setSeamDirection(0);
              setSeamFit(0.5);
            }
          }}
          onOpenPricingModal={() => setShowPricingModal(true)}
          onLogout={() => {
            clearAllPolling();
            clearPersistedProcessingTasks();
            setActiveTasks({});
            methodUiStateRef.current = {};
            hasLoadedPersistedTasksRef.current = false;
            setProcessedImage(null);
            setSuccessMessage('');
            setErrorMessage('');
            clearPersistedSession();
            setAuthState(createLoggedOutState());
            setAccountProfile(undefined);
            setCreditBalance(undefined);
            setAuthError('');
            setRegisterError('');
            setShowLoginModal(true);
            setShowRegisterModal(false);
            clearAuthTokens();
            rememberMeRef.current = false;
          }}
          onLogin={() => {
            setShowLoginModal(true);
            setShowRegisterModal(false);
          }}
          onRegister={() => {
            console.log('page.tsx: onRegister called');
            setShowRegisterModal(true);
            setShowLoginModal(false);
          }}
          isLoggedIn={isLoggedIn}
          isAuthenticating={authState.status === 'authenticating'}
          authError={authError}
          accountSummary={accountSummary}
          creditBalance={creditBalance}
          onOpenLoginModal={() => setShowLoginModal(true)}
          accessToken={accessToken || undefined}
          historyRefreshToken={historyRefreshToken}
        />
      )}

      {renderPricingModal()}

      <LoginModal
        isOpen={showLoginModal}
        isSubmitting={authState.status === 'authenticating'}
        errorMessage={authError}
        onClose={() => {
          if (authState.status !== 'authenticating') {
            setShowLoginModal(false);
          }
        }}
        onSubmit={async (payload) => {
          await authenticateAndLoad(payload);
        }}
        onSwitchToRegister={() => {
          setShowLoginModal(false);
          setShowRegisterModal(true);
          setAuthError('');
        }}
        onForgotPassword={() => {
          if (authState.status === 'authenticating') {
            return;
          }
          setShowLoginModal(false);
          setShowRegisterModal(false);
          setShowForgotPasswordModal(true);
          setAuthError('');
        }}
      />

      <RegisterModal
        isOpen={showRegisterModal}
        isSubmitting={authState.status === 'authenticating'}
        errorMessage={registerError}
        onClose={() => {
          if (authState.status !== 'authenticating') {
            setShowRegisterModal(false);
          }
        }}
        onSubmit={async (payload) => {
          await registerAndLoad(payload);
        }}
        onSwitchToLogin={() => {
          setShowRegisterModal(false);
          setShowLoginModal(true);
          setRegisterError('');
        }}
      />

      <ForgotPasswordModal
        isOpen={showForgotPasswordModal}
        onClose={() => setShowForgotPasswordModal(false)}
        onSendCode={requestPasswordResetCode}
        onSubmit={async (payload) => {
          await resetPasswordViaPhone(payload);
        }}
        onSwitchToLogin={() => {
          setShowLoginModal(true);
          setAuthError('');
        }}
      />
    </div>
  );
}
