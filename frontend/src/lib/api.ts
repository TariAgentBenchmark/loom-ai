import { ProcessingMethod } from "./processing";
import { getStoredRefreshToken, updateAuthTokens } from "./tokenManager";

const DEFAULT_API_BASE_URL =
  typeof window !== "undefined"
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
    let urlToParse = API_BASE_URL;

    // 如果是相对路径，添加当前 origin 或 localhost
    if (API_BASE_URL.startsWith("/")) {
      const base =
        typeof window !== "undefined"
          ? window.location.origin
          : "http://localhost:8000";
      urlToParse = `${base}${API_BASE_URL}`;
    }

    const parsedUrl = new URL(urlToParse);
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

  // Ignore HTML error pages (e.g., nginx 502) and fall back to status text instead of showing raw markup
  if (contentType.includes("text/html")) {
    return {};
  }

  if (contentType.includes("application/json")) {
    try {
      const payload = (await response.clone().json()) as ApiErrorResponse & {
        detail?: string;
        error?: ApiErrorResponse["error"] & { detail?: string };
      };

      const candidates = [
        payload.error?.message,
        payload.message,
        payload.detail,
        payload.error?.detail,
      ].filter(
        (value): value is string =>
          typeof value === "string" && value.trim().length > 0,
      );

      if (candidates.length > 0) {
        return {
          primary: candidates[0],
          secondary: candidates.find(
            (candidate) => candidate !== candidates[0],
          ),
        };
      }
    } catch {
      // Fallback to text parsing below
    }
  }

  try {
    const rawText = await response.clone().text();
    const htmlLikePattern =
      /<\s*html[\s>]/i.test(rawText) ||
      /<!DOCTYPE\s+html/i.test(rawText) ||
      /<\s*body[\s>]/i.test(rawText);
    if (htmlLikePattern) {
      return {};
    }

    const cleaned = rawText.replace(/\s+/g, " ").trim();
    if (cleaned) {
      const truncated =
        cleaned.length > 300 ? `${cleaned.slice(0, 300)}…` : cleaned;
      return { secondary: truncated };
    }
  } catch {
    // Ignore parsing failures; fallback message will be used.
  }

  return {};
};

const ensureSuccess = async (
  response: Response,
  isProcessingRequest = false,
) => {
  if (response.ok) {
    return response;
  }

  // Handle 413 Content Too Large error with a user-friendly message
  if (response.status === 413) {
    return Promise.reject(new Error("图片文件过大，请上传小于50MB的图片"));
  }

  const fallbackMessage = "请求失败";
  const parsed = await parseErrorBody(response);
  const parsedMessages = [parsed.primary, parsed.secondary]
    .filter(
      (value): value is string =>
        typeof value === "string" && value.trim().length > 0,
    )
    .map((value) => value.trim())
    .map((value) =>
      value
        .replace(/HTTP\s*\d+/gi, "")
        .replace(/请求失败[:：]?\s*\d+/g, "")
        .trim(),
    )
    .filter((value) => value.length > 0);

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
      (message) =>
        !genericKeywords.some((keyword) => message.includes(keyword)),
    );

    return Promise.reject(
      new Error(backendMessage ?? "服务器火爆，重试一下。"),
    );
  }

  const messageParts = (parsedMessages.length > 0
    ? parsedMessages
    : [fallbackMessage]
  ).filter((value, index, list): value is string =>
    Boolean(value) && list.indexOf(value) === index,
  );

  // Improve error message for common cases
  let errorMessage = messageParts.join(" - ");
  if (response.status === 409 && errorMessage.includes("邮箱已存在")) {
    errorMessage = "该邮箱已被注册，请直接登录或使用其他邮箱";
  }

  return Promise.reject(new Error(errorMessage));
};

const withAuthHeader = (
  headers: HeadersInit | undefined,
  accessToken: string | undefined,
) => {
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
  console.log(
    "postJson: Making request to",
    `${API_BASE_URL}${path}`,
    "with body",
    body,
  );
  try {
    const response = await performAuthenticatedRequest((token) => {
      const url = `${API_BASE_URL}${path}`;
      const options = {
        method: "POST",
        headers: withAuthHeader({ "Content-Type": "application/json" }, token),
        body: JSON.stringify(body),
        ...init,
      };
      console.log("postJson: Fetch options", {
        url,
        headers: options.headers,
        method: options.method,
      });
      return fetch(url, options);
    }, accessToken);

    console.log(
      "postJson: Response status",
      response.status,
      response.statusText,
    );
    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
    throw new Error(message);
  }
};

