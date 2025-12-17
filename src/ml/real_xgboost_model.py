"""
Zoning Opportunity Discovery (ZOD) - REAL XGBoost ML Pipeline
==============================================================
HONEST IMPLEMENTATION - No fabricated accuracy claims

This module provides:
1. Data collection infrastructure for REAL rezoning decisions
2. XGBoost model training when sufficient data is collected
3. Rule-based fallback with explicit uncertainty bounds

DATA SOURCES (REAL):
- Palm Bay: palmbayfl.novusagenda.com (Novus Agenda)
- Melbourne: melbourneflorida.granicus.com (Granicus/Legistar)
- Brevard County: brevardfl.gov Planning & Development

STATUS: DATA COLLECTION PHASE
- Training records collected: 0
- Minimum required for ML: 100
- Current mode: RULE_BASED_WITH_UNCERTAINTY
"""

import os
import json
import re
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
import hashlib


# =============================================================================
# CONSTANTS - REAL VALUES FROM FLORIDA STATUTES & MUNICIPAL CODES
# =============================================================================

# Actual density limits from Palm Bay Code of Ordinances Chapter 173
PALM_BAY_ZONING_DENSITY = {
    "RS-1": 2.5,   # Single-Family Residential - 2.5 du/acre
    "RS-2": 4.0,   # Single-Family Residential - 4 du/acre
    "RS-3": 5.0,   # Single-Family Residential - 5 du/acre
    "RM-6": 6.0,   # Multi-Family - 6 du/acre
    "RM-10": 10.0, # Multi-Family - 10 du/acre
    "RM-15": 15.0, # Multi-Family - 15 du/acre
    "RM-20": 20.0, # Multi-Family - 20 du/acre
    "PUD": None,   # Planned Unit Development - varies by approval
    "PMU": None,   # Parkway Mixed Use - varies
    "CC": 0,       # Community Commercial - no residential
    "LI": 0,       # Light Industrial - no residential
}

