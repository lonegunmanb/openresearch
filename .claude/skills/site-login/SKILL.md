---
name: site-login
description: Handle website login with browser automation. Use this skill when an agent needs to access a website that requires authentication, before searching or scraping content from that site. Supports concurrent access control to prevent multiple agents from attempting login simultaneously.
---

# Site Login Skill

Provides browser-based login flow for websites that require authentication. Opens a headed browser window for user to manually complete login, then saves the session for future use.

## When to Use This Skill

1. **Before searching a site** - Always check access first
2. **When login is required** - Trigger login flow
3. **After failed requests** - Site may require authentication

## Pre-flight Check (Always Do This First)

Before attempting to search or access a website, check if access is available:

```bash
python .claude/skills/site-login/scripts/check_site_access.py <domain>
```

**Exit codes:**
- `0` - Accessible (can proceed with search)
- `1` - Skipped (user declined login, do NOT search this site)
- `2` - Needs login (trigger login flow first)

**Example:**
```bash
python .claude/skills/site-login/scripts/check_site_access.py z-library.sk
# Output: ✅ z-library.sk: ACCESSIBLE
#    or: ⏭️ z-library.sk: SKIPPED
#    or: 🔐 z-library.sk: NEEDS LOGIN
```

## Login Flow

When pre-flight check returns exit code 2 (needs login):

```bash
python .claude/skills/site-login/scripts/site_login.py <url>
```

⚠️ **IMPORTANT FOR AGENTS:** Before running the login script, you MUST inform the user:
> "I'm opening a browser for you to login. **Please close the browser window after completing the login** so I can continue."

The script detects login completion by monitoring when the user closes the browser. If the user doesn't close the browser, the agent will wait indefinitely (up to timeout).

**Exit codes:**
- `0` - Success (logged in)
- `1` - Skipped (was already marked as skipped)
- `2` - Timeout (user didn't complete login, site now skipped)
- `3` - Failed (max retries, browser closed without valid login)

**Example:**
```bash
python .claude/skills/site-login/scripts/site_login.py https://z-library.sk
```

**What happens:**
1. Acquires lock for the domain (blocks if another agent is logging in)
2. Opens browser window navigated to the URL
3. Waits up to 300 seconds for user to login and close browser
4. Verifies login status after browser closes
5. Retries automatically if browser closed without valid login
6. Marks site as skipped if timeout reached

## Workflow for Agents

```
┌─────────────────────────────────────────┐
│ Agent wants to search site.example.com  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ check_site_access.py site.example.com   │
└────────────────┬────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
        ▼        ▼        ▼
    Exit 0   Exit 1   Exit 2
   (Access) (Skipped) (Login)
        │        │        │
        ▼        ▼        ▼
   Proceed    STOP     Run site_login.py
   with      (Don't    Then check again
   search    search)
```

## Concurrency Control

The skill uses file-based locking to prevent race conditions:

- **Global browser lock**: `.locks/__browser__` - Only one Playwright browser instance can run at a time
- Skip markers: `.skip-website/<domain>`

### Global Browser Lock

Since all Playwright instances share the same `browser_profile` directory, only one browser can be active at a time. The global browser lock ensures:

1. Login script waits if MCP browser is running
2. MCP tools should check lock before starting browser
3. Lock is automatically released when browser closes

**Check if browser is locked:**
```bash
python .claude/skills/site-login/scripts/lock_utils.py browser-check
```

**Wait for browser lock:**
```bash
python .claude/skills/site-login/scripts/lock_utils.py browser-wait
```

**Manually release browser lock (if stuck):**
```bash
python .claude/skills/site-login/scripts/lock_utils.py browser-release
```

## Shared Browser Profile

All logins share a single browser profile at `./browser_profile/`. This profile is also used by Playwright MCP, so logged-in sessions are available to MCP tools.

## Utility Commands

### List Locked Domains
```bash
python .claude/skills/site-login/scripts/lock_utils.py list-locks
```

### List Skipped Sites
```bash
python .claude/skills/site-login/scripts/lock_utils.py list-skipped
```

### Manually Unskip a Site
```bash
python .claude/skills/site-login/scripts/lock_utils.py unskip <domain>
```

### Check Domain Login Status
```bash
python .claude/skills/site-login/scripts/browser_state_utils.py <domain>
```

## Dependencies

- Python 3.8+
- playwright (`pip install playwright && playwright install`)
- psutil (`pip install psutil`)

## Anti-Bot Verification?

If you encounter any of the following situations:
- CAPTCHA, reCAPTCHA, hCaptcha challenges
- Cloudflare DDoS protection / "Checking your browser" page
- DDoS-Guard verification
- "Verify you are human" or "I'm not a robot" prompts
- Any automated access blocking or verification challenges

**DO NOT** simply increase wait times or retry. Instead, read `.claude/skills/human-assisted-browser/SKILL.md` and follow its workflow to request human assistance.
