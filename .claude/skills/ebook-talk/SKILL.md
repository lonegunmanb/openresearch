---
name: ebook-talk
description: Read and query ebooks for information verification or discovery. Use when you need to verify facts from an ebook, find specific information in a book, or explore book contents through Q&A. Combines ebook-downloader (to get PDF) and notebooklm (to create searchable notebook and chat via Playwright). Activate when tasks require consulting book sources.
---

# Ebook Talk

Query ebooks to verify information or find specific content through natural language Q&A.

## When to Use

- Verify a claim or fact by consulting a specific book
- Find information within an ebook (quotes, concepts, data)
- Explore book contents through conversational queries
- Cross-reference information across book sources

## Workflow

### 1. Download the Ebook

Use the `ebook-downloader` skill to obtain the PDF:

1. Read `.claude/skills/ebook-downloader/SKILL.md`
2. Follow its workflow to search and download the ebook
3. The PDF will be saved to `./assets/ebook/`

### 2. Create NotebookLM Notebook and Add Source

Use the `notebooklm` skill to set up the notebook:

1. Read `.claude/skills/notebooklm/SKILL.md`
2. Create a notebook for the book
3. Add the downloaded PDF as a source
4. Wait for the source to be processed

### 3. Chat with the Book

Use Playwright browser control to interact with the NotebookLM chat interface:

1. Navigate to the notebook in NotebookLM
2. Use the chat input to ask your questions
3. Read responses from the snapshot

## ⚠️ CRITICAL: Clear Conversation for New Topics

**When starting a NEW line of inquiry (not a follow-up to previous question), you MUST clear the conversation history first:**

1. Find the "New chat" button or menu option in the browser
2. Click to start a fresh conversation
3. Then ask your new question

**When to clear conversation:**
- Asking about a different topic/concept
- Verifying a different claim
- Starting fresh after completing previous inquiry

**When NOT to clear:**
- Following up on the same topic ("Can you elaborate on that?")
- Asking for clarification of the previous answer
- Drilling deeper into the same subject

## Tips

- **Specific queries work better**: "What does chapter 3 say about X?" is better than "Tell me about X"
- **Quote verification**: Ask NotebookLM to find the exact quote and its context
- **Multiple sources**: You can add multiple PDFs to the same notebook for cross-referencing
- **Reuse notebooks**: Check if a notebook for the book already exists before creating a new one