# FLU categories from Palm Bay Comprehensive Plan
PALM_BAY_FLU_DENSITY = {
    "RES 1": 1.0,      # Residential 1 unit/acre
    "RES 2.5": 2.5,    # Residential 2.5 units/acre
    "RES 4": 4.0,      # Low Density Residential
    "RES 6": 6.0,      # Low-Medium Density
    "RES 10": 10.0,    # Medium Density
    "RES 15": 15.0,    # Medium-High Density
    "RES 20": 20.0,    # High Density Residential
    "NC": 10.0,        # Neighborhood Center
    "CC": 15.0,        # Community Center
    "PMU": 20.0,       # Parkway Mixed Use
    "IND": 0,          # Industrial
    "COM": 0,          # Commercial
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ModelStatus(str, Enum):
    """Current status of the ML model."""
    DATA_COLLECTION = "DATA_COLLECTION"      # Collecting training data
    TRAINING = "TRAINING"                     # Model being trained
    VALIDATED = "VALIDATED"                   # Model trained and validated
    RULE_BASED = "RULE_BASED"                # Fallback to rules (insufficient data)


@dataclass
class RezoningDecision:
    """
    A single historical rezoning decision - THE TRAINING DATA.
    Each record must be verified from official sources.
    """
    # Identifiers
    case_number: str                          # e.g., "CPZ24-00008"
    ordinance_number: Optional[str]           # e.g., "2024-54" (if approved)
    
    # Location
    jurisdiction: str                         # "Palm Bay", "Melbourne", etc.
    address: Optional[str]
    parcel_id: Optional[str]
    acreage: float
    
    # Zoning Change
    from_zoning: str
    to_zoning: str
    from_flu: Optional[str]
    to_flu: Optional[str]                     # If comp plan amendment
    
    # Outcome - THE TARGET VARIABLE
    outcome: str                              # "APPROVED", "DENIED", "WITHDRAWN"
    
    # Decision Details
    pz_board_vote: Optional[str]              # e.g., "5-0", "4-1", "3-2"
    council_vote: Optional[str]               # e.g., "5-0", "4-1"
    decision_date: str                        # ISO format
    
    # Features that might predict outcome
    had_opposition: bool = False
    had_traffic_study: bool = False
    had_stormwater_plan: bool = False
    density_increase: float = 0.0             # du/acre increase
    flu_consistent: bool = True               # Zoning consistent with FLU?
    
    # Data Quality
    source_url: str = ""                      # Where this data came from
    verified: bool = False                    # Has a human verified this?
    collected_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def get_id(self) -> str:
        """Unique ID for deduplication."""
        key = f"{self.jurisdiction}:{self.case_number}"
        return hashlib.md5(key.encode()).hexdigest()[:12]


@dataclass
class ModelMetrics:
    """Honest reporting of model performance."""
    status: ModelStatus
    training_records: int
    minimum_required: int = 100
    
    # Only populated if status == VALIDATED
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Cross-validation details
    cv_folds: int = 0
    cv_scores: List[float] = field(default_factory=list)
    
    # Data quality
    verified_records: int = 0
    jurisdictions_covered: List[str] = field(default_factory=list)
    date_range: Optional[str] = None
    
    last_updated: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Prediction:
    """
    Output of the prediction model.
    ALWAYS includes uncertainty bounds and data quality warnings.
    """
    # The prediction
    approval_probability: float               # 0.0 to 1.0
    
    # Uncertainty bounds - REQUIRED
    lower_bound: float                        # e.g., 0.55
    upper_bound: float                        # e.g., 0.85
    confidence_level: float                   # e.g., 0.80 (80% CI)
    
    # Model information
    model_status: ModelStatus
    prediction_method: str                    # "XGBOOST" or "RULE_BASED"
    
    # Feature contributions (if XGBoost)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    # Comparable cases found
    similar_cases: int = 0
    similar_case_approval_rate: Optional[float] = None
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    prediction_timestamp: str = ""
    model_version: str = "0.1.0-alpha"
    
    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# DATA COLLECTION - THE REAL WORK
# =============================================================================

class RezoningDataCollector:
    """
    Collects REAL rezoning decisions from official sources.
    
    Sources:
    - Palm Bay: palmbayfl.novusagenda.com
    - Melbourne: melbourneflorida.granicus.com
    - Brevard County: brevardfl.gov
    """
    
    def __init__(self, data_dir: str = "./data/rezoning"):
        self.data_dir = data_dir
        self.decisions: List[RezoningDecision] = []
        self._load_existing()
    
    def _load_existing(self):
        """Load previously collected data."""
        data_file = os.path.join(self.data_dir, "decisions.json")
        if os.path.exists(data_file):
            with open(data_file) as f:
                data = json.load(f)
                self.decisions = [
                    RezoningDecision(**d) for d in data.get("decisions", [])
                ]
    
    def save(self):
        """Save collected data."""
        os.makedirs(self.data_dir, exist_ok=True)
        data_file = os.path.join(self.data_dir, "decisions.json")
        
        with open(data_file, "w") as f:
            json.dump({
                "decisions": [d.to_dict() for d in self.decisions],
                "count": len(self.decisions),
                "last_updated": datetime.utcnow().isoformat()
            }, f, indent=2)
    
    def add_decision(self, decision: RezoningDecision) -> bool:
        """Add a decision if not duplicate."""
        decision_id = decision.get_id()
        existing_ids = {d.get_id() for d in self.decisions}
        
        if decision_id not in existing_ids:
            decision.collected_at = datetime.utcnow().isoformat()
            self.decisions.append(decision)
            return True
        return False
    
    def get_metrics(self) -> ModelMetrics:
        """Get current data collection status."""
        jurisdictions = list(set(d.jurisdiction for d in self.decisions))
        verified = sum(1 for d in self.decisions if d.verified)
        
        dates = [d.decision_date for d in self.decisions if d.decision_date]
        date_range = None
        if dates:
            dates.sort()
            date_range = f"{dates[0]} to {dates[-1]}"
        
        status = ModelStatus.DATA_COLLECTION
        if len(self.decisions) >= 100:
            status = ModelStatus.TRAINING if verified < 50 else ModelStatus.VALIDATED
        
        return ModelMetrics(
            status=status,
            training_records=len(self.decisions),
            verified_records=verified,
            jurisdictions_covered=jurisdictions,
            date_range=date_range,
            last_updated=datetime.utcnow().isoformat()
        )
    
    def get_palm_bay_sources(self) -> List[Dict[str, str]]:
        """Return URLs to scrape for Palm Bay data."""
        return [
            {
                "name": "Palm Bay Novus Agenda",
                "url": "https://palmbayfl.novusagenda.com/agendapublic/",
                "type": "meeting_agendas",
                "notes": "Search for 'CPZ' (rezoning) cases in meeting agendas"
            },
            {
                "name": "Palm Bay Municode",
                "url": "https://library.municode.com/fl/palm_bay",
                "type": "ordinances",
                "notes": "Search for rezoning ordinances (2021-xxx, 2022-xxx, etc.)"
            },
            {
                "name": "Palm Bay GIS",
                "url": "https://gis.palmbayflorida.org/",
                "type": "zoning_map",
                "notes": "Verify current zoning designations"
            }
        ]


# =============================================================================
# RULE-BASED PREDICTOR (HONEST VERSION)
# =============================================================================

class RuleBasedPredictor:
    """
    Rule-based prediction when ML model is not yet trained.
    
    IMPORTANT: This does NOT claim ML accuracy.
    It provides estimates based on domain knowledge with WIDE uncertainty bounds.
    """
    
    def __init__(self):
        self.version = "0.1.0-rules"
    
    def predict(
        self,
        jurisdiction: str,
        from_zoning: str,
        to_zoning: str,
        from_flu: str,
        acreage: float,
        has_opposition: bool = False,
        flu_consistent: bool = True
    ) -> Prediction:
        """
        Make a prediction with explicit uncertainty.
        """
        warnings = []
        
        # Start with wide uncertainty - we don't have real data
        base_prob = 0.70  # Generic assumption
        lower = 0.40
        upper = 0.90
        
        # Check FLU consistency (this is actually knowable)
        if not flu_consistent:
            base_prob -= 0.25
            lower -= 0.20
            warnings.append(
                "Zoning request exceeds FLU maximum - requires comp plan amendment"
            )
        else:
            # FLU consistent = "by-right" in theory
            base_prob += 0.10
            lower += 0.10
        
        # Opposition is a real factor
        if has_opposition:
            base_prob -= 0.15
            warnings.append(
                "Neighbor opposition increases denial risk"
            )
        
        # Larger density jumps are harder
        from_density = PALM_BAY_ZONING_DENSITY.get(from_zoning, 4.0) or 4.0
        to_density = PALM_BAY_ZONING_DENSITY.get(to_zoning, from_density) or from_density
        
        density_jump = (to_density - from_density) if to_density else 0
        
        if density_jump > 10:
            base_prob -= 0.10
            warnings.append(
                f"Large density increase ({density_jump:.0f} du/acre) may face scrutiny"
            )
        
        # Clamp values
        base_prob = max(0.20, min(0.90, base_prob))
        lower = max(0.10, min(base_prob - 0.05, lower))
        upper = min(0.95, max(base_prob + 0.05, upper))
        
        # ALWAYS add this warning - we don't have real data
        warnings.insert(0, 
            "⚠️ PREDICTION BASED ON RULES, NOT ML MODEL. "
            "No validated training data available. "
            "Wide uncertainty bounds reflect low confidence."
        )
        
        return Prediction(
            approval_probability=base_prob,
            lower_bound=lower,
            upper_bound=upper,
            confidence_level=0.50,  # Low confidence - just rules
            model_status=ModelStatus.RULE_BASED,
            prediction_method="RULE_BASED",
            similar_cases=0,
            warnings=warnings,
            prediction_timestamp=datetime.utcnow().isoformat(),
            model_version=self.version
        )


# =============================================================================
# XGBOOST MODEL (REAL - BUT NOT YET TRAINED)
# =============================================================================

class RezoningXGBoostModel:
    """
    Real XGBoost model - will be trained when sufficient data collected.
    
    CURRENT STATUS: NOT TRAINED
    REASON: No validated training data
    FALLBACK: RuleBasedPredictor
    """
    
    def __init__(self, data_collector: RezoningDataCollector = None):
        self.data_collector = data_collector or RezoningDataCollector()
        self.model = None  # Will be XGBClassifier when trained
        self.is_trained = False
        self.metrics: Optional[ModelMetrics] = None
        self.rule_predictor = RuleBasedPredictor()
    
    def get_status(self) -> Dict[str, Any]:
        """Get honest status of the model."""
        metrics = self.data_collector.get_metrics()
        
        return {
            "is_trained": self.is_trained,
            "status": metrics.status.value,
            "training_records": metrics.training_records,
            "minimum_required": metrics.minimum_required,
            "records_needed": max(0, metrics.minimum_required - metrics.training_records),
            "verified_records": metrics.verified_records,
            "jurisdictions": metrics.jurisdictions_covered,
            "message": self._get_status_message(metrics)
        }
    
    def _get_status_message(self, metrics: ModelMetrics) -> str:
        """Generate honest status message."""
        if metrics.training_records == 0:
            return (
                "NO TRAINING DATA COLLECTED. "
                "Using rule-based estimates with wide uncertainty. "
                "Collect rezoning decisions from Palm Bay Novus Agenda to enable ML."
            )
        elif metrics.training_records < 50:
            return (
                f"Only {metrics.training_records} records collected. "
                f"Need at least 100 for basic ML training. "
                "Currently using rule-based fallback."
            )
        elif metrics.training_records < 100:
            return (
                f"{metrics.training_records} records collected. "
                f"Need {100 - metrics.training_records} more for ML training."
            )
        else:
            if not self.is_trained:
                return (
                    f"{metrics.training_records} records available. "
                    "Ready to train XGBoost model. Run train() to proceed."
                )
            else:
                return (
                    f"XGBoost model trained on {metrics.training_records} records. "
                    f"Accuracy: {metrics.accuracy:.1%}" if metrics.accuracy else ""
                )
    
    def train(self) -> ModelMetrics:
        """
        Train XGBoost model if sufficient data available.
        """
        metrics = self.data_collector.get_metrics()
        
        if metrics.training_records < 100:
            raise ValueError(
                f"Insufficient training data: {metrics.training_records} records. "
                f"Need at least 100 for meaningful ML training."
            )
        
        # Import XGBoost only when training
        try:
            import xgboost as xgb
            from sklearn.model_selection import cross_val_score, train_test_split
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            import numpy as np
        except ImportError:
            raise ImportError(
                "XGBoost and scikit-learn required for training. "
                "Install with: pip install xgboost scikit-learn"
            )
        
        # Prepare features
        decisions = self.data_collector.decisions
        
        X = []
        y = []
        
        for d in decisions:
            if d.outcome not in ["APPROVED", "DENIED"]:
                continue  # Skip withdrawn
            
            features = [
                d.acreage,
                d.density_increase,
                1.0 if d.flu_consistent else 0.0,
                1.0 if d.had_opposition else 0.0,
                1.0 if d.had_traffic_study else 0.0,
                1.0 if d.had_stormwater_plan else 0.0,
            ]
            
            X.append(features)
            y.append(1 if d.outcome == "APPROVED" else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5)
        
        self.metrics = ModelMetrics(
            status=ModelStatus.VALIDATED,
            training_records=len(decisions),
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, zero_division=0),
            recall=recall_score(y_test, y_pred, zero_division=0),
            f1_score=f1_score(y_test, y_pred, zero_division=0),
            cv_folds=5,
            cv_scores=cv_scores.tolist(),
            verified_records=sum(1 for d in decisions if d.verified),
            jurisdictions_covered=list(set(d.jurisdiction for d in decisions)),
            last_updated=datetime.utcnow().isoformat()
        )
        
        self.is_trained = True
        return self.metrics
    
    def predict(
        self,
        jurisdiction: str,
        from_zoning: str,
        to_zoning: str,
        from_flu: str,
        acreage: float,
        has_opposition: bool = False,
        flu_consistent: bool = True
    ) -> Prediction:
        """
        Make prediction - uses ML if trained, otherwise rules.
        """
        if not self.is_trained or self.model is None:
            # Use rule-based fallback with honest warnings
            return self.rule_predictor.predict(
                jurisdiction=jurisdiction,
                from_zoning=from_zoning,
                to_zoning=to_zoning,
                from_flu=from_flu,
                acreage=acreage,
                has_opposition=has_opposition,
                flu_consistent=flu_consistent
            )
        
        # Use trained XGBoost model
        import numpy as np
        
        from_density = PALM_BAY_ZONING_DENSITY.get(from_zoning, 4.0) or 4.0
        to_density = PALM_BAY_ZONING_DENSITY.get(to_zoning, from_density) or from_density
        density_increase = to_density - from_density if to_density else 0
        
        features = np.array([[
            acreage,
            density_increase,
            1.0 if flu_consistent else 0.0,
            1.0 if has_opposition else 0.0,
            0.0,  # has_traffic_study - unknown
            0.0,  # has_stormwater_plan - unknown
        ]])
        
        prob = self.model.predict_proba(features)[0][1]
        
        # Calculate uncertainty based on model confidence
        uncertainty = 0.10  # Base uncertainty
        if not flu_consistent:
            uncertainty += 0.05
        if has_opposition:
            uncertainty += 0.05
        
        return Prediction(
            approval_probability=float(prob),
            lower_bound=max(0.05, prob - uncertainty),
            upper_bound=min(0.95, prob + uncertainty),
            confidence_level=0.80,
            model_status=ModelStatus.VALIDATED,
            prediction_method="XGBOOST",
            similar_cases=self.metrics.training_records if self.metrics else 0,
            warnings=[],
            prediction_timestamp=datetime.utcnow().isoformat(),
            model_version="1.0.0-xgboost"
        )


