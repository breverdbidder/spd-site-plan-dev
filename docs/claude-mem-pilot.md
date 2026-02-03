# Claude-Mem Pilot Program

**Repository:** breverdbidder/spd-site-plan-dev  
**Pilot Period:** Feb 3-17, 2026  
**Branch:** `pilot/claude-mem`  
**Status:** 🟢 ACTIVE

---

## Overview

Claude-Mem is a Claude Code plugin that provides persistent memory across coding sessions via an "observer AI" that watches and logs decisions, bugfixes, features, and discoveries in real-time.

**GitHub:** https://github.com/thedotmack/claude-mem  
**Docs:** https://docs.claude-mem.ai/introduction

---

## Installation (Claude Code Session)

```bash
# Step 1: Add from marketplace
/plugin marketplace add thedotmack/claude-mem

# Step 2: Install
/plugin install claude-mem
```

After installation, a `.claude-mem/` directory will be created in the repo root.

---

## How It Works

| Feature | Description |
|---------|-------------|
| **Real-time Observation** | Observer AI watches every session, generating searchable logs |
| **Auto-categorization** | Observations tagged as: `decision`, `bugfix`, `feature`, `discovery` |
| **Progressive Disclosure** | ~40 tokens/observation initially, full fetch on-demand (~850 tokens) |
| **Before/After Context** | Each observation includes 7 prior + 7 following events for causality |
| **File Scoping** | Query by file path: `type:decision file:src/agents/` |
| **Concept Scoping** | Query by semantic concept: `decisions about "site plan parsing"` |

---

## Success Metrics (Pilot Evaluation)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Session continuity | 90%+ context retention | Compare pre/post pilot sessions |
| Bug causality tracking | 5+ instances captured | Count "before/after" chains that reveal bug sources |
| Decision recall | 100% architectural decisions logged | Audit `.claude-mem/` vs `PROJECT_STATE.json` |
| Token efficiency | <5% overhead | Compare token usage pre/post |
| Zero data leakage | No sensitive data in logs | Security audit at pilot end |

---

## Comparison: Claude-Mem vs context-boot-mcp-server

| Capability | context-boot-mcp-server | Claude-Mem |
|------------|------------------------|------------|
| Storage | Supabase (remote) | Local `.claude-mem/` |
| Trigger | Manual boot command | Automatic observation |
| Granularity | Session-level checkpoints | Event-level observations |
| Search | N/A | By type, file, concept |
| Causality | No | Yes (before/after context) |
| Token usage | Full checkpoint load | Progressive disclosure |

**Conclusion:** Complementary, not replacement. Claude-Mem for intra-session detail, context-boot for cross-session state.

---

## Pilot Tasks

### Week 1 (Feb 3-9): Installation & Baseline
- [ ] Install Claude-Mem on `pilot/claude-mem` branch
- [ ] Run 3 standard development sessions
- [ ] Capture baseline metrics (session duration, context switches, bugs)
- [ ] Document any installation issues

### Week 2 (Feb 10-17): Evaluation & Decision
- [ ] Run 3 more development sessions with intentional context switches
- [ ] Test causality tracking: introduce a bug, track observation chain
- [ ] Compare `.claude-mem/` observations vs manual `PROJECT_STATE.json` updates
- [ ] Security audit: scan for sensitive data leakage
- [ ] Final recommendation: ADOPT / CONDITIONAL / REJECT

---

## Files to Monitor

```
.claude-mem/
├── observations/       # Auto-generated observation logs
├── index.json         # Searchable index (titles, types, timestamps)
└── config.json        # Plugin configuration
```

---

## Rollback Plan

If pilot fails or security issues found:

```bash
# Remove plugin
/plugin uninstall claude-mem

# Delete local storage
rm -rf .claude-mem/

# Discard branch
git checkout main
git branch -D pilot/claude-mem
```

---

## Decision Criteria

| Score | Action | Criteria |
|-------|--------|----------|
| 80+ | **ADOPT** | All metrics met, no security issues, clear value add |
| 60-79 | **CONDITIONAL** | Partial metrics met, minor issues, needs config tweaks |
| 40-59 | **EVALUATE** | Mixed results, may work for specific use cases only |
| <40 | **REJECT** | Failed metrics, security concerns, or redundant with existing tools |

---

## Contact

**Pilot Owner:** Claude AI (AI Architect)  
**Approval Authority:** Ariel Shapira  
**Created:** 2026-02-03
