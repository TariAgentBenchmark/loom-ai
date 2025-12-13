import {
  AuthenticatedUser,
  LoginPayload,
  LoginResult,
  UserProfile,
  getUserProfile,
  login as loginRequest,
} from "./api";

export type AuthState =
  | { status: "loggedOut" }
  | { status: "authenticating" }
  | {
      status: "authenticated";
      user: AuthenticatedUser;
      accessToken: string;
      refreshToken: string;
    };

export type AuthSession = {
  user: AuthenticatedUser;
  accessToken: string;
  refreshToken: string;
};

export interface AuthContextState extends AuthSession {
  profile?: UserProfile;
}

export const createLoggedOutState = (): AuthState => ({ status: "loggedOut" });

export const createAuthenticatingState = (): AuthState => ({ status: "authenticating" });

export const createAuthenticatedState = (
  user: AuthenticatedUser,
  tokens: Pick<LoginResult, "accessToken" | "refreshToken">,
): AuthState => ({
  status: "authenticated",
  user,
  accessToken: tokens.accessToken,
  refreshToken: tokens.refreshToken,
});

export const authenticate = async (payload: LoginPayload) => {
  const { data } = await loginRequest(payload);
  return data;
};

export const fetchUserProfile = (accessToken: string) => getUserProfile(accessToken);

export const toAccountSummary = (profile?: UserProfile) => {
  if (!profile) {
    return undefined;
  }

  return {
    credits: profile.credits,
    monthlyProcessed: profile.monthlyProcessed,
    totalProcessed: profile.totalProcessed,
    nickname: profile.nickname,
    membershipType: profile.membershipType,
    isTestUser: profile.isTestUser,
  };
};

export const isAuthenticated = (state: AuthState): state is Extract<AuthState, { status: "authenticated" }> =>
  state.status === "authenticated";

export const isAuthenticating = (state: AuthState) => state.status === "authenticating";

export const isLoggedOut = (state: AuthState) => state.status === "loggedOut";

type PersistedSession = AuthSession & { rememberMe: boolean };

const AUTH_STORAGE_KEY = "loomai:auth";

const hasWindow = () => typeof window !== "undefined";

const storageFor = (rememberMe: boolean) => (rememberMe ? window.localStorage : window.sessionStorage);

const parseSession = (raw: string): PersistedSession | null => {
  try {
    return JSON.parse(raw) as PersistedSession;
  } catch (error) {
    console.warn("无法解析缓存的会话数据，已忽略", error);
    return null;
  }
};

export const persistSession = (session: PersistedSession) => {
  if (!hasWindow()) {
    return;
  }

  const primary = storageFor(session.rememberMe);
  primary.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));

  const secondary = storageFor(!session.rememberMe);
  secondary.removeItem(AUTH_STORAGE_KEY);
};

export const restoreSession = (): PersistedSession | null => {
  if (!hasWindow()) {
    return null;
  }

  const storages = [window.localStorage, window.sessionStorage];

  for (const storage of storages) {
    const raw = storage.getItem(AUTH_STORAGE_KEY);
    if (!raw) {
      continue;
    }

    const parsed = parseSession(raw);
    if (!parsed) {
      storage.removeItem(AUTH_STORAGE_KEY);
      continue;
    }

    return parsed;
  }

  return null;
};

export const clearPersistedSession = () => {
  if (!hasWindow()) {
    return;
  }

  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
};
