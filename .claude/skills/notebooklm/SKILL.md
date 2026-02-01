---
name: notebooklm
description: Browser automation for Google NotebookLM using MCP Playwright. Create notebooks, add sources, generate artifacts, and interact with content through browser automation. Activates on explicit /notebooklm or intent like "create a podcast about X"
---

# NotebookLM Browser Automation

Interact with Google NotebookLM through MCP Playwright browser automation. Create notebooks, add sources (URLs, YouTube, PDFs), chat with content, generate all artifact types, and download results.

## Prerequisites

### Login Using site-login Skill (Required)

⚠️ **Before using this skill**, you MUST be authenticated. Use the `site-login` skill to login to `https://notebooklm.google.com/`.

After login, verify authentication by navigating to the NotebookLM homepage and checking that you can see your notebooks.

## MCP Playwright Tools

This skill uses the following MCP Playwright tools for all interactions:

| Tool | Purpose |
|------|---------|
| `mcp_playwright_browser_navigate` | Navigate to NotebookLM pages |
| `mcp_playwright_browser_snapshot` | Capture page accessibility snapshot for understanding current state |
| `mcp_playwright_browser_click` | Click buttons, links, and interactive elements |
| `mcp_playwright_browser_type` | Type text into input fields |
| `mcp_playwright_browser_hover` | Hover over elements |
| `mcp_playwright_browser_press_key` | Press keyboard keys (Enter, Escape, etc.) |
| `mcp_playwright_browser_wait_for` | Wait for elements or text to appear |
| `mcp_playwright_browser_file_upload` | Upload PDF and other files |
| `mcp_playwright_browser_take_screenshot` | Take screenshots for verification |

## When This Skill Activates

**Explicit:** User says "/notebooklm", "use notebooklm", or mentions the tool by name

**Intent detection:** Recognize requests like:
- "Create a podcast about [topic]"
- "Summarize these URLs/documents"
- "Generate a quiz from my research"
- "Turn this into an audio overview"
- "Create flashcards for studying"
- "Generate a video explainer"
- "Make an infographic"
- "Create a mind map of the concepts"
- "Add these sources to NotebookLM"

## Key URLs

| Page | URL |
|------|-----|
| Home (Notebook List) | `https://notebooklm.google.com/` |
| Specific Notebook | `https://notebooklm.google.com/notebook/{notebook_id}` |

## Autonomy Rules

**Run automatically (no confirmation):**
- Navigate to NotebookLM
- Take snapshots to understand page state
- List notebooks (view home page)
- View sources in a notebook
- Chat/ask questions
- Create notebooks
- Add sources

**Ask before running:**
- Delete notebooks or sources (destructive)
- Generate artifacts (long-running, may fail)
- Download files (writes to filesystem)

## Core Workflows

### 1. Navigate and Check State

Always start by navigating to NotebookLM and taking a snapshot:

```
1. mcp_playwright_browser_navigate → https://notebooklm.google.com/
2. mcp_playwright_browser_snapshot → Get current page state
```

The snapshot provides an accessibility tree showing all interactive elements with their `ref` values for clicking.

### 2. List Notebooks

1. Navigate to `https://notebooklm.google.com/`
2. Take snapshot to see all notebook cards
3. Each notebook appears as a clickable element with its title

### 3. Create Notebook

1. Navigate to home page
2. Take snapshot to find "Create new" or "New notebook" button
3. Click the create button
4. Type the notebook title when prompted
5. Press Enter or click confirm

**Typical flow:**
```
1. Navigate to https://notebooklm.google.com/
2. Snapshot → Find "New notebook" button (look for ref)
3. Click the button using its ref
4. Wait for dialog/input
5. Snapshot → Find title input field
6. Type notebook title
7. Press Enter or click Create
```

### 4. Open a Notebook

1. From home page, take snapshot
2. Find the notebook card by title
3. Click the notebook card

### 5. Add Sources

#### Add URL/Website:
1. Open the notebook
2. Snapshot → Find "Add source" or "+" button
3. Click to open source panel
4. Find "Website" or "Link" option and click
5. Paste URL in the input field
6. Click "Insert" or confirm button

#### Add YouTube Video:
1. Same as URL - paste YouTube link
2. NotebookLM will recognize it as a video

