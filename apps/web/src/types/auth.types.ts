export interface User {
  id: string;
  email: string;
  user_metadata: Record<string, any>;
}

export interface OAuthUrlResponse {
  url: string;
}

export interface OAuthCallbackResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}
