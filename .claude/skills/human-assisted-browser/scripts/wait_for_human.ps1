<#
.SYNOPSIS
    Human-in-the-Loop (HITL) wait script for anti-bot verification
.DESCRIPTION
    Creates a signal file and waits for human to complete verification.
    Agent auto-detects when verification passes, or human can manually
    remove the signal file as a fallback.
.PARAMETER Reason
    Reason for waiting (e.g., "reCAPTCHA detected on google.com")
.PARAMETER Timeout
    Maximum wait time in seconds (default: 300)
.PARAMETER SignalFile
    Path to signal file (default: .waiting-for-human)
.EXAMPLE
    .\wait_for_human.ps1 -Reason "CAPTCHA detected on bing.com"
    .\wait_for_human.ps1 -Reason "Login required" -Timeout 600
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Reason,
    
    [int]$Timeout = 300,
    
    [string]$SignalFile = ".waiting-for-human"
)

# Colors for console output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Cyan = "Cyan"
    White = "White"
}

function Write-Banner {
    param([string]$Message, [string]$Color = "Cyan")
    
    $border = "=" * 60
    Write-Host ""
    Write-Host $border -ForegroundColor $Color
    Write-Host $Message -ForegroundColor $Color
    Write-Host $border -ForegroundColor $Color
    Write-Host ""
}

function Send-Notification {
    param([string]$Title, [string]$Message)
    
    # Play system beep
    [Console]::Beep(800, 300)
    [Console]::Beep(1000, 300)
    [Console]::Beep(800, 300)
    
    # Windows Toast Notification (Windows 10+)
    try {
        $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode($Title)) | Out-Null
        $textNodes.Item(1).AppendChild($template.CreateTextNode($Message)) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PowerShell").Show($toast)
    }
    catch {
        # Fallback: Use BurntToast module if available
        if (Get-Module -ListAvailable -Name BurntToast) {
            New-BurntToastNotification -Text $Title, $Message
        }
        else {
            # Fallback: Simple message box
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show($Message, $Title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
        }
    }
}

function New-SignalFile {
    param([string]$FilePath, [string]$Reason)
    
    $content = @"
WAITING_FOR_HUMAN=true
REASON=$Reason
CREATED=$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
TIMEOUT=$Timeout seconds
---
Agent is waiting for human assistance.
✅ Agent will auto-detect when verification passes.
⚠️ If agent gets stuck, manually run: Remove-Item $FilePath
"@
    
    Set-Content -Path $FilePath -Value $content -Encoding UTF8
    Write-Host "📝 Signal file created: $FilePath" -ForegroundColor Yellow
}

function Show-HumanNotification {
    param([string]$Reason)
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║                                                                ║" -ForegroundColor Yellow
    Write-Host "║  🚨 HUMAN ASSISTANCE REQUIRED 🚨                               ║" -ForegroundColor Yellow
    Write-Host "║                                                                ║" -ForegroundColor Yellow
    Write-Host "║  Reason: $($Reason.PadRight(51))║" -ForegroundColor Yellow
    Write-Host "║                                                                ║" -ForegroundColor Yellow
    Write-Host "║  ✅ Agent will auto-detect when verification passes.          ║" -ForegroundColor Yellow
    Write-Host "║  ⚠️  If agent gets stuck, manually run:                        ║" -ForegroundColor Yellow
    Write-Host "║     Remove-Item $($SignalFile.PadRight(44))║" -ForegroundColor Yellow
    Write-Host "║                                                                ║" -ForegroundColor Yellow
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host ""
    
    Send-Notification -Title "🤖 Agent needs help!" -Message $Reason
}

function Wait-ForHuman {
    param(
        [string]$SignalPath,
        [int]$TimeoutSeconds
    )
    
    $elapsed = 0
    $checkInterval = 2  # seconds
    
    Write-Host "⏳ Waiting for human assistance..." -ForegroundColor Cyan
    Write-Host "   Timeout: $TimeoutSeconds seconds" -ForegroundColor Gray
    Write-Host ""
    
    while ($elapsed -lt $TimeoutSeconds) {
        # Check if signal file still exists
        if (-not (Test-Path $SignalPath)) {
            Write-Banner "✅ Human verification complete! Resuming..." "Green"
            return $true
        }
        
        # Progress indicator
        $remaining = $TimeoutSeconds - $elapsed
        $minutes = [math]::Floor($remaining / 60)
        $seconds = $remaining % 60
        Write-Host "`r⏳ Waiting... ($minutes`:$($seconds.ToString('00')) remaining)  " -NoNewline -ForegroundColor Cyan
        
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
    }
    
    Write-Host ""
    Write-Banner "⏰ Timeout reached. Human did not respond in time." "Red"
    
    # Cleanup signal file on timeout
    if (Test-Path $SignalPath) {
        Remove-Item $SignalPath -Force
    }
    
    return $false
}

# Main execution
Write-Banner "🤖 HITL Protocol Initiated" "Cyan"

# Create signal file
New-SignalFile -FilePath $SignalFile -Reason $Reason

# Notify human
Show-HumanNotification -Reason $Reason

# Wait for human
$result = Wait-ForHuman -SignalPath $SignalFile -TimeoutSeconds $Timeout

# Return exit code
if ($result) {
    exit 0
} else {
    exit 1
}