const putJson = async <TData, TBody = unknown>(
  path: string,
  body: TBody,
  accessToken?: string,
  init?: RequestInit,
) => {
  console.log(
    "putJson: Making request to",
    `${API_BASE_URL}${path}`,
    "with body",
    body,
  );
  try {
    const response = await performAuthenticatedRequest((token) => {
      const url = `${API_BASE_URL}${path}`;
      const options = {
        method: "PUT",
        headers: withAuthHeader({ "Content-Type": "application/json" }, token),
        body: JSON.stringify(body),
        ...init,
      };
      console.log("putJson: Fetch options", {
        url,
        headers: options.headers,
        method: options.method,
      });
      return fetch(url, options);
    }, accessToken);

    console.log(
      "putJson: Response status",
      response.status,
      response.statusText,
    );
    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
    throw new Error(message);
  }
};

const delJson = async <TData>(
  path: string,
  accessToken?: string,
) => {
  console.log("delJson: Making request to", `${API_BASE_URL}${path}`);
  try {
    const response = await performAuthenticatedRequest((token) => {
      const url = `${API_BASE_URL}${path}`;
      const options = {
        method: "DELETE",
        headers: withAuthHeader(undefined, token),
      };
      return fetch(url, options);
    }, accessToken);

    console.log("delJson: Response status", response.status, response.statusText);
    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
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
    let message = "请求失败";

    if (err instanceof Error) {
      if (err.name === "AbortError") {
        message = "请求超时，图片处理时间较长，请稍后在历史记录中查看结果";
      } else if (err.message === "Failed to fetch") {
        message =
          "网络连接异常，请检查网络后重试。如任务已创建，请在历史记录中查看";
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
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
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
          headers: withAuthHeader(
            body ? { "Content-Type": "application/json" } : undefined,
            token,
          ),
          body: body ? JSON.stringify(body) : undefined,
        }),
      accessToken,
    );

    const ensured = await ensureSuccess(response);
    return jsonResponse<ApiSuccessResponse<TData>>(ensured);
  } catch (err) {
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
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
  similar_image: "/processing/similar-image",
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
  identifier: string; // Can be either email or phone
  password: string;
  rememberMe?: boolean;
}

export interface RegisterPayload {
  phone: string; // Now required
  password: string;
  confirmPassword: string;
  nickname?: string;
  email?: string; // Now optional
  invitationCode?: string;
  agentLinkToken?: string;
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
  phone: string; // Added phone field
  email?: string; // Made email optional
  nickname?: string;
  credits?: number;
  avatar?: string;
}

export interface UserProfile {
  userId: string;
  phone: string; // Made phone required
  email?: string; // Made email optional
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
  isTestUser?: boolean;
  agentId?: number | null;
  managedAgentId?: number | null;
  managedAgentLevel?: number | null;
  managedAgentName?: string | null;
  managedAgentStatus?: string | null;
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

export interface ServiceCostQueryOptions {
  patternType?: string;
  upscaleEngine?: string;
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

export interface CreditTransaction {
  transactionId: string;
  type: string;
  amount: number;
  balance: number;
  description: string;
  relatedTaskId?: string | null;
  relatedOrderId?: string | null;
  createdAt: string;
}

export interface CreditTransactionSummary {
  totalEarned: number;
  totalSpent: number;
  netChange: number;
  period: string;
}

export interface CreditTransactionsResponse {
  transactions: CreditTransaction[];
  summary: CreditTransactionSummary;
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages?: number;
    totalPages?: number;
  };
}

export const login = (payload: LoginPayload) =>
  postJson<
    LoginResult,
    { identifier: string; password: string; remember_me: boolean }
  >("/auth/login", {
    identifier: payload.identifier,
    password: payload.password,
    remember_me: Boolean(payload.rememberMe),
  });

export const register = (payload: RegisterPayload) => {
  console.log("api.ts: register function called with", {
    phone: payload.phone,
    passwordLength: payload.password.length,
  });
  return postJson<
    RegisterResult,
    {
      phone: string;
      password: string;
      confirm_password: string;
      nickname?: string;
      email?: string;
      invitation_code?: string;
      agent_link_token?: string;
    }
  >("/auth/register", {
    phone: payload.phone,
    password: payload.password,
    confirm_password: payload.confirmPassword,
    nickname: payload.nickname,
    email: payload.email,
    invitation_code: payload.invitationCode,
    agent_link_token: payload.agentLinkToken,
  });
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
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络异常，无法刷新会话，请重新登录"
        : ((err as Error)?.message ?? "刷新令牌失败");
    throw new Error(message);
  }
}

