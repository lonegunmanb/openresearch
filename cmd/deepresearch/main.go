package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// Global log file handle
var logFile *os.File

// AgentConfig defines how to invoke a specific agent CLI
type AgentConfig struct {
	Command         string
	Args            func(prompt, model, workDir string) []string
	InteractiveArgs func(prompt, model, workDir string) []string // Args for interactive mode with initial prompt
	ModelArg        string                                       // The CLI argument name for model (e.g., "--model")
}

var agentConfigs = map[string]AgentConfig{
	"copilot": {
		Command:  "copilot",
		ModelArg: "--model",
		Args: func(prompt, model, workDir string) []string {
			args := []string{"-p", prompt, "--yolo", "--add-dir", workDir}
			if model != "" {
				args = append(args, "--model", model)
			}
			return args
		},
		InteractiveArgs: func(prompt, model, workDir string) []string {
			// -i: Start interactive mode and automatically execute a prompt
			args := []string{"-i", prompt, "--yolo", "--add-dir", workDir}
			if model != "" {
				args = append(args, "--model", model)
			}
			return args
		},
	},
	"claude": {
		Command:  "claude",
		ModelArg: "--model",
		Args: func(prompt, model, workDir string) []string {
			args := []string{"-p", prompt, "--dangerously-skip-permissions"}
			if model != "" {
				args = append(args, "--model", model)
			}
			return args
		},
		InteractiveArgs: func(prompt, model, workDir string) []string {
			// Claude uses --resume or starts fresh - we'll use a prompt file approach
			args := []string{"--dangerously-skip-permissions"}
			if model != "" {
				args = append(args, "--model", model)
			}
			return args
		},
	},
	"gemini": {
		Command:  "gemini",
		ModelArg: "--model",
		Args: func(prompt, model, workDir string) []string {
			args := []string{"-p", prompt, "--yolo"}
			if model != "" {
				args = append(args, "--model", model)
			}
			return args
		},
		InteractiveArgs: func(prompt, model, workDir string) []string {
			// Gemini - assume similar to copilot
			args := []string{"-i", prompt, "--yolo"}
			if model != "" {
				args = append(args, "--model", model)
			}
			return args
		},
	},
}

