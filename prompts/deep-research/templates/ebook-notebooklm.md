# Ebook + NotebookLM Specialist Template

For ebook analysis via NotebookLM, spawn a specialist agent using this template:

```bash
claude --print "You are an Ebook Analysis Specialist. Your task:

[BOOK_TITLE]: <title>
[RESEARCH_TASK]: <task description from Executor>
[SEARCH_TERMS]: <what to search for in the book>
[STORAGE]: Save ebook to assets/ebooks/{author}_{title}.{ext}
[RESEARCH_QUESTIONS]: 
  1. <question 1>
  2. <question 2>

Instructions:
1. Use ebook-downloader to acquire the book and SAVE to assets/ebooks/
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
