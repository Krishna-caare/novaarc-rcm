import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { cn, formatDateTime, formatPercent } from '../lib/utils';
import { Bot, Brain, FileText, AlertTriangle, Mail, CheckCircle, Loader2, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

interface AgentRun {
  run_id: number;
  claim_id: number;
  agent_type: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  confidence: number;
  hitl_required: boolean;
  review_decision: string | null;
  reviewed_by: string | null;
  created_at: string;
}

export function AgentsPage() {
  const [pendingReviews, setPendingReviews] = useState<AgentRun[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [reviewDecision, setReviewDecision] = useState<'approved' | 'rejected' | 'edited'>('approved');
  const [editedOutput, setEditedOutput] = useState<Record<string, unknown>>({});
  const [reviewNotes, setReviewNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    fetchPendingReviews();
  }, []);

  const fetchPendingReviews = async () => {
    setReviewsLoading(true);
    try {
      const data = await api.getPendingReviews();
      setPendingReviews(data);
    } catch (err) {
      console.error('Failed to load pending reviews', err);
    } finally {
      setReviewsLoading(false);
    }
  };

  const handleReview = async (run: AgentRun) => {
    setSelectedRun(run);
    setReviewDecision('approved');
    setEditedOutput(run.output_payload);
    setReviewNotes('');
    setAgentRuns([]);
  };

  const submitReview = async () => {
    if (!selectedRun) return;
    setSubmittingReview(true);
    try {
      await api.reviewAgentRun(
        selectedRun.run_id,
        reviewDecision,
        reviewDecision === 'edited' ? editedOutput : undefined,
        reviewNotes
      );
      setSelectedRun(null);
      fetchPendingReviews();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit review');
    } finally {
      setSubmittingReview(false);
    }
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'coding_assist': return <FileText className="w-5 h-5" />;
      case 'denial_classifier': return <AlertTriangle className="w-5 h-5" />;
      case 'appeal_drafter': return <Mail className="w-5 h-5" />;
      case 'eligibility_check': return <Bot className="w-5 h-5" />;
      default: return <Brain className="w-5 h-5" />;
    }
  };

  const getAgentLabel = (type: string) => {
    switch (type) {
      case 'coding_assist': return 'Coding Assist';
      case 'denial_classifier': return 'Denial Predictor';
      case 'appeal_drafter': return 'Appeal Drafter';
      case 'eligibility_check': return 'Eligibility Check';
      default: return type;
    }
  };

  const formatOutput = (output: Record<string, unknown>) => {
    if (output.appeal_letter) return output.appeal_letter as string;
    if (output.icd10_suggestions) {
      return `ICD-10: ${(output.icd10_suggestions as Array<{code: string}>).map(s => s.code).join(', ')} | CPT: ${(output.cpt_suggestions as Array<{code: string}>).map(s => s.code).join(', ')}`;
    }
    if (output.denial_probability !== undefined) {
      return `Probability: ${formatPercent(output.denial_probability as number)} | Risk: ${(output.risk_factors as string[])?.join(', ')}`;
    }
    return JSON.stringify(output, null, 2);
  };

  const renderSelectedRun = () => (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getAgentIcon(selectedRun!.agent_type)}
            <CardTitle>{getAgentLabel(selectedRun!.agent_type)} Review</CardTitle>
          </div>
          <button onClick={() => setSelectedRun(null)} className="p-2 rounded-lg hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-slate-600">Claim</p>
            <p className="font-mono text-slate-900">CLM-{selectedRun!.claim_id}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-600">Run ID</p>
            <p className="font-mono text-slate-900">RUN-{selectedRun!.run_id}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-600">Created</p>
            <p className="text-slate-900">{formatDateTime(selectedRun!.created_at)}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-600">Confidence</p>
            <p className="text-slate-900">{formatPercent(selectedRun!.confidence * 100)}</p>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-slate-600 mb-2">Input</p>
          <pre className="bg-slate-50 p-4 rounded-lg text-sm overflow-x-auto max-h-64 overflow-y-auto">
            {JSON.stringify(selectedRun!.input_payload, null, 2)}
          </pre>
        </div>

        <div>
          <p className="text-sm font-medium text-slate-600 mb-2">Output</p>
          <pre className="bg-slate-50 p-4 rounded-lg text-sm overflow-x-auto max-h-64 overflow-y-auto whitespace-pre-wrap">
            {formatOutput(selectedRun!.output_payload)}
          </pre>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <p className="text-sm font-medium text-slate-600 mb-3">Review Decision</p>
          <div className="flex gap-3 mb-4">
            {(['approved', 'rejected', 'edited'] as const).map((decision) => (
              <button
                key={decision}
                onClick={() => setReviewDecision(decision)}
                className={cn(
                  'flex-1 py-2 px-4 rounded-lg border-2 font-medium transition-colors',
                  reviewDecision === decision
                    ? 'border-primary-600 bg-primary-50 text-primary-700'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                )}
              >
                {decision.charAt(0).toUpperCase() + decision.slice(1)}
              </button>
            ))}
          </div>

          {reviewDecision === 'edited' && (
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-600 mb-2">Edited Output (JSON)</p>
              <textarea
                value={JSON.stringify(editedOutput, null, 2)}
                onChange={(e) => {
                  try {
                    setEditedOutput(JSON.parse(e.target.value));
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
                rows={10}
                className="input font-mono text-sm"
              />
            </div>
          )}

          <div className="mb-4">
            <p className="text-sm font-medium text-slate-600 mb-2">Reviewer Notes</p>
            <textarea
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              rows={3}
              className="input"
              placeholder="Optional notes about your decision..."
            />
          </div>

          <div className="flex justify-end gap-2">
            <button onClick={() => setSelectedRun(null)} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={submitReview}
              disabled={submittingReview}
              className={cn('btn-primary', reviewDecision === 'rejected' && 'bg-red-600 hover:bg-red-700')}
            >
              {submittingReview ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Submit Review
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderAgentRuns = () => (
    <Card>
      <CardHeader>
        <CardTitle>Agent Runs for Claim</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {agentRuns.map((run) => (
            <div key={run.run_id} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getAgentIcon(run.agent_type)}
                  <span className="font-medium text-slate-900">{getAgentLabel(run.agent_type)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn('badge', run.hitl_required ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800')}>
                    {run.hitl_required ? 'HITL Required' : 'Auto'}
                  </span>
                  {run.review_decision && (
                    <span className={cn('badge', 
                      run.review_decision === 'approved' ? 'bg-green-100 text-green-800' :
                      run.review_decision === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800')}>
                      {run.review_decision}
                    </span>
                  )}
                </div>
              </div>
              <div className="mt-2 text-xs text-slate-500">
                Confidence: {formatPercent(run.confidence * 100)} • {formatDateTime(run.created_at)}
                {run.reviewed_by && ` • Reviewed by ${run.reviewed_by}`}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderEmptyState = () => (
    <Card>
      <CardContent className="p-12 text-center">
        <Bot className="w-16 h-16 mx-auto mb-4 text-slate-300" />
        <h3 className="text-lg font-medium text-slate-900 mb-2">Agent Activity</h3>
        <p className="text-slate-500 mb-4">Select a pending review from the left, or view agent runs for a specific claim</p>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 max-w-md mx-auto">
          <div className="p-4 bg-slate-50 rounded-lg text-center">
            <FileText className="w-8 h-8 mx-auto mb-2 text-blue-600" />
            <p className="font-medium text-sm">Coding Assist</p>
            <p className="text-xs text-slate-500">ICD-10/CPT suggestions</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg text-center">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-600" />
            <p className="font-medium text-sm">Denial Predictor</p>
            <p className="text-xs text-slate-500">XGBoost + SHAP</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg text-center">
            <Mail className="w-8 h-8 mx-auto mb-2 text-green-600" />
            <p className="font-medium text-sm">Appeal Drafter</p>
            <p className="text-xs text-slate-500">LLM-generated letters</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg text-center">
            <Bot className="w-8 h-8 mx-auto mb-2 text-purple-600" />
            <p className="font-medium text-sm">Eligibility Check</p>
            <p className="text-xs text-slate-500">Real-time verification</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
          <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Agent Operations</h1>
            <p className="text-slate-600">Monitor and review AI agent activities with human-in-the-loop oversight</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                    Pending Reviews
                  </CardTitle>
                  <span className="badge bg-amber-100 text-amber-800">{pendingReviews.length}</span>
                </div>
              </CardHeader>
              <CardContent>
                {reviewsLoading ? (
                  <div className="space-y-3">
                    {[1,2,3].map(i => <div key={i} className="h-20 bg-slate-100 rounded animate-pulse" />)}
                  </div>
                ) : pendingReviews.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
                    <p>No pending reviews</p>
                    <p className="text-sm">All agent outputs have been reviewed</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {pendingReviews.map((run) => (
                      <div
                        key={run.run_id}
                        className="p-3 bg-slate-50 rounded-lg border border-slate-200 hover:border-primary-300 cursor-pointer transition-colors"
                        onClick={() => handleReview(run)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            {getAgentIcon(run.agent_type)}
                            <span className="font-medium text-sm text-slate-900">{getAgentLabel(run.agent_type)}</span>
                          </div>
                          <span className={cn('badge', run.hitl_required ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800')}>
                            {run.hitl_required ? 'HITL Required' : 'Auto'}
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-slate-500">
                          Claim: CLM-{run.claim_id} • {formatDateTime(run.created_at)}
                        </div>
                        <div className="mt-2 text-xs text-slate-600">
                          Confidence: {formatPercent(run.confidence * 100)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2">
            {selectedRun ? renderSelectedRun() : agentRuns.length > 0 ? renderAgentRuns() : renderEmptyState()}
          </div>
        </div>
      </div>);
}