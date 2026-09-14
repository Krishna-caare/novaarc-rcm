import enum
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Numeric, Boolean,
    ForeignKey, Index, Enum as SQLEnum, ARRAY, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship, declared_attr
from app.core.database import Base


class ClaimStatus(str, enum.Enum):
    created = "created"
    submitted = "submitted"
    acknowledged = "acknowledged"
    in_process = "in_process"
    paid = "paid"
    denied = "denied"
    appealed = "appealed"


class AppealStatus(str, enum.Enum):
    not_started = "not_started"
    drafted = "drafted"
    submitted = "submitted"
    won = "won"
    lost = "lost"


class UserRole(str, enum.Enum):
    client_leadership = "client_leadership"
    ops_leadership = "ops_leadership"
    ops_manager = "ops_manager"
    team_lead = "team_lead"
    ar_executive = "ar_executive"
    qa_auditor = "qa_auditor"


class AgentType(str, enum.Enum):
    coding_assist = "coding_assist"
    denial_classifier = "denial_classifier"
    appeal_drafter = "appeal_drafter"
    eligibility_check = "eligibility_check"


class ReviewDecision(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    edited = "edited"


class Payer(Base):
    __tablename__ = "payers"

    payer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    payer_type = Column(String(50))
    edi_receiver_id = Column(String(50))

    claims = relationship("Claim", back_populates="payer")
    payments = relationship("Payment", back_populates="payer")
    patients = relationship("Patient", back_populates="payer")


class Provider(Base):
    __tablename__ = "providers"

    provider_id = Column(Integer, primary_key=True, index=True)
    npi = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    specialty = Column(String(100))

    claims = relationship("Claim", back_populates="provider")


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(50), unique=True, nullable=False, index=True)
    dob = Column(Date)
    payer_id = Column(Integer, ForeignKey("payers.payer_id"))
    member_id = Column(String(50))

    payer = relationship("Payer", back_populates="patients")
    claims = relationship("Claim", back_populates="patient")


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.provider_id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("payers.payer_id"), nullable=False)
    date_of_service = Column(Date, nullable=False, index=True)
    charge_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0)
    cpt_codes = Column(ARRAY(Text))
    icd10_codes = Column(ARRAY(Text))
    modifiers = Column(ARRAY(Text))
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.created, nullable=False, index=True)
    submitted_at = Column(DateTime)
    edi_837_ref = Column(String(100))
    denial_predicted = Column(Boolean, default=False)
    denial_probability = Column(Numeric(5, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="claims")
    provider = relationship("Provider", back_populates="claims")
    payer = relationship("Payer", back_populates="claims")
    denials = relationship("Denial", back_populates="claim")
    payments = relationship("Payment", back_populates="claim")
    queue_assignments = relationship("ClaimQueueAssignment", back_populates="claim")
    agent_runs = relationship("AgentRun", back_populates="claim")


class Denial(Base):
    __tablename__ = "denials"

    denial_id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.claim_id"), nullable=False)
    denial_code = Column(String(20))
    description = Column(Text)
    denied_amount = Column(Numeric(12, 2))
    denial_date = Column(Date)
    root_cause = Column(String(100))
    appeal_status = Column(SQLEnum(AppealStatus), default=AppealStatus.not_started)
    appeal_drafted_by_ai = Column(Boolean, default=False)

    claim = relationship("Claim", back_populates="denials")


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.claim_id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    posted_date = Column(Date)
    remittance_ref = Column(String(100))
    payer_id = Column(Integer, ForeignKey("payers.payer_id"))

    claim = relationship("Claim", back_populates="payments")
    payer = relationship("Payer", back_populates="payments")


class WorkQueue(Base):
    __tablename__ = "work_queues"

    queue_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    priority = Column(String(20), default="medium")
    rule_definition = Column(JSON)

    assignments = relationship("ClaimQueueAssignment", back_populates="queue")


class ClaimQueueAssignment(Base):
    __tablename__ = "claim_queue_assignments"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.claim_id"), nullable=False)
    queue_id = Column(Integer, ForeignKey("work_queues.queue_id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    claim = relationship("Claim", back_populates="queue_assignments")
    queue = relationship("WorkQueue", back_populates="assignments")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.claim_id"), nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    input_payload = Column(JSON)
    output_payload = Column(JSON)
    confidence = Column(Numeric(5, 4))
    hitl_required = Column(Boolean, default=False)
    reviewed_by = Column(String(100))
    review_decision = Column(SQLEnum(ReviewDecision))
    created_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("Claim", back_populates="agent_runs")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


Index("idx_claims_status", Claim.status)
Index("idx_claims_payer", Claim.payer_id)
Index("idx_claims_dos", Claim.date_of_service)