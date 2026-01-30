#!/usr/bin/env python3
"""
Site Login - Generic site login with browser automation.

Opens a browser window for user to manually login to a specified site.
Monitors the browser process and waits for it to close.
Supports concurrent access control via file-based locking.

Usage:
    python site_login.py <url>
    python site_login.py https://z-library.sk
    python site_login.py https://github.com

Exit codes:
    0 - Success (logged in or already logged in)
    1 - Skipped (user previously declined)
    2 - Timeout (300s, site marked as skipped)
    3 - Failed (max retries, no valid login detected)
"""

import sys
import time
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright not installed")
    print("Please run: pip install playwright && playwright install")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("❌ psutil not installed")
    print("Please run: pip install psutil")
    sys.exit(1)

from lock_utils import (
    acquire_lock,
    release_lock,
    wait_for_lock,
    is_site_skipped,
    skip_site,
    is_locked,
    acquire_browser_lock,
    release_browser_lock,
    is_browser_locked,
    wait_for_browser_lock,
    get_browser_lock_info,
)
from browser_state_utils import (
    get_domain_from_url,
    check_domain_login,
    get_browser_profile_dir,
)


# Configuration
LOGIN_TIMEOUT_SECONDS = 300  # 5 minutes
MAX_RETRIES = 3
BROWSER_CHECK_INTERVAL = 1.0  # seconds


def get_storage_state_path() -> Path:
    """Get the storage state file path"""
    return get_browser_profile_dir() / "storage_state.json"


def wait_for_context_close(context, storage_state_path: Path, timeout: int = LOGIN_TIMEOUT_SECONDS) -> bool:
    """
    Wait for the browser context to be closed by user.
    
    Uses Playwright's page close event instead of unreliable PID detection.
    Periodically saves storage state while waiting.
    
    Args:
        context: Playwright BrowserContext instance
        storage_state_path: Path to save storage state
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if context was closed by user, False if timeout reached
    """
    import threading
    
    # Use an event to signal when all pages are closed
    all_pages_closed = threading.Event()
    
    def on_page_close(page):
        # Check if this was the last page
        try:
            remaining = len(context.pages)
            if remaining == 0:
                all_pages_closed.set()
        except:
            all_pages_closed.set()
    
    # Register close handler for all existing pages
    for page in context.pages:
        page.on("close", on_page_close)
    
    # Also register for any new pages that might be created
    def on_new_page(page):
        page.on("close", on_page_close)
    
    context.on("page", on_new_page)
    
    start_time = time.time()
    last_save_time = start_time
    save_interval = 5.0  # Save storage state every 5 seconds
    
    while time.time() - start_time < timeout:
        # Check if all pages closed via event
        if all_pages_closed.is_set():
            try:
                context.storage_state(path=str(storage_state_path))
            except:
                pass
            return True
        
        # Periodically save storage state while browser is open
        current_time = time.time()
        if current_time - last_save_time >= save_interval:
            try:
                context.storage_state(path=str(storage_state_path))
            except:
                pass  # Context may be closing
            last_save_time = current_time
        
        # Fallback: Try to access pages - will fail if context closed unexpectedly
        try:
            pages = context.pages
            if len(pages) == 0:
                try:
                    context.storage_state(path=str(storage_state_path))
                except:
                    pass
                return True
        except Exception:
            # Context disconnected
            return True
        
        time.sleep(BROWSER_CHECK_INTERVAL)
    
    return False


