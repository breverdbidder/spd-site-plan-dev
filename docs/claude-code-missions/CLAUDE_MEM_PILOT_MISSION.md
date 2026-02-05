# MISSION: Claude-Mem Pilot Installation & Validation
# Duration: 2-3 hours autonomous
# Repo: breverdbidder/spd-site-plan-dev
# Branch: pilot/claude-mem
# Zero human-in-the-loop

---

## PHASE 0: PRE-FLIGHT (5 min)

```bash
# Ensure you're on the pilot branch
git checkout pilot/claude-mem
git pull origin pilot/claude-mem

# Merge latest from main to stay current
git merge origin/main --no-edit
```

---

## PHASE 1: INSTALL CLAUDE-MEM (5 min)

Run these commands in Claude Code:

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Then restart Claude Code session to activate hooks.

**VERIFICATION:**
```bash
# After restart, check plugin is active
ls -la ~/.claude/plugins/marketplaces/thedotmack/
# Should see claude-mem directory with hooks

# Check if .claude-mem/ was created in repo
ls -la .claude-mem/ 2>/dev/null || echo "No observations yet - expected after first session"
```

---

## PHASE 2: SECURITY CONFIGURATION (5 min)

Claude-Mem supports `<private>` tags to exclude sensitive data. Before any work, create a `.claude-mem-config` or equivalent to ensure:

1. **NO API keys/PATs captured** in observations
2. **NO Supabase credentials** stored
3. **NO GitHub tokens** logged

```bash
# Check if claude-mem has a config file
cat ~/.claude/plugins/marketplaces/thedotmack/claude-mem/.env 2>/dev/null
cat .claude-mem/config.json 2>/dev/null
```

If sensitive data appears in any observation, wrap it with `<private>` tags or configure exclusion patterns.

---

## PHASE 3: REAL DEVELOPMENT SESSION — Bliss Palm Bay Discovery (60-90 min)

Execute a real SPD pipeline task to generate meaningful observations. Target: **Bliss Palm Bay (Account 2835546)**

### Stage 1: Discovery
```bash
# Pull BCPAO data for account 2835546
curl -s "https://www.bcpao.us/api/v1/search?acct=2835546" | python3 -m json.tool > /tmp/bcpao_2835546.json

# Extract key fields
python3 -c "
import json
with open('/tmp/bcpao_2835546.json') as f:
    data = json.load(f)
print(json.dumps({
    'account': data.get('account'),
    'owner': data.get('owner'),
    'address': data.get('siteAddress'),
    'legal': data.get('legal'),
    'landValue': data.get('landValue'),
    'buildingValue': data.get('buildingValue'),
    'acres': data.get('acres'),
    'useCode': data.get('useCode'),
    'zoning': data.get('zoning'),
    'photo': data.get('masterPhotoUrl')
}, indent=2))
"
```

### Stage 2: Create/Update Project Files
```bash
# Create or update project directory
mkdir -p projects/SPD-2025-002

# Save discovery data
cp /tmp/bcpao_2835546.json projects/SPD-2025-002/bcpao_raw.json
```

### Stage 3: Zoning Analysis
- Query BCPAO GIS API for parcel geometry
- Determine zoning district and setback requirements
- Document any decisions about zoning interpretation

```bash
# GIS query for parcel
curl -s "https://gis.brevardfl.gov/gissrv/rest/services/Base_Map/Parcel_New_WKID2881/MapServer/5/query?where=ACCOUNT='2835546'&outFields=*&returnGeometry=true&f=json" > /tmp/gis_2835546.json
```

### Stage 4: Make Architectural Decisions
During this session, make at least 3 explicit architectural decisions that Claude-Mem should capture:

1. **DECISION: Data storage format** — Choose JSON vs Supabase for stage outputs
2. **DECISION: Pipeline orchestration** — LangGraph vs sequential script for SPD stages
3. **DECISION: Report template** — DOCX skill vs custom template for SPD reports

Document your reasoning for each. The Observer AI should capture these as ⚖️ Decision observations.

### Stage 5: Implement Something
Write actual code — at minimum:
- Update `src/pipeline/pipeline_orchestrator.py` with Bliss Palm Bay data flow
- Create or update `projects/SPD-2025-002/stage1_discovery.json` with structured output
- Fix any bugs encountered (Observer AI should capture as 🔴 Bugfix)

---

## PHASE 4: VALIDATE OBSERVATIONS (15 min)

After the development session, audit what Claude-Mem captured:

