"""
SPD Site Plan Development - LangGraph State Schema
===================================================
Defines the state structure for the 12-stage SPD pipeline.

Stages:
1. Discovery        - Property identification and initial data gathering
2. Site Analysis    - Physical site constraints and measurements
3. Zoning Review    - Zoning district, density, setbacks
4. Parking/Unit     - Parking requirements and unit configurations
5. Building Design  - Building footprint, stories, height
6. Financial        - Pro forma, NOI, value calculations
7. Risk Assessment  - Market risk, entitlement risk
8. Report           - Generate due diligence report
9. Decision         - BID / REVIEW / SKIP recommendation
10. Entitlement     - Track rezoning, variances, permits
11. Construction    - Construction timeline and milestones
12. Archive         - Store completed analysis
"""

from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SPDDecision(Enum):
    """Final decision outcomes"""
    BID = "BID"
    REVIEW = "REVIEW"
    SKIP = "SKIP"
    PENDING = "PENDING"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SPDState(TypedDict, total=False):
    """
    Complete state schema for SPD LangGraph pipeline.
    
    All fields are optional (total=False) to allow incremental population
    as the pipeline progresses through stages.
    """
    
    # ==========================================================================
    # STAGE 1: DISCOVERY
    # ==========================================================================
    property_id: str                    # BCPAO account number
    address: str                        # Full property address
    parcel_id: str                      # Parcel identification number
    owner_name: str                     # Current owner
    legal_description: str              # Legal description
    discovery_complete: bool
    discovery_timestamp: str
    
    # ==========================================================================
    # STAGE 2: SITE ANALYSIS
    # ==========================================================================
    site_constraints: Dict[str, Any]    # SiteConstraints as dict
    # Keys: lot_sf, lot_width, lot_depth, easement_sf, wellhead_sf,
    #       front_setback, rear_setback, side_setback, max_lot_coverage,
    #       max_height_no_variance
    
    lot_acres: float
    buildable_sf: float
    building_envelope_sf: float
    site_analysis_complete: bool
    site_analysis_timestamp: str
    
    # ==========================================================================
    # STAGE 3: ZONING REVIEW
    # ==========================================================================
    current_zoning: str                 # Current zoning district (e.g., "RM_15")
    target_zoning: str                  # Target zoning if rezoning needed
    zoning_district: str                # Zoning for calculations
    density_allowed: float              # du/acre
    max_dwelling_units: int
    flu_designation: str                # Future Land Use
    flu_compatible: bool                # FLU supports target zoning
    rezoning_required: bool
    rezoning_fee: float
    
    setbacks: Dict[str, float]          # front, rear, side setbacks
    max_height: float                   # Max height without variance
    max_lot_coverage: float
    
    zoning_review_complete: bool
    zoning_review_timestamp: str
    
    # ==========================================================================
    # STAGE 4: PARKING & UNIT CONFIGURATION
    # ==========================================================================
    parking_available: int              # Total parking spaces available
    parking_per_dwelling: int           # Code requirement per dwelling
    
    parking_analysis: Dict[str, Any]    # Output from parking_unit_config.py
    # Keys: scenarios (list), comparison (dict)
    
    recommended_scenario: str           # "Scenario A" or "Scenario B"
    recommendation_reason: str
    
    selected_scenario: Dict[str, Any]   # User-selected or recommended scenario
    # Keys: dwelling_units, micro_units_per_dwelling, total_tenants,
    #       micro_unit_sf, dwelling_unit_sf, parking, building, financials,
    #       rent, risk_level, recommendation
    
    unit_config_complete: bool
    unit_config_timestamp: str
    
    # ==========================================================================
    # STAGE 5: BUILDING DESIGN
    # ==========================================================================
    building_spec: Dict[str, Any]
    # Keys: gross_sf, stories, footprint_sf, height_ft, fits_envelope,
    #       requires_variance, units_per_floor
    
    floor_plan: Dict[str, Any]          # Floor plate design
    unit_layouts: List[Dict[str, Any]]  # Micro-unit layouts
    
    variance_required: bool
    variance_type: str                  # "HEIGHT", "SETBACK", "COVERAGE"
    variance_justification: str
    
    building_design_complete: bool
    building_design_timestamp: str
    
    # ==========================================================================
    # STAGE 6: FINANCIAL PRO FORMA
    # ==========================================================================
    rent_structure: Dict[str, int]      # with_parking, no_parking rates
    
    financial_projections: Dict[str, Any]
    # Keys: monthly_gross, annual_gpr, vacancy_rate, egi, opex_rate,
    #       opex, noi, cap_rate, value, construction_cost, cash_on_cash
    
    development_costs: Dict[str, float]
    # Keys: hard_costs, soft_costs, land_cost, ebike_infrastructure, total
    
    returns: Dict[str, float]
    # Keys: noi, value, equity_created, irr, cash_on_cash
    
    financial_complete: bool
    financial_timestamp: str
    
    # ==========================================================================
    # STAGE 7: RISK ASSESSMENT
    # ==========================================================================
    market_risk: str                    # LOW, MEDIUM, HIGH
    market_risk_factors: List[str]
    
    entitlement_risk: str               # LOW, MEDIUM, HIGH
    entitlement_risk_factors: List[str]
    
    construction_risk: str              # LOW, MEDIUM, HIGH
    construction_risk_factors: List[str]
    
    overall_risk: str                   # Combined risk level
    risk_mitigation: List[str]          # Mitigation strategies
    
    risk_assessment_complete: bool
    risk_assessment_timestamp: str
    
    # ==========================================================================
    # STAGE 8: REPORT GENERATION
    # ==========================================================================
    report_path: str                    # Path to generated report
    report_format: str                  # "DOCX", "PDF", "HTML"
    report_sections: List[str]          # Sections included
    
    report_complete: bool
    report_timestamp: str
    
    # ==========================================================================
    # STAGE 9: DECISION
    # ==========================================================================
    decision: str                       # BID, REVIEW, SKIP
    decision_score: float               # 0-100 score
    decision_factors: List[str]         # Key factors in decision
    decision_notes: str                 # Human notes
    
    decision_complete: bool
    decision_timestamp: str
    
    # ==========================================================================
    # STAGE 10: ENTITLEMENT TRACKING
    # ==========================================================================
    entitlements: List[Dict[str, Any]]  # List of required entitlements
    # Each: type, status, submitted_date, hearing_date, approved_date, notes
    
    pre_application_meeting: Dict[str, Any]
    # Keys: date, contact, notes, questions, answers
    
    rezoning_status: str                # PENDING, SUBMITTED, APPROVED, DENIED
    variance_status: str
    site_plan_status: str
    
    entitlement_complete: bool
    entitlement_timestamp: str
    
    # ==========================================================================
    # STAGE 11: CONSTRUCTION
    # ==========================================================================
    construction_timeline: Dict[str, Any]
    # Keys: start_date, end_date, milestones, current_phase
    
    permits: List[Dict[str, Any]]       # Building permits
    inspections: List[Dict[str, Any]]   # Inspection results
    
    construction_complete: bool
    construction_timestamp: str
    
    # ==========================================================================
    # STAGE 12: ARCHIVE
    # ==========================================================================
    archived: bool
    archive_timestamp: str
    archive_location: str               # Supabase table/row ID
    
    # ==========================================================================
    # METADATA
    # ==========================================================================
    pipeline_version: str               # SPD pipeline version
    created_at: str
    updated_at: str
    created_by: str
    
    # Stage tracking
    current_stage: int                  # 1-12
    stages_completed: List[int]
    
    # Error handling
    errors: List[Dict[str, Any]]        # Error log
    warnings: List[str]                 # Warning messages