func main() {
	// Parse command line arguments
	prompt := flag.String("p", "", "Direct prompt input (skips interactive approval)")
	promptFile := flag.String("f", "", "Read prompt from file")
	agent := flag.String("agent", "", "Agent to use: copilot, claude, gemini (auto-detect if not specified)")
	model := flag.String("model", "", "Model to use (e.g., claude-sonnet-4-20250514, gpt-4o, gemini-2.0-flash)")
	flag.Parse()

	// Determine user prompt: -p takes priority, then -f, then stdin
	var userPrompt string
	interactiveMode := false // Track if user is in interactive mode (stdin input)
	if *prompt != "" {
		userPrompt = *prompt
	} else if *promptFile != "" {
		content, err := os.ReadFile(*promptFile)
		if err != nil {
			fatal("Failed to read prompt file: %v", err)
		}
		userPrompt = strings.TrimSpace(string(content))
		if userPrompt == "" {
			fatal("Prompt file is empty")
		}
		info("Read prompt from file: %s", *promptFile)
	} else {
		fmt.Print("Enter your research topic: ")
		reader := bufio.NewReader(os.Stdin)
		input, err := reader.ReadString('\n')
		if err != nil {
			fatal("Failed to read input: %v", err)
		}
		userPrompt = strings.TrimSpace(input)
		if userPrompt == "" {
			fatal("Research topic cannot be empty")
		}
		interactiveMode = true // User entered via stdin, enable interactive plan approval
	}

	// Use current directory as working directory
	absWorkDir, err := filepath.Abs(".")
	if err != nil {
		fatal("Failed to resolve working directory: %v", err)
	}

	// Detect or validate agent
	agentName := *agent
	if agentName == "" {
		agentName = detectAgent()
		if agentName == "" {
			fatal("No supported agent CLI found. Install one of: copilot, claude, gemini")
		}
		info("Auto-detected agent: %s", agentName)
	} else {
		if _, ok := agentConfigs[agentName]; !ok {
			fatal("Unknown agent: %s. Supported: copilot, claude, gemini", agentName)
		}
		if !isCommandAvailable(agentConfigs[agentName].Command) {
			fatal("Agent '%s' is not installed or not in PATH", agentName)
		}
	}

	// Get prompts directory (relative to executable or current directory)
	promptsDir := findPromptsDir()
	if promptsDir == "" {
		fatal("Cannot find prompts/deep-research directory")
	}
	info("Using prompts from: %s", promptsDir)
	info("Working directory: %s", absWorkDir)
	if *model != "" {
		info("Using model: %s", *model)
	}

	// Create necessary directories
	createDirs(absWorkDir)

	// Initialize log file
	initLogFile(absWorkDir)
	defer closeLogFile()

	// Log boot
	logEntry("INFO", "BOOT", 0, "Orchestrator started", map[string]string{
		"agent":    agentName,
		"model":    *model,
		"work_dir": absWorkDir,
	})

	// ========== PHASE 1: PLANNER ==========
	phase("PLANNER", "Creating research plan")
	logEntry("INFO", "DISPATCH", 0, "Dispatching Planner agent", map[string]string{
		"phase":       "PLANNER",
		"interactive": fmt.Sprintf("%v", interactiveMode),
	})

	if interactiveMode {
		// Interactive mode: launch agent in conversation mode
		// Write complete instructions to a temp file so agent gets all context in one place
		info("Interactive mode: You can discuss and refine the research plan with the agent")
		info("The agent will automatically exit after creating task.md")
		fmt.Println()

		// Create lock file - agent will delete it when task.md is created
		lockDir := filepath.Join(absWorkDir, ".locks")
		if err := os.MkdirAll(lockDir, 0755); err != nil {
			fatal("Failed to create .locks dir: %v", err)
		}
		plannerLockFile := filepath.Join(lockDir, ".planner.lock")
		// Remove stale lock file if exists from previous run
		if fileExists(plannerLockFile) {
			os.Remove(plannerLockFile)
		}
		if err := os.WriteFile(plannerLockFile, []byte("planner in progress"), 0644); err != nil {
			fatal("Failed to create lock file: %v", err)
		}

		// Create combined instruction file with planner.md content + parameters
		plannerContent, err := os.ReadFile(filepath.Join(promptsDir, "planner.md"))
		if err != nil {
			fatal("Failed to read planner.md: %v", err)
		}
		defer os.Remove(plannerLockFile)

		combinedPrompt := fmt.Sprintf(`# Research Planner Task

## Environment Parameters

- **WORKING_DIR**: %s
- **APPROVAL_MODE**: INTERACTIVE
- **USER_REQUEST**: %s

---

%s
`, absWorkDir, userPrompt, string(plannerContent))

		// Write to tmp/planner_task.md
		taskFile := filepath.Join(absWorkDir, "tmp", "planner_task.md")
		if err := os.MkdirAll(filepath.Dir(taskFile), 0755); err != nil {
			fatal("Failed to create tmp dir: %v", err)
		}
		if err := os.WriteFile(taskFile, []byte(combinedPrompt), 0644); err != nil {
			fatal("Failed to write planner task: %v", err)
		}

		// Prompt with lock file deletion instruction
		initialPrompt := "Read tmp/planner_task.md and follow ALL instructions. The file contains the complete research planner guide and your specific task parameters. CRITICAL: YOU MUST DELETE .locks/.planner.lock AFTER YOU HAVE CREATED task.md FILE!"

		if err := runAgentInteractiveWithLock(agentName, *model, initialPrompt, absWorkDir, plannerLockFile); err != nil {
			logEntry("ERROR", "AGENT_FAILED", 0, "Planner failed", map[string]string{
				"error": err.Error(),
			})
			fatal("Planner failed: %v", err)
		}
	} else {
		// Non-interactive mode (-p or -f): auto-approve the plan
		plannerPrompt := buildPlannerPrompt(promptsDir, absWorkDir, userPrompt, true) // AUTO_APPROVE mode
		if err := runAgent(agentName, *model, plannerPrompt, absWorkDir); err != nil {
			logEntry("ERROR", "AGENT_FAILED", 0, "Planner failed", map[string]string{
				"error": err.Error(),
			})
			fatal("Planner failed: %v", err)
		}
	}

	// Verify task.md was created
	taskFile := filepath.Join(absWorkDir, "task.md")
	if !fileExists(taskFile) {
		logEntry("ERROR", "STATE_WRITE", 0, "Planner did not create task.md", nil)
		fatal("Planner did not create task.md")
	}
	logEntry("INFO", "AGENT_DONE", 0, "Planner completed", map[string]string{
		"output": "task.md",
	})
	success("Research plan created: task.md")

	// ========== RESEARCH LOOP ==========
	maxIterations := 10
	for iteration := 1; iteration <= maxIterations; iteration++ {
		// ========== PHASE 2: RESEARCH-SUPERVISOR ==========
		phase("RESEARCH-SUPERVISOR", fmt.Sprintf("Executing research tasks (iteration %d)", iteration))
		logEntry("INFO", "DISPATCH", iteration, "Dispatching Research-Supervisor", map[string]string{
			"phase":     "RESEARCH-SUPERVISOR",
			"iteration": fmt.Sprintf("%d", iteration),
		})

		supervisorPrompt := buildSupervisorPrompt(promptsDir, absWorkDir)
		if err := runAgent(agentName, *model, supervisorPrompt, absWorkDir); err != nil {
			logEntry("ERROR", "AGENT_FAILED", iteration, "Research-Supervisor failed", map[string]string{
				"error": err.Error(),
			})
			fatal("Research-Supervisor failed: %v", err)
		}
		logEntry("INFO", "AGENT_DONE", iteration, "Research-Supervisor completed", nil)
		success("Research tasks completed")

		// ========== PHASE 3: REFLECTOR ==========
		phase("REFLECTOR", "Analyzing research quality")
		logEntry("INFO", "DISPATCH", iteration, "Dispatching Reflector", map[string]string{
			"phase": "REFLECTOR",
		})

		reflectorPrompt := buildReflectorPrompt(promptsDir, absWorkDir)
		if err := runAgent(agentName, *model, reflectorPrompt, absWorkDir); err != nil {
			logEntry("ERROR", "AGENT_FAILED", iteration, "Reflector failed", map[string]string{
				"error": err.Error(),
			})
			fatal("Reflector failed: %v", err)
		}
		logEntry("INFO", "AGENT_DONE", iteration, "Reflector completed", nil)
		success("Reflection completed")

		// Check if more research is needed
		if !needsMoreResearch(taskFile) {
			logEntry("INFO", "REFLECTION", iteration, "Research sufficient, proceeding to synthesis", map[string]string{
				"recommendation": "READY_FOR_SYNTHESIS",
			})
			info("Reflector indicates research is sufficient")
			break
		}
		logEntry("INFO", "REFLECTION", iteration, "More research needed", map[string]string{
			"recommendation": "CONTINUE_RESEARCH",
		})
		info("Reflector added new tasks, continuing research loop...")
	}

	// ========== PHASE 4: SYNTHESIZER ==========
	phase("SYNTHESIZER", "Generating final report")
	logEntry("INFO", "DISPATCH", 0, "Dispatching Synthesizer", map[string]string{
		"phase": "SYNTHESIZER",
	})

	synthesizerPrompt := buildSynthesizerPrompt(promptsDir, absWorkDir, userPrompt)
	if err := runAgent(agentName, *model, synthesizerPrompt, absWorkDir); err != nil {
		logEntry("ERROR", "AGENT_FAILED", 0, "Synthesizer failed", map[string]string{
			"error": err.Error(),
		})
		fatal("Synthesizer failed: %v", err)
	}

	reportFile := filepath.Join(absWorkDir, "report.md")
	if !fileExists(reportFile) {
		logEntry("ERROR", "STATE_WRITE", 0, "Synthesizer did not create report.md", nil)
		fatal("Synthesizer did not create report.md")
	}
	logEntry("INFO", "AGENT_DONE", 0, "Synthesizer completed", map[string]string{
		"output": "report.md",
	})
	logEntry("INFO", "COMPLETED", 0, "Research workflow completed successfully", nil)
	success("Research complete! Report saved to: report.md")
}

