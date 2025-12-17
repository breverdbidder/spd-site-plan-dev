"""
Zoning-FLU Opportunity Discovery - State Schema
================================================
State management for multi-agent orchestration identifying rezoning opportunities.

Core Concept: Properties where current zoning < FLU maximum = rezoning opportunity
Example: Bliss Palm Bay - PUD zoning in HDR area → RM-20 rezoning opportunity
"""

from typing import TypedDict, List, Dict, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class OpportunityGrade(Enum):
    """Opportunity scoring grades"""
    A_PLUS = "A+"   # Score 90-100: Immediate action
    A = "A"         # Score 80-89: Strong opportunity
    B_PLUS = "B+"   # Score 70-79: Good opportunity
    B = "B"         # Score 60-69: Moderate opportunity
    C = "C"         # Score 50-59: Marginal opportunity
    D = "D"         # Score 40-49: Weak opportunity
    F = "F"         # Score <40: Not viable


class ZoningCategory(Enum):
    """Standard Florida zoning categories"""
    RS = "RS"           # Single Family Residential
    RM_6 = "RM-6"       # Multi-family 6 du/acre
    RM_10 = "RM-10"     # Multi-family 10 du/acre
    RM_15 = "RM-15"     # Multi-family 15 du/acre
    RM_20 = "RM-20"     # Multi-family 20 du/acre
    RM_25 = "RM-25"     # Multi-family 25 du/acre
    PUD = "PUD"         # Planned Unit Development
    C_1 = "C-1"         # Neighborhood Commercial
    C_2 = "C-2"         # General Commercial
    MU = "MU"           # Mixed Use


class FLUCategory(Enum):
    """Future Land Use designations"""
    LDR = "LDR"         # Low Density Residential (1-4 du/acre)
    MDR = "MDR"         # Medium Density Residential (5-10 du/acre)
    HDR = "HDR"         # High Density Residential (11-25 du/acre)
    NC = "NC"           # Neighborhood Commercial
    GC = "GC"           # General Commercial
    MU = "MU"           # Mixed Use
    IND = "IND"         # Industrial


# Density mapping by FLU category (max du/acre)
FLU_DENSITY_MAX = {
    FLUCategory.LDR: 4,
    FLUCategory.MDR: 10,
    FLUCategory.HDR: 25,
    FLUCategory.NC: 0,    # Commercial - no residential
    FLUCategory.GC: 0,
    FLUCategory.MU: 20,
    FLUCategory.IND: 0,
}

# Density mapping by zoning district (max du/acre)
ZONING_DENSITY = {
    ZoningCategory.RS: 4,
    ZoningCategory.RM_6: 6,
    ZoningCategory.RM_10: 10,
    ZoningCategory.RM_15: 15,
    ZoningCategory.RM_20: 20,
    ZoningCategory.RM_25: 25,
    ZoningCategory.PUD: 8,    # Varies, default assumption
    ZoningCategory.C_1: 0,
    ZoningCategory.C_2: 0,
    ZoningCategory.MU: 15,
}


