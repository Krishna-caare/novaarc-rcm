import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { formatCurrency, formatDate, formatNumber } from '../lib/utils';
import { Payment } from '../types';
import { ChevronLeft, ChevronRight, Filter, Plus, Eye, CreditCard, DollarSign, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

export function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [summary, setSummary] = useState<{total_payments: number; total_amount: number; by_payer: Array<{payer_id: number; count: number; total_amount: number}>} | null>(null);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 20 });
  const [filters, setFilters] = useState({ claim_id: '', payer_id: '', date_from: '', date_to: '' });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchPayments();
    fetchSummary();
  }, [pagination.page, filters.claim_id, filters.payer_id, filters.date_from, filters.date_to]);

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const params = {
        claim_id: filters.claim_id ? parseInt(filters.claim_id) : undefined,
        payer_id: filters.payer_id ? parseInt(filters.payer_id) : undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
        skip: (pagination.page - 1) * pagination.limit,
        limit: pagination.limit,
      };
      const data = await api.listPayments(params);
      setPayments(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    setSummaryLoading(true);
    try {
      const data = await api.getPaymentsSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load payment summary', err);
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  return (
          <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Payments</h1>
            <p className="text-slate-600">Track and manage payment postings</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowFilters(!showFilters)} className="btn-secondary">
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
            <button className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              Post Payment
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {showFilters && (
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div>
                  <label className="label">Claim ID</label>
                  <input
                    type="number"
                    value={filters.claim_id}
                    onChange={(e) => handleFilterChange('claim_id', e.target.value)}
                    className="input"
                    placeholder="Claim ID"
                  />
                </div>
                <div>
                  <label className="label">Date From</label>
                  <input
                    type="date"
                    value={filters.date_from}
                    onChange={(e) => handleFilterChange('date_from', e.target.value)}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Date To</label>
                  <input
                    type="date"
                    value={filters.date_to}
                    onChange={(e) => handleFilterChange('date_to', e.target.value)}
                    className="input"
                  />
                </div>
                <div className="flex items-end">
                  <button onClick={() => { setFilters({ claim_id: '', payer_id: '', date_from: '', date_to: '' }); setPagination(prev => ({ ...prev, page: 1 })); }} className="btn-secondary w-full">
                    Clear Filters
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Total Payments</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">{formatNumber(summary?.total_payments || 0)}</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-100 text-blue-600">
                  <CreditCard className="w-6 h-6" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Total Amount</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">{formatCurrency(summary?.total_amount || 0)}</p>
                </div>
                <div className="p-3 rounded-lg bg-green-100 text-green-600">
                  <DollarSign className="w-6 h-6" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Avg Payment</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">
                    {summary && summary.total_payments > 0 ? formatCurrency(summary.total_amount / summary.total_payments) : '$0.00'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-purple-100 text-purple-600">
                  <TrendingUp className="w-6 h-6" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Unique Payers</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">{summary?.by_payer?.length || 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-orange-100 text-orange-600">
                  <DollarSign className="w-6 h-6" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50 text-left text-sm text-slate-500 border-b border-slate-200">
                    <th className="px-4 py-3">Payment ID</th>
                    <th className="px-4 py-3">Claim</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Posted Date</th>
                    <th className="px-4 py-3">Remittance Ref</th>
                    <th className="px-4 py-3">Payer</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-12 text-center text-slate-500">
                        No payments found
                      </td>
                    </tr>
                  ) : (
                    payments.map((payment) => (
                      <tr key={payment.payment_id} className="hover:bg-slate-50 border-b border-slate-100">
                        <td className="px-4 py-3 font-mono text-sm text-slate-900">PMT-{payment.payment_id}</td>
                        <td className="px-4 py-3 text-slate-600">CLM-{payment.claim_id}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{formatCurrency(payment.amount)}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(payment.posted_date)}</td>
                        <td className="px-4 py-3 text-slate-600 font-mono text-sm">{payment.remittance_ref || 'N/A'}</td>
                        <td className="px-4 py-3 text-slate-600">Payer {payment.payer_id}</td>
                        <td className="px-4 py-3">
                          <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-500" title="View">
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
              <p className="text-sm text-slate-600">Showing {payments.length} payments</p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.page === 1 || loading}
                  className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-slate-600">Page {pagination.page}</span>
                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={payments.length < pagination.limit || loading}
                  className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {summary?.by_payer && summary.by_payer.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Payments by Payer</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                      <th className="px-4 py-3">Payer ID</th>
                      <th className="px-4 py-3">Payment Count</th>
                      <th className="px-4 py-3">Total Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.by_payer.map((p) => (
                      <tr key={p.payer_id} className="hover:bg-slate-50 border-b border-slate-100">
                        <td className="px-4 py-3 text-slate-600">Payer {p.payer_id}</td>
                        <td className="px-4 py-3 text-slate-600">{formatNumber(p.count)}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{formatCurrency(p.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>);
}