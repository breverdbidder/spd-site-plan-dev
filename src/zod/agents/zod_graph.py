"""
Zoning Opportunity Discovery (ZOD) - LangGraph Orchestration
Identifies hidden real estate development opportunities through zoning-to-FLU mismatch analysis.

Reference: Bliss Palm Bay (SPD-2025-001/002) - PUD zoned property in HDR FLU area
           = Rezoning opportunity to RM-20 (20 du/acre)
"""

from typing import TypedDict, Annotated, Sequence, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator
from datetime import datetime
from enum import Enum


class OpportunityGrade(str, Enum):
    """Opportunity scoring grades"""
    A_PLUS = "A+"   # 90-100: Exceptional opportunity
    A = "A"         # 80-89: Strong opportunity  
    B_PLUS = "B+"   # 70-79: Good opportunity
    B = "B"         # 60-69: Moderate opportunity
    C = "C"         # 50-59: Marginal opportunity
    D = "D"         # 40-49: Weak opportunity
    F = "F"         # <40: Not viable


class ZODState(TypedDict):
    """
    State object passed through the ZOD pipeline.
    Uses reducer pattern for list accumulation.
    """
    # Input parameters
    jurisdiction: str
    target_flu_categories: list[str]  # ["HDR", "MDR", "MXU"]
    min_parcel_acres: float
    max_parcels_to_analyze: int
    
    # Data acquisition results
    parcels_raw: Annotated[list[dict], operator.add]
    zoning_districts: dict[str, dict]  # code -> {max_density, use_types, overlays}
    flu_designations: dict[str, dict]  # category -> {density_range, permitted_zoning}
    
    # Analysis results
    parcels_analyzed: Annotated[list[dict], operator.add]
    constraint_maps: dict[str, dict]  # parcel_id -> constraints
    
    # Scored opportunities
    opportunities: Annotated[list[dict], operator.add]
    
    # Workflow control
    current_stage: str
    errors: Annotated[list[str], operator.add]
    checkpoints: Annotated[list[dict], operator.add]
    
    # Final outputs
    reports_generated: list[str]
    summary: Optional[dict]


# =============================================================================
# AGENT NODES
# =============================================================================

async def data_acquisition_agent(state: ZODState) -> dict:
    """
    Stage 1: Data Acquisition Agent
    
    Connects to:
    - Municipal GIS APIs (zoning shapefiles, FLU maps)
    - Property appraiser databases (BCPAO for Brevard)
    - Comprehensive plan documents
    
    Returns normalized parcel data with zoning and FLU attributes.
    """
    from src.integrations.gis_client import GISClient
    from src.integrations.bcpao_client import BCPAOClient
    
    jurisdiction = state["jurisdiction"]
    min_acres = state["min_parcel_acres"]
    target_flu = state["target_flu_categories"]
    
    # Initialize clients
    gis = GISClient(jurisdiction)
    bcpao = BCPAOClient()
    
    # Fetch zoning districts with density allowances
    zoning_districts = await gis.get_zoning_districts()
    
    # Fetch FLU designations from comprehensive plan
    flu_designations = await gis.get_flu_designations()
    
    # Query parcels in target FLU categories
    parcels = []
    for flu_category in target_flu:
        flu_parcels = await bcpao.query_parcels_by_flu(
            flu_category=flu_category,
            min_acres=min_acres,
            limit=state["max_parcels_to_analyze"] // len(target_flu)
        )
        parcels.extend(flu_parcels)
    
    checkpoint = {
        "stage": "data_acquisition",
        "timestamp": datetime.utcnow().isoformat(),
        "parcels_found": len(parcels),
        "jurisdiction": jurisdiction
    }
    
    return {
        "parcels_raw": parcels,
        "zoning_districts": zoning_districts,
        "flu_designations": flu_designations,
        "current_stage": "zoning_analysis",
        "checkpoints": [checkpoint]
    }


