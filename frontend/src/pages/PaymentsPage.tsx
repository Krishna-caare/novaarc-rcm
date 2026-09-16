import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { formatCurrency, formatDate, formatNumber } from '../lib/utils';
import { Payment } from '../types';
import { ChevronLeft, ChevronRight, Filter, Plus, Eye, CreditCard, DollarSign, TrendingUp, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

export function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [summary, setSummary] = useState<{total_payments: number; total_amount: number; by_payer: Array<{payer_id: number; count: number; total_amount: number}>} | null>(null);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [showViewPayment, setShowViewPayment] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, limit: 20 });
  const [filters, setFilters] = useState({ claim_id: '', payer_id: '', date_from: '', date_to: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [showPostPayment, setShowPostPayment] = useState(false);
  const [postPaymentLoading, setPostPaymentLoading] = useState(false);
  const [postPaymentError, setPostPaymentError] = useState<string | null>(null);
  const [payers, setPayers] = useState<Array<{ payer_id: number; name: string }>>([]);

  const [postPaymentForm, setPostPaymentForm] = useState({
    claim_id: '',
    amount: '',
    payer_id: '',
    posted_date: new Date().toISOString().split('T')[0],
    remittance_ref: '',
  });

  useEffect(() => {
    fetchPayments();
    fetchSummary();
  }, [pagination.page, filters.claim_id, filters.payer_id, filters.date_from, filters.date_to]);

  useEffect(() => {
    const loadPayers = async () => {
      try {
        const data = await api.getReferenceData();
        if (data.payers) {
          setPayers(data.payers);
          if (data.payers.length > 0) {
            setPostPaymentForm(prev => ({
              ...prev,
              payer_id: prev.payer_id || String(data.payers[0].payer_id),
            }));
          }
        }
      } catch (e) {
        console.warn('Failed to load payers', e);
      }
    };
    loadPayers();
  }, []);

  const handlePostPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setPostPaymentError(null);
    if (!postPaymentForm.claim_id || !postPaymentForm.amount || !postPaymentForm.payer_id) {
      setPostPaymentError('Please fill in Claim ID, Amount, and Payer');
      return;
    }
    const amt = parseFloat(postPaymentForm.amount);
    if (isNaN(amt) || amt <= 0) {
      setPostPaymentError('Please enter a valid positive payment amount');
      return;
    }
    setPostPaymentLoading(true);
    try {
      const remRef = postPaymentForm.remittance_ref.trim() || `RMT${Math.floor(100000 + Math.random() * 900000)}`;
      await api.createPayment({
        claim_id: parseInt(postPaymentForm.claim_id),
        amount: amt,
        payer_id: parseInt(postPaymentForm.payer_id),
        posted_date: postPaymentForm.posted_date || undefined,
        remittance_ref: remRef,
      });
      setShowPostPayment(false);
      setPostPaymentForm({
        claim_id: '',
        amount: '',
        payer_id: payers[0] ? String(payers[0].payer_id) : '',
        posted_date: new Date().toISOString().split('T')[0],
        remittance_ref: '',
      });
      await fetchPayments();
      await fetchSummary();
    } catch (err: any) {
      setPostPaymentError(err.response?.data?.detail || 'Failed to post payment');
    } finally {
      setPostPaymentLoading(false);
    }
  };

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
            <button onClick={() => setShowPostPayment(true)} className="btn-primary">
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
                  <tr className="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                    <th className="px-4 py-3">Payment ID</th>
                    <th className="px-4 py-3">Claim</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Posted Date</th>
                    <th className="px-4 py-3">Remittance Ref</th>
                    <th className="px-4 py-3">Payer</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {payments.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-12 text-center text-slate-500">
                        No payments found
                      </td>
                    </tr>
                  ) : (
                    payments.map((payment) => (
                      <tr key={payment.payment_id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3 font-mono font-semibold text-slate-900">PMT-{payment.payment_id}</td>
                        <td className="px-4 py-3 text-blue-600 font-mono font-medium">CLM-{payment.claim_id}</td>
                        <td className="px-4 py-3 font-semibold text-emerald-700">{formatCurrency(payment.amount)}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(payment.posted_date)}</td>
                        <td className="px-4 py-3 text-slate-600 font-mono text-xs">{payment.remittance_ref || 'N/A'}</td>
                        <td className="px-4 py-3 text-slate-700 font-medium">
                          {payers.find(p => p.payer_id === payment.payer_id)?.name || `Payer #${payment.payer_id}`}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              setSelectedPayment(payment);
                              setShowViewPayment(true);
                            }}
                            className="p-1.5 rounded-lg hover:bg-blue-50 text-slate-400 hover:text-blue-600 transition-colors inline-flex items-center justify-center"
                            title="View Payment Details"
                          >
                            <Eye className="w-4.5 h-4.5" />
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

        {summary && summary.by_payer.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Payments by Payer</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                      <th className="px-4 py-3">Payer ID</th>
                      <th className="px-4 py-3">Payment Count</th>
                      <th className="px-4 py-3">Total Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {summary.by_payer.map((p) => (
                      <tr key={p.payer_id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3 text-slate-700 font-medium">Payer {p.payer_id}</td>
                        <td className="px-4 py-3 text-slate-600">{formatNumber(p.count)}</td>
                        <td className="px-4 py-3 font-semibold text-emerald-700">{formatCurrency(p.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {showPostPayment && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-xl max-w-md w-full shadow-2xl overflow-y-auto max-h-[90vh]">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="font-semibold text-lg text-slate-900">Post New Payment</h3>
                <button onClick={() => setShowPostPayment(false)} className="p-2 hover:bg-slate-100 rounded text-slate-500">✕</button>
              </div>
              <form onSubmit={handlePostPayment} className="p-4 space-y-4">
                {postPaymentError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
                    {postPaymentError}
                  </div>
                )}
                <div>
                  <label className="label">Claim ID *</label>
                  <input
                    type="number"
                    placeholder="e.g. 52"
                    className="input"
                    value={postPaymentForm.claim_id}
                    onChange={e => setPostPaymentForm({ ...postPaymentForm, claim_id: e.target.value })}
                    required
                  />
                  <p className="text-xs text-slate-500 mt-1">Enter the Claim ID number (e.g. 52 for CLM-52)</p>
                </div>

                <div>
                  <label className="label">Payment Amount ($) *</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="e.g. 1500.00"
                    className="input"
                    value={postPaymentForm.amount}
                    onChange={e => setPostPaymentForm({ ...postPaymentForm, amount: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="label">Payer *</label>
                  {payers.length > 0 ? (
                    <select
                      className="input"
                      value={postPaymentForm.payer_id}
                      onChange={e => setPostPaymentForm({ ...postPaymentForm, payer_id: e.target.value })}
                      required
                    >
                      {payers.map(p => (
                        <option key={p.payer_id} value={p.payer_id}>
                          {p.name} (ID: {p.payer_id})
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      placeholder="Payer ID (e.g. 1)"
                      className="input"
                      value={postPaymentForm.payer_id}
                      onChange={e => setPostPaymentForm({ ...postPaymentForm, payer_id: e.target.value })}
                      required
                    />
                  )}
                </div>

                <div>
                  <label className="label">Posted Date *</label>
                  <input
                    type="date"
                    className="input"
                    value={postPaymentForm.posted_date}
                    onChange={e => setPostPaymentForm({ ...postPaymentForm, posted_date: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="label">Remittance Reference (optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. RMT482910 (auto-generated if blank)"
                    className="input"
                    value={postPaymentForm.remittance_ref}
                    onChange={e => setPostPaymentForm({ ...postPaymentForm, remittance_ref: e.target.value })}
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t">
                  <button type="button" onClick={() => setShowPostPayment(false)} className="btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" disabled={postPaymentLoading} className="btn-primary">
                    {postPaymentLoading ? 'Posting...' : 'Post Payment'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
        {/* ── View Payment Modal ────────────────────────────────────── */}
        {showViewPayment && selectedPayment && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-fade-in">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden flex flex-col border border-slate-200 animate-slide-up">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    <CreditCard className="w-4.5 h-4.5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Payment Details</h3>
                    <p className="font-mono text-xs text-slate-500">PMT-{selectedPayment.payment_id}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowViewPayment(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-4 text-xs">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
                  <span className="text-slate-500 font-medium">Payment Amount</span>
                  <span className="text-lg font-bold text-emerald-600">
                    {formatCurrency(selectedPayment.amount)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <p className="text-2xs font-semibold text-slate-400 uppercase">Claim ID</p>
                    <p className="font-mono font-bold text-blue-600 mt-1">CLM-{selectedPayment.claim_id}</p>
                  </div>
                  <div className="p-3 bg-white border border-slate-200 rounded-lg">
                    <p className="text-2xs font-semibold text-slate-400 uppercase">Posted Date</p>
                    <p className="font-medium text-slate-800 mt-1">{formatDate(selectedPayment.posted_date)}</p>
                  </div>
                </div>

                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Remittance Reference</p>
                  <p className="font-mono font-medium text-slate-900 mt-1">{selectedPayment.remittance_ref || 'N/A'}</p>
                </div>

                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Payer</p>
                  <p className="font-medium text-slate-900 mt-1">
                    {payers.find(p => p.payer_id === selectedPayment.payer_id)?.name || `Payer ID #${selectedPayment.payer_id}`}
                  </p>
                </div>
              </div>

              <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/70 flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowViewPayment(false)}
                  className="btn-secondary text-xs"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>);
}