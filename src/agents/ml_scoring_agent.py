"""
ML-Enhanced Opportunity Scoring Agent
=====================================
Integrates XGBoost ML model into the ZOD LangGraph pipeline.

Replaces rule-based scoring with ML predictions:
- Rezoning approval probability
- Value uplift estimates
- Confidence scoring

Also integrates Census API demographics for market analysis.
"""

from typing import Dict, Any, List
from datetime import datetime
import asyncio

# Import ML model
from src.ml.zod_xgboost_model import (
    ZODXGBoostModel,
    ZODPrediction,
    integrate_ml_scoring
)

# Import API integrations
from src.integrations.api_integrations import (
    CensusAPIClient,
    EnhancedDataFetcher,
    enrich_opportunity_with_apis
)

# Import state
from src.state.opportunity_state import (
    OpportunityState,
    OpportunityScore,
    calculate_opportunity_score
)


def ml_opportunity_scoring_agent(state: OpportunityState) -> OpportunityState:
    """
    Stage 5 (Enhanced): ML-based opportunity scoring.
    
    Replaces rule-based scoring with XGBoost predictions.
    
    Inputs: density_gaps, buildable_pct, constraints, parcels
    Outputs: scores with ML predictions, ranked_parcels, top_opportunities
    """
    density_gaps = state.get("density_gaps", {})
    buildable_pct = state.get("buildable_pct", {})
    constraints = state.get("constraints", {})
    parcels = state.get("parcels", [])
    parcels_raw = state.get("parcels_raw", [])
    jurisdiction = state.get("jurisdiction", "Palm Bay")
    approval_rate = state.get("approval_rate", 70.0)
    
    # Initialize ML model
    ml_model = ZODXGBoostModel()
    
    # Build lookups
    parcel_lookup = {p.parcel_id: p for p in parcels}
    raw_lookup = {p.get("parcel_id"): p for p in parcels_raw}
    
    scores = {}
    ml_predictions = {}
    
    for parcel_id, gap in density_gaps.items():
        if gap.gap_du_acre <= 0:
            continue
        
        parcel = parcel_lookup.get(parcel_id)
        raw = raw_lookup.get(parcel_id, {})
        if not parcel:
            continue
        
        acreage = parcel.acreage
        buildable = buildable_pct.get(parcel_id, 100)
        parcel_constraints = constraints.get(parcel_id, [])
        constraint_types = [c.constraint_type for c in parcel_constraints]
        
        # Get ML prediction
        ml_pred = ml_model.predict(
            jurisdiction=jurisdiction,
            flu_designation=raw.get("flu_designation", "HDR"),
            current_zoning=raw.get("current_zoning", "RS"),
            density_gap=gap.gap_du_acre,
            acreage=acreage,
            buildable_pct=buildable,
            constraints=constraint_types,
            year_built=raw.get("year_built"),
            assessed_value=parcel.assessed_value,
            recent_approval_rate=approval_rate
        )
        
        ml_predictions[parcel_id] = ml_pred
        
        # Create combined score using ML + rule-based
        rule_score = calculate_opportunity_score(
            density_gap=gap,
            acreage=acreage,
            buildable_pct=buildable,
            approval_rate=approval_rate,
            constraint_count=len(parcel_constraints)
        )
        
        # Blend ML and rule-based scores (70% ML, 30% rule-based)
        ml_total = ml_pred.approval_probability * 100
        blended_total = (ml_total * 0.7) + (rule_score.total_score * 0.3)
        
        # Create enhanced score
        enhanced_score = OpportunityScore(
            total_score=blended_total,
            grade=ml_pred.grade,
            density_gap_score=rule_score.density_gap_score,
            lot_size_score=rule_score.lot_size_score,
            constraint_score=rule_score.constraint_score,
            market_score=rule_score.market_score,
            rezoning_probability=ml_pred.approval_probability * 100,
            scoring_factors=rule_score.scoring_factors + [
                f"ML Approval Probability: {ml_pred.approval_probability*100:.0f}%",
                f"ML Value Uplift: ${ml_pred.value_uplift_estimate:,.0f}"
            ],
            red_flags=rule_score.red_flags
        )
        
        scores[parcel_id] = enhanced_score
    
    # Rank by blended score
    ranked = sorted(scores.keys(), key=lambda x: scores[x].total_score, reverse=True)
    
    # Build top opportunities with ML data
    top_opportunities = []
    for parcel_id in ranked[:10]:
        parcel = parcel_lookup.get(parcel_id)
        raw = raw_lookup.get(parcel_id, {})
        gap = density_gaps.get(parcel_id)
        score = scores.get(parcel_id)
        ml_pred = ml_predictions.get(parcel_id)
        
        if parcel and gap and score and ml_pred:
            opp = {
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
                "constraints": [c.to_dict() for c in constraints.get(parcel_id, [])],
                # ML enhancements
                "ml_prediction": {
                    "approval_probability": ml_pred.approval_probability,
                    "value_uplift_estimate": ml_pred.value_uplift_estimate,
                    "confidence": ml_pred.confidence,
                    "grade": ml_pred.grade,
                    "features_used": ml_pred.features_used
                }
            }
            top_opportunities.append(opp)
    
    # Update state
    state["scores"] = scores
    state["ranked_parcels"] = ranked
    state["top_opportunities"] = top_opportunities
    state["ml_model_version"] = ml_model.model_version
    state["ml_enhanced"] = True
    state["scoring_timestamp"] = datetime.utcnow().isoformat()
    state["current_stage"] = 6
    state["stages_completed"] = state.get("stages_completed", []) + [5]
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


async def census_enrichment_agent(state: OpportunityState) -> OpportunityState:
    """
    Optional enrichment agent: Add Census demographics to opportunities.
    
    Adds to each opportunity:
    - Median income
    - Population
    - Vacancy rate
    - Affordability metrics
    """
    top_opportunities = state.get("top_opportunities", [])
    
    if not top_opportunities:
        return state
    
    census = CensusAPIClient()
    
    try:
        for opp in top_opportunities[:5]:  # Limit API calls
            address = f"{opp.get('address')}, {opp.get('city')}, FL"
            
            demographics = await census.get_demographics_by_address(address)
            
            if demographics:
                opp["census_demographics"] = demographics.to_dict()
                
                # Calculate market attractiveness
                median_income = demographics.median_income
                vacancy_rate = demographics.vacancy_rate
                
                market_score = 0
                if median_income >= 75000:
                    market_score += 40
                elif median_income >= 50000:
                    market_score += 25
                elif median_income >= 35000:
                    market_score += 10
                
                if vacancy_rate <= 5:
                    market_score += 30
                elif vacancy_rate <= 10:
                    market_score += 20
                elif vacancy_rate <= 15:
                    market_score += 10
                
                opp["census_market_score"] = market_score
    finally:
        await census.close()
    
    state["census_enriched"] = True
    state["updated_at"] = datetime.utcnow().isoformat()
    
    return state


def create_ml_enhanced_pipeline_node(state: OpportunityState) -> OpportunityState:
    """
    Combined ML + API enrichment node for LangGraph pipeline.
    
    Runs:
    1. ML-based opportunity scoring
    2. Census demographic enrichment (async)
    """
    # Run ML scoring (synchronous)
    state = ml_opportunity_scoring_agent(state)
    
    # Run Census enrichment (async)
    try:
        state = asyncio.run(census_enrichment_agent(state))
    except Exception as e:
        state.setdefault("warnings", []).append(f"Census enrichment failed: {e}")
    
    return state