async def zoning_analysis_agent(state: ZODState) -> dict:
    """
    Stage 2: Zoning Analysis Agent
    
    Parses zoning ordinances to extract:
    - Maximum density per district (du/acre)
    - Permitted use types
    - Special overlay restrictions
    - Setback/height limits
    """
    from src.models.zoning_parser import ZoningParser
    
    parcels = state["parcels_raw"]
    districts = state["zoning_districts"]
    
    analyzed = []
    for parcel in parcels:
        current_zoning = parcel.get("zoning_code", "UNKNOWN")
        
        if current_zoning in districts:
            district_info = districts[current_zoning]
            parcel["zoning_analysis"] = {
                "current_zoning": current_zoning,
                "max_density": district_info.get("max_density_du_acre", 0),
                "permitted_uses": district_info.get("permitted_uses", []),
                "overlays": district_info.get("overlays", []),
                "setback_front_ft": district_info.get("setback_front", 25),
                "setback_side_ft": district_info.get("setback_side", 10),
                "setback_rear_ft": district_info.get("setback_rear", 20),
                "max_height_ft": district_info.get("max_height", 35),
                "max_lot_coverage_pct": district_info.get("lot_coverage", 50)
            }
        else:
            parcel["zoning_analysis"] = {
                "current_zoning": current_zoning,
                "max_density": 0,
                "error": f"Unknown zoning code: {current_zoning}"
            }
        
        analyzed.append(parcel)
    
    checkpoint = {
        "stage": "zoning_analysis",
        "timestamp": datetime.utcnow().isoformat(),
        "parcels_analyzed": len(analyzed)
    }
    
    return {
        "parcels_analyzed": analyzed,
        "current_stage": "flu_analysis",
        "checkpoints": [checkpoint]
    }


async def flu_analysis_agent(state: ZODState) -> dict:
    """
    Stage 3: Future Land Use Analysis Agent
    
    Interprets FLU categories from comprehensive plan:
    - Density ranges (min/max du/acre)
    - Permitted zoning districts
    - Calculates "density gap" = FLU max - Current zoning max
    """
    parcels = state["parcels_analyzed"]
    flu_defs = state["flu_designations"]
    
    for parcel in parcels:
        flu_code = parcel.get("flu_designation", "UNKNOWN")
        zoning_analysis = parcel.get("zoning_analysis", {})
        current_density = zoning_analysis.get("max_density", 0)
        
        if flu_code in flu_defs:
            flu_info = flu_defs[flu_code]
            flu_max_density = flu_info.get("max_density_du_acre", 0)
            
            # Calculate density gap (the opportunity)
            density_gap = flu_max_density - current_density
            
            parcel["flu_analysis"] = {
                "flu_designation": flu_code,
                "flu_description": flu_info.get("description", ""),
                "flu_max_density": flu_max_density,
                "flu_min_density": flu_info.get("min_density_du_acre", 0),
                "permitted_zoning_districts": flu_info.get("permitted_zoning", []),
                "density_gap": density_gap,
                "density_gap_pct": (density_gap / current_density * 100) if current_density > 0 else float('inf'),
                "has_opportunity": density_gap > 0
            }
        else:
            parcel["flu_analysis"] = {
                "flu_designation": flu_code,
                "density_gap": 0,
                "has_opportunity": False,
                "error": f"Unknown FLU code: {flu_code}"
            }
    
    # Filter to only parcels with opportunity
    opportunities = [p for p in parcels if p.get("flu_analysis", {}).get("has_opportunity", False)]
    
    checkpoint = {
        "stage": "flu_analysis",
        "timestamp": datetime.utcnow().isoformat(),
        "parcels_with_opportunity": len(opportunities),
        "total_analyzed": len(parcels)
    }
    
    return {
        "parcels_analyzed": [],  # Clear to avoid duplication
        "opportunities": opportunities,
        "current_stage": "constraint_mapping",
        "checkpoints": [checkpoint]
    }


