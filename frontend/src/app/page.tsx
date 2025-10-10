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
import { PricingTab } from '../lib/pricing';
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
  getProcessingStatus,
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

const AUTH_DEMO_CREDENTIALS = {
  email: 'demo@loom-ai.com',
  password: 'password123',
  rememberMe: true,
};

const POLLING_INTERVAL_MS = 3000;

export default function Home() {
  const [authState, setAuthState] = useState(createLoggedOutState());
  const [accountProfile, setAccountProfile] = useState<UserProfile | undefined>(undefined);
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
  const [activeTab, setActiveTab] = useState<PricingTab>('包月会员');
  const [currentPage, setCurrentPage] = useState<PageState>('home');
  const [promptInstruction, setPromptInstruction] = useState<string>('');
  const [patternType, setPatternType] = useState<string>('general');

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const rememberMeRef = useRef(false);

  const isLoggedIn = isAuthenticated(authState);
  const accessToken = isLoggedIn ? authState.accessToken : null;

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

    fetchUserProfile(restored.accessToken)
      .then((profileResponse: ApiSuccessResponse<UserProfile>) => {
        setAccountProfile(profileResponse.data);
        persistSession({ ...restored, rememberMe: restored.rememberMe });
      })
      .catch(() => {
        clearPersistedSession();
        setAuthState(createLoggedOutState());
        setAccountProfile(undefined);
        clearAuthTokens();
        rememberMeRef.current = false;
      });
  }, []);

  const clearPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const authenticateAndLoad = useCallback(
    async (credentials: { email: string; password: string; rememberMe: boolean }) => {
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

        const profileResponse: ApiSuccessResponse<UserProfile> = await fetchUserProfile(
          loginResult.accessToken,
        );
        setAccountProfile(profileResponse.data);
        setShowLoginModal(false);
      } catch (error) {
        clearPersistedSession();
        setAuthState(createLoggedOutState());
        setAccountProfile(undefined);
        setAuthError((error as Error)?.message ?? '登录失败，请检查配置后重试');
        clearAuthTokens();
        rememberMeRef.current = false;
        throw error;
      }
    },
    [],
  );

  const registerAndLoad = useCallback(
    async (credentials: RegisterPayload) => {
      console.log('page.tsx: registerAndLoad called with', { email: credentials.email, password: '***' });
      setRegisterError('');
      setAuthState(createAuthenticatingState());

      try {
        console.log('page.tsx: Calling register API');
        const registerResult = await register(credentials);
        console.log('page.tsx: Register API response', registerResult);
        
        // After successful registration, automatically log in
        console.log('page.tsx: Calling authenticate API');
        const loginResult = await authenticate({
          email: credentials.email,
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

        const profileResponse: ApiSuccessResponse<UserProfile> = await fetchUserProfile(
          loginResult.accessToken,
        );
        setAccountProfile(profileResponse.data);
        setShowRegisterModal(false);
        console.log('page.tsx: Registration flow completed successfully');
      } catch (error) {
        console.error('page.tsx: Registration flow failed', error);
        setAuthState(createLoggedOutState());
        setAccountProfile(undefined);
        
        // Handle specific registration errors
        const errorMessage = (error as Error)?.message;
        if (errorMessage?.includes("该邮箱已被注册")) {
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
    [],
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
        return;
      }

      if (statusData.status === 'failed') {
        setErrorMessage(statusData.error?.message ?? '处理失败，请稍后再试');
        setIsProcessing(false);
        clearInterval(currentPoller);
        pollingRef.current = null;
      }
    },
    [],
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
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        onClose={() => setShowPricingModal(false)}
      />
    ) : null;

  const accountSummary = useMemo(() => toAccountSummary(accountProfile), [accountProfile]);

  return (
    <>
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
          onPatternTypeChange={setPatternType}
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
          }}
          onOpenPricingModal={() => setShowPricingModal(true)}
          onLogout={() => {
            clearPolling();
            clearPersistedSession();
            setAuthState(createLoggedOutState());
            setAccountProfile(undefined);
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
          onOpenLoginModal={() => setShowLoginModal(true)}
          accessToken={accessToken || undefined}
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
    </>
  );
}
