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
  DollarSign, CreditCard, FileText, TrendingUp, AlertTriangle, Download, RefreshCw
} from 'lucide-react';
import { cn, formatCurrency, formatPercent, formatNumber } from '../lib/utils';
import { DashboardRevenueHealth, DashboardARHealth, DashboardPayerPerformance, DenialIntelligence, ClaimsSummary } from '../types';

export function DashboardPage() {
  const {  } = useAuth();
  const [revenueHealth, setRevenueHealth] = useState<DashboardRevenueHealth | null>(null);
  const [arHealth, setArHealth] = useState<DashboardARHealth | null>(null);
  const [payerPerformance, setPayerPerformance] = useState<DashboardPayerPerformance[]>([]);
  const [denialIntelligence, setDenialIntelligence] = useState<DenialIntelligence | null>(null);
  const [claimsSummary, setClaimsSummary] = useState<ClaimsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'revenue' | 'ar' | 'denials' | 'payers'>('revenue');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

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
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600">{error}</p>
        <button onClick={fetchData} className="mt-4 btn-primary">Retry</button>
      </div>
    );
  }

  const totalClaims = claimsSummary?.total_claims || 0;
  const statusBreakdown = claimsSummary?.by_status || [];

  return (
          <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
            <p className="text-slate-600">Revenue cycle management overview</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={fetchData} className="btn-secondary" disabled={loading}>
              <RefreshCw className={cn('w-4 h-4 mr-2', loading && 'animate-spin')} />
              Refresh
            </button>
            <button className="btn-secondary">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Outstanding AR"
            value={formatCurrency(revenueHealth?.ar_outstanding || 0)}
            change={-2.3}
            changeLabel="vs last month"
            icon={<DollarSign className="w-6 h-6" />}
            iconColor="bg-blue-100 text-blue-600"
            trend="down"
          />
          <MetricCard
            title="Collected (MTD)"
            value={formatCurrency(revenueHealth?.collected || 0)}
            change={5.1}
            changeLabel="vs last month"
            icon={<CreditCard className="w-6 h-6" />}
            iconColor="bg-green-100 text-green-600"
            trend="up"
          />
          <MetricCard
            title="Collection Rate"
            value={formatPercent(revenueHealth?.collection_rate || 0)}
            change={1.2}
            changeLabel="vs last month"
            icon={<TrendingUp className="w-6 h-6" />}
            iconColor="bg-purple-100 text-purple-600"
            trend="up"
          />
          <MetricCard
            title="Total Claims"
            value={formatNumber(totalClaims)}
            change={3.5}
            changeLabel="vs last month"
            icon={<FileText className="w-6 h-6" />}
            iconColor="bg-orange-100 text-orange-600"
            trend="up"
          />
        </div>

        <div className="border-b border-slate-200">
          <nav className="flex gap-1 px-1" aria-label="Dashboard tabs">
            <button
              onClick={() => setActiveTab('revenue')}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-t-lg transition-colors',
                activeTab === 'revenue'
                  ? 'bg-white text-primary-600 border-b-2 border-primary-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              )}
            >
              Revenue Health
            </button>
            <button
              onClick={() => setActiveTab('ar')}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-t-lg transition-colors',
                activeTab === 'ar'
                  ? 'bg-white text-primary-600 border-b-2 border-primary-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              )}
            >
              AR Health
            </button>
            <button
              onClick={() => setActiveTab('denials')}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-t-lg transition-colors',
                activeTab === 'denials'
                  ? 'bg-white text-primary-600 border-b-2 border-primary-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              )}
            >
              Denial Intelligence
            </button>
            <button
              onClick={() => setActiveTab('payers')}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-t-lg transition-colors',
                activeTab === 'payers'
                  ? 'bg-white text-primary-600 border-b-2 border-primary-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              )}
            >
              Payer Performance
            </button>
          </nav>
        </div>

        {activeTab === 'revenue' && revenueHealth && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>AR Aging Buckets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {Object.entries(revenueHealth.aging_buckets).map(([label, value]) => {
                    const total = revenueHealth.ar_outstanding || 1;
                    const percentage = (value / total) * 100;
                    let color = '#22c55e';
                    if (label.includes('30-60') || label.includes('60+')) color = '#f59e0b';
                    if (label.includes('90') || label.includes('120')) color = '#ef4444';
                    return (
                      <AgingBucket
                        key={label}
                        label={label}
                        value={value}
                        percentage={percentage}
                        color={color}
                      />
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Claims by Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {statusBreakdown.map((s) => (
                    <StatusBadge
                      key={s.status}
                      status={s.status}
                      count={s.count}
                      total={totalClaims}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'ar' && arHealth && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>AR by Payer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                        <th className="px-4 py-3">Payer</th>
                        <th className="px-4 py-3">AR Outstanding</th>
                        <th className="px-4 py-3">Claims</th>
                        <th className="px-4 py-3">Avg Days</th>
                      </tr>
                    </thead>
                    <tbody>
                      {arHealth.by_payer.map((p) => (
                        <tr key={p.payer_id} className="hover:bg-slate-50 border-b border-slate-100">
                          <td className="px-4 py-3 font-medium text-slate-900">{p.payer_name}</td>
                          <td className="px-4 py-3 text-slate-600">{formatCurrency(p.ar_outstanding)}</td>
                          <td className="px-4 py-3 text-slate-600">{formatNumber(p.claim_count)}</td>
                          <td className="px-4 py-3 text-slate-600">{p.avg_days_outstanding.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AR by Specialty</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                        <th className="px-4 py-3">Specialty</th>
                        <th className="px-4 py-3">AR Outstanding</th>
                        <th className="px-4 py-3">Claims</th>
                        <th className="px-4 py-3">Avg Days</th>
                      </tr>
                    </thead>
                    <tbody>
                      {arHealth.by_specialty.map((s) => (
                        <tr key={s.specialty} className="hover:bg-slate-50 border-b border-slate-100">
                          <td className="px-4 py-3 font-medium text-slate-900">{s.specialty}</td>
                          <td className="px-4 py-3 text-slate-600">{formatCurrency(s.ar_outstanding)}</td>
                          <td className="px-4 py-3 text-slate-600">{formatNumber(s.claim_count)}</td>
                          <td className="px-4 py-3 text-slate-600">{s.avg_days_outstanding.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'denials' && denialIntelligence && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Top Denial Codes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Count</th>
                        <th className="px-4 py-3">Total Denied</th>
                        <th className="px-4 py-3">Avg Denied</th>
                      </tr>
                    </thead>
                    <tbody>
                      {denialIntelligence.top_codes.map((c) => (
                        <DenialCodeRow key={c.denial_code} code={c} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Denials by Root Cause</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {denialIntelligence.by_root_cause.map((r) => (
                    <div key={r.root_cause} className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-slate-900">{r.root_cause}</p>
                        <p className="text-sm text-slate-500">{formatNumber(r.count)} denials • {formatCurrency(r.total_denied)}</p>
                      </div>
                      <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden ml-4">
                        <div
                          className="h-full bg-red-500 rounded-full"
                          style={{ width: `${Math.min((r.count / (denialIntelligence.by_root_cause[0]?.count || 1)) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'payers' && (
          <Card>
            <CardHeader>
              <CardTitle>Payer Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                      <th className="px-4 py-3">Payer</th>
                      <th className="px-4 py-3">Charged</th>
                      <th className="px-4 py-3">Paid</th>
                      <th className="px-4 py-3">Collection Rate</th>
                      <th className="px-4 py-3">Denial Rate</th>
                      <th className="px-4 py-3">Avg Days to Pay</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payerPerformance.map((p) => (
                      <PayerPerformanceRow key={p.payer_id} payer={p} />
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>);
}