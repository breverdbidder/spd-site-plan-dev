# SPD Site Plan Development - Skills Integration

## Overview

The SPD (Site Plan Development) project uses the Agent Skills system to extend Claude's capabilities for the 12-stage site plan development pipeline. Skills provide specialized knowledge, workflows, and tools that Claude can load dynamically when needed.

## Architecture

```
spd-site-plan-dev/
├── skills/
│   ├── skill-creator/          # Meta-skill for creating new SPD skills
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── init_skill.py
│   │   │   └── package_skill.py
│   │   ├── references/
│   │   │   ├── workflows.md
│   │   │   ├── output-patterns.md
│   │   │   └── schema.md
│   │   └── LICENSE.txt
│   └── [future SPD-specific skills]/
├── .github/workflows/
│   ├── spd_skill_integration.yml   # Skill management workflow
│   └── [other orchestration workflows]
└── agents/
    └── orchestrator/                # LangGraph orchestrator
```

## Integration with LangGraph Orchestrator

The SPD orchestrator is a LangGraph-based agentic system that manages the 12-stage pipeline:

1. **Discovery** - Property research & feasibility
2. **Zoning Analysis** - Code compliance verification
3. **Survey Coordination** - Boundary & topographic surveys
4. **Site Analysis** - Environmental & utilities assessment
5. **Conceptual Design** - Initial layout development
6. **Engineering** - Civil, structural, MEP coordination
7. **Regulatory Review** - Permit preparation
8. **Submission** - Application filing
9. **Review Response** - Address agency comments
10. **Approval** - Final permits obtained
11. **Construction Documents** - Detailed drawings
12. **Closeout** - As-builts & documentation

### Skill Loading Strategy

Skills are loaded via **progressive disclosure**:

1. **At Startup**: Claude pre-loads skill `name` and `description` from all skills in `/skills/`
2. **During Tasks**: Claude triggers relevant skills based on the current stage
3. **On Demand**: Full SKILL.md and references loaded only when needed

### Creating SPD-Specific Skills

Use the skill-creator to build domain-specific skills for SPD workflows:

```bash
# Via GitHub Actions workflow
gh workflow run spd_skill_integration.yml \
  -f skill_action=create_new_skill \
  -f skill_name=bcpao-integration \
  -f skill_description="Query Brevard County Property Appraiser for parcel data"

# Or manually via Python
cd skills/skill-creator/scripts
python init_skill.py --name bcpao-integration --description "BCPAO API integration"
```

### Skill Development Workflow

1. **Create skill structure**: Use `init_skill.py`
2. **Add domain logic**: Populate SKILL.md with instructions
3. **Bundle resources**: Add scripts, references, assets as needed
4. **Test with orchestrator**: Run through LangGraph pipeline
5. **Package for distribution**: Use `package_skill.py`
6. **Version control**: Commit to Git for team sharing

## Example SPD Skills (Future)

- **bcpao-integration**: Brevard County Property Appraiser API queries
- **zoning-analyzer**: Parse zoning codes, setback requirements
- **permit-tracker**: Monitor application status via accela-civic-platform
- **survey-coordinator**: Interface with surveyor APIs, manage deliverables
- **autocad-generator**: Generate DXF/DWG files from design parameters
- **utility-locator**: Query 811 systems, coordinate utility companies
- **environmental-screener**: Wetlands, endangered species, FEMA checks
- **cost-estimator**: Construction cost calculations for feasibility
- **timeline-planner**: Critical path scheduling with regulatory milestones
- **document-generator**: Auto-generate permit applications, site plans

## Skill Best Practices for SPD

### 1. Concise Context
Token efficiency is critical. SPD projects involve large documents (surveys, plans, reports):
- Store full documents as assets, not in SKILL.md
- Use grep patterns to search large reference files
- Provide only essential procedural instructions

### 2. Appropriate Degrees of Freedom

- **High freedom**: Zoning interpretation, design alternatives
- **Medium freedom**: Permit application preparation (templates + guidance)
- **Low freedom**: AutoCAD script generation (exact commands)

### 3. Integration with External Tools

SPD skills often interface with external systems:
- **BCPAO API**: Property data retrieval
- **Accela Civic Platform**: Permit tracking
- **AutoCAD/Civil3D**: Drawing generation
- **Census API**: Demographic data
- **FEMA API**: Flood zone verification

Use `scripts/` for API clients and `references/` for API documentation.

### 4. State Persistence

Skills integrate with Supabase for cross-session state:
- Store project state, decisions, approvals
- Enable LangGraph checkpoints between stages
- Track which skills were used and when

## Autonomous Skill Creation

The SPD orchestrator can autonomously create new skills when it encounters repeated patterns:

```python
# In LangGraph orchestrator
if pattern_detected(task_history, frequency_threshold=3):
    dispatch_event(
        event_type="skill_needed",
        payload={
            "action": "create_new_skill",
            "skill_name": infer_skill_name(pattern),
            "skill_description": generate_description(pattern)
        }
    )
```

This triggers the `spd_skill_integration.yml` workflow via `repository_dispatch`.

## Monitoring & Logging

All skill operations log to Supabase `insights` table:
- Skill creation/updates
- Skill trigger events
- Performance metrics (tokens used, execution time)
- Error tracking

Query insights:
```sql
SELECT * FROM insights 
WHERE category = 'spd_skill_integration' 
ORDER BY timestamp DESC;
```

## Security Considerations

- Skills execute code via Claude's bash tool
- Stick to trusted sources (Anthropic, internal team)
- Audit scripts before deployment, especially external API calls
- Use environment variables for secrets (never hardcode keys)
- Apply least-privilege via `allowed-tools` in SKILL.md frontmatter

## Deployment

Skills auto-deploy via GitHub Actions:
1. Commit skill to `/skills/[skill-name]/`
2. Push to `main` branch
3. GitHub Actions validates skill structure
4. Supabase logs deployment event
5. Skill immediately available to orchestrator

## Resources

- [Anthropic Skills Documentation](https://github.com/anthropics/skills)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SPD Pipeline Specification](../docs/PIPELINE.md)
- [Supabase Schema](../docs/SCHEMA.md)

## Contributing

To add a new skill:
1. Use skill-creator or run `init_skill.py`
2. Follow naming convention: `[domain]-[action]` (e.g., `zoning-analyzer`)
3. Include comprehensive `description` in YAML frontmatter
4. Add test cases in `scripts/test_[skill-name].py`
5. Document in this README under "Example SPD Skills"
6. Submit PR with skill + tests + documentation

---

**Stack**: GitHub + Supabase + Cloudflare Pages + GitHub Actions  
**Parent**: EVEREST CAPITAL USA  
**Methodology**: The Everest Ascent™ (12 stages)  
**Positioning**: Agentic AI ecosystem (NOT SaaS)
