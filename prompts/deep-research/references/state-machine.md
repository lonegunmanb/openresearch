# State Machine Reference

This document details the state transitions and data structures used in the deep research orchestration.

## State Diagram

```
                    ┌──────────────────┐
                    │   User Request   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    PLANNING      │
                    │  (Generate Plan) │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
              ┌─────│  User Approval?  │─────┐
              │     └──────────────────┘     │
              │ No                      Yes  │
              ▼                              ▼
    ┌──────────────────┐           ┌──────────────────┐
    │   Modify Plan    │           │  Create task.md  │
    │   or Abort       │           │  RESEARCHING     │
    └──────────────────┘           └────────┬─────────┘
                                            │
              ┌─────────────────────────────┤
              │                             │
              ▼                             ▼
    ┌──────────────────┐           ┌──────────────────┐
    │  Dispatch Task   │◄──────────│  Find Next Task  │
    │  to Sub-Agent    │           │  from DAG        │
    └────────┬─────────┘           └──────────────────┘
             │                              ▲
             ▼                              │
    ┌──────────────────┐                    │
    │  Update State    │────────────────────┘
    │  - Knowledge Graph                    │
    │  - Source Registry                    │
    │  - DAG Status                         │
    └────────┬─────────┘                    │
             │                              │
             ▼                              │
    ┌──────────────────┐                    │
    │  All Tasks Done? │──── No ────────────┘
    └────────┬─────────┘
             │ Yes
             ▼
    ┌──────────────────┐
    │   REFLECTING     │
    │  (Quality Check) │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  Gaps Found?     │──── Yes ───┐
    └────────┬─────────┘            │
             │ No                   │
             ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐
    │  SYNTHESIZING    │   │  Add New Tasks   │
    │  (Write Report)  │   │  RESEARCHING     │
    └────────┬─────────┘   └──────────────────┘
             │
             ▼
    ┌──────────────────┐
    │    COMPLETED     │
    │  (report.md)     │
    └──────────────────┘
```

## Status Values

| Status | Description | Next Actions |
|--------|-------------|--------------|
| `PLANNING` | Initial plan being generated | Present plan to user |
| `RESEARCHING` | Active information gathering | Execute DAG tasks |
| `REFLECTING` | Evaluating completeness | Check gaps, conflicts |
| `SYNTHESIZING` | Writing final report | Generate report.md |
| `COMPLETED` | Research finished | Deliver to user |
| `ERROR` | Unrecoverable error | Notify user, await intervention |

## task.md Data Structures

### YAML Frontmatter

```yaml
---
mission_id: "DR-YYYYMMDD-NNN"      # Unique identifier
created_at: "YYYY-MM-DDTHH:MM:SSZ" # ISO 8601 timestamp
status: "PLANNING"                  # Current state
topic: "Research question"          # Main topic
iteration: 0                        # Current loop count
max_iterations: 50                  # Safety limit
cost_tracking:
  total_tokens: 0                   # Token usage estimate
  tools_used: 0                     # MCP tool calls count
---
```

### DAG Task Format

```markdown
- [ ] [ID]: [Type]: [Description] (Status: [STATUS], DependsOn: [IDs])
```

**ID Prefixes**:
- `P*`: Planning tasks (decomposition, restructuring)
- `S*`: Search tasks (web search, source discovery)
- `R*`: Read tasks (deep analysis, extraction)
- `C*`: Conflict resolution tasks

**Status Values**:
- `PENDING`: Ready to execute (dependencies met)
- `BLOCKED`: Waiting for dependencies
- `IN_PROGRESS`: Currently being executed
- `COMPLETED`: Task finished (marked with [x])
- `FAILED`: Execution failed

### Knowledge Graph Entry

```markdown
[Fact-NNN] [Factual statement]
- Source: [SXX]
- Confidence: High/Medium/Low
- Raw_File: assets/[type]/[filename]
- Extracted: [YYYY-MM-DD]
```

**Confidence Levels**:
- `High`: Official source, verifiable, multiple confirmations
- `Medium`: Reputable source, single confirmation
- `Low`: Unverified, needs cross-reference

### Source Registry Entry

| Column | Description | Example |
|--------|-------------|---------|
| ID | Unique source ID | S01, S02 |
| URL | Original URL | https://... |
| Title | Document title | "Toyota Technical Review 2024" |
| Type | Content type | PDF, HTML, Report, Paper |
| Access Date | When accessed | 2024-05-20 |
| Local Path | Archived location | assets/pdf/s01.pdf |

## Transition Rules

### PLANNING -> RESEARCHING
- **Condition**: User approves plan
- **Actions**: 
  - Create task.md from template
  - Populate DAG with approved tasks
  - Set status to "RESEARCHING"

### RESEARCHING -> REFLECTING
- **Condition**: All current DAG tasks marked [x]
- **Actions**:
  - Set status to "REFLECTING"
  - Invoke Reflector Agent

### REFLECTING -> RESEARCHING
- **Condition**: Gaps or conflicts detected
- **Actions**:
  - Add new tasks to DAG
  - Set status back to "RESEARCHING"

### REFLECTING -> SYNTHESIZING
- **Condition**: Completeness confirmed, no critical gaps
- **Actions**:
  - Set status to "SYNTHESIZING"
  - Invoke Synthesizer Agent

### SYNTHESIZING -> COMPLETED
- **Condition**: report.md generated successfully
- **Actions**:
  - Set status to "COMPLETED"
  - Notify user

### Any -> ERROR
- **Condition**: Unrecoverable error
- **Actions**:
  - Log error to Scratchpad
  - Set status to "ERROR"
  - Notify user

## Iteration Limits

| Checkpoint | Action |
|------------|--------|
| Every 5 iterations | Log progress to Scratchpad |
| Every 10 iterations | Optional user check-in |
| At max_iterations | Force transition to SYNTHESIZING or ERROR |

## Recovery Patterns

### Task Failure Recovery
1. Log failure in Scratchpad AND orchestrator.log
2. Retry with alternative approach (different query, different source)
3. If retry fails, mark task FAILED and add compensating task
4. If critical task, escalate to user

### State Corruption Recovery
1. Read last valid iteration from Scratchpad
2. Rollback DAG status to last consistent state
3. Continue from checkpoint

### Context Overflow Prevention
1. Summarize completed facts periodically
2. Archive detailed logs to external files
3. Keep task.md focused on active state

## Audit Log (orchestrator.log)

All orchestrator decisions and actions are logged to `logs/orchestrator.log` for:
- **Traceability**: Understand how decisions were made
- **Debugging**: Identify where things went wrong
- **Improvement**: Analyze patterns for future optimization

### What Must Be Logged

| Event | Required Fields |
|-------|-----------------|
| Plan generation | Topic, dimensions, estimated iterations |
| User approval | Response, modifications if any |
| Task dispatch | Task ID, agent type, parameters |
| Sub-agent result | Facts extracted, sources found, files saved |
| State transition | From status, to status, reason |
| Errors | Error type, message, recovery action |
| Completion | Total iterations, sources used, facts collected |

### Log File Location

```
logs/
├── orchestrator.log    # Main audit trail (append-only)
└── orchestrator.md     # Detailed reasoning (thought stream)
```