#### Upload File (PDF, etc.):
1. Open source panel
2. Find "Upload" option
3. Use `mcp_playwright_browser_file_upload` with file path

#### Add Google Drive File:
1. Find "Google Drive" option in source panel
2. Click and navigate the Drive picker

### 6. Chat with Sources

1. Open the notebook with sources
2. Snapshot → Find the chat input field (usually at bottom)
3. Click the input field
4. Type your question
5. Press Enter or click Send
6. Wait for response to appear
7. Snapshot to read the response

### 7. Generate Audio Overview (Podcast)

1. Open notebook with processed sources
2. Snapshot → Find "Audio Overview" or "Notebook guide" section
3. Look for "Generate" or play button for audio
4. Click to start generation
5. Wait for generation (this takes 5-15 minutes)
6. Periodically snapshot to check status

**Note:** Audio generation is rate-limited. If it fails, wait 5-10 minutes and retry.

### 8. Generate Other Artifacts

Look for these options in the notebook interface:
- **Study Guide** - Usually in the guide/overview section
- **Briefing Doc** - Summary document
- **FAQ** - Frequently asked questions
- **Timeline** - Chronological overview
- **Mind Map** - Visual concept map

Each follows similar pattern:
1. Find the generate button for that artifact type
2. Click to generate
3. Wait and check status via snapshots

### 9. Download Generated Content

1. After artifact is complete, find download button
2. Click download
3. For audio: Look for download icon near the audio player
4. Files download to browser's default download location

## Element Identification Tips

When taking snapshots, look for these common patterns:

| Element | Common Labels/Text |
|---------|-------------------|
| Create notebook | "New notebook", "Create", "+ New" |
| Add source | "Add source", "+", "Upload" |
| Chat input | "Ask about your sources", input field at bottom |
| Send message | Send icon, arrow button |
| Audio generate | "Generate", play icon in Audio Overview section |
| Download | Download icon, "Download" |
| Delete | Trash icon, "Delete", "Remove" |

## Handling Dynamic Content

NotebookLM uses dynamic loading. Use these strategies:

1. **Wait for content:** Use `mcp_playwright_browser_wait_for` with expected text
2. **Retry snapshots:** If expected elements aren't visible, wait a moment and snapshot again
3. **Check loading states:** Look for "Loading...", spinners, or progress indicators

## Common Workflows

### Research to Podcast

1. Navigate to NotebookLM home
2. Create new notebook with topic name
3. Open the notebook
4. Add sources (URLs, files)
5. Wait for sources to process (check source list for "Ready" status)
6. Find and click Audio Overview generate button
7. Wait 10-20 minutes, checking periodically
8. Download the generated audio

### Document Analysis

1. Create/open notebook
2. Upload PDF or add URL
3. Wait for processing
4. Use chat to ask questions about the content
5. Read responses from snapshots

### Study Material Generation

1. Add learning materials as sources
2. Generate Study Guide
3. Generate Flashcards (if available)
4. Generate Quiz

## Error Handling

| Issue | Solution |
|-------|----------|
| Not logged in | Use site-login skill to authenticate |
| Element not found | Take new snapshot, element may have different text |
| Rate limited | Wait 5-10 minutes before retrying |
| Generation stuck | Refresh page and check status |
| Source not processing | Check if source format is supported |

## Processing Times

| Operation | Typical Time |
|-----------|--------------|
| Source processing | 30s - 5 min |
| Audio generation | 10 - 20 min |
| Video generation | 15 - 45 min |
| Other artifacts | 1 - 5 min |

## Tips for Reliable Automation

1. **Always snapshot first** - Understand page state before acting
2. **Use refs from snapshots** - Click elements using their ref values
3. **Wait after actions** - Page updates take time
4. **Verify results** - Snapshot after actions to confirm success
5. **Handle failures gracefully** - Offer retry or alternative actions

## Output Style

**Progress updates:** Brief status for each step
- "Navigating to NotebookLM..."
- "Creating notebook 'Research: AI'..."
- "Adding source: https://example.com..."
- "Starting audio generation..."

**On success:** Confirm completion with relevant details
**On failure:** Explain what went wrong and offer options
