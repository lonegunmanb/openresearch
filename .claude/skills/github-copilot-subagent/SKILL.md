---
name: copilot-cli-subagent
description: Launch a sub-agent via GitHub Copilot CLI command line to execute tasks asynchronously. Use when delegating complex tasks to an independently running agent, when tasks should run in the background, or when the user explicitly requests starting a sub-agent, and youself is GitHub Copilot Agent. Triggers include requests like "start a sub-agent", "run in background", "process this asynchronously", "have an agent do this".
---

# GitHub Copilot CLI Sub-Agent

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

## Implementation: GitHub Copilot CLI

This project uses GitHub Copilot CLI as the sub-agent implementation.

### Non-Interactive Mode (Recommended for Sub-Agent Tasks)

Use `-p` flag to execute a prompt and exit after completion:

```bash
# Basic usage - will prompt for tool permissions
copilot -p "Task description following the template above"

# Auto-approve all tools (required for truly autonomous execution)
copilot -p "Task description" --allow-all-tools

# Enable all permissions (tools, paths, URLs)
copilot -p "Task description" --allow-all
# or equivalently
copilot -p "Task description" --yolo
```

### Interactive Mode with Initial Prompt

Use `-i` to start interactive mode and auto-execute a prompt:

```bash
copilot -i "Fix the bug in main.js"
```

### Common Options

```bash
# Specify model
copilot -p "Task" --model claude-sonnet-4

# Allow access to additional directories
copilot -p "Task" --add-dir /path/to/project --allow-all-tools

# Silent mode - output only agent response (useful for scripting)
copilot -p "Task" --allow-all-tools --silent

# Save session to markdown file
copilot -p "Task" --allow-all-tools --share ./session-output.md

# Share session to GitHub gist
copilot -p "Task" --allow-all-tools --share-gist
```

### Resuming Sessions

```bash
# Resume most recent session
copilot --continue

# Resume with session picker
copilot --resume

# Resume specific session with auto-approval
copilot --allow-all-tools --resume <session-id>
```

### Available Models

`claude-sonnet-4.5`, `claude-haiku-4.5`, `claude-opus-4.5`, `claude-sonnet-4`, `gpt-5.2-codex`, `gpt-5.2`, `gpt-5.1-codex`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`, `gpt-4.1`
