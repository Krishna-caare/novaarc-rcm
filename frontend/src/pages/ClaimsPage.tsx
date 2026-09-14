import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatCurrency, formatDate, getStatusBadge } from '../lib/utils';
import { Claim } from '../types';
import { Filter, ChevronLeft, ChevronRight, Plus, Eye, Edit, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';

const CLAIM_STATUSES: Array<{value: string, label: string}> = [
  { value: 'created', label: 'Created' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'in_process', label: 'In Process' },
  { value: 'paid', label: 'Paid' },
  { value: 'denied', label: 'Denied' },
  { value: 'appealed', label: 'Appealed' },
];

export function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });
  const [filters, setFilters] = useState({
    status: '',
    payer_id: '',
    provider_id: '',
    patient_id: '',
    date_from: '',
    date_to: '',
    search: '',
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [showView, setShowView] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editData, setEditData] = useState<Partial<Claim>>({});
  const [actionLoading, setActionLoading] = useState(false);

  const fetchClaims = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        status: filters.status || undefined,
        payer_id: filters.payer_id ? parseInt(filters.payer_id) : undefined,
        provider_id: filters.provider_id ? parseInt(filters.provider_id) : undefined,
        patient_id: filters.patient_id ? parseInt(filters.patient_id) : undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
        skip: (pagination.page - 1) * pagination.limit,
        limit: pagination.limit,
      };
      const data = await api.listClaims(params);
      setClaims(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
  }, [pagination.page, filters.status, filters.payer_id, filters.provider_id, filters.date_from, filters.date_to]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const clearFilters = () => {
    setFilters({
      status: '',
      payer_id: '',
      provider_id: '',
      patient_id: '',
      date_from: '',
      date_to: '',
      search: '',
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  const handleView = async (claim: Claim) => {
    try {
      const full = await api.getClaim(claim.claim_id);
      setSelectedClaim(full);
    } catch {
      setSelectedClaim(claim);
    }
    setShowView(true);
  };

  const handleEdit = (claim: Claim) => {
    setSelectedClaim(claim);
    setEditData({ charge_amount: claim.charge_amount, status: claim.status as any, cpt_codes: claim.cpt_codes, icd10_codes: claim.icd10_codes });
    setShowEdit(true);
  };

  const handleEditSave = async () => {
    if (!selectedClaim) return;
    setActionLoading(true);
    try {
      await api.updateClaim(selectedClaim.claim_id, editData as any);
      setShowEdit(false);
      await fetchClaims();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update claim');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmit = async (claim: Claim) => {
    if (!confirm(`Submit claim CLM-${claim.claim_id} to payer?`)) return;
    setActionLoading(true);
    try {
      await api.submitClaim(claim.claim_id);
      await fetchClaims();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit claim');
    } finally {
      setActionLoading(false);
    }
  };

  return (
          <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Claims</h1>
            <p className="text-slate-600">Manage and track all claims</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowFilters(!showFilters)} className={cn('btn-secondary', hasActiveFilters && 'bg-primary-50 text-primary-700 border-primary-200')}>
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
            <button className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              New Claim
            </button>
          </div>
        </div>

        {showFilters && (
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
                <div>
                  <label className="label">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                    className="input"
                  >
                    <option value="">All Statuses</option>
                    {CLAIM_STATUSES.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
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
                <div className="lg:col-span-2">
                  <label className="label">Search</label>
                  <input
                    type="text"
                    placeholder="Search claims..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="input"
                  />
                </div>
                <div className="flex items-end">
                  {hasActiveFilters && (
                    <button onClick={clearFilters} className="btn-secondary w-full">
                      Clear Filters
                    </button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50 text-left text-sm text-slate-500 border-b border-slate-200">
                    <th className="px-4 py-3">Claim ID</th>
                    <th className="px-4 py-3">Patient</th>
                    <th className="px-4 py-3">Provider</th>
                    <th className="px-4 py-3">Payer</th>
                    <th className="px-4 py-3">DOS</th>
                    <th className="px-4 py-3">Charged</th>
                    <th className="px-4 py-3">Paid</th>
                    <th className="px-4 py-3">Balance</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {claims.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="px-4 py-12 text-center text-slate-500">
                        No claims found
                      </td>
                    </tr>
                  ) : (
                    claims.map((claim) => (
                      <tr key={claim.claim_id} className="hover:bg-slate-50 border-b border-slate-100">
                        <td className="px-4 py-3 font-mono text-sm text-slate-900">CLM-{claim.claim_id}</td>
                        <td className="px-4 py-3 text-slate-600">
                          {claim.patient?.mrn || 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {claim.provider?.name || 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {claim.payer?.name || 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(claim.date_of_service)}</td>
                        <td className="px-4 py-3 text-slate-600">{formatCurrency(claim.charge_amount)}</td>
                        <td className="px-4 py-3 text-slate-600">{formatCurrency(claim.paid_amount)}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">
                          {formatCurrency(claim.charge_amount - claim.paid_amount)}
                        </td>
                        <td className="px-4 py-3">
                          <span className={getStatusBadge(claim.status).className}>
                            {getStatusBadge(claim.status).label}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button onClick={() => handleView(claim)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500" title="View">
                              <Eye className="w-4 h-4" />
                            </button>
                            <button onClick={() => handleEdit(claim)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500" title="Edit">
                              <Edit className="w-4 h-4" />
                            </button>
                            {claim.status === 'created' && (
                              <button onClick={() => handleSubmit(claim)} disabled={actionLoading} className="p-2 rounded-lg hover:bg-primary-100 text-primary-600 disabled:opacity-50" title="Submit">
                                <ArrowRight className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            
            <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
              <p className="text-sm text-slate-600">
                Showing {claims.length} claims
              </p>
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
                  disabled={claims.length < pagination.limit || loading}
                  className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {showView && selectedClaim && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="font-semibold">Claim CLM-{selectedClaim.claim_id}</h3>
                <button onClick={() => setShowView(false)} className="p-2 hover:bg-slate-100 rounded">✕</button>
              </div>
              <div className="p-4 space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-4">
                  <div><span className="text-slate-500">Patient</span><p>{selectedClaim.patient?.mrn || selectedClaim.patient_id}</p></div>
                  <div><span className="text-slate-500">Provider</span><p>{selectedClaim.provider?.name || selectedClaim.provider_id}</p></div>
                  <div><span className="text-slate-500">Payer</span><p>{selectedClaim.payer?.name || selectedClaim.payer_id}</p></div>
                  <div><span className="text-slate-500">DOS</span><p>{formatDate(selectedClaim.date_of_service)}</p></div>
                  <div><span className="text-slate-500">Charged</span><p>{formatCurrency(selectedClaim.charge_amount)}</p></div>
                  <div><span className="text-slate-500">Paid</span><p>{formatCurrency(selectedClaim.paid_amount)}</p></div>
                  <div><span className="text-slate-500">Status</span><p><span className={getStatusBadge(selectedClaim.status).className}>{getStatusBadge(selectedClaim.status).label}</span></p></div>
                  <div><span className="text-slate-500">EDI Ref</span><p>{selectedClaim.edi_837_ref || '—'}</p></div>
                </div>
                <div><span className="text-slate-500">CPT</span><p>{selectedClaim.cpt_codes?.join(', ') || '—'}</p></div>
                <div><span className="text-slate-500">ICD10</span><p>{selectedClaim.icd10_codes?.join(', ') || '—'}</p></div>
                <div><span className="text-slate-500">Modifiers</span><p>{selectedClaim.modifiers?.join(', ') || '—'}</p></div>
                {selectedClaim.denial_predicted && <div className="bg-amber-50 p-3 rounded">Denial predicted: {(Number(selectedClaim.denial_probability)*100).toFixed(1)}%</div>}
              </div>
            </div>
          </div>
        )}

        {showEdit && selectedClaim && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white rounded-xl max-w-lg w-full">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="font-semibold">Edit CLM-{selectedClaim.claim_id}</h3>
                <button onClick={() => setShowEdit(false)} className="p-2 hover:bg-slate-100 rounded">✕</button>
              </div>
              <div className="p-4 space-y-4">
                <div>
                  <label className="label">Charge Amount</label>
                  <input type="number" className="input" value={editData.charge_amount as any || ''} onChange={e => setEditData({...editData, charge_amount: parseFloat(e.target.value) as any})} />
                </div>
                <div>
                  <label className="label">Status</label>
                  <select className="input" value={editData.status as any || ''} onChange={e => setEditData({...editData, status: e.target.value as any})}>
                    {CLAIM_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">CPT (comma separated)</label>
                  <input className="input" value={editData.cpt_codes?.join(', ') || ''} onChange={e => setEditData({...editData, cpt_codes: e.target.value.split(',').map(s=>s.trim()).filter(Boolean) as any})} />
                </div>
                <div>
                  <label className="label">ICD10 (comma separated)</label>
                  <input className="input" value={editData.icd10_codes?.join(', ') || ''} onChange={e => setEditData({...editData, icd10_codes: e.target.value.split(',').map(s=>s.trim()).filter(Boolean) as any})} />
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setShowEdit(false)} className="btn-secondary">Cancel</button>
                  <button onClick={handleEditSave} disabled={actionLoading} className="btn-primary">{actionLoading ? 'Saving...' : 'Save'}</button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
}