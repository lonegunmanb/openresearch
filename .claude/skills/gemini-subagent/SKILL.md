---
name: gemini-cli-subagent
description: Launch a sub-agent via Google Gemini CLI command line to execute tasks asynchronously. Use when delegating complex tasks to an independently running agent, when tasks should run in the background, or when the user explicitly requests starting a sub-agent, and yourself is Gemini Agent. Triggers include requests like "start a sub-agent", "run in background", "process this asynchronously", "have an agent do this".
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

## Implementation: Gemini CLI

This project uses Gemini CLI as the sub-agent implementation.

### Non-Interactive Mode (Recommended for Sub-Agent Tasks)

Use `-p` / `--prompt` flag to execute a prompt in non-interactive mode:

```bash
# Basic usage - will prompt for tool permissions
gemini -p "Task description following the template above"

# Auto-approve all actions (YOLO mode)
gemini -p "Task description" --yolo
gemini -p "Task description" -y

# Use approval modes
gemini -p "Task description" --approval-mode yolo      # Auto-approve all tools
gemini -p "Task description" --approval-mode auto_edit # Auto-approve edit tools only
gemini -p "Task description" --approval-mode plan      # Read-only mode
```

### Interactive Mode with Prompt

Use `-i` / `--prompt-interactive` to execute prompt and continue in interactive mode:

```bash
gemini -i "Fix the bug in main.js"
```

Or start interactive mode directly:

```bash
gemini "Fix the bug in main.js"
```

### Common Options

```bash
# Specify model
gemini -p "Task" --model gemini-2.5-pro

# Run in sandbox mode
gemini -p "Task" --sandbox

# Allow specific tools without confirmation
gemini -p "Task" --allowed-tools shell edit

# Include additional directories in workspace
gemini -p "Task" --include-directories /path/to/other/project

# Use specific extensions only
gemini -p "Task" --extensions extension1 extension2

# Output as JSON (useful for scripting)
gemini -p "Task" --output-format json

# Stream JSON output (realtime)
gemini -p "Task" --output-format stream-json

# Debug mode
gemini -p "Task" --debug
```

### Resuming Sessions

```bash
# Resume most recent session
gemini --resume latest

# Resume by session index
gemini --resume 5

# List available sessions
gemini --list-sessions

# Delete a session by index
gemini --delete-session 3
```

### Approval Modes

| Mode | Description |
|------|-------------|
| `default` | Prompt for approval on each action |
| `auto_edit` | Auto-approve edit tools, prompt for others |
| `yolo` | Auto-approve all tools (same as `-y` flag) |
| `plan` | Read-only mode, no modifications allowed |

### Managing Extensions

```bash
# List all available extensions
gemini --list-extensions

# Use specific extensions only
gemini -p "Task" -e extension1 extension2
```
