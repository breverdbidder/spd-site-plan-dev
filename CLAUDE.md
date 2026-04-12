# SPD - Site Plan Development

> **Everest Capital USA** | Agentic AI 12-Stage Pipeline for Site Plan Approval
> Same Stack as BidDeed.AI: GitHub + Supabase + Cloudflare + GitHub Actions

## Build & Test Commands

```bash
# Python (agents, scrapers)
python -m pytest tests/ -v              # Run all tests
python -m black src/ --check            # Check formatting
python -m flake8 src/                   # Lint code

# GitHub Actions (production)
gh workflow run discovery.yml           # Trigger discovery stage
gh workflow run insert_insight.yml      # Insert to Supabase
gh run list --limit=5                   # Check workflow status
```

## Code Style

### Python
- **Version**: Python 3.11+
- **Formatting**: Black (88 char lines)
- **Type hints**: Required
- **Docstrings**: Google style

## Architecture

### SPD 12-Stage Pipeline (Mirrors BidDeed.AI)

```
Stage 1:  Discovery      → Find parcels needing site plans
Stage 2:  Scraping       → BCPAO property data extraction
Stage 3:  Zoning         → Verify zoning compatibility
Stage 4:  Setbacks       → Calculate required setbacks
Stage 5:  Utilities      → Check utility availability
Stage 6:  Environmental  → Wetlands, flood zones, protected
Stage 7:  Traffic        → Impact analysis requirements
Stage 8:  Permits        → Required permit identification
Stage 9:  Cost Est       → Development cost estimation
Stage 10: Timeline       → Approval timeline projection
Stage 11: Report Gen     → Site plan feasibility report
Stage 12: Archive        → Historical data storage
```

### Directory Structure

```
spd-site-plan-dev/
├── src/
│   ├── scrapers/           # Data collection
│   │   ├── bcpao_scraper.py     # Property appraiser
│   │   ├── zoning_scraper.py    # Zoning data
│   │   └── permits_scraper.py   # Permit requirements
│   ├── agents/             # LangGraph agents
│   │   ├── discovery/           # Parcel identification
│   │   └── analysis/            # Feasibility analysis
│   └── utils/              # Shared utilities
├── .github/workflows/      # GitHub Actions
│   └── insert_insight.yml
├── tests/                  # pytest tests
└── reports/                # Generated reports
```

### First Project

| Field | Value |
|-------|-------|
| Project Name | Bliss Palm Bay |
| Parcel ID | 2835546 |
| Status | Discovery |

### External Services

| Service | Purpose | Config |
|---------|---------|--------|
| Supabase | Database (mocerqjnksmhcjzxrewo) | GitHub Secrets |
| GitHub Actions | Compute | .github/workflows/ |
| BCPAO | Property data | Public API |

## Supabase Tables

| Table | Purpose |
|-------|---------|
| `spd_projects` | Active site plan projects |
| `spd_parcels` | Parcel analysis data |
| `spd_permits` | Permit requirements |
| `insights` | Pipeline logging |

## Project Rules

### NEVER
- Store API keys in code
- Guess zoning requirements
- Skip environmental checks
- Assume permit requirements

### ALWAYS
- Verify with official county sources
- Log all decisions to Supabase
- Update PROJECT_STATE.json
- Document assumptions

## Brevard County Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| BCPAO | bcpao.us | Property data |
| Brevard County | brevardfl.gov | Permits, zoning |
| GIS | gis.brevardfl.gov | Maps, boundaries |

## Integration with BidDeed.AI

- Shares Supabase database
- Same GitHub Actions patterns
- Compatible scraper architecture
- Reuses BCPAO integration
---

## Supabase MCP Integration

### Configuration
This repo uses Supabase MCP for direct database operations during Claude Code sessions.
- **Package**: @supabase/mcp-server
- **Token**: SUPABASE_MCP_TOKEN (GitHub Secret)
- **Project**: mocerqjnksmhcjzxrewo.supabase.co

### MCP Operation Rules

#### ✅ AUTONOMOUS (No Approval)
- CREATE TABLE, ALTER TABLE ADD COLUMN
- CREATE INDEX, CREATE VIEW
- SELECT (any query)
- INSERT (any amount)
- UPDATE/DELETE ≤100 rows

