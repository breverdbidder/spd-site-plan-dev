# Claude-Mem Pilot Setup — SPD Site Plan Dev

**Pilot Start:** February 3, 2026  
**Repo:** `breverdbidder/spd-site-plan-dev`  
**Duration:** 2 weeks (through Feb 17, 2026)

---

## Installation Commands

Run in Claude Code session:

```bash
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

---

## Pilot Objectives

1. **Session Continuity** — Verify Claude Code retains architectural decisions across 7-hour sessions
2. **Decision Traceability** — Test "before/after context" on pipeline stage implementations
3. **Token Efficiency** — Measure overhead vs current context-boot-mcp-server approach
4. **Search Quality** — Validate file-scoped and concept-scoped queries

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Decisions captured | 100% of architectural choices | Manual audit of `.claude-mem/observations/` |
| Session recovery time | <30 seconds to full context | Time from `/plugin` load to productive work |
| Token overhead | <5% of session budget | Compare sessions with/without plugin |
| False positives | <10% irrelevant observations | Review observation relevance |

---

## 12-Stage Pipeline Test Matrix

Each SPD pipeline stage = 1 test case for Claude-Mem observation capture:

| Stage | Test Focus | Observation Types Expected |
|-------|------------|---------------------------|
| 1. Discovery | Initial data source decisions | 🔵 discovery, ⚖️ decision |
| 2. Scraping | Anti-detection strategy | ⚖️ decision, 🟣 feature |
| 3. Parcel Analysis | BCPAO integration | 🔵 discovery, 🔴 bugfix |
| 4. Zoning Lookup | GIS polygon matching | ⚖️ decision, 🟣 feature |
| 5. Setback Calc | Formula decisions | ⚖️ decision |
| 6. Constraints | Rule engine design | ⚖️ decision, 🟣 feature |
| 7. Buildable Area | Geometry calculations | 🔴 bugfix, 🟣 feature |
| 8. ML Feasibility | Model selection | ⚖️ decision, 🔵 discovery |
| 9. Report Gen | DOCX formatting | 🟣 feature |
| 10. Review Queue | Human-in-loop design | ⚖️ decision |
| 11. Approval | Workflow state machine | ⚖️ decision, 🔴 bugfix |
| 12. Archive | Storage strategy | ⚖️ decision |

---

## Comparison Protocol

Run parallel sessions to compare:

| Session Type | Memory System | Repo Branch |
|--------------|---------------|-------------|
| A (Control) | context-boot-mcp-server only | `main` |
| B (Test) | Claude-Mem + context-boot | `pilot/claude-mem` |

### Metrics to Compare

1. Time to recover context after session restart
2. Accuracy of "what happened last session" recall
3. Ability to answer "why did we make decision X?"
4. Token consumption per session

---

## Rollback Plan

If Claude-Mem causes issues:

```bash
/plugin uninstall claude-mem
rm -rf .claude-mem/
```

No schema changes, no external dependencies — clean removal.

---

## Escalation Triggers

Surface to Ariel if:
- Plugin crashes Claude Code session
- Observations leak sensitive data (API keys, credentials)
- Token overhead exceeds 10% of session budget
- Plugin conflicts with existing MCP servers

---

## Post-Pilot Decision Matrix

| Outcome | Action |
|---------|--------|
| All metrics pass | Roll out to `brevard-bidder-scraper` |
| Partial pass (>50%) | Extend pilot 1 week, document gaps |
| Fail (<50%) | Archive findings, continue with context-boot only |

---

## References

- [Claude-Mem GitHub](https://github.com/thedotmack/claude-mem)
- [Claude-Mem Docs](https://docs.claude-mem.ai/introduction)
- [SPD Pipeline Spec](./docs/pipeline-architecture.md)
- [Context Boot MCP](https://github.com/breverdbidder/context-boot-mcp-server)
