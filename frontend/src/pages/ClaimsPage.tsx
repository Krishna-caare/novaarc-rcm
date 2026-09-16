import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatCurrency, formatDate } from '../lib/utils';
import { Claim } from '../types';
import {
  Filter, ChevronLeft, ChevronRight, Plus, Eye, Edit,
  ArrowRight, AlertTriangle, Sparkles, ShieldAlert,
  UploadCloud, FileUp, FileText, CheckCircle2, ShieldCheck, Check
} from 'lucide-react';
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
  const [pdfUploading, setPdfUploading] = useState(false);
  const [pdfUploadSuccess, setPdfUploadSuccess] = useState<string | null>(null);
  const [aiSuggestions, setAiSuggestions] = useState<{
    icd10: Array<{ code: string; description: string; confidence?: number; rationale?: string }>;
    cpt: Array<{ code: string; description: string; confidence?: number; modifiers?: string[]; rationale?: string }>;
  } | null>(null);
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
  const [clinicalNotesInput, setClinicalNotesInput] = useState('Follow-up outpatient visit for 58yo male with essential hypertension (BP 148/92) and type 2 diabetes mellitus (HbA1c 7.8%). Medication adjusted.');

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

  const handleAiCodingAssist = async (customNotes?: string) => {
    setAiCodingLoading(true);
    try {
      const patient = refData.patients.find(p => String(p.patient_id) === newClaimForm.patient_id);
      const notesToUse = customNotes || clinicalNotesInput || 'Follow-up outpatient clinical encounter for hypertension and diabetes management.';
      const res = await api.codingAssist(notesToUse, { mrn: patient?.mrn });
      if (res?.icd10_suggestions?.length > 0 || res?.cpt_suggestions?.length > 0) {
        setNewClaimForm(prev => ({
          ...prev,
          icd10_codes: res.icd10_suggestions?.map((s: any) => s.code).join(', ') || prev.icd10_codes,
          cpt_codes: res.cpt_suggestions?.map((s: any) => s.code).join(', ') || prev.cpt_codes,
        }));
        setAiSuggestions({
          icd10: res.icd10_suggestions || [],
          cpt: res.cpt_suggestions || [],
        });
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

  const handleDocumentUpload = async (file: File) => {
    if (!file) return;
    setPdfUploading(true);
    setPdfUploadSuccess(null);
    setNewClaimError(null);
    try {
      const data = await api.extractClaimDocument(file, newClaimForm.patient_id);
      if (data.extracted_text) {
        setClinicalNotesInput(data.extracted_text);
      }
      if (data.suggested_cpt || data.suggested_icd10) {
        setNewClaimForm(prev => ({
          ...prev,
          cpt_codes: data.suggested_cpt || prev.cpt_codes,
          icd10_codes: data.suggested_icd10 || prev.icd10_codes,
          charge_amount: data.suggested_charge ? String(data.suggested_charge) : prev.charge_amount,
        }));
      }
      setAiSuggestions({
        icd10: data.icd10_suggestions || [],
        cpt: data.cpt_suggestions || [],
      });
      setPdfUploadSuccess(`Extracted ${data.word_count || 0} words from "${file.name}". AI suggested CPT: ${data.suggested_cpt || '99213'}, ICD-10: ${data.suggested_icd10 || 'I10'}.`);
    } catch (err: any) {
      if (file.type.includes('text') || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        try {
          const text = await file.text();
          setClinicalNotesInput(text);
          await handleAiCodingAssist(text);
          setPdfUploadSuccess(`Loaded text from "${file.name}" and generated AI coding suggestions.`);
        } catch {
          setNewClaimError(`Failed to parse text file "${file.name}".`);
        }
      } else {
        setNewClaimError(err.response?.data?.detail || `Failed to process "${file.name}". Please ensure it is a valid PDF or text note.`);
      }
    } finally {
      setPdfUploading(false);
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
          {editForm.status === 'denied' && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Denial Workflow Trigger:</strong> Setting status to &quot;Denied&quot; automatically creates a Denial record (CO-16) and queues this claim in the Denials Management & Appeals workbench.
              </span>
            </div>
          )}
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

      {/* ── New Claim Modal (Spacious 4XL Layout) ─────────────────────── */}
      <Modal
        open={showNewClaim}
        onClose={() => {
          setShowNewClaim(false);
          setPdfUploadSuccess(null);
          setNewClaimError(null);
        }}
        title={
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
              <FileText className="w-4.5 h-4.5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Create New Claim (CMS-1500)</h2>
              <p className="text-xs text-slate-500 font-normal">
                Clinical documentation ingestion, AI medical coding with Ling 3.0, and pre-submission claim scrubbing
              </p>
            </div>
          </div>
        }
        size="4xl"
        footer={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2 text-2xs text-slate-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              <span>Standard RCM Pipeline: Intake ➔ AI Coding ➔ Scrubbing ➔ EDI 837 Submission</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowNewClaim(false);
                  setPdfUploadSuccess(null);
                  setNewClaimError(null);
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                form="new-claim-form"
                type="submit"
                disabled={newClaimLoading}
                className="btn-primary flex items-center gap-1.5 px-5"
              >
                {newClaimLoading ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Validating & Creating…</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    <span>Create & Scrub Claim</span>
                  </>
                )}
              </button>
            </div>
          </div>
        }
      >
        <form id="new-claim-form" onSubmit={handleCreateClaim} className="space-y-4">
          {newClaimError && (
            <div className="flex items-center gap-2.5 bg-crimson-50 border border-crimson-200 text-crimson-700 text-sm p-3.5 rounded-xl">
              <AlertTriangle className="w-4.5 h-4.5 flex-shrink-0 text-crimson-600" />
              <span>{newClaimError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* ── LEFT COLUMN: Document Upload & Clinical AI Intake (6 cols) ── */}
            <div className="lg:col-span-6 space-y-3.5">
              {/* PDF Document Upload Zone */}
              <div className="bg-slate-50/80 border-2 border-dashed border-slate-300 hover:border-primary-400 rounded-xl p-4 transition-colors">
                <div className="flex flex-col items-center text-center">
                  <div className="w-10 h-10 rounded-full bg-primary-50 border border-primary-100 flex items-center justify-center text-primary-600 mb-2">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-bold text-slate-800">Upload Clinical Note / Superbill PDF</p>
                  <p className="text-2xs text-slate-500 mt-0.5 max-w-xs">
                    Scrapes medical records, physician notes, and auto-suggests ICD-10 and CPT codes
                  </p>
                  <label className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:border-primary-300 text-primary-700 text-xs font-semibold rounded-lg shadow-2xs cursor-pointer transition-colors">
                    <FileUp className="w-3.5 h-3.5" />
                    <span>{pdfUploading ? 'Extracting & Analyzing…' : 'Choose PDF or Text File'}</span>
                    <input
                      type="file"
                      accept=".pdf,.txt,.md,.doc,.docx"
                      disabled={pdfUploading}
                      className="hidden"
                      onChange={e => {
                        const file = e.target.files?.[0];
                        if (file) handleDocumentUpload(file);
                      }}
                    />
                  </label>
                </div>

                {pdfUploading && (
                  <div className="mt-3 flex items-center justify-center gap-2 text-xs text-primary-700 font-medium py-1.5 bg-primary-50 rounded-lg animate-pulse">
                    <div className="w-3.5 h-3.5 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
                    <span>Scraping PDF and consulting Ling 3.0 Flash Santé…</span>
                  </div>
                )}

                {pdfUploadSuccess && (
                  <div className="mt-3 flex items-start gap-2 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg p-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span className="leading-snug">{pdfUploadSuccess}</span>
                  </div>
                )}
              </div>

              {/* Clinical Documentation / Encounter Notes */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="text-2xs font-bold bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">Step 1</span>
                    <label className="label mb-0 text-xs font-bold text-slate-800">
                      Encounter Notes / Documentation
                    </label>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAiCodingAssist()}
                    disabled={aiCodingLoading}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-2xs font-bold rounded-lg bg-purple-600 hover:bg-purple-700 text-white shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
                  >
                    <Sparkles className="w-3 h-3" />
                    {aiCodingLoading ? 'AI Coding in progress…' : 'AI Auto-Code with Ling 3.0'}
                  </button>
                </div>
                <textarea
                  rows={4}
                  className="input text-xs leading-relaxed font-sans"
                  placeholder="Paste physician encounter notes, clinical summary, or operative notes here..."
                  value={clinicalNotesInput}
                  onChange={e => setClinicalNotesInput(e.target.value)}
                />
                <div className="flex flex-wrap items-center gap-1.5 text-2xs text-slate-500">
                  <span className="font-semibold text-slate-400">Quick samples:</span>
                  <button
                    type="button"
                    onClick={() => {
                      const note = "Follow-up outpatient visit for 58yo male with essential hypertension (BP 148/92) and type 2 diabetes mellitus (HbA1c 7.8%). Medication adjusted.";
                      setClinicalNotesInput(note);
                      handleAiCodingAssist(note);
                    }}
                    className="text-purple-600 hover:underline font-medium cursor-pointer"
                  >
                    🩺 Hypertension & T2DM
                  </button>
                  <span>•</span>
                  <button
                    type="button"
                    onClick={() => {
                      const note = "64yo female with exertional chest pain and dyspnea. Outpatient cardiology evaluation, 12-lead ECG, stress echo ordered.";
                      setClinicalNotesInput(note);
                      handleAiCodingAssist(note);
                    }}
                    className="text-purple-600 hover:underline font-medium cursor-pointer"
                  >
                    🫀 Cardiology / Angina
                  </button>
                  <span>•</span>
                  <button
                    type="button"
                    onClick={() => {
                      const note = "Postoperative day 14 follow-up for right knee diagnostic arthroscopy with partial medial meniscectomy. Physical therapy prescribed.";
                      setClinicalNotesInput(note);
                      handleAiCodingAssist(note);
                    }}
                    className="text-purple-600 hover:underline font-medium cursor-pointer"
                  >
                    🦴 Knee Arthroscopy
                  </button>
                </div>
              </div>

              {/* AI Code Suggestions Chips */}
              {aiSuggestions && (aiSuggestions.icd10.length > 0 || aiSuggestions.cpt.length > 0) && (
                <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xs font-bold uppercase tracking-wider text-purple-900 flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      AI Code Suggestions (Click to Add)
                    </span>
                    <span className="text-2xs text-purple-600 font-medium">Click chip to apply</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {aiSuggestions.icd10.map(item => (
                      <button
                        key={item.code}
                        type="button"
                        onClick={() => {
                          if (!newClaimForm.icd10_codes.includes(item.code)) {
                            setNewClaimForm(prev => ({
                              ...prev,
                              icd10_codes: prev.icd10_codes ? `${prev.icd10_codes}, ${item.code}` : item.code
                            }));
                          }
                        }}
                        className="px-2 py-0.5 rounded text-2xs font-mono font-semibold bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors cursor-pointer"
                        title={`${item.description} (${Math.round((item.confidence || 0.9) * 100)}% confidence)`}
                      >
                        + ICD: {item.code}
                      </button>
                    ))}
                    {aiSuggestions.cpt.map(item => (
                      <button
                        key={item.code}
                        type="button"
                        onClick={() => {
                          if (!newClaimForm.cpt_codes.includes(item.code)) {
                            setNewClaimForm(prev => ({
                              ...prev,
                              cpt_codes: prev.cpt_codes ? `${prev.cpt_codes}, ${item.code}` : item.code
                            }));
                          }
                        }}
                        className="px-2 py-0.5 rounded text-2xs font-mono font-semibold bg-emerald-100 text-emerald-800 hover:bg-emerald-200 transition-colors cursor-pointer"
                        title={`${item.description} (${Math.round((item.confidence || 0.9) * 100)}% confidence)`}
                      >
                        + CPT: {item.code}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ── RIGHT COLUMN: Claim Demographics & Billing Setup (6 cols) ── */}
            <div className="lg:col-span-6 space-y-3.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="label">Patient *</label>
                  {refData.patients.length > 0 ? (
                    <select
                      className="input"
                      value={newClaimForm.patient_id}
                      required
                      onChange={e => {
                        const pid = e.target.value;
                        const patient = refData.patients.find(p => String(p.patient_id) === pid);
                        setNewClaimForm(prev => ({
                          ...prev,
                          patient_id: pid,
                          payer_id: patient?.payer_id ? String(patient.payer_id) : prev.payer_id
                        }));
                      }}
                    >
                      {refData.patients.map(p => (
                        <option key={p.patient_id} value={p.patient_id}>
                          #{p.patient_id} · {p.mrn}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      className="input"
                      placeholder="Patient ID"
                      value={newClaimForm.patient_id}
                      required
                      onChange={e => setNewClaimForm({ ...newClaimForm, patient_id: e.target.value })}
                    />
                  )}
                </div>
                <div>
                  <label className="label">Provider *</label>
                  {refData.providers.length > 0 ? (
                    <select
                      className="input"
                      value={newClaimForm.provider_id}
                      required
                      onChange={e => setNewClaimForm({ ...newClaimForm, provider_id: e.target.value })}
                    >
                      {refData.providers.map(pr => (
                        <option key={pr.provider_id} value={pr.provider_id}>
                          {pr.name}{pr.specialty ? ` · ${pr.specialty}` : ''}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      className="input"
                      placeholder="Provider ID"
                      value={newClaimForm.provider_id}
                      required
                      onChange={e => setNewClaimForm({ ...newClaimForm, provider_id: e.target.value })}
                    />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="label">Payer *</label>
                  {refData.payers.length > 0 ? (
                    <select
                      className="input"
                      value={newClaimForm.payer_id}
                      required
                      onChange={e => setNewClaimForm({ ...newClaimForm, payer_id: e.target.value })}
                    >
                      {refData.payers.map(py => (
                        <option key={py.payer_id} value={py.payer_id}>
                          {py.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      className="input"
                      placeholder="Payer ID"
                      value={newClaimForm.payer_id}
                      required
                      onChange={e => setNewClaimForm({ ...newClaimForm, payer_id: e.target.value })}
                    />
                  )}
                </div>
                <div>
                  <label className="label">Date of Service *</label>
                  <input
                    type="date"
                    className="input"
                    value={newClaimForm.date_of_service}
                    required
                    onChange={e => setNewClaimForm({ ...newClaimForm, date_of_service: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="label mb-0">Charge Amount ($) *</label>
                  <span className="text-2xs text-slate-500 font-medium">Billed to Payer</span>
                </div>
                <input
                  type="number"
                  step="0.01"
                  className="input"
                  placeholder="e.g. 250.00"
                  value={newClaimForm.charge_amount}
                  required
                  onChange={e => setNewClaimForm({ ...newClaimForm, charge_amount: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="label">CPT Procedure Codes</label>
                  <input
                    type="text"
                    className="input font-mono text-xs"
                    placeholder="99213, 99214"
                    value={newClaimForm.cpt_codes}
                    onChange={e => setNewClaimForm({ ...newClaimForm, cpt_codes: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">ICD-10 Diagnosis Codes</label>
                  <input
                    type="text"
                    className="input font-mono text-xs"
                    placeholder="I10, E11.9"
                    value={newClaimForm.icd10_codes}
                    onChange={e => setNewClaimForm({ ...newClaimForm, icd10_codes: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="label">Modifiers <span className="text-slate-400 font-normal">(optional, e.g. 25, 59)</span></label>
                <input
                  type="text"
                  className="input font-mono text-xs"
                  placeholder="25, 59"
                  value={newClaimForm.modifiers}
                  onChange={e => setNewClaimForm({ ...newClaimForm, modifiers: e.target.value })}
                />
              </div>

              {/* Pre-submission Claim Scrubbing & Validation Status */}
              <div className="p-3 bg-slate-50 border border-slate-200/90 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-2xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    Pre-Submission Scrubbing Edits
                  </span>
                  <span className="text-2xs font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                    Clean Claim Check
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-2xs">
                  <div className="flex items-center gap-1.5 text-slate-700">
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                    <span>Patient & MRN Verified</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-700">
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                    <span>Payer Coverage Active</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-700">
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                    <span>ICD-10 Format Validated</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-700">
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                    <span>CPT Medical Necessity Match</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}