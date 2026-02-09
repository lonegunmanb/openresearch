# OpenResearch: Deep Research Multi-Agent System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpenResearch is an AI-powered autonomous research system that orchestrates multiple specialized agents to conduct comprehensive research on complex topics. Given a research question, it automatically searches the web, collects information, detects conflicts, and generates a well-cited report.

> ⚠️ **Disclaimer**: This project is a **personal learning project** created solely to explore the principles of Deep Research and AI agent workflows. It is **NOT intended for commercial use**.
>
> This project references certain websites (such as Z-Library and Sci-Hub) purely as a means to simplify information acquisition and verify the feasibility of algorithms and workflows. **This does not constitute endorsement of copyright infringement.** 
>
> **Please use this project for learning and research purposes only.**

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Agent Roles](#agent-roles)
- [How the Executor Collects Information](#how-the-executor-collects-information)
- [Dynamic Top-K Saturation Detection](#dynamic-top-k-saturation-detection)
- [How the Reflector Detects Conflicts](#how-the-reflector-detects-conflicts)
- [Conflict Resolution with Evidence Weighting](#conflict-resolution-with-evidence-weighting)
- [Closed-World Assumption: Eliminating Hallucinations](#closed-world-assumption-eliminating-hallucinations)
- [File Structure](#file-structure)
- [Usage](#usage)

---

## Prerequisites

Before using OpenResearch, ensure you have the following installed:

### Required

| Dependency | Version | Description |
|------------|---------|-------------|
| **Go** | ≥ 1.21 | Required for building and running the orchestrator |
| **Python** | ≥ 3.10 | Required for Playwright browser automation |
| **Node.js** | ≥ 18.0 | Playwright runtime dependency |
| **Playwright** | Latest | Browser automation framework |

Install Playwright and its browser dependencies:

```bash
pip install playwright
playwright install --with-deps
```

### AI Agent CLI (One of the following)

| CLI Tool | Recommendation | Notes |
|----------|----------------|-------|
| **GitHub Copilot CLI** | ✅ **Recommended** | Fully tested and verified |
| Gemini CLI | ⚠️ Experimental | Not fully tested |
| Claude Code | ⚠️ Experimental | Not fully tested |

> **Note**: We recommend using **GitHub Copilot CLI** as it has been thoroughly tested with this system. The other CLI tools (Gemini CLI and Claude Code) should work in theory but have not been extensively tested.

### Pre-Research Setup (Important!)

> **💡 Tip**: Before starting a research session, it is highly recommended to manually launch the CLI agent in your project directory and have the agent pre-login to key websites. This ensures smooth access during automated research.

**Recommended sites to login:**

| Site | URL | Purpose |
|------|-----|--------|
| Google | `google.com` | Web search |
| Google Scholar | `scholar.google.com` | Academic papers |
| YouTube | `youtube.com` | Video transcripts |
| NotebookLM | `notebooklm.google.com` | Ebook analysis |
| Z-Library | `z-lib.io` | Ebook downloads |
| Sci-Hub | `sci-hub.ru` | Academic paper access |

```bash
# Example: Start the agent and login to sites
cd /path/to/your/research/project
copilot

# Then ask the agent:
# "Please open a browser and login to google.com, youtube.com, and notebooklm.google.com"
```

> ⚠️ **Security Warning**: Your login information is saved in the `browser_profile` and `tmp` directories under the current project folder. **Do not leak these directories!** It is recommended to delete them after completing your research.

---

## Architecture Overview

The system employs a **multi-agent pipeline architecture** with four distinct phases:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR                                       │
│         Manages state transitions, dispatches agents, monitors progress         │
└───────────────┬───────────────┬───────────────┬───────────────┬─────────────────┘
                │               │               │               │
                ▼               ▼               ▼               ▼
         ┌──────────┐    ┌──────────────┐  ┌───────────┐  ┌─────────────┐
         │ PLANNER  │ →  │ RESEARCH-    │→ │ REFLECTOR │→ │ SYNTHESIZER │
         │          │    │ SUPERVISOR   │  │           │  │             │
         │ Creates  │    │              │  │ Quality   │  │ Generates   │
         │ task.md  │    │ Dispatches   │  │ Gate      │  │ report.md   │
         │ with DAG │    │ Executors    │  │           │  │             │
         └──────────┘    └──────────────┘  └───────────┘  └─────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌──────────┐┌──────────┐┌──────────┐
              │Executor  ││Executor  ││Executor  │
              │   E1     ││   E2     ││   E3     │
              └──────────┘└──────────┘└──────────┘
```

### Workflow Phases

| Phase | Agent | Input | Output |
|-------|-------|-------|--------|
| **1. Planning** | Planner | User's research question | `task.md` with research DAG |
| **2. Researching** | Research-Supervisor + Executors | `task.md` | Populated Knowledge Graph |
| **3. Reflecting** | Reflector | Knowledge Graph | Decision: CONTINUE / SYNTHESIZE / ERROR |
| **4. Synthesizing** | Synthesizer | Complete Knowledge Graph | `report.md` |

---

## Agent Roles

### Planner
- Breaks down the research question into sub-questions forming a **Directed Acyclic Graph (DAG)**
- Defines research dimensions and expected source types
- Creates `task.md` with the complete research plan

### Research-Supervisor
- Manages the execution phase
- Dispatches multiple Executor agents in parallel
- Collects results and updates `task.md`

### Executor
- Performs actual web searches using browser automation (Playwright)
- Downloads and archives sources to `assets/`
- Extracts facts with source citations
- Uses **Dynamic Top-K** algorithm to determine when information is saturated

### Reflector
- Evaluates research completeness
- Detects conflicts between collected facts
- Performs hallucination checks (source traceability)
- Decides whether more research is needed

### Synthesizer
- Transforms the Knowledge Graph into a coherent report
- Operates under the **Closed-World Assumption**
- Ensures every claim has a source citation

---

## How the Executor Collects Information

The Executor uses a **hierarchical delegation model** with iterative batch processing:

### Search Method Priority (Fallback Chain)

```
Priority 1: MCP Playwright + Google/Bing/Scholar
     │
     │ On failure (CAPTCHA, blocked, timeout)
     ▼
Priority 2: Serper-Search API → Then visit URLs with Playwright
     │
     │ On failure
     ▼
Priority 3: Built-in web_search tool (last resort)
```

### Execution Cycle

Each Executor runs in iterative batches:

```
┌─────────────────────────────────────────────────────────────┐
│                    BATCH N: PLAN PHASE                       │
│  1. Construct 3-5 high-precision search queries              │
│  2. Determine k value (documents per query)                  │
│  3. Identify sources requiring specialist agents             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   BATCH N: DISPATCH PHASE                    │
│  1. Spawn Sub-Executor for web search                        │
│  2. Spawn Specialists for complex retrieval:                 │
│     - YouTube Transcript Agent                               │
│     - Paper Downloader Agent                                 │
│     - Ebook + NotebookLM Agent                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BATCH N: EVALUATE PHASE                     │
│  1. Aggregate facts from all sub-agents                      │
│  2. Deduplicate and validate sources                         │
│  3. Check saturation signals (see below)                     │
│  4. Decision: STOP or CONTINUE to next batch                 │
└─────────────────────────────────────────────────────────────┘
```

### Resource Storage

All downloaded content is archived locally for traceability:

| Content Type | Storage Path |
|--------------|--------------|
| Web pages | `assets/web/` |
| PDF documents | `assets/pdf/` |
| Academic papers | `assets/pdf/` |
| YouTube transcripts | `assets/transcripts/` |
| Images | `assets/images/` |
| Ebooks | `assets/ebook/` |

---

## Dynamic Top-K Saturation Detection

The Executor uses a **Dynamic Top-K algorithm** to determine when enough information has been collected. This prevents both under-researching (missing critical information) and over-researching (wasting resources on redundant data).

### Algorithm Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k_initial` | 5 | Initial batch size (documents per query) |
| `k_expand` | 10 | Expanded batch size when info insufficient |
| `min_batches` | 2 | Minimum batches before early stop allowed |
| `max_batches` | 10 | Maximum batches (hard limit) |
| `saturation_threshold` | 2 | Consecutive batches with no new info triggers stop |
| `min_tier1_sources` | 3 | Minimum authoritative sources required |

### Saturation Detection Logic

```python
saturation_counter = 0

for batch in range(1, max_batches + 1):
    results = execute_batch(k=k_initial if batch <= 2 else k_expand)
    
    new_relevant_info = evaluate_results(results)
    
    if new_relevant_info:
        saturation_counter = 0  # Reset counter
    else:
        saturation_counter += 1  # Increment counter
    
    # Check ALL stop criteria
    if (batch >= min_batches and
        saturation_counter >= saturation_threshold and
        all_dimensions_covered() and
        tier1_sources >= min_tier1_sources):
        break  # Information saturated
```

### What Counts as "New Relevant Info"?

| New Info (resets counter) | Not New Info (increments counter) |
|---------------------------|-----------------------------------|
| Facts answering uncovered dimensions | Redundant facts already captured |
| Quantitative data not yet captured | Sources repeating previous information |
| New authoritative source | Off-topic or low-quality results only |
| Contradicting/refining existing facts | Duplicate content from same source |

### Dynamic K Adjustment

```
Batch 1-2: k = k_initial (5 documents)
           Establishing baseline knowledge

Batch 3+:  IF new_info_found:
               k = k_initial (continue normal pace)
           ELSE:
               k = k_expand (10 documents, cast wider net)
```

---

## How the Reflector Detects Conflicts

The Reflector is the **quality gate** between research and synthesis. It performs five mandatory evaluation phases:

### Evaluation Phases

1. **Completeness Check** - Are all research dimensions adequately covered?
2. **Conflict Detection** - Do any facts contradict each other?
3. **Hallucination Check** - Does every fact have a valid source?
4. **Gap Analysis** - What critical information is still missing?
5. **Quality Assessment** - Overall scoring of research quality

### Conflict Detection Process

The Reflector scans the Knowledge Graph for contradictory information:

```markdown
### Detected Conflicts

| ID | Topic | Fact A | Fact B | Sources | Severity |
|----|-------|--------|--------|---------|----------|
| CONF-1 | Gold Price | [Fact-012]: Gold at $2,800/oz | [Fact-045]: Gold at $2,650/oz | S03 vs S07 | HIGH |
| CONF-2 | Fed Rate | [Fact-023]: 2 cuts expected | [Fact-067]: 3 cuts expected | S05 vs S12 | MEDIUM |
```

### Severity Classification

| Severity | Criteria | Action |
|----------|----------|--------|
| **HIGH** | Core claims contradict, affects main conclusions | Create C* conflict resolution task |
| **MEDIUM** | Secondary claims differ | Mark for synthesis with suggested framing |
| **LOW** | Minor discrepancies | Acknowledge briefly in report |

---

## Conflict Resolution with Evidence Weighting

When conflicts are detected, the Reflector uses an **Evidence Weighting Algorithm** to determine which source should be trusted.

### Weight Formula

```
W(source) = 0.6 × Authority + 0.4 × Freshness
```

### Authority Scores

| Source Type | Authority Score |
|-------------|-----------------|
| .gov / .edu / Official government | 1.0 |
| Academic journals (peer-reviewed) | 0.9 |
| Industry reports (WGC, IMF, BLS, etc.) | 0.8 |
| Reputable news media (Reuters, Bloomberg) | 0.7 |
| Blogs / Forums / Social media | 0.5 |

### Freshness Scores

| Recency | Freshness Score |
|---------|-----------------|
| Within research time scope | 1.0 |
| 1 year old | 0.8 |
| 2+ years old | 0.6 |
| Significantly outdated | 0.3 |

### Example Conflict Resolution

```markdown
**Conflict**: Gold price as of January 2026

Source S03 (World Gold Council Report, Jan 2026):
  - Authority: 0.8 (Industry Report)
  - Freshness: 1.0 (Current)
  - W(S03) = 0.6 × 0.8 + 0.4 × 1.0 = 0.88

Source S07 (Blog Post, Dec 2025):
  - Authority: 0.5 (Blog)
  - Freshness: 0.8 (1 month old)
  - W(S07) = 0.6 × 0.5 + 0.4 × 0.8 = 0.62

Resolution: Adopt S03 (W=0.88 > 0.62)
```

### C* Task Output Format

For HIGH severity conflicts, a dedicated C* task is created:

```markdown
# Conflict Resolution: C1

## Resolution Decision
**Adopted**: S03 (Fact-012)
**Reasoning**: World Gold Council is an authoritative industry source with 
               current data, while the blog post lacks institutional credibility.

## Report Presentation Guidance
> "Regarding gold prices in January 2026, the World Gold Council reports $2,800/oz [S03], 
> while some online sources cite $2,650/oz [S07]. This report adopts the WGC figure 
> given its institutional authority."
```

---

## Closed-World Assumption: Eliminating Hallucinations

The Synthesizer operates under a strict **Closed-World Assumption (CWA)** to prevent AI hallucinations from contaminating the research report.

### What is the Closed-World Assumption?

> **Only facts explicitly present in the Knowledge Graph are considered true.**
> 
> If something is not in the collected research data, it does not exist for the purposes of this report.

### Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYNTHESIZER CONSTRAINTS                       │
│                                                                  │
│  ✅ ALLOWED:                                                     │
│     - Use facts from Knowledge Graph                             │
│     - Quote sources from Source Registry                         │
│     - State logical inferences from collected facts              │
│                                                                  │
│  ❌ FORBIDDEN:                                                   │
│     - Use knowledge from LLM training data                       │
│     - Make claims without [SXX] citation                         │
│     - Fill gaps with "common knowledge"                          │
│     - Silently resolve contradictions                            │
└─────────────────────────────────────────────────────────────────┘
```

### Citation Index Construction

Before writing, the Synthesizer builds a citation index:

```markdown
| Fact ID | Statement | Source IDs | Verified |
|---------|-----------|------------|----------|
| Fact-001 | Fed held rates at 4.5% | [S01] | ✅ |
| Fact-002 | Gold reached $2,800/oz | [S03, S08] | ✅ |
| Fact-003 | [No source found] | - | ❌ ERROR |
```

**If any fact lacks a valid source → Synthesis is blocked until corrected.**

### Handling Missing Information

When the Knowledge Graph doesn't contain information needed to fully answer the research question:

```markdown
## Limitations & Caveats

1. **Data Gap**: No information was collected regarding [specific aspect].
   Current data does not cover this dimension.

2. **Single-Source Claim**: [Fact-045] relies only on [S12]. 
   Independent verification recommended.

3. **Temporal Scope**: Analysis primarily covers [time range].
   Earlier/later periods not researched.
```

### Citation Density Requirement

Every 1-2 sentences must have at least one source reference:

**✅ Correct:**
> The Federal Reserve maintained rates at 4.5% in January 2026 [S01], while signaling 
> potential cuts in Q2 [S03]. Market expectations currently price in 2-3 cuts by 
> year-end [S05][S08].

**❌ Incorrect:**
> The Fed is expected to cut rates this year as inflation cools down and the economy 
> shows signs of slowing.

---

## File Structure

```
openresearch/
├── task.md                    # Research state (DAG, Knowledge Graph, Sources)
├── report.md                  # Final synthesized report
├── input.md                   # User's research request
├── assets/
│   ├── web/                   # Archived web pages
│   ├── pdf/                   # Downloaded PDFs
│   ├── ebook/                 # Ebooks
│   ├── images/                # Screenshots
│   └── audio/                 # Audio files
├── logs/
│   ├── planner.log
│   ├── research_supervisor.log
│   ├── E1.log, E2.log, ...    # Executor logs
│   ├── E1_result.md, ...      # Executor results
│   ├── reflector.log
│   └── synthesizer.log
├── prompts/
│   └── deep-research/
│       ├── planner.md
│       ├── executor.md
│       ├── reflector.md
│       ├── synthesizer.md
│       └── research-supervisor.md
└── cmd/
    └── deepresearch/
        └── main.go            # Orchestrator
```

---

## Usage

Install `deepresearch` first by:

```bash
cd cmd/deepresearch
go install
```

```bash
# Basic usage with a research question
deepresearch --model claude-opus-4.5 -p "Research the impact of AI on software development jobs in 2025"

# Using an input file
deepresearch --model claude-opus-4.5 -f "input.md"

# Interactive mode (allows clarifying questions)
deepresearch --model claude-opus-4.5
```

---

## Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Source Traceability** | Every fact has [SXX] citation pointing to archived source |
| **Conflict Preservation** | Contradictions are never silently resolved; explicitly presented in report |
| **No Fabrication** | Closed-World Assumption prevents LLM hallucinations |
| **Physical Grounding** | All sources archived locally in `assets/` for audit |
| **Iterative Refinement** | Reflection loop ensures research quality before synthesis |

---

## License

MIT License - See [LICENSE](LICENSE) for details.
