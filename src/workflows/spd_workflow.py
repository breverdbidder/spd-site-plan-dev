"""
SPD Site Plan Development - LangGraph Workflow
==============================================
Main orchestration workflow for the 12-stage SPD pipeline.

This workflow coordinates all stages of site plan due diligence:
1. Discovery → 2. Site Analysis → 3. Zoning Review → 4. Parking/Unit →
5. Building Design → 6. Financial → 7. Risk Assessment → 8. Report →
9. Decision → 10. Entitlement → 11. Construction → 12. Archive
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from datetime import datetime
import json

# Import state schema
from src.state.spd_state import (
    SPDState, 
    create_initial_state, 
    update_stage_completion,
    get_stage_status
)

# Import calculators
from src.calculators.parking_unit_config import (
    ParkingUnitCalculator,
    SiteConstraints,
    ZoningDistrict,
    parking_unit_analysis_node
)


# =============================================================================
# STAGE 1: DISCOVERY NODE
# =============================================================================

def discovery_node(state: SPDState) -> SPDState:
    """
    Stage 1: Property discovery and initial data gathering.
    
    Inputs: property_id, address
    Outputs: parcel_id, owner_name, legal_description
    """
    # In production, this would fetch from BCPAO API
    # For now, pass through with placeholder data
    
    property_id = state.get("property_id", "")
    
    # TODO: Implement BCPAO scraper integration
    # For Bliss Palm Bay, hardcode known values
    if property_id == "2835546":
        state["parcel_id"] = "28-37-16-00-00018.0-0000.00"
        state["owner_name"] = "BLISS PROPERTIES LLC"
        state["legal_description"] = "LOT 18 SANDY PINES UNIT 1"
    
    return update_stage_completion(state, 1, "discovery")


# =============================================================================
# STAGE 2: SITE ANALYSIS NODE
# =============================================================================

def site_analysis_node(state: SPDState) -> SPDState:
    """
    Stage 2: Physical site constraints and measurements.
    
    Inputs: property_id
    Outputs: site_constraints dict, lot_acres, buildable_sf, building_envelope_sf
    """
    property_id = state.get("property_id", "")
    
    # TODO: Implement site data extraction from survey/BCPAO
    # For Bliss Palm Bay, use known values
    if property_id == "2835546":
        site_constraints = {
            "lot_sf": 46394,
            "lot_width": 167.5,
            "lot_depth": 277.0,
            "easement_sf": 0,
            "wellhead_sf": 22000,
            "front_setback": 25,
            "rear_setback": 25,
            "side_setback": 15,
            "max_lot_coverage": 0.60,
            "max_height_no_variance": 25
        }
        
        state["site_constraints"] = site_constraints
        state["lot_acres"] = site_constraints["lot_sf"] / 43560
        state["buildable_sf"] = site_constraints["lot_sf"] - site_constraints["wellhead_sf"]
        
        # Calculate building envelope
        usable_width = site_constraints["lot_width"] - (site_constraints["side_setback"] * 2)
        usable_depth = 156 - site_constraints["front_setback"] - site_constraints["rear_setback"]
        state["building_envelope_sf"] = usable_width * usable_depth
    
    return update_stage_completion(state, 2, "site_analysis")


# =============================================================================
# STAGE 3: ZONING REVIEW NODE
# =============================================================================

def zoning_review_node(state: SPDState) -> SPDState:
    """
    Stage 3: Zoning district analysis and requirements.
    
    Inputs: property_id, lot_acres
    Outputs: current_zoning, target_zoning, density_allowed, max_dwelling_units,
             rezoning_required, setbacks, etc.
    """
    property_id = state.get("property_id", "")
    lot_acres = state.get("lot_acres", 0)
    
    # TODO: Implement Palm Bay zoning lookup
    # For Bliss Palm Bay, use known values
    if property_id == "2835546":
        state["current_zoning"] = "RM_15"
        state["target_zoning"] = "RM_20"
        state["zoning_district"] = "RM_20"  # For calculations
        state["density_allowed"] = 20  # du/acre
        state["max_dwelling_units"] = int(lot_acres * 20)  # 21
        state["flu_designation"] = "HDR"  # High Density Residential
        state["flu_compatible"] = True
        state["rezoning_required"] = True
        state["rezoning_fee"] = 1200.0
        
        state["setbacks"] = {
            "front": 25,
            "rear": 25,
            "side": 15
        }
        state["max_height"] = 25
        state["max_lot_coverage"] = 0.60
    
    return update_stage_completion(state, 3, "zoning_review")


# =============================================================================
# STAGE 4: PARKING & UNIT CONFIGURATION NODE
# =============================================================================

def unit_config_node(state: SPDState) -> SPDState:
    """
    Stage 4: Parking requirements and unit configurations.
    
    Uses parking_unit_analysis_node from parking_unit_config.py
    
    Inputs: site_constraints, zoning_district, parking_available
    Outputs: parking_analysis, recommended_scenario, selected_scenario
    """
    # Set parking available if not set
    if "parking_available" not in state:
        state["parking_available"] = 42  # Default for Bliss
    
    # Call the parking/unit analysis node
    state = parking_unit_analysis_node(state)
    
    # Auto-select recommended scenario
    recommended = state.get("recommended_scenario", "Scenario B")
    scenarios = state.get("parking_analysis", {}).get("scenarios", [])
    
    for scenario in scenarios:
        if recommended in scenario.get("name", ""):
            state["selected_scenario"] = scenario
            break
    
    return update_stage_completion(state, 4, "unit_config")


# =============================================================================
# STAGE 5: BUILDING DESIGN NODE
# =============================================================================

def building_design_node(state: SPDState) -> SPDState:
    """
    Stage 5: Building specifications and layout.
    
    Inputs: selected_scenario
    Outputs: building_spec, variance_required, floor_plan
    """
    scenario = state.get("selected_scenario", {})
    building = scenario.get("building", {})
    
    state["building_spec"] = building
    state["variance_required"] = building.get("requires_variance", False)
    
    if state["variance_required"]:
        if building.get("height_ft", 0) > 25:
            state["variance_type"] = "HEIGHT"
            state["variance_justification"] = (
                f"Request {building.get('height_ft')}ft height with 25ft base setbacks. "
                "Precedent: Similar developments in Palm Bay have received height variances."
            )
    
    return update_stage_completion(state, 5, "building_design")


# =============================================================================
# STAGE 6: FINANCIAL PRO FORMA NODE
# =============================================================================

def financial_node(state: SPDState) -> SPDState:
    """
    Stage 6: Financial projections and returns.
    
    Inputs: selected_scenario
    Outputs: financial_projections, development_costs, returns
    """
    scenario = state.get("selected_scenario", {})
    financials = scenario.get("financials", {})
    building = scenario.get("building", {})
    
    state["rent_structure"] = scenario.get("rent", {})
    state["financial_projections"] = financials
    
    # Calculate development costs
    hard_costs = financials.get("construction_cost", 0)
    soft_costs = hard_costs * 0.15
    land_cost = 350000  # Estimate for Bliss
    ebike_cost = 25000 if scenario.get("parking", {}).get("tenants_without_parking", 0) > 30 else 15000
    total_dev_cost = hard_costs + soft_costs + land_cost + ebike_cost
    
    state["development_costs"] = {
        "hard_costs": hard_costs,
        "soft_costs": soft_costs,
        "land_cost": land_cost,
        "ebike_infrastructure": ebike_cost,
        "total": total_dev_cost
    }
    
    # Calculate returns
    noi = financials.get("noi", 0)
    value = financials.get("value_at_cap", 0)
    
    state["returns"] = {
        "noi": noi,
        "value": value,
        "equity_created": value - total_dev_cost,
        "cash_on_cash": (noi / total_dev_cost * 100) if total_dev_cost > 0 else 0
    }
    
    return update_stage_completion(state, 6, "financial")


# =============================================================================
# STAGE 7: RISK ASSESSMENT NODE
# =============================================================================

def risk_assessment_node(state: SPDState) -> SPDState:
    """
    Stage 7: Market and entitlement risk assessment.
    
    Inputs: parking_analysis, variance_required, rezoning_required
    Outputs: market_risk, entitlement_risk, overall_risk, risk_mitigation
    """
    scenario = state.get("selected_scenario", {})
    
    # Market risk based on parking ratio
    pct_no_parking = scenario.get("parking", {}).get("pct_without_parking", 0)
    
    if pct_no_parking <= 25:
        state["market_risk"] = "LOW"
        state["market_risk_factors"] = ["Strong parking ratio", "Easy lease-up expected"]
    elif pct_no_parking <= 40:
        state["market_risk"] = "MEDIUM"
        state["market_risk_factors"] = [
            f"{pct_no_parking:.0f}% tenants need to be car-free",
            "E-bike infrastructure required",
            "Target young professionals and remote workers"
        ]
    else:
        state["market_risk"] = "HIGH"
        state["market_risk_factors"] = [
            f"{pct_no_parking:.0f}% tenants need to be car-free",
            "Challenging in car-dependent Palm Bay",
            "Significant marketing effort required"
        ]
    
    # Entitlement risk
    entitlement_factors = []
    if state.get("rezoning_required"):
        entitlement_factors.append("Rezoning from RM-15 to RM-20 required")
    if state.get("variance_required"):
        entitlement_factors.append(f"Height variance required ({state.get('building_spec', {}).get('height_ft')}ft)")
    
    if len(entitlement_factors) >= 2:
        state["entitlement_risk"] = "MEDIUM"
    elif len(entitlement_factors) == 1:
        state["entitlement_risk"] = "LOW"
    else:
        state["entitlement_risk"] = "LOW"
    
    state["entitlement_risk_factors"] = entitlement_factors or ["No major entitlement hurdles"]
    
    # Overall risk
    risks = [state["market_risk"], state["entitlement_risk"]]
    if "HIGH" in risks:
        state["overall_risk"] = "HIGH"
    elif "MEDIUM" in risks:
        state["overall_risk"] = "MEDIUM"
    else:
        state["overall_risk"] = "LOW"
    
    # Mitigation strategies
    state["risk_mitigation"] = [
        "E-bike infrastructure for no-parking tenants",
        "Pre-application meeting to confirm City support",
        "$200/mo rent discount for no-parking units",
        "Target Space Coast aerospace workers (remote/hybrid)"
    ]
    
    return update_stage_completion(state, 7, "risk_assessment")


# =============================================================================
# STAGE 8: REPORT GENERATION NODE
# =============================================================================

def report_node(state: SPDState) -> SPDState:
    """
    Stage 8: Generate due diligence report.
    
    TODO: Integrate with docx skill for report generation
    """
    # Placeholder - would generate DOCX report
    state["report_format"] = "DOCX"
    state["report_sections"] = [
        "Executive Summary",
        "Site Analysis",
        "Zoning Review",
        "Unit Configuration",
        "Financial Pro Forma",
        "Risk Assessment",
        "Recommendation"
    ]
    
    return update_stage_completion(state, 8, "report")


# =============================================================================
# STAGE 9: DECISION NODE
# =============================================================================

def decision_node(state: SPDState) -> SPDState:
    """
    Stage 9: Final BID/REVIEW/SKIP decision.
    
    Decision criteria:
    - NOI > $250K/year
    - Cash-on-cash > 5%
    - Overall risk <= MEDIUM
    """
    returns = state.get("returns", {})
    overall_risk = state.get("overall_risk", "HIGH")
    
    noi = returns.get("noi", 0)
    coc = returns.get("cash_on_cash", 0)
    
    # Score calculation
    score = 0
    factors = []
    
    # NOI scoring (40 points max)
    if noi >= 400000:
        score += 40
        factors.append(f"Excellent NOI: ${noi:,.0f}")
    elif noi >= 300000:
        score += 30
        factors.append(f"Good NOI: ${noi:,.0f}")
    elif noi >= 200000:
        score += 20
        factors.append(f"Acceptable NOI: ${noi:,.0f}")
    else:
        score += 10
        factors.append(f"Low NOI: ${noi:,.0f}")
    
    # Cash-on-cash scoring (30 points max)
    if coc >= 8:
        score += 30
        factors.append(f"Strong CoC: {coc:.1f}%")
    elif coc >= 6:
        score += 20
        factors.append(f"Good CoC: {coc:.1f}%")
    elif coc >= 5:
        score += 15
        factors.append(f"Acceptable CoC: {coc:.1f}%")
    else:
        score += 5
        factors.append(f"Low CoC: {coc:.1f}%")
    
    # Risk scoring (30 points max)
    if overall_risk == "LOW":
        score += 30
        factors.append("Low overall risk")
    elif overall_risk == "MEDIUM":
        score += 20
        factors.append("Medium overall risk")
    else:
        score += 10
        factors.append("High overall risk - caution advised")
    
    state["decision_score"] = score
    state["decision_factors"] = factors
    
    # Decision
    if score >= 75:
        state["decision"] = "BID"
    elif score >= 50:
        state["decision"] = "REVIEW"
    else:
        state["decision"] = "SKIP"
    
    return update_stage_completion(state, 9, "decision")


# =============================================================================
# STAGE 10-12: PLACEHOLDER NODES
# =============================================================================

def entitlement_node(state: SPDState) -> SPDState:
    """Stage 10: Entitlement tracking (placeholder)"""
    state["entitlements"] = []
    state["rezoning_status"] = "PENDING"
    state["variance_status"] = "PENDING" if state.get("variance_required") else "N/A"
    return update_stage_completion(state, 10, "entitlement")


def construction_node(state: SPDState) -> SPDState:
    """Stage 11: Construction tracking (placeholder)"""
    state["construction_timeline"] = {}
    return update_stage_completion(state, 11, "construction")


def archive_node(state: SPDState) -> SPDState:
    """Stage 12: Archive to Supabase (placeholder)"""
    state["archived"] = True
    state["archive_timestamp"] = datetime.utcnow().isoformat()
    return state


# =============================================================================
# CONDITIONAL EDGES
# =============================================================================

def should_continue_to_decision(state: SPDState) -> Literal["decision", "end"]:
    """Check if we have enough data to make a decision"""
    if state.get("financial_complete") and state.get("risk_assessment_complete"):
        return "decision"
    return "end"


def route_after_decision(state: SPDState) -> Literal["entitlement", "archive"]:
    """Route based on decision"""
    decision = state.get("decision", "SKIP")
    if decision in ["BID", "REVIEW"]:
        return "entitlement"
    return "archive"


# =============================================================================
# BUILD GRAPH
# =============================================================================

def build_spd_graph() -> StateGraph:
    """Build the SPD LangGraph workflow"""
    
    # Create graph with SPDState
    graph = StateGraph(SPDState)
    
    # Add nodes
    graph.add_node("discovery", discovery_node)
    graph.add_node("site_analysis", site_analysis_node)
    graph.add_node("zoning_review", zoning_review_node)
    graph.add_node("unit_config", unit_config_node)
    graph.add_node("building_design", building_design_node)
    graph.add_node("financial", financial_node)
    graph.add_node("risk_assessment", risk_assessment_node)
    graph.add_node("report", report_node)
    graph.add_node("decision", decision_node)
    graph.add_node("entitlement", entitlement_node)
    graph.add_node("construction", construction_node)
    graph.add_node("archive", archive_node)
    
    # Add edges (linear flow for now)
    graph.add_edge("discovery", "site_analysis")
    graph.add_edge("site_analysis", "zoning_review")
    graph.add_edge("zoning_review", "unit_config")
    graph.add_edge("unit_config", "building_design")
    graph.add_edge("building_design", "financial")
    graph.add_edge("financial", "risk_assessment")
    graph.add_edge("risk_assessment", "report")
    graph.add_edge("report", "decision")
    
    # Conditional routing after decision
    graph.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "entitlement": "entitlement",
            "archive": "archive"
        }
    )
    
    graph.add_edge("entitlement", "construction")
    graph.add_edge("construction", "archive")
    graph.add_edge("archive", END)
    
    # Set entry point
    graph.set_entry_point("discovery")
    
    return graph


# =============================================================================
# RUN PIPELINE
# =============================================================================

def run_spd_pipeline(
    property_id: str,
    address: str,
    parking_available: int = 42
) -> SPDState:
    """
    Run the complete SPD pipeline for a property.
    
    Args:
        property_id: BCPAO account number
        address: Full property address
        parking_available: Number of parking spaces available
        
    Returns:
        Final SPDState with all analysis results
    """
    # Create initial state
    state = create_initial_state(property_id, address)
    state["parking_available"] = parking_available
    
    # Build and compile graph
    graph = build_spd_graph()
    app = graph.compile()
    
    # Run pipeline
    final_state = app.invoke(state)
    
    return final_state


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run for Bliss Palm Bay
    print("=" * 80)
    print("SPD PIPELINE - BLISS PALM BAY")
    print("=" * 80)
    
    final_state = run_spd_pipeline(
        property_id="2835546",
        address="2165 Sandy Pines Dr NE, Palm Bay, FL 32905",
        parking_available=42
    )
    
    # Print results
    print(f"\n📍 Property: {final_state['address']}")
    print(f"🏗️  Decision: {final_state.get('decision', 'PENDING')}")
    print(f"📊 Score: {final_state.get('decision_score', 0)}/100")
    
    print(f"\n📈 Financials:")
    returns = final_state.get("returns", {})
    print(f"   NOI: ${returns.get('noi', 0):,.0f}")
    print(f"   Value: ${returns.get('value', 0):,.0f}")
    print(f"   Cash-on-Cash: {returns.get('cash_on_cash', 0):.1f}%")
    
    print(f"\n🅿️  Parking Analysis:")
    scenario = final_state.get("selected_scenario", {})
    parking = scenario.get("parking", {})
    print(f"   Total Tenants: {scenario.get('total_tenants', 0)}")
    print(f"   With Parking: {parking.get('tenants_with_parking', 0)} ({parking.get('pct_with_parking', 0):.0f}%)")
    print(f"   No Parking: {parking.get('tenants_without_parking', 0)} ({parking.get('pct_without_parking', 0):.0f}%)")
    
    print(f"\n⚠️  Risk Assessment:")
    print(f"   Market Risk: {final_state.get('market_risk', 'N/A')}")
    print(f"   Entitlement Risk: {final_state.get('entitlement_risk', 'N/A')}")
    print(f"   Overall: {final_state.get('overall_risk', 'N/A')}")
    
    print(f"\n✅ Stages Completed: {final_state.get('stages_completed', [])}")
