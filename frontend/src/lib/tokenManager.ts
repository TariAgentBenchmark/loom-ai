export interface StoredTokens {
  accessToken: string;
  refreshToken: string;
}

type TokenUpdateHandler = (tokens: StoredTokens) => void;

let cachedTokens: StoredTokens | null = null;
let rememberMePreference = false;
let updateHandler: TokenUpdateHandler | null = null;

export const setInitialAuthTokens = (
  tokens: StoredTokens | null,
  options?: { rememberMe?: boolean },
) => {
  cachedTokens = tokens;
  if (options?.rememberMe !== undefined) {
    rememberMePreference = options.rememberMe;
  }
};

export const updateAuthTokens = (tokens: StoredTokens) => {
  cachedTokens = tokens;
  if (updateHandler) {
    updateHandler(tokens);
  }
};

export const clearAuthTokens = () => {
  cachedTokens = null;
  rememberMePreference = false;
};

export const getStoredAccessToken = () => cachedTokens?.accessToken;

export const getStoredRefreshToken = () => cachedTokens?.refreshToken;

export const getRememberMePreference = () => rememberMePreference;

export const registerTokenUpdateHandler = (handler: TokenUpdateHandler) => {
  updateHandler = handler;
};

export const unregisterTokenUpdateHandler = () => {
  updateHandler = null;
};
