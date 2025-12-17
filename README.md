# SPD Rough Diamond Pipeline

**Automated BCPAO parcel discovery for annexation arbitrage opportunities**

Part of the BidDeed.AI / Everest Capital USA property acquisition system.

## Overview

This pipeline identifies "rough diamond" properties in Brevard County, Florida - parcels with high rezoning/annexation potential based on XGBoost-derived scoring patterns from 109 historical rezoning cases (77% approval rate).

### Target Properties
- **County AU/GU parcels** within 1 mile of West Melbourne/Palm Bay city limits
- **Agricultural/Vacant land** in unincorporated areas
- **2-100 acres** optimal size range
- **Low value per acre** indicating arbitrage potential

## Scoring Model

Based on XGBoost analysis of 109 Brevard County rezoning cases:

| Feature | Weight | Description |
|---------|--------|-------------|
| Jurisdiction | 28% | West Melbourne (95) > Palm Bay (85) > Unincorp (70) |
| Zoning Match | 22% | AG→Industrial (89) > AG→Residential (85) |
| Acreage | 18% | Sweet spot: 2-10 acres (95), 10-25 acres (85) |
| Opposition Risk | 15% | Value/acre proxy: <$15K (95), $15-30K (85) |
| Staff Rec | 12% | Historical correlation with approval |
| Comp Plan | 5% | Future land use alignment |

### Recommendation Thresholds
- **🟢 BID (80+)**: Immediate acquisition candidate
- **🟡 REVIEW (65-79)**: Due diligence required
- **🟠 WATCH (50-64)**: Monitor for changes
- **🔴 SKIP (<50)**: Does not match criteria

## Usage

```bash
python main.py                              # Full pipeline
python main.py --scrape-only -o data.json   # Scrape only
python main.py --score-only data.json       # Score existing file
python main.py --dry-run                    # No database storage
```

## GitHub Actions

Daily automated runs at 6 AM EST via `.github/workflows/rough_diamond_pipeline.yml`

## Author

BidDeed.AI / Everest Capital USA - December 2025
