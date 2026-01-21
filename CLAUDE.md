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
