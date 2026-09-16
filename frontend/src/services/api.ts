import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

declare global {
  interface ImportMetaEnv {
    VITE_API_URL: string;
  }
  interface ImportMeta {
    env: ImportMetaEnv;
  }
}

// In dev: VITE_API_URL is empty → axios uses relative URLs → Vite proxy forwards to Render
// In prod (Netlify / GitHub Pages): fallback to Render backend URL if VITE_API_URL is not set
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? '' : 'https://novaarc-backend.onrender.com');

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          const basePath = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');
          window.location.href = `${basePath}/login`;
        }
        return Promise.reject(error);
      }
    );
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });
    return response.data;
  }

  async register(data: { name: string; email: string; password: string; role: string }) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async getMe() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async getRoles() {
    const response = await this.client.get('/auth/roles');
    return response.data;
  }

  async getUsers() {
    const response = await this.client.get('/auth/users');
    return response.data;
  }

  async listClaims(params?: {
    status?: string;
    payer_id?: number;
    provider_id?: number;
    patient_id?: number;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/claims', { params });
    return response.data;
  }

  async getReferenceData(): Promise<{
    patients: Array<{ patient_id: number; mrn: string; payer_id?: number }>;
    providers: Array<{ provider_id: number; name: string; specialty?: string }>;
    payers: Array<{ payer_id: number; name: string }>;
  }> {
    const response = await this.client.get('/claims/reference-data');
    return response.data;
  }

  async getClaim(claimId: number) {
    const response = await this.client.get(`/claims/${claimId}`);
    return response.data;
  }

  async createClaim(data: {
    patient_id: number;
    provider_id: number;
    payer_id: number;
    date_of_service: string;
    charge_amount: number;
    cpt_codes?: string[];
    icd10_codes?: string[];
    modifiers?: string[];
  }) {
    const response = await this.client.post('/claims', data);
    return response.data;
  }

  async extractClaimDocument(file: File, patientId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (patientId) formData.append('patient_id', patientId);
    const response = await this.client.post('/claims/extract-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async updateClaim(claimId: number, data: Partial<{
    patient_id: number;
    provider_id: number;
    payer_id: number;
    date_of_service: string;
    charge_amount: number;
    paid_amount: number;
    cpt_codes: string[];
    icd10_codes: string[];
    modifiers: string[];
    status: string;
  }>) {
    const response = await this.client.patch(`/claims/${claimId}`, data);
    return response.data;
  }

  async submitClaim(claimId: number) {
    const response = await this.client.post(`/claims/${claimId}/submit`);
    return response.data;
  }

  async getClaimsSummary() {
    const response = await this.client.get('/claims/stats/summary');
    return response.data;
  }

  async getTopDenialCodes(limit = 10) {
    const response = await this.client.get('/denials/top-codes', { params: { limit } });
    return response.data;
  }

  async getDenial(denialId: number) {
    const response = await this.client.get(`/denials/${denialId}`);
    return response.data;
  }

  async updateDenial(denialId: number, data: Partial<{
    denial_code: string;
    description: string;
    denied_amount: number;
    denial_date: string;
    root_cause: string;
    appeal_status: string;
    appeal_drafted_by_ai: boolean;
  }>) {
    const response = await this.client.patch(`/denials/${denialId}`, data);
    return response.data;
  }

  async draftAppeal(denialId: number, additionalContext?: string) {
    const response = await this.client.post(`/denials/${denialId}/draft-appeal`, { additional_context: additionalContext });
    return response.data;
  }

  async listDenials(params?: {
    claim_id?: number;
    denial_code?: string;
    appeal_status?: string;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/denials', { params });
    return response.data;
  }

  async listPayments(params?: {
    claim_id?: number;
    payer_id?: number;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/payments', { params });
    return response.data;
  }

  async createPayment(data: {
    claim_id: number;
    amount: number;
    posted_date?: string;
    remittance_ref?: string;
    payer_id: number;
  }) {
    const response = await this.client.post('/payments', data);
    return response.data;
  }

  async getPayment(paymentId: number) {
    const response = await this.client.get(`/payments/${paymentId}`);
    return response.data;
  }

  async updatePayment(paymentId: number, data: Partial<{
    amount: number;
    posted_date: string;
    remittance_ref: string;
    payer_id: number;
  }>) {
    const response = await this.client.patch(`/payments/${paymentId}`, data);
    return response.data;
  }

  async getPaymentsSummary() {
    const response = await this.client.get('/payments/stats/summary');
    return response.data;
  }

  async getRevenueHealth() {
    const response = await this.client.get('/dashboard/revenue-health');
    return response.data;
  }

  async getARHealth() {
    const response = await this.client.get('/dashboard/ar-health');
    return response.data;
  }

  async getPayerPerformance() {
    const response = await this.client.get('/dashboard/payer-performance');
    return response.data;
  }

  async getDenialIntelligence() {
    const response = await this.client.get('/dashboard/denial-intelligence');
    return response.data;
  }

  async listWorkQueues() {
    const response = await this.client.get('/work-queues');
    return response.data;
  }

  async createWorkQueue(data: { name: string; priority: string; rule_definition?: Record<string, unknown> }) {
    const response = await this.client.post('/work-queues', data);
    return response.data;
  }

  async getWorkQueue(queueId: number) {
    const response = await this.client.get(`/work-queues/${queueId}`);
    return response.data;
  }

  async updateWorkQueue(queueId: number, data: Partial<{ name: string; priority: string; rule_definition: Record<string, unknown> }>) {
    const response = await this.client.patch(`/work-queues/${queueId}`, data);
    return response.data;
  }

  async getQueueClaims(queueId: number) {
    const response = await this.client.get(`/work-queues/${queueId}/claims`);
    return response.data;
  }

  async resolveClaimInQueue(queueId: number, claimId: number) {
    const response = await this.client.post(`/work-queues/${queueId}/claims/${claimId}/resolve`);
    return response.data;
  }

  async codingAssist(clinicalNotes: string, patientContext?: Record<string, unknown>) {
    const response = await this.client.post('/agents/coding-assist', { clinical_notes: clinicalNotes, patient_context: patientContext });
    return response.data;
  }

  async denialPredict(claimId: number) {
    const response = await this.client.post('/agents/denial-predict', { claim_id: claimId });
    return response.data;
  }

  async reviewAgentRun(runId: number, decision: string, editedOutput?: Record<string, unknown>, reviewerNotes?: string) {
    const response = await this.client.post('/agents/review', { run_id: runId, decision, edited_output: editedOutput, reviewer_notes: reviewerNotes });
    return response.data;
  }

  async getPendingReviews(agentType?: string) {
    const response = await this.client.get('/agents/pending-reviews', { params: { agent_type: agentType } });
    return response.data;
  }

  async getAgentRunsForClaim(claimId: number) {
    const response = await this.client.get(`/agents/runs/${claimId}`);
    return response.data;
  }

  async assistantQuery(query: string, context?: Record<string, unknown>) {
    const response = await this.client.post('/assistant/query', { query, context });
    return response.data;
  }
}

export const api = new ApiClient();