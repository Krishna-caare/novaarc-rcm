import os
import re
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from app.knowledge_graph.data import DENIAL_KNOWLEDGE_BASE, CATEGORIES

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    _SKLEARN_AVAILABLE = True
except Exception:
    _SKLEARN_AVAILABLE = False


class DenialVectorEngine:
    """
    High-Performance Semantic Vector Engine for Healthcare Denial Resolution.
    Vectorizes all denial scenarios, root causes, investigation checklists,
    and CMS-1500 form requirements into a searchable mathematical vector space.
    """

    def __init__(self):
        self.scenarios_metadata: List[Dict[str, Any]] = []
        self.corpus_texts: List[str] = []
        self.vectors: Optional[np.ndarray] = None
        self.encoder_type = "none"
        self._tfidf_vectorizer = None

        self._build_corpus()
        self._initialize_vectorizer()

    def _build_corpus(self):
        """Extracts and builds rich semantic document chunks for every scenario"""
        self.scenarios_metadata = []
        self.corpus_texts = []

        category_map = {c["id"]: c["name"] for c in CATEGORIES}

        for code, data in DENIAL_KNOWLEDGE_BASE.items():
            cat_name = category_map.get(data.get("category_id"), "")
            short_name = data.get("short_name", "")
            code_desc = data.get("description", "")

            for sc in data.get("scenarios", []):
                sc_id = sc.get("id", "")
                title = sc.get("title", "")
                root_cause = sc.get("root_cause", "")
                steps = " ".join(sc.get("investigation_steps", []))
                form_req = sc.get("form_requirements", {})
                form_info = f"{form_req.get('form_name', '')} {form_req.get('box_number', '')} {', '.join(form_req.get('required_documents', []))}"
                action_plan = " ".join(sc.get("action_plan", []))

                # Comprehensive semantic document chunk with high-signal keywords & context
                doc_text = (
                    f"CARC Code: {code} - {short_name}. Category: {cat_name}. "
                    f"Code Description: {code_desc}. Scenario: {title}. "
                    f"Root Cause Analysis: {root_cause}. Investigation: {steps}. "
                    f"Form & Field Requirements: {form_info}. Resolution Action: {action_plan}."
                )

                self.corpus_texts.append(doc_text)
                self.scenarios_metadata.append({
                    "scenario_id": sc_id,
                    "code": code,
                    "category_id": data.get("category_id"),
                    "category_name": cat_name,
                    "title": title,
                    "root_cause": root_cause,
                    "scenario": sc,
                    "doc_text": doc_text,
                })

    def _initialize_vectorizer(self):
        """Initializes Scikit-Learn TF-IDF N-gram Semantic Vectorizer (Instant, 0ms, 100% offline)"""
        if _SKLEARN_AVAILABLE:
            try:
                self._tfidf_vectorizer = TfidfVectorizer(
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    stop_words="english",
                    max_features=4000
                )
                tfidf_matrix = self._tfidf_vectorizer.fit_transform(self.corpus_texts)
                raw_vectors = tfidf_matrix.toarray().astype(np.float32)
                # L2 normalize for cosine similarity via dot product
                norms = np.linalg.norm(raw_vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self.vectors = raw_vectors / norms
                self.encoder_type = "tfidf:ngram_semantic"
                return
            except Exception:
                pass

        self.encoder_type = "keyword_fallback"

    def embed_query(self, query_text: str) -> Optional[np.ndarray]:
        """Encodes query string into normalized vector space"""
        clean_text = query_text.strip()
        if not clean_text or not self._tfidf_vectorizer:
            return None

        try:
            vec = self._tfidf_vectorizer.transform([clean_text]).toarray().astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception:
            return None

    def search(
        self,
        query_text: str,
        carc_filter: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic cosine similarity search across all denial scenarios.
        Supports CARC code biasing/filtering and returns sorted candidates with similarity scores.
        """
        if not self.corpus_texts:
            return []

        q_vec = self.embed_query(query_text)
        results = []

        if q_vec is not None and self.vectors is not None:
            # Vector dot product gives exact cosine similarity since both are L2 normalized
            similarities = np.dot(self.vectors, q_vec.T).flatten()

            for idx, score in enumerate(similarities):
                meta = self.scenarios_metadata[idx]
                sim = float(score)

                # Affinity boost for matching CARC code if provided
                if carc_filter:
                    clean_code = carc_filter.upper().strip()
                    if meta["code"] == clean_code:
                        sim += 0.25 # Significant affinity boost for expected CARC category
                    else:
                        sim *= 0.50 # Penalty for mismatched code category

                if sim >= min_similarity:
                    results.append({
                        "scenario_id": meta["scenario_id"],
                        "code": meta["code"],
                        "category_id": meta["category_id"],
                        "category_name": meta["category_name"],
                        "title": meta["title"],
                        "root_cause": meta["root_cause"],
                        "similarity": round(min(1.0, max(0.0, sim)), 4),
                        "scenario": meta["scenario"],
                        "encoder_type": self.encoder_type,
                    })

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

        # Robust keyword matching fallback
        q_lower = query_text.lower()
        for meta in self.scenarios_metadata:
            text_lower = meta["doc_text"].lower()
            overlap = sum(1 for word in q_lower.split() if len(word) > 3 and word in text_lower)
            if overlap > 0:
                results.append({
                    "scenario_id": meta["scenario_id"],
                    "code": meta["code"],
                    "category_id": meta["category_id"],
                    "category_name": meta["category_name"],
                    "title": meta["title"],
                    "root_cause": meta["root_cause"],
                    "similarity": round(min(1.0, overlap * 0.15), 4),
                    "scenario": meta["scenario"],
                    "encoder_type": "keyword_fallback",
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]


# Global singleton vector engine
denial_vector_engine = DenialVectorEngine()
