"""Human-readable reason codes for risk determinations."""

RC_HIGH_SYNTHETIC_PROBABILITY = "HIGH_SYNTHETIC_PROBABILITY"
RC_HIGH_CONFIDENCE_SPOOF = "HIGH_CONFIDENCE_SPOOF"
RC_MODERATE_SYNTHETIC_INDICATORS = "MODERATE_SYNTHETIC_INDICATORS"
RC_LOW_CONFIDENCE_INFERENCE = "LOW_CONFIDENCE_INFERENCE"
RC_DEGRADED_AUDIO_QUALITY = "DEGRADED_AUDIO_QUALITY"
RC_NATURAL_VOICE_CHARACTERISTICS = "NATURAL_VOICE_CHARACTERISTICS"
RC_CONFIRMED_ANOMALY = "CONFIRMED_ANOMALY"

REASON_DESCRIPTIONS = {
    RC_HIGH_SYNTHETIC_PROBABILITY: "ML Model detected strong acoustic artifacts characteristic of neural vocoders or TTS synthesis.",
    RC_HIGH_CONFIDENCE_SPOOF: "Inference confidence exceeds statistical certainty threshold with high synthetic likelihood.",
    RC_MODERATE_SYNTHETIC_INDICATORS: "Acoustic signature exhibits ambiguous spectral anomalies requiring elevated monitoring.",
    RC_LOW_CONFIDENCE_INFERENCE: "Model confidence is below benchmark; score adjusted conservatively.",
    RC_DEGRADED_AUDIO_QUALITY: "Background noise or low sampling fidelity may introduce classification variance.",
    RC_NATURAL_VOICE_CHARACTERISTICS: "Harmonic structure and phase continuity strongly match genuine human vocalization.",
    RC_CONFIRMED_ANOMALY: "Multi-factor evaluation triggered an automated HIGH-risk security flag.",
}


def get_reason_description(code: str) -> str:
    return REASON_DESCRIPTIONS.get(code, "Acoustic analysis event recorded.")
