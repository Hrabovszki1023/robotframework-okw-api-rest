#!/usr/bin/env python3
"""Convert browser API capture JSON to OKW REST Robot Framework keywords.

Usage:
    python capture2robot.py capture.json [--service AquaAPI] [--out output.robot]

Input: JSON array from browser extension capture (Chrome webRequest format).
Output: Robot Framework test file with OKW REST keywords.

Filters:
- Only xmlhttprequest (API calls), skips main_frame/stylesheet/script/image
- Strips browser-internal headers (sec-ch-*, Sec-Fetch-*, Cookie, User-Agent, ...)
- Extracts base_url from first request
- Generates endpoint paths relative to base_url
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode

SKIP_TYPES = {"main_frame", "sub_frame", "stylesheet", "script", "image", "font", "media", "other"}

SKIP_HEADERS = {
    "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform",
    "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest", "sec-fetch-user",
    "upgrade-insecure-requests",
    "user-agent", "accept", "accept-encoding", "accept-language",
    "origin", "referer", "cookie", "connection",
    "cache-control", "pragma",
}

RELEVANT_HEADERS = {
    "authorization", "x-auth-token", "x-api-key", "x-api-client",
    "x-csrf-token", "x-request-id",
}


def parse_headers(header_list: list[dict]) -> dict[str, str]:
    """Extract relevant headers from capture format."""
    result = {}
    for h in header_list:
        name = h.get("name", "")
        value = h.get("value", "")
        if name.lower() in SKIP_HEADERS:
            continue
        if name.lower() in RELEVANT_HEADERS or name.lower().startswith("x-"):
            result[name] = value
    return result


def extract_base_url(url: str) -> str:
    """Extract base URL (scheme + host + common path prefix)."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def extract_endpoint(url: str, base_url: str) -> tuple[str, dict]:
    """Extract endpoint path and query parameters from URL."""
    parsed = urlparse(url)
    base_parsed = urlparse(base_url)

    path = parsed.path
    if base_parsed.path and base_parsed.path != "/" and path.startswith(base_parsed.path):
        path = path[len(base_parsed.path):]
    if not path.startswith("/"):
        path = "/" + path

    params = parse_qs(parsed.query, keep_blank_values=True)
    flat_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

    return path, flat_params


def find_common_api_prefix(entries: list[dict]) -> str:
    """Find common API path prefix from all URLs."""
    paths = []
    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        if url:
            parsed = urlparse(url)
            paths.append(parsed.path)

    if not paths:
        return ""

    parts_list = [p.strip("/").split("/") for p in paths]
    common = []
    for segments in zip(*parts_list):
        if len(set(segments)) == 1:
            common.append(segments[0])
        else:
            break

    return "/" + "/".join(common) if common else ""


def convert_entry(entry: dict, base_url: str) -> dict | None:
    """Convert a single capture entry to keyword data."""
    req = entry.get("request", {})
    resp = entry.get("response", {})

    req_type = req.get("type", "")
    if req_type in SKIP_TYPES:
        return None

    method = req.get("method", "GET")
    url = req.get("url", "")
    status = resp.get("statusCode", 0)
    headers = parse_headers(req.get("requestHeaders", []))
    content_type = ""
    for h in req.get("requestHeaders", []):
        if h.get("name", "").lower() == "content-type":
            content_type = h.get("value", "")

    endpoint, query_params = extract_endpoint(url, base_url)

    return {
        "reqId": entry.get("reqId", ""),
        "method": method,
        "endpoint": endpoint,
        "query_params": query_params,
        "headers": headers,
        "content_type": content_type,
        "status": status,
        "url": url,
    }


def generate_robot(entries: list[dict], service_name: str, base_url: str) -> str:
    """Generate Robot Framework test file content."""
    lines = [
        "*** Settings ***",
        "Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI",
        "",
        "*** Test Cases ***",
    ]

    api_prefix = find_common_api_prefix(entries)

    converted = []
    for entry in entries:
        data = convert_entry(entry, base_url + api_prefix)
        if data:
            converted.append(data)

    if not converted:
        lines.append("# No API calls found in capture.")
        return "\n".join(lines)

    for i, data in enumerate(converted, 1):
        ep = data["endpoint"]
        method = data["method"]
        test_name = f"API Call {i} {method} {ep}"
        test_name = test_name.replace("/", " ").replace("  ", " ").strip()

        lines.append(f"{test_name}")
        lines.append(f"    RESTStart              {service_name}")
        lines.append(f"")
        lines.append(f"    RESTSelectEndpoint     {ep}")

        for name, value in data["headers"].items():
            if name.lower() == "content-type":
                continue
            lines.append(f"    RESTSetHeader          {name}    {value}")

        for param, value in data["query_params"].items():
            lines.append(f"    RESTSetValue           ?{param}    {value}")

        if method in ("POST", "PUT", "PATCH"):
            lines.append(f"    # TODO: Request-Body-Felder aus Capture ergaenzen")
            lines.append(f"    # RESTSetValue           field    value")

        lines.append(f"    RESTSendRequest        {method}")
        lines.append(f"")

        if data["status"]:
            lines.append(f"    RESTVerifyStatus       {data['status']}")

        lines.append(f"")
        lines.append(f"    RESTStop")
        lines.append(f"")

    # Generate YAML hint
    lines.append("")
    lines.append("# --- YAML Locator ---")
    lines.append(f"# Datei: locators/{service_name}.yaml")
    lines.append(f"#")
    lines.append(f"# {service_name}:")
    lines.append(f"#   __self__:")
    lines.append(f"#     class: okw_api_rest.library.OkwApiRestLibrary")
    lines.append(f"#     base_url: {base_url}{api_prefix}")

    ct = "application/json"
    if converted:
        ct = converted[0].get("content_type", ct) or ct
    lines.append(f"#     content_type: {ct}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert browser API capture to OKW REST Robot keywords")
    parser.add_argument("input", help="JSON capture file")
    parser.add_argument("--service", default="CapturedAPI", help="Service name for YAML (default: CapturedAPI)")
    parser.add_argument("--out", help="Output .robot file (default: stdout)")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: Expected JSON array.", file=sys.stderr)
        sys.exit(1)

    api_entries = [e for e in data if e.get("request", {}).get("type") not in SKIP_TYPES]
    if not api_entries:
        print("No API calls found in capture.", file=sys.stderr)
        sys.exit(1)

    first_url = api_entries[0]["request"]["url"]
    base_url = extract_base_url(first_url)

    robot_content = generate_robot(data, args.service, base_url)

    if args.out:
        Path(args.out).write_text(robot_content, encoding="utf-8")
        print(f"Written: {args.out}")
    else:
        print(robot_content)


if __name__ == "__main__":
    main()
