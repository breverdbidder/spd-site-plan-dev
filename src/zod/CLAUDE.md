# SPD-ZOD: Zoning Opportunity Discovery

> **Everest Capital USA** | Agentic AI Module for Hidden Development Opportunities
> Part of SPD (Site Plan Development) Pipeline

## Overview

ZOD is a multi-agent LangGraph orchestration system that identifies hidden real estate development opportunities through **zoning-to-FLU mismatch analysis**. 

### The Core Insight

Properties are often zoned more restrictively than their Future Land Use (FLU) designation permits. This creates **rezoning opportunities** where developers can unlock higher density development with reasonable approval probability.

**Reference Case: Bliss Palm Bay (SPD-2025-001)**
- Original: PUD zoning (single-family)
- FLU: HDR (High Density Residential) - allows up to 20 du/acre
- Opportunity: Rezone to RM-20 for 21-unit micro-unit workforce housing
- Constraint: 47% encumbered by 200-ft wellhead protection easement

## Build & Test Commands

```bash
# Run discovery pipeline
python -m src.agents.run_zod \
    --jurisdiction "Palm Bay" \
    --flu-categories "HDR,MDR" \
    --min-acres 0.5 \
    --max-parcels 50

# Run tests
python -m pytest tests/ -v

# Format code
python -m black src/ --check
python -m flake8 src/
```

## Architecture

### 8-Stage LangGraph Pipeline

```
Stage 1: Data Acquisition     → GIS + BCPAO data collection
Stage 2: Zoning Analysis      → Parse zoning district rules
Stage 3: FLU Analysis         → Calculate density gap opportunity
Stage 4: Constraint Mapping   → Overlay environmental/physical constraints
Stage 5: Opportunity Scoring  → Weighted scoring (0-100 scale)
Stage 6: Market Validation    → Rezoning history analysis (top 20%)
Stage 7: Regulatory Pathway   → Approval roadmap (top 10%)
Stage 8: Report Generation    → JSON/DOCX reports
```

### Agent Responsibilities

| Agent | Purpose |
|-------|---------|
| Data Acquisition | GIS APIs, BCPAO, parcel data |
| Zoning Analysis | District rules, density limits |
| FLU Analysis | Comprehensive plan interpretation |
| Constraint Mapping | Wetlands, flood, wellhead, easements |
| Opportunity Scoring | Weighted algorithm, A-F grading |
| Market Validation | Historical rezoning approval rates |
| Regulatory Pathway | Approval sequence, timeline, costs |
| Report Generation | Summary and detailed reports |

### Scoring Algorithm

```
Total Score = 
    Density Gap (30%) +
    Lot Size (15%) +
    Buildable % (20%) +
    FLU Alignment (15%) +
    Market Demand (10%) +
    Rezoning Probability (10%)

Grades:
A+: 90-100 | A: 80-89 | B+: 70-79 | B: 60-69 | C: 50-59 | D: 40-49 | F: <40
```

## Directory Structure

```
spd-zod/
├── src/
│   ├── agents/
│   │   ├── zod_graph.py       # Main LangGraph orchestration
│   │   └── run_zod.py         # CLI runner
│   ├── models/
│   │   └── state_models.py    # Pydantic models, jurisdiction defs
│   ├── integrations/
│   │   ├── gis_client.py      # Municipal GIS APIs
│   │   ├── bcpao_client.py    # Brevard County Property Appraiser
│   │   ├── constraint_client.py # Environmental constraints
│   │   └── rezoning_history.py  # Market validation
│   └── reports/
│       └── opportunity_report.py # Report generation
├── .github/workflows/
│   └── zod_pipeline.yml       # Automated weekly runs
├── data/
│   └── jurisdictions/         # Cached jurisdiction definitions
├── tests/
└── reports/                   # Generated reports
```

## Key Concepts

### Density Gap

The difference between FLU-permitted maximum density and current zoning maximum:

```
Density Gap = FLU Max Density - Current Zoning Max Density

Example (Bliss Palm Bay):
  Current: PUD → ~4 du/acre (based on original plat)
  FLU HDR: 20 du/acre maximum
  Gap: 16 du/acre potential upside
```

### Constraint Viability Threshold

Properties with <40% buildable area (after constraint deductions) are flagged as non-viable due to financial infeasibility.

### FLU Consistency

Rezoning requests consistent with FLU have ~30% higher approval probability than those requiring comprehensive plan amendments.

## Integration with SPD Pipeline

ZOD feeds into the broader SPD 12-stage pipeline:

```
ZOD Discovery → SPD Stage 1 (Discovery)
                         ↓
              SPD Stages 2-12 (Full Site Plan Analysis)
```

High-scoring ZOD opportunities become SPD project candidates.

## External Services

| Service | Purpose | Config |
|---------|---------|--------|
| Supabase | Database, logging | SUPABASE_URL, SUPABASE_KEY |
| BCPAO | Brevard parcel data | Public API |
| GIS | Zoning/FLU layers | Municipal endpoints |
| FEMA | Flood zones | Public API |
| NWI | Wetlands | USFWS API |

## Project Rules

### NEVER
- Guess FLU designations (always verify with GIS)
- Assume constraints without overlay analysis
- Skip wellhead protection check in Palm Bay
- Provide legal advice on rezoning

### ALWAYS
- Calculate density gap from verified sources
- Check constraint layers before scoring
- Log all decisions to Supabase insights
- Update PROJECT_STATE.json for SPD integration
- Document assumptions in reports

## Example Usage

```python
from src.agents.zod_graph import run_zod_discovery

# Run discovery
results = await run_zod_discovery(
    jurisdiction="Palm Bay",
    target_flu_categories=["HDR", "MDR"],
    min_parcel_acres=0.5,
    max_parcels=50
)

# Access opportunities
for opp in results["opportunities"]:
    score = opp["opportunity_score"]
    print(f"{opp['address']}: Grade {score['grade']}, Score {score['total_score']}")
```

## Brevard County FLU Reference

| FLU Code | Description | Max Density | Permitted Zoning |
|----------|-------------|-------------|------------------|
| LDR | Low Density Residential | 4 du/ac | RS-1, RS-2, RS-4 |
| MDR | Medium Density Residential | 10 du/ac | RS-4, RM-6, RM-10 |
| HDR | High Density Residential | 20 du/ac | RM-10, RM-15, RM-20 |
| MXU | Mixed Use | 25 du/ac | RM-15, RM-20, BU-1, BU-2 |

## Changelog

### v1.0.0 (Dec 2025)
- Initial release
- 8-agent LangGraph orchestration
- Palm Bay and Brevard County jurisdiction support
- GitHub Actions automation
- Bliss Palm Bay reference implementation