// detectAgent finds the first available agent CLI
func detectAgent() string {
	// Priority order
	priority := []string{"claude", "copilot", "gemini"}
	for _, name := range priority {
		cfg := agentConfigs[name]
		if isCommandAvailable(cfg.Command) {
			return name
		}
	}
	return ""
}

// isCommandAvailable checks if a command is available in PATH
func isCommandAvailable(cmd string) bool {
	_, err := exec.LookPath(cmd)
	return err == nil
}

// runAgentInteractive runs the agent in interactive/conversation mode
// Uses -i flag to start interactive mode with an initial prompt
// Then connects stdin/stdout/stderr directly for user interaction
func runAgentInteractive(agentName, model, initialPrompt, workDir string) error {
	return runAgentInteractiveWithLock(agentName, model, initialPrompt, workDir, "")
}

// runAgentInteractiveWithLock runs the agent in interactive mode with optional lock file monitoring
// If lockFile is provided, the function monitors it and terminates the agent when the lock is deleted
func runAgentInteractiveWithLock(agentName, model, initialPrompt, workDir, lockFile string) error {
	cfg := agentConfigs[agentName]

	// For agents that support -i (like copilot), pass the prompt directly
	// For others (like claude), we need to use a file-based approach
	args := cfg.InteractiveArgs(initialPrompt, model, workDir)

	// Show user instructions
	fmt.Println()
	fmt.Printf("%s╔════════════════════════════════════════════════════════════════╗%s\n", colorCyan, colorReset)
	fmt.Printf("%s║  INTERACTIVE PLANNER MODE                                      ║%s\n", colorCyan, colorReset)
	fmt.Printf("%s╠════════════════════════════════════════════════════════════════╣%s\n", colorCyan, colorReset)
	fmt.Printf("%s║  The agent will process your research request and generate     ║%s\n", colorCyan, colorReset)
	fmt.Printf("%s║  a research plan. You can then discuss and refine the plan.    ║%s\n", colorCyan, colorReset)
	fmt.Printf("%s║                                                                ║%s\n", colorCyan, colorReset)
	fmt.Printf("%s║  When you approve the plan, the agent will create task.md      ║%s\n", colorCyan, colorReset)
	fmt.Printf("%s║  and the workflow will automatically continue.                 ║%s\n", colorCyan, colorReset)
	fmt.Printf("%s╚════════════════════════════════════════════════════════════════╝%s\n", colorCyan, colorReset)
	fmt.Println()

	info("Starting %s in interactive mode with -i flag...", agentName)

	cmd := exec.Command(cfg.Command, args...)
	cmd.Dir = workDir

	// Connect all stdio directly to terminal for full interaction
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// Start the agent process
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start agent: %w", err)
	}

	// Channel to signal process completion
	done := make(chan error, 1)
	go func() {
		done <- cmd.Wait()
	}()

	// If lock file is provided, monitor it
	if lockFile != "" {
		go func() {
			for {
				time.Sleep(500 * time.Millisecond)
				if _, err := os.Stat(lockFile); os.IsNotExist(err) {
					// Lock file deleted, wait a moment for agent to finish any output
					time.Sleep(1 * time.Second)
					fmt.Println()
					info("Lock file deleted, terminating agent...")
					// Terminate the agent process
					if cmd.Process != nil {
						cmd.Process.Kill()
					}
					return
				}
			}
		}()
	}

	// Wait for process to complete (either naturally or killed)
	err := <-done
	
	// If we killed the process due to lock deletion, that's not an error
	if lockFile != "" {
		if _, statErr := os.Stat(lockFile); os.IsNotExist(statErr) {
			// Lock was deleted, process was killed intentionally
			return nil
		}
	}

	if err != nil {
		return fmt.Errorf("agent exited with error: %w", err)
	}

	return nil
}

