# Research Plan Template

Use this template when presenting a research plan to the user for approval.

---

# Research Plan: {{TOPIC}}

**Generated**: {{DATE}}
**Estimated Duration**: {{ITERATIONS}} research cycles

---

## Core Question

{{CORE_QUESTION}}

---

## Sub-Questions (Research DAG)

The research will be decomposed into the following tasks:

### Phase 1: Foundation
- [ ] P1: Intent Decomposition - {{DECOMPOSITION_DESCRIPTION}}

### Phase 2: Execution (Search + Read)
- [ ] E1: {{EXECUTION_TASK_1}} (DependsOn: P1)
- [ ] E2: {{EXECUTION_TASK_2}} (DependsOn: P1)
- [ ] E3: {{EXECUTION_TASK_3}} (DependsOn: P1)

### Phase 3: Conflict Resolution
- [ ] C1: {{CONFLICT_RESOLUTION}} (DependsOn: E1, E2, E3)

### Phase 4: Synthesis
- [ ] Final Report Generation (DependsOn: all above)

---

## Research Dimensions

| # | Dimension | Focus Areas |
|---|-----------|-------------|
| 1 | {{DIMENSION_1}} | {{FOCUS_1}} |
| 2 | {{DIMENSION_2}} | {{FOCUS_2}} |
| 3 | {{DIMENSION_3}} | {{FOCUS_3}} |

---

## Expected Source Types

- [ ] Academic papers / Peer-reviewed journals
- [ ] Official reports / Government publications
- [ ] Industry white papers / Technical documentation
- [ ] News articles / Industry analysis
- [ ] Company filings / Financial reports
- [ ] Other: {{OTHER_SOURCES}}

---

## Scope & Constraints

| Constraint | Value |
|------------|-------|
| Time Scope | {{TIME_SCOPE}} |
| Geographic Scope | {{GEO_SCOPE}} |
| Language | {{LANGUAGE}} |
| Source Requirements | {{SOURCE_REQUIREMENTS}} |
| Exclusions | {{EXCLUSIONS}} |

---

## Quality Criteria

The final report will:
- [ ] Answer the core question comprehensively
- [ ] Include citations for all factual claims
- [ ] Address all research dimensions
- [ ] Acknowledge conflicting information explicitly
- [ ] State confidence levels and limitations

---

## Resource Estimates

| Resource | Estimate |
|----------|----------|
| Research Iterations | ~{{ITERATIONS}} cycles |
| Expected Sources | {{SOURCE_COUNT}} documents |
| Output Length | {{OUTPUT_LENGTH}} words |

---

## Approval Required

**Do you approve this research plan?**

- **YES**: I will create `task.md` and begin the research process
- **NO**: Please explain what changes you'd like, or we can end here
- **MODIFY**: Tell me what to adjust in the plan
