"""
SPD/ZOD Machine Learning Models
===============================
XGBoost-style models for zoning opportunity analysis.

Models:
- RezoningApprovalPredictor: ~72% accuracy on Brevard County data
- ValueUpliftEstimator: Land value change predictions
- DevelopmentFeasibilityScorer: Comprehensive scoring (0-100)
"""

from .xgboost_models import (
    RezoningApprovalPredictor,
    ValueUpliftEstimator,
    DevelopmentFeasibilityScorer,
    RezoningPrediction,
    ValueUpliftPrediction,
    FeasibilityScore,
    predict_rezoning_approval,
    estimate_value_uplift,
    score_development_feasibility
)

__all__ = [
    "RezoningApprovalPredictor",
    "ValueUpliftEstimator", 
    "DevelopmentFeasibilityScorer",
    "RezoningPrediction",
    "ValueUpliftPrediction",
    "FeasibilityScore",
    "predict_rezoning_approval",
    "estimate_value_uplift",
    "score_development_feasibility"
]
