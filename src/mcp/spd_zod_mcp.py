"""
SPD/ZOD MCP Server - Site Plan Development & Zoning Opportunity Discovery
==========================================================================
Version: 1.0.0
Created: December 16, 2025

Exposes the SPD/ZOD ecosystem as MCP tools for Agentic AI:
- Opportunity Discovery (7-agent LangGraph)
- XGBoost ML Predictions
- Site Plan Analysis
- Regulatory Pathway Mapping
- Feasibility Scoring

This MCP server integrates with:
- BidDeed.AI MCP Server (foreclosure auctions)
- Life OS (productivity tracking)
- Smart Router (LLM orchestration)
"""

import asyncio
import json
import os
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from contextlib import asynccontextmanager

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # Fallback for environments without MCP
    FastMCP = None
    
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# CONFIGURATION
# =============================================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "breverdbidder/spd-site-plan-dev"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mocerqjnksmhcjzxrewo.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# =============================================================================
# ENUMS
# =============================================================================

class JurisdictionType(str, Enum):
    PALM_BAY = "Palm Bay"
    MELBOURNE = "Melbourne"
    BREVARD_COUNTY = "Brevard County"
    COCOA = "Cocoa"
    TITUSVILLE = "Titusville"


class FLUCategory(str, Enum):
    LDR = "LDR"
    MDR = "MDR"
    HDR = "HDR"
    MU = "MU"


class ZoningDistrict(str, Enum):
    RS = "RS"
    RM_6 = "RM-6"
    RM_10 = "RM-10"
    RM_15 = "RM-15"
    RM_20 = "RM-20"
    RM_25 = "RM-25"
    PUD = "PUD"
    MU = "MU"


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


# =============================================================================
# INPUT MODELS
# =============================================================================

class DiscoverOpportunitiesInput(BaseModel):
    """Input for opportunity discovery pipeline."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    jurisdiction: JurisdictionType = Field(
        default=JurisdictionType.PALM_BAY,
        description="Municipality to search for opportunities"
    )
    target_flu: List[FLUCategory] = Field(
        default=[FLUCategory.HDR, FLUCategory.MDR],
        description="FLU categories to target (Higher density = more opportunity)"
    )
    min_acreage: float = Field(
        default=0.5,
        ge=0.1,
        le=100.0,
        description="Minimum lot size in acres"
    )
    max_parcels: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Maximum parcels to analyze"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Output format: markdown or json"
    )


class PredictRezoningInput(BaseModel):
    """Input for rezoning approval prediction."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    jurisdiction: JurisdictionType = Field(
        ...,
        description="City/county for the rezoning"
    )
    current_zoning: ZoningDistrict = Field(
        ...,
        description="Current zoning district"
    )
    target_zoning: ZoningDistrict = Field(
        ...,
        description="Requested zoning district"
    )
    flu_designation: FLUCategory = Field(
        ...,
        description="Future Land Use designation"
    )
    acreage: float = Field(
        ...,
        ge=0.1,
        le=100.0,
        description="Lot size in acres"
    )
    buildable_pct: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Percentage of lot that is buildable (after constraints)"
    )
    neighbor_opposition_risk: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Estimated neighbor opposition (0=none, 1=certain)"
    )


class ScoreFeasibilityInput(BaseModel):
    """Input for development feasibility scoring."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    jurisdiction: JurisdictionType = Field(..., description="Municipality")
    current_zoning: ZoningDistrict = Field(..., description="Current zoning")
    target_zoning: ZoningDistrict = Field(..., description="Target zoning")
    flu_designation: FLUCategory = Field(..., description="FLU designation")
    acreage: float = Field(..., ge=0.1, description="Lot size in acres")
    zip_code: str = Field(default="", description="5-digit zip code")
    buildable_pct: float = Field(default=100.0, description="Buildable percentage")
    constraint_count: int = Field(default=0, ge=0, description="Number of site constraints")
    market_vacancy_rate: float = Field(default=0.07, description="Local rental vacancy rate")
    avg_rent_per_sqft: float = Field(default=1.50, description="Average rent per sqft")


class AnalyzeParcelInput(BaseModel):
    """Input for single parcel analysis."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    parcel_id: Optional[str] = Field(default=None, description="Parcel ID")
    address: Optional[str] = Field(default=None, description="Property address")
    account_number: Optional[str] = Field(default=None, description="BCPAO account number")
    output_format: OutputFormat = Field(default=OutputFormat.MARKDOWN)


