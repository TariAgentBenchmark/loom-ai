import { ProcessingMethod } from "./processing";

const DEFAULT_API_BASE_URL = typeof window !== "undefined" 
  ? `${window.location.origin}/api`
  : "http://localhost:8000/v1";

const resolveApiBaseUrl = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) {
    return envUrl.replace(/\/$/, "");
  }
  
  // 在浏览器环境中，使用当前域名 + /api
  if (typeof window !== "undefined") {
    return `${window.location.origin}/api`;
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

const ensureSuccess = async (response: Response) => {
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

  const messageParts = [
    parsed.primary,
    parsed.secondary,
    fallbackMessage,
  ].filter((value, index, list): value is string => Boolean(value) && list.indexOf(value) === index);

  return Promise.reject(new Error(messageParts.join(" - ")));
};

const withAuthHeader = (headers: HeadersInit | undefined, accessToken: string | undefined) => {
  if (!accessToken) {
    return headers;
  }

  const next = new Headers(headers);
  next.set("Authorization", `Bearer ${accessToken}`);
  return next;
};

const postJson = async <TData, TBody = unknown>(
  path: string,
  body: TBody,
  accessToken?: string,
  init?: RequestInit,
) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: withAuthHeader({ "Content-Type": "application/json" }, accessToken),
    body: JSON.stringify(body),
    ...init,
  });

  const ensured = await ensureSuccess(response);
  return jsonResponse<ApiSuccessResponse<TData>>(ensured);
};

const postFormData = async <TData>(
  path: string,
  formData: FormData,
  accessToken: string,
) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: withAuthHeader(undefined, accessToken),
    body: formData,
  });

  const ensured = await ensureSuccess(response);
  return jsonResponse<ApiSuccessResponse<TData>>(ensured);
};

const getJson = async <TData>(path: string, accessToken: string) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: withAuthHeader(undefined, accessToken),
  });

  const ensured = await ensureSuccess(response);
  return jsonResponse<ApiSuccessResponse<TData>>(ensured);
};

const processingPathMap: Record<ProcessingMethod, string> = {
  prompt_edit: "/processing/prompt-edit",
  style: "/processing/vectorize",
  embroidery: "/processing/embroidery",
  extract_pattern: "/processing/extract-pattern",
  watermark_removal: "/processing/remove-watermark",
  noise_removal: "/processing/denoise",
  upscale: "/processing/upscale",
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
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
  user: AuthenticatedUser;
}

export interface RefreshTokenResult {
  accessToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface AuthenticatedUser {
  userId: string;
  email: string;
  nickname?: string;
  credits?: number;
  avatar?: string;
}

export interface UserProfile {
  userId: string;
  email: string;
  nickname?: string;
  phone?: string;
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

export const login = (payload: LoginPayload) =>
  postJson<LoginResult, { email: string; password: string; remember_me: boolean }>(
    "/auth/login",
    {
      email: payload.email,
      password: payload.password,
      remember_me: Boolean(payload.rememberMe),
    },
  );

export const refreshToken = (refreshTokenValue: string) =>
  fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: withAuthHeader(undefined, refreshTokenValue),
  })
    .then(ensureSuccess)
    .then((response) => jsonResponse<ApiSuccessResponse<RefreshTokenResult>>(response));

export interface ProcessingRequestPayload {
  method: ProcessingMethod;
  image: File;
  accessToken: string;
  instruction?: string;
  model?: "new" | "original";
}

export const createProcessingTask = ({
  method,
  image,
  accessToken,
  instruction,
  model,
}: ProcessingRequestPayload) => {
  const formData = new FormData();
  formData.append("image", image);

  if (method === "prompt_edit") {
    formData.append("instruction", instruction ?? "");
    formData.append("model", model ?? "new");
  }

  const path = processingPathMap[method];
  return postFormData<ProcessingTaskData>(path, formData, accessToken);
};

export const getProcessingStatus = (taskId: string, accessToken: string) =>
  getJson<ProcessingStatusData>(`/processing/status/${taskId}`, accessToken);

export const downloadProcessingResult = async (
  taskId: string,
  accessToken: string,
  format: "png" | "jpg" | "svg" = "png",
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
  const filename = filenameMatch?.[1] ?? `${taskId}.${format}`;

  return { blob, filename };
};

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
  return `${API_ORIGIN}${normalizedPath}`;
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

// Admin API types and functions
export interface AdminUser {
  userId: string;
  email: string;
  nickname: string;
  credits: number;
  membershipType: string;
  status: string;
  isAdmin: boolean;
  createdAt: string;
  lastLoginAt: string;
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

export interface AdminRefund {
  refundId: string;
  orderId: string;
  userId: string;
  userEmail: string;
  amount: number;
  reason: string;
  status: string;
  createdAt: string;
  processedAt: string | null;
  completedAt: string | null;
  processedBy: string | null;
  adminNotes: string | null;
}

export interface AdminRefundsResponse {
  refunds: AdminRefund[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  summary: {
    pendingRefunds: number;
    approvedRefunds: number;
    totalRefundAmount: number;
  };
}

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
  subscriptions: {
    pendingRefunds: number;
    totalRefundAmount: number;
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

// Admin API functions
export const adminLogin = (email: string, password: string) =>
  postJson<LoginResult, { email: string; password: string }>(
    "/auth/admin/login",
    { email, password }
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

export const adminUpdateUserSubscription = (
  userId: string,
  membershipType: string,
  duration: number,
  reason: string,
  accessToken: string
) =>
  postJson<any, { membershipType: string; duration: number; reason: string }>(
    `/admin/users/${userId}/subscription`,
    { membershipType, duration, reason },
    accessToken
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

export const adminGetRefunds = (
  accessToken: string,
  options?: {
    page?: number;
    page_size?: number;
    status_filter?: string;
    user_filter?: string;
    start_date?: string;
    end_date?: string;
  }
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append('page', options.page.toString());
  if (options?.page_size) params.append('page_size', options.page_size.toString());
  if (options?.status_filter) params.append('status_filter', options.status_filter);
  if (options?.user_filter) params.append('user_filter', options.user_filter);
  if (options?.start_date) params.append('start_date', options.start_date);
  if (options?.end_date) params.append('end_date', options.end_date);
  
  const query = params.toString();
  const path = `/admin/refunds${query ? `?${query}` : ''}`;
  
  return getJson<AdminRefundsResponse>(path, accessToken);
};

export const adminProcessRefund = (
  refundId: string,
  action: string,
  reason: string,
  adminNotes: string,
  externalRefundId: string | null,
  accessToken: string
) =>
  postJson<any, { action: string; reason: string; adminNotes: string; externalRefundId: string | null }>(
    `/admin/refunds/${refundId}/action`,
    { action, reason, adminNotes, externalRefundId },
    accessToken
  );

export const adminGetDashboardStats = (accessToken: string) =>
  getJson<AdminDashboardStats>("/admin/dashboard/stats", accessToken);