# =============================================================================
# STATE HELPERS
# =============================================================================

def create_initial_state(
    property_id: str,
    address: str
) -> SPDState:
    """Create initial state for a new SPD analysis"""
    now = datetime.utcnow().isoformat()
    
    return SPDState(
        property_id=property_id,
        address=address,
        discovery_complete=False,
        site_analysis_complete=False,
        zoning_review_complete=False,
        unit_config_complete=False,
        building_design_complete=False,
        financial_complete=False,
        risk_assessment_complete=False,
        report_complete=False,
        decision_complete=False,
        entitlement_complete=False,
        construction_complete=False,
        archived=False,
        pipeline_version="1.0.0",
        created_at=now,
        updated_at=now,
        created_by="SPD Pipeline",
        current_stage=1,
        stages_completed=[],
        errors=[],
        warnings=[]
    )


def update_stage_completion(
    state: SPDState,
    stage: int,
    stage_key: str
) -> SPDState:
    """Mark a stage as complete and update metadata"""
    now = datetime.utcnow().isoformat()
    
    # Update completion flag
    state[f"{stage_key}_complete"] = True
    state[f"{stage_key}_timestamp"] = now
    
    # Update stage tracking
    if stage not in state.get("stages_completed", []):
        state["stages_completed"] = state.get("stages_completed", []) + [stage]
    
    state["current_stage"] = stage + 1
    state["updated_at"] = now
    
    return state


def get_stage_status(state: SPDState) -> Dict[str, bool]:
    """Get completion status for all stages"""
    return {
        "1_discovery": state.get("discovery_complete", False),
        "2_site_analysis": state.get("site_analysis_complete", False),
        "3_zoning_review": state.get("zoning_review_complete", False),
        "4_unit_config": state.get("unit_config_complete", False),
        "5_building_design": state.get("building_design_complete", False),
        "6_financial": state.get("financial_complete", False),
        "7_risk_assessment": state.get("risk_assessment_complete", False),
        "8_report": state.get("report_complete", False),
        "9_decision": state.get("decision_complete", False),
        "10_entitlement": state.get("entitlement_complete", False),
        "11_construction": state.get("construction_complete", False),
        "12_archive": state.get("archived", False)
    }
