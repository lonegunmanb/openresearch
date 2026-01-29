#!/usr/bin/env python3
"""
Lock utilities for concurrent agent access control.

Provides file-based locking mechanism to prevent multiple agents
from attempting to login to the same site simultaneously.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Walks up from the script location to find the directory containing .mcp.json
    """
    current = Path(__file__).resolve().parent
    
    # Walk up to find project root (where .mcp.json is)
    for _ in range(10):  # Max 10 levels up
        if (current / ".mcp.json").exists():
            return current
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    # Fallback to cwd
    return Path.cwd()


def get_locks_dir() -> Path:
    """Get the locks directory path (project root/.locks)"""
    return get_project_root() / ".locks"


# Global browser lock name - ensures only one Playwright browser instance at a time
GLOBAL_BROWSER_LOCK = "__browser__"


def get_skip_dir() -> Path:
    """Get the skip-website directory path (project root/.skip-website)"""
    return get_project_root() / ".skip-website"


def ensure_dirs() -> None:
    """Ensure lock and skip directories exist"""
    get_locks_dir().mkdir(parents=True, exist_ok=True)
    get_skip_dir().mkdir(parents=True, exist_ok=True)


def get_lock_file_path(lock_name: str) -> Path:
    """Get the lock file path for a given lock name"""
    # Sanitize lock name for use as filename
    safe_name = lock_name.replace(":", "_").replace("/", "_")
    return get_locks_dir() / safe_name


def get_skip_file_path(domain: str) -> Path:
    """Get the skip marker file path for a domain"""
    safe_domain = domain.replace(":", "_").replace("/", "_")
    return get_skip_dir() / safe_domain


def acquire_lock(lock_name: str, agent_id: Optional[str] = None) -> bool:
    """
    Attempt to acquire a lock.
    
    Uses atomic file creation with O_CREAT | O_EXCL flags to ensure
    only one process can create the lock file.
    
    Args:
        lock_name: The name of the lock (e.g., domain name or "__browser__")
        agent_id: Optional identifier for the agent acquiring the lock
        
    Returns:
        True if lock acquired successfully, False if lock already exists
    """
    ensure_dirs()
    lock_file = get_lock_file_path(lock_name)
    
    lock_data = {
        "pid": os.getpid(),
        "acquired_at": datetime.now().isoformat(),
        "agent_id": agent_id or "unknown",
        "lock_name": lock_name
    }
    
    try:
        # Use O_CREAT | O_EXCL for atomic creation (fails if file exists)
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            json.dump(lock_data, f, indent=2)
        return True
    except FileExistsError:
        return False
    except OSError as e:
        # On Windows, OSError with errno 17 means file exists
        if e.errno == 17:  # EEXIST
            return False
        raise


def release_lock(lock_name: str) -> bool:
    """
    Release a lock.
    
    Args:
        lock_name: The name of the lock to release
        
    Returns:
        True if lock was released, False if lock didn't exist
    """
    lock_file = get_lock_file_path(lock_name)
    try:
        lock_file.unlink()
        return True
    except FileNotFoundError:
        return False


def is_locked(lock_name: str) -> bool:
    """Check if a lock is currently held"""
    return get_lock_file_path(lock_name).exists()


def get_lock_info(lock_name: str) -> Optional[Dict[str, Any]]:
    """
    Get information about an existing lock.
    
    Args:
        lock_name: The name of the lock to check
        
    Returns:
        Lock data dict or None if not locked
    """
    lock_file = get_lock_file_path(lock_name)
    if not lock_file.exists():
        return None
    
    try:
        with open(lock_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"error": "Could not read lock file"}


