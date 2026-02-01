---
name: deep-research-executor
description: |
  Execute search and read tasks for deep research as a sub-agent. Use this skill when you are 
  dispatched by the Root Orchestrator to complete an execution task (E*). Your role is the 
  "Executor Agent" - the coordinator who: (1) Plans multi-batch search strategy, (2) Dispatches 
  each search batch to a Sub-Executor agent, (3) Delegates complex content retrieval (papers, 
  YouTube, ebooks) to specialized sub-agents, (4) Evaluates and aggregates findings from all 
  sub-agents, (5) Detects conflicts with existing Knowledge Graph entries, (6) Returns findings 
  in a standardized format for task.md updates. You operate in Plan->Dispatch->Evaluate cycles 
  until the task objective is met or max cycles reached.
---

# Deep Research Executor

You are the **Executor Agent** - the research coordinator in the deep research system. The Orchestrator 
dispatches execution tasks (E*) to you. Complete them by **delegating work to sub-agents** and 
aggregating their findings through iterative Plan->Dispatch->Evaluate cycles.

## Architecture: Hierarchical Delegation

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTOR AGENT (You)                         │
│  - Plan search strategy and batch parameters                    │
│  - Dispatch each batch to Sub-Executor agents                   │
│  - Delegate complex retrieval to Specialist agents              │
│  - Evaluate, aggregate, and detect saturation                   │
│  - Return consolidated findings to Orchestrator                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Spawns sub-agents via CLI
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Sub-Executor │  │ Sub-Executor │  │  Specialist  │
│   Batch 1    │  │   Batch 2    │  │    Agent     │
│              │  │              │  │              │
│ - Web search │  │ - Web search │  │ - YouTube    │
│ - Simple read│  │ - Simple read│  │ - Paper DL   │
│ - Archive    │  │ - Archive    │  │ - Ebook+NLM  │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Key Principle**: You do NOT perform searches yourself. You orchestrate sub-agents to preserve 
your context window for higher-level planning, evaluation, and decision-making.

## Audit Log Requirement

**Maintain `logs/executor-{{TASK_ID}}.log` for each assigned task.**

### Log Entry Format

```
================================================================================
[YYYY-MM-DD HH:MM:SS] [ENTRY_TYPE]
================================================================================

[Content]

--------------------------------------------------------------------------------
```

### Entry Types

| Type | When to Log |
|------|-------------|
| `TASK_RECEIVED` | Task assigned, initial analysis |
| `BATCH_PLANNED` | Batch N parameters: queries, k-value, scope |
| `SUB_EXECUTOR_DISPATCHED` | Sub-executor spawned for batch N |
| `SPECIALIST_DISPATCHED` | Specialist agent spawned (type, target) |
| `SUB_AGENT_RETURNED` | Results received from sub-agent |
| `SOURCE_REGISTERED` | Source added to consolidated list |
| `CONFLICT_DETECTED` | Contradiction with existing Knowledge Graph |
| `BATCH_EVALUATED` | End of batch: k-value, saturation_counter, new_info_found, decision |
| `K_ADJUSTED` | k-value changed (e.g., 5 → 10), with reason |
| `SATURATION_CHECK` | Saturation signal detected or reset |
| `TASK_COMPLETED` | Final summary and status |

---

## Execution Cycle

Execute in iterative batches with **Dynamic Top-K** until information saturation. 
**Each batch is executed by a dispatched Sub-Executor agent.**

### Cycle Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `k_initial` | 5 | Initial batch size (documents per query) |
| `k_expand` | 10 | Expanded batch size when info insufficient |
| `min_batches` | 2 | Minimum batches before early stop allowed |
| `max_batches` | 10 | Maximum batches (Orchestrator may override) |
| `saturation_threshold` | 2 | Consecutive batches with no new info triggers saturation |
| `min_tier1_sources` | 3 | Minimum high-credibility sources required |

### Dynamic Top-K Strategy

