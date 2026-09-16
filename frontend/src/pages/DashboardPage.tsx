import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import {
  MetricCard,
  StatusBadge,
  AgingBucket,
  PayerPerformanceRow,
  DenialCodeRow,
} from '../components/DashboardComponents';
import {
  DollarSign, CreditCard, FileText, TrendingUp, AlertTriangle,
  Download, RefreshCw, Activity,
} from 'lucide-react';
import { cn, formatCurrency, formatPercent, formatNumber } from '../lib/utils';
import {
  DashboardRevenueHealth, DashboardARHealth,
  DashboardPayerPerformance, DenialIntelligence, ClaimsSummary,
} from '../types';

type Tab = 'revenue' | 'ar' | 'denials' | 'payers';
const TABS: { id: Tab; label: string }[] = [
  { id: 'revenue', label: 'Revenue Health'      },
  { id: 'ar',      label: 'AR Health'           },
  { id: 'denials', label: 'Denial Intelligence' },
  { id: 'payers',  label: 'Payer Performance'   },
];

// ── Skeleton Loaders ──────────────────────────────────────────────────────────
function MetricSkeleton() {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="skeleton-text w-24" />
          <div className="skeleton h-8 rounded w-32" />
          <div className="skeleton-text w-20" />
        </div>
        <div className="skeleton w-12 h-12 rounded-xl" />
      </div>
    </div>
  );
}

function TableSkeleton({ rows = 5 }) {
  return (
    <div className="space-y-0">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-slate-100">
          <div className="skeleton-text flex-1" />
          <div className="skeleton-text w-24" />
          <div className="skeleton-text w-16" />
          <div className="skeleton-text w-20" />
        </div>
      ))}
    </div>
  );
}

