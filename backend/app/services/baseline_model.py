import math
from typing import List, Dict, Any, Tuple, Set
from backend.app.ml.model_interface import RecommendationModel
from backend.app.core.logging import logger

class BaselineRecommendationModel(RecommendationModel):
    """
    Baseline recommendation implementation based on weighted term frequency,
    technical unit matching (voltage/current/power), and field-level relevance scoring.
    """
    
    def predict(
        self, 
        query: str, 
        features: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float, str]]:
        if not candidates:
            return []

        keywords: List[str] = features.get("keywords", [])
        units: Dict[str, List[str]] = features.get("units", {})
        voltage_units: List[str] = units.get("voltage", [])

        scored_candidates: List[Tuple[Dict[str, Any], float, str]] = []

        for std in candidates:
            score = 0.0
            reasons: List[str] = []

            title = (std.get("title") or "").lower()
            scope = (std.get("scope_summary") or "").lower()
            specs = (std.get("key_specifications") or "").lower()
            testing = (std.get("testing_requirements") or "").lower()
            is_code = (std.get("is_code") or "").lower()
            department = (std.get("department") or "").lower()

            # 1. Exact IS code query match
            normalized_q = query.lower()
            if is_code in normalized_q or std.get("standard_id", "").lower() in normalized_q:
                score += 0.50
                reasons.append(f"Direct IS code match for {std.get('is_code')}")

            # 2. Keyword relevance across fields (weighted)
            title_hits = 0
            scope_hits = 0
            spec_hits = 0

            for kw in keywords:
                if len(kw) < 2:
                    continue
                if kw in title:
                    title_hits += 1
                if kw in scope:
                    scope_hits += 1
                if kw in specs or kw in testing:
                    spec_hits += 1

            if keywords:
                kw_ratio = (title_hits * 3.0 + spec_hits * 2.0 + scope_hits * 1.0) / (len(keywords) * 3.0)
                kw_score = min(kw_ratio * 0.40, 0.40)
                score += kw_score

            # 3. Voltage / Technical Unit matching
            if voltage_units:
                for v in voltage_units:
                    if v in title or v in scope or v in specs:
                        score += 0.25
                        reasons.append(f"Matches specified operating voltage ({v.upper()})")
                        break
                    elif "1100" in v or "1.1" in v:
                        if "1100" in title or "1100" in scope or "1100" in specs:
                            score += 0.25
                            reasons.append(f"Matches 1.1 kV (1100 V) distribution rating")
                            break

            # 4. Product category match
            products = features.get("products", [])
            for p in products:
                if p in title or p in scope:
                    score += 0.15
                    reasons.append(f"Matches procurement product type '{p}'")
                    break

            # Normalize final score between 0.05 and 0.99
            final_score = round(min(max(score, 0.05), 0.98), 4)

            # Build human readable explanation reason
            if not reasons:
                if title_hits > 0:
                    reason = f"Keyword alignment with {std.get('department', 'Indian')} standard specifications."
                else:
                    reason = f"General technical scope match under {std.get('department', 'BIS')} standard classification."
            else:
                reason = ". ".join(reasons) + "."

            scored_candidates.append((std, final_score, reason))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]
