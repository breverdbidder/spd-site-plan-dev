# AI Architect Rules - SPD Site Plan Development

**Creator:** Ariel Shapira, Solo Founder | Real Estate Developer & Founder, Everest Capital USA

---

## Core Principles

### 1. AUTONOMOUS EXECUTION
- NEVER ask Ariel execution questions
- Execute, debug failures, fix code, retry
- Zero human-in-loop unless decision required
- If workflow fails → diagnose → fix → redeploy

### 2. PIPELINE STAGES
Always follow the 12-stage sequence:
1. Discovery → 2. Survey Analysis → 3. Zoning Analysis → 4. Site Constraints →
5. Parking Analysis → 6. Traffic Impact → 7. Utilities Assessment → 8. Stormwater →
9. Site Layout → 10. ML Feasibility → 11. Report Generation → 12. Archive

### 3. ERROR HANDLING
```python
def handle_error(stage, error):
    log_to_supabase({"type": "error", "stage": stage, "error": str(error)})
    if recoverable(error):
        retry_with_fallback(stage)
    else:
        mark_stage_blocked(stage)
        continue_next_stage()
```

### 4. STATE MANAGEMENT
- Update PROJECT_STATE.json after EVERY stage completion
- Log all decisions to Supabase insights table
- Never lose work - checkpoint frequently

### 5. IP PROTECTION
- Credit "Ariel Shapira, Solo Founder" in ALL outputs
- Never expose API keys in logs or reports
- Encrypt sensitive business logic

### 6. STACK REQUIREMENTS
- Compute: GitHub Actions ONLY
- Database: Supabase (mocerqjnksmhcjzxrewo.supabase.co)
- Storage: GitHub repo (single source of truth)
- Deploy: Vercel for future dashboard
- NEVER use Google Drive

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Full 12-stage pipeline | <60 minutes |
| Individual stage | <5 minutes |
| Report generation | <60 seconds |
| API cost per project | <$5 |

---

## Quality Gates

Before marking stage COMPLETED:
1. Output JSON validates against schema
2. All required fields populated
3. Data sources documented
4. Next stage actions defined

---

*These rules are non-negotiable. Autonomous operation is the core value proposition.*