def wait_for_lock(lock_name: str, timeout: int = 300, poll_interval: float = 1.0) -> bool:
    """
    Block until a lock is released or timeout is reached.
    
    Args:
        lock_name: The name of the lock to wait for
        timeout: Maximum time to wait in seconds (default: 300)
        poll_interval: Time between checks in seconds (default: 1.0)
        
    Returns:
        True if lock was released within timeout, False if timeout reached
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if not is_locked(lock_name):
            return True
        time.sleep(poll_interval)
    
    return False


def is_site_skipped(domain: str) -> bool:
    """
    Check if a site has been marked as skipped.
    
    Args:
        domain: The domain to check
        
    Returns:
        True if site is skipped, False otherwise
    """
    return get_skip_file_path(domain).exists()


def skip_site(domain: str, reason: str = "timeout") -> None:
    """
    Mark a site as skipped (user declined to login).
    
    Args:
        domain: The domain to skip
        reason: Reason for skipping
    """
    ensure_dirs()
    skip_file = get_skip_file_path(domain)
    
    skip_data = {
        "domain": domain,
        "skipped_at": datetime.now().isoformat(),
        "reason": reason
    }
    
    with open(skip_file, 'w') as f:
        json.dump(skip_data, f, indent=2)


def unskip_site(domain: str) -> bool:
    """
    Remove the skip marker for a site.
    
    Args:
        domain: The domain to unskip
        
    Returns:
        True if marker was removed, False if it didn't exist
    """
    skip_file = get_skip_file_path(domain)
    try:
        skip_file.unlink()
        return True
    except FileNotFoundError:
        return False


def list_locks() -> list:
    """List all currently locked domains"""
    locks_dir = get_locks_dir()
    if not locks_dir.exists():
        return []
    return [f.name for f in locks_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]


def list_skipped_sites() -> list:
    """List all skipped domains"""
    skip_dir = get_skip_dir()
    if not skip_dir.exists():
        return []
    return [f.name for f in skip_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]


# ============================================================
# Global Browser Lock Functions
# ============================================================

def acquire_browser_lock(agent_id: Optional[str] = None) -> bool:
    """
    Acquire the global browser lock.
    
    Only one Playwright browser instance can run at a time because they
    share the same browser_profile directory.
    
    Args:
        agent_id: Optional identifier for the agent acquiring the lock
        
    Returns:
        True if lock acquired successfully, False if lock already exists
    """
    return acquire_lock(GLOBAL_BROWSER_LOCK, agent_id)


def release_browser_lock() -> bool:
    """
    Release the global browser lock.
    
    Returns:
        True if lock was released, False if lock didn't exist
    """
    return release_lock(GLOBAL_BROWSER_LOCK)


def is_browser_locked() -> bool:
    """Check if the global browser lock is held"""
    return is_locked(GLOBAL_BROWSER_LOCK)


def get_browser_lock_info() -> Optional[Dict[str, Any]]:
    """Get information about the current browser lock holder"""
    return get_lock_info(GLOBAL_BROWSER_LOCK)


def wait_for_browser_lock(timeout: int = 300, poll_interval: float = 1.0) -> bool:
    """
    Block until the browser lock is released or timeout is reached.
    
    Args:
        timeout: Maximum time to wait in seconds (default: 300)
        poll_interval: Time between checks in seconds (default: 1.0)
        
    Returns:
        True if lock was released within timeout, False if timeout reached
    """
    return wait_for_lock(GLOBAL_BROWSER_LOCK, timeout, poll_interval)


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lock_utils.py <command> [domain]")
        print("Commands: acquire, release, check, wait, skip, unskip, list-locks, list-skipped")
        print("Browser lock commands: browser-acquire, browser-release, browser-check, browser-wait")
        sys.exit(1)
    
    command = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Global browser lock commands
    if command == "browser-acquire":
        agent_id = domain  # Use domain arg as agent_id if provided
        if acquire_browser_lock(agent_id):
            print(f"✅ Browser lock acquired")
        else:
            info = get_browser_lock_info()
            print(f"❌ Failed to acquire browser lock (held by: {info})")
            sys.exit(1)
    
    elif command == "browser-release":
        if release_browser_lock():
            print(f"✅ Browser lock released")
        else:
            print(f"⚠️ No browser lock found")
    
    elif command == "browser-check":
        if is_browser_locked():
            info = get_browser_lock_info()
            print(f"🔒 Browser is locked: {info}")
            sys.exit(1)
        else:
            print(f"🔓 Browser is not locked")
    
    elif command == "browser-wait":
        print(f"⏳ Waiting for browser lock to be released...")
        if wait_for_browser_lock():
            print(f"✅ Browser lock released")
        else:
            print(f"❌ Timeout waiting for browser lock")
            sys.exit(1)
    
    # Domain-specific lock commands
    elif command == "acquire" and domain:
        if acquire_lock(domain):
            print(f"✅ Lock acquired for {domain}")
        else:
            print(f"❌ Failed to acquire lock for {domain}")
            sys.exit(1)
    
    elif command == "release" and domain:
        if release_lock(domain):
            print(f"✅ Lock released for {domain}")
        else:
            print(f"⚠️ No lock found for {domain}")
    
    elif command == "check" and domain:
        if is_locked(domain):
            info = get_lock_info(domain)
            print(f"🔒 {domain} is locked: {info}")
        else:
            print(f"🔓 {domain} is not locked")
    
    elif command == "wait" and domain:
        print(f"⏳ Waiting for {domain} lock to be released...")
        if wait_for_lock(domain):
            print(f"✅ Lock released for {domain}")
        else:
            print(f"❌ Timeout waiting for {domain}")
            sys.exit(1)
    
    elif command == "skip" and domain:
        skip_site(domain)
        print(f"⏭️ Site {domain} marked as skipped")
    
    elif command == "unskip" and domain:
        if unskip_site(domain):
            print(f"✅ Skip marker removed for {domain}")
        else:
            print(f"⚠️ No skip marker found for {domain}")
    
    elif command == "list-locks":
        locks = list_locks()
        print(f"🔒 Locked domains ({len(locks)}):")
        for d in locks:
            print(f"  - {d}")
    
    elif command == "list-skipped":
        skipped = list_skipped_sites()
        print(f"⏭️ Skipped domains ({len(skipped)}):")
        for d in skipped:
            print(f"  - {d}")
    
    else:
        print(f"Unknown command or missing domain: {command}")
        sys.exit(1)
