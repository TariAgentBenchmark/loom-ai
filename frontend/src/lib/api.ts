import { ProcessingMethod } from "./processing";
import { getStoredRefreshToken, updateAuthTokens } from "./tokenManager";

const DEFAULT_API_BASE_URL = typeof window !== "undefined"
  ? `${window.location.origin}/api/v1`
  : "http://localhost:8000/v1";

const resolveApiBaseUrl = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) {
    return envUrl.replace(/\/$/, "");
  }
  
  // 在浏览器环境中，使用当前域名 + /api/v1
  if (typeof window !== "undefined") {
    return `${window.location.origin}/api/v1`;
  }
  
  // 在服务端渲染时，使用 localhost（仅用于 SSR）
  return "http://localhost:8000/v1";
};

const API_BASE_URL = resolveApiBaseUrl();

const resolveApiOrigin = () => {
  try {
    const parsedUrl = new URL(API_BASE_URL);
    return parsedUrl.origin;
  } catch (error) {
    console.warn("无法解析 API 基础地址，已回退到空 origin", error);
    return "";
  }
};

const API_ORIGIN = resolveApiOrigin();

const jsonResponse = async <T>(response: Response): Promise<T> => {
  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  if (!isJson) {
    return Promise.reject(new Error("接口返回格式错误"));
  }

  const payload = (await response.json()) as T;
  return payload;
};

const parseErrorBody = async (
  response: Response,
): Promise<{ primary?: string; secondary?: string }> => {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      const payload = (await response.clone().json()) as ApiErrorResponse & {
        detail?: string;
        error?: ApiErrorResponse["error"] & { detail?: string };
      };

      const candidates = [
        payload.error?.message,
        payload.message,
        payload.error?.code,
        payload.detail,
        payload.error?.detail,
      ].filter((value): value is string => typeof value === "string" && value.trim().length > 0);

      if (candidates.length > 0) {
        return {
          primary: candidates[0],
          secondary: candidates.find((candidate) => candidate !== candidates[0]),
        };
      }
    } catch {
      // Fallback to text parsing below
    }
  }

  try {
    const rawText = await response.clone().text();
    const cleaned = rawText.replace(/\s+/g, " ").trim();
    if (cleaned) {
      const truncated = cleaned.length > 300 ? `${cleaned.slice(0, 300)}…` : cleaned;
      return { secondary: truncated };
    }
  } catch {
    // Ignore parsing failures; fallback message will be used.
  }

  return {};
};

const ensureSuccess = async (response: Response, isProcessingRequest = false) => {
  if (response.ok) {
    return response;
  }

  // Handle 413 Content Too Large error with a user-friendly message
  if (response.status === 413) {
    return Promise.reject(new Error("图片文件过大，请上传小于50MB的图片"));
  }

  const statusText = response.statusText ? ` ${response.statusText}` : "";
  const fallbackMessage = `请求失败：${response.status}${statusText}`;
  const parsed = await parseErrorBody(response);
  const parsedMessages = [parsed.primary, parsed.secondary]
    .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .map((value) => value.trim());

  const creditErrorMessages = parsedMessages.filter(
    (value) => value.includes("积分不足") || value.includes("积分余额不足"),
  );

  if (response.status === 403 && creditErrorMessages.length > 0) {
    return Promise.reject(
      new Error(creditErrorMessages[0] ?? "积分不足，请充值后再试"),
    );
  }

  // For processing requests, try to use backend-provided messages unless they are generic fallbacks
  if (isProcessingRequest) {
    const genericKeywords = ["服务器火爆", "服务器内部错误"];
    const backendMessage = parsedMessages.find(
      (message) => !genericKeywords.some((keyword) => message.includes(keyword)),
    );

    return Promise.reject(new Error(backendMessage ?? "服务器火爆，重试一下。"));
  }

  const messageParts = [
    ...parsedMessages,
    fallbackMessage,
  ].filter((value, index, list): value is string => Boolean(value) && list.indexOf(value) === index);

  // Improve error message for common cases
  let errorMessage = messageParts.join(" - ");
  if (response.status === 409 && errorMessage.includes("邮箱已存在")) {
    errorMessage = "该邮箱已被注册，请直接登录或使用其他邮箱";
  }

  return Promise.reject(new Error(errorMessage));
};

