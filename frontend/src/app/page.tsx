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
  ProcessingStatusData,
} from '../lib/api';

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
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [activeTab, setActiveTab] = useState<PricingTab>('包月会员');
  const [currentPage, setCurrentPage] = useState<PageState>('home');

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isLoggedIn = isAuthenticated(authState);
  const accessToken = isLoggedIn ? authState.accessToken : null;

  useEffect(() => {
    const restored = restoreSession();
    if (!restored) {
      return;
    }

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

    clearPolling();
    setIsProcessing(true);
    setErrorMessage('');
    setSuccessMessage('');
    setProcessedImage(null);

    createProcessingTask({ method: currentPage, image: uploadedImage, accessToken })
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
        />
      ) : (
        <HomeView
          onSelectMethod={(method) => {
            setCurrentPage(method);
            setProcessedImage(null);
            setErrorMessage('');
          }}
          onOpenPricingModal={() => setShowPricingModal(true)}
          onLogout={() => {
            clearPolling();
            clearPersistedSession();
            setAuthState(createLoggedOutState());
            setAccountProfile(undefined);
            setAuthError('');
            setShowLoginModal(true);
          }}
          onLogin={() => setShowLoginModal(true)}
          isLoggedIn={isLoggedIn}
          isAuthenticating={authState.status === 'authenticating'}
          authError={authError}
          accountSummary={accountSummary}
          onOpenLoginModal={() => setShowLoginModal(true)}
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
      />
    </>
  );
}
