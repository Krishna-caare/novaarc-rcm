import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatCurrency, formatNumber, getPriorityBadge, getStatusBadge } from '../lib/utils';
import { WorkQueueSummary, Claim } from '../types';
import { FolderKanban, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

export function WorkQueuesPage() {
  const [queues, setQueues] = useState<WorkQueueSummary[]>([]);
  const [selectedQueue, setSelectedQueue] = useState<WorkQueueSummary | null>(null);
  const [queueClaims, setQueueClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(false);
  const [claimsLoading, setClaimsLoading] = useState(false);
  const [claimsPagination, setClaimsPagination] = useState({ page: 1, limit: 20 });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchQueues();
  }, []);

  const fetchQueues = async () => {
    setLoading(true);
    try {
      const data = await api.listWorkQueues();
      setQueues(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load work queues');
    } finally {
      setLoading(false);
    }
  };

  const handleQueueClick = async (queue: WorkQueueSummary) => {
    setSelectedQueue(queue);
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
    try {
      await api.resolveClaimInQueue(selectedQueue.queue_id, claimId);
      await fetchQueueClaims(selectedQueue.queue_id);
      await fetchQueues();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resolve claim');
    }
  };

  if (loading) {
    return (
              <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
        </div>);
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
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-4">
            {queues.map((queue) => (
              <div
                key={queue.queue_id}
                className={cn(
                  'cursor-pointer transition-all',
                  selectedQueue?.queue_id === queue.queue_id
                    ? 'ring-2 ring-primary-500 bg-primary-50'
                    : 'hover:bg-slate-50'
                )}
                onClick={() => handleQueueClick(queue)}
              >
                <Card
                  className="cursor-pointer transition-all"
                >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <FolderKanban className="w-5 h-5 text-primary-600" />
                        <h3 className="font-semibold text-slate-900">{queue.name}</h3>
                      </div>
                      <p className="mt-1 text-sm text-slate-500 capitalize">{queue.priority} priority</p>
                    </div>
                    <span className={getPriorityBadge(queue.priority).className}>
                      {getPriorityBadge(queue.priority).label}
                    </span>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-2xl font-bold text-slate-900">{formatNumber(queue.claim_count)}</p>
                      <p className="text-xs text-slate-500">Claims</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-2xl font-bold text-slate-900">{formatCurrency(queue.total_value)}</p>
                      <p className="text-xs text-slate-500">Total Value</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
          </div>

          <div className="lg:col-span-2">
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
                      <p>No claims in this queue</p>
                    </div>
                  ) : (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="bg-slate-50 text-left text-sm text-slate-500 border-b border-slate-200">
                              <th className="px-4 py-3">Claim</th>
                              <th className="px-4 py-3">Patient</th>
                              <th className="px-4 py-3">Provider</th>
                              <th className="px-4 py-3">DOS</th>
                              <th className="px-4 py-3">Charged</th>
                              <th className="px-4 py-3">Balance</th>
                              <th className="px-4 py-3">Status</th>
                              <th className="px-4 py-3">Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {queueClaims.map((claim) => (
                              <tr key={claim.claim_id} className="hover:bg-slate-50 border-b border-slate-100">
                                <td className="px-4 py-3 font-mono text-sm text-slate-900">CLM-{claim.claim_id}</td>
                                <td className="px-4 py-3 text-slate-600">{claim.patient?.mrn || 'N/A'}</td>
                                <td className="px-4 py-3 text-slate-600">{claim.provider?.name || 'N/A'}</td>
                                <td className="px-4 py-3 text-slate-600">{claim.date_of_service}</td>
                                <td className="px-4 py-3 text-slate-600">{formatCurrency(claim.charge_amount)}</td>
                                <td className="px-4 py-3 font-medium text-slate-900">{formatCurrency(claim.charge_amount - claim.paid_amount)}</td>
                                <td className="px-4 py-3">
                                  <span className={getStatusBadge(claim.status).className}>
                                    {getStatusBadge(claim.status).label}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    <button className="p-2 rounded-lg hover:bg-slate-100 text-slate-500" title="View">
                                      <Eye className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => handleResolve(claim.claim_id)}
                                      className="btn-primary text-sm px-3 py-1"
                                    >
                                      Resolve
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
      </div>);
}