export interface ProcessingRequestPayload {
  method: ProcessingMethod;
  image: File;
  image2?: File;
  accessToken: string;
  instruction?: string;
  model?: "new" | "original";
  patternType?: string;
  upscaleEngine?: "meitu_v2" | "runninghub_vr2";
  expandRatio?: string;
  expandTop?: number;
  expandBottom?: number;
  expandLeft?: number;
  expandRight?: number;
  expandPrompt?: string;
  seamDirection?: number;
  seamFit?: number;
  denoise?: number;
}

export const createProcessingTask = (payload: ProcessingRequestPayload) => {
  const {
    method,
    image,
    image2,
    accessToken,
    instruction,
    model,
    patternType,
    upscaleEngine,
    expandRatio,
    expandTop,
    expandBottom,
    expandLeft,
    expandRight,
    expandPrompt,
    seamDirection,
    seamFit,
    denoise,
  } = payload;

  const formData = new FormData();
  formData.append("image", image);
  if (method === "prompt_edit" && image2) {
    formData.append("image2", image2);
  }

  if (method === "prompt_edit") {
    formData.append("instruction", instruction ?? "");
    formData.append("model", model ?? "new");
  }

  if (method === "extract_pattern") {
    formData.append("pattern_type", patternType ?? "general");
  }

  if (method === "upscale" && upscaleEngine) {
    formData.append("engine", upscaleEngine);
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
      typeof seamDirection === "number" && Number.isFinite(seamDirection)
        ? seamDirection
        : 0;
    const safeFit =
      typeof seamFit === "number" && Number.isFinite(seamFit) ? seamFit : 0.5;

    formData.append("direction", safeDirection.toString());
    formData.append("fit", safeFit.toString());
  }

  if (method === "similar_image" && typeof denoise === "number") {
    const safeDenoise = Math.max(0, Math.min(1, denoise));
    formData.append("denoise", safeDenoise.toString());
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
  const defaultExtension =
    format === "jpg"
      ? "jpg"
      : format === "svg"
        ? "svg"
        : format === "zip"
          ? "zip"
          : "png";
  const filename = filenameMatch?.[1] ?? `tuyun.${defaultExtension}`;

  return { blob, filename };
};

export const getServiceCost = async (
  serviceKey: string,
  accessToken: string,
  quantity = 1,
  options?: ServiceCostQueryOptions,
) => {
  const params = new URLSearchParams({
    service_key: serviceKey,
    quantity: Math.max(1, quantity).toString(),
  });

  if (options?.patternType) {
    params.append("pattern_type", options.patternType);
  }
  if (options?.upscaleEngine) {
    params.append("upscale_engine", options.upscaleEngine);
  }

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
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
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
    const message =
      err instanceof Error && err.message === "Failed to fetch"
        ? "网络连接异常或被浏览器拦截，请稍后重试"
        : ((err as Error)?.message ?? "请求失败");
    throw new Error(message);
  }
};

export const getCreditBalance = (accessToken: string) =>
  getJson<CreditBalanceResponse>("/credits/balance", accessToken);

export const getCreditTransactions = (
  accessToken: string,
  options?: {
    type?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
  },
) => {
  const params = new URLSearchParams();
  if (options?.type) params.append("type", options.type);
  if (options?.start_date) params.append("start_date", options.start_date);
  if (options?.end_date) params.append("end_date", options.end_date);
  if (options?.page) params.append("page", options.page.toString());
  if (options?.limit) params.append("limit", options.limit.toString());

  const query = params.toString();
  const path = `/credits/transactions${query ? `?${query}` : ""}`;

  return getJson<CreditTransactionsResponse>(path, accessToken);
};

export const getApiBaseUrl = () => API_BASE_URL;

export const getApiOrigin = () => API_ORIGIN;

