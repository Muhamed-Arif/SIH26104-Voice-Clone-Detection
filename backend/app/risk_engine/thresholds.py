"""Risk thresholds for classification."""
from app.core.config import settings

# Threshold score cutoffs (0-100 scale)
DEFAULT_RISK_LOW_MAX = settings.RISK_THRESHOLD_LOW      # < 30 => LOW
DEFAULT_RISK_HIGH_MIN = settings.RISK_THRESHOLD_HIGH    # >= 70 => HIGH
                                                         # 30..69 => MEDIUM

# Model Confidence Weights
DEFAULT_CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD

# Synthetic Probability Cutoffs (0.0 to 1.0)
PROBABILITY_HIGH = 0.75
PROBABILITY_MEDIUM = 0.40
