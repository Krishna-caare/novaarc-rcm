export type ClaimStatus = 
  | 'created' 
  | 'submitted' 
  | 'acknowledged' 
  | 'in_process' 
  | 'paid' 
  | 'denied' 
  | 'appealed';

export type AppealStatus = 
  | 'not_started' 
  | 'drafted' 
  | 'submitted' 
  | 'won' 
  | 'lost';

export type UserRole = 
  | 'client_leadership' 
  | 'ops_leadership' 
  | 'ops_manager' 
  | 'team_lead' 
  | 'ar_executive' 
  | 'qa_auditor';

export interface Payer {
  payer_id: number;
  name: string;
  payer_type: string | null;
  edi_receiver_id: string | null;
}

export interface Provider {
  provider_id: number;
  npi: string;
  name: string;
  specialty: string | null;
}

export interface Patient {
  patient_id: number;
  mrn: string;
  dob: string | null;
  payer_id: number | null;
  member_id: string | null;
}

export interface Claim {
  claim_id: number;
  patient_id: number;
  provider_id: number;
  payer_id: number;
  date_of_service: string;
  charge_amount: number;
  paid_amount: number;
  cpt_codes: string[];
  icd10_codes: string[];
  modifiers: string[];
  status: ClaimStatus;
  submitted_at: string | null;
  edi_837_ref: string | null;
  denial_predicted: boolean;
  denial_probability: number | null;
  created_at: string;
  updated_at: string;
  patient?: Patient;
  provider?: Provider;
  payer?: Payer;
  denials?: Denial[];
  payments?: Payment[];
  agent_runs?: AgentRun[];
}

export interface Denial {
  denial_id: number;
  claim_id: number;
  denial_code: string | null;
  description: string | null;
  denied_amount: number | null;
  denial_date: string | null;
  root_cause: string | null;
  appeal_status: AppealStatus;
  appeal_drafted_by_ai: boolean;
}

export interface Payment {
  payment_id: number;
  claim_id: number;
  amount: number;
  posted_date: string | null;
  remittance_ref: string | null;
  payer_id: number;
}

export interface WorkQueue {
  queue_id: number;
  name: string;
  priority: string;
  rule_definition: Record<string, unknown> | null;
}

export interface WorkQueueSummary {
  queue_id: number;
  name: string;
  priority: string;
  claim_count: number;
  total_value: number;
}

export interface ClaimQueueAssignment {
  id: number;
  claim_id: number;
  queue_id: number;
  assigned_at: string;
  resolved_at: string | null;
}

export interface AgentRun {
  run_id: number;
  claim_id: number;
  agent_type: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  confidence: number;
  hitl_required: boolean;
  reviewed_by: string | null;
  review_decision: string | null;
  created_at: string;
}

export interface User {
  user_id: number;
  name: string;
  role: UserRole;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface DashboardRevenueHealth {
  ar_outstanding: number;
  collected: number;
  collection_rate: number;
  aging_buckets: Record<string, number>;
}

export interface DashboardARHealth {
  by_payer: Array<{
    payer_id: number;
    payer_name: string;
    ar_outstanding: number;
    claim_count: number;
    avg_days_outstanding: number;
  }>;
  by_specialty: Array<{
    specialty: string;
    ar_outstanding: number;
    claim_count: number;
    avg_days_outstanding: number;
  }>;
}

export interface DashboardPayerPerformance {
  payer_id: number;
  payer_name: string;
  total_charged: number;
  total_paid: number;
  avg_days_to_pay: number;
  denial_rate: number;
  collection_rate: number;
}

export interface DenialIntelligence {
  top_codes: Array<{
    denial_code: string;
    count: number;
    total_denied: number;
    avg_denied: number;
  }>;
  monthly_trend: Array<{
    month: string;
    count: number;
    total_denied: number;
  }>;
  by_root_cause: Array<{
    root_cause: string;
    count: number;
    total_denied: number;
  }>;
}

export interface CodingAssistResponse {
  icd10_suggestions: Array<{
    code: string;
    description: string;
    confidence: number;
    rationale: string;
  }>;
  cpt_suggestions: Array<{
    code: string;
    description: string;
    confidence: number;
    modifiers: string[];
    rationale: string;
  }>;
  documentation_gaps: string[];
  overall_confidence: number;
  hitl_required: boolean;
}

export interface DenialPredictResponse {
  denial_probability: number;
  shap_explanation: Record<string, number>;
  risk_factors: string[];
  hitl_required: boolean;
}

export interface AppealDraftResponse {
  appeal_letter: string;
  confidence: number;
  hitl_required: boolean;
}

export interface AssistantQueryResponse {
  intent: string;
  response: string;
  data?: Record<string, unknown>;
  follow_up_suggestions: string[];
}

export interface ClaimsSummary {
  total_claims: number;
  by_status: Array<{
    status: string;
    count: number;
    total_charges: number;
  }>;
  total_charges: number;
  total_paid: number;
  collection_rate: number;
}