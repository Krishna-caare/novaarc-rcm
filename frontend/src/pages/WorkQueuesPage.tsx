import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatCurrency, formatNumber, getPriorityBadge, getStatusBadge } from '../lib/utils';
import { WorkQueueSummary, Claim } from '../types';
import { FolderKanban, ChevronLeft, ChevronRight, Eye, X, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

export function WorkQueuesPage() {
  const [queues, setQueues] = useState<WorkQueueSummary[]>([]);
  const [selectedQueue, setSelectedQueue] = useState<WorkQueueSummary | null>(null);
  const [queueClaims, setQueueClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(false);
  const [claimsLoading, setClaimsLoading] = useState(false);
  const [claimsPagination, setClaimsPagination] = useState({ page: 1, limit: 20 });
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [viewingClaim, setViewingClaim] = useState<Claim | null>(null);
  const [resolvingClaimId, setResolvingClaimId] = useState<number | null>(null);

  useEffect(() => {
    fetchQueues();
  }, []);

  const fetchQueues = async () => {
    setLoading(true);
    try {
      const data = await api.listWorkQueues();
      setQueues(data);
      if (data.length > 0 && !selectedQueue) {
        setSelectedQueue(data[0]);
        fetchQueueClaims(data[0].queue_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load work queues');
    } finally {
      setLoading(false);
    }
  };

  const handleQueueClick = async (queue: WorkQueueSummary) => {
    setSelectedQueue(queue);
    setError(null);
    setSuccessMessage(null);
    await fetchQueueClaims(queue.queue_id);
  };

  const fetchQueueClaims = async (queueId: number) => {
    setClaimsLoading(true);
    try {
      const data = await api.getQueueClaims(queueId);
      setQueueClaims(data);
      setClaimsPagination(prev => ({ ...prev, page: 1 }));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load queue claims');
    } finally {
      setClaimsLoading(false);
    }
  };

  const handleResolve = async (claimId: number) => {
    if (!selectedQueue) return;
    setResolvingClaimId(claimId);
    setError(null);
    try {
      await api.resolveClaimInQueue(selectedQueue.queue_id, claimId);
      // Optimistic removal from queue claims
      setQueueClaims(prev => prev.filter(c => c.claim_id !== claimId));
      setSelectedQueue(prev => prev ? {
        ...prev,
        claim_count: Math.max(0, prev.claim_count - 1),
      } : null);
      setQueues(prev => prev.map(q => q.queue_id === selectedQueue.queue_id ? {
        ...q,
        claim_count: Math.max(0, q.claim_count - 1)
      } : q));
      
      if (viewingClaim?.claim_id === claimId) {
        setViewingClaim(null);
      }

      setSuccessMessage(`Claim CLM-${claimId} resolved in ${selectedQueue.name} successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);

      // Refresh in background to sync server state
      fetchQueues();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resolve claim in queue');
    } finally {
      setResolvingClaimId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Work Queues</h1>
          <p className="text-slate-600">Prioritized claim work queues for AR operations</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
          <AlertCircle className="w-4.5 h-4.5 text-red-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-lg flex items-center gap-2 animate-fade-in text-sm font-medium">
          <CheckCircle2 className="w-4.5 h-4.5 text-emerald-600 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Compact Queues List Widget */}
        <div className="lg:col-span-4">
          <Card className="overflow-hidden shadow-sm border border-slate-200/80 sticky top-4">
            <CardHeader className="py-3 px-4 bg-slate-50/80 border-b border-slate-200/80">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FolderKanban className="w-4 h-4 text-primary-600" />
                  <CardTitle className="text-sm font-semibold text-slate-900">
                    Active Queues ({queues.length})
                  </CardTitle>
                </div>
                <span className="text-2xs font-medium text-slate-400 uppercase tracking-wider">
                  Select Queue
                </span>
              </div>
            </CardHeader>
            <div className="divide-y divide-slate-100">
              {queues.map((queue) => {
                const isSelected = selectedQueue?.queue_id === queue.queue_id;
                const badge = getPriorityBadge(queue.priority);
                return (
                  <button
                    key={queue.queue_id}
                    type="button"
                    onClick={() => handleQueueClick(queue)}
                    className={cn(
                      'w-full text-left px-3.5 py-2.5 transition-all flex items-center justify-between gap-2 cursor-pointer border-l-[3px]',
                      isSelected
                        ? 'bg-primary-50/80 border-primary-600 text-slate-900'
                        : 'border-transparent hover:bg-slate-50/80 text-slate-700'
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className={cn(
                          'text-xs truncate',
                          isSelected ? 'font-bold text-primary-950' : 'font-semibold text-slate-800'
                        )}>
                          {queue.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-2xs text-slate-500 mt-0.5">
                        <span className="font-medium text-slate-700">{formatNumber(queue.claim_count)} claims</span>
                        <span className="text-slate-300">•</span>
                        <span className="font-semibold text-emerald-700">{formatCurrency(queue.total_value)}</span>
                      </div>
                    </div>
                    <span className={cn('text-2xs px-2 py-0.5 rounded-full font-medium flex-shrink-0', badge.className)}>
                      {badge.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </Card>
        </div>

        <div className="lg:col-span-8">
          {selectedQueue ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FolderKanban className="w-5 h-5 text-primary-600" />
                    <CardTitle>{selectedQueue.name}</CardTitle>
                  </div>
                  <span className={getPriorityBadge(selectedQueue.priority).className}>
                    {getPriorityBadge(selectedQueue.priority).label}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {claimsLoading ? (
                  <div className="p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
                  </div>
                ) : queueClaims.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    <FolderKanban className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No unresolved claims in this queue</p>
                  </div>
                ) : (
                  <>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                            <th className="px-4 py-3">Claim</th>
                            <th className="px-4 py-3">Patient</th>
                            <th className="px-4 py-3">Provider</th>
                            <th className="px-4 py-3">DOS</th>
                            <th className="px-4 py-3">Charged</th>
                            <th className="px-4 py-3">Balance</th>
                            <th className="px-4 py-3">Status</th>
                            <th className="px-4 py-3 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-sm">
                          {queueClaims.map((claim) => (
                            <tr key={claim.claim_id} className="hover:bg-slate-50/80 transition-colors">
                              <td className="px-4 py-3 font-mono text-sm font-semibold text-blue-600">CLM-{claim.claim_id}</td>
                              <td className="px-4 py-3 text-slate-700">{claim.patient?.mrn || 'N/A'}</td>
                              <td className="px-4 py-3 text-slate-700">{claim.provider?.name || 'N/A'}</td>
                              <td className="px-4 py-3 text-slate-700">{claim.date_of_service}</td>
                              <td className="px-4 py-3 text-slate-700">{formatCurrency(claim.charge_amount)}</td>
                              <td className="px-4 py-3 font-medium text-slate-900">{formatCurrency(claim.charge_amount - claim.paid_amount)}</td>
                              <td className="px-4 py-3">
                                <span className={getStatusBadge(claim.status).className}>
                                  {getStatusBadge(claim.status).label}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <button
                                    onClick={() => setViewingClaim(claim)}
                                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-blue-600 transition-colors cursor-pointer"
                                    title="View Claim Details"
                                  >
                                    <Eye className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => handleResolve(claim.claim_id)}
                                    disabled={resolvingClaimId === claim.claim_id}
                                    className="btn-primary text-xs px-3 py-1 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                                  >
                                    {resolvingClaimId === claim.claim_id ? (
                                      <>
                                        <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        <span>Resolving...</span>
                                      </>
                                    ) : (
                                      'Resolve'
                                    )}
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
                      <p className="text-sm text-slate-600">
                        Showing {queueClaims.length} claims
                      </p>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setClaimsPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                          disabled={claimsPagination.page === 1 || claimsLoading}
                          className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-sm text-slate-600">Page {claimsPagination.page}</span>
                        <button
                          disabled={claimsLoading}
                          className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-12 text-center">
                <FolderKanban className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">Select a Work Queue</h3>
                <p className="text-slate-500">Click on a queue from the left to view and manage its claims</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* ── View Claim Modal ──────────────────────────────────────────────────────── */}
      {viewingClaim && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200 animate-scale-in max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                  <FileText className="w-4.5 h-4.5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Claim Details</h3>
                  <p className="font-mono text-xs text-slate-500">CLM-{viewingClaim.claim_id}</p>
                </div>
              </div>
              <button
                onClick={() => setViewingClaim(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4 overflow-y-auto text-xs">
              {/* Status & Queue Info */}
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 font-medium">Status:</span>
                  <span className={getStatusBadge(viewingClaim.status).className}>
                    {getStatusBadge(viewingClaim.status).label}
                  </span>
                </div>
                {selectedQueue && (
                  <span className={getPriorityBadge(selectedQueue.priority).className}>
                    {selectedQueue.name}
                  </span>
                )}
              </div>

              {/* Financial Summary */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-white border border-slate-200 rounded-lg text-center">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Charged</p>
                  <p className="font-bold text-slate-900 text-sm mt-1">{formatCurrency(viewingClaim.charge_amount)}</p>
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-lg text-center">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Paid</p>
                  <p className="font-bold text-emerald-600 text-sm mt-1">{formatCurrency(viewingClaim.paid_amount)}</p>
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-lg text-center">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Balance</p>
                  <p className="font-bold text-blue-600 text-sm mt-1">
                    {formatCurrency(viewingClaim.charge_amount - viewingClaim.paid_amount)}
                  </p>
                </div>
              </div>

              {/* Patient & Provider Details */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Patient MRN</p>
                  <p className="font-medium text-slate-900 mt-1">{viewingClaim.patient?.mrn || 'N/A'}</p>
                  {viewingClaim.patient?.dob && (
                    <p className="text-2xs text-slate-500 mt-0.5">DOB: {viewingClaim.patient.dob}</p>
                  )}
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Provider</p>
                  <p className="font-medium text-slate-900 mt-1">{viewingClaim.provider?.name || 'N/A'}</p>
                  {viewingClaim.provider?.specialty && (
                    <p className="text-2xs text-slate-500 mt-0.5">{viewingClaim.provider.specialty}</p>
                  )}
                </div>
              </div>

              {/* Payer & DOS */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Payer</p>
                  <p className="font-medium text-slate-900 mt-1">{viewingClaim.payer?.name || 'N/A'}</p>
                  {viewingClaim.payer?.payer_type && (
                    <p className="text-2xs text-slate-500 mt-0.5">{viewingClaim.payer.payer_type}</p>
                  )}
                </div>
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase">Date of Service</p>
                  <p className="font-medium text-slate-900 mt-1">{viewingClaim.date_of_service || 'N/A'}</p>
                </div>
              </div>

              {/* Diagnosis & Procedure Codes */}
              <div className="space-y-2">
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase mb-1.5">ICD-10 Diagnosis Codes</p>
                  <div className="flex flex-wrap gap-1.5">
                    {viewingClaim.icd10_codes && viewingClaim.icd10_codes.length > 0 ? (
                      viewingClaim.icd10_codes.map((code) => (
                        <span key={code} className="px-2 py-0.5 bg-blue-50 text-blue-700 font-mono text-xs rounded border border-blue-200 font-semibold">
                          {code}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-400">None specified</span>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <p className="text-2xs font-semibold text-slate-400 uppercase mb-1.5">CPT Procedure Codes</p>
                  <div className="flex flex-wrap gap-1.5">
                    {viewingClaim.cpt_codes && viewingClaim.cpt_codes.length > 0 ? (
                      viewingClaim.cpt_codes.map((code) => (
                        <span key={code} className="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-mono text-xs rounded border border-emerald-200 font-semibold">
                          {code}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-400">None specified</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/70 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setViewingClaim(null)}
                className="btn-secondary text-xs"
              >
                Close
              </button>
              {selectedQueue && (
                <button
                  type="button"
                  onClick={() => handleResolve(viewingClaim.claim_id)}
                  disabled={resolvingClaimId === viewingClaim.claim_id}
                  className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {resolvingClaimId === viewingClaim.claim_id ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Resolving...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Resolve Claim in Queue</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}