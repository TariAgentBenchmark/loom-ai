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

export default function Home() {
  const [authState, setAuthState] = useState(createLoggedOutState());
  const [accountProfile, setAccountProfile] = useState<UserProfile | undefined>(undefined);
  const [creditBalance, setCreditBalance] = useState<CreditBalanceResponse | undefined>(undefined);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [authError, setAuthError] = useState<string>('');
  const [registerError, setRegisterError] = useState<string>('');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageState>('home');
  const [promptInstruction, setPromptInstruction] = useState<string>('');
  const [patternType, setPatternType] = useState<string>('general');
  const [upscaleEngine, setUpscaleEngine] = useState<'meitu_v2'>('meitu_v2');
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

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const rememberMeRef = useRef(false);

  const isLoggedIn = isAuthenticated(authState);
  const accessToken = isLoggedIn ? authState.accessToken : null;

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

  const clearPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

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

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
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
      currentPoller: ReturnType<typeof setInterval>,
    ) => {
      const statusData = statusResponse.data;

      if (statusData.status === 'completed' && statusData.result?.processedImage) {
        setProcessedImage(statusData.result.processedImage);
        setIsProcessing(false);
        clearInterval(currentPoller);
        pollingRef.current = null;
        setSuccessMessage('处理完成，可以下载结果');
        setHistoryRefreshToken((token) => token + 1);
        if (accessToken) {
          hydrateAccount(accessToken).catch(() => {
            /* 静默忽略刷新错误 */
          });
        }
        return;
      }

      if (statusData.status === 'failed') {
        setErrorMessage(statusData.error?.message ?? '处理失败，请稍后再试');
        setIsProcessing(false);
        clearInterval(currentPoller);
        pollingRef.current = null;
      }
    },
    [hydrateAccount, accessToken],
  );

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

    let trimmedInstruction = '';
    if (currentPage === 'prompt_edit') {
      trimmedInstruction = promptInstruction.trim();
      if (!trimmedInstruction) {
        setErrorMessage('请输入要执行的修改指令');
        return;
      }
    }

    clearPolling();
    setIsProcessing(true);
    setErrorMessage('');
    setSuccessMessage('');
    setProcessedImage(null);

    const payload: ProcessingRequestPayload = {
      method: currentPage,
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

        const poller = setInterval(() => {
          getProcessingStatus(task.taskId, accessToken)
            .then((statusResponse) => handleStatusResponse(statusResponse, poller))
            .catch((error) => {
              setErrorMessage(error?.message ?? '无法获取任务状态，请稍后重试');
              setIsProcessing(false);
              clearInterval(poller);
              pollingRef.current = null;
            });
        }, POLLING_INTERVAL_MS);

        pollingRef.current = poller;
      })
      .catch((error: Error) => {
        setErrorMessage(error.message ?? '任务创建失败');
        setIsProcessing(false);
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
          isProcessing={isProcessing}
          hasUploadedImage={Boolean(uploadedImage)}
          onBack={() => {
            clearPolling();
            setCurrentPage('home');
            setPromptInstruction('');
            setPatternType('general');
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
            // 当从通用模式切换到其他模式时，清除分辨率设置
            if (value !== 'general') {
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
            setProcessedImage(null);
            setErrorMessage('');
            setSuccessMessage('');
            setImagePreview(null);
            setUploadedImage(null);
            setIsProcessing(false);
            clearPolling();
            if (method === 'prompt_edit') {
              setPromptInstruction('');
            }
            if (method === 'extract_pattern') {
              setPatternType('general');
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
            clearPolling();
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
    </div>
  );
}
