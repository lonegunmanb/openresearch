---
name: ebook-downloader
description: Download ebooks from Z-Library using Playwright browser automation. Use when users need to find and download ebooks. Requires login check before accessing Z-Library.
---

# Ebook Downloader

Download ebooks from Z-Library and convert to PDF format for archival.

## ⚠️ CRITICAL: Interactive Browser Control

**DO NOT write Playwright scripts or automation code.** Instead:

1. **Use Playwright MCP tools** to control the browser interactively
2. **After EVERY action, take a snapshot** to observe the current page state
3. **Analyze the snapshot content** to understand what's on the page
4. **Decide your next action based on what you SEE**, not on pre-planned scripts

This is a **feedback loop**: Action → Snapshot → Analyze → Next Action

The browser state is unpredictable (popups, CAPTCHAs, different layouts). You MUST observe and adapt.

## Pre-flight Access Check (ALWAYS DO THIS FIRST)

Before accessing Z-Library, you MUST check if you're logged in:

1. Read `.claude/skills/check-site-access/SKILL.md` for detailed instructions
2. Run the access check for `z-library.sk`
3. Handle the result:
   - **ACCESSIBLE (exit 0)**: Proceed with search
   - **SKIPPED (exit 1)**: Do NOT search, inform user the site was previously declined
   - **NEEDS_LOGIN (exit 2)**: Trigger login flow first (see Login Required section below)

## Workflow

1. **Check site access first** (see Pre-flight section above)

2. **Search Z-Library:**
   - Navigate to: `http://z-library.sk/`
   - Take snapshot → analyze what you see
   - Use the search box to enter book title/author
   - Take snapshot → find and click the search button or press Enter
   - Take snapshot → analyze search results

3. **Select and Download:**
   - Review search results in the snapshot
   - Click on the desired book entry
   - Take snapshot → look for download button/link
   - Click the download button (prefer PDF format if available, otherwise EPUB)
   - The file downloads to the default download location

4. **Move and Convert to PDF:**
   ```bash
   # Create assets/ebook directory if not exists
   mkdir -p ./assets/ebook
   
   # Move downloaded file to assets/ebook/
   mv /path/to/downloaded/book.* ./assets/ebook/
   
   # If not PDF, convert to PDF using Calibre's ebook-convert
   # For EPUB to PDF:
   ebook-convert ./assets/ebook/book.epub ./assets/ebook/book.pdf
   
   # Or use LibreOffice for other formats:
   libreoffice --headless --convert-to pdf --outdir ./assets/ebook ./assets/ebook/book.*
   ```

## Z-Library Search Tips

- Search by exact title for better results
- Include author name to narrow results
- Check file format and size before downloading
- Prefer PDF format when available to avoid conversion

## How to Interact with the Browser

**NEVER do this:**
```python
# ❌ WRONG - Don't write scripts
page.goto("https://z-library.sk/...")
page.click("button#download")
```

**ALWAYS do this:**
1. Use `playwright-browser_navigate` to go to URL → then `playwright-browser_snapshot`
2. Analyze the snapshot: What elements are visible? What should you click?
3. Use `playwright-browser_click` with the ref you identified from snapshot
4. Take another snapshot to verify the result
5. Repeat until task is complete

**Key principle:** You are a human looking at a screen and deciding what to do next. Each snapshot is your "eyes". Don't assume anything about the page layout—always look first.

## Login Required?

If the pre-flight check returns **NEEDS_LOGIN** (exit code 2), or if you see a login prompt in the snapshot:

1. Read `.claude/skills/site-login/SKILL.md` for the complete login workflow
2. Follow its instructions to trigger the login flow for Z-Library
3. After successful login, return here and continue with the search workflow

## Anti-Bot Verification?

If you SEE in the snapshot any of the following:
- CAPTCHA, reCAPTCHA, hCaptcha challenges
- Cloudflare DDoS protection / "Checking your browser" page
- DDoS-Guard verification
- "Verify you are human" or "I'm not a robot" prompts
- Any automated access blocking or verification challenges

**DO NOT** simply increase wait times or retry. Instead, read `.claude/skills/human-assisted-browser/SKILL.md` and follow its workflow to request human assistance.

## Output Location

All downloaded ebooks are stored in: `./assets/ebook/`

Naming convention: Use the original filename or sanitize the book title (replace spaces with underscores, remove special characters).

## PDF Conversion

If the downloaded file is not PDF, convert it:

### Using Calibre (recommended for ebooks)
```bash
# Install Calibre if needed
# Ubuntu/Debian: sudo apt install calibre
# Windows: choco install calibre

# Convert EPUB to PDF
ebook-convert input.epub output.pdf

# Convert MOBI to PDF
ebook-convert input.mobi output.pdf
```

### Using LibreOffice (for other formats)
```bash
libreoffice --headless --convert-to pdf --outdir ./assets/ebook ./assets/ebook/document.docx
```

## Example Interaction Flow

```
1. Run check-site-access for z-library.sk
   → Exit 0: Proceed
2. playwright-browser_navigate to "http://z-library.sk/"
3. playwright-browser_snapshot
   → You SEE: Homepage with search box
4. playwright-browser_type in search box: "The Great Gatsby"
5. playwright-browser_snapshot → playwright-browser_click search button
6. playwright-browser_snapshot
   → You SEE: Search results list
7. playwright-browser_click on the desired result
8. playwright-browser_snapshot
   → You SEE: Book detail page with download options
9. playwright-browser_click on PDF download (or EPUB if no PDF)
10. Wait for download to complete
11. Move file to ./assets/ebook/ and convert to PDF if needed
```

Each step depends on what you OBSERVE, not on a fixed script.

## Dependencies

- Playwright MCP tools (for browser automation)
- Calibre (`ebook-convert`) for ebook format conversion
- LibreOffice (optional, for document formats)
