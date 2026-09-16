import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Menu, X, LogOut, ChevronDown,
  BarChart2, FileText, FolderKanban, Bot,
  CreditCard, AlertTriangle, Users, Sparkles,
  Eye, EyeOff, Activity, Shield,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { UserRole } from '../types';

// ── Navigation configuration ──────────────────────────────────────────────────
const navigation = [
  {
    group: 'Overview',
    items: [
      { name: 'Dashboard',   href: '/dashboard',   icon: BarChart2,     iconColor: 'text-blue-400' },
    ],
  },
  {
    group: 'Revenue Cycle',
    items: [
      { name: 'Claims',      href: '/claims',       icon: FileText,      iconColor: 'text-sky-400' },
      { name: 'Work Queues', href: '/work-queues',  icon: FolderKanban,  iconColor: 'text-purple-400' },
      { name: 'Denials',     href: '/denials',      icon: AlertTriangle, iconColor: 'text-amber-400' },
      { name: 'Payments',    href: '/payments',     icon: CreditCard,    iconColor: 'text-emerald-400' },
    ],
  },
  {
    group: 'AI Agents',
    items: [
      { name: 'Agents',      href: '/agents',       icon: Bot,           iconColor: 'text-fuchsia-400' },
      { name: 'Assistant',   href: '/assistant',    icon: Sparkles,      iconColor: 'text-indigo-300' },
    ],
  },
  {
    group: 'Administration',
    items: [
      { name: 'Users',       href: '/users',        icon: Users,         iconColor: 'text-slate-400' },
    ],
  },
];

// ── User initials avatar ──────────────────────────────────────────────────────
function UserAvatar({ name, size = 'sm' }: { name?: string; size?: 'sm' | 'md' }) {
  const initials = name
    ? name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U';
  return (
    <div className={cn(
      'rounded-full bg-blue-600 flex items-center justify-center',
      'font-bold text-white flex-shrink-0 shadow-xs border border-blue-400/30',
      size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm',
    )}>
      {initials}
    </div>
  );
}