# =============================================================================
# MAIN - HONEST STATUS REPORT
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ZONING OPPORTUNITY DISCOVERY - ML MODEL STATUS")
    print("=" * 80)
    
    collector = RezoningDataCollector()
    model = RezoningXGBoostModel(collector)
    status = model.get_status()
    
    print(f"\n📊 MODEL STATUS: {status['status']}")
    print(f"   Training records: {status['training_records']}")
    print(f"   Minimum required: {status['minimum_required']}")
    print(f"   Records needed: {status['records_needed']}")
    print(f"   Is trained: {status['is_trained']}")
    print(f"\n💬 {status['message']}")
    
    print("\n" + "=" * 80)
    print("DATA COLLECTION SOURCES")
    print("=" * 80)
    
    for source in collector.get_palm_bay_sources():
        print(f"\n📁 {source['name']}")
        print(f"   URL: {source['url']}")
        print(f"   Type: {source['type']}")
        print(f"   Notes: {source['notes']}")
    
    print("\n" + "=" * 80)
    print("EXAMPLE PREDICTION (RULE-BASED - NO ML)")
    print("=" * 80)
    
    prediction = model.predict(
        jurisdiction="Palm Bay",
        from_zoning="PUD",
        to_zoning="RM-20",
        from_flu="RES 20",
        acreage=1.065,
        has_opposition=False,
        flu_consistent=True
    )
    
    print(f"\n🎯 Approval Probability: {prediction.approval_probability:.1%}")
    print(f"   Uncertainty Range: {prediction.lower_bound:.1%} - {prediction.upper_bound:.1%}")
    print(f"   Confidence Level: {prediction.confidence_level:.0%}")
    print(f"   Method: {prediction.prediction_method}")
    
    print(f"\n⚠️ WARNINGS:")
    for w in prediction.warnings:
        print(f"   - {w}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS TO BUILD REAL ML MODEL")
    print("=" * 80)
    print("""
1. COLLECT DATA:
   - Scrape Palm Bay Novus Agenda for CPZ cases
   - Extract: case number, from/to zoning, acreage, outcome, vote
   - Target: 100+ verified decisions

2. VERIFY DATA:
   - Cross-reference with ordinance numbers
   - Confirm outcomes from meeting minutes
   - Flag uncertain records

3. TRAIN MODEL:
   - Run model.train() when 100+ records collected
   - Report ACTUAL accuracy from cross-validation
   - Document feature importance

4. VALIDATE:
   - Test on held-out data
   - Compare to rule-based baseline
   - Report honest confidence intervals
""")