def perform_login(url: str, domain: str, retry_count: int = 0) -> bool:
    """
    Open browser and wait for user to login.
    
    Args:
        url: The URL to navigate to
        domain: The domain being logged into
        retry_count: Current retry attempt number
        
    Returns:
        True if login successful, False otherwise
    """
    browser_profile = get_browser_profile_dir()
    browser_profile.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"🔐 Site Login: {domain}")
    print(f"{'='*60}")
    print(f"\nAttempt {retry_count + 1} of {MAX_RETRIES}")
    print(f"\nInstructions:")
    print(f"  1. Browser will open and navigate to: {url}")
    print(f"  2. Complete the login process manually")
    print(f"  3. Close the browser window when done")
    print(f"  4. Login status will be verified automatically")
    print(f"\n⏱️  Timeout: {LOGIN_TIMEOUT_SECONDS} seconds")
    print(f"{'='*60}\n")
    
    storage_state = get_storage_state_path()
    
    with sync_playwright() as p:
        print("🚀 Launching browser...")
        
        # Launch persistent context (shares profile with MCP)
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(browser_profile),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Get or create a page
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            print(f"📖 Navigating to {url}...")
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            print("⏳ Waiting for browser to be closed...")
            print("   (Close the browser window after completing login)\n")
            
            # Wait for context/browser to close or timeout (also saves storage state periodically)
            closed = wait_for_context_close(context, storage_state, LOGIN_TIMEOUT_SECONDS)
            
            if not closed:
                print(f"\n⏰ Timeout reached ({LOGIN_TIMEOUT_SECONDS}s)")
                print("   User did not complete login in time")
                return False
            
            print("🔍 Browser closed, verifying login status...")
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            try:
                context.close()
            except:
                pass
    
    # Verify login after browser is closed
    # Storage state was saved periodically during the wait loop
    result = check_domain_login(storage_state, domain)
    
    if result["logged_in"]:
        print(f"\n✅ Login verified for {domain}")
        print(f"   {result['details']}")
        return True
    else:
        print(f"\n❌ No login detected for {domain}")
        print(f"   {result['details']}")
        return False


def site_login(url: str) -> int:
    """
    Main login flow with lock management.
    
    Args:
        url: The URL to login to
        
    Returns:
        Exit code (0=success, 1=skipped, 2=timeout, 3=failed)
    """
    domain = get_domain_from_url(url)
    
    print(f"🌐 Target: {url}")
    print(f"📍 Domain: {domain}")
    
    # Step 1: Check if site is skipped
    if is_site_skipped(domain):
        print(f"\n⏭️ Site {domain} is marked as skipped")
        print("   User previously declined to login")
        return 1
    
    # Step 2: Check if already logged in
    storage_state = get_storage_state_path()
    result = check_domain_login(storage_state, domain)
    
    if result["logged_in"]:
        print(f"\n✅ Already logged in to {domain}")
        print(f"   {result['details']}")
        return 0
    
    # Step 3: Try to acquire GLOBAL BROWSER lock (not domain-specific)
    # This is necessary because only one Playwright browser can use browser_profile at a time
    print(f"\n🔒 Acquiring browser lock...")
    
    if not acquire_browser_lock(agent_id=f"site_login:{domain}"):
        lock_info = get_browser_lock_info()
        print(f"   Browser lock exists: {lock_info}")
        print(f"   Waiting for browser lock to be released...")
        
        if not wait_for_browser_lock(timeout=LOGIN_TIMEOUT_SECONDS):
            print(f"\n❌ Timeout waiting for browser lock")
            return 3
        
        # After lock released, check if login succeeded (another agent might have done it)
        result = check_domain_login(storage_state, domain)
        if result["logged_in"]:
            print(f"\n✅ Login completed by another agent")
            return 0
        
        # Try to acquire lock again
        if not acquire_browser_lock(agent_id=f"site_login:{domain}"):
            print(f"\n❌ Could not acquire browser lock")
            return 3
    
    print(f"   Browser lock acquired ✓")
    
    # Step 4: Perform login with retries
    try:
        for retry in range(MAX_RETRIES):
            success = perform_login(url, domain, retry)
            
            if success:
                return 0
            
            if retry < MAX_RETRIES - 1:
                print(f"\n🔄 Retrying... ({retry + 2}/{MAX_RETRIES})")
            else:
                print(f"\n❌ Max retries reached")
        
        # Check if timeout occurred (user didn't close browser in time)
        # In this case, mark site as skipped
        print(f"\n⏭️ Marking {domain} as skipped")
        skip_site(domain, reason="login_timeout_or_declined")
        return 2
        
    finally:
        # Always release GLOBAL BROWSER lock
        print(f"\n🔓 Releasing browser lock")
        release_browser_lock()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python site_login.py <url>")
        print("")
        print("Examples:")
        print("  python site_login.py https://z-library.sk")
        print("  python site_login.py https://github.com")
        print("")
        print("Exit codes:")
        print("  0 - Success (logged in)")
        print("  1 - Skipped (user previously declined)")
        print("  2 - Timeout (marked as skipped)")
        print("  3 - Failed (max retries)")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    exit_code = site_login(url)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
