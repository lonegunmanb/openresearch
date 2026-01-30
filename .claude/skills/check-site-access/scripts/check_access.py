#!/usr/bin/env python3
"""
Check Site Access - Pre-flight check before searching a site.

Determines if a site is accessible for searching with custom storage state path:
- Already logged in: Can proceed with search
- Skipped: User declined login, should not search this site
- Needs login: Should trigger login flow first

Usage:
    python check_access.py <domain> --storage-state <path> --skip-dir <path>
    python check_access.py github.com --storage-state ./profile/storage_state.json --skip-dir ./.skip-website

Exit codes:
    0 - Accessible (logged in or no login required)
    1 - Skipped (user previously declined to login)
    2 - Needs login (not logged in, login required)
    3 - Error (invalid paths, missing files)
"""

import sys
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SiteLoginCheck:
    """Site login check configuration"""
    name: str
    domains: List[str]
    required_cookies: List[str]
    auth_cookie_patterns: List[str]
    localstorage_keys: List[str]
    
    def matches_domain(self, domain: str) -> bool:
        """Check if domain matches this site config"""
        domain = domain.lower()
        for d in self.domains:
            if domain == d or domain.endswith(f".{d}") or d.endswith(f".{domain}"):
                return True
        return False


def get_site_configs_path() -> Path:
    """Get the path to site_configs.json"""
    return Path(__file__).parent / "site_configs.json"


