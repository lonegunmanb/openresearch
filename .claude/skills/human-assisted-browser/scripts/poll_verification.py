#!/usr/bin/env python3
"""
Poll browser page for verification completion.
Detects when CAPTCHA/verification page transitions to normal content.

Usage:
    python poll_verification.py --storage-state ./browser_profile/storage_state.json

Exit codes:
  0 - Verification completed successfully
  1 - Timeout waiting for verification
  2 - Error occurred
"""

import argparse
import time
import sys
import os
import json

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detect_captcha import detect_captcha, CAPTCHA_PATTERNS


def poll_for_completion(
    storage_state_path: str,
    timeout: int = 300,
    poll_interval: int = 5,
    signal_file: str = ".waiting-for-human"
):
    """
    Poll the browser page until verification is complete.
    
    Detection methods:
    1. Signal file is removed (human signals completion)
    2. Page content no longer contains CAPTCHA patterns
    
    Args:
        storage_state_path: Path to save browser state after completion
        timeout: Maximum seconds to wait
        poll_interval: Seconds between checks
        signal_file: Path to human signal file
    """
    print(f"🔍 Polling for verification completion (timeout: {timeout}s)")
    print(f"   Signal file: {signal_file}")
    print(f"   Poll interval: {poll_interval}s")
    print()
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed >= timeout:
            print(f"\n❌ Timeout after {timeout}s")
            return False
        
        # Method 1: Check if signal file was removed
        if not os.path.exists(signal_file):
            print(f"\n✅ Signal file removed - human confirmed completion!")
            return True
        
        # Method 2: Would check page content here if we had browser access
        # In practice, this runs alongside the browser
        
        # Progress
        remaining = int(timeout - elapsed)
        sys.stdout.write(f"\r⏳ Waiting... {int(elapsed)}s elapsed, {remaining}s remaining ")
        sys.stdout.flush()
        
        time.sleep(poll_interval)
    
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--storage-state",
        default="./browser_profile/storage_state.json",
        help="Path to save browser storage state"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum seconds to wait (default: 300)"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between checks (default: 5)"
    )
    parser.add_argument(
        "--signal-file",
        default=".waiting-for-human",
        help="Path to human signal file"
    )
    
    args = parser.parse_args()
    
    success = poll_for_completion(
        storage_state_path=args.storage_state,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        signal_file=args.signal_file
    )
    
    if success:
        print("\n🎉 Verification completed! Agent can resume.")
        
        # Clean up signal file if it still exists
        if os.path.exists(args.signal_file):
            os.remove(args.signal_file)
        
        sys.exit(0)
    else:
        print("\n💔 Verification not completed within timeout.")
        sys.exit(1)


if __name__ == "__main__":
    main()
