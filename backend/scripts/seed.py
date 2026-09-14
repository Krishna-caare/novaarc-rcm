import asyncio
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.models import (
    Payer, Provider, Patient, Claim, Denial, Payment,
    WorkQueue, ClaimQueueAssignment, User, UserRole, ClaimStatus, AppealStatus
)
from app.core.auth import get_password_hash

fake = Faker()
Faker.seed(42)
random.seed(42)


PAYERS = [
    {"name": "Blue Cross Blue Shield", "payer_type": "Commercial", "edi_receiver_id": "BCBS001"},
    {"name": "UnitedHealthcare", "payer_type": "Commercial", "edi_receiver_id": "UHC001"},
    {"name": "Aetna", "payer_type": "Commercial", "edi_receiver_id": "AET001"},
    {"name": "Cigna", "payer_type": "Commercial", "edi_receiver_id": "CIG001"},
    {"name": "Humana", "payer_type": "Commercial", "edi_receiver_id": "HUM001"},
    {"name": "Medicare", "payer_type": "Government", "edi_receiver_id": "MCR001"},
    {"name": "Medicaid", "payer_type": "Government", "edi_receiver_id": "MCD001"},
    {"name": "Kaiser Permanente", "payer_type": "Commercial", "edi_receiver_id": "KP001"},
]

PROVIDERS = [
    {"npi": "1234567890", "name": "Dr. Sarah Johnson", "specialty": "Cardiology"},
    {"npi": "1234567891", "name": "Dr. Michael Chen", "specialty": "Orthopedics"},
    {"npi": "1234567892", "name": "Dr. Emily Rodriguez", "specialty": "Primary Care"},
    {"npi": "1234567893", "name": "Dr. James Wilson", "specialty": "Radiology"},
    {"npi": "1234567894", "name": "Dr. Lisa Anderson", "specialty": "Cardiology"},
    {"npi": "1234567895", "name": "Dr. Robert Taylor", "specialty": "Orthopedics"},
    {"npi": "1234567896", "name": "Dr. Jennifer Martinez", "specialty": "Primary Care"},
    {"npi": "1234567897", "name": "Dr. David Brown", "specialty": "Radiology"},
    {"npi": "1234567898", "name": "Dr. Amanda Davis", "specialty": "Cardiology"},
    {"npi": "1234567899", "name": "Dr. Christopher Miller", "specialty": "Orthopedics"},
]

CPT_CODES = [
    "99213", "99214", "99215", "99203", "99204", "99205",
    "93000", "93010", "93306", "93307", "93308",
    "71045", "71046", "72100", "72110", "73030",
    "20610", "20550", "20551", "20552", "20553",
    "97110", "97112", "97116", "97530", "97140",
    "99283", "99284", "99285", "99291", "99292",
]

ICD10_CODES = [
    "I10", "I25.10", "I50.9", "I48.91", "I20.9",
    "M79.1", "M25.511", "M25.512", "M25.561", "M25.562",
    "M54.5", "M54.2", "M54.16", "M54.17", "M48.00",
    "E11.9", "E11.65", "E11.22", "E11.40", "E78.5",
    "J44.1", "J45.909", "J18.9", "R05", "R06.02",
    "Z00.00", "Z01.818", "Z12.11", "Z13.6", "Z23",
    "G89.29", "G44.1", "R51", "R10.9", "R19.7",
]

MODIFIERS = ["25", "59", "51", "76", "77", "78", "79", "24", "26", "TC"]