class GetRegulatoryPathwayInput(BaseModel):
    """Input for regulatory pathway mapping."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    jurisdiction: JurisdictionType = Field(..., description="Municipality")
    current_zoning: ZoningDistrict = Field(..., description="Current zoning")
    target_zoning: ZoningDistrict = Field(..., description="Target zoning")
    requires_variance: bool = Field(default=False, description="Variance needed?")
    requires_site_plan: bool = Field(default=True, description="Site plan review needed?")


# =============================================================================
# MCP SERVER INITIALIZATION
# =============================================================================

if FastMCP:
    @asynccontextmanager
    async def app_lifespan():
        """Initialize HTTP client and configuration."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield {
                "http_client": client,
                "github_headers": {
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json"
                }
            }

    mcp = FastMCP("spd_zod_mcp", lifespan=app_lifespan)
else:
    mcp = None


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

async def discover_opportunities_impl(
    jurisdiction: str,
    target_flu: List[str],
    min_acreage: float,
    max_parcels: int,
    output_format: str
) -> str:
    """Run the opportunity discovery pipeline."""
    try:
        # Import the workflow
        from src.workflows.opportunity_discovery import run_opportunity_discovery
        
        # Run pipeline
        results = run_opportunity_discovery(
            jurisdiction=jurisdiction,
            target_flu_categories=target_flu,
            min_acreage=min_acreage,
            max_parcels=max_parcels
        )
        
        if output_format == "json":
            return json.dumps(results.get("final_report", {}), indent=2)
        
        # Format as markdown
        top_opps = results.get("top_opportunities", [])
        
        md = f"""# 🎯 Zoning Opportunity Discovery Results

**Jurisdiction:** {jurisdiction}
**Target FLU:** {', '.join(target_flu)}
**Parcels Analyzed:** {len(results.get('parcels', []))}
**Opportunities Found:** {results.get('opportunities_identified', 0)}
**Additional Units Possible:** {results.get('total_additional_units', 0)}

## Top Opportunities

"""
        for i, opp in enumerate(top_opps[:10], 1):
            score = opp.get("score", {})
            gap = opp.get("density_gap", {})
            md += f"""### {i}. {opp.get('address')}

| Metric | Value |
|--------|-------|
| **Grade** | {score.get('grade')} ({score.get('total_score', 0):.0f}/100) |
| **Current Zoning** | {opp.get('current_zoning')} |
| **FLU Designation** | {opp.get('flu_designation')} |
| **Density Gap** | {gap.get('gap_du_acre', 0)} du/acre |
| **Additional Units** | {gap.get('additional_units', 0)} |
| **Buildable** | {opp.get('buildable_pct', 100):.0f}% |

"""
        return md
        
    except Exception as e:
        return f"Error running opportunity discovery: {str(e)}"


async def predict_rezoning_impl(
    jurisdiction: str,
    current_zoning: str,
    target_zoning: str,
    flu_designation: str,
    acreage: float,
    buildable_pct: float,
    neighbor_opposition_risk: float
) -> str:
    """Predict rezoning approval probability."""
    try:
        from src.ml.xgboost_models import predict_rezoning_approval
        
        result = predict_rezoning_approval(
            jurisdiction=jurisdiction,
            current_zoning=current_zoning,
            target_zoning=target_zoning,
            flu_designation=flu_designation,
            acreage=acreage,
            buildable_pct=buildable_pct,
            neighbor_opposition_risk=neighbor_opposition_risk
        )
        
        md = f"""# 🏛️ Rezoning Approval Prediction

**Grade:** {result.grade}
**Approval Probability:** {result.approval_probability*100:.1f}%
**Confidence:** {result.confidence*100:.0f}%

## Recommendation
{result.recommendation}

## Analysis Details

| Feature | Value |
|---------|-------|
| Jurisdiction | {jurisdiction} |
| Current Zoning | {current_zoning} |
| Target Zoning | {target_zoning} |
| FLU Designation | {flu_designation} |
| Lot Size | {acreage:.2f} acres |
| Buildable Area | {buildable_pct:.0f}% |
| Comparable Cases | {result.comparable_cases} |

"""
        if result.risk_factors:
            md += "## ⚠️ Risk Factors\n\n"
            for rf in result.risk_factors:
                md += f"- {rf}\n"
        
        return md
        
    except Exception as e:
        return f"Error predicting rezoning: {str(e)}"