// runAgent executes an agent with the given prompt (non-interactive mode)
func runAgent(agentName, model, prompt, workDir string) error {
	return runAgentWithOptions(agentName, model, prompt, workDir, false)
}

// runAgentWithOptions executes an agent with the given prompt by calling PowerShell
// If interactive is true, stdin is connected to allow user interaction with the agent
func runAgentWithOptions(agentName, model, prompt, workDir string, interactive bool) error {
	cfg := agentConfigs[agentName]
	args := cfg.Args(prompt, model, workDir)

	// Write prompt to a temp file to avoid command line escaping issues
	tmpFile, err := os.CreateTemp("", "deepresearch-prompt-*.txt")
	if err != nil {
		return fmt.Errorf("failed to create temp file: %w", err)
	}
	tmpPromptPath := tmpFile.Name()
	defer os.Remove(tmpPromptPath)

	if _, err := tmpFile.WriteString(prompt); err != nil {
		tmpFile.Close()
		return fmt.Errorf("failed to write prompt to temp file: %w", err)
	}
	tmpFile.Close()

	// Build PowerShell command that reads prompt from file
	// $p = Get-Content -Raw 'tempfile'; copilot -p $p --yolo --add-dir ...
	var psArgs []string
	for i, arg := range args {
		if i == 1 && arg == prompt {
			// Skip the prompt, we'll inject it via variable
			continue
		}
		if i == 0 {
			// Skip -p, we'll add it with the variable
			continue
		}
		// Quote if contains spaces
		if strings.ContainsAny(arg, " \t") {
			psArgs = append(psArgs, fmt.Sprintf("'%s'", strings.ReplaceAll(arg, "'", "''")))
		} else {
			psArgs = append(psArgs, arg)
		}
	}

	psScript := fmt.Sprintf(
		"$p = Get-Content -Raw '%s'; & '%s' -p $p %s",
		strings.ReplaceAll(tmpPromptPath, "'", "''"),
		cfg.Command,
		strings.Join(psArgs, " "),
	)

	modeStr := "non-interactive"
	if interactive {
		modeStr = "interactive"
	}
	info("Executing via PowerShell (%s): %s -p <prompt> %s", modeStr, cfg.Command, strings.Join(psArgs, " "))

	cmd := exec.Command("pwsh", "-NoProfile", "-Command", psScript)
	cmd.Dir = workDir

	if interactive {
		// Interactive mode: connect stdin/stdout/stderr directly
		// This allows user to interact with the agent (e.g., approve/modify research plan)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		// Run and wait
		if err := cmd.Run(); err != nil {
			return fmt.Errorf("agent exited with error: %w", err)
		}
	} else {
		// Non-interactive mode: stream output but don't connect stdin
		// Create pipes for stdout and stderr
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			return fmt.Errorf("failed to create stdout pipe: %w", err)
		}
		stderr, err := cmd.StderrPipe()
		if err != nil {
			return fmt.Errorf("failed to create stderr pipe: %w", err)
		}

		// Start the command
		if err := cmd.Start(); err != nil {
			return fmt.Errorf("failed to start agent: %w", err)
		}

		// Stream output in real-time
		go streamOutput(stdout, os.Stdout)
		go streamOutput(stderr, os.Stderr)

		// Wait for completion
		if err := cmd.Wait(); err != nil {
			return fmt.Errorf("agent exited with error: %w", err)
		}
	}

	return nil
}

