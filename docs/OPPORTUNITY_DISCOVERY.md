# Zoning-FLU Opportunity Discovery System

## Overview

An Agentic AI orchestration system that identifies hidden real estate development opportunities by analyzing mismatches between current zoning and Future Land Use (FLU) designations.

**Core Insight:** When a property's current zoning is more restrictive than its FLU designation allows, a rezoning opportunity exists.

### Reference Case: Bliss Palm Bay
- **Address:** 2165 Sandy Pines Dr NE, Palm Bay, FL 32905
- **Original:** PUD zoning (effective 8 du/acre)
- **FLU:** HDR (allows up to 20 du/acre)
- **Opportunity:** Rezone to RM-20 → 21 units at 19.7 du/acre
- **Value Created:** Unlocked 13+ additional units through rezoning

## Architecture

### 7-Agent LangGraph Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OPPORTUNITY DISCOVERY PIPELINE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │    DATA      │───▶│   ZONING     │───▶│     FLU      │          │
│  │ ACQUISITION  │    │  ANALYSIS    │    │  ANALYSIS    │          │
│  │  (Agent 1)   │    │  (Agent 2)   │    │  (Agent 3)   │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                                       │                   │
│         │         ┌──────────────────────────────┘                  │
│         ▼         ▼                                                 │
│  ┌──────────────┐    ┌──────────────┐                              │
│  │  CONSTRAINT  │───▶│ OPPORTUNITY  │                              │
│  │   MAPPING    │    │   SCORING    │                              │
│  │  (Agent 4)   │    │  (Agent 5)   │                              │
│  └──────────────┘    └──────────────┘                              │
│                             │                                       │
│         ┌───────────────────┴───────────────────┐                  │
│         ▼                                       ▼                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   MARKET     │───▶│  REGULATORY  │───▶│    FINAL     │          │
│  │ VALIDATION   │    │   PATHWAY    │    │   REPORT     │          │
│  │  (Agent 6)   │    │  (Agent 7)   │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Purpose | Inputs | Outputs |
|-------|---------|--------|---------|
| **Data Acquisition** | Pull parcel data from BCPAO, GIS | Jurisdiction, FLU targets | Parcel records |
| **Zoning Analysis** | Parse zoning ordinances | Parcels | Density limits, setbacks |
| **FLU Analysis** | Interpret comp plan | Parcels | FLU max density |
| **Constraint Mapping** | Identify development constraints | Parcels | Buildable area % |
| **Opportunity Scoring** | Rank opportunities | Gaps, constraints | Scored rankings |
| **Market Validation** | Research comparable rezonings | Top opportunities | Approval probability |
| **Regulatory Pathway** | Map approval process | Top opportunities | Timeline, costs |

## Opportunity Scoring Model

### Scoring Components (100 points)

| Component | Weight | Scoring Logic |
|-----------|--------|---------------|
| **Density Gap** | 25% | Higher gap = more upside |
| **Lot Size** | 15% | Larger lots = more efficient |
| **Constraints** | 20% | Fewer constraints = better |
| **Market Demand** | 15% | Local rental demand |
| **Rezoning Probability** | 25% | Based on approval history |

### Grade Scale

| Grade | Score Range | Interpretation |
|-------|-------------|----------------|
| A+ | 90-100 | Immediate action - exceptional opportunity |
| A | 80-89 | Strong opportunity - pursue aggressively |
| B+ | 70-79 | Good opportunity - worth pursuing |
| B | 60-69 | Moderate opportunity - evaluate carefully |
| C | 50-59 | Marginal - significant constraints |
| D | 40-49 | Weak - major hurdles |
| F | <40 | Not viable - skip |

## Key Concepts

### Density Gap Calculation

```
Density Gap = FLU Max Density - Current Zoning Density

Example:
- Current Zoning: PUD (8 du/acre)
- FLU Designation: HDR (20 du/acre max)
- Density Gap: 12 du/acre
- On 1.065 acres: 12 extra units possible
```

### FLU vs Zoning Hierarchy

