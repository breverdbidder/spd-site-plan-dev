---
description: Generate feasibility report for a project
allowed-tools:
  - Read
  - Write
  - Bash
argument-hint: <project name>
---

# Generate Report Command

Generate a comprehensive site feasibility report.

## Process

1. Gather all project data
2. Compile parcel information
3. Include zoning analysis
4. Add utility assessment
5. Summarize environmental factors
6. Calculate estimated costs
7. Provide recommendation

## Output

Creates a DOCX report with:

```
SITE FEASIBILITY REPORT
[Project Name]
━━━━━━━━━━━━━━━━━━━━━━━

EXECUTIVE SUMMARY
- Parcel: [ID]
- Acreage: [size]
- Zoning: [code]
- Recommendation: [PROCEED/HOLD/REJECT]

PARCEL DATA
[Full BCPAO information]

ZONING ANALYSIS
[Setbacks, allowed uses, constraints]

UTILITY ASSESSMENT
[Water, sewer, electric availability]

ENVIRONMENTAL
[Flood zone, wetlands, permits required]

COST ESTIMATES
- Land: $[amount]
- Utilities: $[amount]
- Permits: $[amount]
- Development: $[amount]
- Total: $[amount]

TIMELINE
[Estimated project timeline]

RISKS
[Key risks and mitigation]

RECOMMENDATION
[Final recommendation with rationale]
```

Report saved to: projects/[name]/reports/feasibility-[date].docx
