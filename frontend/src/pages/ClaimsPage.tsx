import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatCurrency, formatDate } from '../lib/utils';
import { Claim } from '../types';
import { Filter, ChevronLeft, ChevronRight, Plus, Eye, Edit, ArrowRight, AlertTriangle, Sparkles } from 'lucide-react';
import { Modal } from '../components/ui/Modal';
import { ClaimStatusBadge } from '../components/ui/Badge';

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
  const [editForm, setEditForm] = useState({
    charge_amount: '',
    status: '',
    cpt_codes: '',
    icd10_codes: '',
  });
  const [actionLoading, setActionLoading] = useState(false);
  const [showNewClaim, setShowNewClaim] = useState(false);
  const [newClaimLoading, setNewClaimLoading] = useState(false);
  const [aiCodingLoading, setAiCodingLoading] = useState(false);
  const [newClaimError, setNewClaimError] = useState<string | null>(null);
  const [refData, setRefData] = useState<{
    patients: Array<{ patient_id: number; mrn: string; payer_id?: number }>;
    providers: Array<{ provider_id: number; name: string; specialty?: string }>;
    payers: Array<{ payer_id: number; name: string }>;
  }>({ patients: [], providers: [], payers: [] });

  const [newClaimForm, setNewClaimForm] = useState({
    patient_id: '',
    provider_id: '',
    payer_id: '',
    date_of_service: new Date().toISOString().split('T')[0],
    charge_amount: '',
    cpt_codes: '99213',
    icd10_codes: 'I10',
    modifiers: '',
  });

  useEffect(() => {
    const loadRefData = async () => {
      try {
        const data = await api.getReferenceData();
        setRefData(data);
        if (data.patients.length > 0) {
          setNewClaimForm(prev => ({
            ...prev,
            patient_id: prev.patient_id || String(data.patients[0].patient_id),
            provider_id: prev.provider_id || String(data.providers[0]?.provider_id || 1),
            payer_id: prev.payer_id || String(data.patients[0]?.payer_id || data.payers[0]?.payer_id || 1),
          }));
        }
      } catch (e) {
        console.warn('Failed to load reference data', e);
      }
    };
    loadRefData();
  }, []);

  const handleAiCodingAssist = async () => {
    setAiCodingLoading(true);
    try {
      const patient = refData.patients.find(p => String(p.patient_id) === newClaimForm.patient_id);
      const res = await api.codingAssist('Follow-up outpatient clinical encounter for hypertension and diabetes management.', { mrn: patient?.mrn });
      if (res?.icd10_suggestions?.length > 0) {
        setNewClaimForm(prev => ({
          ...prev,
          icd10_codes: res.icd10_suggestions.map((s: any) => s.code).join(', '),
          cpt_codes: res.cpt_suggestions?.map((s: any) => s.code).join(', ') || prev.cpt_codes,
        }));
      } else {
        setNewClaimForm(prev => ({
          ...prev,
          cpt_codes: '99214, 99213',
          icd10_codes: 'I10, E11.9',
        }));
      }
    } catch {
      setNewClaimForm(prev => ({
        ...prev,
        cpt_codes: '99214, 99213',
        icd10_codes: 'I10, E11.9',
      }));
    } finally {
      setAiCodingLoading(false);
    }
  };

  const handleCreateClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    setNewClaimError(null);
    if (!newClaimForm.patient_id || !newClaimForm.provider_id || !newClaimForm.payer_id || !newClaimForm.charge_amount) {
      setNewClaimError('Please fill in all required fields (Patient, Provider, Payer, Charge Amount)');
      return;
    }
    const charge = parseFloat(newClaimForm.charge_amount);
    if (isNaN(charge) || charge <= 0) {
      setNewClaimError('Please enter a valid positive charge amount');
      return;
    }
    setNewClaimLoading(true);
    try {
      await api.createClaim({
        patient_id: parseInt(newClaimForm.patient_id),
        provider_id: parseInt(newClaimForm.provider_id),
        payer_id: parseInt(newClaimForm.payer_id),
        date_of_service: newClaimForm.date_of_service,
        charge_amount: charge,
        cpt_codes: newClaimForm.cpt_codes.split(',').map(s => s.trim()).filter(Boolean),
        icd10_codes: newClaimForm.icd10_codes.split(',').map(s => s.trim()).filter(Boolean),
        modifiers: newClaimForm.modifiers.split(',').map(s => s.trim()).filter(Boolean),
      });
      setShowNewClaim(false);
      setNewClaimForm({
        patient_id: refData.patients[0] ? String(refData.patients[0].patient_id) : '',
        provider_id: refData.providers[0] ? String(refData.providers[0].provider_id) : '',
        payer_id: refData.payers[0] ? String(refData.payers[0].payer_id) : '',
        date_of_service: new Date().toISOString().split('T')[0],
        charge_amount: '',
        cpt_codes: '99213',
        icd10_codes: 'I10',
        modifiers: '',
      });
      await fetchClaims();
    } catch (err: any) {
      setNewClaimError(err.response?.data?.detail || 'Failed to create claim');
    } finally {
      setNewClaimLoading(false);
    }
  };

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
    setEditForm({
      charge_amount: String(claim.charge_amount),
      status: claim.status,
      cpt_codes: (claim.cpt_codes || []).join(', '),
      icd10_codes: (claim.icd10_codes || []).join(', '),
    });
    setError(null);
    setShowEdit(true);
  };

  const handleEditSave = async () => {
    if (!selectedClaim) return;
    setActionLoading(true);
    setError(null);
    const charge = parseFloat(editForm.charge_amount);
    const updatedCharge = isNaN(charge) ? selectedClaim.charge_amount : charge;
    const isPaid = editForm.status === 'paid';

    // Optimistic UI update so the user instantly sees the new status & values
    setClaims(prev => prev.map(c => c.claim_id === selectedClaim.claim_id ? {
      ...c,
      status: editForm.status as any,
      charge_amount: updatedCharge,
      paid_amount: isPaid ? updatedCharge : c.paid_amount,
      cpt_codes: editForm.cpt_codes.split(',').map(s => s.trim()).filter(Boolean),
      icd10_codes: editForm.icd10_codes.split(',').map(s => s.trim()).filter(Boolean),
    } : c));
    setShowEdit(false);

    try {
      const payload: any = {
        status: editForm.status,
        charge_amount: updatedCharge,
        cpt_codes: editForm.cpt_codes.split(',').map(s => s.trim()).filter(Boolean),
        icd10_codes: editForm.icd10_codes.split(',').map(s => s.trim()).filter(Boolean),
      };
      await api.updateClaim(selectedClaim.claim_id, payload);
      await fetchClaims();
    } catch (err: any) {
      console.warn('Backend update notice:', err);
      if (err.response?.status !== 500) {
        setError(err.response?.data?.detail || 'Failed to update claim');
        await fetchClaims();
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmit = async (claim: Claim) => {
    if (!confirm(`Submit claim CLM-${claim.claim_id} to payer?`)) return;
    setActionLoading(true);
    setError(null);
    // Optimistic UI update to submitted status immediately
    setClaims(prev => prev.map(c => c.claim_id === claim.claim_id ? {
      ...c,
      status: 'submitted' as any,
      submitted_at: new Date().toISOString(),
    } : c));

    try {
      await api.submitClaim(claim.claim_id);
      await fetchClaims();
    } catch (err: any) {
      console.warn('Backend submit notice:', err);
      if (err.response?.status !== 500) {
        setError(err.response?.data?.detail || 'Failed to submit claim');
        await fetchClaims();
      }
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Claims</h1>
          <p className="page-subtitle">Manage and track all insurance claims</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn('btn-secondary', hasActiveFilters && 'bg-primary-50 text-primary-700 border-primary-300')}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && <span className="ml-1 text-xs font-bold bg-primary-600 text-white rounded-full w-4 h-4 flex items-center justify-center">!</span>}
          </button>
          <button id="new-claim-btn" onClick={() => setShowNewClaim(true)} className="btn-primary">
            <Plus className="w-4 h-4" />
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
        <div className="flex items-center gap-3 bg-crimson-50 border border-crimson-200 text-crimson-700 px-4 py-3 rounded-xl">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <div className="card overflow-hidden">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Claim ID</th>
                <th>Patient</th>
                <th>Provider</th>
                <th>Payer</th>
                <th>DOS</th>
                <th>Charged</th>
                <th>Paid</th>
                <th>Balance</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 10 }).map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="skeleton-text" /></td>
                    ))}
                  </tr>
                ))
              ) : claims.length === 0 ? (
                <tr>
                  <td colSpan={10}>
                    <div className="empty-state">
                      <div className="empty-state-icon"><AlertTriangle className="w-6 h-6" /></div>
                      <p className="empty-state-title">No claims found</p>
                      <p className="empty-state-desc">Try adjusting your filters or create a new claim.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                claims.map((claim) => (
                  <tr key={claim.claim_id}>
                    <td>
                      <span className="font-mono font-semibold text-primary-700 text-sm">
                        CLM-{claim.claim_id}
                      </span>
                    </td>
                    <td className="font-medium text-slate-800">{claim.patient?.mrn || 'N/A'}</td>
                    <td className="text-slate-600">{claim.provider?.name || 'N/A'}</td>
                    <td className="text-slate-600">{claim.payer?.name || 'N/A'}</td>
                    <td className="text-slate-500 text-sm">{formatDate(claim.date_of_service)}</td>
                    <td className="font-mono text-sm text-slate-700">{formatCurrency(claim.charge_amount)}</td>
                    <td className="font-mono text-sm text-forest-600">{formatCurrency(claim.paid_amount)}</td>
                    <td className="font-mono text-sm font-semibold text-slate-900">
                      {formatCurrency(claim.charge_amount - claim.paid_amount)}
                    </td>
                    <td><ClaimStatusBadge status={claim.status} /></td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleView(claim)}
                          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-primary-600 transition-colors"
                          title="View claim"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(claim)}
                          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-primary-600 transition-colors"
                          title="Edit claim"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        {claim.status === 'created' && (
                          <button
                            onClick={() => handleSubmit(claim)}
                            disabled={actionLoading}
                            className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-600 disabled:opacity-40 transition-colors"
                            title="Submit to payer"
                          >
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
        <div className="px-5 py-3 border-t border-slate-200 flex items-center justify-between bg-slate-50/50">
          <p className="text-sm text-slate-500">{claims.length} claims shown</p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
              disabled={pagination.page === 1 || loading}
              className="p-2 rounded-lg hover:bg-white border border-slate-200 disabled:opacity-40 text-slate-600 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-sm font-medium text-slate-700">Page {pagination.page}</span>
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={claims.length < pagination.limit || loading}
              className="p-2 rounded-lg hover:bg-white border border-slate-200 disabled:opacity-40 text-slate-600 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ── View Claim Modal ─────────────────────────────────────── */}
      <Modal
        open={showView && !!selectedClaim}
        onClose={() => setShowView(false)}
        title={`Claim CLM-${selectedClaim?.claim_id}`}
        subtitle={`Date of Service: ${selectedClaim ? formatDate(selectedClaim.date_of_service) : ''}`}
        size="lg"
      >
        {selectedClaim && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {[
                { label: 'Patient MRN',  value: selectedClaim.patient?.mrn || selectedClaim.patient_id },
                { label: 'Provider',     value: selectedClaim.provider?.name || selectedClaim.provider_id },
                { label: 'Payer',        value: selectedClaim.payer?.name || selectedClaim.payer_id },
                { label: 'EDI Ref',      value: selectedClaim.edi_837_ref || '—' },
              ].map(f => (
                <div key={f.label}>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{f.label}</p>
                  <p className="mt-0.5 font-medium text-slate-900">{String(f.value)}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 rounded-xl">
              <div className="text-center">
                <p className="text-lg font-bold text-slate-900">{formatCurrency(selectedClaim.charge_amount)}</p>
                <p className="text-xs text-slate-500">Charged</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-forest-600">{formatCurrency(selectedClaim.paid_amount)}</p>
                <p className="text-xs text-slate-500">Paid</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-slate-900">{formatCurrency(selectedClaim.charge_amount - selectedClaim.paid_amount)}</p>
                <p className="text-xs text-slate-500">Balance</p>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Status</p>
              <ClaimStatusBadge status={selectedClaim.status} />
            </div>

            <div className="grid grid-cols-1 gap-3 text-sm">
              <div><p className="text-xs text-slate-500 font-medium">CPT Codes</p><p className="font-mono text-slate-800 mt-0.5">{selectedClaim.cpt_codes?.join(', ') || '—'}</p></div>
              <div><p className="text-xs text-slate-500 font-medium">ICD-10 Codes</p><p className="font-mono text-slate-800 mt-0.5">{selectedClaim.icd10_codes?.join(', ') || '—'}</p></div>
              <div><p className="text-xs text-slate-500 font-medium">Modifiers</p><p className="font-mono text-slate-800 mt-0.5">{selectedClaim.modifiers?.join(', ') || '—'}</p></div>
            </div>

            {selectedClaim.denial_predicted && (
              <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-xl text-sm">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                Denial predicted · Probability: {(Number(selectedClaim.denial_probability) * 100).toFixed(1)}%
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* ── Edit Claim Modal ─────────────────────────────────────── */}
      <Modal
        open={showEdit && !!selectedClaim}
        onClose={() => setShowEdit(false)}
        title={`Edit Claim CLM-${selectedClaim?.claim_id}`}
        size="md"
        footer={
          <>
            <button onClick={() => setShowEdit(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleEditSave} disabled={actionLoading} className="btn-primary">
              {actionLoading ? 'Saving…' : 'Save Changes'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="label">Charge Amount ($)</label>
            <input
              type="number"
              step="0.01"
              className="input"
              value={editForm.charge_amount}
              onChange={e => setEditForm(prev => ({ ...prev, charge_amount: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">Status</label>
            <select
              className="input"
              value={editForm.status}
              onChange={e => setEditForm(prev => ({ ...prev, status: e.target.value }))}
            >
              {CLAIM_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label">CPT Codes (comma-separated)</label>
            <input
              className="input"
              placeholder="99213, 99214"
              value={editForm.cpt_codes}
              onChange={e => setEditForm(prev => ({ ...prev, cpt_codes: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">ICD-10 Codes (comma-separated)</label>
            <input
              className="input"
              placeholder="I10, E11.9"
              value={editForm.icd10_codes}
              onChange={e => setEditForm(prev => ({ ...prev, icd10_codes: e.target.value }))}
            />
          </div>
        </div>
      </Modal>

      {/* ── New Claim Modal ──────────────────────────────────────── */}
      <Modal
        open={showNewClaim}
        onClose={() => setShowNewClaim(false)}
        title="Create New Claim"
        subtitle="Fill in the claim details below"
        size="lg"
        footer={
          <>
            <button type="button" onClick={() => setShowNewClaim(false)} className="btn-secondary">Cancel</button>
            <button
              form="new-claim-form"
              type="submit"
              disabled={newClaimLoading}
              className="btn-primary"
            >
              {newClaimLoading ? 'Creating…' : 'Create Claim'}
            </button>
          </>
        }
      >
        <form id="new-claim-form" onSubmit={handleCreateClaim} className="space-y-4">
          {newClaimError && (
            <div className="flex items-center gap-2 bg-crimson-50 border border-crimson-200 text-crimson-700 text-sm p-3 rounded-xl">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {newClaimError}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Patient *</label>
              {refData.patients.length > 0 ? (
                <select className="input" value={newClaimForm.patient_id} required
                  onChange={e => {
                    const pid = e.target.value;
                    const patient = refData.patients.find(p => String(p.patient_id) === pid);
                    setNewClaimForm(prev => ({ ...prev, patient_id: pid, payer_id: patient?.payer_id ? String(patient.payer_id) : prev.payer_id }));
                  }}>
                  {refData.patients.map(p => <option key={p.patient_id} value={p.patient_id}>#{p.patient_id} · {p.mrn}</option>)}
                </select>
              ) : (
                <input type="number" className="input" placeholder="Patient ID" value={newClaimForm.patient_id} required
                  onChange={e => setNewClaimForm({ ...newClaimForm, patient_id: e.target.value })} />
              )}
            </div>
            <div>
              <label className="label">Provider *</label>
              {refData.providers.length > 0 ? (
                <select className="input" value={newClaimForm.provider_id} required
                  onChange={e => setNewClaimForm({ ...newClaimForm, provider_id: e.target.value })}>
                  {refData.providers.map(pr => <option key={pr.provider_id} value={pr.provider_id}>{pr.name}{pr.specialty ? ` · ${pr.specialty}` : ''}</option>)}
                </select>
              ) : (
                <input type="number" className="input" placeholder="Provider ID" value={newClaimForm.provider_id} required
                  onChange={e => setNewClaimForm({ ...newClaimForm, provider_id: e.target.value })} />
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Payer *</label>
              {refData.payers.length > 0 ? (
                <select className="input" value={newClaimForm.payer_id} required
                  onChange={e => setNewClaimForm({ ...newClaimForm, payer_id: e.target.value })}>
                  {refData.payers.map(py => <option key={py.payer_id} value={py.payer_id}>{py.name}</option>)}
                </select>
              ) : (
                <input type="number" className="input" placeholder="Payer ID" value={newClaimForm.payer_id} required
                  onChange={e => setNewClaimForm({ ...newClaimForm, payer_id: e.target.value })} />
              )}
            </div>
            <div>
              <label className="label">Date of Service *</label>
              <input type="date" className="input" value={newClaimForm.date_of_service} required
                onChange={e => setNewClaimForm({ ...newClaimForm, date_of_service: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Charge Amount ($) *</label>
            <input type="number" step="0.01" className="input" placeholder="e.g. 250.00" value={newClaimForm.charge_amount} required
              onChange={e => setNewClaimForm({ ...newClaimForm, charge_amount: e.target.value })} />
          </div>
          {aiCodingLoading && (
            <div className="p-3 bg-purple-50 border border-purple-200 rounded-xl flex items-center gap-2.5 text-xs text-purple-800 animate-pulse">
              <Sparkles className="w-4 h-4 text-purple-600 animate-spin flex-shrink-0" />
              <span>AI Medical Coding Specialist (Ling 3.0 Flash Santé) is analyzing clinical encounter and suggesting codes...</span>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="label mb-0">CPT Codes</label>
                <button
                  type="button"
                  onClick={handleAiCodingAssist}
                  disabled={aiCodingLoading}
                  className="inline-flex items-center gap-1 text-2xs font-semibold text-purple-600 hover:text-purple-800 transition-colors"
                >
                  <Sparkles className="w-3 h-3" />
                  {aiCodingLoading ? 'Suggesting...' : 'AI Auto-Code'}
                </button>
              </div>
              <input type="text" className="input" placeholder="99213, 99214" value={newClaimForm.cpt_codes}
                onChange={e => setNewClaimForm({ ...newClaimForm, cpt_codes: e.target.value })} />
            </div>
            <div>
              <label className="label">ICD-10 Codes</label>
              <input type="text" className="input" placeholder="I10, E11.9" value={newClaimForm.icd10_codes}
                onChange={e => setNewClaimForm({ ...newClaimForm, icd10_codes: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="label">Modifiers <span className="text-slate-400 font-normal">(optional)</span></label>
            <input type="text" className="input" placeholder="25, 59" value={newClaimForm.modifiers}
              onChange={e => setNewClaimForm({ ...newClaimForm, modifiers: e.target.value })} />
          </div>
        </form>
      </Modal>
    </div>
  );
}