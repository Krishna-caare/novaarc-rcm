from typing import List
from app.models import Claim, Patient, Provider, Payer
from decimal import Decimal


def generate_837_claim(claim: Claim) -> str:
    patient = claim.patient
    provider = claim.provider
    payer = claim.payer

    segments = []

    segments.append("ISA*00*          *00*          *ZZ*PROVIDER_ID    *ZZ*PAYER_ID       *240115*1200*^*00501*000000001*0*P*:~")
    segments.append("GS*HC*PROVIDER_ID*PAYER_ID*20240115*1200*1*X*005010X222A1~")

    segments.append(f"ST*837*0001*005010X222A1~")
    edi_ref = claim.edi_837_ref or f"CLM{claim.claim_id}"
    segments.append(f"BHT*0019*00*{edi_ref}*20240115*1200*CH~")

    segments.append("NM1*41*2*PROVIDER ORG*****46*PROVIDER_ID~")
    segments.append("PER*IC*CONTACT NAME*TE*5551234567~")

    segments.append("NM1*40*2*PAYER ORG*****46*PAYER_ID~")

    segments.append(f"NM1*IL*1*{patient.mrn}*{patient.member_id or ''}*****MI*{patient.member_id or '12345'}~")
    segments.append("NM1*PR*2*PAYER NAME*****PI*PAYER_ID~")

    segments.append(f"CLM*{claim.claim_id}*{claim.charge_amount:.2f}***11:B:1*Y*A*Y*I~")

    for i, cpt in enumerate(claim.cpt_codes or []):
        segments.append(f"SV1*HC:{cpt}*{claim.charge_amount:.2f}*UN*1***1~")

    for icd in claim.icd10_codes or []:
        segments.append(f"HI*ABK:{icd}~")

    segments.append(f"NM1*82*1*{provider.name.split()[-1] if provider.name else 'PROVIDER'}*{provider.name.split()[0] if provider.name else ''}*****XX*{provider.npi}~")

    segments.append("SE*25*0001~")
    segments.append("GE*1*1~")
    segments.append("IEA*1*000000001~")

    return "\n".join(segments)


def parse_835_remittance(edi_content: str) -> dict:
    payments = []
    lines = edi_content.strip().split("~")

    current_payment = {}
    for line in lines:
        elements = line.split("*")
        if not elements:
            continue

        segment_id = elements[0]

        if segment_id == "CLP":
            if current_payment:
                payments.append(current_payment)
            current_payment = {
                "claim_id": elements[1],
                "status": elements[2],
                "charge_amount": Decimal(elements[3]) if elements[3] else Decimal("0"),
                "paid_amount": Decimal(elements[4]) if elements[4] else Decimal("0"),
                "payer_claim_control": elements[6] if len(elements) > 6 else None,
            }
        elif segment_id == "CAS" and current_payment:
            if "adjustments" not in current_payment:
                current_payment["adjustments"] = []
            current_payment["adjustments"].append({
                "group_code": elements[1],
                "reason_code": elements[2],
                "amount": Decimal(elements[3]) if elements[3] else Decimal("0"),
            })

    if current_payment:
        payments.append(current_payment)

    return {"payments": payments}


def parse_837_claim(edi_content: str) -> dict:
    claim_data = {
        "patient": {},
        "provider": {},
        "payer": {},
        "services": [],
        "diagnoses": []
    }
    lines = edi_content.strip().split("~")

    for line in lines:
        elements = line.split("*")
        if not elements:
            continue

        segment_id = elements[0]

        if segment_id == "NM1":
            entity_id = elements[1]
            if entity_id == "IL":
                claim_data["patient"] = {
                    "member_id": elements[8] if len(elements) > 8 else None,
                    "name": f"{elements[3]} {elements[4]}" if len(elements) > 4 else None,
                }
            elif entity_id == "85":
                claim_data["provider"] = {
                    "npi": elements[8] if len(elements) > 8 else None,
                    "name": f"{elements[3]} {elements[4]}" if len(elements) > 4 else None,
                }
            elif entity_id == "PR":
                claim_data["payer"] = {
                    "name": elements[3] if len(elements) > 3 else None,
                }
        elif segment_id == "CLM":
            claim_data["claim_id"] = elements[1]
            claim_data["charge_amount"] = Decimal(elements[2]) if elements[2] else Decimal("0")
        elif segment_id == "SV1":
            claim_data["services"].append({
                "cpt_code": elements[1].replace("HC:", "") if elements[1].startswith("HC:") else elements[1],
                "charge_amount": Decimal(elements[2]) if elements[2] else Decimal("0"),
            })
        elif segment_id == "HI":
            for elem in elements[1:]:
                if elem.startswith("ABK:") or elem.startswith("BK:"):
                    claim_data["diagnoses"].append(elem.replace("ABK:", "").replace("BK:", ""))

    return claim_data