// streamOutput copies from reader to writer line by line
func streamOutput(r io.Reader, w io.Writer) {
	scanner := bufio.NewScanner(r)
	// Increase buffer size for long lines
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, 1024*1024)
	for scanner.Scan() {
		fmt.Fprintln(w, scanner.Text())
	}
}

// ========== LOGGING ==========

// initLogFile initializes the orchestrator log file
func initLogFile(baseDir string) {
	logPath := filepath.Join(baseDir, "logs", "orchestrator.log")
	var err error
	logFile, err = os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		// Don't fatal, just warn - logging is not critical
		info("Warning: Could not open log file: %v", err)
		logFile = nil
	}
}

// closeLogFile closes the log file
func closeLogFile() {
	if logFile != nil {
		logFile.Close()
	}
}

// logEntry writes a log entry to orchestrator.log
// Format: [TIMESTAMP] [LEVEL] [TYPE] [ITER] | summary | field1=value1, field2=value2
func logEntry(level, logType string, iteration int, summary string, fields map[string]string) {
	if logFile == nil {
		return
	}

	timestamp := time.Now().Format("2006-01-02T15:04:05.000Z07:00")

	// Build fields string
	var fieldParts []string
	for k, v := range fields {
		fieldParts = append(fieldParts, fmt.Sprintf("%s=%s", k, v))
	}
	fieldsStr := ""
	if len(fieldParts) > 0 {
		fieldsStr = " | " + strings.Join(fieldParts, ", ")
	}

	// Format: [TIMESTAMP] [LEVEL] [TYPE] [ITER] | summary | fields
	iterStr := fmt.Sprintf("[%d]", iteration)
	if iteration == 0 {
		iterStr = "[-]"
	}

	line := fmt.Sprintf("[%s] [%s] [%s] %s | %s%s\n",
		timestamp, level, logType, iterStr, summary, fieldsStr)

	logFile.WriteString(line)
}

