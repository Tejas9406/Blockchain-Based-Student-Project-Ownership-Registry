import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  LoginResponseData,
  UserProfileResponse,
  UserRegisterRequest,
  UserLoginRequest,
  UserSummaryResponse,
} from '../types';
import { authService } from '../services/auth.service';
import {
  clearTokens,
  getAccessToken,
  setAccessToken,
  setRefreshToken,
} from '../utils/token';

export interface AuthContextType {
  user: UserSummaryResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: UserLoginRequest) => Promise<LoginResponseData>;
  register: (payload: UserRegisterRequest) => Promise<UserProfileResponse>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const isAuthenticated = useMemo(() => !!user, [user]);

  // Session Restoration
  const refreshUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const userData = await authService.getMe();
      setUser(userData);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (payload: UserLoginRequest): Promise<LoginResponseData> => {
      setIsLoading(true);
      try {
        const responseData = await authService.login(payload);
        setAccessToken(responseData.access_token);
        if (responseData.refresh_token) {
          setRefreshToken(responseData.refresh_token);
        }
        setUser(responseData.user);
        return responseData;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const register = useCallback(
    async (payload: UserRegisterRequest): Promise<UserProfileResponse> => {
      setIsLoading(true);
      try {
        const profile = await authService.register(payload);
        return profile;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      isAuthenticated,
      isLoading,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, isAuthenticated, isLoading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
