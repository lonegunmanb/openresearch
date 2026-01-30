#!/usr/bin/env python3
"""
Detect if current page contains anti-bot verification challenges.
Returns exit code and JSON output for agent consumption.

Exit codes:
  0 - No verification detected, page is accessible
  1 - Verification detected, human assistance needed
  2 - Error occurred
"""

import sys
import json
import re
from typing import Tuple, Optional

# Patterns that indicate anti-bot verification
CAPTCHA_PATTERNS = [
    # reCAPTCHA
    r"recaptcha",
    r"g-recaptcha",
    r"I'm not a robot",
    r"I am not a robot",
    
    # hCaptcha
    r"hcaptcha",
    r"h-captcha",
    
    # Generic challenge
    r"verify you are human",
    r"prove you are human",
    r"confirm you are human",
    r"please complete the challenge",
    r"complete the security check",
    r"unusual traffic",
    r"automated queries",
    r"robot check",
    r"bot detection",
    r"security challenge",
    r"access denied",
    r"blocked",
    
    # Cloudflare
    r"checking your browser",
    r"ray id",
    r"cloudflare",
    r"please wait while we verify",
    r"just a moment",
    r"enable javascript and cookies",
    
    # PerimeterX / HUMAN
    r"press & hold",
    r"perimeterx",
    
    # DataDome
    r"datadome",
    
    # Specific sites
    r"sorry/index\?continue",  # Google
    r"validate your browser",
]

# URL patterns that indicate verification pages
CAPTCHA_URL_PATTERNS = [
    r"google\.com/sorry",
    r"recaptcha\.net",
    r"hcaptcha\.com",
    r"challenges\.cloudflare\.com",
    r"/captcha",
    r"/challenge",
    r"/verify",
]


def detect_captcha(content: str, url: str = "") -> Tuple[bool, Optional[str]]:
    """
    Detect if page content or URL indicates anti-bot verification.
    
    Returns:
        (is_captcha: bool, detected_type: Optional[str])
    """
    content_lower = content.lower()
    url_lower = url.lower()
    
    # Check URL patterns first
    for pattern in CAPTCHA_URL_PATTERNS:
        if re.search(pattern, url_lower):
            return True, f"URL pattern: {pattern}"
    
    # Check content patterns
    for pattern in CAPTCHA_PATTERNS:
        if re.search(pattern, content_lower):
            return True, f"Content pattern: {pattern}"
    
    return False, None


def main():
    """Read page content from stdin or file and detect CAPTCHA."""
    content = ""
    url = ""
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print(__doc__)
            sys.exit(0)
        elif sys.argv[1] == "--url":
            url = sys.argv[2] if len(sys.argv) > 2 else ""
    
    # Read content from stdin
    if not sys.stdin.isatty():
        content = sys.stdin.read()
    
    # Detect
    is_captcha, detected_type = detect_captcha(content, url)
    
    result = {
        "captcha_detected": is_captcha,
        "detected_type": detected_type,
        "url": url,
        "action_required": "human_verification" if is_captcha else "none"
    }
    
    print(json.dumps(result, indent=2))
    
    sys.exit(1 if is_captcha else 0)


if __name__ == "__main__":
    main()
