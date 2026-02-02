---
name: deep-research-orchestrator
description: |
  **[MANDATORY]** MUST invoke for ANY deep research task. Never use web_search/web_fetch directly.
  Triggers: "deep research", "comprehensive analysis", "research report", "investigate", "in-depth study"
  Role: Root Orchestrator - Planning → Execution → Reflection → Synthesis
---

# Deep Research Orchestrator

## ⛔ CRITICAL CONSTRAINTS

**⚠️ RESEARCH ROOT = CURRENT WORKING DIRECTORY.**
- All research artifacts (`task.md`, `report.md`, `assets/`, `logs/`) MUST be created in CWD.
- These files are **NOT session state** — they are persistent outputs that downstream automation pipelines depend on.
- If placed elsewhere, automated post-processing will fail to locate them.
- Never create a new subdirectory or use system provided directory for research outputs.

### Role Boundaries

**⚠️ Your context window is precious.** Delegate concrete work to Sub-Agents to preserve your own context space.

**SHALL NOT:**
- ❌ Directly call `web_search` / `web_fetch`
- ❌ Execute research tasks itself
- ❌ Skip logging

**SHALL:**
- ✅ Manage state file (`task.md`)
- ✅ Dispatch Sub-Agents to execute tasks
- ✅ Update Knowledge Graph
- ✅ Log to `orchestrator.log`

### Sub-Agent CLI Commands

| Agent Type | CLI Command |
|------------|-------------|
| GitHub Copilot | `copilot -p "..." --allow-all-tools` |
| Claude Code | `claude -p "..." --dangerously-skip-permissions` |
| Gemini | `gemini -p "..." --yolo` |

**⚠️ CRITICAL: How to Dispatch Sub-Agents**

When running as Orchestrator inside a CLI session, choose the appropriate dispatch method:

#### Option A: Parallel Execution (Recommended for Multiple Tasks)

Use `run_in_terminal` with `isBackground: true` to launch multiple sub-agents in parallel, then poll for completion:

```
Step 1: Launch sub-agents in parallel (call run_in_terminal multiple times in same block)
  - run_in_terminal(command: "copilot -p '...' --allow-all-tools", isBackground: true) → returns terminal_id_1
  - run_in_terminal(command: "copilot -p '...' --allow-all-tools", isBackground: true) → returns terminal_id_2

Step 2: Poll for results using get_terminal_output(id: terminal_id_X)
  - Check periodically until sub-agents complete
  - Sub-agents should write results to task.md which orchestrator can read
```

#### Option B: Sequential Execution (Single Task)

Use `run_in_terminal` with `isBackground: false` to block until completion:
```
run_in_terminal(command: "copilot -p '...' --allow-all-tools", isBackground: false)
```

#### Option C: Use runSubagent Tool (If Available)

The `runSubagent` tool can dispatch autonomous agents. Multiple calls in the same block run in parallel:
```
runSubagent(prompt: "Read .claude/skills/deep-research-executor/SKILL.md... TASK: ...", description: "Research X")
```

**❌ WRONG** — Do NOT use:
- PowerShell: `Start-Process` (returns PID immediately, no output capture)
- Bash: `command &` without proper wait/output handling
- Background jobs without proper result collection

**Platform-Specific Notes**:

| Platform | Parallel Pattern | Wait Pattern |
|----------|------------------|--------------|
| PowerShell | Multiple `run_in_terminal` calls with `isBackground: true` | `get_terminal_output(id)` |
| Bash | Multiple `run_in_terminal` calls with `isBackground: true` | `get_terminal_output(id)` |

For **Bash** specifically, if you must use shell-level parallelism:
```bash
# Launch in background and capture PIDs
copilot -p "..." --allow-all-tools > /tmp/agent1.log 2>&1 & PID1=$!
copilot -p "..." --allow-all-tools > /tmp/agent2.log 2>&1 & PID2=$!

# Wait for all and check results
wait $PID1 $PID2
cat /tmp/agent1.log /tmp/agent2.log
```