async def score_feasibility_impl(
    jurisdiction: str,
    current_zoning: str,
    target_zoning: str,
    flu_designation: str,
    acreage: float,
    zip_code: str,
    buildable_pct: float,
    constraint_count: int,
    market_vacancy_rate: float,
    avg_rent_per_sqft: float
) -> str:
    """Score development feasibility."""
    try:
        from src.ml.xgboost_models import score_development_feasibility
        
        result = score_development_feasibility(
            jurisdiction=jurisdiction,
            current_zoning=current_zoning,
            target_zoning=target_zoning,
            flu_designation=flu_designation,
            acreage=acreage,
            zip_code=zip_code,
            buildable_pct=buildable_pct,
            constraint_count=constraint_count,
            market_vacancy_rate=market_vacancy_rate,
            avg_rent_per_sqft=avg_rent_per_sqft
        )
        
        md = f"""# 📊 Development Feasibility Score

**Total Score:** {result.total_score:.1f}/100
**Grade:** {result.grade}

## Recommendation
{result.recommendation}

## Component Scores

| Component | Score | Weight |
|-----------|-------|--------|
| Rezoning | {result.rezoning_score:.0f} | 25% |
| Market | {result.market_score:.0f} | 20% |
| Constraints | {result.constraint_score:.0f} | 20% |
| Financial | {result.financial_score:.0f} | 20% |
| Location | {result.location_score:.0f} | 15% |

"""
        if result.strengths:
            md += "## ✅ Strengths\n\n"
            for s in result.strengths:
                md += f"- {s}\n"
            md += "\n"
        
        if result.weaknesses:
            md += "## ⚠️ Weaknesses\n\n"
            for w in result.weaknesses:
                md += f"- {w}\n"
        
        return md
        
    except Exception as e:
        return f"Error scoring feasibility: {str(e)}"


async def get_regulatory_pathway_impl(
    jurisdiction: str,
    current_zoning: str,
    target_zoning: str,
    requires_variance: bool,
    requires_site_plan: bool
) -> str:
    """Get regulatory approval pathway."""
    
    # Palm Bay standard process
    steps = []
    total_cost = 0
    total_weeks = 0
    
    # Step 1: Pre-Application Meeting
    steps.append({
        "step": 1,
        "name": "Pre-Application Meeting",
        "description": "Meet with Planning & Zoning to discuss project",
        "weeks": 2,
        "cost": 0
    })
    total_weeks += 2
    
    # Step 2: Rezoning Application (if needed)
    if current_zoning != target_zoning:
        steps.append({
            "step": 2,
            "name": "Rezoning Application",
            "description": f"Submit rezoning petition ({current_zoning} → {target_zoning})",
            "weeks": 8,
            "cost": 1200
        })
        total_weeks += 8
        total_cost += 1200
        
        # Planning Board
        steps.append({
            "step": 3,
            "name": "Planning Board Hearing",
            "description": "Present to Planning and Zoning Board",
            "weeks": 4,
            "cost": 0
        })
        total_weeks += 4
        
        # City Council
        steps.append({
            "step": 4,
            "name": "City Council Hearing",
            "description": "Final approval by City Council",
            "weeks": 4,
            "cost": 0
        })
        total_weeks += 4
    
    # Variance (if needed)
    if requires_variance:
        steps.append({
            "step": len(steps) + 1,
            "name": "Variance Application",
            "description": "Submit variance petition with justification",
            "weeks": 6,
            "cost": 800
        })
        total_weeks += 6
        total_cost += 800
    
    # Site Plan Review
    if requires_site_plan:
        steps.append({
            "step": len(steps) + 1,
            "name": "Site Plan Review",
            "description": "Submit detailed site development plan",
            "weeks": 6,
            "cost": 2500
        })
        total_weeks += 6
        total_cost += 2500
    
    # Building Permit
    steps.append({
        "step": len(steps) + 1,
        "name": "Building Permit",
        "description": "Submit construction documents",
        "weeks": 4,
        "cost": 5000
    })
    total_weeks += 4
    total_cost += 5000
    
    md = f"""# 📋 Regulatory Approval Pathway

**Jurisdiction:** {jurisdiction}
**Total Timeline:** ~{total_weeks} weeks ({total_weeks // 4} months)
**Estimated Costs:** ${total_cost:,}

## Approval Steps

| Step | Name | Duration | Cost |
|------|------|----------|------|
"""
    for step in steps:
        md += f"| {step['step']} | {step['name']} | {step['weeks']} weeks | ${step['cost']:,} |\n"
    
    md += f"""
## Critical Path Items

1. Rezoning approval ({jurisdiction} City Council)
2. Traffic study completion (if required)
3. Stormwater management plan approval

## Stakeholders

- {jurisdiction} Planning & Zoning Department
- {jurisdiction} City Council
- SJRWMD (if wetlands present)
- Adjacent property owners
- Utility providers

## Tips for Success

1. **Pre-Application Meeting**: Get buy-in early
2. **Traffic Study**: Commission proactively if >50 units
3. **Neighbor Outreach**: Meet with adjacent owners before public hearing
4. **Professional Team**: Hire local land use attorney
"""
    
    return md


