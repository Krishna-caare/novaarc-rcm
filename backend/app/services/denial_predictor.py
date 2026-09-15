import json
import pickle
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal

from app.models import Claim, Denial, ClaimStatus
from app.core.config import settings


MODEL_PATH = Path("models/denial_predictor.pkl")
FEATURE_NAMES = [
    "payer_id", "provider_specialty_encoded", "charge_amount", "num_cpt_codes",
    "num_icd10_codes", "has_prior_denial", "days_since_service", "avg_denial_rate_payer",
    "avg_denial_rate_provider", "claim_status_encoded"
]


class DenialPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = FEATURE_NAMES

    def load_model(self):
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.scaler = data["scaler"]
        else:
            self._train_dummy_model()

    def _train_dummy_model(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler

        np.random.seed(42)
        n_samples = 1000
        X = np.random.randn(n_samples, len(self.feature_names))
        y = (X[:, 0] + X[:, 2] * 0.5 + np.random.randn(n_samples) * 0.3 > 0).astype(int)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

    def extract_features(self, claim: Claim, payer_denial_rate: float, provider_denial_rate: float, has_prior_denial: bool) -> np.ndarray:
        specialty_map = {"Cardiology": 1, "Orthopedics": 2, "Primary Care": 3, "Radiology": 4, "Other": 0}
        status_map = {s.value: i for i, s in enumerate(ClaimStatus)}

        features = [
            claim.payer_id or 0,
            specialty_map.get(claim.provider.specialty if claim.provider else None, 0),
            float(claim.charge_amount),
            len(claim.cpt_codes or []),
            len(claim.icd10_codes or []),
            1 if has_prior_denial else 0,
            (pd.Timestamp.now() - pd.Timestamp(claim.date_of_service)).days if claim.date_of_service else 0,
            payer_denial_rate,
            provider_denial_rate,
            status_map.get(claim.status.value, 0)
        ]
        return np.array(features).reshape(1, -1)

    def predict(self, features: np.ndarray) -> tuple[float, dict]:
        if self.model is None:
            self.load_model()

        features_scaled = self.scaler.transform(features)
        prob = self.model.predict_proba(features_scaled)[0, 1]

        shap_values = {}
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            for i, name in enumerate(self.feature_names):
                shap_values[name] = float(importances[i] * features[0, i])

        return float(prob), shap_values


denial_predictor = DenialPredictor()


async def get_denial_prediction(db: AsyncSession, claim_id: int) -> tuple[Decimal, dict, list[str]]:
    result = await db.execute(select(Claim).where(Claim.claim_id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise ValueError(f"Claim {claim_id} not found")

    payer_denial_result = await db.execute(
        select(
            func.count(Denial.denial_id).label("denials"),
            func.count(Claim.claim_id).label("claims")
        )
        .join(Claim, Denial.claim_id == Claim.claim_id)
        .where(Claim.payer_id == claim.payer_id)
    )
    payer_stats = payer_denial_result.first()
    payer_denial_rate = (payer_stats.denials / payer_stats.claims) if payer_stats and payer_stats.claims > 0 else 0.1

    provider_denial_result = await db.execute(
        select(
            func.count(Denial.denial_id).label("denials"),
            func.count(Claim.claim_id).label("claims")
        )
        .join(Claim, Denial.claim_id == Claim.claim_id)
        .where(Claim.provider_id == claim.provider_id)
    )
    provider_stats = provider_denial_result.first()
    provider_denial_rate = (provider_stats.denials / provider_stats.claims) if provider_stats and provider_stats.claims > 0 else 0.1

    prior_denial_result = await db.execute(
        select(Denial).where(Denial.claim_id == claim_id)
    )
    has_prior_denial = prior_denial_result.scalar_one_or_none() is not None

    features = denial_predictor.extract_features(
        claim, payer_denial_rate, provider_denial_rate, has_prior_denial
    )

    probability, shap_explanation = denial_predictor.predict(features)

    risk_factors = []
    if has_prior_denial:
        risk_factors.append("Prior denial on this claim")
    if payer_denial_rate > 0.2:
        risk_factors.append(f"High payer denial rate ({payer_denial_rate:.1%})")
    if provider_denial_rate > 0.2:
        risk_factors.append(f"High provider denial rate ({provider_denial_rate:.1%})")
    if float(claim.charge_amount) > 10000:
        risk_factors.append("High charge amount (>$10,000)")
    if len(claim.cpt_codes or []) > 5:
        risk_factors.append("Many CPT codes (>5)")
    if len(claim.icd10_codes or []) > 5:
        risk_factors.append("Many ICD-10 codes (>5)")

    hitl_required = probability > 0.7

    return Decimal(str(probability)), shap_explanation, risk_factors, hitl_required