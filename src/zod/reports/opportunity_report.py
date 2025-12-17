"""
Opportunity Report Generator - Creates comprehensive reports for ZOD opportunities.

Output format matches SPD pipeline standards for consistency.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


async def generate_opportunity_report(parcel: dict, output_dir: str = "reports/zod") -> str:
    """
    Generate comprehensive opportunity report.
    
    Args:
        parcel: Analyzed parcel dict with all pipeline results
        output_dir: Directory for report output
    
    Returns:
        Path to generated report
    """
    # Extract data
    parcel_id = parcel.get("parcel_id", parcel.get("account_id", "unknown"))
    address = parcel.get("address", "Unknown")
    city = parcel.get("city", "")
    
    zoning = parcel.get("zoning_analysis", {})
    flu = parcel.get("flu_analysis", {})
    constraints = parcel.get("constraint_analysis", {})
    score = parcel.get("opportunity_score", {})
    market = parcel.get("market_validation", {})
    regulatory = parcel.get("regulatory_pathway", {})
    
    # Build report content
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "ZOD Opportunity Analysis",
            "version": "1.0",
            "pipeline": "SPD-ZOD"
        },
        
        "property_identification": {
            "parcel_id": parcel_id,
            "address": address,
            "city": city,
            "state": "FL",
            "owner": parcel.get("owner_name", "Unknown"),
            "total_acres": parcel.get("acres", 0),
            "legal_description": parcel.get("legal_description", "")
        },
        
        "opportunity_summary": {
            "total_score": score.get("total_score", 0),
            "grade": score.get("grade", "F"),
            "recommendation": _get_recommendation(score.get("total_score", 0)),
            "density_gap": flu.get("density_gap", 0),
            "unit_upside": score.get("unit_analysis", {}).get("unit_upside", 0)
        },
        
        "zoning_analysis": {
            "current_zoning": zoning.get("current_zoning", "Unknown"),
            "current_max_density": zoning.get("max_density", 0),
            "flu_designation": flu.get("flu_designation", "Unknown"),
            "flu_max_density": flu.get("flu_max_density", 0),
            "density_gap": flu.get("density_gap", 0),
            "density_gap_pct": flu.get("density_gap_pct", 0),
            "permitted_target_zoning": flu.get("permitted_zoning_districts", []),
            "analysis": _build_zoning_narrative(zoning, flu)
        },
        
        "constraint_analysis": {
            "total_acres": constraints.get("total_acres", 0),
            "buildable_acres": constraints.get("buildable_acres", 0),
            "buildable_pct": constraints.get("buildable_pct", 0),
            "wetland_acres": constraints.get("wetland_acres", 0),
            "flood_zone_acres": constraints.get("flood_zone_acres", 0),
            "wellhead_protection_acres": constraints.get("wellhead_protection_acres", 0),
            "easement_acres": constraints.get("easement_acres", 0),
            "is_viable": constraints.get("is_viable", True),
            "constraints_detail": constraints.get("constraints_detail", [])
        },
        
        "unit_potential": {
            "current_max_units": score.get("unit_analysis", {}).get("current_max_units", 0),
            "potential_max_units": score.get("unit_analysis", {}).get("potential_max_units", 0),
            "unit_upside": score.get("unit_analysis", {}).get("unit_upside", 0),
            "buildable_acres": constraints.get("buildable_acres", 0),
            "target_density": flu.get("flu_max_density", 0)
        },
        
        "score_breakdown": {
            "total_score": score.get("total_score", 0),
            "grade": score.get("grade", "F"),
            "components": score.get("components", {}),
            "scoring_methodology": "Weighted average: Density Gap (30%), Lot Size (15%), Buildable % (20%), FLU Alignment (15%), Market Demand (10%), Rezoning Probability (10%)"
        },
        
        "market_validation": {
            "validated": market.get("validated", False),
            "rezoning_history": market.get("rezoning_history", {}),
            "comparable_developments": market.get("comparable_developments", 0),
            "opposition_risk": market.get("opposition_risk", "UNKNOWN")
        },
        
        "regulatory_pathway": {
            "full_analysis": regulatory.get("full_analysis", False),
            "approvals_required": regulatory.get("approvals_required", []),
            "total_timeline_months": regulatory.get("total_timeline_months", 0),
            "estimated_total_cost": regulatory.get("estimated_total_cost", 0),
            "stakeholders": regulatory.get("stakeholders", []),
            "risk_factors": regulatory.get("risk_factors", [])
        },
        
        "next_steps": _generate_next_steps(score, flu, constraints, regulatory)
    }
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"ZOD_{parcel_id}_{timestamp}.json"
    filepath = output_path / filename
    
    # Write report
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Generated opportunity report: {filepath}")
    
    return str(filepath)


def _get_recommendation(score: float) -> str:
    """Get recommendation based on score."""
    if score >= 80:
        return "STRONG BUY - Exceptional opportunity with high probability of successful rezoning"
    elif score >= 70:
        return "BUY - Good opportunity with favorable rezoning prospects"
    elif score >= 60:
        return "EVALUATE - Moderate opportunity requiring additional due diligence"
    elif score >= 50:
        return "HOLD - Marginal opportunity with significant risks"
    else:
        return "PASS - Insufficient opportunity value for development risk"


def _build_zoning_narrative(zoning: dict, flu: dict) -> str:
    """Build narrative explanation of zoning opportunity."""
    current = zoning.get("current_zoning", "Unknown")
    current_density = zoning.get("max_density", 0)
    flu_code = flu.get("flu_designation", "Unknown")
    flu_max = flu.get("flu_max_density", 0)
    gap = flu.get("density_gap", 0)
    permitted = flu.get("permitted_zoning_districts", [])
    
    if gap <= 0:
        return f"No density upside. Current zoning ({current} at {current_density} du/ac) is at or above FLU ({flu_code}) maximum."
    
    narrative = f"""
