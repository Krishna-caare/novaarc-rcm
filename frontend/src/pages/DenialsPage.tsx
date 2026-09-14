import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { formatCurrency, formatDate, formatNumber } from '../lib/utils';
import { Denial, AppealStatus } from '../types';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

export function DenialsPage() {
  const [denials, setDenials] = useState<Denial[]>([]);
  const [topCodes, setTopCodes] = useState<Array<{denial_code: string; count: number; total_denied: number; avg_denied: number}>>([]);
  const [loading, setLoading] = useState(false);
  const [codesLoading, setCodesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 20 });
  const [selectedDenial, setSelectedDenial] = useState<Denial | null>(null);
  const [appealDraft, setAppealDraft] = useState<string>('');
  const [draftingAppeal, setDraftingAppeal] = useState(false);
  const [appealContext, setAppealContext] = useState('');

  useEffect(() => {
    fetchDenials();
    fetchTopCodes();
  }, [pagination.page]);

  const fetchDenials = async () => {
    setLoading(true);
    try {
      const data = await api.listDenials({ skip: (pagination.page - 1) * pagination.limit, limit: pagination.limit });
      setDenials(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load denials');
    } finally {
      setLoading(false);
    }
  };

  const fetchTopCodes = async () => {
    setCodesLoading(true);
    try {
      const data = await api.getTopDenialCodes(15);
      setTopCodes(data);
    } catch (err) {
      console.error('Failed to load top codes', err);
    } finally {
      setCodesLoading(false);
    }
  };

  const handleDraftAppeal = async (denial: Denial) => {
    setSelectedDenial(denial);
    setDraftingAppeal(true);
    try {
      const result = await api.draftAppeal(denial.denial_id, appealContext);
      setAppealDraft(result.appeal_letter);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to draft appeal');
    } finally {
      setDraftingAppeal(false);
    }
  };

  const handleAppealContextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setAppealContext(e.target.value);
  };

  const closeAppealModal = () => {
    setSelectedDenial(null);
    setAppealDraft('');
    setAppealContext('');
  };

  const formatAppealStatus = (status: AppealStatus) => {
    const labels: Record<AppealStatus, string> = {
      not_started: 'Not Started',
      drafted: 'Drafted',
      submitted: 'Submitted',
      won: 'Won',
      lost: 'Lost',
    };
    return labels[status] || status;
  };

  const getAppealStatusBadge = (status: AppealStatus) => {
    const badges: Record<AppealStatus, string> = {
      not_started: 'badge-neutral',
      drafted: 'badge-info',
      submitted: 'badge-warning',
      won: 'badge-success',
      lost: 'badge-danger',
    };
    return badges[status] || 'badge-neutral';
  };

  return (
          <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Denials</h1>
            <p className="text-slate-600">Track and manage claim denials</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Denial List</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50 text-left text-sm text-slate-500 border-b border-slate-200">
                        <th className="px-4 py-3">Denial ID</th>
                        <th className="px-4 py-3">Claim</th>
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Description</th>
                        <th className="px-4 py-3">Denied Amt</th>
                        <th className="px-4 py-3">Date</th>
                        <th className="px-4 py-3">Root Cause</th>
                        <th className="px-4 py-3">Appeal Status</th>
                        <th className="px-4 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {denials.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="px-4 py-12 text-center text-slate-500">
                            No denials found
                          </td>
                        </tr>
                      ) : (
                        denials.map((denial) => (
                          <tr key={denial.denial_id} className="hover:bg-slate-50 border-b border-slate-100">
                            <td className="px-4 py-3 font-mono text-sm text-slate-900">DNL-{denial.denial_id}</td>
                            <td className="px-4 py-3 text-slate-600">CLM-{denial.claim_id}</td>
                            <td className="px-4 py-3 font-mono text-sm text-slate-900">{denial.denial_code || 'N/A'}</td>
                            <td className="px-4 py-3 text-slate-600 max-w-xs truncate">
                              {denial.description || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-slate-600">{formatCurrency(denial.denied_amount || 0)}</td>
                            <td className="px-4 py-3 text-slate-600">{formatDate(denial.denial_date)}</td>
                            <td className="px-4 py-3 text-slate-600">{denial.root_cause || 'N/A'}</td>
                            <td className="px-4 py-3">
                              <span className={getAppealStatusBadge(denial.appeal_status)}>
                                {formatAppealStatus(denial.appeal_status)}
                              </span>
                              {denial.appeal_drafted_by_ai && (
                                <span className="ml-1 px-1.5 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">AI</span>
                              )}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => handleDraftAppeal(denial)}
                                  disabled={draftingAppeal}
                                  className="btn-primary text-sm px-3 py-1"
                                >
                                  {draftingAppeal ? 'Drafting...' : 'Draft Appeal'}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
                  <p className="text-sm text-slate-600">Showing {denials.length} denials</p>
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
                      disabled={denials.length < pagination.limit || loading}
                      className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader>
                <CardTitle>Top Denial Codes</CardTitle>
              </CardHeader>
              <CardContent>
                {codesLoading ? (
                  <div className="space-y-3">
                    {[1,2,3,4,5].map(i => (
                      <div key={i} className="h-12 bg-slate-100 rounded animate-pulse" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {topCodes.slice(0, 10).map((code, index) => (
                      <div key={code.denial_code} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-slate-500">{index + 1}.</span>
                          <div>
                            <p className="font-mono font-medium text-slate-900">{code.denial_code}</p>
                            <p className="text-xs text-slate-500">{formatNumber(code.count)} denials</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-slate-900">{formatCurrency(code.total_denied)}</p>
                          <p className="text-xs text-slate-500">Avg: {formatCurrency(code.avg_denied)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {selectedDenial && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
              <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Appeal Letter Draft</h2>
                <button onClick={closeAppealModal} className="p-2 rounded-lg hover:bg-slate-100">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              
              <div className="p-4 border-b border-slate-200">
                <label className="label">Additional Context (optional)</label>
                <textarea
                  value={appealContext}
                  onChange={handleAppealContextChange}
                  rows={3}
                  className="input"
                  placeholder="Add any additional context for the appeal..."
                />
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                <div className="prose max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{appealDraft}</pre>
                </div>
              </div>

              <div className="p-4 border-t border-slate-200 flex justify-end gap-2">
                <button onClick={closeAppealModal} className="btn-secondary">
                  Close
                </button>
                <button className="btn-primary">
                  Copy to Clipboard
                </button>
              </div>
            </div>
          </div>
        )}
      </div>);
}