**Future Land Use (FLU):** Sets the MAXIMUM allowable intensity
- Established in Comprehensive Plan
- Harder to change (requires plan amendment)
- Represents community's long-term vision

**Zoning:** Must be CONSISTENT with FLU but can be MORE RESTRICTIVE
- Easier to change (rezoning application)
- Properties zoned below FLU max = opportunities
- Rezoning to FLU max is "by-right" request

### Common Florida Categories

| FLU | Max Density | Compatible Zonings |
|-----|-------------|-------------------|
| LDR | 1-4 du/acre | RS, RE |
| MDR | 5-10 du/acre | RM-6, RM-10 |
| HDR | 11-25 du/acre | RM-15, RM-20, RM-25 |
| MU | Varies | Mixed-use districts |

## Data Sources

### Primary Sources
- **BCPAO:** Brevard County Property Appraiser (parcel data)
- **Municipal GIS:** Zoning layers, FLU maps
- **Comprehensive Plans:** FLU designations, density tables

### Constraint Sources
- **FEMA NFHL:** Flood zones
- **SJRWMD:** Wetlands jurisdiction
- **Municipal Utilities:** Wellhead protection zones
- **Survey:** Easements, rights-of-way

## Usage

### Run via GitHub Actions

```yaml
# Trigger workflow manually
workflow_dispatch:
  inputs:
    jurisdiction: "Palm Bay"
    target_flu: "HDR,MDR"
    min_acreage: "0.5"
    max_parcels: "100"
```

### Run Locally

```python
from src.workflows.opportunity_discovery import run_opportunity_discovery

results = run_opportunity_discovery(
    jurisdiction="Palm Bay",
    target_flu_categories=["HDR", "MDR"],
    min_acreage=0.5,
    max_parcels=100
)

# Access results
print(f"Opportunities: {results['opportunities_identified']}")
for opp in results['top_opportunities'][:5]:
    print(f"- {opp['address']}: Grade {opp['score']['grade']}")
```

## Output Report Format

```json
{
  "parcel_id": "28-37-16-00-00018.0-0000.00",
  "address": "2165 Sandy Pines Dr NE",
  "owner": "BLISS PROPERTIES LLC",
  "acreage": 1.065,
  "current_zoning": "PUD",
  "flu_designation": "HDR",
  "density_gap": {
    "current_density": 8.0,
    "flu_density": 20.0,
    "gap_du_acre": 12.0,
    "additional_units": 13
  },
  "score": {
    "total_score": 72.5,
    "grade": "B+",
    "scoring_factors": [
      "Good density gap: 12 du/acre",
      "Good lot size: 1.07 acres"
    ],
    "red_flags": [
      "Significant constraints: 47% affected"
    ]
  },
  "buildable_pct": 52.6,
  "constraints": [
    {
      "type": "Wellhead Protection Easement",
      "impact": "47% of parcel encumbered",
      "resolution": "~10 years"
    }
  ]
}
```

## Edge Cases Handled

1. **Split Zoning:** Uses most restrictive or weighted average
2. **Unknown Zoning Codes:** Defaults to RS with warning
3. **PUD Properties:** Deed restrictions may override zoning
4. **Active Comp Plan Amendments:** Flagged as uncertain
5. **Recent Rezoning Denials:** Significantly reduces score
6. **High Constraint Areas (>60%):** May not be financially viable

## Integration with SPD Pipeline

This orchestration feeds into the main SPD (Site Plan Development) pipeline:

```
Opportunity Discovery → SPD Stage 1 (Discovery)
                     → SPD Stage 3 (Zoning Review)
                     → SPD Stage 4 (Site Constraints)
```

Properties identified with high scores are automatically queued for full SPD analysis.

## ROI Model

**Internal Value Created:**
- 1 extra deal per quarter identified: $50K
- 1 avoided loss (constrained property): $100K
- Time savings (automated analysis): $25K
- **Total Annual Value:** $300-400K

**Cost:** $3.3K/year (compute + Supabase)
**ROI:** ~100x

---

*Part of the SPD Site Plan Development Agentic AI ecosystem by Everest Capital USA*