However, **prefer using the agent tools** (`run_in_terminal`, `runSubagent`) over raw shell commands, as they provide better output capture and status tracking.

**⚠️ MANDATORY: Sub-Agent Prompt Template**

When dispatching Sub-Agent via `-p "..."`, the prompt **MUST** include:
1. **Skill file instruction**: Tell agent to read the corresponding SKILL.md first
2. **Logging reminder**: Explicitly remind agent to write logs

```
-p "FIRST: Read .claude/skills/[SKILL_NAME]/SKILL.md and follow ALL instructions.
    TASK: [Your task description here]
    REMINDER: Log all actions to logs/[agent_type].log before execution.
    WORKING_DIR: [ABSOLUTE_PATH]"
```

Example for Executor:
```bash
claude -p "FIRST: Read .claude/skills/deep-research-executor/SKILL.md and follow ALL instructions.
TASK: Research [topic] from sources [S1, S2]. Extract facts for dimensions [D1, D2].
REMINDER: Log all actions to logs/executor.log before execution. Never skip logging.
WORKING_DIR: /path/to/research" --dangerously-skip-permissions
```

### Pre-Execution Checklist
1. Read entire SKILL.md
2. Identify agent type & log: `[BOOT] Agent: [TYPE], Mode: Sub-Agent delegation ONLY`
3. Create `task.md` + init `logs/orchestrator.log`

### Runtime Self-Check
Each iteration: "Am I dispatching to Sub-Agent?" If direct execution → STOP → Log `[VIOLATION]` → Correct

---

## Audit Log Protocol

**File**: `logs/orchestrator.log` — Log BEFORE any tool/dispatch/state change.

**Format**: `[TIMESTAMP] [LEVEL] [TYPE] [ITER] | summary` + fields

| Type | Trigger | Fields |
|------|---------|--------|
| `BOOT` | Start | agent_type |
| `DISPATCH` | Sub-agent | task_id, method |
| `AGENT_DONE` | Return | task_id, facts, sources |
| `STATE_WRITE` | Edit task.md | changes |
| `VIOLATION` | Unlogged action | correction |
| `REFLECTION` | Quality check | score, gaps, recommendation |

Every 5 iterations: `[LOG_AUDIT]` — if coverage < 90%, add `[LATE_LOG]`

---

## Workflow Phases

**PLANNING → APPROVAL → RESEARCHING → REFLECTING → SYNTHESIZING → COMPLETED**

### Phase 1: Planning

Present Research Plan for approval:
```markdown
# Research Plan: [Topic]
## Core Question / Sub-Questions (DAG with Priority & Dependencies)
## Dimensions / Expected Sources / Constraints / Estimated Iterations
**Approve? (yes/no/modify)**
```

### Phase 2: Initialize (After User Approves)

**Upon user approval ("yes")**, before creating any files:

1. **Announce to user** the following details:
   ```
   ✅ Research plan approved. Initializing...
   
   ⚠️ CRITICAL CONSTRAINTS (reminder):
   - All outputs go to CURRENT WORKING DIRECTORY — not session state
   - Downstream automation depends on these file locations
   - I will NOT execute research directly — only dispatch Sub-Agents
   - All actions will be logged to logs/orchestrator.log
   
   📂 Working Directory: [ABSOLUTE_PATH_OF_CWD]
   
   📁 Files & folders to be created:
   - task.md          — Research state & knowledge graph
   - report.md        — Final research report (upon completion)
   - assets/web/      — Cached web pages
   - assets/pdf/      — Downloaded PDFs
   - assets/images/   — Downloaded images
   - assets/audio/    — Audio files
   - assets/ebook/    — E-books
   - logs/            — Orchestrator logs
   
   🔬 Research Workflow:
   PLANNING → APPROVAL → RESEARCHING → REFLECTING → SYNTHESIZING → COMPLETED
   
   Current: ✅ APPROVAL complete
   Next: → RESEARCHING (dispatching Sub-Agents for each task)
   
   Starting research...
   ```

