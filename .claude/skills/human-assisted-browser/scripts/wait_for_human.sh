#!/bin/bash
# Human-in-the-Loop Verification Wait Script
# Usage: ./wait_for_human.sh [timeout_seconds] [signal_file]

TIMEOUT=${1:-300}  # Default 5 minutes
SIGNAL_FILE=${2:-.waiting-for-human}
POLL_INTERVAL=5

# Create signal file with context
create_signal() {
    local url="$1"
    local challenge_type="$2"
    
    cat > "$SIGNAL_FILE" << EOF
status: WAITING
url: ${url:-unknown}
detected_at: $(date -Iseconds)
challenge_type: ${challenge_type:-unknown}
message: |
  Please complete the verification in the browser window.
  Agent will auto-detect when done.
  If agent gets stuck after you pass verification, run: rm $SIGNAL_FILE
EOF
}

# Notify human (cross-platform)
notify_human() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  🔐 HUMAN VERIFICATION REQUIRED                               ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  Please complete the verification in the browser window.      ║"
    echo "║                                                               ║"
    echo "║  ✅ Agent will auto-detect when verification passes.          ║"
    echo "║  ⚠️  If agent gets stuck, manually run: rm $SIGNAL_FILE ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Try to play sound notification
    if command -v afplay &> /dev/null; then
        # macOS
        afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &
    elif command -v paplay &> /dev/null; then
        # Linux with PulseAudio
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null &
    elif command -v aplay &> /dev/null; then
        # Linux with ALSA
        aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null &
    fi
    
    # Try desktop notification
    if command -v notify-send &> /dev/null; then
        notify-send "Agent Paused" "Verification needed in browser" 2>/dev/null &
    elif command -v osascript &> /dev/null; then
        osascript -e 'display notification "Please complete verification in browser" with title "Agent Paused"' 2>/dev/null &
    fi
}

# Main wait loop
wait_for_human() {
    local elapsed=0
    
    while [ -f "$SIGNAL_FILE" ] && [ $elapsed -lt $TIMEOUT ]; do
        sleep $POLL_INTERVAL
        elapsed=$((elapsed + POLL_INTERVAL))
        
        # Progress indicator
        remaining=$((TIMEOUT - elapsed))
        printf "\r⏳ Waiting for human... %ds elapsed, %ds remaining " "$elapsed" "$remaining"
    done
    
    echo ""  # New line after progress
    
    if [ -f "$SIGNAL_FILE" ]; then
        echo "❌ Timeout after ${TIMEOUT}s waiting for human verification"
        rm -f "$SIGNAL_FILE"
        return 1
    else
        echo "✅ Human verification completed! Resuming agent..."
        return 0
    fi
}

# Entry point
main() {
    local url="$3"
    local challenge_type="$4"
    
    create_signal "$url" "$challenge_type"
    notify_human
    wait_for_human
    exit $?
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
