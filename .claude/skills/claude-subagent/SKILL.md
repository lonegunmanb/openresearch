---
name: claude-cli-subagent
description: Launch a sub-agent via Anthropic Claude CLI command line to execute tasks asynchronously. Use when delegating complex tasks to an independently running agent, when tasks should run in the background, or when the user explicitly requests starting a sub-agent, and youself is Claude Agent. Triggers include requests like "start a sub-agent", "run in background", "process this asynchronously", "have an agent do this".
---

# CLI Sub-Agent

Launch asynchronous sub-agents via command line to execute complex tasks.

## When to Use

**Use sub-agents when:**
- Task is complex and requires multiple steps
- User wants the task to run asynchronously in the background
- Need to implement a complete feature end-to-end
- User explicitly requests delegation to a sub-agent

**Do NOT use sub-agents when:**
- Task is simple and can be completed immediately
- User needs interactive feedback during the process
- Immediate results are needed in the current conversation

## Task Description Specification

### Template

```markdown
## Task
[One-line description of what needs to be done]

## Context
[Why this is needed, relevant background]

## Requirements
[List of specific requirements]

## Files Involved
[Files to create/modify, if known]

## Acceptance Criteria
[Verifiable outcome checklist]
```

### Example

```markdown
## Task
Implement JWT-based user authentication

## Requirements
- Add login/logout endpoints at /api/auth
- Use bcrypt for password encryption
- JWT tokens expire after 24 hours
- Include refresh token mechanism

## Files Involved
- src/routes/auth.ts (create)
- src/middleware/authenticate.ts (create)
- src/models/User.ts (modify)

## Acceptance Criteria
- [ ] Users can register
- [ ] Users can login and receive JWT
- [ ] Protected routes reject invalid tokens
- [ ] Tests pass
```

## Best Practices

1. **Be specific**: Vague tasks lead to unexpected results
2. **Provide context**: Sub-agents don't have conversation history
3. **Set boundaries**: Clearly define what's in and out of scope
4. **Reference patterns**: Point to similar code in the codebase
5. **Define done**: Clear acceptance criteria help the agent know when to stop

---

## Implementation: Claude Code CLI

This project uses Claude Code CLI as the sub-agent implementation.

### Non-Interactive Mode (Recommended for Sub-Agent Tasks)

Use `-p` / `--print` flag to execute a prompt and exit after completion:

```bash
# Basic usage - will prompt for tool permissions
claude -p "Task description following the template above"

# Bypass all permission checks (for sandboxed environments only)
claude -p "Task description" --dangerously-skip-permissions

# Use plan mode (Claude plans but asks before executing)
claude -p "Task description" --permission-mode plan

# Accept edits automatically
claude -p "Task description" --permission-mode acceptEdits
```

### Interactive Mode with Prompt

Start interactive mode with an initial prompt:

```bash
claude "Fix the bug in main.js"
```

### Common Options

```bash
# Specify model (alias or full name)
claude -p "Task" --model sonnet
claude -p "Task" --model opus
claude -p "Task" --model claude-sonnet-4-5-20250929

# Allow access to additional directories
claude -p "Task" --add-dir /path/to/other/project

# Restrict available tools
claude -p "Task" --allowed-tools "Bash(git:*) Edit Read"

# Deny specific tools
claude -p "Task" --disallowed-tools "Bash(rm:*)"

# Set maximum budget
claude -p "Task" --max-budget-usd 5.00

# Custom system prompt
claude -p "Task" --system-prompt "You are a senior developer focused on clean code"

# Append to default system prompt
claude -p "Task" --append-system-prompt "Always write tests for new code"

# Output as JSON (useful for scripting)
claude -p "Task" --output-format json

# Stream JSON output (realtime)
claude -p "Task" --output-format stream-json
```

### Resuming Sessions

```bash
# Continue most recent conversation in current directory
claude --continue

# Resume by session ID or open interactive picker
claude --resume
claude --resume <session-id>

# Fork session (create new ID instead of reusing original)
claude --continue --fork-session
```

### Permission Modes

| Mode | Description |
|------|-------------|
| `default` | Prompt for each permission |
| `acceptEdits` | Auto-accept file edits, prompt for others |
| `plan` | Claude plans but asks before executing |
| `dontAsk` | Skip non-critical confirmations |
| `bypassPermissions` | Skip all permission checks (requires `--allow-dangerously-skip-permissions`) |

### Available Models

Use alias (`sonnet`, `opus`, `haiku`) or full model name (e.g., `claude-sonnet-4-5-20250929`).
