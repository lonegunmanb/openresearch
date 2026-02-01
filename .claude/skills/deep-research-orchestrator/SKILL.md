---
name: deep-research-orchestrator
description: |
  Orchestrate autonomous deep research workflows following the CLI-Native Deep Research architecture. 
  Use this skill when users request to: (1) Start a deep research investigation on any topic, 
  (2) Conduct comprehensive multi-source analysis, (3) Generate research reports with proper citations,
  (4) Perform iterative information gathering with quality control. This skill acts as the Root 
  Orchestrator, managing the entire research lifecycle from planning to final report synthesis.
---

# Deep Research Orchestrator

## ⛔ CRITICAL CONSTRAINTS (MUST READ FIRST)

**Before executing ANY action, you MUST internalize these non-negotiable rules.**

### Role Boundaries

| Orchestrator SHALL | Orchestrator SHALL NOT |
|--------------------|------------------------|
| Manage state (`task.md`) | Directly call `web_search`, `web_fetch` |
| Dispatch Sub-Agents for research tasks | Execute any research/search tasks itself |
| Evaluate and aggregate Sub-Agent results | Download or read source documents directly |
| Update Knowledge Graph with returned facts | Make factual claims without Sub-Agent verification |
| Log all decisions to `orchestrator.log` | Skip logging or self-check steps |

### Sub-Agent Dispatch Requirements

**All research execution (E\* tasks) MUST be delegated to Sub-Agents.**

You MUST use the CLI sub-agent that matches your own agent type:

| If You Are | Use This CLI Command | Skill Reference |
|------------|---------------------|-----------------|
| **GitHub Copilot CLI** | `copilot -p "..." --allow-all-tools` | `github-copilot-subagent` |
| **Claude Code CLI** | `claude -p "..." --dangerously-skip-permissions` | `claude-subagent` |
| **Gemini CLI** | `gemini -p "..." --yolo` | `gemini-subagent` |

**How to determine your agent type:**
- Check your system prompt for identifiers like "GitHub Copilot CLI", "Claude", or "Gemini"
- If uncertain, ask the user to confirm which CLI agent you are running as

### Mandatory Pre-Execution Checklist

Before starting any research, you MUST:

- [ ] Read this entire SKILL.md (not just templates)
- [ ] Identify your agent type (Copilot/Claude/Gemini)
- [ ] Confirm understanding by logging to `orchestrator.log`:
  ```
  [BOOT] Skill loaded. Agent type: [YOUR_TYPE]
  Execution mode: Sub-Agent delegation via [CLI_COMMAND]
  Orchestrator role: State management and task dispatch ONLY.
  ```
- [ ] Create `task.md` with proper DAG structure
- [ ] Initialize `logs/orchestrator.log`

### Runtime Self-Check

At each iteration of the research loop, before taking action:

1. **Ask yourself**: "Am I about to directly execute a research task, or dispatch to a Sub-Agent?"
2. **If direct execution** → **STOP** immediately and correct
3. **Log the check** to `orchestrator.log`:
   ```
   [SELF-CHECK] Iteration N: Dispatching E3 to Executor Sub-Agent via [CLI] ✓
   ```

### Violations

If you find yourself directly calling `web_search`, `web_fetch`, or similar research tools as Orchestrator:

1. **STOP** immediately
2. **Log** the violation: `[VIOLATION] Direct research execution attempted. Correcting...`
3. **Correct** by dispatching to appropriate Sub-Agent instead
4. **Continue** with proper flow

---

This skill implements a CLI-Native autonomous deep research system based on the "Text-as-State" 
philosophy, using `task.md` as a persistent state machine and coordinating multiple sub-agents 
through iterative loops.

## Audit Log Requirement

**Maintain `logs/orchestrator.log` throughout the entire research lifecycle.**

Every decision and action must be logged for traceability and post-hoc improvement.

### Log Entry Format

```
================================================================================
[YYYY-MM-DD HH:MM:SS] [ENTRY_TYPE] [ITERATION]
================================================================================

[Content]

--------------------------------------------------------------------------------
```

### Entry Types