const withAuthHeader = (headers: HeadersInit | undefined, accessToken: string | undefined) => {
  if (!accessToken) {
    return headers;
  }

  const next = new Headers(headers);
  next.set("Authorization", `Bearer ${accessToken}`);
  return next;
};

async function performAuthenticatedRequest(
  makeRequest: (token?: string) => Promise<Response>,
  accessToken?: string,
) {
  const response = await makeRequest(accessToken);

  if (response.status !== 401 || !accessToken) {
    return response;
  }

  const refreshTokenValue = getStoredRefreshToken();
  if (!refreshTokenValue) {
    return response;
  }

  try {
    const refreshResponse = await refreshToken(refreshTokenValue);
    const newAccessToken = refreshResponse.data.accessToken;

    if (!newAccessToken) {
      return response;
    }

    updateAuthTokens({
      accessToken: newAccessToken,
      refreshToken: refreshTokenValue,
    });

    return makeRequest(newAccessToken);
  } catch {
    return response;
  }
}

const postJson = async <TData, TBody = unknown>(
  path: string,
  body: TBody,
  accessToken?: string,
  init?: RequestInit,
) => {
  console.log('postJson: Making request to', `${API_BASE_URL}${path}`, 'with body', body);
  try {
    const response = await performAuthenticatedRequest(
      (token) => {
        const url = `${API_BASE_URL}${path}`;
        const options = {
          method: "POST",
          headers: withAuthHeader({ "Content-Type": "application/json" }, token),
          body: JSON.stringify(body),
          ...init,
        };
        console.log('postJson: Fetch options', { url, headers: options.headers, method: options.method });
        return fetch(url, options);
      },
      accessToken,
    );

    console.log('postJson: Response status', response.status, response.statusText);
    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络连接异常或被浏览器拦截，请稍后重试'
      : (err as Error)?.message ?? '请求失败';
    throw new Error(message);
  }
};

const putJson = async <TData, TBody = unknown>(
  path: string,
  body: TBody,
  accessToken?: string,
  init?: RequestInit,
) => {
  console.log('putJson: Making request to', `${API_BASE_URL}${path}`, 'with body', body);
  try {
    const response = await performAuthenticatedRequest(
      (token) => {
        const url = `${API_BASE_URL}${path}`;
        const options = {
          method: "PUT",
          headers: withAuthHeader({ "Content-Type": "application/json" }, token),
          body: JSON.stringify(body),
          ...init,
        };
        console.log('putJson: Fetch options', { url, headers: options.headers, method: options.method });
        return fetch(url, options);
      },
      accessToken,
    );

    console.log('putJson: Response status', response.status, response.statusText);
    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络连接异常或被浏览器拦截，请稍后重试'
      : (err as Error)?.message ?? '请求失败';
    throw new Error(message);
  }
};

const postFormData = async <TData>(
  path: string,
  formData: FormData,
  accessToken: string,
  isProcessingRequest = false,
) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时
    
    const response = await performAuthenticatedRequest(
      (token) =>
        fetch(`${API_BASE_URL}${path}`, {
          method: "POST",
          headers: withAuthHeader(undefined, token),
          body: formData,
          signal: controller.signal,
        }),
      accessToken,
    );

    clearTimeout(timeoutId);
    const ensured = await ensureSuccess(response, isProcessingRequest);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    let message = '请求失败';
    
    if (err instanceof Error) {
      if (err.name === 'AbortError') {
        message = '请求超时，图片处理时间较长，请稍后在历史记录中查看结果';
      } else if (err.message === 'Failed to fetch') {
        message = '网络连接异常，请检查网络后重试。如任务已创建，请在历史记录中查看';
      } else {
        message = err.message;
      }
    }
    
    throw new Error(message);
  }
};