#### ⚠️ REQUIRES CONFIRMATION  
- UPDATE/DELETE >100 rows
- Schema changes to core tables
- New foreign key constraints

#### 🚫 NEVER WITHOUT EXPLICIT APPROVAL
- DROP TABLE
- TRUNCATE
- ALTER TABLE DROP COLUMN
- DELETE/UPDATE without WHERE clause

### Audit Logging
Log all schema changes and bulk operations to `activities` table:
```sql
INSERT INTO activities (activity_type, description, metadata, created_at)
VALUES ('mcp_operation', 'description', '{"operation": "..."}', NOW());
```

---

# Autonomous Improvement Protocol (Greptile-Powered)

## Before ANY Code Change:
1. Query Greptile: "What does [file/component] do and connections?"
2. Query Greptile: "Dependencies and side effects of changing [file]?"
3. Query Greptile: "Existing tests for [component]?"

## Sprint Task Workflow:
```
1. get_next_task() from Supabase
2. start_task(task_id)
3. Query Greptile for context
4. Implement + write tests
5. Create PR
6. complete_task(task_id, pr_url)
7. Repeat
```

## Quality Gates:
- Tests written and passing
- Type hints on new functions  
- Error handling with retry logic
- Greptile queried for side effects


<!-- KARPATHY_DISCIPLINE_BEGIN v1.0 -->
## Behavioral Discipline (Karpathy Guidelines)

> Adapted from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) · MIT License · ~14k★ · Karpathy-starred.
> Adopted by Everest Capital 2026-04-12. This section is **complementary** to the existing HONESTY PROTOCOL, PAIRING RULE, COST DISCIPLINE, and CLI-ANYTHING mandates above — it does not replace them.

**Tradeoff posture:** These guidelines bias toward caution over speed. For trivial tasks (typo fix, one-line config), use judgment and skip the ceremony.

### K1. Think Before Coding *(reinforces HONESTY PROTOCOL)*

Don't assume. Don't hide confusion. Surface tradeoffs.

- State assumptions explicitly. If uncertain, label as `INFERRED` per HONESTY PROTOCOL.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

**Everest delta:** when an assumption is surfaced, it must carry a `VERIFIED / UNTESTED / INFERRED` tag. Wrong `VERIFIED` = 3× penalty to honesty_violations table.

### K2. Simplicity First *(complements XGBoost efficiency cap)*

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and 50 would do, rewrite.

Ask: "Would a senior engineer call this overcomplicated?" If yes, simplify.

**Everest delta:** this is per-diff. XGBoost efficiency (90 min/chat, max 3 chats/task) is per-session. Both apply.

### K3. Surgical Changes *(NEW — closes AUTOLOOP evolver bloat gap)*

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, **mention it — don't delete it.**

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless explicitly asked.

**The test:** every changed line must trace directly to the user's request.

**Everest delta — AUTOLOOP V2 evolver constraint:** prompt/rule updates produced by the evolver must be **minimal and surgical**. Diffs that exceed 20% line growth or touch sections unrelated to the failing case must be rejected by the evolver's self-check and re-attempted with a narrower edit. This closes the bloat failure mode flagged by Dylan Cleppe's extraction-funnel analysis (2026-04-12) and by Karpathy directly.

### K4. Goal-Driven Execution *(complements EG14 gate)*

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

**Everest delta:** for SUMMIT dispatches touching production (zonewise-web, dify-zonewise, nexus), the EG14 14-point enterprise gate is the canonical success criteria. Goal-driven execution at the sub-task level must compose up to an EG14 verdict, not replace it.

### Working indicators

These guidelines are working if:
- Fewer unnecessary changes appear in diffs.
- Fewer rewrites happen due to overcomplication.
- Clarifying questions arrive *before* implementation, not after mistakes.
- AUTOLOOP evolver prompt diffs stay small and targeted.

### Attribution

Source: https://github.com/forrestchang/andrej-karpathy-skills (MIT)
Upstream quote from Karpathy: *"LLMs are exceptionally good at looping until they meet specific goals. Don't tell it what to do, give it success criteria and watch it go."*
<!-- KARPATHY_DISCIPLINE_END v1.0 -->
