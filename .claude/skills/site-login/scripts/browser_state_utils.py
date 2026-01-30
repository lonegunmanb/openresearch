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
    auth_cookie_patterns: List[str] = None  # Patterns to match auth cookies
    localstorage_keys: List[str] = None  # localStorage keys to check
    
    def __post_init__(self):
        self.required_cookies = self.required_cookies or []
        self.auth_cookie_patterns = self.auth_cookie_patterns or []
        self.localstorage_keys = self.localstorage_keys or []


def get_site_configs_path() -> Path:
    """Get the path to site_configs.json"""
    return Path(__file__).parent / "site_configs.json"


def load_site_configs() -> Dict[str, SiteLoginCheck]:
    """
    Load site configurations from JSON file.
    Falls back to hardcoded defaults if file not found.
    """
    config_path = get_site_configs_path()
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            configs = {}
            for key, site in data.get("sites", {}).items():
                configs[key] = SiteLoginCheck(
                    name=site.get("name", key),
                    domains=site.get("domains", []),
                    required_cookies=site.get("required_cookies", []),
                    auth_cookie_patterns=site.get("auth_cookie_patterns", []),
                    localstorage_keys=site.get("localstorage_keys", []),
                )
            return configs
        except (json.JSONDecodeError, IOError, KeyError):
            pass
    
    # Fallback defaults
    return {
        "github": SiteLoginCheck(
            name="GitHub",
            domains=["github.com"],
            required_cookies=["logged_in", "user_session"],
        ),
        "google": SiteLoginCheck(
            name="Google",
            domains=["google.com", "accounts.google.com"],
            required_cookies=["SID", "HSID"],
        ),
    }


def load_generic_detection_config() -> Dict[str, Any]:
    """Load generic detection settings from config file."""
    config_path = get_site_configs_path()
    
    defaults = {
        "auth_cookie_patterns": [
            "session", "sess", "token", "auth", "user", "login", "logged",
            "jwt", "access", "sid", "credential", "identity"
        ],
        "auth_localstorage_patterns": [
            "token", "auth", "user", "session", "jwt", "access"
        ],
        "min_cookie_value_length": 10,
        "min_auth_cookies_for_login": 1,
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("generic_detection", defaults)
        except (json.JSONDecodeError, IOError):
            pass
    
    return defaults


# Load configs at module level
SITE_CONFIGS = load_site_configs()
GENERIC_DETECTION = load_generic_detection_config()


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
    Check if a domain has valid login cookies/localStorage.
    
    Uses a multi-tier approach:
    1. Check if domain matches a known site config (exact rules)
    2. Use enhanced generic detection (patterns + value validation)
    
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
        "auth_cookies": [],
        "localstorage_auth": [],
        "details": ""
    }
    
    # First, check if this domain matches any known site config
    for site_key, config in SITE_CONFIGS.items():
        for config_domain in config.domains:
            if domain == config_domain or domain.endswith(f".{config_domain}") or config_domain.endswith(f".{domain}"):
                # Use site-specific check
                site_result = check_site_login(state_file, site_key)
                result["logged_in"] = site_result.get("logged_in", False)
                result["auth_cookies"] = site_result.get("found_cookies", [])
                result["details"] = site_result.get("details", "")
                return result
    
    # Generic detection for unknown sites
    state_data = load_storage_state(state_file)
    if not state_data:
        result["details"] = f"State file does not exist or is invalid: {state_file}"
        return result
    
    cookies = get_cookies_for_domain(state_data, domain)
    result["cookie_count"] = len(cookies)
    
    if not cookies:
        result["details"] = f"No cookies found for {domain}"
        return result
    
    # Get generic detection settings
    patterns = GENERIC_DETECTION.get("auth_cookie_patterns", [])
    min_value_len = GENERIC_DETECTION.get("min_cookie_value_length", 10)
    min_auth_cookies = GENERIC_DETECTION.get("min_auth_cookies_for_login", 1)
    
    # Find auth cookies: name matches pattern AND value looks like a token
    auth_cookies = []
    for cookie in cookies:
        cookie_name = cookie.get("name", "").lower()
        cookie_value = cookie.get("value", "")
        
        # Check if cookie name matches any auth pattern
        matches_pattern = any(p in cookie_name for p in patterns)
        
        # Check if value looks like a real token (not empty, not too short)
        has_valid_value = len(cookie_value) >= min_value_len
        
        if matches_pattern and has_valid_value:
            auth_cookies.append(cookie.get("name"))
    
    result["auth_cookies"] = auth_cookies
    
    # Check localStorage too
    ls_patterns = GENERIC_DETECTION.get("auth_localstorage_patterns", [])
    localstorage = get_localstorage_for_origin(state_data, domain)
    
    auth_ls_keys = []
    for key, value in localstorage.items():
        key_lower = key.lower()
        if any(p in key_lower for p in ls_patterns) and len(value) >= min_value_len:
            auth_ls_keys.append(key)
    
    result["localstorage_auth"] = auth_ls_keys
    
    # Determine login status
    total_auth = len(auth_cookies) + len(auth_ls_keys)
    result["logged_in"] = total_auth >= min_auth_cookies
    
    # Generate details
    if result["logged_in"]:
        auth_sources = []
        if auth_cookies:
            auth_sources.append(f"cookies: {auth_cookies[:3]}")
        if auth_ls_keys:
            auth_sources.append(f"localStorage: {auth_ls_keys[:3]}")
        result["details"] = f"Found auth indicators for {domain} ({', '.join(auth_sources)})"
    else:
        result["details"] = f"Found {len(cookies)} cookies for {domain}, but no valid auth indicators"
    
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