// findPromptsDir locates the prompts/deep-research directory
func findPromptsDir() string {
	// Try relative to current directory
	candidates := []string{
		"prompts/deep-research",
		"../prompts/deep-research",
		"../../prompts/deep-research",
	}

	// Also try relative to executable
	if execPath, err := os.Executable(); err == nil {
		execDir := filepath.Dir(execPath)
		candidates = append(candidates,
			filepath.Join(execDir, "prompts/deep-research"),
			filepath.Join(execDir, "../prompts/deep-research"),
			filepath.Join(execDir, "../../prompts/deep-research"),
		)
	}

	for _, candidate := range candidates {
		if abs, err := filepath.Abs(candidate); err == nil {
			if _, err := os.Stat(abs); err == nil {
				return abs
			}
		}
	}
	return ""
}

// createDirs creates necessary directories
func createDirs(baseDir string) {
	dirs := []string{
		"assets/web",
		"assets/pdf",
		"assets/images",
		"assets/audio",
		"assets/ebook",
		"logs",
	}
	for _, dir := range dirs {
		path := filepath.Join(baseDir, dir)
		if err := os.MkdirAll(path, 0755); err != nil {
			fatal("Failed to create directory %s: %v", path, err)
		}
	}
}

// fileExists checks if a file exists
func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// needsMoreResearch checks if task.md indicates more research is needed
func needsMoreResearch(taskFile string) bool {
	content, err := os.ReadFile(taskFile)
	if err != nil {
		return false
	}

	contentStr := strings.ToLower(string(content))

	// Check for incomplete tasks ([ ] instead of [x])
	if strings.Contains(contentStr, "- [ ]") {
		return true
	}

	// Check for explicit status
	if strings.Contains(contentStr, "status: researching") ||
		strings.Contains(contentStr, "recommendation: continue_research") ||
		strings.Contains(contentStr, "recommendation: add_conflict_tasks") {
		return true
	}

	return false
}

// ========== PROMPT BUILDERS ==========

