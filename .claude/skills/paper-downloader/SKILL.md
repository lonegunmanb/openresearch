---
name: paper-downloader
description: Download academic papers via DOI using Playwright browser automation. Use when users need to retrieve research paper PDFs. Searches Google Scholar first, falls back to Sci-Hub if blocked.
---

# Paper Downloader

Download academic papers and convert to Markdown for LLM analysis.

## ⚠️ CRITICAL: Interactive Browser Control

**DO NOT write Playwright scripts or automation code.** Instead:

1. **Use `mcp__puppeteer-mcp-server__browser_action` tool** to control the browser interactively
2. **After EVERY action, take a screenshot** to observe the current page state
3. **Analyze the screenshot content** to understand what's on the page
4. **Decide your next action based on what you SEE**, not on pre-planned scripts

This is a **feedback loop**: Action → Screenshot → Analyze → Next Action

The browser state is unpredictable (popups, CAPTCHAs, different layouts). You MUST observe and adapt.

## Workflow

1. **Search Google Scholar first:**
   - Navigate to: `https://scholar.google.com/scholar?q=SEARCH+TERMS`
   - Take screenshot → analyze what you see
   - If blocked by CAPTCHA → skip to Sci-Hub

2. **Download via Sci-Hub:**
   - Navigate to: `https://sci-hub.ru/DOI_HERE`
   - Take screenshot → observe the page content
   - Look for and click "No" on robot check if present
   - Take screenshot → find and click the download link
   - PDF saves to `/tmp/`

3. **Convert to Markdown:**
   ```bash
   mv /tmp/paper.pdf ./assets/
   ~/.local/bin/markitdown ./assets/paper.pdf -o ./assets/paper.md
   ```

## Sci-Hub Mirrors

If `sci-hub.ru` fails, try: `sci-hub.st`, `sci-hub.red`

## How to Interact with the Browser

**NEVER do this:**
```python
# ❌ WRONG - Don't write scripts
page.goto("https://sci-hub.ru/...")
page.click("button#download")
```

**ALWAYS do this:**
1. Use `browser_action` with `action: "goto"` → then `action: "screenshot"`
2. Analyze the screenshot: What elements are visible? What should you click?
3. Use `browser_action` with `action: "click"` at the coordinates you identified
4. Take another screenshot to verify the result
5. Repeat until task is complete

**Key principle:** You are a human looking at a screen and deciding what to do next. Each screenshot is your "eyes". Don't assume anything about the page layout—always look first.

## Login Required?

If prompted to login (you'll SEE this in the screenshot), read `.claude/skills/site-login/SKILL.md` and follow its workflow.

## Anti-Bot Verification?

If you SEE in the screenshot any of the following:
- CAPTCHA, reCAPTCHA, hCaptcha challenges
- Cloudflare DDoS protection / "Checking your browser" page
- DDoS-Guard verification
- "Verify you are human" or "I'm not a robot" prompts
- Any automated access blocking or verification challenges

**DO NOT** simply increase wait times or retry. Instead, read `.claude/skills/human-assisted-browser/SKILL.md` and follow its workflow to request human assistance.

## DNS Fix

If domains don't resolve:
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## Example Interaction Flow

```
1. browser_action: goto "https://sci-hub.ru/10.1038/s41578-019-0165-5"
2. browser_action: screenshot
   → You SEE: A page with "I am not a robot" checkbox and a "No" button
3. browser_action: click at coordinates where "No" button is visible
4. browser_action: screenshot
   → You SEE: A PDF preview with a download icon at (x, y)
5. browser_action: click at the download icon coordinates
6. browser_action: screenshot
   → You SEE: Download started / PDF saved
7. Move PDF, convert to Markdown
```

Each step depends on what you OBSERVE, not on a fixed script.
