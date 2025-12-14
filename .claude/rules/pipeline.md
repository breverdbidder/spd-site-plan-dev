# Site Plan Pipeline Rules

## 12-Stage Pipeline

```
1. Discovery      → Identify parcel, ownership, basic info
2. Parcel Data    → Pull BCPAO data, boundaries, legal description
3. Zoning         → Determine zoning code, allowed uses
4. Setbacks       → Calculate front, side, rear setbacks
5. Utilities      → Check water, sewer, electric availability
6. Environmental  → SJRWMD permits, wetlands, flood zone
7. Survey         → Boundary survey, topographic survey
8. Engineering    → Site engineering, drainage, grading
9. Permit Prep    → Prepare application package
10. Submission    → Submit to Brevard County
11. Review        → Track review status, respond to comments
12. Approval      → Final approval, record plat
```

## Stage Requirements

Each stage MUST:
1. Complete all checklist items
2. Log completion to `activities` table
3. Update PROJECT_STATE.json
4. Generate stage report if applicable

## Decision Points

- **PROCEED**: All requirements met
- **HOLD**: Waiting for external input
- **REJECT**: Fatal issue found (e.g., zoning incompatible)

## Data Storage

All project data goes to Supabase:
- `projects` - Project overview
- `parcels` - Parcel details
- `zoning_data` - Zoning analysis
- `permit_status` - Permit tracking
