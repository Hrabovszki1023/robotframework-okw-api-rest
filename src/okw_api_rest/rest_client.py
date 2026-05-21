from __future__ import annotations

import requests

from .rest_context import RestContext


def send_request(ctx: RestContext, method: str) -> None:
    url = ctx.get_request_url()
    headers = ctx.get_headers()
    params = ctx.get_query_params() or None
    body = ctx.get_body()

    method = method.upper()
    content_type = headers.get("Content-Type", "")

    kwargs: dict = {"headers": headers, "params": params}

    if method in ("POST", "PUT", "PATCH") and body:
        if "application/x-www-form-urlencoded" in content_type:
            kwargs["data"] = body
        else:
            kwargs["json"] = body

    response = requests.request(method, url, **kwargs)
    ctx.store_response(response)
