import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../services/api';
import { User, UserRole } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');
    if (storedToken && storedUser && storedUser !== "undefined") {
      try {
        const parsed = JSON.parse(storedUser);
        if (parsed) {
          setToken(storedToken);
          setUser(parsed);
        } else {
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
        }
      } catch {
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
      }
    } else if (storedUser === "undefined") {
      localStorage.removeItem('user');
      localStorage.removeItem('access_token');
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password);
    localStorage.setItem('access_token', data.access_token);
    setToken(data.access_token);
    try {
      const me = await api.getMe();
      localStorage.setItem('user', JSON.stringify(me));
      setUser(me);
    } catch {
      // fallback: decode token or keep null, will fetch on next load
      setUser(null);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const hasRole = (roles: UserRole[]) => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, hasRole, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}