const getJson = async <TData>(path: string, accessToken: string) => {
  try {
    const response = await performAuthenticatedRequest(
      (token) =>
        fetch(`${API_BASE_URL}${path}`, {
          method: "GET",
          headers: withAuthHeader(undefined, token),
        }),
      accessToken,
    );

    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络连接异常或被浏览器拦截，请稍后重试'
      : (err as Error)?.message ?? '请求失败';
    throw new Error(message);
  }
};

const deleteJson = async <TData, TBody = undefined>(
  path: string,
  accessToken: string,
  body?: TBody,
) => {
  try {
    const response = await performAuthenticatedRequest(
      (token) =>
        fetch(`${API_BASE_URL}${path}`, {
          method: "DELETE",
          headers: withAuthHeader(body ? { "Content-Type": "application/json" } : undefined, token),
          body: body ? JSON.stringify(body) : undefined,
        }),
      accessToken,
    );

    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络连接异常或被浏览器拦截，请稍后重试'
      : (err as Error)?.message ?? '请求失败';
    throw new Error(message);
  }
};

const processingPathMap: Record<ProcessingMethod, string> = {
  prompt_edit: "/processing/prompt-edit",
  style: "/processing/vectorize",
  embroidery: "/processing/embroidery",
  flat_to_3d: "/processing/flat-to-3d",
  extract_pattern: "/processing/extract-pattern",
  watermark_removal: "/processing/remove-watermark",
  noise_removal: "/processing/denoise",
  upscale: "/processing/upscale",
  expand_image: "/processing/expand-image",
  seamless_loop: "/processing/seamless-loop",
};

export interface ApiSuccessResponse<T> {
  success: boolean;
  data: T;
  message: string;
  timestamp: string;
}

export interface ApiErrorResponse {
  success: false;
  message?: string;
  error?: {
    code?: string;
    message?: string;
    status_code?: number;
  };
}

export interface LoginPayload {
  identifier: string;  // Can be either email or phone
  password: string;
  rememberMe?: boolean;
}

export interface RegisterPayload {
  phone: string;  // Now required
  password: string;
  confirmPassword: string;
  nickname?: string;
  email?: string;  // Now optional
}

export interface SendVerificationCodePayload {
  phone: string;
}

export interface VerifyPhoneCodePayload {
  phone: string;
  code: string;
}

export interface SendPasswordResetCodePayload {
  phone: string;
}

export interface ResetPasswordByPhonePayload {
  phone: string;
  code: string;
  newPassword: string;
  confirmPassword: string;
}

export interface SendVerificationCodeResult {
  message: string;
  expires_in: number;
}

export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
  user: AuthenticatedUser;
}

export interface RegisterResult {
  userId: string;
  email: string;
  nickname?: string;
  credits: number;
  createdAt: string;
}

