# SPD Site Plan Development - Agentic AI Pipeline

## Architecture
- **Stack:** Same as BidDeed.AI (GitHub + Supabase + Cloudflare + LangGraph)
- **Repo:** github.com/breverdbidder/spd-site-plan-dev
- **Model:** 12-stage agentic pipeline (Discovery → Approval)
- **First Project:** Bliss Palm Bay (Parcel 2835546)

## Features to Implement

### Phase 1: Pipeline Architecture 🔄
- [x] 12-stage pipeline design
- [x] Stage 1: Discovery (parcel identification)
- [x] Stage 2: Zoning Analysis (ZoneWise integration)
- [ ] Stage 3: Environmental Review
- [ ] Stage 4: Traffic Impact
- [ ] Stage 5: Utility Assessment
- [ ] Stage 6: Preliminary Design
- [ ] Stage 7: Engineering Review
- [ ] Stage 8: Permit Application
- [ ] Stage 9: Agency Coordination
- [ ] Stage 10: Public Hearing Prep
- [ ] Stage 11: Approval Process
- [ ] Stage 12: Final Documentation

### Phase 2: Data Sources Integration
- [ ] Brevard County GIS (parcels)
- [ ] ZoneWise zoning data
- [ ] BCPAO property records
- [ ] Environmental databases
- [ ] FDOT traffic data
- [ ] Utility provider APIs

### Phase 3: Document Generation
- [ ] Site plan PDF generation
- [ ] Traffic study template
- [ ] Environmental assessment
- [ ] Permit application forms
- [ ] Public notice documents

### Phase 4: Bliss Palm Bay Project
- [ ] Parcel 2835546 analysis
- [ ] Zoning compliance check
- [ ] Setback calculations
- [ ] FAR verification
- [ ] Utility availability
- [ ] Access road requirements

### Phase 5: Agency Integration
- [ ] Brevard County Planning
- [ ] SJRWMD (water management)
- [ ] FDEP (environmental)
- [ ] FDOT (traffic)
- [ ] Fire marshal
- [ ] Utility providers

### Phase 6: Agentic Workflow
- [ ] LangGraph orchestration
- [ ] Multi-agent coordination
- [ ] Decision logging
- [ ] Human-in-the-loop checkpoints
- [ ] Approval gates

### Phase 7: Reporting Dashboard
- [ ] Project status tracking
- [ ] Timeline visualization
- [ ] Document checklist
- [ ] Agency response tracking
- [ ] Cost estimation

## Pipeline Stages (The Everest Ascent™)
1. **Discovery** - Identify parcel, owner, existing conditions
2. **Zoning Analysis** - Verify allowable uses, setbacks, FAR
3. **Environmental Review** - Wetlands, endangered species, flood zones
4. **Traffic Impact** - Trip generation, intersection analysis
5. **Utility Assessment** - Water, sewer, electric, gas availability
6. **Preliminary Design** - Site layout, building placement
7. **Engineering Review** - Stormwater, grading, utilities
8. **Permit Application** - Forms, fees, submissions
9. **Agency Coordination** - Multi-agency review management
10. **Public Hearing Prep** - Notices, presentations, responses
11. **Approval Process** - Board meetings, conditions
12. **Final Documentation** - Recorded plat, permits, approvals

## Key Files
- `src/pipeline/` - Stage implementations
- `src/agents/` - LangGraph agent definitions
- `src/documents/` - Template generation
- `PROJECT_STATE.json` - Pipeline state tracking