async def constraint_mapping_agent(state: ZODState) -> dict:
    """
    Stage 4: Constraint Mapping Agent
    
    Overlays environmental and physical constraints:
    - Wetlands (NWI)
    - Flood zones (FEMA)
    - Wellhead protection areas
    - Easements and rights-of-way
    - Endangered species habitat
    
    Calculates net buildable area after constraint deductions.
    
    Reference: Bliss Palm Bay had 47% encumbered by 200-ft wellhead protection.
    """
    from src.integrations.constraint_client import ConstraintClient
    
    opportunities = state["opportunities"]
    constraint_client = ConstraintClient()
    constraint_maps = {}
    
    for parcel in opportunities:
        parcel_id = parcel.get("parcel_id", parcel.get("account_id"))
        parcel_acres = parcel.get("acres", 0)
        
        # Query constraint layers
        constraints = await constraint_client.get_constraints(parcel_id)
        
        # Calculate encumbered area
        wetland_acres = constraints.get("wetland_acres", 0)
        flood_zone_acres = constraints.get("flood_zone_acres", 0)
        easement_acres = constraints.get("easement_acres", 0)
        wellhead_acres = constraints.get("wellhead_protection_acres", 0)
        
        # Total encumbered (with overlap handling)
        total_encumbered = constraints.get("total_encumbered_acres", 
            min(parcel_acres, wetland_acres + flood_zone_acres + easement_acres + wellhead_acres))
        
        buildable_acres = max(0, parcel_acres - total_encumbered)
        buildable_pct = (buildable_acres / parcel_acres * 100) if parcel_acres > 0 else 0
        
        parcel["constraint_analysis"] = {
            "total_acres": parcel_acres,
            "wetland_acres": wetland_acres,
            "flood_zone_acres": flood_zone_acres,
            "easement_acres": easement_acres,
            "wellhead_protection_acres": wellhead_acres,
            "total_encumbered_acres": total_encumbered,
            "buildable_acres": buildable_acres,
            "buildable_pct": buildable_pct,
            "constraints_detail": constraints.get("details", []),
            "is_viable": buildable_pct >= 40  # <40% buildable = not financially viable
        }
        
        constraint_maps[parcel_id] = parcel["constraint_analysis"]
    
    # Filter to viable parcels
    viable_opportunities = [p for p in opportunities if p.get("constraint_analysis", {}).get("is_viable", False)]
    
    checkpoint = {
        "stage": "constraint_mapping",
        "timestamp": datetime.utcnow().isoformat(),
        "viable_parcels": len(viable_opportunities),
        "eliminated_by_constraints": len(opportunities) - len(viable_opportunities)
    }
    
    return {
        "constraint_maps": constraint_maps,
        "opportunities": [],  # Clear previous
        "parcels_analyzed": viable_opportunities,  # Pass forward viable ones
        "current_stage": "opportunity_scoring",
        "checkpoints": [checkpoint]
    }


async def opportunity_scoring_agent(state: ZODState) -> dict:
    """
    Stage 5: Opportunity Scoring Agent
    
    Synthesizes all inputs into opportunity score (0-100):
    
    Scoring Factors:
    - Density gap magnitude (30%): Higher gap = more upside
    - Lot size (15%): Larger lots = more absolute units
    - Buildable percentage (20%): Higher = fewer constraints
    - FLU alignment (15%): How well FLU supports target zoning
    - Market demand (10%): Based on area demographics
    - Rezoning probability (10%): Historical approval rates
    """
    parcels = state["parcels_analyzed"]
    
    scored_opportunities = []
    
    for parcel in parcels:
        flu = parcel.get("flu_analysis", {})
        constraints = parcel.get("constraint_analysis", {})
        zoning = parcel.get("zoning_analysis", {})
        
        # Extract key metrics
        density_gap = flu.get("density_gap", 0)
        flu_max = flu.get("flu_max_density", 0)
        buildable_acres = constraints.get("buildable_acres", 0)
        buildable_pct = constraints.get("buildable_pct", 0)
        total_acres = constraints.get("total_acres", 0)
        
        # Calculate potential units
        current_max_units = int(total_acres * zoning.get("max_density", 0))
        potential_max_units = int(buildable_acres * flu_max)
        unit_upside = potential_max_units - current_max_units
        
        # Scoring components (0-100 each, then weighted)
        density_gap_score = min(100, density_gap * 10)  # 10 du/ac gap = 100
        lot_size_score = min(100, total_acres * 20)  # 5+ acres = 100
        buildable_score = buildable_pct  # Direct percentage
        flu_alignment_score = 80 if flu.get("has_opportunity") else 20
        market_demand_score = 70  # TODO: Integrate Census API for demographics
        rezoning_probability_score = 65  # TODO: Historical approval analysis
        
        # Weighted final score
        score = (
            density_gap_score * 0.30 +
            lot_size_score * 0.15 +
            buildable_score * 0.20 +
            flu_alignment_score * 0.15 +
            market_demand_score * 0.10 +
            rezoning_probability_score * 0.10
        )
        
        # Assign grade
        if score >= 90:
            grade = OpportunityGrade.A_PLUS
        elif score >= 80:
            grade = OpportunityGrade.A
        elif score >= 70:
            grade = OpportunityGrade.B_PLUS
        elif score >= 60:
            grade = OpportunityGrade.B
        elif score >= 50:
            grade = OpportunityGrade.C
        elif score >= 40:
            grade = OpportunityGrade.D
        else:
            grade = OpportunityGrade.F
        
        parcel["opportunity_score"] = {
            "total_score": round(score, 1),
            "grade": grade.value,
            "components": {
                "density_gap_score": round(density_gap_score, 1),
                "lot_size_score": round(lot_size_score, 1),
                "buildable_score": round(buildable_pct, 1),
                "flu_alignment_score": flu_alignment_score,
                "market_demand_score": market_demand_score,
                "rezoning_probability_score": rezoning_probability_score
            },
            "unit_analysis": {
                "current_max_units": current_max_units,
                "potential_max_units": potential_max_units,
                "unit_upside": unit_upside
            }
        }
        
        scored_opportunities.append(parcel)
    
    # Sort by score descending
    scored_opportunities.sort(key=lambda x: x.get("opportunity_score", {}).get("total_score", 0), reverse=True)
    
    checkpoint = {
        "stage": "opportunity_scoring",
        "timestamp": datetime.utcnow().isoformat(),
        "total_scored": len(scored_opportunities),
        "grade_distribution": {
            grade.value: len([p for p in scored_opportunities 
                           if p.get("opportunity_score", {}).get("grade") == grade.value])
            for grade in OpportunityGrade
        }
    }
    
    return {
        "opportunities": scored_opportunities,
        "parcels_analyzed": [],
        "current_stage": "market_validation",
        "checkpoints": [checkpoint]
    }


