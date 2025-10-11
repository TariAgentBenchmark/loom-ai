"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  AdminAuthState,
  AdminAuthContextState,
  createAdminLoggedOutState,
  createAdminAuthenticatingState,
  createAdminAuthenticatedState,
  authenticateAdmin,
  isAdminAuthenticated,
  isAdminAuthenticating,
  isAdminLoggedOut,
  restoreAdminSession,
  persistAdminSession,
  clearPersistedAdminSession,
} from "../lib/admin-auth";

interface AdminAuthContextValue {
  state: AdminAuthState;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextValue | undefined>(undefined);

interface AdminAuthProviderProps {
  children: ReactNode;
}

export const AdminAuthProvider = ({ children }: AdminAuthProviderProps) => {
  const [state, setState] = useState<AdminAuthState>(createAdminLoggedOutState);

  useEffect(() => {
    const session = restoreAdminSession();
    if (session) {
      setState(
        createAdminAuthenticatedState(session.user, {
          accessToken: session.accessToken,
          refreshToken: session.refreshToken,
        })
      );
    }
  }, []);

  const login = async (identifier: string, password: string) => {
    setState(createAdminAuthenticatingState());
    try {
      const result = await authenticateAdmin(identifier, password);
      const authState = createAdminAuthenticatedState(result.user, {
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      });
      
      persistAdminSession({
        user: result.user,
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
      });
      
      setState(authState);
    } catch (error) {
      setState(createAdminLoggedOutState());
      throw error;
    }
  };

  const logout = () => {
    clearPersistedAdminSession();
    setState(createAdminLoggedOutState());
  };

  const contextValue: AdminAuthContextValue = {
    state,
    login,
    logout,
  };

  return (
    <AdminAuthContext.Provider value={contextValue}>
      {children}
    </AdminAuthContext.Provider>
  );
};

export const useAdminAuth = (): AdminAuthContextValue => {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error("useAdminAuth must be used within an AdminAuthProvider");
  }
  return context;
};

export const useAdminAuthState = (): AdminAuthState => {
  const { state } = useAdminAuth();
  return state;
};

export const useAdminIsAuthenticated = (): boolean => {
  const state = useAdminAuthState();
  return isAdminAuthenticated(state);
};

export const useAdminIsAuthenticating = (): boolean => {
  const state = useAdminAuthState();
  return isAdminAuthenticating(state);
};

export const useAdminIsLoggedOut = (): boolean => {
  const state = useAdminAuthState();
  return isAdminLoggedOut(state);
};

export const useAdminUser = (): AdminAuthContextState | undefined => {
  const state = useAdminAuthState();
  if (isAdminAuthenticated(state)) {
    return {
      user: state.user,
      accessToken: state.accessToken,
      refreshToken: state.refreshToken,
    };
  }
  return undefined;
};

export const useAdminAccessToken = (): string | undefined => {
  const state = useAdminAuthState();
  if (isAdminAuthenticated(state)) {
    return state.accessToken;
  }
  return undefined;
};