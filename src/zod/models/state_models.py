"""
ZOD State Models - Pydantic models for type safety and validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class OpportunityGrade(str, Enum):
    """Opportunity scoring grades"""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class ZoningDistrict(BaseModel):
    """Zoning district definition"""
    code: str
    description: str
    max_density_du_acre: float = 0
    permitted_uses: list[str] = Field(default_factory=list)
    overlays: list[str] = Field(default_factory=list)
    setback_front: float = 25
    setback_side: float = 10
    setback_rear: float = 20
    max_height: float = 35
    lot_coverage: float = 50


class FLUDesignation(BaseModel):
    """Future Land Use designation from comprehensive plan"""
    code: str
    description: str
    min_density_du_acre: float = 0
    max_density_du_acre: float = 0
    permitted_zoning: list[str] = Field(default_factory=list)
    intensity_max: Optional[float] = None  # FAR for commercial


class Constraint(BaseModel):
    """Environmental or physical constraint"""
    type: str
    description: str
    acres_affected: float
    is_absolute: bool = False  # True = no development allowed
    mitigation_possible: bool = True
    estimated_mitigation_cost: Optional[float] = None


class ConstraintAnalysis(BaseModel):
    """Constraint analysis results for a parcel"""
    total_acres: float
    wetland_acres: float = 0
    flood_zone_acres: float = 0
    easement_acres: float = 0
    wellhead_protection_acres: float = 0
    total_encumbered_acres: float = 0
    buildable_acres: float = 0
    buildable_pct: float = 0
    constraints_detail: list[Constraint] = Field(default_factory=list)
    is_viable: bool = True


class ZoningAnalysis(BaseModel):
    """Zoning analysis results"""
    current_zoning: str
    max_density: float = 0
    permitted_uses: list[str] = Field(default_factory=list)
    overlays: list[str] = Field(default_factory=list)
    setback_front_ft: float = 25
    setback_side_ft: float = 10
    setback_rear_ft: float = 20
    max_height_ft: float = 35
    max_lot_coverage_pct: float = 50


class FLUAnalysis(BaseModel):
    """FLU analysis results"""
    flu_designation: str
    flu_description: str = ""
    flu_max_density: float = 0
    flu_min_density: float = 0
    permitted_zoning_districts: list[str] = Field(default_factory=list)
    density_gap: float = 0
    density_gap_pct: float = 0
    has_opportunity: bool = False


class UnitAnalysis(BaseModel):
    """Unit count analysis"""
    current_max_units: int = 0
    potential_max_units: int = 0
    unit_upside: int = 0


class ScoreComponents(BaseModel):
    """Breakdown of opportunity score"""
    density_gap_score: float = 0
    lot_size_score: float = 0
    buildable_score: float = 0
    flu_alignment_score: float = 0
    market_demand_score: float = 0
    rezoning_probability_score: float = 0


class OpportunityScore(BaseModel):
    """Opportunity scoring results"""
    total_score: float = 0
    grade: OpportunityGrade = OpportunityGrade.F
    components: ScoreComponents = Field(default_factory=ScoreComponents)
    unit_analysis: UnitAnalysis = Field(default_factory=UnitAnalysis)


class RezoningHistory(BaseModel):
    """Rezoning history for market validation"""
    total_nearby: int = 0
    similar_requests: int = 0
    approved: int = 0
    approval_rate_pct: float = 0


class MarketValidation(BaseModel):
    """Market validation results"""
    validated: bool = False
    reason: Optional[str] = None
    rezoning_history: Optional[RezoningHistory] = None
    comparable_developments: int = 0
    opposition_risk: str = "UNKNOWN"
    validation_date: Optional[datetime] = None


class ApprovalStep(BaseModel):
    """Single approval step in regulatory pathway"""
    type: str
    authority: str
    timeline_months: int
    cost_estimate: float
    notes: str = ""


class Stakeholder(BaseModel):
    """Stakeholder in approval process"""
    type: str
    role: str


class RegulatoryPathway(BaseModel):
    """Full regulatory pathway analysis"""
    full_analysis: bool = False
    reason: Optional[str] = None
    approvals_required: list[ApprovalStep] = Field(default_factory=list)
    total_timeline_months: int = 0
    estimated_total_cost: float = 0
    cost_breakdown: dict[str, float] = Field(default_factory=dict)
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    recommended_sequence: list[str] = Field(default_factory=list)


class Parcel(BaseModel):
    """Complete parcel data with all analyses"""
    # Identification
    parcel_id: str
    account_id: Optional[str] = None
    address: str
    city: str
    state: str = "FL"
    zip_code: Optional[str] = None
    
    # Physical
    acres: float
    legal_description: Optional[str] = None
    
    # Raw data
    zoning_code: str
    flu_designation: str
    owner_name: Optional[str] = None
    
    # Analyses (populated through pipeline)
    zoning_analysis: Optional[ZoningAnalysis] = None
    flu_analysis: Optional[FLUAnalysis] = None
    constraint_analysis: Optional[ConstraintAnalysis] = None
    opportunity_score: Optional[OpportunityScore] = None
    market_validation: Optional[MarketValidation] = None
    regulatory_pathway: Optional[RegulatoryPathway] = None


class Checkpoint(BaseModel):
    """Pipeline checkpoint for resume capability"""
    stage: str
    timestamp: datetime
    data: dict = Field(default_factory=dict)


class ZODSummary(BaseModel):
    """Pipeline execution summary"""
    generated_at: datetime
    jurisdiction: str
    total_opportunities: int
    grade_distribution: dict[str, int]
    top_opportunity: Optional[dict] = None
    total_unit_upside: int = 0
    average_score: float = 0


# =============================================================================
# BREVARD COUNTY SPECIFIC DEFINITIONS
# =============================================================================

BREVARD_ZONING_DISTRICTS: dict[str, ZoningDistrict] = {
    "RS-1": ZoningDistrict(
        code="RS-1",
        description="Single Family Residential (1 unit/acre)",
        max_density_du_acre=1,
        permitted_uses=["single_family"],
        setback_front=25,
        setback_side=10,
        setback_rear=20
    ),
    "RS-2": ZoningDistrict(
        code="RS-2",
        description="Single Family Residential (2 units/acre)",
        max_density_du_acre=2,
        permitted_uses=["single_family"],
        setback_front=25,
        setback_side=7.5,
        setback_rear=20
    ),
    "RS-4": ZoningDistrict(
        code="RS-4",
        description="Single Family Residential (4 units/acre)",
        max_density_du_acre=4,
        permitted_uses=["single_family", "duplex"],
        setback_front=25,
        setback_side=7.5,
        setback_rear=20
    ),
    "RM-6": ZoningDistrict(
        code="RM-6",
        description="Residential Multi-Family (6 units/acre)",
        max_density_du_acre=6,
        permitted_uses=["single_family", "duplex", "multifamily"],
        setback_front=25,
        setback_side=10,
        setback_rear=20
    ),
    "RM-10": ZoningDistrict(
        code="RM-10",
        description="Residential Multi-Family (10 units/acre)",
        max_density_du_acre=10,
        permitted_uses=["single_family", "duplex", "multifamily", "townhouse"],
        setback_front=25,
        setback_side=10,
        setback_rear=20
    ),
    "RM-15": ZoningDistrict(
        code="RM-15",
        description="Residential Multi-Family (15 units/acre)",
        max_density_du_acre=15,
        permitted_uses=["single_family", "duplex", "multifamily", "townhouse"],
        setback_front=25,
        setback_side=10,
        setback_rear=25
    ),
    "RM-20": ZoningDistrict(
        code="RM-20",
        description="Residential Multi-Family (20 units/acre)",
        max_density_du_acre=20,
        permitted_uses=["multifamily", "townhouse", "apartment"],
        setback_front=25,
        setback_side=15,
        setback_rear=25,
        max_height=45
    ),
    "PUD": ZoningDistrict(
        code="PUD",
        description="Planned Unit Development",
        max_density_du_acre=0,  # Varies by specific PUD
        permitted_uses=["per_pud_document"],
        setback_front=0,  # Per PUD document
        setback_side=0,
        setback_rear=0
    )
}

BREVARD_FLU_DESIGNATIONS: dict[str, FLUDesignation] = {
    "LDR": FLUDesignation(
        code="LDR",
        description="Low Density Residential",
        min_density_du_acre=0,
        max_density_du_acre=4,
        permitted_zoning=["RS-1", "RS-2", "RS-4"]
    ),
    "MDR": FLUDesignation(
        code="MDR",
        description="Medium Density Residential",
        min_density_du_acre=4,
        max_density_du_acre=10,
        permitted_zoning=["RS-4", "RM-6", "RM-10"]
    ),
    "HDR": FLUDesignation(
        code="HDR",
        description="High Density Residential",
        min_density_du_acre=10,
        max_density_du_acre=20,
        permitted_zoning=["RM-10", "RM-15", "RM-20"]
    ),
    "MXU": FLUDesignation(
        code="MXU",
        description="Mixed Use",
        min_density_du_acre=0,
        max_density_du_acre=25,
        permitted_zoning=["RM-15", "RM-20", "BU-1", "BU-2"],
        intensity_max=2.0  # FAR
    ),
    "NC": FLUDesignation(
        code="NC",
        description="Neighborhood Commercial",
        min_density_du_acre=0,
        max_density_du_acre=15,
        permitted_zoning=["BU-1", "RM-15"],
        intensity_max=1.0
    )
}


# =============================================================================
# PALM BAY SPECIFIC DEFINITIONS
# =============================================================================

PALM_BAY_ZONING_DISTRICTS: dict[str, ZoningDistrict] = {
    "RS-1": ZoningDistrict(
        code="RS-1",
        description="Single Family Residential (1 unit/acre)",
        max_density_du_acre=1,
        permitted_uses=["single_family"],
        setback_front=25,
        setback_side=10,
        setback_rear=20
    ),
    "RS-2": ZoningDistrict(
        code="RS-2",
        description="Single Family Residential (2 units/acre)",
        max_density_du_acre=2,
        permitted_uses=["single_family"],
        setback_front=25,
        setback_side=7.5,
        setback_rear=20
    ),
    "RM-6": ZoningDistrict(
        code="RM-6",
        description="Residential Multi-Family (6 units/acre)",
        max_density_du_acre=6,
        permitted_uses=["single_family", "duplex", "multifamily"],
        setback_front=25,
        setback_side=10,
        setback_rear=20
    ),
    "RM-10": ZoningDistrict(
        code="RM-10",
        description="Residential Multi-Family (10 units/acre)",
        max_density_du_acre=10,
        permitted_uses=["single_family", "duplex", "multifamily", "townhouse"],
        setback_front=25,
        setback_side=10,
        setback_rear=20
    ),
    "RM-15": ZoningDistrict(
        code="RM-15",
        description="Residential Multi-Family (15 units/acre)",
        max_density_du_acre=15,
        permitted_uses=["single_family", "duplex", "multifamily", "townhouse"],
        setback_front=25,
        setback_side=10,
        setback_rear=25
    ),
    "RM-20": ZoningDistrict(
        code="RM-20",
        description="Residential Multi-Family (20 units/acre)",
        max_density_du_acre=20,
        permitted_uses=["multifamily", "townhouse", "apartment"],
        setback_front=25,
        setback_side=15,
        setback_rear=25,
        max_height=45
    ),
    "PUD": ZoningDistrict(
        code="PUD",
        description="Planned Unit Development",
        max_density_du_acre=0,  # Per PUD document - MUST research specific PUD
        permitted_uses=["per_pud_document"],
        setback_front=0,
        setback_side=0,
        setback_rear=0
    )
}

PALM_BAY_FLU_DESIGNATIONS: dict[str, FLUDesignation] = {
    "LDR": FLUDesignation(
        code="LDR",
        description="Low Density Residential (up to 4 du/ac)",
        min_density_du_acre=0,
        max_density_du_acre=4,
        permitted_zoning=["RS-1", "RS-2"]
    ),
    "MDR": FLUDesignation(
        code="MDR", 
        description="Medium Density Residential (4-10 du/ac)",
        min_density_du_acre=4,
        max_density_du_acre=10,
        permitted_zoning=["RM-6", "RM-10"]
    ),
    "HDR": FLUDesignation(
        code="HDR",
        description="High Density Residential (10-20 du/ac)",
        min_density_du_acre=10,
        max_density_du_acre=20,
        permitted_zoning=["RM-10", "RM-15", "RM-20"]
    ),
    "MXU": FLUDesignation(
        code="MXU",
        description="Mixed Use",
        min_density_du_acre=0,
        max_density_du_acre=20,
        permitted_zoning=["RM-15", "RM-20", "C-1", "C-2"],
        intensity_max=2.0
    )
}


def get_jurisdiction_definitions(jurisdiction: str) -> tuple[dict, dict]:
    """
    Get zoning and FLU definitions for a jurisdiction.
    
    Args:
        jurisdiction: Name of jurisdiction (e.g., "Palm Bay", "Brevard County")
    
    Returns:
        Tuple of (zoning_districts, flu_designations) dicts
    """
    jurisdiction_lower = jurisdiction.lower()
    
    if "palm bay" in jurisdiction_lower:
        return PALM_BAY_ZONING_DISTRICTS, PALM_BAY_FLU_DESIGNATIONS
    elif "brevard" in jurisdiction_lower:
        return BREVARD_ZONING_DISTRICTS, BREVARD_FLU_DESIGNATIONS
    else:
        # Default to Brevard County definitions
        return BREVARD_ZONING_DISTRICTS, BREVARD_FLU_DESIGNATIONS