| Type | When to Log | Example Content |
|------|-------------|-----------------|
| `PLAN_GENERATED` | After creating research plan | Plan summary, dimensions, estimated iterations |
| `PLAN_APPROVED` | User approves plan | User response, any modifications |
| `TASK_CREATED` | task.md initialized | Mission ID, initial DAG structure |
| `DECISION` | Any orchestration decision | "Chose to dispatch S1 because dependencies met" |
| `DISPATCH` | Sub-agent task delegation | Task ID, agent type, task description |
| `RESULT` | Sub-agent returns | Facts extracted, sources found, files saved |
| `STATE_UPDATE` | task.md modified | What changed: DAG status, Knowledge Graph additions |
| `REFLECTION` | Quality check performed | Completeness score, gaps found, conflicts detected |
| `STATUS_CHANGE` | State transition | "RESEARCHING -> REFLECTING", reason |
| `ERROR` | Any error encountered | Error description, recovery action taken |
| `COMPLETED` | Research finished | Final stats: iterations, sources, facts collected |

### Logging Commands

At the start of orchestration, initialize the log:

```
================================================================================
[2024-05-20 10:00:00] [ORCHESTRATOR_START] [0]
================================================================================

Mission: DR-20240520-001
Topic: [Research topic]
Max Iterations: 50

--------------------------------------------------------------------------------
```

Log every decision with reasoning:

```
================================================================================
[2024-05-20 10:05:32] [DECISION] [1]
================================================================================

Decision: Dispatch search task S1
Reasoning: P1 (intent decomposition) completed, S1 dependencies satisfied
Next Action: Invoke Executor Agent for web search on "sulfide electrolyte costs"

--------------------------------------------------------------------------------
```

### Log Best Practices

1. **Log before action**: Record decision before executing
2. **Log after result**: Record outcome immediately after receiving
3. **Include reasoning**: Always explain WHY, not just WHAT
4. **Preserve evidence chain**: Reference task IDs and fact IDs
5. **Log errors immediately**: Include stack traces if available

---

## Core Workflow

Deep research involves these phases:

1. **PLANNING**: Generate research plan for user review
2. **APPROVAL**: User reviews and approves/modifies the plan
3. **RESEARCHING**: Execute search and reading tasks via sub-agents
4. **REFLECTING**: Evaluate information completeness and quality
5. **SYNTHESIZING**: Generate the final report with citations
6. **COMPLETED**: Deliver `report.md` to user

## Phase 1: Planning (User Interaction Required)

When user requests deep research on a topic:

1. Analyze the research question to identify:
   - Core question and sub-questions
   - Required dimensions (e.g., technical, market, policy)
   - Potential authoritative sources
   - Constraints and scope boundaries

2. Present a **Research Plan** for user approval:

```markdown
# Research Plan: [Topic]

## Core Question
[Main research question]

## Sub-Questions (DAG)
- [ ] Q1: [First sub-question] (Priority: P1)
- [ ] Q2: [Second sub-question] (Priority: P1, DependsOn: Q1)
- [ ] Q3: [Third sub-question] (Priority: P2)
...

## Research Dimensions
1. [Dimension 1]: [What to investigate]
2. [Dimension 2]: [What to investigate]
...

## Expected Sources
- [ ] Academic papers / journals
- [ ] Official reports / white papers
- [ ] News and industry analysis
- [ ] Other: [specify]

## Constraints
- Time scope: [e.g., data from 2024 onwards]
- Geographic scope: [e.g., Global / China-US-Japan comparison]
- Source requirements: [e.g., no unverified social media]

## Estimated Iterations
~[N] research cycles

---
**Do you approve this plan? (yes/no/modify)**
```

3. Wait for user response:
   - **"yes"**: Proceed to create `task.md` and begin research
   - **"no"**: Ask for clarification or end task
   - **"modify"**: Update plan based on feedback and re-present

## Phase 2: Initialize Task State

After approval, create the research workspace:

1. Create `task.md` using the template at `assets/task-template.md`
2. Populate template variables with approved plan content:
   - `{{TOPIC}}`, `{{CORE_QUESTION}}` - from research plan
   - `{{DIMENSIONS_TABLE}}` - research dimensions as markdown table rows
   - `{{TIME_SCOPE}}`, `{{GEO_SCOPE}}`, etc. - from constraints
   - `{{DAG_SEARCH_TASKS}}`, `{{DAG_READ_TASKS}}` - from approved DAG
   - Set `status: "RESEARCHING"`
