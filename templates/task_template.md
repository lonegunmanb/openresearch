---
mission_id: "DR-{{DATE}}-001"
created_at: "{{TIMESTAMP}}"
status: "PLANNING"
topic: "{{TOPIC}}"
iteration: 0
max_iterations: 50
cost_tracking:
  total_tokens: 0
  tools_used: 0
---

# 1. Research Objectives & Constraints (Directives)

> Read-only section defining user's original requirements and boundary conditions.

- **Core Question**: {{TOPIC}}
- **Output Format**: Deep analysis report (Markdown)
- **Constraints**: 
  - Must cite verifiable data sources
  - No unsourced information allowed
  - Prioritize authoritative sources (official, academic, government)

---

# 2. Execution Plan (DAG Scheduler)

> Dynamically updated section. Root Agent dispatches sub-tasks based on this list.

- [ ] P1: Intent Decomposition - Break down core question into executable sub-tasks (Status: PENDING)

---

# 3. Knowledge Graph

> Structured fact storage. All sub-agent search results must be appended here.

## 3.1 Dimension One

(To be populated...)

---

# 4. Source Registry

> Single source of truth index for generating citations.

| ID | URL | Title | Type | Access Date | Local Path |
|----|-----|-------|------|-------------|------------|
| - | - | - | - | - | - |

---

# 5. Scratchpad

> Agent's chain-of-thought cache. For recording current confusion, discovered contradictions, or strategy adjustments.

- **Iteration 0**: Task initialized, awaiting planning...

---

# 6. Final Report

> To be completed by Synthesizer Agent

(To be generated...)