# =============================================================================
# REGISTER MCP TOOLS
# =============================================================================

if mcp:
    @mcp.tool()
    async def discover_opportunities(input: DiscoverOpportunitiesInput) -> str:
        """
        Discover rezoning opportunities in a jurisdiction.
        
        Runs the 7-agent LangGraph pipeline to find properties where
        current zoning underutilizes FLU maximum density.
        """
        return await discover_opportunities_impl(
            jurisdiction=input.jurisdiction.value,
            target_flu=[f.value for f in input.target_flu],
            min_acreage=input.min_acreage,
            max_parcels=input.max_parcels,
            output_format=input.output_format.value
        )
    
    @mcp.tool()
    async def predict_rezoning_approval(input: PredictRezoningInput) -> str:
        """
        Predict probability of rezoning approval using XGBoost ML model.
        
        Based on 2020-2024 Brevard County rezoning decision data.
        Accuracy: ~72%
        """
        return await predict_rezoning_impl(
            jurisdiction=input.jurisdiction.value,
            current_zoning=input.current_zoning.value,
            target_zoning=input.target_zoning.value,
            flu_designation=input.flu_designation.value,
            acreage=input.acreage,
            buildable_pct=input.buildable_pct,
            neighbor_opposition_risk=input.neighbor_opposition_risk
        )
    
    @mcp.tool()
    async def score_development_feasibility(input: ScoreFeasibilityInput) -> str:
        """
        Calculate comprehensive development feasibility score.
        
        Combines rezoning probability, market conditions, constraints,
        financial potential, and location into a 0-100 score with grade.
        """
        return await score_feasibility_impl(
            jurisdiction=input.jurisdiction.value,
            current_zoning=input.current_zoning.value,
            target_zoning=input.target_zoning.value,
            flu_designation=input.flu_designation.value,
            acreage=input.acreage,
            zip_code=input.zip_code,
            buildable_pct=input.buildable_pct,
            constraint_count=input.constraint_count,
            market_vacancy_rate=input.market_vacancy_rate,
            avg_rent_per_sqft=input.avg_rent_per_sqft
        )
    
    @mcp.tool()
    async def get_regulatory_pathway(input: GetRegulatoryPathwayInput) -> str:
        """
        Get step-by-step regulatory approval pathway for development.
        
        Returns timeline, costs, and tips for successful approval.
        """
        return await get_regulatory_pathway_impl(
            jurisdiction=input.jurisdiction.value,
            current_zoning=input.current_zoning.value,
            target_zoning=input.target_zoning.value,
            requires_variance=input.requires_variance,
            requires_site_plan=input.requires_site_plan
        )
    
    @mcp.tool()
    async def get_spd_status() -> str:
        """
        Get current status of SPD projects and pipeline.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/PROJECT_STATE.json",
                    timeout=30.0
                )
                if response.status_code == 200:
                    state = response.json()
                    projects = state.get("projects", [])
                    
                    md = "# 📊 SPD Project Status\n\n"
                    
                    for project in projects:
                        status_emoji = "✅" if project.get("status") == "COMPLETED" else "🔄"
                        md += f"""## {status_emoji} {project.get('name')}

**Address:** {project.get('address')}, {project.get('city')}, {project.get('state')}
**Status:** {project.get('status')}
**ML Score:** {project.get('ml_score', 'N/A')} ({project.get('ml_grade', 'N/A')})
**Recommendation:** {project.get('recommendation', 'N/A')}

"""
                    return md
                return "Error fetching project state"
        except Exception as e:
            return f"Error: {str(e)}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run MCP server."""
    if mcp:
        mcp.run()
    else:
        print("MCP not available. Run with: pip install mcp")


if __name__ == "__main__":
    main()
