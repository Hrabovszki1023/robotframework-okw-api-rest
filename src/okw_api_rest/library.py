from __future__ import annotations

import re
import yaml
import os

from robot.api import logger
from robot.api.deco import keyword, library

from okw_contract_utils import MatchMode, assert_match, expand_mem

from .rest_context import RestContext
from .rest_client import send_request, _fetch_oauth2_token, _build_ssl_kwargs


_IGNORE = "$IGNORE"
_EMPTY = "$EMPTY"

_mem_store: dict[str, str] = {}

_ENV_RE = re.compile(r"\$\{([A-Za-z0-9_\-\.]+)\}")


def _resolve_env_vars(obj, env: dict):
    """Recursively resolve ${VAR} placeholders in YAML values from env dict."""
    if isinstance(obj, str):
        def repl(m):
            key = m.group(1)
            if key in env:
                return str(env[key])
            # Fall back to OS environment variable
            os_val = os.environ.get(key)
            if os_val is not None:
                return os_val
            raise ValueError(f"Environment variable '{key}' not found in env file or OS environment.")
        return _ENV_RE.sub(repl, obj)
    elif isinstance(obj, dict):
        return {k: _resolve_env_vars(v, env) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(v, env) for v in obj]
    return obj


def _load_env_file(env_path: str) -> dict:
    """Load a YAML environment file and return its contents as a dict."""
    if not os.path.isfile(env_path):
        raise FileNotFoundError(f"Environment file not found: {env_path}")
    with open(env_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _expand(value: str) -> str:
    if value is None:
        return ""
    return expand_mem(str(value), _mem_store)


def _is_ignore(value: str) -> bool:
    return str(value).strip().upper() == _IGNORE


@library(scope="GLOBAL")
class OkwApiRestLibrary:
    """OKW keyword-driven REST API testing library.

    Provides keywords for building, sending, and verifying REST API requests
    following the OKW phase model: Start -> Scope -> Input -> Action -> Verify -> Stop.

    = Runnable Examples =

    Complete ``.robot`` examples for this library are available in the
    [https://github.com/Hrabovszki1023/okw-examples/tree/master/rest-api|okw-examples]
    repository. Install and run:

    | pip install -r requirements.txt
    | robot rest-api/

    = Import =

    | Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

    = YAML Configuration =

    | NotesAPI:
    |   __self__:
    |     class: okw_api_rest.library.OkwApiRestLibrary
    |     base_url: https://practice.expandtesting.com/notes/api
    |     content_type: application/x-www-form-urlencoded

    = Example =

    | RESTStart              NotesAPI
    | RESTSelectEndpoint     /users/login
    | RESTSetValue           email        user@example.com
    | RESTSetValue           password     Secret123!
    | RESTSendRequest        POST
    | RESTVerifyStatus       200
    | RESTMemorizeValue      data.token   TOKEN
    | RESTStop
    """

    ROBOT_LIBRARY_DOC_FORMAT = "ROBOT"
    ROBOT_LIBRARY_VERSION = "0.1.0"

    def __init__(self):
        self._ctx: RestContext | None = None
        self._service_name: str | None = None

    def _require_ctx(self) -> RestContext:
        if self._ctx is None:
            raise RuntimeError("No REST service active. Call RESTStart first.")
        return self._ctx

    def _load_yaml(self, name: str) -> dict:
        search_dirs = []

        try:
            from robot.libraries.BuiltIn import BuiltIn
            suite_source = BuiltIn().get_variable_value("${SUITE SOURCE}")
            if suite_source:
                search_dirs.append(os.path.join(os.path.dirname(suite_source), "locators"))
                search_dirs.append(os.path.dirname(suite_source))
        except Exception:
            pass

        search_dirs.append(os.path.join(os.getcwd(), "locators"))
        search_dirs.append(os.getcwd())

        for d in search_dirs:
            for ext in (".yaml", ".yml"):
                path = os.path.join(d, f"{name}{ext}")
                if os.path.isfile(path):
                    with open(path, encoding="utf-8") as f:
                        return yaml.safe_load(f)

        raise FileNotFoundError(
            f"YAML file for service '{name}' not found. "
            f"Searched: {search_dirs}"
        )

    def _find_env_file(self, env_name: str, service_name: str) -> str:
        """Find environment YAML file by name.

        Search order (like ~/.ssh/ convention):
        1. ~/.okw/env/          (user profile — secure, not in repo)
        2. OKW_ENV_DIR env var  (explicit override, e.g. for CI/CD)
        3. locators/ next to test suite
        4. test suite directory
        5. cwd/locators/
        6. cwd
        """
        search_dirs = []

        # 1. User profile: ~/.okw/env/
        okw_home = os.path.join(os.path.expanduser("~"), ".okw", "env")
        search_dirs.append(okw_home)

        # 2. OKW_ENV_DIR environment variable
        env_dir = os.environ.get("OKW_ENV_DIR")
        if env_dir:
            search_dirs.append(env_dir)

        # 3+4. Next to test suite
        try:
            from robot.libraries.BuiltIn import BuiltIn
            suite_source = BuiltIn().get_variable_value("${SUITE SOURCE}")
            if suite_source:
                search_dirs.append(os.path.join(os.path.dirname(suite_source), "locators"))
                search_dirs.append(os.path.dirname(suite_source))
        except Exception:
            pass

        # 5+6. Current working directory
        search_dirs.append(os.path.join(os.getcwd(), "locators"))
        search_dirs.append(os.getcwd())

        for d in search_dirs:
            for ext in (".yaml", ".yml"):
                path = os.path.join(d, f"{env_name}{ext}")
                if os.path.isfile(path):
                    logger.info(f"RESTStart: Found env file at {path}")
                    return path

        raise FileNotFoundError(
            f"Environment file '{env_name}' not found. "
            f"Searched: {search_dirs}"
        )

    # ── Start / Stop ────────────────────────────────────────────

    @keyword("RESTStart")
    def rest_start(self, service: str, env: str | None = None):
        """Starts a REST service session.

        Loads the YAML configuration for the given service name and
        initialises the REST context with base URL, content type,
        authentication, and SSL settings.

        The optional ``env`` parameter specifies an environment file
        (YAML) whose values replace ``${VAR}`` placeholders in the
        service YAML. If omitted, placeholders are resolved from OS
        environment variables.

        Examples:
        | RESTStart | NotesAPI |
        | RESTStart | NotesAPI | env-test |
        """
        logger.info(f"RESTStart: Loading service '{service}'...")
        model = self._load_yaml(service)

        if service not in model:
            raise KeyError(f"Service '{service}' not found in YAML root.")

        svc_model = model[service]

        # Load environment variables for ${VAR} resolution
        env_vars = {}
        if env:
            env_path = self._find_env_file(env, service)
            env_vars = _load_env_file(env_path)
            logger.info(f"RESTStart: Loaded env file '{env}' ({len(env_vars)} variables).")

        # Resolve ${VAR} placeholders in __self__
        self_cfg = svc_model.get("__self__", {})
        self_cfg = _resolve_env_vars(self_cfg, env_vars)

        base_url = self_cfg.get("base_url")
        if not base_url:
            raise ValueError(f"Service '{service}' has no base_url in __self__.")

        content_type = self_cfg.get("content_type", "application/json")

        # Authentication config
        auth_keys = {"auth_type", "auth_user", "auth_password",
                     "auth_header", "auth_key", "auth_token",
                     "token_url", "client_id", "client_secret", "scope"}
        auth_cfg = {k: v for k, v in self_cfg.items() if k in auth_keys}

        # SSL config
        ssl_keys = {"verify_ssl", "client_cert", "client_key", "ca_bundle"}
        ssl_cfg = {k: v for k, v in self_cfg.items() if k in ssl_keys}

        # Retry config
        retry_cfg = {}
        if "retry_count" in self_cfg:
            retry_cfg["retry_count"] = int(self_cfg["retry_count"])
        if "retry_delay" in self_cfg:
            retry_cfg["retry_delay"] = int(self_cfg["retry_delay"])
        if "retry_on" in self_cfg:
            raw = self_cfg["retry_on"]
            if isinstance(raw, str):
                retry_cfg["retry_on"] = {int(s.strip()) for s in raw.split(",")}
            elif isinstance(raw, list):
                retry_cfg["retry_on"] = {int(s) for s in raw}
            else:
                retry_cfg["retry_on"] = {int(raw)}

        # OAuth 2.0: fetch token before creating context
        auth_type = auth_cfg.get("auth_type", "none").lower()
        if auth_type == "oauth2_client_credentials":
            ssl_kwargs = _build_ssl_kwargs(ssl_cfg)
            token = _fetch_oauth2_token(auth_cfg, ssl_kwargs)
            auth_cfg["_oauth2_token"] = token

        self._ctx = RestContext(
            base_url=base_url,
            content_type=content_type,
            auth=auth_cfg,
            ssl=ssl_cfg,
            retry=retry_cfg,
        )
        self._service_name = service
        verify = ssl_cfg.get("verify_ssl", True)
        retry_info = f", retry={retry_cfg['retry_count']}x" if retry_cfg.get("retry_count") else ""
        logger.info(
            f"RESTStart: Service '{service}' active "
            f"(base_url={base_url}, auth={auth_type}, verify_ssl={verify}{retry_info})."
        )

    @keyword("RESTStop")
    def rest_stop(self):
        """Stops the REST service and releases resources.

        Examples:
        | RESTStop |
        """
        name = self._service_name or "<unknown>"
        if self._ctx is not None:
            self._ctx._session.close()
        self._ctx = None
        self._service_name = None
        logger.info(f"RESTStop: Service '{name}' stopped.")

    # ── Scope ───────────────────────────────────────────────────

    @keyword("RESTSelectEndpoint")
    def rest_select_endpoint(self, path: str):
        """Selects the API endpoint for the next request.

        Resets body, query parameters, headers, and context.
        Path is relative to the base_url from YAML.

        Examples:
        | RESTSelectEndpoint | /users/register |
        | RESTSelectEndpoint | /notes/$MEM{NOTE_ID} |
        """
        ctx = self._require_ctx()
        path = _expand(path)
        ctx.select_endpoint(path)
        logger.info(f"RESTSelectEndpoint: {path}")

    # ── Input ───────────────────────────────────────────────────

    @keyword("RESTSetValue")
    def rest_set_value(self, field: str, value: str):
        """Sets a request body field or query parameter with auto type detection.

        Values are automatically converted to native JSON types:
        - ``true`` / ``false`` -> boolean
        - ``null`` or ``$NULL`` -> null
        - Integer strings (``42``) -> number
        - Float strings (``3.14``) -> number
        - Everything else -> string

        Fields prefixed with ``?`` are sent as URL query parameters
        (always as string, no type conversion).

        Use ``RESTSetValueAsString`` to force a value as string.

        Examples:
        | RESTSetValue | name      | Zoltan  | # -> string "Zoltan" |
        | RESTSetValue | count     | 42      | # -> integer 42 |
        | RESTSetValue | price     | 3.14    | # -> float 3.14 |
        | RESTSetValue | active    | true    | # -> boolean true |
        | RESTSetValue | deleted   | false   | # -> boolean false |
        | RESTSetValue | comment   | $NULL   | # -> null |
        | RESTSetValue | ?page     | 1       | # -> query param (string) |
        """
        if _is_ignore(value):
            logger.info(f"RESTSetValue: {field} = $IGNORE (skipped)")
            return

        ctx = self._require_ctx()
        value = _expand(str(value))
        if value == _EMPTY:
            value = ""

        ctx.set_value(field, value)
        log_val = "***" if "password" in field.lower() else value
        logger.info(f"RESTSetValue: {field} = {log_val}")

    @keyword("RESTSetValueAsString")
    def rest_set_value_as_string(self, field: str, value: str):
        """Sets a request body field as string, without type conversion.

        Use this when a value that looks like a number or boolean
        must be sent as a JSON string.

        Examples:
        | RESTSetValueAsString | zipcode | 01234 | # -> string "01234" |
        | RESTSetValueAsString | flag    | true  | # -> string "true" |
        | RESTSetValueAsString | code    | 42    | # -> string "42" |
        """
        if _is_ignore(value):
            logger.info(f"RESTSetValueAsString: {field} = $IGNORE (skipped)")
            return

        ctx = self._require_ctx()
        value = _expand(str(value))
        if value == _EMPTY:
            value = ""

        ctx.set_value(field, value, force_string=True)
        log_val = "***" if "password" in field.lower() else value
        logger.info(f"RESTSetValueAsString: {field} = '{log_val}' (string)")

    @keyword("RESTSetValueAsList")
    def rest_set_value_as_list(self, field: str, *values: str):
        """Sets a request body field as a JSON array.

        All values are auto-typed (integers, floats, booleans are
        converted). Use for short primitive arrays.

        Examples:
        | RESTSetValueAsList | tags   | wichtig | dringend | arbeit |
        | RESTSetValueAsList | scores | 42      | 87       | 15     |
        | RESTSetValueAsList | flags  | true    | false    | true   |
        """
        if len(values) == 1 and _is_ignore(values[0]):
            logger.info(f"RESTSetValueAsList: {field} = $IGNORE (skipped)")
            return

        ctx = self._require_ctx()
        expanded = [_expand(str(v)) for v in values]
        ctx.set_value_as_list(field, expanded)
        logger.info(f"RESTSetValueAsList: {field} = [{', '.join(expanded)}]")

    @keyword("RESTSetFile")
    def rest_set_file(self, field: str, filepath: str, mime_type: str | None = None):
        """Sets a file field for multipart form-data upload.

        Can be called multiple times — files accumulate until
        ``RESTSelectEndpoint`` resets them. When files are present,
        ``RESTSendRequest`` automatically switches to multipart
        encoding. Text fields set via ``RESTSetValue`` are sent as
        form fields alongside the files.

        The MIME type is auto-detected from the file extension.
        An optional third argument overrides it.

        Multiple files with the **same field name** are supported
        (e.g. ``<input type="file" multiple>``).

        Examples:
        | RESTSetFile | avatar   | C:/img/photo.jpg |
        | RESTSetFile | document | report.pdf       | application/pdf |
        | RESTSetFile | attachments | file1.jpg |
        | RESTSetFile | attachments | file2.jpg |
        """
        if _is_ignore(filepath):
            logger.info(f"RESTSetFile: {field} = $IGNORE (skipped)")
            return

        ctx = self._require_ctx()
        filepath = _expand(filepath)
        ctx.set_file(field, filepath, mime_type)
        filename = os.path.basename(filepath)
        logger.info(f"RESTSetFile: {field} = '{filename}' ({mime_type or 'auto'})")

    @keyword("RESTSetContext")
    def rest_set_context(self, path: str):
        """Sets the context path for subsequent SetValue/VerifyValue calls.

        Fields are resolved relative to the context path.
        Each call replaces the previous context (flat, no stack).

        Examples:
        | RESTSetContext | customer         |
        | RESTSetContext | customer.address |
        | RESTSetContext | items[0]         |
        """
        ctx = self._require_ctx()
        path = _expand(path)
        ctx.set_context(path)
        logger.info(f"RESTSetContext: {path}")

    @keyword("RESTSetHeader")
    def rest_set_header(self, header: str, value: str):
        """Sets a request header for the next request.

        Multiple headers can be set. Headers persist until
        RESTSelectEndpoint is called.

        Examples:
        | RESTSetHeader | x-auth-token | $MEM{TOKEN} |
        | RESTSetHeader | Accept       | application/json |
        """
        if _is_ignore(value):
            logger.info(f"RESTSetHeader: {header} = $IGNORE (skipped)")
            return

        ctx = self._require_ctx()
        value = _expand(str(value))
        ctx.set_header(header, value)
        logger.info(f"RESTSetHeader: {header} = {value}")

    # ── Action ──────────────────────────────────────────────────

    @keyword("RESTSendRequest")
    def rest_send_request(self, method: str):
        """Sends the prepared HTTP request.

        After sending, the response is stored. All subsequent
        RESTVerify* and RESTMemorize* keywords operate on this response.

        Examples:
        | RESTSendRequest | POST   |
        | RESTSendRequest | GET    |
        | RESTSendRequest | PUT    |
        | RESTSendRequest | DELETE |
        """
        ctx = self._require_ctx()
        method = method.upper()
        url = ctx.get_request_url()
        logger.info(f"RESTSendRequest: {method} {url}")
        send_request(ctx, method)
        logger.info(
            f"RESTSendRequest: Response {ctx.get_response_status()} "
            f"({len(ctx.get_response_body())} bytes)"
        )

    # ── Verify ──────────────────────────────────────────────────

    @keyword("RESTVerifyValue")
    def rest_verify_value(self, field: str, expected: str):
        """Verifies a response field value (exact match).

        Dot notation for nested fields. Context-aware.

        Examples:
        | RESTVerifyValue | message    | User account created successfully |
        | RESTVerifyValue | data.name  | Zoltan |
        """
        if _is_ignore(expected):
            logger.info(f"RESTVerifyValue: {field} = $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        expected = _expand(str(expected))
        if expected == _EMPTY:
            expected = ""
        actual = ctx.get_response_value(field)
        assert_match(actual, expected, MatchMode.EXACT,
                     context=f"RESTVerifyValue: {field}")
        logger.info(f"RESTVerifyValue: {field} = '{actual}' (PASS)")

    @keyword("RESTVerifyValueWCM")
    def rest_verify_value_wcm(self, field: str, expected: str):
        """Verifies a response field value (wildcard match: ``*``, ``?``).

        Examples:
        | RESTVerifyValueWCM | message | *successfully* |
        """
        if _is_ignore(expected):
            logger.info(f"RESTVerifyValueWCM: {field} = $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        expected = _expand(str(expected))
        actual = ctx.get_response_value(field)
        assert_match(actual, expected, MatchMode.WCM,
                     context=f"RESTVerifyValueWCM: {field}")
        logger.info(f"RESTVerifyValueWCM: {field} = '{actual}' (PASS)")

    @keyword("RESTVerifyValueREGX")
    def rest_verify_value_regx(self, field: str, expected: str):
        """Verifies a response field value (regular expression match).

        Examples:
        | RESTVerifyValueREGX | data.id | ^[a-f0-9]{24}$ |
        """
        if _is_ignore(expected):
            logger.info(f"RESTVerifyValueREGX: {field} = $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        expected = _expand(str(expected))
        actual = ctx.get_response_value(field)
        assert_match(actual, expected, MatchMode.REGX,
                     context=f"RESTVerifyValueREGX: {field}")
        logger.info(f"RESTVerifyValueREGX: {field} = '{actual}' (PASS)")

    @keyword("RESTVerifyStatus")
    def rest_verify_status(self, expected: str):
        """Verifies the HTTP status code of the response.

        Examples:
        | RESTVerifyStatus | 200 |
        | RESTVerifyStatus | 201 |
        | RESTVerifyStatus | 404 |
        """
        if _is_ignore(expected):
            logger.info(f"RESTVerifyStatus: $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        actual = ctx.get_response_status()
        expected_int = int(expected)
        if actual != expected_int:
            raise AssertionError(
                f"RESTVerifyStatus: Expected {expected_int}, got {actual}."
            )
        logger.info(f"RESTVerifyStatus: {actual} (PASS)")

    @keyword("RESTVerifyResponseTime")
    def rest_verify_response_time(self, max_ms: str):
        """Verifies that the response time is below the given threshold.

        The value is the maximum allowed response time in milliseconds.
        The actual response time must be **less than** this value.

        Examples:
        | RESTVerifyResponseTime | 500  |
        | RESTVerifyResponseTime | 2000 |
        """
        if _is_ignore(max_ms):
            logger.info(f"RESTVerifyResponseTime: $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        actual = ctx.get_response_time_ms()
        threshold = float(max_ms)
        if actual >= threshold:
            raise AssertionError(
                f"RESTVerifyResponseTime: {actual:.0f}ms >= {threshold:.0f}ms (too slow)."
            )
        logger.info(f"RESTVerifyResponseTime: {actual:.0f}ms < {threshold:.0f}ms (PASS)")

    @keyword("RESTVerifyListCount")
    def rest_verify_list_count(self, field: str, expected: str):
        """Verifies the number of elements in a JSON array field.

        The field must resolve to a list in the response.
        Context-aware (uses current RESTSetContext path).

        Examples:
        | RESTVerifyListCount | data       | 5 |
        | RESTVerifyListCount | items      | 0 |
        | RESTVerifyListCount | tags       | 3 |
        """
        if _is_ignore(expected):
            logger.info(f"RESTVerifyListCount: {field} = $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        raw = ctx.get_response_value_raw(field)
        if not isinstance(raw, list):
            raise AssertionError(
                f"RESTVerifyListCount: '{field}' is not a list (got {type(raw).__name__})."
            )
        actual = len(raw)
        expected_int = int(expected)
        if actual != expected_int:
            raise AssertionError(
                f"RESTVerifyListCount: '{field}' has {actual} elements, expected {expected_int}."
            )
        logger.info(f"RESTVerifyListCount: {field} has {actual} elements (PASS)")

    @keyword("RESTVerifyHeader")
    def rest_verify_header(self, header: str, expected: str):
        """Verifies a response header value.

        Examples:
        | RESTVerifyHeader | Content-Type | application/json |
        """
        if _is_ignore(expected):
            logger.info(f"RESTVerifyHeader: {header} = $IGNORE (skipped)")
            return
        ctx = self._require_ctx()
        expected = _expand(str(expected))
        actual = ctx.get_response_header(header)
        assert_match(actual, expected, MatchMode.EXACT,
                     context=f"RESTVerifyHeader: {header}")
        logger.info(f"RESTVerifyHeader: {header} = '{actual}' (PASS)")

    # ── Memorize ────────────────────────────────────────────────

    @keyword("RESTMemorizeValue")
    def rest_memorize_value(self, field: str, name: str):
        """Stores a response field value under a symbolic name.

        The value can be used later via ``$MEM{name}`` expansion.

        Examples:
        | RESTMemorizeValue | data.token | TOKEN   |
        | RESTMemorizeValue | data.id    | USER_ID |
        """
        ctx = self._require_ctx()
        value = ctx.get_response_value(field)
        _mem_store[name] = value
        logger.info(f"RESTMemorizeValue: {field} -> $MEM{{{name}}} = '{value}'")

    @keyword("RESTMemorizeBody")
    def rest_memorize_body(self, name: str):
        """Stores the entire response body as a string.

        Examples:
        | RESTMemorizeBody | RESPONSE |
        """
        ctx = self._require_ctx()
        body = ctx.get_response_body()
        _mem_store[name] = body
        logger.info(f"RESTMemorizeBody: -> $MEM{{{name}}} ({len(body)} bytes)")

    # ── Save ───────────────────────────────────────────────────

    @keyword("RESTSaveResponseToFile")
    def rest_save_response_to_file(self, filepath: str):
        """Saves the HTTP response body to a local file.

        The response is written as raw bytes, which works correctly
        for both binary content (PDF, images, ZIP) and text content
        (JSON, XML, CSV, HTML).

        The file path supports OKW memory expansion (``$MEM{name}``)
        and environment variable expansion (``~``, ``$ENV_VAR``).

        Parent directories are created automatically if they do not exist.
        If the file already exists, it is overwritten (logged as warning).

        Examples:
        | RESTSaveResponseToFile | C:/temp/report.pdf |
        | RESTSaveResponseToFile | $MEM{DOWNLOAD_DIR}/export.csv |
        | RESTSaveResponseToFile | ~/downloads/response.json |
        | RESTSaveResponseToFile | $IGNORE |
        """
        if _is_ignore(filepath):
            logger.info("RESTSaveResponseToFile: $IGNORE (skipped)")
            return

        ctx = self._require_ctx()
        filepath = _expand(filepath)
        filepath = os.path.expanduser(os.path.expandvars(filepath))

        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if os.path.isfile(filepath):
            logger.warn(f"RESTSaveResponseToFile: File exists and will be overwritten: '{filepath}'")

        content = ctx.get_response_content()

        with open(filepath, "wb") as f:
            f.write(content)

        content_type = ctx._response_headers.get("Content-Type", "unknown")
        logger.info(
            f"RESTSaveResponseToFile: {len(content)} bytes "
            f"-> '{filepath}' (Content-Type: {content_type})"
        )