export interface RefreshTokenResult {
  accessToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface AuthenticatedUser {
  userId: string;
  phone: string;  // Added phone field
  email?: string;  // Made email optional
  nickname?: string;
  credits?: number;
  avatar?: string;
}

export interface UserProfile {
  userId: string;
  phone: string;  // Made phone required
  email?: string;  // Made email optional
  nickname?: string;
  avatar?: string;
  credits?: number;
  membershipType?: string;
  membershipExpiry?: string | null;
  totalProcessed?: number;
  monthlyProcessed?: number;
  joinedAt?: string;
  lastLoginAt?: string;
  status?: string;
}

export interface ProcessingTaskData {
  taskId: string;
  status: string;
  estimatedTime?: number | null;
  creditsUsed: number;
  createdAt: string;
}

export interface ProcessingStatusData {
  taskId: string;
  status: string;
  progress: number;
  estimatedTime: number;
  createdAt: string;
  completedAt?: string | null;
  result?: {
    originalImage: string;
    processedImage: string;
    fileSize?: number;
    dimensions?: {
      width: number;
      height: number;
    };
  };
  error?: {
    message?: string;
    code?: string;
  };
}

export interface DownloadResult {
  blob: Blob;
  filename: string;
}

export interface ServiceCostResponse {
  service_key: string;
  quantity: number;
  total_cost: number;
  unit_cost: number;
}

export interface ServicePriceItem {
  id: number;
  service_id: string;
  service_key: string;
  service_name: string;
  description?: string | null;
  price_credits: number;
  active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CreditBalanceResponse {
  credits: number;
  totalEarned: number;
  totalSpent: number;
  netChange: number;
  monthlySpent: number;
  monthlyQuota: number;
  monthlyRemaining: number;
  monthlyUsagePercent: number;
  lastUpdated: string;
}

export const login = (payload: LoginPayload) =>
  postJson<LoginResult, { identifier: string; password: string; remember_me: boolean }>(
    "/auth/login",
    {
      identifier: payload.identifier,
      password: payload.password,
      remember_me: Boolean(payload.rememberMe),
    },
  );

export const register = (payload: RegisterPayload) => {
  console.log('api.ts: register function called with', { phone: payload.phone, passwordLength: payload.password.length });
  return postJson<RegisterResult, { phone: string; password: string; confirm_password: string; nickname?: string; email?: string }>(
    "/auth/register",
    {
      phone: payload.phone,
      password: payload.password,
      confirm_password: payload.confirmPassword,
      nickname: payload.nickname,
      email: payload.email,
    },
  );
};

export async function refreshToken(
  refreshTokenValue: string,
): Promise<ApiSuccessResponse<RefreshTokenResult>> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: withAuthHeader(undefined, refreshTokenValue),
    });

    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<RefreshTokenResult>>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络异常，无法刷新会话，请重新登录'
      : (err as Error)?.message ?? '刷新令牌失败';
    throw new Error(message);
  }
}

export interface ProcessingRequestPayload {
  method: ProcessingMethod;
  image: File;
  accessToken: string;
  instruction?: string;
  model?: "new" | "original";
  patternType?: string;
  patternQuality?: 'standard' | '4k';
  upscaleEngine?: 'meitu_v2' | 'runninghub_vr2';
  aspectRatio?: string;
  expandRatio?: string;
  expandTop?: number;
  expandBottom?: number;
  expandLeft?: number;
  expandRight?: number;
  expandPrompt?: string;
  seamDirection?: number;
  seamFit?: number;
}

export const createProcessingTask = (payload: ProcessingRequestPayload) => {
  const {
    method,
    image,
    accessToken,
    instruction,
    model,
    patternType,
    patternQuality,
    upscaleEngine,
    aspectRatio,
    expandRatio,
    expandTop,
    expandBottom,
    expandLeft,
    expandRight,
    expandPrompt,
    seamDirection,
    seamFit,
  } = payload;

  const formData = new FormData();
  formData.append("image", image);

  if (method === "prompt_edit") {
    formData.append("instruction", instruction ?? "");
    formData.append("model", model ?? "new");
  }

  if (method === "extract_pattern") {
    formData.append("pattern_type", patternType ?? "general1");
    if (patternQuality) {
      formData.append("quality", patternQuality);
    }
  }

  if (method === "upscale" && upscaleEngine) {
    formData.append("engine", upscaleEngine);
  }

  // 添加分辨率参数
  if (aspectRatio) {
    formData.append("aspect_ratio", aspectRatio);
  }

  if (method === "expand_image") {
    formData.append("expand_top", (expandTop ?? 0).toString());
    formData.append("expand_bottom", (expandBottom ?? 0).toString());
    formData.append("expand_left", (expandLeft ?? 0).toString());
    formData.append("expand_right", (expandRight ?? 0).toString());
    if (expandRatio) {
      formData.append("expand_ratio", expandRatio);
    }
    if (expandPrompt) {
      formData.append("prompt", expandPrompt);
    }
  }

  if (method === "seamless_loop") {
    const safeDirection =
      typeof seamDirection === "number" && Number.isFinite(seamDirection) ? seamDirection : 0;
    const safeFit = typeof seamFit === "number" && Number.isFinite(seamFit) ? seamFit : 0.5;

    formData.append("direction", safeDirection.toString());
    formData.append("fit", safeFit.toString());
  }

  const path = processingPathMap[method];
  return postFormData<ProcessingTaskData>(path, formData, accessToken, true);
};