3. Create required directories if not exist:
   - `assets/web/` - HTML snapshots
   - `assets/pdf/` - Downloaded PDFs
   - `assets/images/` - Extracted charts
   - `assets/audio/` - Audio files
   - `assets/ebook/` - Other formats
   - `logs/` - Execution logs
4. Initialize `logs/orchestrator.log` with ORCHESTRATOR_START entry

## Phase 3: Research Loop (The Ralph Loop)

Execute the main research loop:

```
while status != "COMPLETED" and status != "ERROR" and iteration < max_iterations:
    1. Read task.md state
    2. Find next executable task (dependencies satisfied)
    3. Dispatch to appropriate sub-agent
    4. Update Knowledge Graph with findings
    5. Update Source Registry with citations
    6. Mark task complete in DAG
    7. Increment iteration counter
    8. Check stopping criteria
```

### Dispatching Sub-Agents

Based on task type, dispatch appropriate prompts. See `references/agent-prompts.md` for full prompts.

| Task Type | Agent Role | Key Responsibilities |
|-----------|------------|---------------------|
| Plan (P*) | Planner Agent | Task decomposition, DAG restructuring |
| Execute (E*) | Executor Agent | Search + Read cycle: discover sources, deep read, extract facts |
| Conflict (C*) | Reflector Agent | Cross-source comparison, credibility assessment |

### Updating task.md

After each sub-agent returns:

1. **Append** facts to Knowledge Graph (never overwrite):
   ```markdown
   [Fact-XXX] [Extracted fact statement]
   - Source: [SXX]
   - Confidence: High/Medium/Low
   - Raw_File: assets/[path]
   ```

2. **Append** to Source Registry:
   ```markdown
   | SXX | [URL] | [Title] | [Type] | [Date] | assets/[path] |
   ```

3. **Update** DAG task status:
   - Change `[ ]` to `[x]` for completed tasks
   - Add new tasks if gaps discovered

4. **Log** to Scratchpad:
   ```markdown
   - **Iteration N**: [What was done, what was found, what's next]
   ```

## Phase 4: Reflection Checkpoints

Trigger reflection when:
- All current DAG tasks marked complete
- Iteration count reaches checkpoint (every 5 iterations)
- Sub-agent reports conflicting information

### Dispatching Reflector Agent

When reflection is triggered, spawn a **Reflector Agent** to evaluate the current Knowledge Graph:

```bash
claude --print "You are a Reflector Agent for deep research quality control. Your task:

[RESEARCH_TASK]: <core research question>
[RESEARCH_DIMENSIONS]: <dimensions to cover>
[KNOWLEDGE_GRAPH]: <current accumulated facts from task.md>
[SOURCE_REGISTRY]: <current source list from task.md>

Instructions:
1. Read the entire Knowledge Graph
2. Compare against the Research Task and Dimensions
3. Perform the following checks:

COMPLETENESS CHECK:
- Can the core question be fully answered with current facts?
- Are all research dimensions adequately covered?
- Rate coverage: 0-100% for each dimension

CONFLICT DETECTION:
- Are there contradictory data points across sources?
- For each conflict: note Fact IDs, sources, and nature of contradiction

GAP ANALYSIS:
- What information is still missing?
- What questions remain unanswered?
- Suggest specific search queries to fill gaps

HALLUCINATION CHECK:
- Does every fact have a valid [SXX] source reference?
- Are there any claims without source attribution?

Return format:
## Reflection Report

### Completeness Score
- Overall: [X]%
- Dimension 1: [Y]% - [status: Sufficient/Insufficient]
- Dimension 2: [Z]% - [status: Sufficient/Insufficient]
...

### Conflicts Detected
| Fact A | Fact B | Nature of Conflict | Suggested Resolution |
|--------|--------|-------------------|---------------------|
| [Fact-XXX] | [Fact-YYY] | [description] | [recommendation] |

### Gaps Identified
1. [Gap description] - Suggested query: [search query]
2. [Gap description] - Suggested query: [search query]

### Hallucination Check
- Facts without sources: [list or 'None']
- Invalid source references: [list or 'None']

### Recommendation
- Status: CONTINUE_RESEARCH | ADD_CONFLICT_TASKS | READY_FOR_SYNTHESIS
- New tasks to add: [list of suggested DAG tasks]
- Reasoning: [explanation]
"
```

