# 🧠 Claude-Mem Pilot — Step-by-Step Install Guide

**Date:** February 5, 2026
**Time Required:** ~5 minutes human · 2-3 hours Claude Code autonomous
**Repo:** [spd-site-plan-dev](https://github.com/breverdbidder/spd-site-plan-dev)
**Branch:** [pilot/claude-mem](https://github.com/breverdbidder/spd-site-plan-dev/tree/pilot/claude-mem)
**Mission File:** [CLAUDE_MEM_PILOT_MISSION.md](https://github.com/breverdbidder/spd-site-plan-dev/blob/pilot/claude-mem/docs/claude-code-missions/CLAUDE_MEM_PILOT_MISSION.md)
**Plugin:** [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) (23,502 ⭐)
**Docs:** [docs.claude-mem.ai](https://docs.claude-mem.ai/introduction)

---

## Step 1: Open PowerShell

Right-click Windows Start → **Terminal (Admin)** or **PowerShell**

---

## Step 2: Clone & Checkout

Copy-paste this entire block:

```powershell
cd $HOME\Projects
git clone https://github.com/breverdbidder/spd-site-plan-dev.git
cd spd-site-plan-dev
git checkout pilot/claude-mem
```

> **Already cloned?** Just do:
> ```powershell
> cd $HOME\Projects\spd-site-plan-dev
> git fetch origin
> git checkout pilot/claude-mem
> git pull origin pilot/claude-mem
> ```

---

## Step 3: Launch Claude Code

```powershell
claude
```

---

## Step 4: Install Claude-Mem Plugin

Inside Claude Code, type these two commands one at a time:

```
/plugin marketplace add thedotmack/claude-mem
```

Wait for confirmation, then:

```
/plugin install claude-mem
```

---

## Step 5: Restart Claude Code

Type `/exit` to quit, then relaunch:

```powershell
claude
```

> Claude-Mem hooks activate on restart. You should see memory context loading.

---

## Step 6: Launch the Mission

Copy-paste this into Claude Code:

```
Read and execute the mission file at docs/claude-code-missions/CLAUDE_MEM_PILOT_MISSION.md — run all 7 phases autonomously with zero human input. Start with Phase 0 pre-flight and continue through Phase 7 commit & push. Report results when complete.
```

---

## Step 7: Walk Away

Claude Code will autonomously:

1. ✅ Pull BCPAO data for Bliss Palm Bay (Account 2835546)
2. ✅ Run real pipeline stages to generate meaningful observations
3. ✅ Make 3+ architectural decisions (triggers Observer AI capture)
4. ✅ Audit `.claude-mem/` for observation quality
5. ✅ Security scan for leaked credentials
6. ✅ Test cross-session memory recall
7. ✅ Generate `docs/claude-mem-pilot-results.md`
8. ✅ Commit and push everything to `pilot/claude-mem` branch

---

## Quick Reference Links

| Resource | Link |
|----------|------|
| **SPD Repo** | [github.com/breverdbidder/spd-site-plan-dev](https://github.com/breverdbidder/spd-site-plan-dev) |
| **Pilot Branch** | [pilot/claude-mem](https://github.com/breverdbidder/spd-site-plan-dev/tree/pilot/claude-mem) |
| **Mission File** | [CLAUDE_MEM_PILOT_MISSION.md](https://github.com/breverdbidder/spd-site-plan-dev/blob/pilot/claude-mem/docs/claude-code-missions/CLAUDE_MEM_PILOT_MISSION.md) |
| **Pilot Setup Doc** | [claude-mem-pilot-setup.md](https://github.com/breverdbidder/spd-site-plan-dev/blob/pilot/claude-mem/docs/claude-mem-pilot-setup.md) |
| **Pilot Plan** | [claude-mem-pilot.md](https://github.com/breverdbidder/spd-site-plan-dev/blob/pilot/claude-mem/docs/claude-mem-pilot.md) |
| **TODO (priority)** | [TODO.md](https://github.com/breverdbidder/spd-site-plan-dev/blob/pilot/claude-mem/TODO.md) |
| **Claude-Mem Plugin** | [github.com/thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) |
| **Claude-Mem Docs** | [docs.claude-mem.ai](https://docs.claude-mem.ai/introduction) |
| **Installation Guide** | [docs.claude-mem.ai/installation](https://docs.claude-mem.ai/installation) |
| **Search Tools** | [docs.claude-mem.ai/usage/search-tools](https://docs.claude-mem.ai/usage/search-tools) |
| **Web Viewer** | [localhost:37777](http://localhost:37777) (after install) |

---

## Troubleshooting

### Plugin install fails
```
/plugin marketplace list
```
If `thedotmack` not listed, manually add:
```
/plugin marketplace add https://github.com/thedotmack/claude-mem
```

### No observations after session
Check hooks are installed:
```bash
ls -la ~/.claude/hooks/
```
Check plugin is registered:
```bash
cat ~/.claude/plugins/installed.json
```

### Sensitive data in observations
Wrap sensitive commands with privacy tags:
```
<private>export SUPABASE_KEY=xxx</private>
```

### Web viewer not loading
```bash
# Check if worker is running
curl http://localhost:37777/api/health
```

---

## After Mission Completes

Come back to me (Claude AI chat) and say:

> **"Pull the Claude-Mem pilot results from the spd repo"**

I'll fetch `docs/claude-mem-pilot-results.md` from GitHub and we'll review together to make the ADOPT/EXTEND/REJECT/HYBRID decision.

---

**Total human effort: 4 commands + 1 paste = ~60 seconds**
**Total autonomous effort: 2-3 hours Claude Code**
