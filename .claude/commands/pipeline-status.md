---
description: Show current pipeline status for a project
allowed-tools:
  - Read
argument-hint: <project name>
---

# Pipeline Status Command

Display the 12-stage pipeline status for a project.

## Process

1. Load project from PROJECT_STATE.json
2. Check completion status of each stage
3. Identify current stage
4. List blockers and next actions

## Output

```
🏗️ Pipeline Status: $ARGUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CURRENT STAGE: [stage name] ([number]/12)

COMPLETED ✅
1. Discovery
2. Parcel Data
3. [etc...]

IN PROGRESS 🔄
[current stage number]. [stage name]
- [current tasks]
- [blockers if any]

PENDING ⏳
[remaining stages]

TIMELINE
- Started: [date]
- Current Stage Since: [date]
- Est. Completion: [date]

NEXT ACTION
- [specific next step]
```