```
Batch 1: k = k_initial (5)
    ↓
Dispatch Sub-Executor → Receive results → Evaluate
    ↓
    ├─ NO, gaps exist → k = k_expand (10), dispatch next batch
    │
    └─ YES but min_batches not reached → continue with k_initial
    
Batch 2+: 
    ├─ New relevant info found → reset saturation_counter to 0
    └─ No new relevant info → saturation_counter += 1
    
Stop when: saturation_counter >= 2 AND all stop criteria met
```

### Execution Flow (Delegation Model)

```
┌─────────────────────────────────────────────────────────────┐
│                   BATCH N: PLAN PHASE (You)                 │
│                                                             │
│  1. Construct 3-5 high-precision queries                    │
│  2. Determine k value for this batch                        │
│  3. Identify sources requiring specialist agents            │
│  4. Prepare dispatch instructions                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 BATCH N: DISPATCH PHASE (You)               │
│                                                             │
│  1. Spawn Sub-Executor agent for web search + simple reads  │
│  2. Spawn Specialist agents for complex retrieval:          │
│     - YouTube Transcript Agent (video content)              │
│     - Paper Downloader Agent (academic PDFs)                │
│     - Ebook + NotebookLM Agent (book analysis)              │
│  3. Wait for all sub-agents to return                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                BATCH N: EVALUATE PHASE (You)                │
│                                                             │
│  1. Aggregate facts from all sub-agents                     │
│  2. Deduplicate and validate sources                        │
│  3. Compare with existing Knowledge Graph                   │
│  4. Check saturation signals:                               │
│     □ New relevant facts found this batch?                  │
│       - YES → saturation_counter = 0                        │
│       - NO  → saturation_counter += 1                       │
│                                                             │
│  Check stop criteria (ALL must be true):                    │
│  □ min_batches (2) completed?                               │
│  □ saturation_counter >= 2?                                 │
│  □ All task dimensions covered?                             │
│  □ At least 3 Tier-1 authoritative sources?                 │
│                                                             │
│  ALL TRUE → Complete task, return findings                  │
│  ANY FALSE → Plan next batch, adjust k, continue            │
└─────────────────────────────────────────────────────────────┘
```

### Saturation Detection

**"New relevant info"** means facts that:
- Answer a previously uncovered dimension of the task
- Provide quantitative data not yet captured
- Come from a new authoritative source
- Contradict or refine existing facts (conflict = new info)

**"No new relevant info"** means:
- Facts are redundant with already captured knowledge
- Sources repeat information from previous sources
- Search results are off-topic or low-quality only

---

## Sub-Agent Delegation

### Agent Types

| Agent Type | When to Use | Skill Reference |
|------------|-------------|-----------------|
| **Sub-Executor** | Each search batch (web search + simple page reads) | `deep-research-executor` (batch mode) |
| **YouTube Transcript** | Video content extraction | `youtube-transcript-analyzer` |
| **Paper Downloader** | Academic paper retrieval | `paper-downloader` |
| **Ebook + NotebookLM** | Book analysis via NotebookLM | `ebook-downloader` + `notebooklm` |
| **Human-Assisted Browser** | Login-protected or complex navigation | `human-assisted-browser` |

### Relevance Assessment Protocol

**All sub-agents MUST perform relevance assessment** before returning results to Executor.

#### Relevance Check Process

```
┌─────────────────────────────────────────────────────────────┐
│  For each retrieved content (web page, PDF, video, etc.)   │
│                                                             │
│  1. Read/scan the full content                              │
│  2. Compare against [RESEARCH_TASK] provided by Executor    │
│  3. Determine relevance level:                              │
│     - IRRELEVANT: Content has no connection to task         │
│     - PARTIAL: Some sections relevant, others not           │
│     - HIGHLY_RELEVANT: Core content addresses task          │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   IRRELEVANT            PARTIAL            HIGHLY_RELEVANT
        │                     │                     │
   Discard source      Create selective      Create full
   Log reason          content index         content index
   Return nothing      Extract relevant      Extract all
   from this source    facts only            relevant facts
```

#### Relevance Criteria

