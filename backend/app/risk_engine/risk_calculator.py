from typing import List
from app.database.base import RiskLevel
from app.risk_engine.models.risk_result import RiskFactor, RiskResult
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
from app.risk_engine.models.spectral_analyzer import SpectralAnalyzer
from app.risk_engine.models.prosody_checker import ProsodyChecker



class RiskCalculator:
    """Computes risk score, risk level, action, and human-readable reason codes."""

    @classmethod
    def calculate_risk(
        cls,
        synthetic_probability: float,
        confidence: float,
        audio_quality: str = "HIGH",
    ) -> RiskResult:
        # Clamp inputs
        synth_prob = max(0.0, min(1.0, float(synthetic_probability)))
        conf = max(0.0, min(1.0, float(confidence)))

        reason_codes: List[str] = []
        risk_factors: List[RiskFactor] = []

        # Run ensemble models
        spectral_res = SpectralAnalyzer.analyze(synth_prob)
        prosody_res = ProsodyChecker.check(synth_prob)

        # Base score from probability (0..100) using ensemble weighting
        ensemble_prob = (synth_prob * 0.5) + (spectral_res["score"] * 0.25) + (prosody_res["score"] * 0.25)
        ensemble_conf = (conf * 0.5) + (spectral_res["confidence"] * 0.25) + (prosody_res["confidence"] * 0.25)
        
        base_score = ensemble_prob * 100.0

        if ensemble_conf >= DEFAULT_CONFIDENCE_THRESHOLD:
            # High confidence boosts extreme predictions
            if synth_prob >= PROBABILITY_HIGH:
                adjusted_score = base_score * (0.8 + 0.2 * conf)
                reason_codes.append(RC_HIGH_SYNTHETIC_PROBABILITY)
                reason_codes.append(RC_HIGH_CONFIDENCE_SPOOF)
                risk_factors.append(RiskFactor(
                    code=RC_HIGH_SYNTHETIC_PROBABILITY,
                    description="The model found a high probability of synthetic speech.",
                    contribution=round(synth_prob, 4),
                ))
            elif synth_prob >= PROBABILITY_MEDIUM:
                adjusted_score = base_score
                reason_codes.append(RC_MODERATE_SYNTHETIC_INDICATORS)
                risk_factors.append(RiskFactor(
                    code=RC_MODERATE_SYNTHETIC_INDICATORS,
                    description="Synthetic speech indicators are present at a moderate level.",
                    contribution=round(synth_prob, 4),
                ))
            else:
                adjusted_score = base_score * (1.0 - 0.1 * conf)
                reason_codes.append(RC_NATURAL_VOICE_CHARACTERISTICS)
        else:
            # Low confidence dampens toward uncertainty center
            adjusted_score = (base_score * 0.7) + (50.0 * 0.3)
            reason_codes.append(RC_LOW_CONFIDENCE_INFERENCE)
            risk_factors.append(RiskFactor(
                code=RC_LOW_CONFIDENCE_INFERENCE,
                description="The model confidence is below the reliable inference threshold.",
                contribution=round(1.0 - ensemble_conf, 4),
            ))

        # Audio quality modifier
        quality_upper = audio_quality.upper() if audio_quality else "HIGH"
        if quality_upper in ("DEGRADED", "LOW", "POOR"):
            reason_codes.append(RC_DEGRADED_AUDIO_QUALITY)
            risk_factors.append(RiskFactor(
                code=RC_DEGRADED_AUDIO_QUALITY,
                description="Audio quality increases uncertainty in the classification.",
                contribution=0.05,
            ))
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

        return RiskResult(
            risk_score=final_score,
            risk_level=risk_level,
            confidence=round(ensemble_conf, 4),
            risk_factors=risk_factors,
            reason_codes=reason_codes,
            suggested_action=suggested_action,
        )
