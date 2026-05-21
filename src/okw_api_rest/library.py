from __future__ import annotations

import yaml
import os

from robot.api import logger
from robot.api.deco import keyword, library

from okw_contract_utils import MatchMode, assert_match, expand_mem

from .rest_context import RestContext
from .rest_client import send_request


_IGNORE = "$IGNORE"
_EMPTY = "$EMPTY"

_mem_store: dict[str, str] = {}


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

    # ── Start / Stop ────────────────────────────────────────────

    @keyword("RESTStart")
    def rest_start(self, service: str):
        """Starts a REST service session.

        Loads the YAML configuration for the given service name and
        initialises the REST context with base URL and content type.

        Examples:
        | RESTStart | NotesAPI |
        """
        logger.info(f"RESTStart: Loading service '{service}'...")
        model = self._load_yaml(service)

        if service not in model:
            raise KeyError(f"Service '{service}' not found in YAML root.")

        svc_model = model[service]
        self_cfg = svc_model.get("__self__", {})

        base_url = self_cfg.get("base_url")
        if not base_url:
            raise ValueError(f"Service '{service}' has no base_url in __self__.")

        content_type = self_cfg.get("content_type", "application/json")

        self._ctx = RestContext(base_url=base_url, content_type=content_type)
        self._service_name = service
        logger.info(f"RESTStart: Service '{service}' active (base_url={base_url}).")

    @keyword("RESTStop")
    def rest_stop(self):
        """Stops the REST service and releases resources.

        Examples:
        | RESTStop |
        """
        name = self._service_name or "<unknown>"
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
        """Sets a request body field or query parameter.

        Fields prefixed with ``?`` are sent as URL query parameters.
        Without prefix, fields are added to the request body.
        When a context is active, body fields are set relative to the context path.

        Examples:
        | RESTSetValue | name     | Zoltan   |
        | RESTSetValue | ?page    | 1        |
        | RESTSetValue | ?active  | true     |
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