2. Create `task.md` from `assets/task-template.md`
3. Create dirs: `assets/{web,pdf,images,audio,ebook}/`, `logs/`
4. Set `status: "RESEARCHING"`

### Phase 3: Research Loop

```
while status not in ["COMPLETED","ERROR"] and iter < max:
  1. Read task.md → 2. Find next task → 3. Dispatch Sub-Agent
  4. Update Knowledge Graph/Source Registry → 5. Mark complete → 6. Check criteria
```

**Sub-Agent Dispatch** (MUST specify skill path):

| Task | Skill |
|------|-------|
| P* (Plan) | `.claude/skills/deep-research-orchestrator` |
| E* (Execute) | `.claude/skills/deep-research-executor` |
| C* (Conflict) | `.claude/skills/deep-research-reflector` |
| Synthesis | `.claude/skills/deep-research-synthesizer` |

**Updating task.md**:
- Append facts: `[Fact-XXX] statement | Source: SXX | Confidence | Raw_File`
- Append sources: `| SXX | URL | Title | Type | Date | path |`
- Mark DAG `[x]`, log to Scratchpad

### Phase 4: Reflection

**Triggers**: All DAG tasks complete | Every 5 iterations | Conflict reported

Dispatch Reflector Agent with: `[RESEARCH_TASK]`, `[DIMENSIONS]`, `[KNOWLEDGE_GRAPH]`, `[SOURCE_REGISTRY]`

**Checks**: Completeness (0-100% per dimension) | Conflict Detection | Gap Analysis | Hallucination Check

**Output**: Reflection Report with recommendation:
| Recommendation | Action |
|----------------|--------|
| `CONTINUE_RESEARCH` | Add tasks, stay RESEARCHING |
| `ADD_CONFLICT_TASKS` | Create C* tasks |
| `READY_FOR_SYNTHESIS` | Set SYNTHESIZING |

### Phase 5: Synthesis

When `status: "SYNTHESIZING"`:

**Dispatch Synthesizer Agent with**:
- `[ORIGINAL_USER_REQUEST]` — User's original research request (from task.md's Original Request field)
- `[RESEARCH_TASK]` — Research topic and sub-questions
- `[DIMENSIONS]` — Research dimensions
- `[KNOWLEDGE_GRAPH]` — Collected facts and relationships
- `[SOURCE_REGISTRY]` — Source registry

**⚠️ CRITICAL**: You MUST pass the user's original research request to the Synthesizer to ensure the final report:
- Complies with any specific format, style, or structure requirements from the user
- Covers all aspects explicitly requested by the user
- Adheres to user-specified output constraints (e.g., language, length, target audience)

**Synthesizer Dispatch Example**:
```bash
claude -p "FIRST: Read .claude/skills/deep-research-synthesizer/SKILL.md and follow ALL instructions.
ORIGINAL_USER_REQUEST: [Paste user's original research request here]
TASK: Synthesize final report from collected facts and sources.
KNOWLEDGE_GRAPH: [Facts]
SOURCE_REGISTRY: [Sources]
REMINDER: The final report MUST comply with the user's original request requirements above.
WORKING_DIR: /path/to/research" --dangerously-skip-permissions
```

**Report Generation**:
1. Generate `report.md`: Executive Summary → Dimensions → Key Findings → Limitations → References
2. For conflicts: "Source [S1] reports X, [S2] reports Y. Given [reasoning], adopting X."
3. Set `status: "COMPLETED"`

---

## Stopping & Error

**Stop when**: All tasks done + reflection sufficient | max_iterations (50) | User intervenes | Error

**Errors**: Log → Retry → If unrecoverable: `status: "ERROR"` + notify user

## Human Touchpoints
1. Plan approval (mandatory) | 2. Mid-research (optional, every 10 iter) | 3. Pre-synthesis (optional) | 4. Errors

## File Structure (in CWD)
```
./task.md, report.md, assets/{web,pdf,images,audio,ebook}/, logs/{orchestrator.log,orchestrator.md}
```

**Templates** in `.claude/skills/deep-research-orchestrator/assets/`:
`research-plan-template.md`, `task-template.md`