@dataclass
class ParcelData:
    """Property appraiser parcel data"""
    parcel_id: str
    account_number: str
    address: str
    city: str
    zip_code: str
    owner_name: str
    acreage: float
    lot_sf: int
    assessed_value: float
    just_value: float
    legal_description: str
    use_code: str
    use_description: str
    year_built: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ZoningData:
    """Current zoning classification"""
    district: str
    district_name: str
    density_max: float          # du/acre allowed by zoning
    setbacks: Dict[str, float]  # front, rear, side
    max_height: float
    max_lot_coverage: float
    overlay_districts: List[str] = field(default_factory=list)
    special_restrictions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FLUData:
    """Future Land Use designation"""
    designation: str
    designation_name: str
    density_max: float          # Maximum du/acre per FLU
    intensity_max: Optional[float] = None  # FAR for commercial
    compatible_zonings: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConstraintData:
    """Site development constraints"""
    constraint_type: str        # wellhead, wetland, flood, easement
    impact_description: str
    area_affected_sf: int
    area_affected_pct: float
    is_absolute: bool           # True = no development, False = design around
    resolution_options: List[str] = field(default_factory=list)
    resolution_timeline: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DensityGap:
    """The core opportunity metric"""
    current_density: float      # Zoning allows
    flu_density: float          # FLU allows
    gap_du_acre: float          # FLU - current
    gap_percentage: float       # (FLU - current) / current * 100
    potential_units_current: int
    potential_units_flu: int
    additional_units: int       # Units gained by rezoning
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RezoningHistory:
    """Recent rezoning application in area"""
    case_number: str
    address: str
    from_zoning: str
    to_zoning: str
    flu_designation: str
    density_requested: float
    acreage: float
    status: str                 # APPROVED, DENIED, PENDING, WITHDRAWN
    decision_date: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    vote_count: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OpportunityScore:
    """Final scoring for opportunity ranking"""
    total_score: float          # 0-100
    grade: str                  # A+, A, B+, B, C, D, F
    
    # Component scores (each 0-100, weighted)
    density_gap_score: float    # Weight: 25%
    lot_size_score: float       # Weight: 15%
    constraint_score: float     # Weight: 20%
    market_score: float         # Weight: 15%
    rezoning_probability: float # Weight: 25%
    
    # Scoring rationale
    scoring_factors: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegulatoryPathway:
    """Required approvals and timeline"""
    steps: List[Dict[str, Any]]     # Ordered list of approval steps
    total_timeline_months: int
    total_estimated_cost: float
    critical_path_items: List[str]
    stakeholders: List[str]
    risk_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OpportunityState(TypedDict, total=False):
    """
    Complete state for Zoning-FLU Opportunity Discovery pipeline.
    
    Stages:
    1. Data Acquisition    - Pull parcel, zoning, FLU data
    2. Zoning Analysis     - Parse current zoning restrictions
    3. FLU Analysis        - Determine FLU maximum density
    4. Constraint Mapping  - Identify development constraints
    5. Opportunity Scoring - Calculate and rank opportunities
    6. Market Validation   - Research comparable rezonings
    7. Regulatory Pathway  - Map approval requirements
    """
    
    # =========================================================================
    # INPUT PARAMETERS
    # =========================================================================
    jurisdiction: str               # "Palm Bay", "Melbourne", "Brevard County"
    target_flu_categories: List[str]  # ["HDR", "MDR"] - FLU categories to search
    min_acreage: float              # Minimum lot size
    max_parcels: int                # Maximum parcels to analyze
    
    # =========================================================================
    # STAGE 1: DATA ACQUISITION
    # =========================================================================
    parcels_raw: List[Dict[str, Any]]   # Raw parcel data from BCPAO
    parcels: List[ParcelData]           # Parsed parcel objects
    acquisition_timestamp: str
    acquisition_source: str
    acquisition_errors: List[str]
    
    # =========================================================================
    # STAGE 2: ZONING ANALYSIS
    # =========================================================================
    zoning_data: Dict[str, ZoningData]  # parcel_id -> ZoningData
    zoning_ordinance_url: str
    zoning_map_url: str
    zoning_analysis_timestamp: str
    
    # =========================================================================
    # STAGE 3: FLU ANALYSIS
    # =========================================================================
    flu_data: Dict[str, FLUData]        # parcel_id -> FLUData
    comp_plan_url: str
    flu_map_url: str
    flu_analysis_timestamp: str
    
    # =========================================================================
    # STAGE 4: DENSITY GAP CALCULATION
    # =========================================================================
    density_gaps: Dict[str, DensityGap]  # parcel_id -> DensityGap
    opportunities_identified: int
    total_additional_units: int
    density_gap_timestamp: str
    
    # =========================================================================
    # STAGE 5: CONSTRAINT MAPPING
    # =========================================================================
    constraints: Dict[str, List[ConstraintData]]  # parcel_id -> constraints
    buildable_area: Dict[str, float]    # parcel_id -> buildable_sf after constraints
    buildable_pct: Dict[str, float]     # parcel_id -> buildable percentage
    constraint_timestamp: str
    
    # =========================================================================
    # STAGE 6: OPPORTUNITY SCORING
    # =========================================================================
    scores: Dict[str, OpportunityScore]  # parcel_id -> score
    ranked_parcels: List[str]           # Parcel IDs sorted by score
    top_opportunities: List[Dict[str, Any]]  # Top N with full details
    scoring_timestamp: str
    
    # =========================================================================
    # STAGE 7: MARKET VALIDATION
    # =========================================================================
    rezoning_history: List[RezoningHistory]
    approval_rate: float                # % approved in last 2 years
    comparable_developments: List[Dict[str, Any]]
    market_demand_score: float
    market_validation_timestamp: str
    
    # =========================================================================
    # STAGE 8: REGULATORY PATHWAY
    # =========================================================================
    pathways: Dict[str, RegulatoryPathway]  # parcel_id -> pathway
    pathway_timestamp: str
    
    # =========================================================================
    # FINAL OUTPUT
    # =========================================================================
    final_report: Dict[str, Any]
    report_path: str
    
    # =========================================================================
    # METADATA & TRACKING
    # =========================================================================
    pipeline_id: str
    pipeline_version: str
    created_at: str
    updated_at: str
    current_stage: int
    stages_completed: List[int]
    errors: List[Dict[str, Any]]
    warnings: List[str]
    
    # Human-in-the-loop checkpoints
    human_review_required: bool
    human_review_notes: str
    human_approved: bool