// ── Role display ──────────────────────────────────────────────────────────────
function formatRole(role: string) {
  return role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ── Sidebar Component ─────────────────────────────────────────────────────────
function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs lg:hidden animate-fade-in"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel — Dark Navy Theme */}
      <aside className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 flex flex-col',
        'bg-[#132c4a] border-r border-[#1e3e66] shadow-xl',
        'transform transition-transform duration-250 ease-spring',
        'lg:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full',
      )}>
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-[#1e3e66] bg-[#0f243d] flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center flex-shrink-0 shadow-md">
              <Activity className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <span className="text-base font-bold text-white tracking-tight">NovaArc</span>
              <span className="ml-1.5 text-2xs font-bold bg-blue-900/60 text-blue-300 px-1.5 py-0.5 rounded uppercase tracking-wider border border-blue-700/50">
                RCM
              </span>
            </div>
          </div>
          <button
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 overflow-y-auto sidebar-scroll scrollbar-thin space-y-5">
          {navigation.map((group) => (
            <div key={group.group}>
              <p className="text-2xs font-bold text-slate-400/90 uppercase tracking-wider px-3 mb-2">
                {group.group}
              </p>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    onClick={onClose}
                    className={({ isActive }) => cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium',
                      'transition-all duration-150 cursor-pointer select-none group',
                      isActive
                        ? 'bg-blue-600 text-white font-semibold shadow-md'
                        : 'text-slate-300 hover:bg-white/10 hover:text-white',
                    )}
                  >
                    {({ isActive }) => (
                      <>
                        <item.icon className={cn(
                          'w-4.5 h-4.5 flex-shrink-0 transition-colors',
                          isActive ? 'text-white' : item.iconColor,
                        )} style={{ width: '1.125rem', height: '1.125rem' }} />
                        <span className="truncate">{item.name}</span>
                        {isActive && (
                          <span className="ml-auto w-1.5 h-1.5 rounded-full bg-white" />
                        )}
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-3 border-t border-[#1e3e66] bg-[#0e2137] flex-shrink-0">
          <div className="flex items-center gap-3 px-2 py-2 rounded-xl bg-white/5 border border-white/5">
            <UserAvatar name={user?.name} size="sm" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user?.name || 'User'}</p>
              <p className="text-2xs text-slate-400 truncate">{formatRole(user?.role || '')}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-white/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

// ── Top Header Component ──────────────────────────────────────────────────────
function TopHeader({ onMenuClick }: { onMenuClick: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Close user menu on route change
  useEffect(() => { setUserMenuOpen(false); }, [location.pathname]);

  // Page title from route
  const pageTitle = location.pathname.replace('/', '').replace('-', ' ')
    .replace(/\b\w/g, c => c.toUpperCase()) || 'Dashboard';

  const handleLogout = () => {
    logout();
    navigate('/login');
    setUserMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-slate-200">
      <div className="flex items-center justify-between h-14 px-4 sm:px-6">
        {/* Left: hamburger + breadcrumb */}
        <div className="flex items-center gap-3">
          <button
            className="lg:hidden p-2 -ml-1 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            onClick={onMenuClick}
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 text-sm">
            <span className="hidden sm:block text-slate-400 font-medium">NovaArc RCM</span>
            <span className="hidden sm:block text-slate-300">/</span>
            <span className="font-semibold text-slate-800">{pageTitle}</span>
          </div>
        </div>

        {/* Right: user menu */}
        <div className="relative">
          <button
            id="user-menu-btn"
            className="flex items-center gap-2.5 px-2 py-1.5 rounded-xl hover:bg-slate-100 transition-colors"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
          >
            <UserAvatar name={user?.name} size="sm" />
            <div className="hidden sm:block text-left">
              <p className="text-sm font-semibold text-slate-800 leading-none">{user?.name}</p>
              <p className="text-2xs text-slate-500 mt-0.5">{formatRole(user?.role || '')}</p>
            </div>
            <ChevronDown className={cn(
              'w-4 h-4 text-slate-400 transition-transform duration-150',
              userMenuOpen && 'rotate-180',
            )} />
          </button>

          {userMenuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
              <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-dropdown border border-slate-200 py-2 z-50 animate-slide-down">
                <div className="px-4 py-2.5 border-b border-slate-100 mb-1">
                  <p className="text-sm font-semibold text-slate-900">{user?.name}</p>
                  <p className="text-xs text-slate-500">{formatRole(user?.role || '')}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-crimson-600 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

// ── Main Layout ───────────────────────────────────────────────────────────────
export function Layout({ children }: { children?: React.ReactNode } = {}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="lg:pl-64 flex flex-col min-h-screen">
        <TopHeader onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 animate-fade-in">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  );
}

// ── Login Page ─────────────────────────────────────────────────────────────────
export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const demoCredentials = [
    { role: 'Client Leadership', email: 'client_leadership@novaarc.local' },
    { role: 'Ops Manager',       email: 'ops_manager@novaarc.local'       },
    { role: 'AR Executive',      email: 'ar_executive@novaarc.local'      },
  ];

  return (
    <div className="min-h-screen flex">
      {/* ── Left Panel: Brand ─────────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-[52%] xl:w-[55%] bg-primary-700 flex-col relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.3) 0%, transparent 50%),
                              radial-gradient(circle at 75% 75%, rgba(255,255,255,0.2) 0%, transparent 50%)`,
          }}
        />
        <div className="absolute bottom-0 left-0 right-0 h-64 opacity-10"
          style={{
            background: 'linear-gradient(to top, rgba(255,255,255,0.15), transparent)',
          }}
        />

        {/* Content */}
        <div className="relative flex flex-col h-full px-10 py-10">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/80 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold text-white">NovaArc</span>
              <span className="ml-2 text-xs font-bold bg-white/15 text-white/80 px-2 py-0.5 rounded uppercase tracking-wider">
                RCM
              </span>
            </div>
          </div>

          {/* Hero text */}
          <div className="flex-1 flex flex-col justify-center max-w-sm">
            <div className="inline-flex items-center gap-2 bg-white/10 text-white/80 text-xs font-semibold px-3 py-1.5 rounded-full mb-6 w-fit">
              <Shield className="w-3.5 h-3.5" />
              HIPAA Compliant · SOC 2 Ready
            </div>
            <h1 className="text-4xl xl:text-5xl font-bold text-white leading-tight">
              Revenue Cycle
              <br />
              <span className="text-blue-300">Intelligence</span>
            </h1>
            <p className="mt-5 text-base text-slate-300 leading-relaxed">
              AI-powered claims management, denial automation, and real-time analytics — built for modern healthcare organizations.
            </p>

            {/* Feature list */}
            <div className="mt-8 space-y-3">
              {[
                { label: 'AI Medical Coding Assistant', desc: 'ICD-10 & CPT suggestions in seconds' },
                { label: 'Denial Intelligence',          desc: 'Predict and prevent claim denials' },
                { label: 'Automated Appeal Drafting',    desc: 'Payer-specific letter generation'  },
                { label: 'NL Analytics Assistant',       desc: 'Query your AR data in plain English' },
              ].map(f => (
                <div key={f.label} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-forest-500/80 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{f.label}</p>
                    <p className="text-xs text-slate-400">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} NovaArc Health Technologies. All rights reserved.
          </p>
        </div>
      </div>

      {/* ── Right Panel: Login Form ────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-slate-50">
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-2.5 mb-8">
          <div className="w-9 h-9 rounded-xl bg-primary-700 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-primary-700">NovaArc RCM</span>
        </div>

        <div className="w-full max-w-sm animate-slide-up">
          {/* Heading */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900">Welcome back</h2>
            <p className="mt-1.5 text-sm text-slate-500">
              Sign in to access your revenue cycle dashboard
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-5 flex items-start gap-3 bg-crimson-50 border border-crimson-200 text-crimson-700 px-4 py-3 rounded-xl text-sm animate-slide-down">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-email" className="label">Email address</label>
              <input
                id="login-email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input input-lg"
                placeholder="you@organization.com"
              />
            </div>

            <div>
              <label htmlFor="login-password" className="label">Password</label>
              <div className="relative">
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input input-lg pr-12"
                  placeholder="••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4.5 h-4.5" style={{width:'1.125rem',height:'1.125rem'}} /> : <Eye className="w-4.5 h-4.5" style={{width:'1.125rem',height:'1.125rem'}} />}
                </button>
              </div>
            </div>

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full btn-primary btn-lg mt-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z"/>
                  </svg>
                  Signing in…
                </>
              ) : 'Sign in'}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-8 p-4 bg-white border border-slate-200 rounded-xl">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Demo Access</p>
              <span className="text-xs text-slate-500">
                Password: <span className="font-mono font-bold text-slate-700 normal-case">password123</span>
              </span>
            </div>
            <div className="space-y-2">
              {demoCredentials.map(c => (
                <button
                  key={c.email}
                  type="button"
                  onClick={() => { setEmail(c.email); setPassword('password123'); }}
                  className="w-full flex items-center justify-between px-3 py-2 text-xs rounded-lg hover:bg-primary-50 border border-slate-100 hover:border-primary-200 transition-colors group"
                >
                  <span className="font-semibold text-slate-700">{c.role}</span>
                  <span className="font-mono text-slate-400 group-hover:text-primary-600 transition-colors">
                    {c.email.split('@')[0]}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}