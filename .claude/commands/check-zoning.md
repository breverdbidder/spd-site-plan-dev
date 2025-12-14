---
description: Check zoning code and allowed uses for a parcel
allowed-tools:
  - Read
  - Bash
argument-hint: <parcel ID>
---

# Check Zoning Command

Query zoning information for a specific parcel.

## Process

1. Query BCPAO for parcel zoning
2. Look up zoning code requirements
3. List allowed uses
4. Calculate setbacks
5. Identify any overlays

## Output

```
🏛️ Zoning Report: $ARGUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ZONING
- Code: [zone code]
- Description: [full description]
- Category: [Residential/Commercial/Industrial]

ALLOWED USES
- By Right: [list]
- Conditional: [list]
- Prohibited: [key prohibitions]

SETBACKS
- Front: [ft]
- Side: [ft]
- Rear: [ft]
- Max Height: [ft]
- Max Coverage: [%]

OVERLAYS
- [any overlay districts]

VARIANCE REQUIRED: [Yes/No]
- Reason: [if yes, why]
```