func buildPlannerPrompt(promptsDir, workDir, userPrompt string, skipApproval bool) string {
	plannerFile := filepath.Join(promptsDir, "planner.md")
	approvalMode := "INTERACTIVE"
	if skipApproval {
		approvalMode = "AUTO_APPROVE"
	}

	prompt := fmt.Sprintf(`FIRST: Read %s and follow ALL instructions.

WORKING_DIR: %s
APPROVAL_MODE: %s
`, plannerFile, workDir, approvalMode)

	if userPrompt != "" {
		prompt += fmt.Sprintf(`
USER_REQUEST: %s
`, userPrompt)
	} else {
		prompt += `
USER_REQUEST: (Read from stdin - wait for user input)
`
	}

	prompt += `
TASK: Create a research plan based on the user request. Generate task.md with the research DAG.
OUTPUT: task.md in WORKING_DIR

IMPORTANT: 
- Directories (assets/, logs/) are ALREADY created by the orchestrator
- Do NOT run any shell/terminal commands
- Only use file creation tools to create task.md
`
	return prompt
}

func buildSupervisorPrompt(promptsDir, workDir string) string {
	supervisorFile := filepath.Join(promptsDir, "research-supervisor.md")
	return fmt.Sprintf(`FIRST: Read %s and follow ALL instructions.

WORKING_DIR: %s
TASK: Execute all pending research tasks (E* tasks) in task.md. Dispatch Executor agents as needed.
Update task.md with results. Exit when all E* tasks are complete.
`, supervisorFile, workDir)
}

func buildReflectorPrompt(promptsDir, workDir string) string {
	reflectorFile := filepath.Join(promptsDir, "reflector.md")
	return fmt.Sprintf(`FIRST: Read %s and follow ALL instructions.

WORKING_DIR: %s
TASK: Analyze the research quality in task.md. Check completeness, conflicts, and gaps.
If more research is needed, add new tasks to task.md and set recommendation.
If research is sufficient, set status to SYNTHESIZING.
`, reflectorFile, workDir)
}

func buildSynthesizerPrompt(promptsDir, workDir, originalRequest string) string {
	synthesizerFile := filepath.Join(promptsDir, "synthesizer.md")
	prompt := fmt.Sprintf(`FIRST: Read %s and follow ALL instructions.

WORKING_DIR: %s
`, synthesizerFile, workDir)

	if originalRequest != "" {
		prompt += fmt.Sprintf(`ORIGINAL_USER_REQUEST: %s
`, originalRequest)
	}

	prompt += `TASK: Generate the final research report based on task.md knowledge graph.
OUTPUT: report.md in WORKING_DIR
`
	return prompt
}

// ========== OUTPUT HELPERS ==========

func phase(name, description string) {
	fmt.Printf("\n%s━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n", colorCyan, colorReset)
	fmt.Printf("%s▶ PHASE: %s%s\n", colorCyan, name, colorReset)
	fmt.Printf("  %s\n", description)
	fmt.Printf("%s━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n\n", colorCyan, colorReset)
}

func info(format string, args ...any) {
	fmt.Printf("%s[INFO]%s %s\n", colorBlue, colorReset, fmt.Sprintf(format, args...))
}

func success(format string, args ...any) {
	fmt.Printf("%s[SUCCESS]%s %s\n", colorGreen, colorReset, fmt.Sprintf(format, args...))
}

func fatal(format string, args ...any) {
	fmt.Printf("%s[ERROR]%s %s\n", colorRed, colorReset, fmt.Sprintf(format, args...))
	os.Exit(1)
}

// ANSI color codes
var (
	colorReset = "\033[0m"
	colorRed   = "\033[31m"
	colorGreen = "\033[32m"
	colorBlue  = "\033[34m"
	colorCyan  = "\033[36m"
)

func init() {
	// Disable colors on Windows if not supported
	if runtime.GOOS == "windows" {
		// Windows Terminal and modern PowerShell support ANSI codes
		// but we'll check for TERM or WT_SESSION
		if os.Getenv("WT_SESSION") == "" && os.Getenv("TERM") == "" {
			colorReset = ""
			colorRed = ""
			colorGreen = ""
			colorBlue = ""
			colorCyan = ""
		}
	}
}
