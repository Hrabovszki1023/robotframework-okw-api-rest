from __future__ import annotations

import json
import os

import requests
from requests.auth import HTTPBasicAuth
from robot.api import logger

from .rest_context import RestContext


def _build_auth(auth_cfg: dict):
    """Build requests auth object from YAML config."""
    auth_type = auth_cfg.get("auth_type", "none").lower()

    if auth_type == "basic":
        user = auth_cfg.get("auth_user", "")
        password = auth_cfg.get("auth_password", "")
        return HTTPBasicAuth(user, password)

    return None


def _expand_path(path: str | None) -> str | None:
    """Expand ~ and environment variables in file paths."""
    if path is None:
        return None
    return os.path.expanduser(os.path.expandvars(path))


def _build_ssl_kwargs(ssl_cfg: dict) -> dict:
    """Build SSL-related kwargs for requests from YAML config."""
    kwargs = {}

    # verify: True (default), False, or path to CA bundle
    verify = ssl_cfg.get("verify_ssl", True)
    if isinstance(verify, str) and verify.lower() in ("false", "no", "0"):
        verify = False
    elif isinstance(verify, str) and verify.lower() in ("true", "yes", "1"):
        verify = True
    kwargs["verify"] = verify

    # CA bundle overrides verify (path to CA file)
    ca_bundle = _expand_path(ssl_cfg.get("ca_bundle"))
    if ca_bundle:
        kwargs["verify"] = ca_bundle

    # Client certificate (mTLS)
    client_cert = _expand_path(ssl_cfg.get("client_cert"))
    client_key = _expand_path(ssl_cfg.get("client_key"))
    if client_cert and client_key:
        kwargs["cert"] = (client_cert, client_key)
    elif client_cert:
        kwargs["cert"] = client_cert

    return kwargs


def _apply_auth_header(headers: dict, auth_cfg: dict) -> None:
    """Apply header-based auth (api_key, bearer) to request headers."""
    auth_type = auth_cfg.get("auth_type", "none").lower()

    if auth_type == "api_key":
        header_name = auth_cfg.get("auth_header", "X-API-Key")
        api_key = auth_cfg.get("auth_key", "")
        if api_key:
            headers[header_name] = api_key

    elif auth_type == "bearer":
        token = auth_cfg.get("auth_token", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"


def send_request(ctx: RestContext, method: str) -> None:
    import time

    url = ctx.get_request_url()
    headers = ctx.get_headers()
    params = ctx.get_query_params() or None
    body = ctx.get_body()

    method = method.upper()
    content_type = headers.get("Content-Type", "")

    # Auth: header-based (api_key, bearer)
    _apply_auth_header(headers, ctx.auth)

    # Auth: request-based (basic)
    auth = _build_auth(ctx.auth)

    # SSL config
    ssl_kwargs = _build_ssl_kwargs(ctx.ssl)

    kwargs: dict = {"headers": headers, "params": params, "auth": auth}
    kwargs.update(ssl_kwargs)

    if method in ("POST", "PUT", "PATCH") and ctx.has_files():
        headers.pop("Content-Type", None)
        kwargs["data"] = body or None
        kwargs["files"] = ctx.get_files()
    elif method in ("POST", "PUT", "PATCH") and body:
        if "application/x-www-form-urlencoded" in content_type:
            kwargs["data"] = body
        else:
            kwargs["json"] = body

    # Retry config
    retry_count = ctx.retry.get("retry_count", 0)
    retry_delay_ms = ctx.retry.get("retry_delay", 1000)
    retry_on = ctx.retry.get("retry_on", set())

    _log_request(method, url, headers, params, body, content_type,
                 files=ctx.get_files() if ctx.has_files() else None)
    response = requests.request(method, url, **kwargs)

    attempt = 1
    while response.status_code in retry_on and attempt <= retry_count:
        logger.info(
            f"<<< {response.status_code} — retry {attempt}/{retry_count} "
            f"(waiting {retry_delay_ms}ms)"
        )
        time.sleep(retry_delay_ms / 1000.0)
        response = requests.request(method, url, **kwargs)
        attempt += 1

    ctx.store_response(response)
    _log_response(response)


def _format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _is_text_mime(mime: str) -> bool:
    return mime.startswith("text/") or mime in (
        "application/json", "application/xml", "application/javascript",
    )


def _file_preview(data: bytes, mime: str, n: int = 80) -> str:
    """Human-readable file content preview like browser DevTools."""
    if _is_text_mime(mime):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if len(text) <= n:
            preview = repr(text)
        else:
            preview = repr(text[:n // 2]) + " ... " + repr(text[-(n // 2):])
        return f"Content: {preview}"
    head = data[:20]
    return f"Content: (binary, first 20 bytes: {head.hex(' ')})"


def _mask_sensitive(obj, _depth=0):
    """Mask password fields in a dict for safe logging."""
    if not isinstance(obj, dict) or _depth > 10:
        return obj
    masked = {}
    for k, v in obj.items():
        if "password" in k.lower() or "token" in k.lower() or "secret" in k.lower():
            masked[k] = "***"
        elif isinstance(v, dict):
            masked[k] = _mask_sensitive(v, _depth + 1)
        else:
            masked[k] = v
    return masked


def _log_request(method, url, headers, params, body, content_type, files=None):
    """Log request details as formatted JSON to Robot log."""
    parts = [f">>> {method} {url}"]

    if params:
        parts.append(f"    Query: {json.dumps(params, ensure_ascii=False)}")

    if files:
        for name, (fname, data, mime) in files:
            size = _format_size(len(data))
            preview = _file_preview(data, mime)
            parts.append(f"    File: {name}: {fname} ({mime}, {size})")
            parts.append(f"          {preview}")

    if body:
        safe_body = _mask_sensitive(body) if isinstance(body, dict) else body
        try:
            formatted = json.dumps(safe_body, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            formatted = str(safe_body)
        parts.append(f"    Request Body:\n{formatted}")

    logger.info("\n".join(parts))


def _log_response(response):
    """Log response status and body as formatted JSON to Robot log."""
    parts = [f"<<< {response.status_code} {response.reason}"]

    body = response.text
    if body:
        try:
            parsed = json.loads(body)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            formatted = body
        parts.append(f"    Response Body:\n{formatted}")

    logger.info("\n".join(parts))
