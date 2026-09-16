import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { formatCurrency, formatDate, formatNumber } from '../lib/utils';
import { Denial, AppealStatus } from '../types';
import { 
  ChevronLeft, ChevronRight, Sparkles, Copy, Check, X, 
  AlertTriangle, ShieldAlert, FileText, CheckCircle2, 
  RefreshCw, TrendingUp, DollarSign, Bot, ArrowRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

interface TopCodeItem {
  denial_code: string;
  count: number;
  total_denied?: number;
  total_denied_amount?: number;
  avg_denied?: number;
  avg_denied_amount?: number;
}

export function DenialsPage() {
  const [denials, setDenials] = useState<Denial[]>([]);
  const [topCodes, setTopCodes] = useState<TopCodeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [codesLoading, setCodesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 20 });
  const [selectedDenial, setSelectedDenial] = useState<Denial | null>(null);
  const [appealDraft, setAppealDraft] = useState<string>('');
  const [draftingAppeal, setDraftingAppeal] = useState(false);
  const [activeDraftingId, setActiveDraftingId] = useState<number | null>(null);
  const [appealContext, setAppealContext] = useState('');
  const [copied, setCopied] = useState(false);
  const [filterCode, setFilterCode] = useState<string | null>(null);
  const [aiLoadingStep, setAiLoadingStep] = useState(0);

  useEffect(() => {
    fetchDenials();
    fetchTopCodes();
  }, [pagination.page]);

  // AI loading step ticker animation
  useEffect(() => {
    if (!draftingAppeal) return;
    const interval = setInterval(() => {
      setAiLoadingStep((prev) => (prev + 1) % 3);
    }, 1400);
    return () => clearInterval(interval);
  }, [draftingAppeal]);

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
    setActiveDraftingId(denial.denial_id);
    setAppealDraft('');
    setCopied(false);
    setAiLoadingStep(0);

    try {
      const result = await api.draftAppeal(denial.denial_id, appealContext);
      setAppealDraft(result.appeal_letter || '');
      // Update local denial status so table reflects AI drafted badge immediately
      setDenials((prev) =>
        prev.map((d) =>
          d.denial_id === denial.denial_id
            ? { ...d, appeal_status: 'drafted', appeal_drafted_by_ai: true }
            : d
        )
      );
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to draft appeal letter');
    } finally {
      setDraftingAppeal(false);
      setActiveDraftingId(null);
    }
  };

  const handleRegenerateAppeal = async () => {
    if (!selectedDenial) return;
    setDraftingAppeal(true);
    setCopied(false);
    setAiLoadingStep(0);
    try {
      const result = await api.draftAppeal(selectedDenial.denial_id, appealContext);
      setAppealDraft(result.appeal_letter || '');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to regenerate appeal');
    } finally {
      setDraftingAppeal(false);
    }
  };

  const handleCopy = () => {
    if (!appealDraft) return;
    navigator.clipboard.writeText(appealDraft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const closeAppealModal = () => {
    setSelectedDenial(null);
    setAppealDraft('');
    setAppealContext('');
    setCopied(false);
  };

  const handleStatusChange = async (denialId: number, newStatus: AppealStatus | string) => {
    // Optimistically update local denials list
    setDenials((prev) =>
      prev.map((d) => (d.denial_id === denialId ? { ...d, appeal_status: newStatus as AppealStatus } : d))
    );
    if (selectedDenial?.denial_id === denialId) {
      setSelectedDenial((prev) => (prev ? { ...prev, appeal_status: newStatus as AppealStatus } : null));
    }
    try {
      await api.updateDenial(denialId, { appeal_status: newStatus as any });
    } catch (err) {
      console.warn('Failed to update appeal status:', err);
    }
  };

  const formatAppealStatus = (status: AppealStatus | string) => {
    const labels: Record<string, string> = {
      not_started: 'Not Started',
      drafted: 'Drafted',
      submitted: 'Submitted',
      won: 'Won',
      lost: 'Lost',
    };
    return labels[status] || status;
  };

  const getAppealStatusBadge = (status: AppealStatus | string) => {
    switch (status) {
      case 'won':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'drafted':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'submitted':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'lost':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  // Filtered denials
  const displayedDenials = filterCode
    ? denials.filter((d) => d.denial_code === filterCode)
    : denials;

  // KPI Calculations - sanitized to never produce NaN
  const totalDeniedSum = denials.reduce((sum, d) => {
    const val = typeof d.denied_amount === 'number' ? d.denied_amount : parseFloat(String(d.denied_amount || 0));
    return sum + (isNaN(val) ? 0 : val);
  }, 0);
  const draftedCount = denials.filter((d) => d.appeal_status === 'drafted' || d.appeal_drafted_by_ai).length;
  const topCodeItem = topCodes[0];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto animate-fade-in">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-blue-600" />
            Denials Management
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitor denial trends, analyze root causes, and generate automated AI appeal letters
          </p>
        </div>
        {filterCode && (
          <button
            onClick={() => setFilterCode(null)}
            className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            <span>Filtering by <strong className="text-blue-600">{filterCode}</strong></span>
            <X className="w-3.5 h-3.5 text-slate-400" />
          </button>
        )}
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl flex items-center justify-between text-sm animate-slide-down">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Top Summary KPI Cards ────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <p className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Total Denials</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{formatNumber(denials.length)}</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center flex-shrink-0">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <p className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Total Value Denied</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{formatCurrency(totalDeniedSum)}</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <p className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">AI Appeals Drafted</p>
            <p className="text-xl font-bold text-purple-700 mt-0.5">{formatNumber(draftedCount)}</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Top Denial Code</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5 truncate">
              {topCodeItem ? topCodeItem.denial_code : 'N/A'}
              <span className="text-xs font-normal text-slate-500 ml-1.5">
                ({topCodeItem ? `${topCodeItem.count} claims` : ''})
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* ── Top Denial Codes Horizontal Ribbon ─────────────────────── */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Top Denial Reason Codes (CARC)</span>
          </div>
          <span className="text-xs text-slate-400">Click a code to filter claims</span>
        </div>

        {codesLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-14 bg-slate-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5">
            {topCodes.slice(0, 5).map((code) => {
              const total = code.total_denied ?? code.total_denied_amount ?? 0;
              const avg = code.avg_denied ?? code.avg_denied_amount ?? 0;
              const isSelected = filterCode === code.denial_code;

              return (
                <button
                  key={code.denial_code}
                  type="button"
                  onClick={() => setFilterCode(isSelected ? null : code.denial_code)}
                  className={`text-left p-2.5 rounded-lg border transition-all ${
                    isSelected
                      ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-500/20 shadow-xs'
                      : 'bg-slate-50/70 border-slate-200/70 hover:bg-slate-100/80 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-blue-700">{code.denial_code}</span>
                    <span className="text-2xs font-semibold px-1.5 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                      {code.count}
                    </span>
                  </div>
                  <div className="mt-1 flex items-baseline justify-between text-2xs">
                    <span className="font-semibold text-slate-800">{formatCurrency(total)}</span>
                    <span className="text-slate-400">Avg: {formatCurrency(avg)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Full Width Denial List Table ───────────────────────────── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200/80 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-800">Denial List</h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200/60 text-slate-700">
              {displayedDenials.length} records
            </span>
          </div>
          {filterCode && (
            <span className="text-xs text-blue-600 font-medium">
              Filtered by: {filterCode}
            </span>
          )}
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left border-collapse min-w-[960px]">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Denial ID</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Claim</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">CARC</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right whitespace-nowrap">Denied Amt</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Date</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Root Cause</th>
                <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Appeal Status</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right w-44 min-w-[160px] whitespace-nowrap">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      <span>Loading denials...</span>
                    </div>
                  </td>
                </tr>
              ) : displayedDenials.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-slate-500">
                    No denials found matching criteria
                  </td>
                </tr>
              ) : (
                displayedDenials.map((denial) => {
                  const isRowDrafting = activeDraftingId === denial.denial_id;

                  return (
                    <tr 
                      key={denial.denial_id} 
                      className={`hover:bg-slate-50/80 transition-colors ${
                        isRowDrafting ? 'bg-blue-50/30' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900 whitespace-nowrap">
                        DNL-{denial.denial_id}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        <span className="font-mono text-blue-600 font-medium hover:underline cursor-pointer">
                          CLM-{denial.claim_id}
                        </span>
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        <span className="font-mono font-bold text-slate-800 px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200/60 text-xs">
                          {denial.denial_code || 'N/A'}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-slate-600">
                        <div className="max-w-[200px] truncate" title={denial.description || ''}>
                          {denial.description || 'N/A'}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-right font-semibold text-slate-900 whitespace-nowrap">
                        {formatCurrency(denial.denied_amount || 0)}
                      </td>
                      <td className="px-3 py-3 text-slate-500 whitespace-nowrap">
                        {formatDate(denial.denial_date)}
                      </td>
                      <td className="px-3 py-3 text-slate-700 whitespace-nowrap">
                        <div className="truncate max-w-[140px]" title={denial.root_cause || ''}>
                          {denial.root_cause || 'N/A'}
                        </div>
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <select
                            value={denial.appeal_status}
                            onChange={(e) => handleStatusChange(denial.denial_id, e.target.value)}
                            className={`text-2xs font-bold px-2 py-0.5 rounded-full border cursor-pointer bg-white transition-colors focus:ring-1 focus:ring-blue-500 ${getAppealStatusBadge(denial.appeal_status)}`}
                            title="Click to update Appeal Status (Not Started -> Drafted -> Submitted -> Won / Lost)"
                          >
                            <option value="not_started">Not Started</option>
                            <option value="drafted">Drafted</option>
                            <option value="submitted">Submitted</option>
                            <option value="won">Won (Approved)</option>
                            <option value="lost">Lost (Upheld)</option>
                          </select>
                          {denial.appeal_drafted_by_ai && (
                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-2xs font-bold bg-purple-50 text-purple-700 rounded-md border border-purple-200" title="Drafted by AI Appeal Specialist">
                              <Sparkles className="w-2.5 h-2.5 text-purple-600" />
                              AI
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right w-44 min-w-[160px] whitespace-nowrap">
                        <button
                          onClick={() => handleDraftAppeal(denial)}
                          disabled={draftingAppeal}
                          className={`inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg shadow-xs transition-all w-32 ${
                            isRowDrafting
                              ? 'bg-blue-100 text-blue-700 border border-blue-300 animate-pulse'
                              : denial.appeal_status === 'drafted'
                              ? 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
                              : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-500/20'
                          }`}
                        >
                          {isRowDrafting ? (
                            <>
                              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600 flex-shrink-0" />
                              Drafting...
                            </>
                          ) : denial.appeal_status === 'drafted' ? (
                            <>
                              <FileText className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                              View Appeal
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-3.5 h-3.5 text-white flex-shrink-0" />
                              Draft Appeal
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Table Pagination */}
        <div className="px-5 py-3.5 border-t border-slate-200/80 bg-slate-50/50 flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Showing <strong className="text-slate-800">{displayedDenials.length}</strong> of{' '}
            <strong className="text-slate-800">{denials.length}</strong> denials
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPagination((prev) => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
              disabled={pagination.page === 1 || loading}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4 text-slate-600" />
            </button>
            <span className="text-xs font-medium text-slate-700 px-2">Page {pagination.page}</span>
            <button
              onClick={() => setPagination((prev) => ({ ...prev, page: prev.page + 1 }))}
              disabled={denials.length < pagination.limit || loading}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4 text-slate-600" />
            </button>
          </div>
        </div>
      </div>

      {/* ── AI Appeal Modal with Rich Loading Animation ────────────── */}
      {selectedDenial && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-xl max-w-3xl w-full max-h-[85vh] overflow-hidden flex flex-col border border-slate-200 animate-slide-up">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-xs">
                  <Sparkles className="w-4.5 h-4.5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Automated Appeal Letter
                  </h2>
                  <p className="text-xs text-slate-500">
                    Claim <strong className="text-blue-600">CLM-{selectedDenial.claim_id}</strong> · Denial <strong className="text-slate-700">DNL-{selectedDenial.denial_id}</strong> (Code {selectedDenial.denial_code})
                  </p>
                </div>
              </div>
              <button
                onClick={closeAppealModal}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {draftingAppeal ? (
                /* ── AI Working / Loading State ── */
                <div className="py-12 px-6 flex flex-col items-center text-center space-y-6">
                  {/* Glowing Pulse Ring */}
                  <div className="relative">
                    <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center animate-pulse">
                      <div className="w-14 h-14 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-lg shadow-blue-500/30">
                        <Bot className="w-7 h-7 animate-bounce" />
                      </div>
                    </div>
                    <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center shadow-sm">
                      <Sparkles className="w-3.5 h-3.5 animate-spin" />
                    </div>
                  </div>

                  {/* Status Heading */}
                  <div className="space-y-1.5 max-w-md">
                    <h3 className="text-lg font-bold text-slate-900">
                      NovaArc AI is Drafting Your Appeal Letter...
                    </h3>
                    <p className="text-xs text-slate-500">
                      Powered by <span className="font-semibold text-blue-600">Ling 3.0 Flash Santé</span> & <span className="font-semibold text-indigo-600">Nemotron 3.5</span> for clinical precision and medical necessity citations.
                    </p>
                  </div>

                  {/* Progress Checklist Steps */}
                  <div className="w-full max-w-md bg-slate-50 rounded-xl p-4 border border-slate-200/80 text-left space-y-2.5">
                    <div className={`flex items-center gap-2.5 text-xs transition-colors ${aiLoadingStep >= 0 ? 'text-blue-700 font-semibold' : 'text-slate-400'}`}>
                      {aiLoadingStep > 0 ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin flex-shrink-0" />
                      )}
                      <span>Analyzing denial code <strong>{selectedDenial.denial_code}</strong> & root cause guidelines</span>
                    </div>

                    <div className={`flex items-center gap-2.5 text-xs transition-colors ${aiLoadingStep >= 1 ? 'text-blue-700 font-semibold' : 'text-slate-400'}`}>
                      {aiLoadingStep > 1 ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      ) : aiLoadingStep === 1 ? (
                        <div className="w-4 h-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin flex-shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-300 flex-shrink-0" />
                      )}
                      <span>Retrieving payer medical necessity justifications & clinical evidence</span>
                    </div>

                    <div className={`flex items-center gap-2.5 text-xs transition-colors ${aiLoadingStep >= 2 ? 'text-blue-700 font-semibold' : 'text-slate-400'}`}>
                      {aiLoadingStep === 2 ? (
                        <div className="w-4 h-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin flex-shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-300 flex-shrink-0" />
                      )}
                      <span>Drafting formal appeal narrative with ERISA & insurance code citations</span>
                    </div>
                  </div>

                  {/* Shimmer Skeleton preview */}
                  <div className="w-full max-w-md space-y-2 pt-2">
                    <div className="h-3.5 bg-slate-200/70 rounded-full w-full animate-pulse" />
                    <div className="h-3.5 bg-slate-200/70 rounded-full w-5/6 animate-pulse" />
                    <div className="h-3.5 bg-slate-200/70 rounded-full w-4/6 animate-pulse" />
                  </div>
                </div>
              ) : (
                /* ── Letter Generated View ── */
                <>
                  {/* Context Input */}
                  <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-slate-700">
                        Additional Appeal Context / Special Instructions (Optional)
                      </label>
                      <button
                        type="button"
                        onClick={handleRegenerateAppeal}
                        disabled={draftingAppeal}
                        className="inline-flex items-center gap-1 text-2xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        <RefreshCw className="w-3 h-3" />
                        Regenerate Draft
                      </button>
                    </div>
                    <textarea
                      value={appealContext}
                      onChange={(e) => setAppealContext(e.target.value)}
                      rows={2}
                      className="input text-xs"
                      placeholder="e.g. Include physician peer-to-peer notes, mention prior authorization reference #..."
                    />
                  </div>

                  {/* Letter Content Preview */}
                  <div className="relative bg-slate-900 text-slate-100 rounded-xl p-5 font-mono text-xs leading-relaxed max-h-[360px] overflow-y-auto border border-slate-800 shadow-inner">
                    <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 text-2xs text-slate-400">
                      <span className="flex items-center gap-1.5 text-blue-400 font-semibold">
                        <Sparkles className="w-3 h-3" />
                        Generated by AI Appeal Specialist
                      </span>
                      <span>{appealDraft.length} characters</span>
                    </div>
                    <pre className="whitespace-pre-wrap font-sans text-slate-200 text-xs leading-relaxed">
                      {appealDraft || 'No appeal letter text available.'}
                    </pre>
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between">
              <button
                type="button"
                onClick={closeAppealModal}
                className="btn-secondary text-xs"
              >
                Close
              </button>

              {!draftingAppeal && appealDraft && (
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex items-center gap-1.5 mr-2">
                    <span className="text-2xs font-semibold text-slate-500 uppercase">Status:</span>
                    <select
                      value={selectedDenial.appeal_status}
                      onChange={(e) => handleStatusChange(selectedDenial.denial_id, e.target.value)}
                      className={`text-2xs font-bold px-2 py-1 rounded-lg border bg-white cursor-pointer ${getAppealStatusBadge(selectedDenial.appeal_status)}`}
                    >
                      <option value="drafted">Drafted</option>
                      <option value="submitted">Submitted</option>
                      <option value="won">Won (Overturned)</option>
                      <option value="lost">Lost (Upheld)</option>
                    </select>
                  </div>

                  {selectedDenial.appeal_status !== 'submitted' && selectedDenial.appeal_status !== 'won' && (
                    <button
                      type="button"
                      onClick={() => handleStatusChange(selectedDenial.denial_id, 'submitted')}
                      className="inline-flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300 hover:bg-amber-100 transition-colors"
                      title="Transmit appeal to payer"
                    >
                      Submit to Payer
                    </button>
                  )}

                  {selectedDenial.appeal_status !== 'won' && (
                    <button
                      type="button"
                      onClick={() => handleStatusChange(selectedDenial.denial_id, 'won')}
                      className="inline-flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100 transition-colors"
                      title="Mark appeal won and denial reversed"
                    >
                      Mark as Won
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={handleCopy}
                    className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                      copied
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-500/20'
                    }`}
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy Letter
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}