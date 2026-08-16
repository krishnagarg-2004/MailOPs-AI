export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (returnTo?: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}