// ── Main Dashboard Page ───────────────────────────────────────────────────────
export function DashboardPage() {
  const { user } = useAuth();
  const [revenueHealth, setRevenueHealth] = useState<DashboardRevenueHealth | null>(null);
  const [arHealth, setArHealth] = useState<DashboardARHealth | null>(null);
  const [payerPerformance, setPayerPerformance] = useState<DashboardPayerPerformance[]>([]);
  const [denialIntelligence, setDenialIntelligence] = useState<DenialIntelligence | null>(null);
  const [claimsSummary, setClaimsSummary] = useState<ClaimsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('revenue');
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rev, ar, payers, denials, claims] = await Promise.all([
        api.getRevenueHealth(),
        api.getARHealth(),
        api.getPayerPerformance(),
        api.getDenialIntelligence(),
        api.getClaimsSummary(),
      ]);
      setRevenueHealth(rev);
      setArHealth(ar);
      setPayerPerformance(payers);
      setDenialIntelligence(denials);
      setClaimsSummary(claims);
      setLastRefreshed(new Date());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const totalClaims    = claimsSummary?.total_claims || 0;
  const statusBreakdown = claimsSummary?.by_status || [];

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  })();

  return (
    <div className="space-y-6">
      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="page-title">
            {greeting}{user?.name ? `, ${user.name.split(' ')[0]}` : ''} 👋
          </h1>
          <p className="page-subtitle mt-1">
            Revenue cycle overview · Last updated {lastRefreshed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="btn-secondary"
          >
            <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            Refresh
          </button>
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* ── Error State ─────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 bg-crimson-50 border border-crimson-200 text-crimson-700 px-5 py-4 rounded-xl">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-medium">Failed to load dashboard</p>
            <p className="text-sm text-crimson-600">{error}</p>
          </div>
          <button onClick={fetchData} className="btn-danger btn-sm">Retry</button>
        </div>
      )}

      {/* ── Metric Cards ─────────────────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <MetricSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Outstanding AR"
            value={formatCurrency(revenueHealth?.ar_outstanding || 0)}
            change={-2.3}
            changeLabel="vs last month"
            icon={<DollarSign className="w-5 h-5" />}
            iconBg="bg-blue-100 text-blue-600"
            trend="down"
            accent="blue"
          />
          <MetricCard
            title="Collected (MTD)"
            value={formatCurrency(revenueHealth?.collected || 0)}
            change={5.1}
            changeLabel="vs last month"
            icon={<CreditCard className="w-5 h-5" />}
            iconBg="bg-forest-100 text-forest-600"
            trend="up"
            accent="green"
          />
          <MetricCard
            title="Collection Rate"
            value={formatPercent(revenueHealth?.collection_rate || 0)}
            change={1.2}
            changeLabel="vs last month"
            icon={<TrendingUp className="w-5 h-5" />}
            iconBg="bg-violet-100 text-violet-600"
            trend="up"
            accent="purple"
          />
          <MetricCard
            title="Total Claims"
            value={formatNumber(totalClaims)}
            change={3.5}
            changeLabel="vs last month"
            icon={<FileText className="w-5 h-5" />}
            iconBg="bg-amber-100 text-amber-600"
            trend="up"
            accent="amber"
          />
        </div>
      )}

      {/* ── Tabs ─────────────────────────────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-card border border-slate-200 overflow-hidden">
        {/* Tab bar */}
        <div className="border-b border-slate-200 px-4">
          <nav className="flex gap-0 -mb-px" aria-label="Dashboard tabs">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'px-4 py-3.5 text-sm font-medium border-b-2 transition-all duration-150 whitespace-nowrap',
                  activeTab === tab.id
                    ? 'border-primary-700 text-primary-700 bg-primary-50/30'
                    : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300',
                )}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        <div className="p-6 animate-fade-in">
          {loading && <TableSkeleton rows={6} />}

          {/* Revenue Health Tab */}
          {!loading && activeTab === 'revenue' && revenueHealth && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* AR Aging Buckets */}
              <div className="lg:col-span-2 space-y-2">
                <div className="flex items-center gap-2 mb-5">
                  <Activity className="w-4 h-4 text-primary-600" />
                  <h3 className="font-semibold text-slate-800 text-sm">AR Aging Buckets</h3>
                </div>
                <div className="space-y-5">
                  {Object.entries(revenueHealth.aging_buckets).map(([label, value]) => {
                    const total = revenueHealth.ar_outstanding || 1;
                    const pct   = (value / total) * 100;
                    let color   = '#059669';
                    if (label.includes('30-60') || label.includes('60+'))    color = '#D97706';
                    if (label.includes('90') || label.includes('120'))       color = '#DC2626';
                    return (
                      <AgingBucket
                        key={label}
                        label={label}
                        value={value}
                        percentage={pct}
                        color={color}
                      />
                    );
                  })}
                </div>

                {/* KPI row */}
                <div className="mt-6 grid grid-cols-3 gap-4 pt-5 border-t border-slate-100">
                  {[
                    { label: 'Gross Charges',    value: formatCurrency(revenueHealth.gross_charges || 0) },
                    { label: 'Adjustments',      value: formatCurrency(revenueHealth.adjustments   || 0) },
                    { label: 'Net Collections',  value: formatCurrency(revenueHealth.collected      || 0) },
                  ].map(kpi => (
                    <div key={kpi.label} className="text-center">
                      <p className="text-lg font-bold text-slate-900">{kpi.value}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{kpi.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Claims by Status */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="w-4 h-4 text-primary-600" />
                  <h3 className="font-semibold text-slate-800 text-sm">Claims by Status</h3>
                </div>
                <div className="space-y-1">
                  {statusBreakdown.map((s) => (
                    <StatusBadge
                      key={s.status}
                      status={s.status}
                      count={s.count}
                      total={totalClaims}
                    />
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-slate-100 text-center">
                  <p className="text-2xl font-bold text-slate-900">{formatNumber(totalClaims)}</p>
                  <p className="text-xs text-slate-500">Total Claims</p>
                </div>
              </div>
            </div>
          )}

          {/* AR Health Tab */}
          {!loading && activeTab === 'ar' && arHealth && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-slate-800 text-sm mb-4">AR by Payer</h3>
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Payer</th>
                        <th>AR Outstanding</th>
                        <th>Claims</th>
                        <th>Avg Days</th>
                      </tr>
                    </thead>
                    <tbody>
                      {arHealth.by_payer.map((p) => (
                        <tr key={p.payer_id}>
                          <td className="font-medium text-slate-900">{p.payer_name}</td>
                          <td className="font-mono text-sm">{formatCurrency(p.ar_outstanding)}</td>
                          <td>{formatNumber(p.claim_count)}</td>
                          <td>{p.avg_days_outstanding.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 text-sm mb-4">AR by Specialty</h3>
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Specialty</th>
                        <th>AR Outstanding</th>
                        <th>Claims</th>
                        <th>Avg Days</th>
                      </tr>
                    </thead>
                    <tbody>
                      {arHealth.by_specialty.map((s) => (
                        <tr key={s.specialty}>
                          <td className="font-medium text-slate-900">{s.specialty}</td>
                          <td className="font-mono text-sm">{formatCurrency(s.ar_outstanding)}</td>
                          <td>{formatNumber(s.claim_count)}</td>
                          <td>{s.avg_days_outstanding.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Denial Intelligence Tab */}
          {!loading && activeTab === 'denials' && denialIntelligence && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-slate-800 text-sm mb-4">Top Denial Codes</h3>
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Count</th>
                        <th>Total Denied</th>
                        <th>Avg Denied</th>
                      </tr>
                    </thead>
                    <tbody>
                      {denialIntelligence.top_codes.map((c) => (
                        <DenialCodeRow key={c.denial_code} code={c} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-slate-800 text-sm mb-4">Denials by Root Cause</h3>
                <div className="space-y-4">
                  {denialIntelligence.by_root_cause.map((r) => {
                    const pct = Math.min(
                      (r.count / (denialIntelligence.by_root_cause[0]?.count || 1)) * 100,
                      100,
                    );
                    return (
                      <div key={r.root_cause}>
                        <div className="flex items-center justify-between text-sm mb-1.5">
                          <span className="font-medium text-slate-800">{r.root_cause}</span>
                          <span className="text-slate-500">
                            {formatNumber(r.count)} · {formatCurrency(r.total_denied)}
                          </span>
                        </div>
                        <div className="progress-bar">
                          <div
                            className="progress-fill bg-crimson-400"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Payer Performance Tab */}
          {!loading && activeTab === 'payers' && (
            <div>
              <h3 className="font-semibold text-slate-800 text-sm mb-4">Payer Performance Overview</h3>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Payer</th>
                      <th>Charged</th>
                      <th>Paid</th>
                      <th>Collection Rate</th>
                      <th>Denial Rate</th>
                      <th>Avg Days to Pay</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payerPerformance.map((p) => (
                      <PayerPerformanceRow key={p.payer_id} payer={p} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}