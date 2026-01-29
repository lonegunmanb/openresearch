#!/usr/bin/env python3
"""
Browser State Utils - Check and manage browser storage state.

Provides utilities for checking login status across different websites
by examining cookies and localStorage in Playwright's storage state.
"""

import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


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


def get_browser_profile_dir() -> Path:
    """Get the browser profile directory path"""
    return get_project_root() / "browser_profile"


@dataclass
class SiteLoginCheck:
    """Site login check configuration"""
    name: str                          # Site name
    domains: List[str]                 # Related domain list
    required_cookies: List[str] = None # Required cookie names
    required_localstorage_keys: List[str] = None  # Required localStorage keys
    
    def __post_init__(self):
        self.required_cookies = self.required_cookies or []
        self.required_localstorage_keys = self.required_localstorage_keys or []


# Predefined site login check configurations
SITE_CONFIGS = {
    "zlibrary": SiteLoginCheck(
        name="Z-Library",
        domains=["z-library.sk", "z-lib.io", "z-lib.org", "singlelogin.re"],
        required_cookies=["remix_userid", "remix_userkey"],
    ),
    "google": SiteLoginCheck(
        name="Google",
        domains=["google.com", "accounts.google.com"],
        required_cookies=["SID", "HSID", "SSID"],
    ),
    "github": SiteLoginCheck(
        name="GitHub",
        domains=["github.com"],
        required_cookies=["logged_in", "user_session"],
    ),
}