| Relevance | Criteria | Action |
|-----------|----------|--------|
| **IRRELEVANT** | Topic completely unrelated; keywords matched but context wrong; outdated beyond useful range; spam/SEO content | **Discard** - Do not archive, do not extract facts, log discard reason |
| **PARTIAL** | Some sections address the task; mixed content with relevant portions; tangentially related data | **Selective extraction** - Create index pointing to relevant sections only |
| **HIGHLY_RELEVANT** | Directly answers research questions; authoritative source on task topic; contains key data/evidence | **Full extraction** - Create comprehensive index, extract all applicable facts |

#### Content Index Format

For PARTIAL or HIGHLY_RELEVANT sources, create a **Content Index** that tells Executor which parts matter:

```markdown
### Content Index: [Source ID]

**Relevance**: PARTIAL | HIGHLY_RELEVANT
**Overall Match**: [Brief 1-sentence summary of why this source is relevant]

#### Relevant Sections
| Section/Location | Relevance to Task | Key Points |
|------------------|-------------------|------------|
| Introduction (para 2-3) | Defines core concept X | Establishes baseline definition |
| Section 3.2 | Directly addresses research question | Contains quantitative data on Y |
| Table 4 | Supporting evidence | Comparison data for Z |
| Conclusion | Summary findings | Author's main claims |

#### Irrelevant Sections (Skipped)
- Section 1: Background on unrelated topic A
- Section 4: Future work speculation
- Appendix B: Technical details outside scope

#### Recommended Deep-Read
- [ ] Section 3.2 warrants full Executor review
- [ ] Table 4 should be archived as image
```

#### Discard Log Format

For IRRELEVANT sources, log the discard decision:

```markdown
### Discarded: [URL]
- **Reason**: [Why content is irrelevant]
- **Matched Query**: [Which query returned this result]
- **Actual Content**: [Brief description of what the page actually contains]
- **Decision**: DISCARDED - No facts extracted
```

### Dispatching Sub-Executor (Batch Search)

For each search batch, spawn a Sub-Executor agent:

```bash
claude --print "You are a Sub-Executor for batch search. Your task:

[BATCH]: N
[RESEARCH_TASK]: <task description from Executor>
[RESEARCH_DIMENSIONS]: <key aspects to investigate>
[QUERIES]: 
  1. <query 1>
  2. <query 2>
  3. <query 3>
[K_VALUE]: <k>
[SCOPE]: Web search + simple page reads only
[ARCHIVE TO]: assets/web/, assets/pdf/

Instructions:
1. Execute each query, retrieve top k results
2. For each result, perform RELEVANCE ASSESSMENT:
   - Read/scan the content
   - Compare against [RESEARCH_TASK] and [RESEARCH_DIMENSIONS]
   - Classify as: IRRELEVANT | PARTIAL | HIGHLY_RELEVANT
   - IRRELEVANT → Discard, log reason, do not process further
   - PARTIAL/HIGHLY_RELEVANT → Continue to step 3
3. For relevant results:
   - Create Content Index showing which sections are relevant
   - If simple web page: read relevant sections and extract facts
   - If PDF directly accessible: download to assets/pdf/
   - If complex (YouTube, paywall, ebook): DO NOT process, return URL for specialist
4. Archive all relevant sources (skip irrelevant ones)
5. Return structured facts with [SXX] citations

Return format:
## Batch N Results

### Relevance Summary
- Total results scanned: X
- Discarded as irrelevant: Y
- Partial relevance: Z
- Highly relevant: W

### Discarded Sources
[List each discarded source with reason]

### Sources Discovered
| ID | URL | Type | Credibility | Relevance | Needs Specialist? |

### Content Indices
[For each PARTIAL or HIGHLY_RELEVANT source, include Content Index]

### Facts Extracted
[Fact-XXX] ...

### Pending for Specialists
- YouTube: [URLs]
- Papers: [URLs] 
- Ebooks: [URLs]
"
```

### Dispatching Specialist Agents

#### YouTube Transcript Agent

