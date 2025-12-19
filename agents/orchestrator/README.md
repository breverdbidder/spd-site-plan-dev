# SPD Skill Creator - LangGraph Orchestration

Autonomous skill creation and deployment system for SPD Site Plan Development, following [Anthropic skill-creator best practices](https://github.com/anthropics/skills/tree/main/skills/skill-creator).

## Architecture

```
SPD Skill Creator
├── LangGraph Orchestrator (Python)
│   ├── Analyze Request → Determine skill type, freedom level, resources
│   ├── Generate SKILL.md → Create concise, progressive disclosure content
│   ├── Validate → Check frontmatter, line count, structure
│   └── Deploy → Commit to GitHub, log to Supabase
├── GitHub Actions Workflow
│   ├── Manual trigger (workflow_dispatch)
│   ├── API trigger (repository_dispatch)
│   └── Auto-deploy to skills/ directory
└── Supabase Logging
    └── Track all skill creations in insights table
```

## Skill Anatomy

Following Anthropic standards:

```
skills/parcel-analyzer/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown instructions (<500 lines)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash)
    ├── references/       - Documentation (loaded as needed)
    └── assets/           - Output files (templates, images)
```

## Core Principles

### 1. Concise is Key
Context window is public good. Only add what Claude doesn't already know.

### 2. Progressive Disclosure
- **Metadata (name + description)**: Always in context (~100 words)
- **SKILL.md body**: When skill triggers (<5k words, <500 lines)
- **Bundled resources**: As needed by Claude

### 3. Freedom Levels
- **High freedom**: Text instructions, heuristics, multiple valid approaches
- **Medium freedom**: Pseudocode, configurable patterns, preferred approach
- **Low freedom**: Specific scripts, precise sequences, fragile operations

## Usage

### Manual Creation (GitHub UI)

1. Go to Actions → skill_creator.yml workflow
2. Click "Run workflow"
3. Enter skill request
4. Wait for completion (~2-3 minutes)
5. Review deployed skill in `skills/{skill-name}/`

### API Trigger (Programmatic)

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  https://api.github.com/repos/breverdbidder/spd-site-plan-dev/dispatches \
  -d '{
    "event_type": "create_skill",
    "client_payload": {
      "skill_request": "Create a skill for calculating site development costs..."
    }
  }'
```

### Python Integration

```python
from spd_skill_creator_agent import run_skill_creator

skill_request = """
Create a skill for permit tracking.
Should monitor BCPAO ePermitting system, track application status,
alert on approvals/rejections, and log timeline metrics.
"""

result = run_skill_creator(skill_request)

if result['deployment_status'] == 'SUCCESS':
    print(f"✅ Skill created: {result['skill_name']}")
else:
    print(f"❌ Error: {result['error']}")
```

## Workflow Stages

### 1. Analyze Request
- Determines skill type: `workflow | tool | domain | bundled`
- Sets freedom level: `high | medium | low`
- Identifies bundled resources: `scripts | references | assets`
- Extracts skill name and description

### 2. Generate SKILL.md
- Creates YAML frontmatter (name, description)
- Writes concise workflow guidance (<500 lines)
- Implements progressive disclosure patterns
- References bundled resources appropriately

### 3. Validate
- Checks YAML frontmatter presence
- Verifies name and description fields
- Ensures under 500 lines
- Validates structure and clarity

### 4. Deploy
- Creates skill directory
- Writes SKILL.md
- Creates bundled resource directories
- Commits and pushes to GitHub
- Logs to Supabase insights

## Examples

### High Freedom Skill (Workflow)
```yaml
---
name: stakeholder-communication
description: Multi-step workflow for communicating with property owners, government officials, and contractors
---

# Stakeholder Communication

## Workflow
1. Identify stakeholders by role
2. Determine communication timing and method
3. Draft context-appropriate messages
4. Track responses and follow-ups
```

### Medium Freedom Skill (Tool)
```yaml
---
name: zoning-calculator
description: Calculate maximum density, setbacks, and buildable area based on Brevard County zoning codes
---

# Zoning Calculator

## Quick Start
```python
from scripts.zoning_calc import calculate_max_density
result = calculate_max_density(parcel_id="2835546", zoning="RU-1-11")
```

See references/ZONING_CODES.md for all zones
```

### Low Freedom Skill (Bundled)
```yaml
---
name: permit-submission
description: Submit site plan applications with exact required document set
---

# Permit Submission

**DO NOT DEVIATE - System will reject out-of-order submissions**

```bash
./scripts/submit_permit.sh --parcel 2835546 --type "Multi-Family"
```

See references/EPERMITTING_API.md for full docs
```

## Integration with SPD Pipeline

Skills integrate with the 12-stage SPD pipeline:

```
Stage 1: Discovery → Uses: parcel-analyzer, zoning-calculator
Stage 2: Feasibility → Uses: cost-estimator, regulatory-checker  
Stage 3: Design → Uses: site-plan-generator, cad-exporter
Stage 4: Review → Uses: plan-reviewer, compliance-checker
...
Stage 12: Archive → Uses: document-organizer, records-manager
```

## Best Practices

### DO:
✅ Keep SKILL.md under 500 lines  
✅ Use progressive disclosure (references/)  
✅ Match freedom level to task fragility  
✅ Reference bundled resources clearly  
✅ Write concise, token-efficient content  

### DON'T:
❌ Create README.md or auxiliary docs  
❌ Exceed 500 lines in SKILL.md  
❌ Duplicate content across files  
❌ Include verbose explanations  
❌ Forget YAML frontmatter  

## Troubleshooting

### Validation Failed
```
❌ Validation failed: Missing YAML frontmatter
```
**Fix**: Ensure SKILL.md starts with `---` and includes `name:` and `description:` fields

### Skill Not Triggering
```
Claude doesn't use my skill
```
**Fix**: Improve `description` in YAML frontmatter - this is what Claude uses to decide when to use the skill

---

**Powered by**: LangGraph + Anthropic + GitHub Actions + Supabase  
**Stack**: Python 3.11, Claude Sonnet 4.5, GitHub REST API  
**Repo**: https://github.com/breverdbidder/spd-site-plan-dev