def get_domain_from_url(url: str) -> str:
    """
    Extract domain from a URL.
    
    Args:
        url: Full URL (e.g., "https://www.example.com/path")
        
    Returns:
        Domain without www prefix (e.g., "example.com")
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    
    # Remove port if present
    if ':' in domain:
        domain = domain.split(':')[0]
    
    # Remove www. prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain.lower()


def load_storage_state(state_file: Path) -> Optional[Dict[str, Any]]:
    """
    Load storage_state.json file.
    
    Args:
        state_file: State file path
        
    Returns:
        Parsed JSON data, or None if file doesn't exist or is invalid
    """
    if not state_file.exists():
        return None
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_cookies_for_domain(state_data: Dict[str, Any], domain: str) -> List[Dict]:
    """
    Get all cookies for a specified domain.
    
    Args:
        state_data: storage_state data
        domain: Target domain
        
    Returns:
        List of matching cookies
    """
    cookies = state_data.get("cookies", [])
    matched = []
    
    for cookie in cookies:
        cookie_domain = cookie.get("domain", "")
        # Handle domains starting with . (subdomain wildcard)
        if cookie_domain.startswith("."):
            if domain.endswith(cookie_domain) or domain == cookie_domain[1:]:
                matched.append(cookie)
        elif cookie_domain == domain or domain.endswith("." + cookie_domain):
            matched.append(cookie)
    
    return matched


def get_localstorage_for_origin(state_data: Dict[str, Any], domain: str) -> Dict[str, str]:
    """
    Get localStorage data for a specified domain.
    
    Args:
        state_data: storage_state data
        domain: Target domain
        
    Returns:
        localStorage key-value dictionary
    """
    origins = state_data.get("origins", [])
    
    for origin in origins:
        origin_url = origin.get("origin", "")
        if domain in origin_url:
            localStorage = origin.get("localStorage", [])
            return {item["name"]: item["value"] for item in localStorage}
    
    return {}


def check_site_login(state_file: Path, site_key: str) -> Dict[str, Any]:
    """
    Check if a specified site is logged in.
    
    Args:
        state_file: storage_state.json file path
        site_key: Site identifier (e.g., "zlibrary", "google")
        
    Returns:
        Check result dictionary
    """
    result = {
        "logged_in": False,
        "site_name": "",
        "found_cookies": [],
        "missing_cookies": [],
        "details": ""
    }
    
    # Get site configuration
    config = SITE_CONFIGS.get(site_key)
    if not config:
        result["details"] = f"Unknown site: {site_key}"
        return result
    
    result["site_name"] = config.name
    
    # Load state file
    state_data = load_storage_state(state_file)
    if not state_data:
        result["details"] = f"State file does not exist or is invalid: {state_file}"
        return result
    
    # Collect cookies from all related domains
    all_cookies = {}
    for domain in config.domains:
        cookies = get_cookies_for_domain(state_data, domain)
        for cookie in cookies:
            all_cookies[cookie["name"]] = cookie
    
    # Check required cookies
    found = []
    missing = []
    
    for required_cookie in config.required_cookies:
        if required_cookie in all_cookies:
            found.append(required_cookie)
        else:
            missing.append(required_cookie)
    
    result["found_cookies"] = found
    result["missing_cookies"] = missing
    
    # Determine login status
    if config.required_cookies:
        result["logged_in"] = len(missing) == 0
    else:
        result["logged_in"] = len(all_cookies) > 0
    
    # Generate details
    if result["logged_in"]:
        result["details"] = f"Detected {config.name} login status (cookies: {', '.join(found)})"
    else:
        if missing:
            result["details"] = f"No {config.name} login detected (missing: {', '.join(missing)})"
        else:
            result["details"] = f"No login information found for {config.name}"
    
    return result


def check_domain_login(state_file: Path, domain: str) -> Dict[str, Any]:
    """
    Check if any login-related cookies exist for a domain.
    
    This is a generic check that doesn't require predefined site configs.
    It looks for any cookies associated with the domain.
    
    Args:
        state_file: storage_state.json file path
        domain: Domain to check (e.g., "example.com")
        
    Returns:
        Check result dictionary
    """
    result = {
        "logged_in": False,
        "domain": domain,
        "cookie_count": 0,
        "cookie_names": [],
        "details": ""
    }
    
    state_data = load_storage_state(state_file)
    if not state_data:
        result["details"] = f"State file does not exist or is invalid: {state_file}"
        return result
    
    cookies = get_cookies_for_domain(state_data, domain)
    result["cookie_count"] = len(cookies)
    result["cookie_names"] = [c.get("name", "") for c in cookies]
    
    # Consider logged in if there are any cookies for this domain
    # This is a heuristic - having cookies suggests some interaction/login
    if len(cookies) > 0:
        result["logged_in"] = True
        result["details"] = f"Found {len(cookies)} cookies for {domain}"
    else:
        result["details"] = f"No cookies found for {domain}"
    
    return result


def list_all_sites_in_state(state_file: Path) -> List[str]:
    """
    List all site domains in the state file.
    
    Args:
        state_file: storage_state.json file path
        
    Returns:
        List of domain names
    """
    state_data = load_storage_state(state_file)
    if not state_data:
        return []
    
    domains = set()
    
    # Extract domains from cookies
    for cookie in state_data.get("cookies", []):
        domain = cookie.get("domain", "").lstrip(".")
        if domain:
            domains.add(domain)
    
    # Extract domains from origins
    for origin in state_data.get("origins", []):
        origin_url = origin.get("origin", "")
        if "://" in origin_url:
            domain = origin_url.split("://")[1].split("/")[0]
            domains.add(domain)
    
    return sorted(domains)


def print_state_summary(state_file: Path):
    """Print state file summary"""
    state_data = load_storage_state(state_file)
    if not state_data:
        print(f"❌ State file does not exist or is invalid: {state_file}")
        return
    
    print(f"📁 State file: {state_file}")
    print(f"🍪 Cookies count: {len(state_data.get('cookies', []))}")
    print(f"💾 Origins count: {len(state_data.get('origins', []))}")
    print()
    
    domains = list_all_sites_in_state(state_file)
    print(f"🌐 Sites included ({len(domains)} total):")
    for domain in domains:
        print(f"   - {domain}")
    print()
    
    print("🔐 Known sites login status:")
    for site_key in SITE_CONFIGS:
        result = check_site_login(state_file, site_key)
        status = "✅" if result["logged_in"] else "❌"
        print(f"   {status} {result['site_name']}: {result['details']}")


if __name__ == "__main__":
    import sys
    
    # Default state file path - check browser profile first
    browser_profile = get_browser_profile_dir()
    
    # Playwright stores state in different locations depending on usage
    # Check common locations
    possible_paths = [
        browser_profile / "Default" / "Cookies",  # Chrome-style
        Path.cwd() / "storage_state.json",  # Manual export
    ]
    
    state_file = None
    for path in possible_paths:
        if path.exists():
            state_file = path
            break
    
    if state_file is None:
        # Use a default path for display
        state_file = Path.cwd() / "storage_state.json"
    
    print("=" * 60)
    print("Browser State Check Tool")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        # Check specific domain
        domain = sys.argv[1]
        result = check_domain_login(state_file, domain)
        status = "✅" if result["logged_in"] else "❌"
        print(f"{status} {domain}: {result['details']}")
        if result["cookie_names"]:
            print(f"   Cookies: {', '.join(result['cookie_names'][:5])}")
            if len(result["cookie_names"]) > 5:
                print(f"   ... and {len(result['cookie_names']) - 5} more")
    else:
        print_state_summary(state_file)
