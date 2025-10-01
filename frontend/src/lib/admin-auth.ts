import {
  AuthenticatedUser,
  LoginResult,
  adminLogin,
} from "./api";

export type AdminAuthState =
  | { status: "loggedOut" }
  | { status: "authenticating" }
  | {
      status: "authenticated";
      user: AuthenticatedUser;
      accessToken: string;
      refreshToken: string;
    };

export type AdminAuthSession = {
  user: AuthenticatedUser;
  accessToken: string;
  refreshToken: string;
};

export interface AdminAuthContextState extends AdminAuthSession {}

export const createAdminLoggedOutState = (): AdminAuthState => ({ status: "loggedOut" });

export const createAdminAuthenticatingState = (): AdminAuthState => ({ status: "authenticating" });

export const createAdminAuthenticatedState = (
  user: AuthenticatedUser,
  tokens: Pick<LoginResult, "accessToken" | "refreshToken">,
): AdminAuthState => ({
  status: "authenticated",
  user,
  accessToken: tokens.accessToken,
  refreshToken: tokens.refreshToken,
});

export const authenticateAdmin = async (email: string, password: string) => {
  const { data } = await adminLogin(email, password);
  return data;
};

export const isAdminAuthenticated = (state: AdminAuthState): state is Extract<AdminAuthState, { status: "authenticated" }> =>
  state.status === "authenticated";

export const isAdminAuthenticating = (state: AdminAuthState) => state.status === "authenticating";

export const isAdminLoggedOut = (state: AdminAuthState) => state.status === "loggedOut";

type PersistedAdminSession = AdminAuthSession;

const ADMIN_AUTH_STORAGE_KEY = "loomai:admin-auth";

const hasWindow = () => typeof window !== "undefined";

const parseAdminSession = (raw: string): PersistedAdminSession | null => {
  try {
    return JSON.parse(raw) as PersistedAdminSession;
  } catch (error) {
    console.warn("无法解析缓存的管理员会话数据，已忽略", error);
    return null;
  }
};

export const persistAdminSession = (session: PersistedAdminSession) => {
  if (!hasWindow()) {
    return;
  }

  window.localStorage.setItem(ADMIN_AUTH_STORAGE_KEY, JSON.stringify(session));
};

export const restoreAdminSession = (): PersistedAdminSession | null => {
  if (!hasWindow()) {
    return null;
  }

  const raw = window.localStorage.getItem(ADMIN_AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  const parsed = parseAdminSession(raw);
  if (!parsed) {
    window.localStorage.removeItem(ADMIN_AUTH_STORAGE_KEY);
    return null;
  }

  return parsed;
};

export const clearPersistedAdminSession = () => {
  if (!hasWindow()) {
    return;
  }

  window.localStorage.removeItem(ADMIN_AUTH_STORAGE_KEY);
};