def create_initial_opportunity_state(
    jurisdiction: str,
    target_flu_categories: List[str] = None,
    min_acreage: float = 0.5,
    max_parcels: int = 100
) -> OpportunityState:
    """Create initial state for opportunity discovery pipeline"""
    import uuid
    
    now = datetime.utcnow().isoformat()
    
    return OpportunityState(
        jurisdiction=jurisdiction,
        target_flu_categories=target_flu_categories or ["HDR", "MDR"],
        min_acreage=min_acreage,
        max_parcels=max_parcels,
        parcels_raw=[],
        parcels=[],
        acquisition_errors=[],
        zoning_data={},
        flu_data={},
        density_gaps={},
        opportunities_identified=0,
        total_additional_units=0,
        constraints={},
        buildable_area={},
        buildable_pct={},
        scores={},
        ranked_parcels=[],
        top_opportunities=[],
        rezoning_history=[],
        approval_rate=0.0,
        comparable_developments=[],
        market_demand_score=0.0,
        pathways={},
        pipeline_id=str(uuid.uuid4())[:8],
        pipeline_version="1.0.0",
        created_at=now,
        updated_at=now,
        current_stage=1,
        stages_completed=[],
        errors=[],
        warnings=[],
        human_review_required=False,
        human_review_notes="",
        human_approved=False
    )


def calculate_density_gap(
    zoning: ZoningData,
    flu: FLUData,
    acreage: float
) -> DensityGap:
    """Calculate the density gap opportunity"""
    current = zoning.density_max
    flu_max = flu.density_max
    gap = flu_max - current
    gap_pct = (gap / current * 100) if current > 0 else 100
    
    current_units = int(acreage * current)
    flu_units = int(acreage * flu_max)
    
    return DensityGap(
        current_density=current,
        flu_density=flu_max,
        gap_du_acre=gap,
        gap_percentage=gap_pct,
        potential_units_current=current_units,
        potential_units_flu=flu_units,
        additional_units=flu_units - current_units
    )


def calculate_opportunity_score(
    density_gap: DensityGap,
    acreage: float,
    buildable_pct: float,
    approval_rate: float,
    constraint_count: int
) -> OpportunityScore:
    """Calculate composite opportunity score"""
    factors = []
    red_flags = []
    
    # 1. Density Gap Score (25% weight)
    # Higher gap = better opportunity
    if density_gap.gap_du_acre >= 10:
        density_score = 100
        factors.append(f"Excellent density gap: {density_gap.gap_du_acre} du/acre")
    elif density_gap.gap_du_acre >= 5:
        density_score = 75
        factors.append(f"Good density gap: {density_gap.gap_du_acre} du/acre")
    elif density_gap.gap_du_acre >= 2:
        density_score = 50
        factors.append(f"Moderate density gap: {density_gap.gap_du_acre} du/acre")
    else:
        density_score = 25
        red_flags.append(f"Small density gap: {density_gap.gap_du_acre} du/acre")
    
    # 2. Lot Size Score (15% weight)
    if acreage >= 2.0:
        lot_score = 100
        factors.append(f"Large lot: {acreage:.2f} acres")
    elif acreage >= 1.0:
        lot_score = 75
        factors.append(f"Good lot size: {acreage:.2f} acres")
    elif acreage >= 0.5:
        lot_score = 50
    else:
        lot_score = 25
        red_flags.append(f"Small lot may limit efficiency")
    
    # 3. Constraint Score (20% weight)
    # Higher buildable % = better score
    if buildable_pct >= 80:
        constraint_score = 100
        factors.append("Minimal constraints")
    elif buildable_pct >= 60:
        constraint_score = 75
        factors.append(f"{100-buildable_pct:.0f}% constrained area")
    elif buildable_pct >= 40:
        constraint_score = 50
        red_flags.append(f"Significant constraints: {100-buildable_pct:.0f}% affected")
    else:
        constraint_score = 25
        red_flags.append(f"Major constraints: {100-buildable_pct:.0f}% affected")
    
    # 4. Market Score (15% weight) - placeholder
    market_score = 70  # Default, would come from market analysis
    
    # 5. Rezoning Probability (25% weight)
    if approval_rate >= 80:
        rezoning_score = 100
        factors.append(f"High approval rate: {approval_rate:.0f}%")
    elif approval_rate >= 60:
        rezoning_score = 75
        factors.append(f"Good approval rate: {approval_rate:.0f}%")
    elif approval_rate >= 40:
        rezoning_score = 50
        red_flags.append(f"Moderate approval rate: {approval_rate:.0f}%")
    else:
        rezoning_score = 25
        red_flags.append(f"Low approval rate: {approval_rate:.0f}%")
    
    # Calculate weighted total
    total = (
        density_score * 0.25 +
        lot_score * 0.15 +
        constraint_score * 0.20 +
        market_score * 0.15 +
        rezoning_score * 0.25
    )
    
    # Determine grade
    if total >= 90:
        grade = "A+"
    elif total >= 80:
        grade = "A"
    elif total >= 70:
        grade = "B+"
    elif total >= 60:
        grade = "B"
    elif total >= 50:
        grade = "C"
    elif total >= 40:
        grade = "D"
    else:
        grade = "F"
    
    return OpportunityScore(
        total_score=total,
        grade=grade,
        density_gap_score=density_score,
        lot_size_score=lot_score,
        constraint_score=constraint_score,
        market_score=market_score,
        rezoning_probability=rezoning_score,
        scoring_factors=factors,
        red_flags=red_flags
    )
