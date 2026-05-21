from __future__ import annotations

import os

import requests
from requests.auth import HTTPBasicAuth

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

    if method in ("POST", "PUT", "PATCH") and body:
        if "application/x-www-form-urlencoded" in content_type:
            kwargs["data"] = body
        else:
            kwargs["json"] = body

    response = requests.request(method, url, **kwargs)
    ctx.store_response(response)
