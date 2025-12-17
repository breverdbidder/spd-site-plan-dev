"""
Zoning-FLU Opportunity Discovery - LangGraph Orchestration
==========================================================
Multi-agent system for identifying rezoning opportunities.

Agents:
1. Data Acquisition Agent   - GIS APIs, property appraiser databases
2. Zoning Analysis Agent    - Parse zoning ordinances, extract density
3. FLU Analysis Agent       - Interpret comprehensive plans
4. Constraint Mapping Agent - Environmental, easements, flood zones
5. Opportunity Scoring Agent - Calculate and rank opportunities
6. Market Validation Agent  - Research comparable rezonings
7. Regulatory Pathway Agent - Map approval requirements

Reference Case: Bliss Palm Bay
- Address: 2165 Sandy Pines Dr NE, Palm Bay, FL 32905
- Original: PUD zoning (8 du/acre effective)
- FLU: HDR (allows up to 20 du/acre)
- Opportunity: Rezone to RM-20 → 21 units at 19.7 du/acre
"""

from typing import Dict, Any, Literal, List
from langgraph.graph import StateGraph, END
from datetime import datetime
import json
import os

# Import state schema
from src.state.opportunity_state import (
    OpportunityState,
    create_initial_opportunity_state,
    ParcelData,
    ZoningData,
    FLUData,
    ConstraintData,
    DensityGap,
    RezoningHistory,
    OpportunityScore,
    RegulatoryPathway,
    calculate_density_gap,
    calculate_opportunity_score,
    FLU_DENSITY_MAX,
    ZONING_DENSITY,
    FLUCategory,
    ZoningCategory
)


# =============================================================================
# AGENT 1: DATA ACQUISITION
# =============================================================================