async def market_validation_agent(state: ZODState) -> dict:
    """
    Stage 6: Market Validation Agent (Top 20% only)
    
    For high-scoring opportunities:
    - Research recent rezoning applications
    - Analyze approval rates for similar requests
    - Identify comparable developments
    - Assess neighborhood opposition risk
    """
    from src.integrations.rezoning_history import RezoningHistoryClient
    
    opportunities = state["opportunities"]
    
    # Only validate top 20%
    top_count = max(1, len(opportunities) // 5)
    top_opportunities = opportunities[:top_count]
    remaining = opportunities[top_count:]
    
    rezoning_client = RezoningHistoryClient()
    
    for parcel in top_opportunities:
        parcel_id = parcel.get("parcel_id", parcel.get("account_id"))
        target_zoning = parcel.get("flu_analysis", {}).get("permitted_zoning_districts", [])
        
        # Get rezoning history in area
        history = await rezoning_client.get_nearby_rezonings(
            parcel_id=parcel_id,
            radius_miles=2,
            years_back=5
        )
        
        # Calculate approval rate for similar requests
        similar_requests = [r for r in history if r.get("target_zoning") in target_zoning]
        approved = len([r for r in similar_requests if r.get("status") == "APPROVED"])
        approval_rate = (approved / len(similar_requests) * 100) if similar_requests else 50
        
        # Identify comparable developments
        comparables = await rezoning_client.get_comparable_developments(
            parcel_id=parcel_id,
            development_type="multifamily",
            radius_miles=3
        )
        
        parcel["market_validation"] = {
            "validated": True,
            "rezoning_history": {
                "total_nearby": len(history),
                "similar_requests": len(similar_requests),
                "approved": approved,
                "approval_rate_pct": round(approval_rate, 1)
            },
            "comparable_developments": len(comparables),
            "opposition_risk": "LOW" if approval_rate > 70 else ("MEDIUM" if approval_rate > 50 else "HIGH"),
            "validation_date": datetime.utcnow().isoformat()
        }
    
    # Mark remaining as not validated
    for parcel in remaining:
        parcel["market_validation"] = {
            "validated": False,
            "reason": "Below top 20% threshold for deep validation"
        }
    
    validated_opportunities = top_opportunities + remaining
    
    checkpoint = {
        "stage": "market_validation",
        "timestamp": datetime.utcnow().isoformat(),
        "validated_count": len(top_opportunities),
        "skipped_count": len(remaining)
    }
    
    return {
        "opportunities": [],
        "parcels_analyzed": validated_opportunities,
        "current_stage": "regulatory_pathway",
        "checkpoints": [checkpoint]
    }


async def regulatory_pathway_agent(state: ZODState) -> dict:
    """
    Stage 7: Regulatory Pathway Agent (Top 10% only)
    
    Creates detailed approval roadmap:
    - Required approvals (rezoning, variances, site plan, permits)
    - Timeline estimates
    - Cost estimates
    - Stakeholder identification (HOAs, utilities, neighbors)
    
    Reference: Bliss Palm Bay Section 6 regulatory pathway
    """
    parcels = state["parcels_analyzed"]
    
    # Only full pathway for top 10%
    top_count = max(1, len(parcels) // 10)
    top_parcels = parcels[:top_count]
    remaining = parcels[top_count:]
    
    for parcel in top_parcels:
        zoning = parcel.get("zoning_analysis", {})
        flu = parcel.get("flu_analysis", {})
        constraints = parcel.get("constraint_analysis", {})
        
        current_zoning = zoning.get("current_zoning", "")
        target_zoning = flu.get("permitted_zoning_districts", [])
        buildable_acres = constraints.get("buildable_acres", 0)
        potential_units = parcel.get("opportunity_score", {}).get("unit_analysis", {}).get("potential_max_units", 0)
        
        # Determine required approvals
        approvals_required = []
        timeline_months = 0
        estimated_costs = {}
        
        # Rezoning required if changing zoning
        if target_zoning and current_zoning not in target_zoning:
            approvals_required.append({
                "type": "Rezoning Application",
                "authority": "City/County Planning Board",
                "timeline_months": 4,
                "cost_estimate": 5000,
                "notes": f"From {current_zoning} to {target_zoning[0] if target_zoning else 'RM-20'}"
            })
            timeline_months += 4
            estimated_costs["rezoning"] = 5000
        
        # Site plan required for multifamily
        if potential_units > 4:
            approvals_required.append({
                "type": "Site Plan Approval",
                "authority": "Planning & Zoning",
                "timeline_months": 3,
                "cost_estimate": 3500,
                "notes": "Required for developments >4 units"
            })
            timeline_months += 3
            estimated_costs["site_plan"] = 3500
        
        # Traffic study if >50 units or high impact
        if potential_units > 50:
            approvals_required.append({
                "type": "Traffic Impact Study",
                "authority": "DOT / County Engineering",
                "timeline_months": 2,
                "cost_estimate": 8000,
                "notes": "Required for high-density developments"
            })
            timeline_months += 2
            estimated_costs["traffic_study"] = 8000
        
        # Environmental permits if constraints
        if constraints.get("wetland_acres", 0) > 0:
            approvals_required.append({
                "type": "Environmental Permit",
                "authority": "SJRWMD / DEP",
                "timeline_months": 6,
                "cost_estimate": 15000,
                "notes": "Wetland mitigation may be required"
            })
            timeline_months += 6
            estimated_costs["environmental"] = 15000
        
        # Building permits (standard)
        approvals_required.append({
            "type": "Building Permits",
            "authority": "Building Department",
            "timeline_months": 2,
            "cost_estimate": potential_units * 500,
            "notes": f"Estimated {potential_units} units × $500/unit"
        })
        timeline_months += 2
        estimated_costs["building_permits"] = potential_units * 500
        
        # Identify stakeholders
        stakeholders = [
            {"type": "City/County Planning", "role": "Primary approval authority"},
            {"type": "Utility Provider", "role": "Capacity confirmation"},
            {"type": "Adjacent Property Owners", "role": "Notice recipients"}
        ]
        
        if "PUD" in current_zoning:
            stakeholders.append({"type": "HOA (if applicable)", "role": "Deed restriction review"})
        
        parcel["regulatory_pathway"] = {
            "full_analysis": True,
            "approvals_required": approvals_required,
            "total_timeline_months": timeline_months,
            "estimated_total_cost": sum(estimated_costs.values()),
            "cost_breakdown": estimated_costs,
            "stakeholders": stakeholders,
            "risk_factors": [
                "Neighbor opposition" if parcel.get("market_validation", {}).get("opposition_risk") == "HIGH" else None,
                "Environmental constraints" if constraints.get("wetland_acres", 0) > 0 else None,
                "Traffic concerns" if potential_units > 50 else None
            ],
            "recommended_sequence": [a["type"] for a in approvals_required]
        }
        parcel["regulatory_pathway"]["risk_factors"] = [r for r in parcel["regulatory_pathway"]["risk_factors"] if r]
    
    # Simplified pathway for remaining
    for parcel in remaining:
        parcel["regulatory_pathway"] = {
            "full_analysis": False,
            "reason": "Below top 10% threshold for full regulatory analysis",
            "estimated_timeline_months": 6,
            "estimated_cost_range": "$15,000 - $50,000"
        }
    
    final_opportunities = top_parcels + remaining
    
    checkpoint = {
        "stage": "regulatory_pathway",
        "timestamp": datetime.utcnow().isoformat(),
        "full_analysis_count": len(top_parcels),
        "simplified_count": len(remaining)
    }
    
    return {
        "opportunities": final_opportunities,
        "parcels_analyzed": [],
        "current_stage": "report_generation",
        "checkpoints": [checkpoint]
    }


async def report_generation_agent(state: ZODState) -> dict:
    """
    Stage 8: Report Generation Agent
    
    Generates comprehensive reports for each opportunity:
    - Property identification
    - Zoning vs FLU analysis
    - Constraint summary
    - Opportunity score breakdown
    - Regulatory pathway
    - Recommendation
    """
    from src.reports.opportunity_report import generate_opportunity_report
    
    opportunities = state["opportunities"]
    reports_generated = []
    
    for parcel in opportunities:
        report_path = await generate_opportunity_report(parcel)
        reports_generated.append(report_path)
    
    # Generate summary
    grade_distribution = {}
    for parcel in opportunities:
        grade = parcel.get("opportunity_score", {}).get("grade", "F")
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
    
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "jurisdiction": state["jurisdiction"],
        "total_opportunities": len(opportunities),
        "grade_distribution": grade_distribution,
        "top_opportunity": opportunities[0] if opportunities else None,
        "total_unit_upside": sum(
            p.get("opportunity_score", {}).get("unit_analysis", {}).get("unit_upside", 0)
            for p in opportunities
        ),
        "average_score": round(
            sum(p.get("opportunity_score", {}).get("total_score", 0) for p in opportunities) / len(opportunities), 1
        ) if opportunities else 0
    }
    
    checkpoint = {
        "stage": "report_generation",
        "timestamp": datetime.utcnow().isoformat(),
        "reports_generated": len(reports_generated)
    }
    
    return {
        "reports_generated": reports_generated,
        "summary": summary,
        "current_stage": "complete",
        "checkpoints": [checkpoint]
    }


# =============================================================================
# CONDITIONAL EDGES
# =============================================================================

def should_continue_to_market_validation(state: ZODState) -> Literal["market_validation", "report_generation"]:
    """
    Skip market validation if no viable opportunities remain.
    """
    opportunities = state.get("opportunities", []) or state.get("parcels_analyzed", [])
    if not opportunities:
        return "report_generation"
    return "market_validation"


def should_continue_to_regulatory(state: ZODState) -> Literal["regulatory_pathway", "report_generation"]:
    """
    Skip regulatory pathway if no validated opportunities.
    """
    parcels = state.get("parcels_analyzed", [])
    validated = [p for p in parcels if p.get("market_validation", {}).get("validated", False)]
    if not validated:
        return "report_generation"
    return "regulatory_pathway"


# =============================================================================
# BUILD GRAPH
# =============================================================================

def build_zod_graph() -> StateGraph:
    """
    Builds the ZOD LangGraph orchestration graph.
    
    Flow:
    1. Data Acquisition → 2. Zoning Analysis → 3. FLU Analysis
    4. Constraint Mapping → 5. Opportunity Scoring
    6. Market Validation (top 20%) → 7. Regulatory Pathway (top 10%)
    8. Report Generation → END
    """
    graph = StateGraph(ZODState)
    
    # Add nodes
    graph.add_node("data_acquisition", data_acquisition_agent)
    graph.add_node("zoning_analysis", zoning_analysis_agent)
    graph.add_node("flu_analysis", flu_analysis_agent)
    graph.add_node("constraint_mapping", constraint_mapping_agent)
    graph.add_node("opportunity_scoring", opportunity_scoring_agent)
    graph.add_node("market_validation", market_validation_agent)
    graph.add_node("regulatory_pathway", regulatory_pathway_agent)
    graph.add_node("report_generation", report_generation_agent)
    
    # Add edges (sequential with conditional branches)
    graph.set_entry_point("data_acquisition")
    graph.add_edge("data_acquisition", "zoning_analysis")
    graph.add_edge("zoning_analysis", "flu_analysis")
    graph.add_edge("flu_analysis", "constraint_mapping")
    graph.add_edge("constraint_mapping", "opportunity_scoring")
    
    # Conditional: Skip market validation if no opportunities
    graph.add_conditional_edges(
        "opportunity_scoring",
        should_continue_to_market_validation,
        {
            "market_validation": "market_validation",
            "report_generation": "report_generation"
        }
    )
    
    # Conditional: Skip regulatory if no validated opportunities
    graph.add_conditional_edges(
        "market_validation",
        should_continue_to_regulatory,
        {
            "regulatory_pathway": "regulatory_pathway",
            "report_generation": "report_generation"
        }
    )
    
    graph.add_edge("regulatory_pathway", "report_generation")
    graph.add_edge("report_generation", END)
    
    return graph


def compile_zod_graph(checkpointer: bool = True):
    """
    Compile the ZOD graph with optional checkpointing.
    
    Args:
        checkpointer: Enable memory-based checkpointing for resume capability
    
    Returns:
        Compiled LangGraph ready for execution
    """
    graph = build_zod_graph()
    
    if checkpointer:
        memory = MemorySaver()
        return graph.compile(checkpointer=memory)
    
    return graph.compile()


# =============================================================================
# EXECUTION HELPER
# =============================================================================

async def run_zod_discovery(
    jurisdiction: str,
    target_flu_categories: list[str],
    min_parcel_acres: float = 0.5,
    max_parcels: int = 100
) -> dict:
    """
    Execute ZOD discovery for a jurisdiction.
    
    Args:
        jurisdiction: Target jurisdiction (e.g., "Palm Bay", "Brevard County")
        target_flu_categories: FLU categories to search (e.g., ["HDR", "MDR"])
        min_parcel_acres: Minimum parcel size to consider
        max_parcels: Maximum parcels to analyze
    
    Returns:
        Final state with all opportunities and reports
    
    Example:
        >>> results = await run_zod_discovery(
        ...     jurisdiction="Palm Bay",
        ...     target_flu_categories=["HDR", "MDR"],
        ...     min_parcel_acres=0.5,
        ...     max_parcels=50
        ... )
        >>> print(f"Found {len(results['opportunities'])} opportunities")
    """
    app = compile_zod_graph()
    
    initial_state = {
        "jurisdiction": jurisdiction,
        "target_flu_categories": target_flu_categories,
        "min_parcel_acres": min_parcel_acres,
        "max_parcels_to_analyze": max_parcels,
        "parcels_raw": [],
        "zoning_districts": {},
        "flu_designations": {},
        "parcels_analyzed": [],
        "constraint_maps": {},
        "opportunities": [],
        "current_stage": "initializing",
        "errors": [],
        "checkpoints": [],
        "reports_generated": [],
        "summary": None
    }
    
    config = {"configurable": {"thread_id": f"zod-{jurisdiction}-{datetime.utcnow().isoformat()}"}}
    
    final_state = await app.ainvoke(initial_state, config)
    
    return final_state


if __name__ == "__main__":
    import asyncio
    
    # Example: Discover opportunities in Palm Bay HDR areas
    async def main():
        results = await run_zod_discovery(
            jurisdiction="Palm Bay",
            target_flu_categories=["HDR", "MDR"],
            min_parcel_acres=0.5,
            max_parcels=20
        )
        
        print(f"\n{'='*60}")
        print("ZOD DISCOVERY COMPLETE")
        print(f"{'='*60}")
        print(f"Opportunities Found: {len(results.get('opportunities', []))}")
        print(f"Reports Generated: {len(results.get('reports_generated', []))}")
        
        if results.get('summary'):
            print(f"\nSummary:")
            print(f"  Total Unit Upside: {results['summary'].get('total_unit_upside', 0)}")
            print(f"  Average Score: {results['summary'].get('average_score', 0)}")
            print(f"  Grade Distribution: {results['summary'].get('grade_distribution', {})}")
    
    asyncio.run(main())
