import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, X, LogOut, User, ChevronDown, BarChart2, FileText, FolderKanban, Bot, CreditCard, AlertTriangle, Users } from 'lucide-react';
import { cn } from '../lib/utils';
import { UserRole } from '../types';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: BarChart2, roles: ['client_leadership', 'ops_leadership', 'ops_manager', 'team_lead', 'ar_executive', 'qa_auditor'] },
  { name: 'Claims', href: '/claims', icon: FileText, roles: ['client_leadership', 'ops_leadership', 'ops_manager', 'team_lead', 'ar_executive', 'qa_auditor'] },
  { name: 'Work Queues', href: '/work-queues', icon: FolderKanban, roles: ['ops_leadership', 'ops_manager', 'team_lead', 'ar_executive'] },
  { name: 'Denials', href: '/denials', icon: AlertTriangle, roles: ['ops_leadership', 'ops_manager', 'team_lead', 'ar_executive', 'qa_auditor'] },
  { name: 'Payments', href: '/payments', icon: CreditCard, roles: ['ops_leadership', 'ops_manager', 'team_lead', 'ar_executive'] },
  { name: 'Agents', href: '/agents', icon: Bot, roles: ['ops_leadership', 'ops_manager', 'team_lead', 'qa_auditor'] },
  { name: 'Assistant', href: '/assistant', icon: Bot, roles: ['client_leadership', 'ops_leadership', 'ops_manager', 'team_lead', 'ar_executive'] },
  { name: 'Users', href: '/users', icon: Users, roles: ['client_leadership', 'ops_leadership'] },
];

export function Layout({ children }: { children?: React.ReactNode } = {}) {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const filteredNav = navigation.filter((item) => 
    user && hasRole(item.roles as UserRole[])
  );

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200">
            <h1 className="text-xl font-bold text-primary-600">NovaArc RCM</h1>
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-slate-100"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {filteredNav.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }: { isActive: boolean }) =>
                  cn(
                    'flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  )
                }
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5 mr-3 text-slate-400" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          <div className="p-4 border-t border-slate-200">
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                <User className="w-5 h-5 text-primary-600" />
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
                <p className="text-xs text-slate-500 capitalize">{user?.role.replace('_', ' ')}</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-slate-100"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <div className="flex-1 lg:flex-none" />
            
            <div className="flex items-center space-x-4">
              <div className="relative">
                <button
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-slate-100"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                    <User className="w-5 h-5 text-primary-600" />
                  </div>
                  <span className="hidden sm:block text-sm font-medium text-slate-700">{user?.name}</span>
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                </button>
                
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50">
                    <div className="px-4 py-2 border-b border-slate-200">
                      <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                      <p className="text-xs text-slate-500 capitalize">{user?.role.replace('_', ' ')}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
                    >
                      <LogOut className="w-4 h-4 mr-3" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="p-4 sm:p-6 lg:p-8">
          {children ?? <Outlet />}
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold text-primary-600">NovaArc RCM</h1>
          <h2 className="mt-6 text-center text-2xl font-semibold text-slate-900">Sign in</h2>
          <p className="mt-2 text-center text-slate-600">Enter your credentials to access the dashboard</p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="label">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="label">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-3"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <div className="text-center text-sm text-slate-500">
          <p>Demo credentials:</p>
          <p className="font-mono text-xs">ops_leadership@novaarc.local / password123</p>
        </div>
      </div>
    </div>
  );
}