export const resolveFileUrl = (path: string | null | undefined) => {
  if (!path) {
    return path ?? "";
  }

  if (/^(https?:|data:|blob:)/i.test(path)) {
    return path;
  }

  if (!API_ORIGIN) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const resolvedUrl = `${API_ORIGIN}${normalizedPath}`;

  // 添加日志来调试SVG文件URL解析
  if (path.toLowerCase().includes(".svg")) {
    console.log("resolveFileUrl: SVG file URL resolution", {
      originalPath: path,
      normalizedPath,
      API_ORIGIN,
      resolvedUrl,
      isSvg: true,
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
  retentionDays?: number;
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
  },
) => {
  const params = new URLSearchParams();
  if (options?.type) params.append("type", options.type);
  if (options?.status) params.append("status", options.status);
  if (options?.page) params.append("page", options.page.toString());
  if (options?.limit) params.append("limit", options.limit.toString());

  const query = params.toString();
  const path = `/history/tasks${query ? `?${query}` : ""}`;

  return getJson<HistoryResponse>(path, accessToken);
};

export const getTaskDetail = (taskId: string, accessToken: string) =>
  getJson<TaskDetail>(`/history/tasks/${taskId}`, accessToken);

export const downloadTaskFile = async (
  taskId: string,
  accessToken: string,
  fileType: "original" | "result" = "result",
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
  const filename =
    filenameMatch?.[1] ??
    `${taskId}.${fileType === "original" ? "jpg" : "png"}`;

  return { blob, filename };
};

// Admin API types and functions
export interface AdminUser {
  userId: string;
  email: string | null;
  nickname: string | null;
  phone: string | null;
  agentId?: number | null;
  agentName?: string | null;
  invitationCode?: string | null;
  credits: number;
  membershipType: string;
  status: string;
  isAdmin: boolean;
  isTestUser: boolean;
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

export interface AdminUserDetail extends AdminUser { }

export interface AdminCreditTransaction {
  transactionId: string;
  userId: string;
  userEmail: string | null;
  type: string;
  amount: number;
  balanceAfter: number;
  source: string;
  description: string;
  createdAt: string;
  relatedTaskId: string | null;
  relatedOrderId: string | null;
}

export interface AdminUserTask {
  taskId: string;
  type: string;
  typeName?: string | null;
  status: string;
  creditsUsed: number;
  createdAt?: string | null;
  completedAt?: string | null;
  originalFilename?: string | null;
  resultFilename?: string | null;
  originalImage?: {
    url: string;
    filename: string;
    size: number;
    dimensions?: { width: number; height: number };
  } | null;
  resultImage?: {
    url: string;
    filename: string;
    size: number;
    dimensions?: { width: number; height: number };
  } | null;
  errorMessage?: string | null;
  errorCode?: string | null;
}

export interface AdminUserTaskListResponse {
  tasks: AdminUserTask[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
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
  userEmail: string | null;
  userPhone: string | null;
  userNickname: string | null;
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

export interface AdminOrderDetail extends AdminOrder { }

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

export interface AdminApiLimitMetric {
  api: string;
  limit: number;
  active: number;
  available: number;
  leasedTokens?: number;
  leased_tokens?: number;
}

export interface AdminApiLimitMetricsResponse {
  metrics: AdminApiLimitMetric[];
}

export interface AdminAgent {
  id: number;
  name: string;
  contact?: string | null;
  notes?: string | null;
  status: string;
  level: number;
  parentAgentId?: number | null;
  ownerUserId?: string | null;
  ownerUserPhone?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  invitationCode?: string | null;
  referralLinkToken?: string | null;
  referralLinkStatus?: string | null;
  referralLinkUsageCount?: number | null;
  referralLinkMaxUses?: number | null;
  referralLinkExpiresAt?: string | null;
  commissionMode?: string | null;
  invitationCount: number;
  userCount: number;
}

export interface AdminAgentsResponse {
  agents: AdminAgent[];
}

export interface AdminAgentReferralLink {
  agentId: number;
  token: string;
  status: string;
  usageCount: number;
  maxUses?: number | null;
  expiresAt?: string | null;
  createdAt?: string | null;
}

export interface AdminUserLookupItem {
  userId: string;
  phone?: string | null;
  email?: string | null;
  nickname?: string | null;
}

export interface AdminUserLookupResponse {
  users: AdminUserLookupItem[];
}

export interface ManagedAgentChild {
  id: number;
  name: string;
  level: number;
  status: string;
  parentAgentId?: number | null;
  ownerUserId?: string | null;
  ownerUserPhone?: string | null;
  invitationCode?: string | null;
  createdAt?: string | null;
}

export interface ManagedAgentResponse {
  id: number;
  name: string;
  status: string;
  contact?: string | null;
  notes?: string | null;
  ownerUserId?: string | null;
  ownerUserPhone?: string | null;
  invitationCode?: string | null;
  referralLinkToken?: string | null;
  referralLinkStatus?: string | null;
  createdAt?: string | null;
  invitedCount?: number;
}

export interface AgentLedgerItem {
  orderId: string;
  userId: string;
  userPhone?: string | null;
  paidAt?: string | null;
  amount: number;
  commission: number;
  rate: number;
   status: string;
  settledAt?: string | null;
}

export interface AgentLedgerResponse {
  items: AgentLedgerItem[];
  totalAmount: number;
  totalCommission: number;
  totalOrders: number;
  page: number;
  pageSize: number;
  totalPages: number;
  settledAmount?: number;
  unsettledAmount?: number;
}

export interface AdminCommissionItem {
  orderId: string;
  amount: number;
  commission: number;
  rate: number;
  status: string;
  paidAt?: string | null;
  settledAt?: string | null;
  settledBy?: string | null;
  userId?: string | null;
  userPhone?: string | null;
}

export interface AdminCommissionList {
  items: AdminCommissionItem[];
  totalAmount: number;
  totalCommission: number;
  settledAmount: number;
  unsettledAmount: number;
  totalOrders: number;
}

export interface AdminInvitationCode {
  id: number;
  code: string;
  agentId: number;
  agentName: string;
  status: string;
  maxUses?: number | null;
  usageCount: number;
  remainingUses?: number | null;
  expiresAt?: string | null;
  description?: string | null;
  createdAt: string;
}

export interface AdminInvitationCodeList {
  invitationCodes: AdminInvitationCode[];
}

// Admin API functions
export const adminLogin = (identifier: string, password: string) =>
  postJson<LoginResult, { identifier: string; password: string }>(
    "/auth/admin/login",
    { identifier, password },
  );

export const adminGetUsers = (
  accessToken: string,
  options?: {
    page?: number;
    page_size?: number;
    status_filter?: string;
    membership_filter?: string;
    email_filter?: string;
    keyword?: string;
    sort_by?: string;
    sort_order?: string;
  },
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append("page", options.page.toString());
  if (options?.page_size)
    params.append("page_size", options.page_size.toString());
  if (options?.status_filter)
    params.append("status_filter", options.status_filter);
  if (options?.membership_filter)
    params.append("membership_filter", options.membership_filter);
  if (options?.email_filter)
    params.append("email_filter", options.email_filter);
  if (options?.keyword) params.append("keyword", options.keyword);
  if (options?.sort_by) params.append("sort_by", options.sort_by);
  if (options?.sort_order) params.append("sort_order", options.sort_order);

  const query = params.toString();
  const path = `/admin/users${query ? `?${query}` : ""}`;

  return getJson<AdminUsersResponse>(path, accessToken);
};

export const adminGetUserDetail = (userId: string, accessToken: string) =>
  getJson<AdminUserDetail>(`/admin/users/${userId}`, accessToken);

export const adminGetUserTasks = (
  userId: string,
  accessToken: string,
  options?: { page?: number; limit?: number; type?: string; status?: string },
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append("page", options.page.toString());
  if (options?.limit) params.append("limit", options.limit.toString());
  if (options?.type) params.append("type", options.type);
  if (options?.status) params.append("status", options.status);

  const query = params.toString();
  const path = `/admin/users/${userId}/tasks${query ? `?${query}` : ""}`;
  return getJson<AdminUserTaskListResponse>(path, accessToken);
};

export interface AdminCreateUserPayload {
  phone: string;
  password: string;
  email?: string;
  nickname?: string;
  initialCredits?: number;
  isAdmin?: boolean;
  invitationCode?: string;
  isTestUser?: boolean;
}

export const adminCreateUser = (
  payload: AdminCreateUserPayload,
  accessToken: string,
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
      invitationCode: payload.invitationCode,
      isTestUser: Boolean(payload.isTestUser),
    },
    accessToken,
  );

export const adminUpdateUserStatus = (
  userId: string,
  status: string,
  reason: string,
  accessToken: string,
) =>
  postJson<any, { status: string; reason: string }>(
    `/admin/users/${userId}/status`,
    { status, reason },
    accessToken,
  );

export interface AdminUserAgentUpdatePayload {
  agentId?: number | null;
  reason?: string;
}

export const adminUpdateUserAgent = (
  userId: string,
  payload: AdminUserAgentUpdatePayload,
  accessToken: string,
) =>
  putJson<{ userId: string; oldAgentId?: number | null; newAgentId?: number | null }, AdminUserAgentUpdatePayload>(
    `/admin/users/${userId}/agent`,
    payload,
    accessToken,
  );

export interface AdminDeleteUserPayload {
  reason?: string;
}

export const adminDeleteUser = (
  userId: string,
  accessToken: string,
  payload?: AdminDeleteUserPayload,
) =>
  deleteJson<{ userId: string; deletedAt: string }, AdminDeleteUserPayload>(
    `/admin/users/${userId}`,
    accessToken,
    payload,
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
  },
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append("page", options.page.toString());
  if (options?.page_size)
    params.append("page_size", options.page_size.toString());
  if (options?.transaction_type)
    params.append("transaction_type", options.transaction_type);
  if (options?.source_filter)
    params.append("source_filter", options.source_filter);
  if (options?.start_date) params.append("start_date", options.start_date);
  if (options?.end_date) params.append("end_date", options.end_date);

  const query = params.toString();
  const path = `/admin/users/${userId}/transactions${query ? `?${query}` : ""}`;

  return getJson<AdminCreditTransactionsResponse>(path, accessToken);
};

export const adminAdjustUserCredits = (
  userId: string,
  amount: number,
  reason: string,
  sendNotification: boolean,
  accessToken: string,
) =>
  postJson<any, { amount: number; reason: string; sendNotification: boolean }>(
    `/admin/users/${userId}/credits/adjust`,
    { amount, reason, sendNotification },
    accessToken,
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
  },
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append("page", options.page.toString());
  if (options?.page_size)
    params.append("page_size", options.page_size.toString());
  if (options?.status_filter)
    params.append("status_filter", options.status_filter);
  if (options?.user_filter) params.append("user_filter", options.user_filter);
  if (options?.package_type_filter)
    params.append("package_type_filter", options.package_type_filter);
  if (options?.start_date) params.append("start_date", options.start_date);
  if (options?.end_date) params.append("end_date", options.end_date);

  const query = params.toString();
  const path = `/admin/orders${query ? `?${query}` : ""}`;

  return getJson<AdminOrdersResponse>(path, accessToken);
};

export const adminGetOrderDetail = (orderId: string, accessToken: string) =>
  getJson<AdminOrderDetail>(`/admin/orders/${orderId}`, accessToken);

export const adminUpdateOrderStatus = (
  orderId: string,
  status: string,
  reason: string,
  adminNotes: string,
  accessToken: string,
) =>
  putJson<any, { status: string; reason: string; adminNotes: string }>(
    `/admin/orders/${orderId}/status`,
    { status, reason, adminNotes },
    accessToken,
  );

export const adminGetServicePrices = (
  accessToken: string,
  includeInactive = true,
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
  accessToken: string,
) =>
  putJson<
    AdminServicePriceUpdateResult,
    {
      priceCredits: number;
      serviceName?: string;
      description?: string;
      active?: boolean;
    }
  >(`/admin/service-prices/${serviceKey}`, payload, accessToken);

export const adminGetDashboardStats = (accessToken: string) =>
  getJson<AdminDashboardStats>("/admin/dashboard/stats", accessToken);

export const adminGetApiLimitMetrics = (accessToken: string) =>
  getJson<AdminApiLimitMetricsResponse>("/admin/limits/metrics", accessToken);

export const adminGetAllTasks = (
  accessToken: string,
  options?: {
    page?: number;
    limit?: number;
    userSearch?: string;
    taskType?: string;
    status?: string;
    startDate?: string;
    endDate?: string;
  },
) => {
  const params = new URLSearchParams();
  if (options?.page) params.append("page", options.page.toString());
  if (options?.limit) params.append("limit", options.limit.toString());
  if (options?.userSearch) params.append("user_search", options.userSearch);
  if (options?.taskType) params.append("task_type", options.taskType);
  if (options?.status) params.append("status", options.status);
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);

  const query = params.toString();
  const path = `/admin/tasks${query ? `?${query}` : ""}`;
  return getJson<AdminUserTaskListResponse>(path, accessToken);
};

export interface UserSuggestion {
  userId: string;
  displayText: string;
  nickname: string | null;
  email: string | null;
  phone: string | null;
}

export const adminSearchUserSuggestions = (
  accessToken: string,
  query: string,
  limit?: number,
) => {
  const params = new URLSearchParams();
  params.append("q", query);
  if (limit) params.append("limit", limit.toString());

  const queryString = params.toString();
  const path = `/admin/users/search-suggestions?${queryString}`;
  return getJson<{ suggestions: UserSuggestion[] }>(path, accessToken);
};

export const adminGetAgents = (
  accessToken: string,
  options?: { status?: string },
) => {
  const params = new URLSearchParams();
  if (options?.status) params.append("status", options.status);
  const query = params.toString();
  const path = `/admin/agents${query ? `?${query}` : ""}`;
  return getJson<AdminAgentsResponse>(path, accessToken);
};

export const adminCreateAgent = (
  payload: {
    name: string;
    userIdentifier: string;
    contact?: string;
    notes?: string;
    status?: string;
    commissionMode?: string;
  },
  accessToken: string,
) => postJson<AdminAgent, typeof payload>("/admin/agents", payload, accessToken);

export const adminUpdateAgent = (
  agentId: number,
  payload: { name?: string; contact?: string; notes?: string; status?: string; commissionMode?: string },
  accessToken: string,
) =>
  putJson<AdminAgent, typeof payload>(
    `/admin/agents/${agentId}`,
    payload,
    accessToken,
  );

export const adminDeleteAgent = (agentId: number, accessToken: string) =>
  delJson<{ id: number; name: string; deleted: boolean }>(`/admin/agents/${agentId}`, accessToken);

export const adminRotateAgentReferralLink = (agentId: number, accessToken: string) =>
  postJson<AdminAgentReferralLink, Record<string, never>>(
    `/admin/agents/${agentId}/referral-link/rotate`,
    {},
    accessToken,
  );

export const adminGetAgentUsers = (agentId: number, accessToken: string) =>
  getJson<{
    agent: { id: number; name: string; status: string };
    users: Array<{
      userId: string;
      email?: string | null;
      phone?: string | null;
      nickname?: string | null;
      createdAt: string;
    }>;
  }>(`/admin/agents/${agentId}/users`, accessToken);

export const adminSearchUsers = (query: string, accessToken: string, limit = 10) => {
  const params = new URLSearchParams();
  params.append("q", query);
  params.append("limit", limit.toString());
  return getJson<AdminUserLookupResponse>(`/admin/users/search?${params.toString()}`, accessToken);
};

export const agentGetManagedAgent = (accessToken: string) =>
  getJson<ManagedAgentResponse>("/agent/me", accessToken);

export const agentGetLedger = (
  accessToken: string,
  options?: { startDate?: string; endDate?: string; page?: number; pageSize?: number },
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("startDate", options.startDate);
  if (options?.endDate) params.append("endDate", options.endDate);
  if (options?.page) params.append("page", options.page.toString());
  if (options?.pageSize) params.append("pageSize", options.pageSize.toString());
  const query = params.toString();
  return getJson<AgentLedgerResponse>(`/agent/ledger${query ? `?${query}` : ""}`, accessToken);
};

export const adminGetAgentCommissions = (
  agentId: number,
  accessToken: string,
  options?: { startDate?: string; endDate?: string; status?: string },
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("startDate", options.startDate);
  if (options?.endDate) params.append("endDate", options.endDate);
  if (options?.status) params.append("status", options.status);
  const query = params.toString();
  return getJson<AdminCommissionList>(
    `/admin/agents/${agentId}/commissions${query ? `?${query}` : ""}`,
    accessToken,
  );
};

export const adminSettleAgentCommissions = (
  agentId: number,
  payload: { startDate?: string; endDate?: string; orderIds?: number[]; note?: string },
  accessToken: string,
) => postJson<{ settledOrders: number; settledAmount: number }, typeof payload>(
  `/admin/agents/${agentId}/commissions/settle`,
  payload,
  accessToken,
);

export const adminSettleAgentOrder = (
  agentId: number,
  orderId: string,
  payload: { note?: string } = {},
  accessToken: string,
) =>
  postJson<{ orderId: string; commission: number; settled: boolean }, typeof payload>(
    `/admin/agents/${agentId}/commissions/${orderId}/settle`,
    payload,
    accessToken,
  );

export const adminGetInvitationCodes = (
  accessToken: string,
  options?: { agent_id?: number; status?: string; code_search?: string },
) => {
  const params = new URLSearchParams();
  if (options?.agent_id) params.append("agent_id", options.agent_id.toString());
  if (options?.status) params.append("status", options.status);
  if (options?.code_search) params.append("code_search", options.code_search);
  const query = params.toString();
  const path = `/admin/invitation-codes${query ? `?${query}` : ""}`;
  return getJson<AdminInvitationCodeList>(path, accessToken);
};

export const adminCreateInvitationCode = (
  payload: {
    agentId: number;
    description?: string;
    maxUses?: number;
    expiresAt?: string;
    code?: string;
  },
  accessToken: string,
) =>
  postJson<AdminInvitationCode, typeof payload>(
    "/admin/invitation-codes",
    payload,
    accessToken,
  );

export const adminUpdateInvitationCode = (
  codeId: number,
  payload: {
    description?: string;
    maxUses?: number;
    expiresAt?: string | null;
    status?: string;
  },
  accessToken: string,
) =>
  putJson<AdminInvitationCode, typeof payload>(
    `/admin/invitation-codes/${codeId}`,
    payload,
    accessToken,
  );

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
  postJson<
    null,
    {
      phone: string;
      code: string;
      new_password: string;
      confirm_password: string;
    }
  >("/auth/reset-password-by-phone", {
    phone: payload.phone,
    code: payload.code,
    new_password: payload.newPassword,
    confirm_password: payload.confirmPassword,
  });

// Batch Processing Types and Functions
export interface BatchTaskData {
  batchId: string;
  status: string;
  totalImages: number;
  estimatedTime?: number | null;
  totalCreditsUsed: number;
  createdAt: string;
}

export interface BatchTaskStatus {
  batchId: string;
  status: string;
  totalImages: number;
  completedImages: number;
  failedImages: number;
  progress: number;
  tasks: Array<{
    taskId: string;
    filename: string;
    status: string;
    resultUrl?: string | null;
    errorMessage?: string | null;
  }>;
  createdAt: string;
  completedAt?: string | null;
}

export interface BatchProcessingRequestPayload {
  method: ProcessingMethod;
  images: File[];
  referenceImage?: File;
  accessToken: string;
  instruction?: string;
  patternType?: string;
  upscaleEngine?: "meitu_v2" | "runninghub_vr2";
  expandRatio?: string;
  expandTop?: string;
  expandBottom?: string;
  expandLeft?: string;
  expandRight?: string;
  expandPrompt?: string;
  seamDirection?: number;
  seamFit?: number;
}

export const createBatchTask = (payload: BatchProcessingRequestPayload) => {
  const {
    method,
    images,
    referenceImage,
    accessToken,
    instruction,
    patternType,
    upscaleEngine,
    expandRatio,
    expandTop,
    expandBottom,
    expandLeft,
    expandRight,
    expandPrompt,
    seamDirection,
    seamFit,
  } = payload;

  const batchTaskTypeMap: Partial<Record<ProcessingMethod, string>> = {
    style: "vectorize",
    watermark_removal: "remove_watermark",
    noise_removal: "denoise",
  };

  const batchTaskType = batchTaskTypeMap[method] ?? method;

  const formData = new FormData();

  // Append all images
  images.forEach((image) => {
    formData.append("images", image);
  });

  // Append reference image for prompt_edit
  if (method === "prompt_edit" && referenceImage) {
    formData.append("reference_image", referenceImage);
  }

  // Add method-specific parameters
  if (method === "prompt_edit" && instruction) {
    formData.append("instruction", instruction);
  }

  if (method === "extract_pattern") {
    formData.append("pattern_type", patternType ?? "general");
  }

  if (method === "upscale" && upscaleEngine) {
    formData.append("upscale_engine", upscaleEngine);
  }

  if (method === "expand_image") {
    if (expandRatio) {
      formData.append("expand_ratio", expandRatio);
    }
    if (expandTop) formData.append("expand_top", expandTop);
    if (expandBottom) formData.append("expand_bottom", expandBottom);
    if (expandLeft) formData.append("expand_left", expandLeft);
    if (expandRight) formData.append("expand_right", expandRight);
    if (expandPrompt) formData.append("expand_prompt", expandPrompt);
  }

  if (method === "seamless_loop") {
    if (typeof seamDirection === "number") {
      formData.append("seam_direction", seamDirection.toString());
    }
    if (typeof seamFit === "number") {
      formData.append("seam_fit", seamFit.toString());
    }
  }

  return postFormData<BatchTaskData>(
    `/processing/batch/${batchTaskType}`,
    formData,
    accessToken,
    true
  );
};

export const getBatchStatus = (batchId: string, accessToken: string) =>
  getJson<BatchTaskStatus>(`/processing/batch/status/${batchId}`, accessToken);

export interface BatchDownloadFile {
  url: string;
  filename: string;
}

export interface BatchDownloadResponse {
  files: BatchDownloadFile[];
}

export const downloadBatchResults = async (
  batchId: string,
  accessToken: string,
): Promise<BatchDownloadFile[]> => {
  const response = await getJson<BatchDownloadResponse>(
    `/processing/batch/download/${batchId}`,
    accessToken
  );

  return response.data.files;
};
