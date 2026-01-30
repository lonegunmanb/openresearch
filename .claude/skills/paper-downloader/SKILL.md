---
name: paper-downloader
description: Download academic papers via DOI using Playwright browser automation. Use when users need to retrieve research paper PDFs. Searches Google Scholar first, falls back to Sci-Hub if blocked.
---

# Paper Downloader

Download academic papers and convert to Markdown for LLM analysis.

## Workflow

1. **Search Google Scholar first:**
   ```
   https://scholar.google.com/scholar?q=SEARCH+TERMS
   ```
   If blocked by CAPTCHA → skip to Sci-Hub

2. **Download via Sci-Hub:**
   ```
   https://sci-hub.ru/DOI_HERE
   ```
   - Click "No" on robot check
   - Click download link
   - PDF saves to `/tmp/`

3. **Convert to Markdown:**
   ```bash
   mv /tmp/paper.pdf ./assets/
   ~/.local/bin/markitdown ./assets/paper.pdf -o ./assets/paper.md
   ```

## Sci-Hub Mirrors

If `sci-hub.ru` fails, try: `sci-hub.st`, `sci-hub.red`

## Login Required?

If prompted to login, read `.claude/skills/site-login/SKILL.md` and follow its workflow.

## DNS Fix

If domains don't resolve:
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## Example

```
Navigate: https://sci-hub.ru/10.1038/s41578-019-0165-5
→ Click "No" on robot check
→ Click download link
→ Move PDF, convert to Markdown
```