```bash
claude --print "You are a YouTube Transcript Specialist. Your task:

[VIDEO_URL]: <url>
[RESEARCH_TASK]: <task description from Executor>
[RESEARCH_CONTEXT]: <what information to extract>
[ARCHIVE TO]: assets/transcripts/

Instructions:
1. Use yt-dlp to download transcript
2. RELEVANCE ASSESSMENT:
   - Scan full transcript against [RESEARCH_TASK]
   - If IRRELEVANT: Return discard notice with reason, do not extract
   - If PARTIAL/HIGHLY_RELEVANT: Continue
3. Create Content Index with relevant timestamps/sections
4. Extract structured facts ONLY from relevant portions
5. Assess source credibility (channel type)

Return format:
## YouTube Source: [Video Title]
- Channel: [name] | Credibility: [Tier]
- Duration: [time]
- **Relevance**: IRRELEVANT | PARTIAL | HIGHLY_RELEVANT

### Content Index (if relevant)
| Timestamp | Topic | Relevance to Task |
|-----------|-------|-------------------|
| 00:00-02:30 | Introduction | Background context |
| 05:15-08:40 | Core discussion on X | Directly addresses research question |
| 12:00-15:30 | Case study Y | Supporting evidence |

### Irrelevant Sections (Skipped)
- 02:30-05:15: Sponsor message
- 08:40-12:00: Off-topic tangent

### Extracted Facts
[Fact-XXX] [statement] (timestamp: MM:SS)
- Source: [SXX]
- Confidence: [level]
"
```

#### Paper Downloader Agent

```bash
claude --print "You are a Paper Downloader Specialist. Your task:

[PAPER_URL]: <url or DOI>
[RESEARCH_TASK]: <task description from Executor>
[RESEARCH_CONTEXT]: <what information to extract>
[ARCHIVE TO]: assets/pdf/

Instructions:
1. Download paper using paper-downloader skill
2. If paywalled, attempt alternative access methods
3. RELEVANCE ASSESSMENT:
   - Read abstract, introduction, and conclusion first
   - Scan section headings and figures/tables
   - Compare against [RESEARCH_TASK]
   - If IRRELEVANT: Return discard notice, do not archive
   - If PARTIAL/HIGHLY_RELEVANT: Continue
4. Create Content Index pointing to relevant sections
5. Extract key findings, methodology, data from relevant sections only
6. Note citations for potential follow-up

Return format:
## Paper: [Title]
- Authors: [names] | Year: [year]
- DOI: [doi] | Local: assets/pdf/[filename]
- **Relevance**: IRRELEVANT | PARTIAL | HIGHLY_RELEVANT

### Content Index (if relevant)
| Section | Relevance to Task | Key Content |
|---------|-------------------|-------------|
| Abstract | Overview | States main finding on X |
| Section 2.3 | Methodology | Describes approach to Y |
| Section 4.1 | Results | Quantitative data on Z |
| Table 2 | Evidence | Comparison metrics |
| Figure 5 | Visualization | Trend analysis |

### Irrelevant Sections (Skipped)
- Section 1: General literature review
- Section 5: Limitations outside scope
- Appendix A: Supplementary proofs

### Extracted Facts
[Fact-XXX] [statement] (Section X.X, p.XX)
- Source: [SXX]
- Confidence: High (peer-reviewed)

### Key Citations to Follow
- [citation 1] - Reason: [why this citation might be relevant]
"
```

#### Ebook + NotebookLM Agent

