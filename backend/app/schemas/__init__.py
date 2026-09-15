from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


class ClaimStatus(str, Enum):
    created = "created"
    submitted = "submitted"
    acknowledged = "acknowledged"
    in_process = "in_process"
    paid = "paid"
    denied = "denied"
    appealed = "appealed"


class AppealStatus(str, Enum):
    not_started = "not_started"
    drafted = "drafted"
    submitted = "submitted"
    won = "won"
    lost = "lost"


class UserRole(str, Enum):
    client_leadership = "client_leadership"
    ops_leadership = "ops_leadership"
    ops_manager = "ops_manager"
    team_lead = "team_lead"
    ar_executive = "ar_executive"
    qa_auditor = "qa_auditor"


class AgentType(str, Enum):
    coding_assist = "coding_assist"
    denial_classifier = "denial_classifier"
    appeal_drafter = "appeal_drafter"
    eligibility_check = "eligibility_check"


class ReviewDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"
    edited = "edited"


class PayerBase(BaseModel):
    name: str
    payer_type: Optional[str] = None
    edi_receiver_id: Optional[str] = None


class PayerCreate(PayerBase):
    pass


class PayerUpdate(PayerBase):
    name: Optional[str] = None


class Payer(PayerBase):
    payer_id: int

    model_config = ConfigDict(from_attributes=True)


class ProviderBase(BaseModel):
    npi: str
    name: str
    specialty: Optional[str] = None


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(ProviderBase):
    npi: Optional[str] = None
    name: Optional[str] = None


class Provider(ProviderBase):
    provider_id: int

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    mrn: str
    dob: Optional[date] = None
    payer_id: Optional[int] = None
    member_id: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    mrn: Optional[str] = None


class Patient(PatientBase):
    patient_id: int

    model_config = ConfigDict(from_attributes=True)


class ClaimBase(BaseModel):
    patient_id: int
    provider_id: int
    payer_id: int
    date_of_service: date
    charge_amount: Decimal
    cpt_codes: List[str] = []
    icd10_codes: List[str] = []
    modifiers: List[str] = []


class ClaimCreate(ClaimBase):
    pass


class ClaimUpdate(BaseModel):
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    payer_id: Optional[int] = None
    date_of_service: Optional[date] = None
    charge_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    cpt_codes: Optional[List[str]] = None
    icd10_codes: Optional[List[str]] = None
    modifiers: Optional[List[str]] = None
    status: Optional[ClaimStatus] = None
    submitted_at: Optional[datetime] = None
    edi_837_ref: Optional[str] = None
    denial_predicted: Optional[bool] = None
    denial_probability: Optional[Decimal] = None


class Claim(ClaimBase):
    claim_id: int
    paid_amount: Decimal
    status: ClaimStatus
    submitted_at: Optional[datetime] = None
    edi_837_ref: Optional[str] = None
    denial_predicted: bool
    denial_probability: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    patient: Optional[Patient] = None
    provider: Optional[Provider] = None
    payer: Optional[Payer] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimDetail(Claim):
    patient: Optional[Patient] = None
    provider: Optional[Provider] = None
    payer: Optional[Payer] = None
    denials: List["Denial"] = []
    payments: List["Payment"] = []
    agent_runs: List["AgentRun"] = []


class DenialBase(BaseModel):
    claim_id: int
    denial_code: Optional[str] = None
    description: Optional[str] = None
    denied_amount: Optional[Decimal] = None
    denial_date: Optional[date] = None
    root_cause: Optional[str] = None


class DenialCreate(DenialBase):
    pass


class DenialUpdate(BaseModel):
    denial_code: Optional[str] = None
    description: Optional[str] = None
    denied_amount: Optional[Decimal] = None
    denial_date: Optional[date] = None
    root_cause: Optional[str] = None
    appeal_status: Optional[AppealStatus] = None
    appeal_drafted_by_ai: Optional[bool] = None