DENIAL_CODES = [
    {"code": "CO-16", "description": "Claim/service lacks information or has submission/billing error(s)", "root_cause": "Missing Information"},
    {"code": "CO-18", "description": "Exact duplicate claim/service", "root_cause": "Duplicate Claim"},
    {"code": "CO-27", "description": "Expenses incurred after coverage terminated", "root_cause": "Coverage Terminated"},
    {"code": "CO-45", "description": "Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement", "root_cause": "Contractual Adjustment"},
    {"code": "CO-97", "description": "The benefit for this service is included in the payment/allowance for another service/procedure", "root_cause": "Bundling"},
    {"code": "CO-109", "description": "Claim not covered by this payer/contractor", "root_cause": "Not Covered"},
    {"code": "CO-119", "description": "Benefit maximum for this time period has been reached", "root_cause": "Benefit Maximum"},
    {"code": "CO-151", "description": "Payment adjusted because the payer deems the information submitted does not support this level of service", "root_cause": "Medical Necessity"},
    {"code": "CO-167", "description": "This diagnosis is not covered", "root_cause": "Diagnosis Not Covered"},
    {"code": "CO-204", "description": "This service/equipment/drug is not covered under the patient's current benefit plan", "root_cause": "Plan Exclusion"},
    {"code": "CO-226", "description": "Information requested from the Billing/Rendering Provider was not provided or was insufficient", "root_cause": "Missing Documentation"},
    {"code": "CO-234", "description": "This service/procedure is not paid separately", "root_cause": "Bundling"},
    {"code": "CO-252", "description": "An attachment/other documentation is required to adjudicate this claim/service", "root_cause": "Missing Documentation"},
    {"code": "CO-256", "description": "Service not payable per managed care contract", "root_cause": "Contractual"},
    {"code": "PR-1", "description": "Deductible amount", "root_cause": "Patient Responsibility"},
    {"code": "PR-2", "description": "Coinsurance amount", "root_cause": "Patient Responsibility"},
    {"code": "PR-3", "description": "Copayment amount", "root_cause": "Patient Responsibility"},
]

WORK_QUEUES = [
    {"name": "New Claims - Review", "priority": "high", "rule_definition": {"status": ["created"], "auto_assign": True}},
    {"name": "High Risk - Denial Prevention", "priority": "critical", "rule_definition": {"denial_probability": {"gt": 0.7}, "auto_assign": True}},
    {"name": "Denials - Work", "priority": "high", "rule_definition": {"status": ["denied"], "appeal_status": ["not_started"]}},
    {"name": "Appeals - Drafting", "priority": "high", "rule_definition": {"appeal_status": ["not_started", "drafted"]}},
    {"name": "Appeals - Follow-up", "priority": "medium", "rule_definition": {"appeal_status": ["submitted"]}},
    {"name": "Aging - 30-60 Days", "priority": "medium", "rule_definition": {"days_outstanding": {"gte": 30, "lt": 60}}},
    {"name": "Aging - 60+ Days", "priority": "high", "rule_definition": {"days_outstanding": {"gte": 60}}},
]


async def seed_payers(db: AsyncSession) -> list[Payer]:
    payers = []
    for p in PAYERS:
        payer = Payer(**p)
        db.add(payer)
        payers.append(payer)
    await db.flush()
    return payers


async def seed_providers(db: AsyncSession) -> list[Provider]:
    providers = []
    for p in PROVIDERS:
        provider = Provider(**p)
        db.add(provider)
        providers.append(provider)
    await db.flush()
    return providers


async def seed_patients(db: AsyncSession, payers: list[Payer]) -> list[Patient]:
    patients = []
    for _ in range(200):
        payer = random.choice(payers)
        patient = Patient(
            mrn=f"MRN{random.randint(100000, 999999)}",
            dob=fake.date_between(start_date='-80y', end_date='-18y'),
            payer_id=payer.payer_id,
            member_id=f"MEM{random.randint(100000, 999999)}"
        )
        db.add(patient)
        patients.append(patient)
    await db.flush()
    return patients


async def seed_claims(db: AsyncSession, patients: list[Patient], providers: list[Provider], payers: list[Payer]) -> list[Claim]:
    claims = []
    statuses = list(ClaimStatus)
    
    for i in range(300):
        patient = random.choice(patients)
        provider = random.choice(providers)
        payer = random.choice(payers)
        
        dos = fake.date_between(start_date='-1y', end_date='today')
        charge = Decimal(str(round(random.uniform(100, 15000), 2)))
        
        num_cpt = random.randint(1, 5)
        cpt_codes = random.sample(CPT_CODES, num_cpt)
        
        num_icd = random.randint(1, 4)
        icd10_codes = random.sample(ICD10_CODES, num_icd)
        
        num_mod = random.randint(0, 2)
        modifiers = random.sample(MODIFIERS, num_mod) if num_mod > 0 else []
        
        status = random.choices(statuses, weights=[5, 20, 15, 25, 10, 15, 10])[0]
        
        paid = Decimal("0")
        submitted_at = None
        edi_ref = None
        
        if status != ClaimStatus.created:
            submitted_at = fake.date_time_between(start_date=dos, end_date='now')
            edi_ref = f"EDI837-{i+1}-{int(submitted_at.timestamp())}"
            
        if status in [ClaimStatus.paid, ClaimStatus.denied, ClaimStatus.appealed]:
            paid = Decimal(str(round(random.uniform(0, float(charge)), 2)))
            
        denial_predicted = status == ClaimStatus.denied or random.random() < 0.15
        denial_prob = Decimal(str(round(random.uniform(0.1, 0.9), 4))) if denial_predicted else None
        
        claim = Claim(
            patient_id=patient.patient_id,
            provider_id=provider.provider_id,
            payer_id=payer.payer_id,
            date_of_service=dos,
            charge_amount=charge,
            paid_amount=paid,
            cpt_codes=cpt_codes,
            icd10_codes=icd10_codes,
            modifiers=modifiers,
            status=status,
            submitted_at=submitted_at,
            edi_837_ref=edi_ref,
            denial_predicted=denial_predicted,
            denial_probability=denial_prob,
            created_at=fake.date_time_between(start_date=dos, end_date=submitted_at or 'now'),
            updated_at=fake.date_time_between(start_date=dos, end_date='now')
        )
        db.add(claim)
        claims.append(claim)
    
    await db.flush()
    return claims