### Reflection Evaluation Criteria

The Reflector Agent evaluates:

1. **Completeness**: Can the core question be answered?
2. **Conflicts**: Are there contradictory data points?
3. **Gaps**: What information is still missing?
4. **Hallucination Check**: Do all facts have source IDs?

### Handling Reflector Results

Based on Reflector Agent's recommendation:

| Recommendation | Orchestrator Action |
|----------------|---------------------|
| `CONTINUE_RESEARCH` | Add suggested tasks to DAG, set `status: "RESEARCHING"` |
| `ADD_CONFLICT_TASKS` | Create conflict resolution tasks (C*), set `status: "RESEARCHING"` |
| `READY_FOR_SYNTHESIS` | Set `status: "SYNTHESIZING"` |

### Logging Reflection

Log the reflection outcome to `logs/orchestrator.log`:

```
================================================================================
[YYYY-MM-DD HH:MM:SS] [REFLECTION] [N]
================================================================================

Trigger: [All tasks complete / Checkpoint / Conflict reported]
Completeness: [X]%
Conflicts: [count]
Gaps: [count]
Hallucinations: [count]
Recommendation: [CONTINUE_RESEARCH / ADD_CONFLICT_TASKS / READY_FOR_SYNTHESIS]
Action Taken: [What orchestrator did in response]

--------------------------------------------------------------------------------
```

## Phase 5: Synthesis

When `status: "SYNTHESIZING"`:

1. Read entire Knowledge Graph
2. Generate `report.md` following this structure:
   ```markdown
   # [Research Topic]
   
   ## Executive Summary
   [Key findings in 3-5 sentences]
   
   ## 1. [Dimension 1]
   [Analysis with inline citations like [S1][S2]]
   
   ## 2. [Dimension 2]
   [Analysis with inline citations]
   
   ## Key Findings
   - Finding 1 [S1]
   - Finding 2 [S2][S3]
   
   ## Limitations & Caveats
   [Known gaps, conflicting data, confidence levels]
   
   ## References
   [Full citation list from Source Registry]
   ```

3. For conflicting data, explicitly state:
   > "Source [S1] reports X, while [S2] reports Y. Given [reasoning], this report adopts X."

4. Set `status: "COMPLETED"`
5. Present `report.md` to user

## Stopping Criteria

Research terminates when ANY of:
- All DAG tasks completed AND reflection confirms sufficiency
- `max_iterations` reached (default: 50)
- User manually intervenes
- Unrecoverable error encountered

## Error Handling

When errors occur:
1. Log error details to Scratchpad
2. Attempt recovery (retry, alternative source)
3. If unrecoverable, set `status: "ERROR"` and notify user

## Human-in-the-Loop Touchpoints

User intervention is expected at:
1. **Initial plan approval** (mandatory)
2. **Mid-research review** (optional, every 10 iterations)
3. **Pre-synthesis review** (optional, before final report)
4. **Error resolution** (when needed)

## File Structure Reference

```
project-root/
├── task.md                 # State machine (created from assets/task-template.md)
├── report.md               # Final output (created at synthesis)
├── assets/
│   ├── web/                # HTML snapshots
│   ├── pdf/                # Downloaded PDFs
│   ├── images/             # Extracted charts
│   ├── audio/              # Audio files
│   └── ebook/              # Other formats
└── logs/
    ├── orchestrator.log    # Orchestrator decisions & actions (audit trail)
    └── orchestrator.md     # Orchestrator reasoning log (thought stream)
```

### Skill Assets (Templates)

This skill provides templates in `.claude/skills/deep-research-orchestrator/assets/`:

| Template | Purpose |
|----------|---------|
| `research-plan-template.md` | Present research plan to user for approval |
| `task-template.md` | Create task.md state machine after approval |

## Quick Start Example

**User**: "I want to do deep research on solid-state battery supply chain bottlenecks in 2025"

**Orchestrator Response**:
1. Generate research plan covering:
   - Raw materials (lithium, sulfide electrolytes)
   - Manufacturing equipment
   - Production processes
   - Key players (Toyota, CATL, QuantumScape)
   - Regional comparison (China, US, Japan)
2. Present plan for approval
3. On approval, create task.md with DAG
4. Begin research loop
5. Deliver report.md with citations