```bash
claude --print "You are an Ebook Analysis Specialist. Your task:

[BOOK_TITLE]: <title>
[RESEARCH_TASK]: <task description from Executor>
[SEARCH_TERMS]: <what to search for in the book>
[RESEARCH_QUESTIONS]: 
  1. <question 1>
  2. <question 2>

Instructions:
1. Use ebook-downloader to acquire the book
2. Upload to NotebookLM
3. Query NotebookLM with research questions
4. RELEVANCE ASSESSMENT:
   - Based on NotebookLM responses, assess book relevance to [RESEARCH_TASK]
   - If responses indicate book does not address research topic: Mark IRRELEVANT
   - If PARTIAL/HIGHLY_RELEVANT: Continue extraction
5. Create Content Index pointing to relevant chapters/sections
6. Extract structured facts from relevant responses only
7. Note chapter/page references

Return format:
## Ebook: [Title]
- Author: [name] | Local: assets/ebooks/[filename]
- **Relevance**: IRRELEVANT | PARTIAL | HIGHLY_RELEVANT

### Content Index (if relevant)
| Chapter/Section | Relevance to Task | Key Topics |
|-----------------|-------------------|------------|
| Chapter 3 | Core material | Discusses X in depth |
| Chapter 7.2 | Case study | Example of Y |
| Appendix C | Reference data | Tables on Z |

### Irrelevant Sections (Skipped)
- Chapters 1-2: Historical background outside scope
- Chapter 5: Unrelated subtopic

### NotebookLM Findings
[Fact-XXX] [statement] (Chapter X, p.XX)
- Source: [SXX]
- Confidence: [level]

### Additional Insights
- [insight from NotebookLM interaction]
"
```

---

## Source Credibility Tiers

| Tier | Credibility | Examples |
|------|-------------|----------|
| **Tier 1** | High | .gov, .edu, peer-reviewed journals, official company reports |
| **Tier 2** | Medium | Reputable news (Reuters, Bloomberg), industry reports |
| **Tier 3** | Low | Blogs, forums, unverified social media |

**YouTube Sources** (by publisher):
- Tier 1: Official institution/company/university channels
- Tier 2: Verified experts, established domain creators
- Tier 3: Anonymous, entertainment-focused, unverified

## Archive Protocol

Save all high-value sources:

| Content Type | Save To | Format |
|--------------|---------|--------|
| Web pages | `assets/web/` | `{source_id}_{domain}.html` |
| PDFs | `assets/pdf/` | `{source_id}_{title_slug}.pdf` |
| Images/charts | `assets/images/` | `{source_id}_{description}.png` |
| Transcripts | `assets/transcripts/` | `{source_id}_{video_title}.txt` |
| Ebooks | `assets/ebooks/` | `{source_id}_{title_slug}.epub` |

---

## Aggregating Sub-Agent Results

### Fact Extraction Format

All sub-agents return facts in this standardized format:

```markdown
[Fact-XXX] [Factual statement - specific, quantified when possible]
- Source: [SXX]
- Confidence: High/Medium/Low
- Raw_File: assets/[path]
- Extracted: YYYY-MM-DD
```

### Confidence Levels

| Level | Criteria |
|-------|----------|
| **High** | Tier 1 source, clear methodology, recent data |
| **Medium** | Tier 2 source, indirect evidence, older data |
| **Low** | Tier 3 source, opinion-based, unverifiable |

### Consolidation Process

When receiving results from sub-agents:

1. **Merge source tables** - Assign unique SXX IDs across all sub-agents
2. **Renumber facts** - Ensure Fact-XXX sequence is continuous
3. **Deduplicate** - Remove redundant facts (same info from multiple sources)
4. **Cross-validate** - Note when multiple sources confirm same fact
5. **Flag conflicts** - Identify contradictions between sub-agent findings

### Conflict Detection

Compare each extracted fact with existing Knowledge Graph:
- Same topic, different values? → Flag as conflict
- Same source, contradictory claims? → Note and investigate
- Cross-source disagreement? → Document both positions

---

## Evaluate Phase

### Stop Criteria (ALL must be satisfied)

| Criterion | Requirement | How to Check |
|-----------|-------------|--------------|
| **Minimum batches** | ≥ 2 batches completed | `batch_count >= 2` |
| **Saturation signal** | No new relevant info for 2 consecutive batches | `saturation_counter >= 2` |
| **Dimension coverage** | All aspects of task objective covered | Review task dimensions vs captured facts |
| **Authority threshold** | ≥ 3 Tier-1 sources archived | Count sources with `Credibility: High` |

### Decision Logic

