---
name: human-assisted-browser
description: Handle anti-bot verification with human assistance. Use when an agent encounters CAPTCHA, reCAPTCHA, or other verification challenges that require human intervention. Provides a workflow for the agent to pause, wait for human help, then resume execution.
---

# Human-Assisted Browser Skill

Enables agents to request human assistance when encountering anti-bot verification, then seamlessly resume automated operation.

## When to Use

- Agent encounters reCAPTCHA, hCaptcha, or other CAPTCHA challenges
- Website blocks automated access and requires verification
- Login pages with complex anti-bot measures
- Any situation where human visual verification is required

## Workflow Overview

```
Agent detects verification
        │
        ▼
┌───────────────────┐
│ Switch to Headed  │  ← Open visible browser window
│ Browser Mode      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Create Signal     │  ← Write .waiting-for-human file
│ File              │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Notify Human      │  ← Print message, optional sound/notification
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Poll for          │  ← Check every 5 seconds
│ Completion        │     - Page content changed?
└─────────┬─────────┘     - Signal file removed?
          │
          ▼
┌───────────────────┐
│ Save Session      │  ← Store cookies for future use
│ Continue          │
└───────────────────┘
```

## Implementation

### 1. Detection: Identify Verification Pages

Common patterns to detect:
```python
CAPTCHA_INDICATORS = [
    "recaptcha",
    "hcaptcha", 
    "challenge",
    "verify you are human",
    "I'm not a robot",
    "unusual traffic",
    "please complete the challenge",
    "robot check"
]
```

### 2. Signal File Protocol

When verification detected, create signal file:
```bash
# Create waiting signal
echo "WAITING" > .waiting-for-human

# Content includes context:
cat > .waiting-for-human << EOF
status: WAITING
url: https://google.com/search?q=...
detected_at: 2026-01-30T06:45:00Z
challenge_type: reCAPTCHA
message: Please complete the verification in the browser window
EOF
```

Human removes file when done:
```bash
rm .waiting-for-human
```

### 3. Polling Script

```bash
#!/bin/bash
# wait_for_human.sh

SIGNAL_FILE=".waiting-for-human"
TIMEOUT=300  # 5 minutes max wait
POLL_INTERVAL=5

echo "🔐 Verification required. Please complete it in the browser window."
echo "   Signal file: $SIGNAL_FILE"
echo "   Timeout: ${TIMEOUT}s"

elapsed=0
while [ -f "$SIGNAL_FILE" ] && [ $elapsed -lt $TIMEOUT ]; do
    sleep $POLL_INTERVAL
    elapsed=$((elapsed + POLL_INTERVAL))
    echo -n "."
done

if [ -f "$SIGNAL_FILE" ]; then
    echo ""
    echo "❌ Timeout waiting for human verification"
    exit 1
else
    echo ""
    echo "✅ Verification completed! Resuming..."
    exit 0
fi
```

### 4. Page-Based Detection (Alternative)

Instead of signal file, detect when page content changes:

```python
def wait_for_verification_complete(page, timeout=300):
    """Wait for verification page to disappear"""
    import time
    start = time.time()
    
    while time.time() - start < timeout:
        snapshot = page.accessibility.snapshot()
        content = str(snapshot).lower()
        
        # Check if CAPTCHA indicators are gone
        captcha_present = any(
            indicator in content 
            for indicator in CAPTCHA_INDICATORS
        )
        
        if not captcha_present:
            print("✅ Verification completed!")
            return True
            
        time.sleep(5)
    
    return False
```

## Integration with Copilot CLI Sub-Agent

### Prompt Template for HITL-Aware Agent

```markdown
You are a research agent with human-assisted browser capability.

When you encounter anti-bot verification:
1. STOP automated actions
2. Announce: "🔐 Human verification required"
3. Create signal file: echo "WAITING" > .waiting-for-human
4. Wait in a loop checking if signal file exists
5. When file is removed, continue with your task

Detection keywords: "captcha", "robot", "verify", "challenge", "unusual traffic"

After human helps, remember to:
- Save browser cookies to storage_state.json
- Thank the human and continue
```

### Example Copilot CLI Invocation

```bash
copilot -p "
You are a research agent. Search for 'solid state battery CATL 2025'.

If you encounter any verification challenge:
1. Print '🔐 HUMAN ASSISTANCE NEEDED - Please complete verification in browser'
2. Run: echo 'WAITING' > .waiting-for-human
3. Run: while [ -f .waiting-for-human ]; do sleep 5; echo 'Waiting...'; done
4. After human removes the file, continue your search

Save all cookies to browser_profile/storage_state.json when done.
" --allow-all-tools
```

## Session Persistence

After successful verification, save session for reuse:

```python
# Save cookies after verification
browser_context.storage_state(path="browser_profile/storage_state.json")

# Reuse in future sessions
browser = playwright.chromium.launch(headless=False)
context = browser.new_context(storage_state="browser_profile/storage_state.json")
```

## Best Practices

1. **Always use Headed mode** when HITL might be needed
2. **Persist sessions** - Save cookies after verification to avoid re-verification
3. **Timeout gracefully** - Don't wait forever, fail after reasonable timeout
4. **Clear notifications** - Make it obvious when human help is needed
5. **Pre-warm sessions** - Use site-login skill before research tasks

## Combining with site-login Skill

For known sites requiring login:
```bash
# Check access first
python .claude/skills/site-login/scripts/check_site_access.py google.com
# Exit code 2 = needs login, trigger HITL flow
```

## Audio/Visual Notification (Optional)

Alert the human when assistance needed:
```bash
# macOS
osascript -e 'display notification "Verification needed" with title "Agent Paused"'
afplay /System/Library/Sounds/Glass.aiff

# Linux  
notify-send "Agent Paused" "Verification needed in browser"
paplay /usr/share/sounds/freedesktop/stereo/complete.oga

# Windows PowerShell
[System.Media.SystemSounds]::Exclamation.Play()
```