def data_acquisition_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 1: Pull parcel data from property appraiser and GIS.
    
    Data Sources:
    - BCPAO API (Brevard County Property Appraiser)
    - Municipal GIS (Palm Bay, Melbourne, etc.)
    - Parcel shapefiles
    
    Inputs: jurisdiction, target_flu_categories, min_acreage, max_parcels
    Outputs: parcels_raw, parcels, acquisition_timestamp
    """
    jurisdiction = state.get("jurisdiction", "Palm Bay")
    target_flu = state.get("target_flu_categories", ["HDR"])
    min_acreage = state.get("min_acreage", 0.5)
    max_parcels = state.get("max_parcels", 100)
    
    # In production: Query BCPAO API and GIS layers
    # For now, use Bliss Palm Bay as reference case
    
    parcels_raw = []
    
    # Reference case: Bliss Palm Bay
    if jurisdiction == "Palm Bay":
        parcels_raw.append({
            "parcel_id": "28-37-16-00-00018.0-0000.00",
            "account_number": "2835546",
            "address": "2165 Sandy Pines Dr NE",
            "city": "Palm Bay",
            "zip_code": "32905",
            "owner_name": "BLISS PROPERTIES LLC",
            "acreage": 1.065,
            "lot_sf": 46394,
            "assessed_value": 350000,
            "just_value": 375000,
            "legal_description": "LOT 18 SANDY PINES UNIT 1",
            "use_code": "0100",
            "use_description": "VACANT RESIDENTIAL",
            "flu_designation": "HDR",
            "current_zoning": "PUD"
        })
        
        # Additional sample parcels for demonstration
        # In production, these would come from API queries
        sample_parcels = [
            {
                "parcel_id": "28-37-16-00-00019.0-0000.00",
                "account_number": "2835547",
                "address": "2175 Sandy Pines Dr NE",
                "city": "Palm Bay",
                "zip_code": "32905",
                "owner_name": "SMITH JOHN",
                "acreage": 0.75,
                "lot_sf": 32670,
                "assessed_value": 225000,
                "just_value": 240000,
                "legal_description": "LOT 19 SANDY PINES UNIT 1",
                "use_code": "0100",
                "use_description": "VACANT RESIDENTIAL",
                "flu_designation": "HDR",
                "current_zoning": "RS"
            },
            {
                "parcel_id": "28-37-16-00-00020.0-0000.00",
                "account_number": "2835548",
                "address": "2185 Sandy Pines Dr NE",
                "city": "Palm Bay",
                "zip_code": "32905",
                "owner_name": "JONES MARY",
                "acreage": 1.25,
                "lot_sf": 54450,
                "assessed_value": 400000,
                "just_value": 425000,
                "legal_description": "LOT 20 SANDY PINES UNIT 1",
                "use_code": "0100",
                "use_description": "VACANT RESIDENTIAL",
                "flu_designation": "MDR",
                "current_zoning": "RS"
            }
        ]
        
        # Filter by FLU and acreage
        for parcel in sample_parcels:
            if (parcel.get("flu_designation") in target_flu and 
                parcel.get("acreage", 0) >= min_acreage):
                parcels_raw.append(parcel)
    
    # Convert to ParcelData objects
    parcels = []
    for p in parcels_raw[:max_parcels]:
        try:
            parcel = ParcelData(
                parcel_id=p["parcel_id"],
                account_number=p["account_number"],
                address=p["address"],
                city=p["city"],
                zip_code=p["zip_code"],
                owner_name=p["owner_name"],
                acreage=p["acreage"],
                lot_sf=p["lot_sf"],
                assessed_value=p["assessed_value"],
                just_value=p["just_value"],
                legal_description=p["legal_description"],
                use_code=p["use_code"],
                use_description=p["use_description"]
            )
            parcels.append(parcel)
        except Exception as e:
            state.setdefault("acquisition_errors", []).append(
                f"Error parsing parcel {p.get('parcel_id')}: {str(e)}"
            )
    
    # Update state
    state["parcels_raw"] = parcels_raw
    state["parcels"] = parcels
    state["acquisition_timestamp"] = datetime.utcnow().isoformat()
    state["acquisition_source"] = f"BCPAO API / {jurisdiction} GIS"
    state["current_stage"] = 2
    state["stages_completed"] = state.get("stages_completed", []) + [1]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# AGENT 2: ZONING ANALYSIS
# =============================================================================

def zoning_analysis_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 2: Parse zoning ordinances and extract restrictions.
    
    Inputs: parcels, parcels_raw
    Outputs: zoning_data (parcel_id -> ZoningData)
    """
    parcels_raw = state.get("parcels_raw", [])
    zoning_data = {}
    
    # Zoning ordinance lookup tables by jurisdiction
    # In production: Scrape from municipal code
    palm_bay_zoning = {
        "RS": ZoningData(
            district="RS",
            district_name="Single Family Residential",
            density_max=4.0,
            setbacks={"front": 25, "rear": 25, "side": 10},
            max_height=35,
            max_lot_coverage=0.50
        ),
        "RM-6": ZoningData(
            district="RM-6",
            district_name="Multi-Family Residential (6 du/acre)",
            density_max=6.0,
            setbacks={"front": 25, "rear": 25, "side": 10},
            max_height=35,
            max_lot_coverage=0.55
        ),
        "RM-10": ZoningData(
            district="RM-10",
            district_name="Multi-Family Residential (10 du/acre)",
            density_max=10.0,
            setbacks={"front": 25, "rear": 25, "side": 15},
            max_height=35,
            max_lot_coverage=0.55
        ),
        "RM-15": ZoningData(
            district="RM-15",
            district_name="Multi-Family Residential (15 du/acre)",
            density_max=15.0,
            setbacks={"front": 25, "rear": 25, "side": 15},
            max_height=35,
            max_lot_coverage=0.55
        ),
        "RM-20": ZoningData(
            district="RM-20",
            district_name="Multi-Family Residential (20 du/acre)",
            density_max=20.0,
            setbacks={"front": 25, "rear": 25, "side": 15},
            max_height=45,
            max_lot_coverage=0.60
        ),
        "PUD": ZoningData(
            district="PUD",
            district_name="Planned Unit Development",
            density_max=8.0,  # Default, varies by PUD
            setbacks={"front": 25, "rear": 25, "side": 15},
            max_height=35,
            max_lot_coverage=0.50,
            special_restrictions=["Density determined by approved PUD plan"]
        )
    }
    
    # Map parcels to zoning data
    for parcel in parcels_raw:
        parcel_id = parcel.get("parcel_id")
        current_zoning = parcel.get("current_zoning", "RS")
        
        # Normalize zoning code
        zoning_key = current_zoning.replace("-", "").replace("_", "-").upper()
        if zoning_key in ["RM6", "RM 6"]:
            zoning_key = "RM-6"
        elif zoning_key in ["RM10", "RM 10"]:
            zoning_key = "RM-10"
        elif zoning_key in ["RM15", "RM 15"]:
            zoning_key = "RM-15"
        elif zoning_key in ["RM20", "RM 20"]:
            zoning_key = "RM-20"
        
        if zoning_key in palm_bay_zoning:
            zoning_data[parcel_id] = palm_bay_zoning[zoning_key]
        else:
            # Default to RS if unknown
            zoning_data[parcel_id] = palm_bay_zoning["RS"]
            state.setdefault("warnings", []).append(
                f"Unknown zoning '{current_zoning}' for {parcel_id}, defaulting to RS"
            )
    
    # Update state
    state["zoning_data"] = zoning_data
    state["zoning_ordinance_url"] = "https://www.palmbayflorida.org/government/city-departments/growth-management/planning-zoning"
    state["zoning_analysis_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 3
    state["stages_completed"] = state.get("stages_completed", []) + [2]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# AGENT 3: FLU ANALYSIS
# =============================================================================

def flu_analysis_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 3: Interpret Future Land Use designations from comprehensive plan.
    
    Inputs: parcels_raw
    Outputs: flu_data (parcel_id -> FLUData), density_gaps
    """
    parcels_raw = state.get("parcels_raw", [])
    zoning_data = state.get("zoning_data", {})
    flu_data = {}
    density_gaps = {}
    
    # FLU designation lookup (Palm Bay Comprehensive Plan)
    flu_lookup = {
        "LDR": FLUData(
            designation="LDR",
            designation_name="Low Density Residential",
            density_max=4.0,
            compatible_zonings=["RS", "RE", "RU-1"],
            notes="1-4 dwelling units per acre"
        ),
        "MDR": FLUData(
            designation="MDR",
            designation_name="Medium Density Residential",
            density_max=10.0,
            compatible_zonings=["RS", "RM-6", "RM-10"],
            notes="5-10 dwelling units per acre"
        ),
        "HDR": FLUData(
            designation="HDR",
            designation_name="High Density Residential",
            density_max=20.0,  # Palm Bay HDR max
            compatible_zonings=["RM-10", "RM-15", "RM-20"],
            notes="11-20 dwelling units per acre"
        ),
        "MU": FLUData(
            designation="MU",
            designation_name="Mixed Use",
            density_max=20.0,
            intensity_max=1.5,
            compatible_zonings=["MU-1", "MU-2", "RM-20", "C-1"],
            notes="Mixed residential/commercial"
        )
    }
    
    total_additional_units = 0
    opportunities_count = 0
    
    for parcel in parcels_raw:
        parcel_id = parcel.get("parcel_id")
        flu_designation = parcel.get("flu_designation", "LDR")
        acreage = parcel.get("acreage", 0)
        
        # Get FLU data
        if flu_designation in flu_lookup:
            flu_data[parcel_id] = flu_lookup[flu_designation]
        else:
            flu_data[parcel_id] = flu_lookup["LDR"]
            state.setdefault("warnings", []).append(
                f"Unknown FLU '{flu_designation}' for {parcel_id}, defaulting to LDR"
            )
        
        # Calculate density gap if we have zoning data
        if parcel_id in zoning_data:
            zoning = zoning_data[parcel_id]
            flu = flu_data[parcel_id]
            
            gap = calculate_density_gap(zoning, flu, acreage)
            density_gaps[parcel_id] = gap
            
            # Count opportunities (gap > 0)
            if gap.gap_du_acre > 0:
                opportunities_count += 1
                total_additional_units += gap.additional_units
    
    # Update state
    state["flu_data"] = flu_data
    state["density_gaps"] = density_gaps
    state["opportunities_identified"] = opportunities_count
    state["total_additional_units"] = total_additional_units
    state["comp_plan_url"] = "https://www.palmbayflorida.org/government/city-departments/growth-management/planning-zoning/comprehensive-plan"
    state["flu_analysis_timestamp"] = datetime.utcnow().isoformat()
    state["density_gap_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 4
    state["stages_completed"] = state.get("stages_completed", []) + [3]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# AGENT 4: CONSTRAINT MAPPING
# =============================================================================

def constraint_mapping_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 4: Identify development constraints.
    
    Constraint Types:
    - Wellhead protection zones
    - Wetlands / SJRWMD jurisdiction
    - Flood zones (FEMA)
    - Easements
    - Conservation areas
    - Endangered species habitat
    
    Inputs: parcels
    Outputs: constraints, buildable_area, buildable_pct
    """
    parcels = state.get("parcels", [])
    parcels_raw = state.get("parcels_raw", [])
    constraints = {}
    buildable_area = {}
    buildable_pct = {}
    
    # Build lookup from raw data
    raw_lookup = {p.get("parcel_id"): p for p in parcels_raw}
    
    for parcel in parcels:
        parcel_id = parcel.parcel_id
        lot_sf = parcel.lot_sf
        parcel_constraints = []
        constrained_sf = 0
        
        # Check for known constraints
        # In production: Query GIS constraint layers
        
        # Reference case: Bliss Palm Bay wellhead
        if parcel_id == "28-37-16-00-00018.0-0000.00":
            wellhead = ConstraintData(
                constraint_type="Wellhead Protection Easement",
                impact_description="200-ft radius utility easement from existing well",
                area_affected_sf=22000,
                area_affected_pct=47.4,
                is_absolute=False,
                resolution_options=[
                    "Wait for well decommissioning (~10 years)",
                    "Design buildings outside easement",
                    "Parking/landscaping allowed in easement"
                ],
                resolution_timeline="~10 years for full use"
            )
            parcel_constraints.append(wellhead)
            constrained_sf += wellhead.area_affected_sf
        
        # Calculate buildable area
        net_buildable = max(0, lot_sf - constrained_sf)
        buildable_pct_value = (net_buildable / lot_sf * 100) if lot_sf > 0 else 0
        
        constraints[parcel_id] = parcel_constraints
        buildable_area[parcel_id] = net_buildable
        buildable_pct[parcel_id] = buildable_pct_value
    
    # Update state
    state["constraints"] = constraints
    state["buildable_area"] = buildable_area
    state["buildable_pct"] = buildable_pct
    state["constraint_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 5
    state["stages_completed"] = state.get("stages_completed", []) + [4]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# AGENT 5: OPPORTUNITY SCORING
# =============================================================================

def opportunity_scoring_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 5: Calculate and rank opportunities.
    
    Scoring Components (100 points):
    - Density Gap Score (25%): Higher gap = better
    - Lot Size Score (15%): Larger lots more efficient
    - Constraint Score (20%): Fewer constraints = better
    - Market Score (15%): Local demand factors
    - Rezoning Probability (25%): Based on approval history
    
    Inputs: density_gaps, buildable_pct, constraints, parcels
    Outputs: scores, ranked_parcels, top_opportunities
    """
    density_gaps = state.get("density_gaps", {})
    buildable_pct = state.get("buildable_pct", {})
    constraints = state.get("constraints", {})
    parcels = state.get("parcels", [])
    parcels_raw = state.get("parcels_raw", [])
    
    # Build lookup
    parcel_lookup = {p.parcel_id: p for p in parcels}
    raw_lookup = {p.get("parcel_id"): p for p in parcels_raw}
    
    scores = {}
    
    # Assume 70% approval rate (would come from market validation)
    approval_rate = 70.0
    
    for parcel_id, gap in density_gaps.items():
        if gap.gap_du_acre <= 0:
            continue  # Skip parcels with no opportunity
        
        parcel = parcel_lookup.get(parcel_id)
        if not parcel:
            continue
        
        acreage = parcel.acreage
        buildable = buildable_pct.get(parcel_id, 100)
        constraint_count = len(constraints.get(parcel_id, []))
        
        score = calculate_opportunity_score(
            density_gap=gap,
            acreage=acreage,
            buildable_pct=buildable,
            approval_rate=approval_rate,
            constraint_count=constraint_count
        )
        
        scores[parcel_id] = score
    
    # Rank by score
    ranked = sorted(scores.keys(), key=lambda x: scores[x].total_score, reverse=True)
    
    # Build top opportunities with full details
    top_opportunities = []
    for parcel_id in ranked[:10]:  # Top 10
        parcel = parcel_lookup.get(parcel_id)
        raw = raw_lookup.get(parcel_id, {})
        gap = density_gaps.get(parcel_id)
        score = scores.get(parcel_id)
        
        if parcel and gap and score:
            top_opportunities.append({
                "parcel_id": parcel_id,
                "address": parcel.address,
                "city": parcel.city,
                "owner": parcel.owner_name,
                "acreage": parcel.acreage,
                "current_zoning": raw.get("current_zoning", "Unknown"),
                "flu_designation": raw.get("flu_designation", "Unknown"),
                "density_gap": gap.to_dict(),
                "score": score.to_dict(),
                "buildable_pct": buildable_pct.get(parcel_id, 100),
                "constraints": [c.to_dict() for c in constraints.get(parcel_id, [])]
            })
    
    # Update state
    state["scores"] = scores
    state["ranked_parcels"] = ranked
    state["top_opportunities"] = top_opportunities
    state["scoring_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 6
    state["stages_completed"] = state.get("stages_completed", []) + [5]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# AGENT 6: MARKET VALIDATION
# =============================================================================

def market_validation_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 6: Research comparable rezonings and market demand.
    
    Inputs: top_opportunities, jurisdiction
    Outputs: rezoning_history, approval_rate, comparable_developments
    """
    jurisdiction = state.get("jurisdiction", "Palm Bay")
    
    # In production: Query planning department records
    # For now, use sample Palm Bay rezoning history
    
    rezoning_history = []
    
    if jurisdiction == "Palm Bay":
        # Recent Palm Bay rezonings (sample data)
        sample_rezonings = [
            RezoningHistory(
                case_number="REZ-2024-001",
                address="1500 Malabar Rd SE",
                from_zoning="RS",
                to_zoning="RM-15",
                flu_designation="HDR",
                density_requested=15.0,
                acreage=2.5,
                status="APPROVED",
                decision_date="2024-08-15",
                conditions=["Traffic study required", "Stormwater management plan"],
                vote_count="4-1"
            ),
            RezoningHistory(
                case_number="REZ-2024-002",
                address="2000 Palm Bay Rd NE",
                from_zoning="PUD",
                to_zoning="RM-20",
                flu_designation="HDR",
                density_requested=20.0,
                acreage=1.8,
                status="APPROVED",
                decision_date="2024-09-20",
                conditions=["Affordable housing commitment"],
                vote_count="5-0"
            ),
            RezoningHistory(
                case_number="REZ-2024-003",
                address="3200 Babcock St SE",
                from_zoning="RS",
                to_zoning="RM-10",
                flu_designation="MDR",
                density_requested=10.0,
                acreage=3.0,
                status="DENIED",
                decision_date="2024-10-10",
                conditions=[],
                vote_count="1-4"
            ),
            RezoningHistory(
                case_number="REZ-2023-015",
                address="1800 Jupiter Blvd SE",
                from_zoning="RS",
                to_zoning="RM-15",
                flu_designation="HDR",
                density_requested=15.0,
                acreage=1.5,
                status="APPROVED",
                decision_date="2023-11-12",
                conditions=["Buffer landscaping"],
                vote_count="3-2"
            )
        ]
        
        rezoning_history = sample_rezonings
    
    # Calculate approval rate
    approved = sum(1 for r in rezoning_history if r.status == "APPROVED")
    total = len(rezoning_history)
    approval_rate = (approved / total * 100) if total > 0 else 50.0
    
    # Comparable developments (would come from real estate data)
    comparable_developments = [
        {
            "name": "Palm Bay Village",
            "address": "1600 Palm Bay Rd NE",
            "units": 48,
            "density": 16.0,
            "year_built": 2022,
            "occupancy": 95,
            "avg_rent": 1650
        },
        {
            "name": "Harbor Point Apartments",
            "address": "2200 Malabar Rd SE",
            "units": 72,
            "density": 18.0,
            "year_built": 2023,
            "occupancy": 92,
            "avg_rent": 1750
        }
    ]
    
    # Market demand score (based on vacancy rates, rent growth)
    market_demand_score = 75.0  # Would come from market analysis
    
    # Update state
    state["rezoning_history"] = rezoning_history
    state["approval_rate"] = approval_rate
    state["comparable_developments"] = comparable_developments
    state["market_demand_score"] = market_demand_score
    state["market_validation_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 7
    state["stages_completed"] = state.get("stages_completed", []) + [6]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# AGENT 7: REGULATORY PATHWAY
# =============================================================================

def regulatory_pathway_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 7: Map approval requirements for top opportunities.
    
    Creates step-by-step approval roadmap including:
    - Pre-application meeting
    - Rezoning application
    - Site plan review
    - Building permits
    - Impact fee payments
    
    Inputs: top_opportunities, jurisdiction
    Outputs: pathways (parcel_id -> RegulatoryPathway)
    """
    top_opportunities = state.get("top_opportunities", [])
    jurisdiction = state.get("jurisdiction", "Palm Bay")
    pathways = {}
    
    # Palm Bay approval process template
    palm_bay_process = [
        {
            "step": 1,
            "name": "Pre-Application Meeting",
            "description": "Meet with Planning & Zoning to discuss project",
            "timeline_weeks": 2,
            "cost": 0,
            "required_documents": ["Conceptual site plan", "Project narrative"]
        },
        {
            "step": 2,
            "name": "Rezoning Application",
            "description": "Submit formal rezoning petition",
            "timeline_weeks": 8,
            "cost": 1200,
            "required_documents": ["Application form", "Survey", "Legal description", "Justification letter"]
        },
        {
            "step": 3,
            "name": "Planning Board Hearing",
            "description": "Present to Planning and Zoning Board",
            "timeline_weeks": 4,
            "cost": 0,
            "required_documents": ["Traffic study", "Stormwater analysis"]
        },
        {
            "step": 4,
            "name": "City Council Hearing",
            "description": "Final approval by City Council",
            "timeline_weeks": 4,
            "cost": 0,
            "required_documents": ["Updated plans per Planning Board conditions"]
        },
        {
            "step": 5,
            "name": "Site Plan Review",
            "description": "Submit detailed site development plan",
            "timeline_weeks": 6,
            "cost": 2500,
            "required_documents": ["Full site plan", "Engineering drawings", "Landscape plan"]
        },
        {
            "step": 6,
            "name": "Building Permit",
            "description": "Submit construction documents for permit",
            "timeline_weeks": 4,
            "cost": 5000,  # Varies by project size
            "required_documents": ["Architectural drawings", "Structural", "MEP", "Energy calcs"]
        }
    ]
    
    for opp in top_opportunities[:5]:  # Top 5 only
        parcel_id = opp.get("parcel_id")
        
        # Customize pathway based on constraints
        steps = palm_bay_process.copy()
        
        # Add variance step if needed (e.g., for height)
        # This would be determined by building design analysis
        
        total_weeks = sum(s["timeline_weeks"] for s in steps)
        total_cost = sum(s["cost"] for s in steps)
        
        pathway = RegulatoryPathway(
            steps=steps,
            total_timeline_months=total_weeks // 4,
            total_estimated_cost=total_cost,
            critical_path_items=[
                "Rezoning approval (8 weeks)",
                "Traffic study completion",
                "City Council vote"
            ],
            stakeholders=[
                "Palm Bay Planning & Zoning",
                "Palm Bay City Council",
                "SJRWMD (if wetlands)",
                "Palm Bay Utilities",
                "Adjacent property owners"
            ],
            risk_factors=[
                "Neighbor opposition at hearings",
                "Traffic study findings",
                "Stormwater requirements"
            ]
        )
        
        pathways[parcel_id] = pathway
    
    # Update state
    state["pathways"] = pathways
    state["pathway_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 8
    state["stages_completed"] = state.get("stages_completed", []) + [7]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# FINAL REPORT NODE
# =============================================================================

def final_report_node(state: OpportunityState) -> OpportunityState:
    """
    Generate final opportunity discovery report.
    """
    top_opportunities = state.get("top_opportunities", [])
    pathways = state.get("pathways", {})
    approval_rate = state.get("approval_rate", 0)
    
    # Build final report
    report = {
        "title": f"Zoning-FLU Opportunity Discovery Report",
        "jurisdiction": state.get("jurisdiction"),
        "generated_at": datetime.utcnow().isoformat(),
        "pipeline_id": state.get("pipeline_id"),
        "summary": {
            "parcels_analyzed": len(state.get("parcels", [])),
            "opportunities_identified": state.get("opportunities_identified", 0),
            "total_additional_units": state.get("total_additional_units", 0),
            "approval_rate": approval_rate
        },
        "top_opportunities": top_opportunities,
        "pathways": {k: v.to_dict() for k, v in pathways.items()},
        "rezoning_history": [r.to_dict() for r in state.get("rezoning_history", [])],
        "methodology": {
            "scoring_weights": {
                "density_gap": "25%",
                "lot_size": "15%",
                "constraints": "20%",
                "market": "15%",
                "rezoning_probability": "25%"
            },
            "data_sources": [
                "BCPAO Property Appraiser",
                "Palm Bay GIS",
                "Palm Bay Comprehensive Plan"
            ]
        }
    }
    
    state["final_report"] = report
    state["current_stage"] = 8
    state["stages_completed"] = state.get("stages_completed", []) + [8]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


# =============================================================================
# CONDITIONAL ROUTING
# =============================================================================

def should_run_market_validation(state: OpportunityState) -> Literal["market_validation", "skip_to_report"]:
    """Only run market validation if we have opportunities"""
    opportunities = state.get("opportunities_identified", 0)
    if opportunities > 0:
        return "market_validation"
    return "skip_to_report"


def should_run_regulatory(state: OpportunityState) -> Literal["regulatory", "skip_to_report"]:
    """Only run regulatory for top scored opportunities"""
    top = state.get("top_opportunities", [])
    if len(top) > 0 and top[0].get("score", {}).get("total_score", 0) >= 50:
        return "regulatory"
    return "skip_to_report"


def needs_human_review(state: OpportunityState) -> Literal["human_review", "continue"]:
    """Check if human review is needed before regulatory"""
    if state.get("human_review_required", False):
        return "human_review"
    return "continue"


# =============================================================================
# BUILD GRAPH
# =============================================================================

def build_opportunity_graph() -> StateGraph:
    """Build the Zoning-FLU Opportunity Discovery workflow"""
    
    graph = StateGraph(OpportunityState)
    
    # Add nodes
    graph.add_node("data_acquisition", data_acquisition_agent)
    graph.add_node("zoning_analysis", zoning_analysis_agent)
    graph.add_node("flu_analysis", flu_analysis_agent)
    graph.add_node("constraint_mapping", constraint_mapping_agent)
    graph.add_node("opportunity_scoring", opportunity_scoring_agent)
    graph.add_node("market_validation", market_validation_agent)
    graph.add_node("regulatory_pathway", regulatory_pathway_agent)
    graph.add_node("final_report", final_report_node)
    
    # Linear edges for core analysis
    graph.add_edge("data_acquisition", "zoning_analysis")
    graph.add_edge("zoning_analysis", "flu_analysis")
    graph.add_edge("flu_analysis", "constraint_mapping")
    graph.add_edge("constraint_mapping", "opportunity_scoring")
    
    # Conditional: Only run market validation if opportunities exist
    graph.add_conditional_edges(
        "opportunity_scoring",
        should_run_market_validation,
        {
            "market_validation": "market_validation",
            "skip_to_report": "final_report"
        }
    )
    
    # Conditional: Only run regulatory for high-scoring opportunities
    graph.add_conditional_edges(
        "market_validation",
        should_run_regulatory,
        {
            "regulatory": "regulatory_pathway",
            "skip_to_report": "final_report"
        }
    )
    
    graph.add_edge("regulatory_pathway", "final_report")
    graph.add_edge("final_report", END)
    
    # Set entry point
    graph.set_entry_point("data_acquisition")
    
    return graph


# =============================================================================
# RUN PIPELINE
# =============================================================================

def run_opportunity_discovery(
    jurisdiction: str = "Palm Bay",
    target_flu_categories: List[str] = None,
    min_acreage: float = 0.5,
    max_parcels: int = 100
) -> OpportunityState:
    """
    Run the complete opportunity discovery pipeline.
    
    Args:
        jurisdiction: Municipality to search
        target_flu_categories: FLU categories to target (default: HDR, MDR)
        min_acreage: Minimum lot size
        max_parcels: Maximum parcels to analyze
        
    Returns:
        Final OpportunityState with all analysis results
    """
    if target_flu_categories is None:
        target_flu_categories = ["HDR", "MDR"]
    
    # Create initial state
    state = create_initial_opportunity_state(
        jurisdiction=jurisdiction,
        target_flu_categories=target_flu_categories,
        min_acreage=min_acreage,
        max_parcels=max_parcels
    )
    
    # Build and compile graph
    graph = build_opportunity_graph()
    app = graph.compile()
    
    # Run pipeline
    final_state = app.invoke(state)
    
    return final_state


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ZONING-FLU OPPORTUNITY DISCOVERY")
    print("=" * 80)
    
    final_state = run_opportunity_discovery(
        jurisdiction="Palm Bay",
        target_flu_categories=["HDR", "MDR"],
        min_acreage=0.5,
        max_parcels=100
    )
    
    # Print results
    print(f"\n📍 Jurisdiction: {final_state['jurisdiction']}")
    print(f"📊 Parcels Analyzed: {len(final_state.get('parcels', []))}")
    print(f"🎯 Opportunities Found: {final_state.get('opportunities_identified', 0)}")
    print(f"🏠 Total Additional Units: {final_state.get('total_additional_units', 0)}")
    
    print("\n🏆 TOP OPPORTUNITIES:")
    print("-" * 60)
    for i, opp in enumerate(final_state.get("top_opportunities", [])[:5], 1):
        score = opp.get("score", {})
        gap = opp.get("density_gap", {})
        print(f"\n{i}. {opp.get('address')}")
        print(f"   Grade: {score.get('grade')} ({score.get('total_score', 0):.0f}/100)")
        print(f"   Current: {opp.get('current_zoning')} → FLU: {opp.get('flu_designation')}")
        print(f"   Density Gap: {gap.get('gap_du_acre', 0)} du/acre")
        print(f"   Additional Units: {gap.get('additional_units', 0)}")
        print(f"   Buildable: {opp.get('buildable_pct', 100):.0f}%")
    
    print(f"\n📈 Rezoning Approval Rate: {final_state.get('approval_rate', 0):.0f}%")
    
    print(f"\n✅ Stages Completed: {final_state.get('stages_completed', [])}")