export const getProcessingStatus = (taskId: string, accessToken: string) =>
  getJson<ProcessingStatusData>(`/processing/status/${taskId}`, accessToken);

export const downloadProcessingResult = async (
  taskId: string,
  accessToken: string,
  format: "png" | "jpg" | "svg" | "zip" = "png",
): Promise<DownloadResult> => {
  const response = await fetch(
    `${API_BASE_URL}/processing/result/${taskId}/download?format=${format}`,
    {
      method: "GET",
      headers: withAuthHeader(undefined, accessToken),
    },
  );

  const ensured = await ensureSuccess(response);
  const blob = await ensured.blob();

  const contentDisposition = ensured.headers.get("content-disposition") ?? "";
  const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  const defaultExtension = format === "jpg" ? "jpg" : format === "svg" ? "svg" : format === "zip" ? "zip" : "png";
  const filename = filenameMatch?.[1] ?? `tuyun.${defaultExtension}`;

  return { blob, filename };
};

export const getServiceCost = async (
  serviceKey: string,
  accessToken: string,
  quantity = 1,
) => {
  const params = new URLSearchParams({
    service_key: serviceKey,
    quantity: Math.max(1, quantity).toString(),
  });

  try {
    const response = await performAuthenticatedRequest(
      (token) =>
        fetch(`${API_BASE_URL}/membership/service-cost?${params.toString()}`, {
          method: "GET",
          headers: withAuthHeader(undefined, token),
        }),
      accessToken,
    );

    const ensured = await ensureSuccess(response);
    return jsonResponse<ServiceCostResponse>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络连接异常或被浏览器拦截，请稍后重试'
      : (err as Error)?.message ?? '请求失败';
    throw new Error(message);
  }
};

