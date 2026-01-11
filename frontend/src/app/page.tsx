'use client';

import {
  ChangeEvent,
  DragEvent,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import HomeView from '../components/HomeView';
import PricingModal from '../components/PricingModal';
import CreditHistoryModal from '../components/CreditHistoryModal';
import ProcessingPage from '../components/ProcessingPage';
import BatchProcessingWrapper from '../components/BatchProcessingWrapper';
import LoginModal from '../components/LoginModal';
import RegisterModal from '../components/RegisterModal';
import ForgotPasswordModal from '../components/ForgotPasswordModal';
import DisclaimerBar from '../components/DisclaimerBar';
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
  agentGetManagedAgent,
} from '../lib/api';
import {
  clearAuthTokens,
  registerTokenUpdateHandler,
  setInitialAuthTokens,
  unregisterTokenUpdateHandler,
} from '../lib/tokenManager';
import { AlertTriangle } from 'lucide-react';

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

const MAX_IMAGE_FILE_SIZE_BYTES = 15 * 1024 * 1024; // 15MB 限制
const MAX_IMAGE_DIMENSION = 3000;

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

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [authState, setAuthState] = useState(createLoggedOutState());
  const [accountProfile, setAccountProfile] = useState<UserProfile | undefined>(undefined);
  const [creditBalance, setCreditBalance] = useState<CreditBalanceResponse | undefined>(undefined);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [authError, setAuthError] = useState<string>('');
  const [registerError, setRegisterError] = useState<string>('');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [prefilledInvitationCode, setPrefilledInvitationCode] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [primaryImageDimensions, setPrimaryImageDimensions] = useState<{ width: number; height: number } | null>(null);
  const [secondaryImage, setSecondaryImage] = useState<File | null>(null);
  const [secondaryImagePreview, setSecondaryImagePreview] = useState<string | null>(null);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [showCreditHistoryModal, setShowCreditHistoryModal] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageState>('home');
  const [promptInstruction, setPromptInstruction] = useState<string>('');
  const [patternType, setPatternType] = useState<string>('general');
  const [denimAspectRatio, setDenimAspectRatio] = useState<string>('1:1');
  const [denimImageCount, setDenimImageCount] = useState<number>(2);
  const [upscaleEngine, setUpscaleEngine] = useState<'meitu_v2' | 'runninghub_vr2'>('meitu_v2');
  const [expandRatio, setExpandRatio] = useState<string>('original');
  const [expandEdges, setExpandEdges] = useState<ExpandEdgesState>({
    top: '0.00',
    bottom: '0.00',
    left: '0.00',
    right: '0.00',
  });
  const [expandPrompt, setExpandPrompt] = useState<string>('');
  const [seamDirection, setSeamDirection] = useState<number>(0);
  const [seamFit, setSeamFit] = useState<number>(0.7);
  const [similarDenoise, setSimilarDenoise] = useState<number>(0.7);
  const [historyRefreshToken, setHistoryRefreshToken] = useState(0);
  const [activeTasks, setActiveTasks] = useState<PersistedProcessingTaskMap>({});
  const [isCreatingTask, setIsCreatingTask] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const [showAgentAlertModal, setShowAgentAlertModal] = useState(false);

  const methodUiStateRef = useRef<MethodUiStateMap>({});
  const pollingRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({});
  const hasLoadedPersistedTasksRef = useRef(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const secondaryFileInputRef = useRef<HTMLInputElement>(null);
  const rememberMeRef = useRef(false);

  const isLoggedIn = isAuthenticated(authState);
  const accessToken = isLoggedIn ? authState.accessToken : null;
  const hasAgentManagement = Boolean(accountProfile?.managedAgentId);
  const authenticatedUserId = authState.status === 'authenticated' ? authState.user.userId : null;
  const currentMethod = currentPage === 'home' ? null : currentPage;
  const currentMethodTask = currentMethod ? activeTasks[currentMethod] : undefined;
  const isCurrentMethodProcessing = Boolean(currentMethodTask);
  const currentTaskId = currentMethodTask?.taskId ?? null;
  const inviteCode = useMemo(() => {
    const token = searchParams.get('invite');
    return token ? token.trim() : '';
  }, [searchParams]);

  useEffect(() => {
    if (!inviteCode || isLoggedIn) {
      return;
    }
    setPrefilledInvitationCode(inviteCode.toUpperCase());
  }, [inviteCode, isLoggedIn]);

  // 比例换算：当选择扩图比例时，根据原图尺寸自动计算边距
  useEffect(() => {
    if (expandRatio === 'original' || !primaryImageDimensions) {
      return;
    }

    const { width, height } = primaryImageDimensions;

    // 解析目标比例
    const parseRatio = (ratioStr: string): { width: number; height: number } | null => {
      const parts = ratioStr.split(':');
      if (parts.length !== 2) return null;
      const w = parseFloat(parts[0]);
      const h = parseFloat(parts[1]);
      if (isNaN(w) || isNaN(h) || w <= 0 || h <= 0) return null;
      return { width: w, height: h };
    };

    const targetRatio = parseRatio(expandRatio);
    if (!targetRatio) return;

    const currentRatio = width / height;
    const desiredRatio = targetRatio.width / targetRatio.height;

    let expandTop = 0;
    let expandBottom = 0;
    let expandLeft = 0;
    let expandRight = 0;

    if (Math.abs(currentRatio - desiredRatio) < 0.001) {
      // 已经是目标比例，不需要扩展
      setExpandEdges({
        top: '0.00',
        bottom: '0.00',
        left: '0.00',
        right: '0.00',
      });
      return;
    }

    if (currentRatio > desiredRatio) {
      // 当前图片太宽，需要在上下扩展
      const targetHeight = width / desiredRatio;
      const totalExpand = (targetHeight - height) / height;
      expandTop = totalExpand / 2;
      expandBottom = totalExpand / 2;

      // 限制在最大值范围内
      expandTop = Math.min(0.5, expandTop);
      expandBottom = Math.min(0.5, expandBottom);
    } else {
      // 当前图片太高，需要在左右扩展
      const targetWidth = height * desiredRatio;
      const totalExpand = (targetWidth - width) / width;
      expandLeft = totalExpand / 2;
      expandRight = totalExpand / 2;

      // 限制在最大值范围内
      expandLeft = Math.min(1.0, expandLeft);
      expandRight = Math.min(1.0, expandRight);
    }

    setExpandEdges({
      top: expandTop.toFixed(2),
      bottom: expandBottom.toFixed(2),
      left: expandLeft.toFixed(2),
      right: expandRight.toFixed(2),
    });
  }, [expandRatio, primaryImageDimensions]);

  const applyStoredMethodUiState = useCallback(
    (method: ProcessingMethod) => {
      const hasActiveTask = Boolean(activeTasks[method]);
      if (!hasActiveTask) {
        // 没有进行中的任务时，不保留上次结果，回到初始状态
        methodUiStateRef.current[method] = {
          processedImage: null,
          successMessage: '',
          errorMessage: '',
        };
        setProcessedImage(null);
        setSuccessMessage('');
        setErrorMessage('');
        return;
      }

      const stored = methodUiStateRef.current[method];
      setProcessedImage(stored?.processedImage ?? null);
      setSuccessMessage(stored?.successMessage ?? '');
      setErrorMessage(stored?.errorMessage ?? '');
    },
    [activeTasks],
  );

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

  const applyFileSelection = (
    file: File,
    slot: 'primary' | 'secondary' = 'primary',
    dimensions?: { width: number; height: number } | null,
  ) => {
    if (slot === 'primary') {
      setUploadedImage(file);
      setPrimaryImageDimensions(dimensions ?? null);
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        setImagePreview(result);

        if (dimensions) {
          return;
        }

        // 读取图片尺寸，便于做前端校验
        const img = new Image();
        img.onload = () => {
          setPrimaryImageDimensions({
            width: img.naturalWidth,
            height: img.naturalHeight,
          });
        };
        img.onerror = () => setPrimaryImageDimensions(null);
        img.src = result;
      };
      reader.readAsDataURL(file);
    } else {
      setSecondaryImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setSecondaryImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const getImageDimensions = useCallback((file: File) => {
    if (file.type === 'image/svg+xml') {
      return Promise.resolve(null);
    }

    return new Promise<{ width: number; height: number } | null>((resolve) => {
      const img = new Image();
      const objectUrl = URL.createObjectURL(file);

      img.onload = () => {
        URL.revokeObjectURL(objectUrl);
        resolve({ width: img.naturalWidth, height: img.naturalHeight });
      };

      img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        resolve(null);
      };

      img.src = objectUrl;
    });
  }, []);

  const validateImageFile = useCallback(
    async (
      file: File,
    ): Promise<
      | { ok: true; dimensions: { width: number; height: number } | null }
      | { ok: false; message: string }
    > => {
      if (!file.type.startsWith('image/')) {
        return { ok: false, message: '请上传有效的图片文件' };
      }

      if (file.size > MAX_IMAGE_FILE_SIZE_BYTES) {
        return { ok: false, message: '图片大小不能超过15MB，请重新上传。' };
      }

      const dimensions = await getImageDimensions(file);
      if (
        dimensions &&
        (dimensions.width > MAX_IMAGE_DIMENSION ||
          dimensions.height > MAX_IMAGE_DIMENSION)
      ) {
        return {
          ok: false,
          message: `图片分辨率不能超过${MAX_IMAGE_DIMENSION}x${MAX_IMAGE_DIMENSION}，请重新上传。`,
        };
      }

      return { ok: true, dimensions };
    },
    [getImageDimensions],
  );

  const handleImageUpload = async (
    event: ChangeEvent<HTMLInputElement>,
    slot: 'primary' | 'secondary' = 'primary',
  ) => {
    if (isCurrentMethodProcessing) {
      setErrorMessage('当前任务正在处理中，请等待完成后再上传新图片');
      if (event.target) {
        event.target.value = '';
      }
      return;
    }

    const file = event.target.files?.[0];
    if (!file) return;

    const input = event.target;
    const validation = await validateImageFile(file);
    if (!validation.ok) {
    setErrorMessage(validation.message);
      input.value = '';
      return;
    }

    setErrorMessage('');
    applyFileSelection(file, slot, validation.dimensions);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleDrop = async (
    event: DragEvent<HTMLDivElement>,
    slot: 'primary' | 'secondary' = 'primary',
  ) => {
    event.preventDefault();

    if (isCurrentMethodProcessing) {
      setErrorMessage('当前任务正在处理中，请等待完成后再上传新图片');
      return;
    }
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      const validation = await validateImageFile(file);
      if (!validation.ok) {
        setErrorMessage(validation.message);
        return;
      }

      setErrorMessage('');
      applyFileSelection(file, slot, validation.dimensions);
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
        const fallbackMessage = '服务器火爆，重试一下。';
        const backendMessage = statusData.error?.message?.trim();
        const errorCode = statusData.error?.code?.trim();
        const genericCodes = ['P006'];
        const genericKeywords = ['服务器火爆', '服务器内部错误'];
        const hasGenericKeyword = backendMessage
          ? genericKeywords.some((keyword) => backendMessage.includes(keyword))
          : false;
        const shouldUseFallback =
          !backendMessage ||
          (errorCode ? genericCodes.includes(errorCode) : false) ||
          hasGenericKeyword;
        const resolvedErrorMessage =
          shouldUseFallback || !backendMessage ? fallbackMessage : backendMessage;

        updateMethodUiState(method, {
          errorMessage: resolvedErrorMessage,
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

    if (currentPage === 'upscale' && primaryImageDimensions) {
      // 通用1/2 均遵循美图尺寸限制
      const maxSize = 2560;
      const { width, height } = primaryImageDimensions;
      if (width > maxSize || height > maxSize) {
        setErrorMessage(
          `AI高清尺寸限制：原图需不超过 ${maxSize}x${maxSize}，当前 ${width}x${height}。请换用较小图片后再试。`,
        );
        return;
      }
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
      if (secondaryImage) {
        payload.image2 = secondaryImage;
      }
    }

    if (currentPage === 'extract_pattern') {
      payload.patternType = patternType;
      if (patternType === 'denim') {
        payload.aspectRatio = denimAspectRatio;
        payload.numImages = denimImageCount;
      }
    }

    if (currentPage === 'upscale') {
      payload.upscaleEngine = upscaleEngine;
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

    if (currentPage === 'similar_image') {
      const clamped = Math.max(0, Math.min(1, similarDenoise));
      payload.denoise = Number(clamped.toFixed(2));
      setSimilarDenoise(clamped);
    }

    setIsCreatingTask(true);
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
        setIsCreatingTask(false);
      })
      .catch((error: Error) => {
        setErrorMessage(error.message ?? '任务创建失败');
        setIsCreatingTask(false);
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

  const renderCreditHistoryModal = () =>
    showCreditHistoryModal ? (
      <CreditHistoryModal
        accessToken={accessToken || undefined}
        onClose={() => setShowCreditHistoryModal(false)}
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
    <div className="notranslate min-h-screen flex flex-col">
      <div className="flex-1">
      {currentPage !== 'home' ? (
        <>
          <ProcessingPage
            method={currentPage}
            imagePreview={imagePreview}
            secondaryImagePreview={secondaryImagePreview}
            processedImage={processedImage}
            currentTaskId={currentTaskId || undefined}
            isProcessing={isCurrentMethodProcessing || isCreatingTask}
            hasUploadedImage={Boolean(uploadedImage)}
            onBack={() => {
              setCurrentPage('home');
              setBatchMode(false);
              setPromptInstruction('');
              setPatternType('general');
              setDenimAspectRatio('1:1');
              setDenimImageCount(2);
              setUpscaleEngine('meitu_v2');
              setExpandRatio('original');
              setExpandEdges({ top: '0.00', bottom: '0.00', left: '0.00', right: '0.00' });
              setExpandPrompt('');
              setSeamDirection(0);
              setSeamFit(0.5);
              setErrorMessage('');
              setSuccessMessage('');
              setProcessedImage(null);
              setImagePreview(null);
              setPrimaryImageDimensions(null);
              setUploadedImage(null);
              setSecondaryImage(null);
              setSecondaryImagePreview(null);
            }}
            onOpenPricingModal={() => setShowPricingModal(true)}
            onProcessImage={handleProcessImage}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            fileInputRef={fileInputRef}
            secondaryFileInputRef={secondaryFileInputRef}
            onFileInputChange={handleImageUpload}
            onSecondaryFileInputChange={(event) => handleImageUpload(event, 'secondary')}
            onSecondaryDragOver={handleDragOver}
            onSecondaryDrop={(event) => handleDrop(event, 'secondary')}
            errorMessage={errorMessage}
            successMessage={successMessage}
            accessToken={accessToken || undefined}
            promptInstruction={promptInstruction}
            onPromptInstructionChange={setPromptInstruction}
            patternType={patternType}
            denimAspectRatio={denimAspectRatio}
            onDenimAspectRatioChange={setDenimAspectRatio}
            onPatternTypeChange={(value) => {
              setPatternType(value);
              if (currentPage === 'extract_pattern') {
                setProcessedImage(null);
                setErrorMessage('');
                setSuccessMessage('');
              }
            }}
            upscaleEngine={upscaleEngine}
            onUpscaleEngineChange={setUpscaleEngine}
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
            denoise={similarDenoise}
            onDenoiseChange={setSimilarDenoise}
            historyRefreshToken={historyRefreshToken}
            batchMode={batchMode}
            onBatchModeChange={setBatchMode}
          />

          {/* Batch Processing Overlay */}
          {batchMode && accessToken && (
            <BatchProcessingWrapper
              method={currentPage}
              accessToken={accessToken}
              onBack={() => setBatchMode(false)}
              onHistoryRefresh={() => setHistoryRefreshToken((token) => token + 1)}
              promptInstruction={promptInstruction}
              patternType={patternType}
              onPatternTypeChange={setPatternType}
              denimAspectRatio={denimAspectRatio}
              onDenimAspectRatioChange={setDenimAspectRatio}
              denimImageCount={denimImageCount}
              upscaleEngine={upscaleEngine}
              expandRatio={expandRatio}
              expandEdges={expandEdges}
              expandPrompt={expandPrompt}
              onExpandRatioChange={setExpandRatio}
              onExpandEdgeChange={handleExpandEdgeChange}
              onExpandPromptChange={setExpandPrompt}
              seamDirection={seamDirection}
              seamFit={seamFit}
              onSeamDirectionChange={setSeamDirection}
              onSeamFitChange={setSeamFit}
            />
          )}
        </>
      ) : (
        <HomeView
          onSelectMethod={(method) => {
            if (!isLoggedIn) {
              setShowLoginModal(true);
              return;
            }
            setBatchMode(false);
            setCurrentPage(method);
            applyStoredMethodUiState(method);
            setImagePreview(null);
            setPrimaryImageDimensions(null);
            setUploadedImage(null);
            setSecondaryImage(null);
            setSecondaryImagePreview(null);
            if (method === 'prompt_edit') {
              setPromptInstruction('');
            }
            if (method === 'extract_pattern') {
              setPatternType('general');
              setDenimAspectRatio('1:1');
              setDenimImageCount(2);
            }
            if (method === 'expand_image') {
              setExpandRatio('original');
              setExpandEdges({ top: '0.00', bottom: '0.00', left: '0.00', right: '0.00' });
              setExpandPrompt('');
            }
            if (method === 'seamless_loop') {
              setSeamDirection(0);
              setSeamFit(0.7);
            }
            if (method === 'similar_image') {
              setSimilarDenoise(0.7);
            }
          }}
          onSelectBatchMode={(method) => {
            if (!isLoggedIn) {
              setShowLoginModal(true);
              return;
            }
            setBatchMode(true);
            setCurrentPage(method);
            applyStoredMethodUiState(method);
          }}
          onOpenPricingModal={() => setShowPricingModal(true)}
          onOpenCreditHistory={() => setShowCreditHistoryModal(true)}
          onOpenAgentManager={async () => {
            if (!accessToken) {
              setShowLoginModal(true);
              return;
            }

            try {
              await agentGetManagedAgent(accessToken);
              router.push("/agent");
            } catch (error) {
              console.error("代理管理入口检查失败：", error);
              setShowAgentAlertModal(true);
            }
          }}
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
          hasAgentManagement={hasAgentManagement}
        />
      )}
      </div>

      <DisclaimerBar />
      {renderPricingModal()}
      {renderCreditHistoryModal()}
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
        prefilledInvitationCode={prefilledInvitationCode}
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

      {/* Agent Alert Modal */}
      {showAgentAlertModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-80 max-w-sm shadow-2xl p-6">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">提示</h3>
              <p className="text-sm text-gray-500 mb-6">当前账号未绑定代理商，申请代理联系管理员</p>
              <button
                onClick={() => setShowAgentAlertModal(false)}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-16 text-sm text-gray-500">
          页面加载中...
        </div>
      }
    >
      <HomeContent />
    </Suspense>
  );
}