Property is currently zoned {current} allowing {current_density} du/acre. 
The Future Land Use designation is {flu_code}, which permits up to {flu_max} du/acre.
This creates a density gap of {gap} du/acre ({gap/current_density*100:.0f}% upside) through rezoning.

Permitted zoning districts under {flu_code} FLU: {', '.join(permitted)}

Recommended target zoning: {permitted[-1] if permitted else 'RM-20'} to maximize development potential.
"""
    return narrative.strip()


def _generate_next_steps(
    score: dict,
    flu: dict,
    constraints: dict,
    regulatory: dict
) -> list[dict]:
    """Generate recommended next steps."""
    steps = []
    
    grade = score.get("grade", "F")
    
    if grade in ["A+", "A", "B+"]:
        steps.append({
            "priority": 1,
            "action": "Title Search",
            "description": "Conduct thorough title search to identify all encumbrances",
            "estimated_cost": "$350",
            "timeline": "3-5 days"
        })
        
        steps.append({
            "priority": 2,
            "action": "Pre-Application Meeting",
            "description": "Schedule pre-application meeting with Planning Department",
            "estimated_cost": "$0-500",
            "timeline": "2-4 weeks"
        })
        
        steps.append({
            "priority": 3,
            "action": "Site Survey",
            "description": "Commission boundary and topographic survey",
            "estimated_cost": "$3,000-5,000",
            "timeline": "2-3 weeks"
        })
    
    if constraints.get("wellhead_protection_acres", 0) > 0:
        steps.append({
            "priority": 2,
            "action": "Utility Coordination",
            "description": "Meet with utility department to discuss wellhead status and timeline",
            "estimated_cost": "$0",
            "timeline": "1-2 weeks"
        })
    
    if constraints.get("wetland_acres", 0) > 0:
        steps.append({
            "priority": 3,
            "action": "Environmental Assessment",
            "description": "Commission wetland delineation and Phase I environmental",
            "estimated_cost": "$5,000-15,000",
            "timeline": "4-6 weeks"
        })
    
    if grade in ["B", "C"]:
        steps.append({
            "priority": 1,
            "action": "Feasibility Study",
            "description": "Commission detailed financial feasibility analysis before proceeding",
            "estimated_cost": "$2,000-5,000",
            "timeline": "2-3 weeks"
        })
    
    # Sort by priority
    steps.sort(key=lambda x: x.get("priority", 99))
    
    return steps


async def generate_summary_report(
    opportunities: list[dict],
    jurisdiction: str,
    output_dir: str = "reports/zod"
) -> str:
    """
    Generate summary report for all opportunities.
    
    Args:
        opportunities: List of analyzed parcel dicts
        jurisdiction: Jurisdiction name
        output_dir: Output directory
    
    Returns:
        Path to summary report
    """
    # Grade distribution
    grades = {}
    for opp in opportunities:
        grade = opp.get("opportunity_score", {}).get("grade", "F")
        grades[grade] = grades.get(grade, 0) + 1
    
    # Total potential
    total_unit_upside = sum(
        opp.get("opportunity_score", {}).get("unit_analysis", {}).get("unit_upside", 0)
        for opp in opportunities
    )
    
    # Top opportunities
    top_5 = sorted(
        opportunities,
        key=lambda x: x.get("opportunity_score", {}).get("total_score", 0),
        reverse=True
    )[:5]
    
    summary = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "ZOD Summary Report",
            "jurisdiction": jurisdiction
        },
        
        "overview": {
            "total_opportunities": len(opportunities),
            "total_unit_upside": total_unit_upside,
            "average_score": round(
                sum(o.get("opportunity_score", {}).get("total_score", 0) for o in opportunities) / len(opportunities), 1
            ) if opportunities else 0
        },
        
        "grade_distribution": grades,
        
        "top_opportunities": [
            {
                "parcel_id": opp.get("parcel_id"),
                "address": opp.get("address"),
                "score": opp.get("opportunity_score", {}).get("total_score", 0),
                "grade": opp.get("opportunity_score", {}).get("grade", "F"),
                "density_gap": opp.get("flu_analysis", {}).get("density_gap", 0),
                "unit_upside": opp.get("opportunity_score", {}).get("unit_analysis", {}).get("unit_upside", 0)
            }
            for opp in top_5
        ],
        
        "recommendations": [
            "Focus on A/B+ opportunities first - highest probability of successful rezoning",
            "Schedule pre-application meetings for top 5 opportunities",
            "Commission title searches to identify unknown encumbrances",
            "Monitor comprehensive plan amendments that could affect FLU designations"
        ]
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"ZOD_Summary_{jurisdiction.replace(' ', '_')}_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Generated summary report: {filepath}")
    
    return str(filepath)
