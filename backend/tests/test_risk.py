import pytest
from app.database.base import RiskLevel
from app.risk_engine.risk_calculator import RiskCalculator
from app.risk_engine.reason_codes import (
    RC_HIGH_SYNTHETIC_PROBABILITY,
    RC_HIGH_CONFIDENCE_SPOOF,
    RC_NATURAL_VOICE_CHARACTERISTICS,
    RC_DEGRADED_AUDIO_QUALITY,
)


def test_high_risk_calculation():
    assessment = RiskCalculator.calculate_risk(
        synthetic_probability=0.91,
        confidence=0.87,
        audio_quality="HIGH",
    )
    assert assessment.risk_score >= 70
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.suggested_action == "BLOCK"
    assert RC_HIGH_SYNTHETIC_PROBABILITY in assessment.reason_codes
    assert RC_HIGH_CONFIDENCE_SPOOF in assessment.reason_codes


def test_low_risk_calculation():
    assessment = RiskCalculator.calculate_risk(
        synthetic_probability=0.08,
        confidence=0.92,
        audio_quality="HIGH",
    )
    assert assessment.risk_score < 30
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.suggested_action == "ALLOW"
    assert RC_NATURAL_VOICE_CHARACTERISTICS in assessment.reason_codes


def test_medium_risk_calculation():
    assessment = RiskCalculator.calculate_risk(
        synthetic_probability=0.50,
        confidence=0.70,
        audio_quality="HIGH",
    )
    assert 30 <= assessment.risk_score < 70
    assert assessment.risk_level == RiskLevel.MEDIUM
    assert assessment.suggested_action == "ALERT"


def test_degraded_quality_modifier():
    assessment = RiskCalculator.calculate_risk(
        synthetic_probability=0.65,
        confidence=0.60,
        audio_quality="DEGRADED",
    )
    assert RC_DEGRADED_AUDIO_QUALITY in assessment.reason_codes
