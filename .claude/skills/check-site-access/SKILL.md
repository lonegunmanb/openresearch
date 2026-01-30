---
name: check-site-access
description: Check if a website is accessible before attempting to search or scrape. Use this skill when an agent needs to verify site access status (logged in, skipped, or needs login) with a custom storage state path. Unlike site-login skill, this skill allows specifying arbitrary storage state and skip directory locations, making it suitable for isolated research tasks with separate browser profiles.
---

# Check Site Access Skill

Provides pre-flight access checking for websites before searching or scraping. Determines if a site is accessible (logged in), skipped (user declined), or requires login.

## Key Difference from site-login

This skill allows **custom paths** for storage state and skip directory, enabling:
- Isolated browser profiles per research task
- Multiple concurrent research sessions with separate login states
- Flexible integration with different workspace structures

## Usage

### Basic Check

```bash
python .claude/skills/check-site-access/scripts/check_access.py <domain> --storage-state <path> --skip-dir <path>
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `domain` | Yes | Domain to check (e.g., `github.com`, `z-library.sk`) |
| `--storage-state` | Yes | Path to Playwright storage state JSON file |
| `--skip-dir` | Yes | Path to directory containing skip markers |
| `--json` | No | Output result as JSON |

### Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| 0 | ACCESSIBLE | Site is logged in, proceed with search |
| 1 | SKIPPED | User declined login, do NOT search this site |
| 2 | NEEDS_LOGIN | Not logged in, trigger login flow first |
| 3 | ERROR | Check failed (missing files, invalid paths) |

### Examples

```bash
# Check GitHub access with task-specific profile
python .claude/skills/check-site-access/scripts/check_access.py github.com \
    --storage-state ./research-task-001/browser_profile/storage_state.json \
    --skip-dir ./research-task-001/.skip-website

# Check with JSON output for programmatic use
python .claude/skills/check-site-access/scripts/check_access.py z-library.sk \
    --storage-state /path/to/storage_state.json \
    --skip-dir /path/to/.skip-website \
    --json
```

## Workflow Integration

```
Agent wants to search site.example.com
                 |
                 v
+------------------------------------------+
| check_access.py site.example.com         |
|   --storage-state <task_profile>         |
|   --skip-dir <task_skip_dir>             |
+------------------------------------------+
                 |
        +--------+--------+--------+
        |        |        |        |
        v        v        v        v
    Exit 0   Exit 1   Exit 2   Exit 3
   (Access) (Skipped) (Login)  (Error)
        |        |        |        |
        v        v        v        v
   Proceed    STOP    Trigger   Handle
   with      search   login     error
   search             flow
```

## Adding Custom Site Configurations

The script includes predefined login detection rules for common sites. To check a site not in the predefined list, the script falls back to generic cookie detection for the domain.

Predefined sites with optimized detection:
- `github.com` - Checks `logged_in`, `user_session` cookies
- `google.com` - Checks `SID`, `HSID`, `SSID` cookies
- `z-library.sk` - Checks `remix_userid`, `remix_userkey` cookies

## Dependencies

- Python 3.8+