def load_site_configs() -> Dict[str, SiteLoginCheck]:
    """Load site configurations from JSON file."""
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
            auth_cookie_patterns=[],
            localstorage_keys=[],
        ),
        "google": SiteLoginCheck(
            name="Google",
            domains=["google.com", "accounts.google.com"],
            required_cookies=["SID", "HSID"],
            auth_cookie_patterns=[],
            localstorage_keys=[],
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
    """Extract domain from a URL or return as-is if already a domain."""
    if "://" in url:
        parsed = urlparse(url)
        domain = parsed.netloc
    else:
        domain = url.split("/")[0]
    
    # Remove port if present
    if ":" in domain:
        domain = domain.split(":")[0]
    
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    
    return domain.lower()


def is_site_skipped(domain: str, skip_dir: Path) -> bool:
    """Check if a site is marked as skipped."""
    if not skip_dir.exists():
        return False
    
    safe_domain = domain.replace(":", "_").replace("/", "_")
    skip_file = skip_dir / safe_domain
    return skip_file.exists()


def load_storage_state(storage_state_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse storage state JSON file."""
    if not storage_state_path.exists():
        return None
    
    try:
        with open(storage_state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_cookies_for_domain(storage_state: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
    """Extract cookies that match a domain from storage state."""
    cookies = storage_state.get("cookies", [])
    matching_cookies = []
    
    for cookie in cookies:
        cookie_domain = cookie.get("domain", "").lstrip(".")
        if cookie_domain == domain or domain.endswith(f".{cookie_domain}") or cookie_domain.endswith(f".{domain}"):
            matching_cookies.append(cookie)
    
    return matching_cookies


def get_localstorage_for_origin(storage_state: Dict[str, Any], domain: str) -> Dict[str, str]:
    """Get localStorage data for a specified domain."""
    origins = storage_state.get("origins", [])
    
    for origin in origins:
        origin_url = origin.get("origin", "")
        if domain in origin_url:
            localStorage = origin.get("localStorage", [])
            return {item["name"]: item["value"] for item in localStorage}
    
    return {}


def check_site_login(storage_state: Dict[str, Any], site_config: SiteLoginCheck) -> Dict[str, Any]:
    """Check login status for a predefined site configuration."""
    result = {
        "logged_in": False,
        "site_name": site_config.name,
        "details": "",
        "found_cookies": [],
        "missing_cookies": [],
    }
    
    # Collect cookies from all related domains
    all_cookies = {}
    for domain in site_config.domains:
        for cookie in get_cookies_for_domain(storage_state, domain):
            all_cookies[cookie.get("name")] = cookie
    
    # Check for required cookies
    found = []
    missing = []
    
    for required in site_config.required_cookies:
        if required in all_cookies:
            found.append(required)
        else:
            missing.append(required)
    
    # Also check auth_cookie_patterns if required_cookies is empty
    if not site_config.required_cookies and site_config.auth_cookie_patterns:
        for cookie_name in all_cookies.keys():
            name_lower = cookie_name.lower()
            if any(p in name_lower for p in site_config.auth_cookie_patterns):
                found.append(cookie_name)
    
    result["found_cookies"] = found
    result["missing_cookies"] = missing
    
    # Determine login status
    if site_config.required_cookies:
        result["logged_in"] = len(missing) == 0 and len(found) > 0
    else:
        result["logged_in"] = len(found) > 0
    
    if result["logged_in"]:
        result["details"] = f"Logged in to {site_config.name} (found: {found})"
    else:
        if missing:
            result["details"] = f"Not logged in to {site_config.name}, missing: {missing}"
        else:
            result["details"] = f"No login indicators found for {site_config.name}"
    
    return result


def check_domain_login(storage_state: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """
    Check login status for a domain using enhanced detection.
    
    First tries known site configs, then falls back to generic detection
    with pattern matching and value validation.
    """
    result = {
        "logged_in": False,
        "details": "",
        "auth_cookies": [],
        "localstorage_auth": [],
    }
    
    # First, check if domain matches a known site config
    for site_key, config in SITE_CONFIGS.items():
        if config.matches_domain(domain):
            site_result = check_site_login(storage_state, config)
            result["logged_in"] = site_result.get("logged_in", False)
            result["auth_cookies"] = site_result.get("found_cookies", [])
            if site_result.get("missing_cookies"):
                result["details"] = f"Not logged in to {config.name}, missing: {site_result['missing_cookies']}"
            else:
                result["details"] = site_result.get("details", "")
            return result
    
    # Generic detection for unknown sites
    cookies = get_cookies_for_domain(storage_state, domain)
    
    if not cookies:
        result["details"] = f"No cookies found for {domain}"
        return result
    
    # Get detection settings
    patterns = GENERIC_DETECTION.get("auth_cookie_patterns", [])
    min_value_len = GENERIC_DETECTION.get("min_cookie_value_length", 10)
    min_auth = GENERIC_DETECTION.get("min_auth_cookies_for_login", 1)
    
    # Find auth cookies: name matches pattern AND value looks valid
    auth_cookies = []
    for cookie in cookies:
        cookie_name = cookie.get("name", "")
        cookie_value = cookie.get("value", "")
        name_lower = cookie_name.lower()
        
        matches_pattern = any(p in name_lower for p in patterns)
        has_valid_value = len(cookie_value) >= min_value_len
        
        if matches_pattern and has_valid_value:
            auth_cookies.append(cookie_name)
    
    result["auth_cookies"] = auth_cookies
    
    # Check localStorage too
    ls_patterns = GENERIC_DETECTION.get("auth_localstorage_patterns", [])
    localstorage = get_localstorage_for_origin(storage_state, domain)
    
    auth_ls_keys = []
    for key, value in localstorage.items():
        key_lower = key.lower()
        if any(p in key_lower for p in ls_patterns) and len(value) >= min_value_len:
            auth_ls_keys.append(key)
    
    result["localstorage_auth"] = auth_ls_keys
    
    # Determine login status
    total_auth = len(auth_cookies) + len(auth_ls_keys)
    result["logged_in"] = total_auth >= min_auth
    
    if result["logged_in"]:
        auth_sources = []
        if auth_cookies:
            auth_sources.append(f"cookies: {auth_cookies[:3]}")
        if auth_ls_keys:
            auth_sources.append(f"localStorage: {auth_ls_keys[:3]}")
        result["details"] = f"Found auth for {domain} ({', '.join(auth_sources)})"
    else:
        result["details"] = f"Found {len(cookies)} cookies for {domain}, but no valid auth indicators"
    
    return result


def check_access(domain: str, storage_state_path: Path, skip_dir: Path, output_json: bool = False) -> int:
    """
    Check if a site is accessible for searching.
    
    Returns:
        Exit code (0=accessible, 1=skipped, 2=needs login, 3=error)
    """
    domain = get_domain_from_url(domain)
    
    result = {
        "domain": domain,
        "status": "",
        "logged_in": False,
        "skipped": False,
        "needs_login": False,
        "error": None,
        "details": "",
    }
    
    # Step 1: Check if site is skipped
    if is_site_skipped(domain, skip_dir):
        result["status"] = "skipped"
        result["skipped"] = True
        result["details"] = f"Site {domain} is marked as skipped (user declined login)"
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"SKIPPED {domain}: {result['details']}")
        
        return 1
    
    # Step 2: Load storage state
    storage_state = load_storage_state(storage_state_path)
    
    if storage_state is None:
        result["status"] = "needs_login"
        result["needs_login"] = True
        result["details"] = f"Storage state not found or invalid: {storage_state_path}"
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"NEEDS_LOGIN {domain}: {result['details']}")
        
        return 2
    
    # Step 3: Check login status with enhanced detection
    login_result = check_domain_login(storage_state, domain)
    
    result["logged_in"] = login_result.get("logged_in", False)
    result["details"] = login_result.get("details", "")
    
    if result["logged_in"]:
        result["status"] = "accessible"
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"ACCESSIBLE {domain}: {result['details']}")
        
        return 0
    else:
        result["status"] = "needs_login"
        result["needs_login"] = True
        
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"NEEDS_LOGIN {domain}: {result['details']}")
        
        return 2


def main():
    parser = argparse.ArgumentParser(
        description="Check if a website is accessible (logged in, skipped, or needs login)"
    )
    parser.add_argument(
        "domain",
        help="Domain or URL to check (e.g., github.com, https://z-library.sk)"
    )
    parser.add_argument(
        "--storage-state",
        required=True,
        type=Path,
        help="Path to Playwright storage state JSON file"
    )
    parser.add_argument(
        "--skip-dir",
        required=True,
        type=Path,
        help="Path to directory containing skip markers"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    exit_code = check_access(
        domain=args.domain,
        storage_state_path=args.storage_state,
        skip_dir=args.skip_dir,
        output_json=args.json
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
