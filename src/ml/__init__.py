"""
SPD/ZOD Machine Learning Module
===============================
XGBoost models for real estate development predictions.

Models:
- ZOD XGBoost: Rezoning approval probability & value uplift
- SPD Feasibility: Site development feasibility scoring

Integrates with:
- BidDeed.AI ML ecosystem (src/ml/xgboost_model.py)
- LangGraph orchestration pipeline
- Census API demographics
- Zillow/Redfin valuations
"""

from .zod_xgboost_model import (
    ZODXGBoostModel,
    ZODPrediction,
    TrainingMetrics,
    train_zod_model,
    integrate_ml_scoring,
    REZONING_HISTORY,
    VALUE_UPLIFT_PER_UNIT,
    CONSTRAINT_IMPACT
)

__all__ = [
    "ZODXGBoostModel",
    "ZODPrediction",
    "TrainingMetrics",
    "train_zod_model",
    "integrate_ml_scoring",
    "REZONING_HISTORY",
    "VALUE_UPLIFT_PER_UNIT",
    "CONSTRAINT_IMPACT"
]
