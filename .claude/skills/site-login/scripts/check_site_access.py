#!/usr/bin/env python3
"""
Check Site Access - Pre-flight check before searching a site.

Determines if a site is accessible for searching:
- Already logged in: Can proceed with search
- Skipped: User declined login, should not search this site
- Needs login: Should trigger login flow first

Usage:
    python check_site_access.py <domain_or_url>

Exit codes:
    0 - Accessible (logged in or no login required)
    1 - Skipped (user previously declined to login)
    2 - Needs login (not logged in, login required)
"""

import sys
import json
from pathlib import Path

from lock_utils import is_site_skipped
from browser_state_utils import (
    get_domain_from_url,
    check_domain_login,
    check_site_login,
    SITE_CONFIGS,
    get_browser_profile_dir,
)


def get_storage_state_path() -> Path:
    """Get the storage state file path"""
    return get_browser_profile_dir() / "storage_state.json"


def check_access(domain_or_url: str, output_json: bool = False) -> int:
    """
    Check if a site is accessible for searching.
    
    Args:
        domain_or_url: Domain name or full URL
        output_json: If True, output result as JSON
        
    Returns:
        Exit code (0=accessible, 1=skipped, 2=needs login)
    """
    # Extract domain if URL provided
    if '://' in domain_or_url or '/' in domain_or_url:
        domain = get_domain_from_url(domain_or_url)
    else:
        domain = domain_or_url.lower()
    
    result = {
        "domain": domain,
        "status": "",
        "logged_in": False,
        "skipped": False,
        "needs_login": False,
        "details": ""
    }
    
    # Step 1: Check if site is skipped
    if is_site_skipped(domain):
        result["status"] = "skipped"
        result["skipped"] = True
        result["details"] = f"Site {domain} is marked as skipped (user declined login)"
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"⏭️ {domain}: SKIPPED")
            print(f"   {result['details']}")
        
        return 1
    
    # Step 2: Check login status
    storage_state = get_storage_state_path()
    
    # Try predefined site config first
    site_key = None
    for key, config in SITE_CONFIGS.items():
        if domain in config.domains or any(domain.endswith(d) for d in config.domains):
            site_key = key
            break
    
    if site_key:
        login_result = check_site_login(storage_state, site_key)
    else:
        login_result = check_domain_login(storage_state, domain)
    
    result["logged_in"] = login_result.get("logged_in", False)
    
    if result["logged_in"]:
        result["status"] = "accessible"
        result["details"] = login_result.get("details", f"Logged in to {domain}")
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ {domain}: ACCESSIBLE")
            print(f"   {result['details']}")
        
        return 0
    else:
        result["status"] = "needs_login"
        result["needs_login"] = True
        result["details"] = login_result.get("details", f"Not logged in to {domain}")
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"🔐 {domain}: NEEDS LOGIN")
            print(f"   {result['details']}")
        
        return 2


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python check_site_access.py <domain_or_url> [--json]")
        print("")
        print("Examples:")
        print("  python check_site_access.py z-library.sk")
        print("  python check_site_access.py https://github.com")
        print("  python check_site_access.py google.com --json")
        print("")
        print("Exit codes:")
        print("  0 - Accessible (logged in)")
        print("  1 - Skipped (user declined)")
        print("  2 - Needs login")
        sys.exit(1)
    
    domain_or_url = sys.argv[1]
    output_json = "--json" in sys.argv or "-j" in sys.argv
    
    exit_code = check_access(domain_or_url, output_json)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