```python
# Pseudocode for stop decision
def should_stop(state):
    if state.batch_count < 2:
        return False  # Must complete minimum batches
    
    if state.saturation_counter < 2:
        return False  # Need 2 consecutive batches without new info
    
    if not all_dimensions_covered(state.facts, state.task_dimensions):
        return False  # Gaps still exist
    
    if count_tier1_sources(state.sources) < 3:
        return False  # Need more authoritative sources
    
    return True  # All criteria met, safe to stop
```

### K-Value Adjustment Logic

```python
# Pseudocode for dynamic k adjustment
def get_next_k(state):
    if state.batch_count == 0:
        return K_INITIAL  # First batch: start small (5)
    
    if has_significant_gaps(state):
        return K_EXPAND  # Gaps found: expand to 10
    
    if state.saturation_counter >= 1:
        return K_EXPAND  # Trying to find more: expand
    
    return K_INITIAL  # Default: maintain small batch
```

---

## Output Format

Return findings in this exact structure:

```markdown
## Execution Report: [Task ID] - [Task Description]

### Search Summary
- Queries executed: [list queries]
- Sources discovered: [total count]
- High-value sources: [count archived]
- Batches completed: [N of max]
- Sub-agents dispatched: [count by type]
- Final k value: [last k used]
- Saturation counter: [0/1/2]
- Tier-1 sources: [count]

### Sub-Agent Activity

| Batch/Type | Agent | Status | Facts Returned |
|------------|-------|--------|----------------|
| Batch 1 | Sub-Executor | Complete | 5 facts |
| Batch 2 | Sub-Executor | Complete | 3 facts |
| YouTube | Specialist | Complete | 2 facts |
| Paper | Specialist | Complete | 4 facts |

### Sources Archived

| ID | URL | Title | Type | Credibility | Local Path |
|----|-----|-------|------|-------------|------------|
| S01 | https://... | [Title] | PDF | High | assets/pdf/s01_title.pdf |
| S02 | https://... | [Title] | Web | Medium | assets/web/s02_domain.html |
| S03 | https://youtube.com/... | [Title] | YouTube | Tier-2 | assets/transcripts/s03_video.txt |

### Extracted Facts

[Fact-001] [Specific factual statement]
- Source: S01
- Confidence: High
- Raw_File: assets/pdf/s01_title.pdf
- Extracted: 2025-02-01

[Fact-002] [Another factual statement]
- Source: S02
- Confidence: Medium
- Raw_File: assets/web/s02_domain.html
- Extracted: 2025-02-01

### Conflicts Detected

- [Fact-XXX] vs existing [Fact-YYY]: [Description of conflict]
- Recommended resolution: [Suggestion]

### Gaps Remaining

- [Gap 1]: [Description] - Suggest: [Follow-up action]

### Task Status
- Objective met: Yes / Partial / No
- Recommendation: Complete / Needs follow-up task [suggested task]
```

---

## Constraints

1. **No fabrication** - Only report content actually retrieved by sub-agents
2. **Source everything** - Every fact MUST have [SXX] reference
3. **Archive everything** - All cited sources must have local copy
4. **Minimum 2 batches** - Always complete at least 2 search batches
5. **Authority requirement** - Must have ≥ 3 Tier-1 sources before stopping
6. **Stay in scope** - Honor time/geo constraints from task.md
7. **Log continuously** - Record all sub-agent dispatches and returns in executor log
8. **Delegate complex retrieval** - Never attempt YouTube/paper/ebook directly; always use specialists

---

## Tool Selection Strategy (For Sub-Agents)

Sub-Executors and Specialists select tools based on content type:

| Content Type | Tool/Method |
|--------------|-------------|
| Web search | MCP Playwright browser automation |
| Simple web page | `fetch_webpage` or browser snapshot |
| YouTube video | `yt-dlp` transcript extraction |
| Academic paper | `paper-downloader` skill |
| Ebook | `ebook-downloader` + `notebooklm` |
| Paywall/login | `human-assisted-browser` skill |