class Denial(DenialBase):
    denial_id: int
    appeal_status: AppealStatus
    appeal_drafted_by_ai: bool

    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    claim_id: int
    amount: Decimal
    posted_date: Optional[date] = None
    remittance_ref: Optional[str] = None
    payer_id: int


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    posted_date: Optional[date] = None
    remittance_ref: Optional[str] = None
    payer_id: Optional[int] = None


class Payment(PaymentBase):
    payment_id: int
    payer: Optional[Payer] = None

    model_config = ConfigDict(from_attributes=True)


class WorkQueueBase(BaseModel):
    name: str
    priority: str = "medium"
    rule_definition: Optional[dict] = None


class WorkQueueCreate(WorkQueueBase):
    pass


class WorkQueueUpdate(WorkQueueBase):
    name: Optional[str] = None


class WorkQueue(WorkQueueBase):
    queue_id: int

    model_config = ConfigDict(from_attributes=True)


class ClaimQueueAssignmentBase(BaseModel):
    claim_id: int
    queue_id: int


class ClaimQueueAssignmentCreate(ClaimQueueAssignmentBase):
    pass


class ClaimQueueAssignment(ClaimQueueAssignmentBase):
    id: int
    assigned_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AgentRunBase(BaseModel):
    claim_id: int
    agent_type: AgentType
    input_payload: dict
    output_payload: dict
    confidence: Decimal
    hitl_required: bool = False


class AgentRunCreate(AgentRunBase):
    pass


class AgentRunUpdate(BaseModel):
    reviewed_by: Optional[str] = None
    review_decision: Optional[ReviewDecision] = None


class AgentRun(AgentRunBase):
    run_id: int
    reviewed_by: Optional[str] = None
    review_decision: Optional[ReviewDecision] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    name: str
    role: UserRole
    email: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    user_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ClaimSubmitRequest(BaseModel):
    claim_id: int


class DenialTopCodesResponse(BaseModel):
    denial_code: str
    count: int
    total_denied_amount: Decimal
    avg_denied_amount: Decimal


class DashboardRevenueHealth(BaseModel):
    ar_outstanding: Decimal
    collected: Decimal
    collection_rate: float
    aging_buckets: dict[str, Decimal]


class DashboardARHealth(BaseModel):
    by_payer: List[dict]
    by_specialty: List[dict]


class DashboardPayerPerformance(BaseModel):
    payer_id: int
    payer_name: str
    total_charged: Decimal
    total_paid: Decimal
    avg_days_to_pay: float
    denial_rate: float


class WorkQueueSummary(BaseModel):
    queue_id: int
    name: str
    priority: str
    claim_count: int
    total_value: Decimal


class CodingAssistRequest(BaseModel):
    clinical_notes: str
    patient_context: Optional[dict] = None


class CodingAssistResponse(BaseModel):
    icd10_suggestions: List[dict]
    cpt_suggestions: List[dict]
    confidence: Decimal
    hitl_required: bool


class DenialPredictRequest(BaseModel):
    claim_id: int


class DenialPredictResponse(BaseModel):
    denial_probability: Decimal
    shap_explanation: dict
    risk_factors: List[str]
    hitl_required: bool


class AppealDraftRequest(BaseModel):
    denial_id: Optional[int] = None
    additional_context: Optional[str] = None


class AppealDraftResponse(BaseModel):
    appeal_letter: str
    confidence: Decimal
    hitl_required: bool


class AgentReviewRequest(BaseModel):
    run_id: int
    decision: ReviewDecision
    edited_output: Optional[dict] = None
    reviewer_notes: Optional[str] = None


class AssistantQueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None


class AssistantQueryResponse(BaseModel):
    intent: str
    response: str
    data: Optional[dict] = None
    follow_up_suggestions: List[str] = []


ClaimDetail.model_rebuild()
Denial.model_rebuild()
Payment.model_rebuild()
AgentRun.model_rebuild()