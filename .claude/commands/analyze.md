---
description: Analyze a parcel for site plan feasibility
allowed-tools: Bash, Read, Glob
argument-hint: [parcel-id]
---

# Analyze Parcel - SPD

## Arguments
- `$1`: Parcel ID (e.g., 2835546)

## Analysis Steps

### 1. Fetch BCPAO Data
```bash
python src/scrapers/bcpao_scraper.py --parcel-id "$1" 2>/dev/null || echo "BCPAO scraper not found"
```

### 2. Check Zoning
```bash
python src/scrapers/zoning_scraper.py --parcel-id "$1" 2>/dev/null || echo "Zoning scraper not found"
```

### 3. Generate Report
Invoke `site-analyzer` agent with parcel data.

## Quick Reference

### Brevard County Zoning Codes
| Code | Type | Min Lot |
|------|------|---------|
| RU-1-13 | SF Residential | 13,000 sf |
| RU-1-9 | SF Residential | 9,000 sf |
| RU-2-10 | Duplex | 10,000 sf |
| BU-1 | General Business | Varies |

### BCPAO API
```
https://www.bcpao.us/api/v1/search?parcel=$1
```

## Output

Generate feasibility assessment:
- Zoning compatibility
- Setback requirements
- Utility availability
- Environmental constraints
- Development potential
