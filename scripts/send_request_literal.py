#!/usr/bin/env python3
"""Small editable HTTP request sender using hardcoded literals.

Edit the REQUEST_SPEC dictionary below, then run:
  python3 scripts/send_request_literal.py
"""

import json
import sys

try:
    import requests
except ImportError:
    print("Missing dependency: requests")
    print("Install with: pip install requests")
    sys.exit(1)


REQUEST_SPEC = {
    "rendered_url": "http://localhost:50118/app/api/credentials/username/name%ZZ",
    "method": "GET",
    "header": {
        "Content-Type": "*/*"
    },
    "body": {}
}


def main() -> None:
    method = REQUEST_SPEC.get("method", "GET").upper()
    url = REQUEST_SPEC["rendered_url"]
    headers = REQUEST_SPEC.get("header", {})
    body = REQUEST_SPEC.get("body", {})

    kwargs = {
        "headers": headers,
        "timeout": 30,
    }

    # For methods that usually carry payload, send body as JSON.
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        kwargs["json"] = body

    resp = requests.request(method, url, **kwargs)

    print(f"[request] {method} {url}")
    print(f"[status] {resp.status_code}")
    print("[response headers]")
    for k, v in resp.headers.items():
        print(f"{k}: {v}")

    print("[response body]")
    text = resp.text
    try:
        parsed = resp.json()
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except ValueError:
        print(text)


if __name__ == "__main__":
    main()