export const getPublicServicePrices = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/membership/public/services`, {
      method: "GET",
    });

    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<ServicePriceItem[]>>(ensured);
  } catch (err) {
    const message = (err instanceof Error && err.message === 'Failed to fetch')
      ? '网络连接异常或被浏览器拦截，请稍后重试'
      : (err as Error)?.message ?? '请求失败';
    throw new Error(message);
  }
};

export const getCreditBalance = (accessToken: string) =>
  getJson<CreditBalanceResponse>('/credits/balance', accessToken);

export const getApiBaseUrl = () => API_BASE_URL;

export const getApiOrigin = () => API_ORIGIN;

export const resolveFileUrl = (path: string | null | undefined) => {
  if (!path) {
    return path ?? '';
  }

  if (/^(https?:|data:|blob:)/i.test(path)) {
    return path;
  }

  if (!API_ORIGIN) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const resolvedUrl = `${API_ORIGIN}${normalizedPath}`;
  
  // 添加日志来调试SVG文件URL解析
  if (path.toLowerCase().includes('.svg')) {
    console.log('resolveFileUrl: SVG file URL resolution', {
      originalPath: path,
      normalizedPath,
      API_ORIGIN,
      resolvedUrl,
      isSvg: true
    });
  }
  
  return resolvedUrl;
};

export const getUserProfile = (accessToken: string) =>
  getJson<UserProfile>("/user/profile", accessToken);

// 历史记录相关接口
export interface HistoryTask {
  taskId: string;
  type: string;
  typeName: string;
  status: string;
  originalImage: {
    url: string;
    filename: string;
    size: number;
    dimensions?: { width: number; height: number };
  };
  resultImage?: {
    url: string;
    filename: string;
    size: number;
    dimensions?: { width: number; height: number };
  };
  creditsUsed: number;
  processingTime?: number;
  favorite: boolean;
  tags: string[];
  createdAt: string;
  completedAt?: string;
}

export interface HistoryResponse {
  tasks: HistoryTask[];
  statistics: {
    totalTasks: number;
    completedTasks: number;
    failedTasks: number;
    totalCreditsUsed: number;
    avgProcessingTime: number;
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface TaskDetail extends HistoryTask {
  options?: any;
  metadata?: any;
  notes?: string;
  downloadCount: number;
  lastDownloaded?: string;
  startedAt?: string;
}

export const getHistoryTasks = (
  accessToken: string,
  options?: {
    type?: string;
    status?: string;
    page?: number;
    limit?: number;
  }
) => {
  const params = new URLSearchParams();
  if (options?.type) params.append('type', options.type);
  if (options?.status) params.append('status', options.status);
  if (options?.page) params.append('page', options.page.toString());
  if (options?.limit) params.append('limit', options.limit.toString());
  
  const query = params.toString();
  const path = `/history/tasks${query ? `?${query}` : ''}`;
  
  return getJson<HistoryResponse>(path, accessToken);
};

export const getTaskDetail = (taskId: string, accessToken: string) =>
  getJson<TaskDetail>(`/history/tasks/${taskId}`, accessToken);

export const downloadTaskFile = async (
  taskId: string,
  accessToken: string,
  fileType: "original" | "result" = "result"
): Promise<DownloadResult> => {
  const response = await fetch(
    `${API_BASE_URL}/history/tasks/${taskId}/download?file_type=${fileType}`,
    {
      method: "GET",
      headers: withAuthHeader(undefined, accessToken),
    },
  );

  const ensured = await ensureSuccess(response);
  const blob = await ensured.blob();

  const contentDisposition = ensured.headers.get("content-disposition") ?? "";
  const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  const filename = filenameMatch?.[1] ?? `${taskId}.${fileType === "original" ? "jpg" : "png"}`;

  return { blob, filename };
};

// Admin API types and functions
export interface AdminUser {
  userId: string;
  email: string | null;
  nickname: string | null;
  credits: number;
  membershipType: string;
  status: string;
  isAdmin: boolean;
  createdAt: string;
  lastLoginAt: string | null;
}

export interface AdminUsersResponse {
  users: AdminUser[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface AdminUserDetail extends AdminUser {}

export interface AdminCreditTransaction {
  transactionId: string;
  userId: string;
  userEmail: string;
  type: string;
  amount: number;
  balanceAfter: number;
  source: string;
  description: string;
  createdAt: string;
  relatedTaskId: string | null;
  relatedOrderId: string | null;
}

export interface AdminCreditTransactionsResponse {
  transactions: AdminCreditTransaction[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  summary: {
    totalEarned: number;
    totalSpent: number;
    netChange: number;
    currentBalance: number;
  };
}

export interface AdminOrder {
  orderId: string;
  userId: string;
  userEmail: string;
  packageId: string;
  packageName: string;
  packageType: string;
  originalAmount: number;
  discountAmount: number;
  finalAmount: number;
  paymentMethod: string;
  status: string;
  createdAt: string;
  paidAt: string | null;
  expiresAt: string | null;
  creditsAmount: number | null;
  membershipDuration: number | null;
}

export interface AdminOrdersResponse {
  orders: AdminOrder[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  summary: {
    totalRevenue: number;
    pendingOrders: number;
    conversionRate: number;
  };
}

export interface AdminOrderDetail extends AdminOrder {}


export interface AdminDashboardStats {
  users: {
    total: number;
    active: number;
    admin: number;
    newToday: number;
    membershipBreakdown: {
      free: number;
      basic: number;
      premium: number;
      enterprise: number;
    };
  };
  credits: {
    total: number;
    transactionsToday: number;
  };
  orders: {
    total: number;
    paid: number;
    pending: number;
    conversionRate: number;
  };
  revenue: {
    total: number;
    today: number;
    averageOrderValue: number;
  };
  recentActivity: Array<{
    type: string;
    id: string;
    user: string;
    description: string;
    amount: number;
    status: string;
    timestamp: string;
  }>;
}

export interface AdminServicePrice {
  serviceId: string;
  serviceKey: string;
  serviceName: string;
  description?: string | null;
  priceCredits: number;
  active: boolean;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface AdminServicePriceList {
  services: AdminServicePrice[];
}

export interface AdminServicePriceUpdateResult {
  service: AdminServicePrice;
  changes: Record<string, unknown>;
  updated: boolean;
}

// Admin API functions
export const adminLogin = (identifier: string, password: string) =>
  postJson<LoginResult, { identifier: string; password: string }>(
    "/auth/admin/login",
    { identifier, password }
  );

export const adminGetUsers = (
  accessToken: string,
  options?: {
    page?: number;
    page_size?: number;
    status_filter?: string;
    membership_filter?: string;
    email_filter?: string;
    sort_by?: string;
    sort_order?: string;
  }
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append('page', options.page.toString());
  if (options?.page_size) params.append('page_size', options.page_size.toString());
  if (options?.status_filter) params.append('status_filter', options.status_filter);
  if (options?.membership_filter) params.append('membership_filter', options.membership_filter);
  if (options?.email_filter) params.append('email_filter', options.email_filter);
  if (options?.sort_by) params.append('sort_by', options.sort_by);
  if (options?.sort_order) params.append('sort_order', options.sort_order);
  
  const query = params.toString();
  const path = `/admin/users${query ? `?${query}` : ''}`;
  
  return getJson<AdminUsersResponse>(path, accessToken);
};

export const adminGetUserDetail = (userId: string, accessToken: string) =>
  getJson<AdminUserDetail>(`/admin/users/${userId}`, accessToken);

export interface AdminCreateUserPayload {
  phone: string;
  password: string;
  email?: string;
  nickname?: string;
  initialCredits?: number;
  isAdmin?: boolean;
}

export const adminCreateUser = (
  payload: AdminCreateUserPayload,
  accessToken: string
) =>
  postJson<AdminUser, AdminCreateUserPayload>(
    "/admin/users",
    {
      phone: payload.phone,
      password: payload.password,
      email: payload.email,
      nickname: payload.nickname,
      initialCredits: payload.initialCredits ?? 0,
      isAdmin: Boolean(payload.isAdmin),
    },
    accessToken
  );

export const adminUpdateUserStatus = (
  userId: string,
  status: string,
  reason: string,
  accessToken: string
) =>
  postJson<any, { status: string; reason: string }>(
    `/admin/users/${userId}/status`,
    { status, reason },
    accessToken
  );


export interface AdminDeleteUserPayload {
  reason?: string;
}

export const adminDeleteUser = (
  userId: string,
  accessToken: string,
  payload?: AdminDeleteUserPayload
) =>
  deleteJson<{ userId: string; deletedAt: string }, AdminDeleteUserPayload>(
    `/admin/users/${userId}`,
    accessToken,
    payload
  );

export const adminGetUserTransactions = (
  userId: string,
  accessToken: string,
  options?: {
    page?: number;
    page_size?: number;
    transaction_type?: string;
    source_filter?: string;
    start_date?: string;
    end_date?: string;
  }
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append('page', options.page.toString());
  if (options?.page_size) params.append('page_size', options.page_size.toString());
  if (options?.transaction_type) params.append('transaction_type', options.transaction_type);
  if (options?.source_filter) params.append('source_filter', options.source_filter);
  if (options?.start_date) params.append('start_date', options.start_date);
  if (options?.end_date) params.append('end_date', options.end_date);
  
  const query = params.toString();
  const path = `/admin/users/${userId}/transactions${query ? `?${query}` : ''}`;
  
  return getJson<AdminCreditTransactionsResponse>(path, accessToken);
};

export const adminAdjustUserCredits = (
  userId: string,
  amount: number,
  reason: string,
  sendNotification: boolean,
  accessToken: string
) =>
  postJson<any, { amount: number; reason: string; sendNotification: boolean }>(
    `/admin/users/${userId}/credits/adjust`,
    { amount, reason, sendNotification },
    accessToken
  );

export const adminGetOrders = (
  accessToken: string,
  options?: {
    page?: number;
    page_size?: number;
    status_filter?: string;
    user_filter?: string;
    package_type_filter?: string;
    start_date?: string;
    end_date?: string;
  }
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append('page', options.page.toString());
  if (options?.page_size) params.append('page_size', options.page_size.toString());
  if (options?.status_filter) params.append('status_filter', options.status_filter);
  if (options?.user_filter) params.append('user_filter', options.user_filter);
  if (options?.package_type_filter) params.append('package_type_filter', options.package_type_filter);
  if (options?.start_date) params.append('start_date', options.start_date);
  if (options?.end_date) params.append('end_date', options.end_date);
  
  const query = params.toString();
  const path = `/admin/orders${query ? `?${query}` : ''}`;
  
  return getJson<AdminOrdersResponse>(path, accessToken);
};

export const adminGetOrderDetail = (orderId: string, accessToken: string) =>
  getJson<AdminOrderDetail>(`/admin/orders/${orderId}`, accessToken);

export const adminUpdateOrderStatus = (
  orderId: string,
  status: string,
  reason: string,
  adminNotes: string,
  accessToken: string
) =>
  postJson<any, { status: string; reason: string; adminNotes: string }>(
    `/admin/orders/${orderId}/status`,
    { status, reason, adminNotes },
    accessToken
  );

export const adminGetServicePrices = (
  accessToken: string,
  includeInactive = true
) => {
  const params = new URLSearchParams();
  if (includeInactive) {
    params.append("include_inactive", "true");
  }

  const query = params.toString();
  const path = `/admin/service-prices${query ? `?${query}` : ""}`;

  return getJson<AdminServicePriceList>(path, accessToken);
};

export const adminUpdateServicePrice = (
  serviceKey: string,
  payload: {
    priceCredits: number;
    serviceName?: string;
    description?: string;
    active?: boolean;
  },
  accessToken: string
) =>
  putJson<AdminServicePriceUpdateResult, {
    priceCredits: number;
    serviceName?: string;
    description?: string;
    active?: boolean;
  }>(
    `/admin/service-prices/${serviceKey}`,
    payload,
    accessToken
  );


export const adminGetDashboardStats = (accessToken: string) =>
  getJson<AdminDashboardStats>("/admin/dashboard/stats", accessToken);

export const sendVerificationCode = (payload: SendVerificationCodePayload) =>
  postJson<SendVerificationCodeResult, { phone: string }>(
    "/auth/send-verification-code",
    payload,
  );

export const verifyPhoneCode = (payload: VerifyPhoneCodePayload) =>
  postJson<null, { phone: string; code: string }>(
    "/auth/verify-phone-code",
    payload,
  );

export const sendPasswordResetCode = (payload: SendPasswordResetCodePayload) =>
  postJson<{ message: string; expires_in: number }, { phone: string }>(
    "/auth/send-password-reset-code",
    payload,
  );

export const resetPasswordByPhone = (payload: ResetPasswordByPhonePayload) =>
  postJson<null, { phone: string; code: string; new_password: string; confirm_password: string }>(
    "/auth/reset-password-by-phone",
    {
      phone: payload.phone,
      code: payload.code,
      new_password: payload.newPassword,
      confirm_password: payload.confirmPassword,
    },
  );
