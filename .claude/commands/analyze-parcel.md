---
description: Analyze a parcel for site plan development
allowed-tools:
  - Read
  - Write
  - Bash
argument-hint: <parcel ID>
---

# Analyze Parcel Command

Run full analysis on a parcel for site plan development.

## Process

1. Query BCPAO for parcel data
2. Determine zoning and setbacks
3. Check utility availability
4. Identify environmental constraints
5. Calculate buildable area
6. Generate feasibility report

## Output

```
🏗️ Parcel Analysis: $ARGUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PARCEL DATA
- ID: $ARGUMENTS
- Owner: [from BCPAO]
- Legal: [legal description]
- Acres: [acreage]

ZONING
- Code: [zone]
- Allowed: [uses]
- Setbacks: F:[x] S:[y] R:[z]

UTILITIES
- Water: [available/unavailable]
- Sewer: [available/unavailable]
- Electric: [available/unavailable]

ENVIRONMENTAL
- Flood Zone: [zone]
- Wetlands: [yes/no]
- SJRWMD: [required/not required]

FEASIBILITY
- Buildable Area: [sq ft]
- Constraints: [list]
- Recommendation: [PROCEED/HOLD/REJECT]
```