```bash
# List all observations
ls -la .claude-mem/
find .claude-mem/ -type f | head -50

# Count observations by type
echo "=== OBSERVATION COUNTS ==="
grep -r "decision" .claude-mem/ --include="*.json" -l | wc -l
grep -r "bugfix" .claude-mem/ --include="*.json" -l | wc -l
grep -r "feature" .claude-mem/ --include="*.json" -l | wc -l
grep -r "discovery" .claude-mem/ --include="*.json" -l | wc -l

# Check for sensitive data leaks
echo "=== SECURITY AUDIT ==="
grep -ri "ghp_" .claude-mem/ && echo "⚠️ GITHUB TOKEN FOUND" || echo "✅ No GitHub tokens"
grep -ri "sbp_" .claude-mem/ && echo "⚠️ SUPABASE KEY FOUND" || echo "✅ No Supabase keys"
grep -ri "supabase_service_role" .claude-mem/ && echo "⚠️ SERVICE ROLE FOUND" || echo "✅ No service roles"
grep -ri "eyJ" .claude-mem/ && echo "⚠️ JWT TOKEN FOUND" || echo "✅ No JWTs"

# Sample 3 random observations for quality check
echo "=== SAMPLE OBSERVATIONS ==="
find .claude-mem/ -name "*.json" | shuf | head -3 | while read f; do
    echo "--- $f ---"
    cat "$f" | python3 -m json.tool 2>/dev/null || cat "$f"
    echo ""
done
```

### Quality Checklist:
- [ ] ≥3 decision observations captured
- [ ] ≥1 discovery observation from BCPAO data pull
- [ ] Observations include before/after context (7 events each)
- [ ] No sensitive credentials in any observation
- [ ] Observations are searchable by file path
- [ ] Observations are searchable by concept

---

## PHASE 5: TEST MEMORY RECALL (15 min)

Start a NEW Claude Code session (to test cross-session memory):

```
# In new session, test if Claude-Mem injects context
# Ask about previous decisions:
"What data storage format did we decide on for SPD stage outputs?"
"What architectural decisions were made for Bliss Palm Bay?"
"Show me observations related to pipeline_orchestrator.py"
```

### Recall Checklist:
- [ ] Claude remembers the data storage decision without manual context
- [ ] Session starts with lightweight index (~2K tokens, not full dump)
- [ ] On-demand detail fetch works (expand specific observation)
- [ ] File-scoped search returns relevant results
- [ ] Concept-scoped search returns relevant results

---

## PHASE 6: GENERATE PILOT REPORT (15 min)

Create `docs/claude-mem-pilot-results.md` with:

```markdown
# Claude-Mem Pilot Results — SPD Site Plan Dev
# Date: [TODAY]
# Branch: pilot/claude-mem

## Installation
- Plugin version: [version]
- Install time: [minutes]
- Issues: [any problems]

## Observations Captured
- Total: [count]
- Decisions: [count]
- Bugfixes: [count]
- Features: [count]
- Discoveries: [count]

## Token Efficiency
- Index load cost: [tokens]
- Per-observation fetch cost: [tokens]
- Compared to PROJECT_STATE.json boot: [comparison]

## Security Audit
- Sensitive data leaks: [yes/no, details]
- Privacy controls working: [yes/no]

## Cross-Session Recall
- Decision recall accuracy: [%]
- Context recovery time: [seconds]
- Relevance of injected context: [1-10]

## Comparison: Claude-Mem vs context-boot-mcp-server
| Metric | context-boot | claude-mem | Winner |
|--------|-------------|------------|--------|
| Setup time | | | |
| Observation granularity | | | |
| Token efficiency | | | |
| Search capability | | | |
| Security | | | |

## Recommendation
- [ ] ADOPT — Roll out to BidDeed.AI main repo
- [ ] EXTEND PILOT — Need more data
- [ ] REJECT — Not worth the overhead
- [ ] HYBRID — Use alongside context-boot-mcp-server

## Notes
[freeform observations]
```

---

## PHASE 7: COMMIT & PUSH (5 min)

```bash
# Add claude-mem observations and pilot results
git add .claude-mem/ docs/claude-mem-pilot-results.md projects/SPD-2025-002/
git commit -m "feat: Claude-Mem pilot Phase 1 complete - observations and results"
git push origin pilot/claude-mem
```

---

## SUCCESS CRITERIA

| Metric | Pass | Fail |
|--------|------|------|
| Plugin installs without errors | ✅ | ❌ |
| ≥5 observations captured | ✅ | ❌ |
| Zero credential leaks | ✅ | ❌ |
| Cross-session recall works | ✅ | ❌ |
| Token overhead <5% | ✅ | ❌ |
| Pilot report committed | ✅ | ❌ |

---

## BLOCKERS / ESCALATION

If any of these occur, log to Supabase insights and continue:
1. **Plugin install fails** → Try manual install from GitHub clone
2. **No observations generated** → Check hooks in `~/.claude/hooks/`
3. **Sensitive data leaked** → Immediately delete `.claude-mem/`, configure exclusions, retry
4. **Plugin causes session crashes** → Uninstall, document failure, REJECT recommendation

---

**Generated by Claude AI Architect | Feb 5, 2026**
**Zero human actions required — paste this mission into Claude Code and walk away**
