from __future__ import annotations


class RestContext:
    """Holds the mutable state for one REST service session."""

    def __init__(
        self,
        base_url: str,
        content_type: str = "application/json",
        auth: dict | None = None,
        ssl: dict | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.content_type = content_type
        self.auth = auth or {}
        self.ssl = ssl or {}

        self._endpoint: str | None = None
        self._body: dict = {}
        self._query_params: dict = {}
        self._headers: dict = {}
        self._context_path: str | None = None

        self._response = None
        self._response_json: dict | None = None
        self._response_headers: dict = {}
        self._status_code: int | None = None

    def select_endpoint(self, path: str):
        self._endpoint = path if path.startswith("/") else f"/{path}"
        self._body = {}
        self._query_params = {}
        self._headers = {}
        self._context_path = None

    def set_context(self, path: str):
        self._context_path = path

    def set_value(self, field: str, value: str, force_string: bool = False):
        typed = value if force_string else self._auto_type(value)
        if field.startswith("?"):
            self._query_params[field[1:]] = value
        elif self._context_path:
            self._set_nested(self._body, f"{self._context_path}.{field}", typed)
        elif "[" in field:
            self._set_nested(self._body, field, typed)
        else:
            self._body[field] = typed

    def set_value_as_list(self, field: str, values: list[str]):
        """Set a field as a JSON array of auto-typed values."""
        typed_list = [self._auto_type(v) for v in values]
        if self._context_path:
            self._set_nested(self._body, f"{self._context_path}.{field}", typed_list)
        else:
            self._body[field] = typed_list

    @staticmethod
    def _auto_type(value: str):
        """Convert string value to native JSON type where unambiguous."""
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() == "null" or value == "$NULL":
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def set_header(self, name: str, value: str):
        self._headers[name] = value

    def get_request_url(self) -> str:
        if not self._endpoint:
            raise RuntimeError("No endpoint selected. Call RESTSelectEndpoint first.")
        return f"{self.base_url}{self._endpoint}"

    def get_body(self) -> dict:
        return self._body

    def get_query_params(self) -> dict:
        return self._query_params

    def get_headers(self) -> dict:
        headers = dict(self._headers)
        if "Content-Type" not in headers:
            headers["Content-Type"] = self.content_type
        return headers

    def store_response(self, response):
        self._response = response
        self._status_code = response.status_code
        self._response_headers = dict(response.headers)
        try:
            self._response_json = response.json()
        except Exception:
            self._response_json = None

    def get_response_value(self, field_path: str) -> str:
        if self._response_json is None:
            raise RuntimeError("No JSON response available.")
        path = f"{self._context_path}.{field_path}" if self._context_path else field_path
        return str(self._resolve_path(self._response_json, path))

    def get_response_status(self) -> int:
        if self._status_code is None:
            raise RuntimeError("No response available. Call RESTSendRequest first.")
        return self._status_code

    def get_response_header(self, name: str) -> str:
        if not self._response_headers:
            raise RuntimeError("No response available.")
        for k, v in self._response_headers.items():
            if k.lower() == name.lower():
                return v
        raise KeyError(f"Response header '{name}' not found.")

    def get_response_time_ms(self) -> float:
        if self._response is None:
            raise RuntimeError("No response available.")
        return self._response.elapsed.total_seconds() * 1000

    def get_response_body(self) -> str:
        if self._response is None:
            raise RuntimeError("No response available.")
        return self._response.text

    @staticmethod
    def _resolve_path(obj, path: str):
        for part in path.split("."):
            if "[" in part:
                key, idx_str = part.split("[", 1)
                idx = int(idx_str.rstrip("]"))
                if key:
                    obj = obj[key]
                obj = obj[idx]
            else:
                obj = obj[part]
        return obj

    @staticmethod
    def _set_nested(target: dict, path: str, value):
        parts = path.split(".")
        for part in parts[:-1]:
            if "[" in part:
                key, idx_str = part.split("[", 1)
                idx = int(idx_str.rstrip("]"))
                if key:
                    target.setdefault(key, [])
                    target = target[key]
                while len(target) <= idx:
                    target.append({})
                target = target[idx]
            else:
                target.setdefault(part, {})
                target = target[part]
        leaf = parts[-1]
        if "[" in leaf:
            key, idx_str = leaf.split("[", 1)
            idx = int(idx_str.rstrip("]"))
            if key:
                target.setdefault(key, [])
                target = target[key]
            while len(target) <= idx:
                target.append(None)
            target[idx] = value
        else:
            target[leaf] = value