async def seed_denials(db: AsyncSession, claims: list[Claim]):
    denied_claims = [c for c in claims if c.status == ClaimStatus.denied]
    
    for claim in denied_claims:
        num_denials = random.randint(1, 2)
        for _ in range(num_denials):
            denial_data = random.choice(DENIAL_CODES)
            denied_amt = Decimal(str(round(random.uniform(50, float(claim.charge_amount)), 2)))
            
            denial = Denial(
                claim_id=claim.claim_id,
                denial_code=denial_data["code"],
                description=denial_data["description"],
                denied_amount=denied_amt,
                denial_date=fake.date_between(start_date=claim.date_of_service, end_date='today'),
                root_cause=denial_data["root_cause"],
                appeal_status=random.choice(list(AppealStatus)),
                appeal_drafted_by_ai=random.random() < 0.3
            )
            db.add(denial)
    
    await db.flush()


async def seed_payments(db: AsyncSession, claims: list[Claim], payers: list[Payer]):
    paid_claims = [c for c in claims if c.status in [ClaimStatus.paid, ClaimStatus.denied, ClaimStatus.appealed] and c.paid_amount > 0]
    
    for claim in paid_claims:
        num_payments = random.randint(1, 2)
        remaining = float(claim.paid_amount)
        
        for i in range(num_payments):
            if i == num_payments - 1:
                amount = Decimal(str(round(remaining, 2)))
            else:
                amount = Decimal(str(round(random.uniform(10, remaining), 2)))
                remaining -= float(amount)
            
            payment = Payment(
                claim_id=claim.claim_id,
                amount=amount,
                posted_date=fake.date_between(start_date=claim.date_of_service, end_date='today'),
                remittance_ref=f"RMT{random.randint(100000, 999999)}",
                payer_id=claim.payer_id
            )
            db.add(payment)
    
    await db.flush()


async def seed_work_queues(db: AsyncSession) -> list[WorkQueue]:
    queues = []
    for wq in WORK_QUEUES:
        queue = WorkQueue(**wq)
        db.add(queue)
        queues.append(queue)
    await db.flush()
    return queues


async def seed_users(db: AsyncSession) -> list[User]:
    users = []
    for role in UserRole:
        user = User(
            name=f"{role.value.replace('_', ' ').title()} User",
            role=role,
            email=f"{role.value}@novaarc.local",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        users.append(user)
    await db.flush()
    return users


async def main():
    print("Initializing database...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        print("Seeding payers...")
        payers = await seed_payers(db)
        print(f"Created {len(payers)} payers")
        
        print("Seeding providers...")
        providers = await seed_providers(db)
        print(f"Created {len(providers)} providers")
        
        print("Seeding patients...")
        patients = await seed_patients(db, payers)
        print(f"Created {len(patients)} patients")
        
        print("Seeding claims...")
        claims = await seed_claims(db, patients, providers, payers)
        print(f"Created {len(claims)} claims")
        
        print("Seeding denials...")
        await seed_denials(db, claims)
        
        print("Seeding payments...")
        await seed_payments(db, claims, payers)
        
        print("Seeding work queues...")
        queues = await seed_work_queues(db)
        print(f"Created {len(queues)} work queues")
        
        print("Seeding users...")
        users = await seed_users(db)
        print(f"Created {len(users)} users")
        
        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())