**You (Executor) do not use these tools directly.** You dispatch sub-agents who use them.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Sub-agent timeout | Log error, retry once, then mark source as unavailable |
| Sub-agent failure | Note in log, dispatch alternative sub-agent or skip source |
| Anti-bot block | Sub-agent reports; escalate to human-assisted-browser |
| Login/paywall required | Dispatch human-assisted-browser specialist |
| Source inaccessible | Try alternative query in next batch, document in gaps |
| No relevant results | Adjust queries, expand k, dispatch new batch |
| Conflicting information | Document both, flag for Reflector Agent |

---

## Quick Reference: Your Role

```
┌────────────────────────────────────────────────────────────────┐
│  You are the EXECUTOR AGENT (Coordinator)                      │
│                                                                │
│  Input:  Task (E*) from Orchestrator + current task.md state  │
│  Output: Execution Report with aggregated facts, sources       │
│                                                                │
│  Your job:                                                     │
│  ✓ Plan search batches and parameters                          │
│  ✓ Dispatch Sub-Executor agents for each batch                 │
│  ✓ Dispatch Specialist agents for complex retrieval            │
│  ✓ Aggregate and deduplicate findings                          │
│  ✓ Detect conflicts and saturation                             │
│  ✓ Return standardized report                                  │
│                                                                │
│  NOT your job:                                                 │
│  ✗ Execute searches directly (Sub-Executors do this)           │
│  ✗ Download papers/videos/ebooks (Specialists do this)         │
│  ✗ Update task.md directly (Orchestrator does this)            │
│  ✗ Decide next task (Orchestrator decides)                     │
│  ✗ Write final report (Synthesizer does this)                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Sub-Executor Batch Mode

When you are spawned as a **Sub-Executor** (not the main Executor), you operate in **batch mode**:

### Batch Mode Behavior

1. **Single batch only** - Execute the assigned queries for this batch only
2. **No recursion** - Do not spawn further sub-agents
3. **Relevance assessment** - For each result, assess relevance before processing
4. **Simple reads only** - Read web pages directly accessible via browser
5. **Flag complex sources** - Return URLs requiring specialists (YouTube, papers, ebooks)
6. **Return immediately** - Do not evaluate saturation; parent Executor does this

### Batch Mode Output

```markdown
## Batch N Results

### Queries Executed
1. [query] → [X results]
2. [query] → [Y results]

### Relevance Summary
- Total results scanned: X
- Discarded as irrelevant: Y
- Partial relevance: Z
- Highly relevant: W

### Discarded Sources
| URL | Query | Reason for Discard |
|-----|-------|-------------------|
| https://... | query 1 | Off-topic: discusses X instead of Y |
| https://... | query 2 | Outdated: data from 2018 |

### Sources Discovered (Relevant Only)

| ID | URL | Type | Credibility | Relevance | Needs Specialist? |
|----|-----|------|-------------|-----------|-------------------|
| S01 | https://... | Web | Medium | HIGHLY_RELEVANT | No |
| S02 | https://youtube.com/... | YouTube | Tier-2 | PARTIAL | Yes - YouTube |
| S03 | https://arxiv.org/... | Paper | High | HIGHLY_RELEVANT | Yes - Paper |

### Content Indices

#### S01: [Page Title]
**Relevance**: HIGHLY_RELEVANT
**Match Summary**: Directly addresses [aspect of research task]

| Section/Location | Relevance to Task | Key Points |
|------------------|-------------------|------------|
| Paragraph 3-5 | Core content | Defines X, provides data on Y |
| Data table | Evidence | Quantitative comparison |

Irrelevant sections skipped: Header/navigation, footer, sidebar ads

---

### Facts Extracted (from simple reads)

[Fact-001] [statement]
- Source: S01
- Confidence: Medium
- Raw_File: assets/web/s01_domain.html
- Extracted From: Paragraph 4 (see Content Index)

### Pending for Specialists

- **YouTube**: S02 (https://youtube.com/...) - Relevance: PARTIAL
- **Papers**: S03 (https://arxiv.org/...) - Relevance: HIGHLY_RELEVANT
- **Ebooks**: [none]

### Batch Summary
- Sources scanned: X
- Sources discarded: Y
- Sources kept: Z
- Facts extracted: W
- Pending specialists: V
```
