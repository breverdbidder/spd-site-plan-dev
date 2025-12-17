# SPD Rough Diamond Pipeline

**Automated BCPAO parcel discovery and scoring for annexation arbitrage opportunities**

Part of BidDeed.AI / Everest Capital USA property acquisition platform.

## Overview

This pipeline identifies "rough diamond" properties in Brevard County, FL - specifically County AU/GU (Agricultural/General Use) parcels within 1 mile of West Melbourne and Palm Bay city limits that represent annexation arbitrage opportunities.

### XGBoost-Derived Scoring Model

Based on analysis of **109 Brevard County rezoning cases (2024-2025)** with a **77% approval rate**:

| Feature | Weight | Description |
|---------|--------|-------------|
| Jurisdiction | 28% | West Melbourne 91%, Palm Bay 80% |
| Zoning Transition | 22% | County→City = 92% success |
| Acreage | 18% | Sweet spot: 2-25 acres |
| Opposition Risk | 15% | HOA adjacency = -23% |
| Staff Recommendation | 12% | Staff support = 94% correlation |
| Comprehensive Plan | 5% | Pre-aligned = near-certain |

### Scoring Thresholds

- 🟢 **BID** (80-100): Immediate acquisition candidate
- 🟡 **REVIEW** (65-79): Conduct due diligence
- 🟠 **WATCH** (50-64): Monitor for changes
- 🔴 **SKIP** (<50): Does not match criteria

## Quick Start

```bash
# Clone repository
git clone https://github.com/breverdbidder/spd-site-plan-dev.git
cd spd-site-plan-dev

# Run full pipeline
python main.py

# Scrape only
python main.py --scrape-only -o data/bcpao_raw.json

# Score existing file
python main.py --score-only data/bcpao_raw.json -o data/scored.json
```

## Project Structure

```
spd-rough-diamond/
├── main.py                    # CLI entry point
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── src/
│   ├── scrapers/
│   │   └── bcpao_scraper.py   # BCPAO API integration
│   ├── models/
│   │   └── scoring_model.py   # XGBoost-derived scoring
│   ├── integrations/
│   │   └── supabase_client.py # Database storage
│   └── agents/
│       └── pipeline_orchestrator.py  # LangGraph workflow
├── config/
├── data/                      # Output files
├── tests/
└── .github/
    └── workflows/
        └── rough_diamond_pipeline.yml  # Daily automation
```

## Pipeline Stages

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  SCRAPE │ -> │  SCORE  │ -> │ FILTER  │ -> │  STORE  │ -> │ REPORT  │
│  BCPAO  │    │ XGBoost │    │ BID/REV │    │Supabase │    │ Summary │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

1. **SCRAPE**: Fetch parcels from BCPAO API (unincorporated AG/vacant)
2. **SCORE**: Apply ML-derived scoring model
3. **FILTER**: Extract BID and REVIEW candidates
4. **STORE**: Save to Supabase for tracking
5. **REPORT**: Generate summary with top candidates

## Target Criteria

### Green Flags (Score Boosters)
- ✅ West Melbourne, Palm Bay, Titusville, Cocoa jurisdictions
- ✅ 2-25 acres (optimal: 5-15 acres)
- ✅ Arterial road frontage (Dairy, Ellis, Babcock, US-1)
- ✅ Adjacent to existing industrial/commercial
- ✅ County parcel adjacent to city limits
- ✅ Low value per acre (<$30K)

### Red Flags (Score Penalties)
- ❌ Adjacent to master-planned HOA community
- ❌ Beach/barrier island location
- ❌ School capacity shortfall
- ❌ Prior failed rezoning attempt
- ❌ Environmental constraints (wetlands, scrub jay)

## Supabase Schema

```sql
-- Run in Supabase SQL Editor
CREATE TABLE rough_diamond_parcels (
    id BIGSERIAL PRIMARY KEY,
    account VARCHAR(20) UNIQUE NOT NULL,
    parcel_id VARCHAR(30),
    address TEXT,
    acres DECIMAL(10,2),
    taxing_district VARCHAR(100),
    land_use_code TEXT,
    market_value DECIMAL(15,2),
    owner TEXT,
    bcpao_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE parcel_scores (
    id BIGSERIAL PRIMARY KEY,
    account VARCHAR(20) REFERENCES rough_diamond_parcels(account),
    score INTEGER NOT NULL,
    recommendation VARCHAR(20),
    risk_level VARCHAR(20),
    timeline VARCHAR(20),
    scoring_factors JSONB,
    scored_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE search_runs (
    id BIGSERIAL PRIMARY KEY,
    run_type VARCHAR(50),
    total_found INTEGER,
    bid_count INTEGER,
    review_count INTEGER,
    parameters JSONB,
    run_at TIMESTAMPTZ DEFAULT NOW()
);
```

## GitHub Actions Automation

The pipeline runs daily at 6 AM EST via GitHub Actions:

```yaml
on:
  schedule:
    - cron: '0 11 * * *'  # 6 AM EST = 11 AM UTC
```

Required secrets:
- `SUPABASE_SERVICE_KEY`: Supabase service role key

## Environment Variables

```bash
# Required for database storage
export SUPABASE_SERVICE_KEY="eyJ..."

# Optional
export SUPABASE_URL="https://mocerqjnksmhcjzxrewo.supabase.co"
```

## Target Zip Codes

| Zip | Area | Priority |
|-----|------|----------|
| 32904 | West Melbourne | 1 |
| 32934 | West Melbourne/Viera | 1 |
| 32905 | Palm Bay North | 1 |
| 32907 | Palm Bay Central | 1 |
| 32908 | Palm Bay West | 2 |
| 32909 | Palm Bay South | 2 |
| 32940 | Melbourne/Viera | 2 |

## Integration with BidDeed.AI

This pipeline feeds into the main BidDeed.AI 12-stage foreclosure analysis system:

1. **Discovery** ← Rough Diamond candidates added here
2. Scraping
3. Title Search
4. Lien Priority Analysis
5. Tax Certificates
6. Demographics
7. ML Score
8. Max Bid Calculation
9. Decision Log
10. Report Generation
11. Disposition Tracking
12. Archive

## License

Proprietary - Everest Capital USA

## Contact

- **Developer**: Ariel Shapira
- **Company**: Everest Capital USA
- **Platform**: BidDeed.AI
