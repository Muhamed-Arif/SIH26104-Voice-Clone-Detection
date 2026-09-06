from typing import List, Tuple
from app.database.base import RiskLevel
from app.schemas.risk import RiskAssessment
from app.risk_engine.thresholds import (
    DEFAULT_RISK_LOW_MAX,
    DEFAULT_RISK_HIGH_MIN,
    DEFAULT_CONFIDENCE_THRESHOLD,
    PROBABILITY_HIGH,
    PROBABILITY_MEDIUM,
)
from app.risk_engine.reason_codes import (
    RC_HIGH_SYNTHETIC_PROBABILITY,
    RC_HIGH_CONFIDENCE_SPOOF,
    RC_MODERATE_SYNTHETIC_INDICATORS,
    RC_LOW_CONFIDENCE_INFERENCE,
    RC_DEGRADED_AUDIO_QUALITY,
    RC_NATURAL_VOICE_CHARACTERISTICS,
    RC_CONFIRMED_ANOMALY,
)


class RiskCalculator:
    """Computes risk score, risk level, action, and human-readable reason codes."""

    @classmethod
    def calculate_risk(
        cls,
        synthetic_probability: float,
        confidence: float,
        audio_quality: str = "HIGH",
    ) -> RiskAssessment:
        # Clamp inputs
        synth_prob = max(0.0, min(1.0, float(synthetic_probability)))
        conf = max(0.0, min(1.0, float(confidence)))

        reason_codes: List[str] = []

        # Base score from probability (0..100)
        # Weighted by confidence: if confidence is high, score amplifies towards certainty
        base_score = synth_prob * 100.0

        if conf >= DEFAULT_CONFIDENCE_THRESHOLD:
            # High confidence boosts extreme predictions
            if synth_prob >= PROBABILITY_HIGH:
                adjusted_score = base_score * (0.8 + 0.2 * conf)
                reason_codes.append(RC_HIGH_SYNTHETIC_PROBABILITY)
                reason_codes.append(RC_HIGH_CONFIDENCE_SPOOF)
            elif synth_prob >= PROBABILITY_MEDIUM:
                adjusted_score = base_score
                reason_codes.append(RC_MODERATE_SYNTHETIC_INDICATORS)
            else:
                adjusted_score = base_score * (1.0 - 0.1 * conf)
                reason_codes.append(RC_NATURAL_VOICE_CHARACTERISTICS)
        else:
            # Low confidence dampens toward uncertainty center
            adjusted_score = (base_score * 0.7) + (50.0 * 0.3)
            reason_codes.append(RC_LOW_CONFIDENCE_INFERENCE)

        # Audio quality modifier
        quality_upper = audio_quality.upper() if audio_quality else "HIGH"
        if quality_upper in ("DEGRADED", "LOW", "POOR"):
            reason_codes.append(RC_DEGRADED_AUDIO_QUALITY)
            # Add uncertainty modifier
            if adjusted_score > 50:
                adjusted_score = min(100.0, adjusted_score + 5.0)

        # Final rounded integer score in 0..100
        final_score = int(round(max(0.0, min(100.0, adjusted_score))))

        # Classify Level and Action
        if final_score >= DEFAULT_RISK_HIGH_MIN:
            risk_level = RiskLevel.HIGH
            suggested_action = "BLOCK"
            if RC_CONFIRMED_ANOMALY not in reason_codes:
                reason_codes.append(RC_CONFIRMED_ANOMALY)
        elif final_score >= DEFAULT_RISK_LOW_MAX:
            risk_level = RiskLevel.MEDIUM
            suggested_action = "ALERT"
        else:
            risk_level = RiskLevel.LOW
            suggested_action = "ALLOW"
            if not reason_codes:
                reason_codes.append(RC_NATURAL_VOICE_CHARACTERISTICS)

        return RiskAssessment(
            risk_score=final_score,
            risk_level=risk_level,
            reason_codes=reason_codes,
            suggested_action=suggested_action,
        )
