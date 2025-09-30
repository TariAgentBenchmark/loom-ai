import { ProcessingMethod, ProcessingOptions } from "./processing";

const DEFAULT_API_BASE_URL = "http://localhost:8000/v1";

const resolveApiBaseUrl = () =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? DEFAULT_API_BASE_URL;

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

const ensureSuccess = async (response: Response) => {
  if (response.ok) {
    return response;
  }

  const fallbackMessage = `请求失败：${response.status}`;
  const parsed = await jsonResponse<ApiErrorResponse>(response).catch(() => null);
  const message =
    parsed?.error?.message ?? parsed?.message ?? fallbackMessage;
  return Promise.reject(new Error(message));
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
  seamless: "/processing/seamless",
  style: "/processing/vectorize",
  embroidery: "/processing/embroidery",
  extract_edit: "/processing/extract-edit",
  extract_pattern: "/processing/extract-pattern",
  watermark_removal: "/processing/remove-watermark",
  noise_removal: "/processing/denoise",
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

type ProcessingOptionPayload = ProcessingOptions[ProcessingMethod];

const serializeOptions = (options: ProcessingOptionPayload | undefined) => {
  if (!options) {
    return undefined;
  }

  return JSON.stringify(options);
};

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
  options?: ProcessingOptionPayload;
  accessToken: string;
}

export const createProcessingTask = ({
  method,
  image,
  options,
  accessToken,
}: ProcessingRequestPayload) => {
  const formData = new FormData();
  formData.append("image", image);

  const serialized = serializeOptions(options);
  if (serialized) {
    formData.append("options", serialized);
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

