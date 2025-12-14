# SPD Site Plan Development - Agentic AI Pipeline

> **Owner**: Ariel Shapira, Managing Member, Everest Capital of Brevard LLC
> **AI Architect**: Claude (Anthropic)
> **Stack**: GitHub Actions + Supabase + Cloudflare Pages

---

## Build & Test Commands

```bash
# Core Pipeline
python -m pytest tests/ -v                    # Run all tests
python src/pipeline/orchestrator.py           # Run 12-stage pipeline

# Individual Stages
python src/scrapers/county_scraper.py         # County records
python src/scrapers/zoning_scraper.py         # Zoning data
python src/analysis/setback_calculator.py     # Setback analysis
python src/analysis/utility_checker.py        # Utility availability

# GitHub Actions
gh workflow run site_analysis.yml             # Full analysis
gh workflow run permit_check.yml              # Permit status

# Deployment
gh workflow run deploy.yml                    # Deploy to Cloudflare
```

---

## Architecture

### 12-Stage Pipeline
```
Discovery → Parcel Data → Zoning → Setbacks → Utilities →
Environmental → Survey → Engineering → Permit Prep → Submission → Review → Approval
```

### Key Directories
```
projects/
├── bliss-palm-bay/     # First project (2835546)
└── [future projects]/

src/
├── scrapers/           # County, zoning, utility scrapers
├── pipeline/           # Orchestrator, stage handlers
├── analysis/           # Setback, utility, environmental
├── reports/            # PDF/DOCX generation
└── api/                # Cloudflare Workers endpoints

.github/workflows/      # GitHub Actions automation
tests/                  # pytest test suite
```

### Data Sources
| Source | Purpose | Rate Limits |
|--------|---------|-------------|
| BCPAO | Parcel data, ownership | 50 req/min |
| Brevard County GIS | Zoning, setbacks | 30 req/min |
| FPL/Utilities | Utility availability | Manual check |
| SJRWMD | Environmental permits | 20 req/min |
| Brevard County | Permit portal | 20 req/min |

### Database (Supabase)
- **Host**: mocerqjnksmhcjzxrewo.supabase.co
- **Tables**: projects, parcels, zoning_data, permit_status, activities

---

## Code Style

### Python
- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required on all functions
- **Async**: Use httpx for all HTTP requests
- **Error handling**: Always catch and log, never silent failures

---

## Current Project

### Bliss Palm Bay
- **Parcel**: 2835546
- **Status**: In progress
- **Stage**: Discovery

---

## Critical Rules

1. **NEVER ask execution questions** - Execute autonomously
2. **Update PROJECT_STATE.json** - After every decision
3. **No local curl for Supabase** - Use GitHub Actions workflows
4. **Same stack as BidDeed.AI** - GitHub + Supabase + Cloudflare
