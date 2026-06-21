# CONTRACT – robotframework-okw-api-rest

This document defines the public contract of `robotframework-okw-api-rest`.

## Keywords (Public API)

### Lifecycle

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTStart` | `<service>` `[env]` | Starts REST service: loads YAML config, base URL, authentication. Optional env file for variable resolution. |
| `RESTStop` | — | Stops REST service and releases resources. |

### Scope

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSelectEndpoint` | `<path>` | Selects endpoint path relative to `base_url`. Resets values, context, headers, and files. |

### Input – Body / Query

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSetValue` | `<field>` `<value>` | Sets body field (auto type detection) or query parameter (`?` prefix). Context-aware. |
| `RESTSetValueAsString` | `<field>` `<value>` | Sets body field always as string (no type conversion). |
| `RESTSetValueAsList` | `<field>` `[*values]` | Sets body field as JSON array. Without values: empty array. Auto-typed. |

### Input – Context

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSetContext` | `<path>` | Sets JSON path for subsequent `RESTSetValue` / `RESTVerifyValue`. Replaces previous context (flat, no stack). Cleared by `RESTSelectEndpoint`. |

### Input – Header

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSetHeader` | `<header>` `<value>` | Sets a request header. Persists until `RESTSelectEndpoint`. |

### Input – File

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSetFile` | `<field>` `<filepath>` `[mime_type]` | Sets file for multipart upload. MIME auto-detected from extension. Multiple calls accumulate files. |

### Action

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSendRequest` | `<method>` | Sends HTTP request (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`). Switches to multipart encoding when files are present. Response is stored for subsequent verify/memorize keywords. |

### Verification

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTVerifyValue` | `<field>` `<expected>` | EXACT match on response field (dot notation). Context-aware. |
| `RESTVerifyValueWCM` | `<field>` `<pattern>` | Wildcard match on response field (`*` = any chars, `?` = one char). Context-aware. |
| `RESTVerifyValueREGX` | `<field>` `<regex>` | Regex match on response field. Context-aware. |
| `RESTVerifyStatus` | `<expected>` | Verifies HTTP status code. |
| `RESTVerifyResponseTime` | `<max_ms>` | Verifies response time is below threshold in milliseconds. |
| `RESTVerifyListCount` | `<field>` `<expected>` | Verifies number of elements in a JSON array field. Context-aware. |
| `RESTVerifyHeader` | `<header>` `<expected>` | Verifies response header value. |

### Memorize

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTMemorizeValue` | `<field>` `<name>` | Stores response field value in `$MEM{name}`. |
| `RESTMemorizeBody` | `<name>` | Stores entire response body as string in `$MEM{name}`. |

### Save

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `RESTSaveResponseToFile` | `<filepath>` | Saves response body as raw bytes to file. Parent directories created automatically. Existing files overwritten. |

## Phase Model

Keywords follow a fixed lifecycle:

| Phase | Keyword | GUI Equivalent |
|-------|---------|----------------|
| Start | `RESTStart` | `StartApp` |
| Scope | `RESTSelectEndpoint` | `SelectWindow` |
| Input | `RESTSetValue` | `SetValue` |
| Context | `RESTSetContext` | `SetContext` |
| Header | `RESTSetHeader` | — |
| File | `RESTSetFile` | — |
| Action | `RESTSendRequest` | `ClickOn` |
| Verify | `RESTVerifyValue` | `VerifyValue` |
| Status | `RESTVerifyStatus` | — |
| Timing | `RESTVerifyResponseTime` | — |
| Memorize | `RESTMemorizeValue` | `MemorizeValue` |
| Save | `RESTSaveResponseToFile` | — |
| Stop | `RESTStop` | `StopApp` |

## OKW Tokens

This library follows the OKW Global Token Model defined in `okw-contract-utils`,
with one REST-specific extension (`$NULL`).

### Supported tokens

- **`$IGNORE`** — Keyword becomes a no-op (PASS). For input keywords: the field is not added to the request. For verify keywords: verification is skipped.
- **`$EMPTY`** — Sets or verifies an empty string (`""`).
- **`$NULL`** — Sets field value to JSON `null`. REST-specific token, not part of `okw-contract-utils`.

### Token applicability

| Keyword | `$IGNORE` | `$EMPTY` | `$NULL` |
|---------|-----------|----------|---------|
| `RESTSetValue` | field not sent | `""` | `null` |
| `RESTSetValueAsString` | field not sent | `""` | — |
| `RESTSetFile` | file not added | — | — |
| `RESTSetHeader` | header not set | `""` | — |
| `RESTVerifyValue` / `WCM` / `REGX` | skip verification | verify `""` | — |
| `RESTVerifyStatus` | skip verification | — | — |
| `RESTVerifyResponseTime` | skip verification | — | — |
| `RESTVerifyListCount` | skip verification | — | — |
| `RESTVerifyHeader` | skip verification | — | — |
| `RESTSaveResponseToFile` | skip save | — | — |

### Not supported

- **`$DELETE`** — This library does not implement delete semantics on fields.

## Auto Type Detection

`RESTSetValue` converts body field values to native JSON types automatically.

| Input | JSON type | Rule |
|-------|-----------|------|
| `Zoltan` | `"Zoltan"` (string) | Text → string |
| `42` | `42` (integer) | Integer pattern → number |
| `3.14` | `3.14` (float) | Float pattern → number |
| `true` / `false` | `true` / `false` (boolean) | Boolean keyword → boolean |
| `null` / `$NULL` | `null` | Null keyword → null |
| `$EMPTY` | `""` (empty string) | Empty string |

**Query parameters** (`?` prefix) are always strings — no type conversion.

**`RESTSetValueAsString`** bypasses type detection — value is always sent as string.

**`RESTSetValueAsList`** applies auto type detection to each element.

## Token Evaluation Order

For parameters of type Value/Expected/Field/Path:

1. Robot Framework variable expansion (e.g., `${IGNORE}` → `$IGNORE`)
2. OKW value expansion (`$MEM{KEY}` → stored value)
3. Token parsing (`$IGNORE`, `$EMPTY`, `$NULL`)
4. Keyword execution / verification

## Value Expansion

All Value, Field, Expected, Path, and Header parameters support `$MEM{KEY}` expansion
(OKW Global Value Expansion Model). Missing keys cause FAIL (no silent fallback).

```
RESTSetHeader        x-auth-token    $MEM{TOKEN}
RESTSelectEndpoint   /notes/$MEM{NOTE_ID}
```

## YAML Configuration Contract

### `__self__` fields

| Field | Required | Description |
|-------|----------|-------------|
| `class` | yes | `okw_api_rest.library.OkwApiRestLibrary` |
| `base_url` | yes | Base URL for all endpoints |
| `content_type` | no | Default content type (default: `application/json`) |

### Authentication fields

| Field | Required | Description |
|-------|----------|-------------|
| `auth_type` | yes | `basic`, `api_key`, `bearer`, or `oauth2_client_credentials` |

**Basic Auth:**

| Field | Required |
|-------|----------|
| `auth_user` | yes |
| `auth_password` | yes |

**API Key:**

| Field | Required |
|-------|----------|
| `auth_header` | yes |
| `auth_key` | yes |

**Bearer Token:**

| Field | Required |
|-------|----------|
| `auth_token` | yes |

**OAuth 2.0 Client Credentials:**

| Field | Required | Description |
|-------|----------|-------------|
| `token_url` | yes | Full URL of the OAuth token endpoint |
| `client_id` | yes | Client ID |
| `client_secret` | yes | Client Secret |
| `scope` | no | Space-separated scopes |

`RESTStart` fetches the token automatically and sets `Authorization: Bearer <token>`
on every request. The test code is unaware of OAuth.

### SSL / Certificate fields

| Field | Default | Description |
|-------|---------|-------------|
| `verify_ssl` | `true` | Set `false` for self-signed certificates |
| `client_cert` | — | Path to client certificate (mTLS) |
| `client_key` | — | Path to private key (mTLS) |
| `ca_bundle` | — | Path to custom CA bundle |

Paths support `~` and `$ENV_VAR` expansion.

### Retry fields

| Field | Default | Description |
|-------|---------|-------------|
| `retry_count` | `0` (off) | Maximum number of retries |
| `retry_delay` | `1000` | Delay between retries in milliseconds |
| `retry_on` | (none) | Status codes that trigger retry (comma-separated, list, or single value) |

## Environment File Search Order

| Priority | Path | Purpose |
|----------|------|---------|
| 1 | `~/.okw/env/` | User profile (secure, not in repo) |
| 2 | `$OKW_ENV_DIR` | CI/CD override |
| 3 | `locators/` next to test | Development convenience |
| 4 | OS environment variables | Fallback for individual `${VAR}` |

## Default Semantics

- `RESTSelectEndpoint` resets all request state: body fields, query parameters, context, headers, files.
- `RESTSetContext` replaces the previous context (flat, no stack).
- `RESTSendRequest` switches to multipart encoding automatically when files are present.
- Query parameters (`?` prefix) are always strings and not affected by `RESTSetContext`.
- `RESTSaveResponseToFile` creates parent directories and overwrites existing files.

## ASR Logging

### Request/Response Logging

`RESTSendRequest` logs request and response in the Robot log:

```
>>> POST https://dummyjson.com/auth/login
    Headers:
      Content-Type: application/json
      User-Agent: python-requests/2.31.0
    Request Body:
{
  "username": "emilys",
  "password": "***"
}

<<< 200 OK
    Headers:
      Content-Type: application/json; charset=utf-8
    Response Body:
{
  "accessToken": "eyJ...",
  "username": "emilys"
}
```

Sensitive fields (`password`, `token`, `secret`) are masked with `***` in the request body.
Headers are logged in cleartext for maximum observability.

### Verification Logging

```
RESTVerifyResponseTime: 341ms < 500ms (PASS)
RESTVerifyListCount: todos has 3 elements (PASS)
```

### Retry Logging

```
<<< 429 — retry 1/3 (waiting 1000ms)
<<< 429 — retry 2/3 (waiting 1000ms)
<<< 200 OK
```

### File Upload Logging

```
>>> POST https://api.example.com/upload
    File: file: report.pdf (application/pdf, 1.2 MB)
          Content: (binary, first 20 bytes: 25 50 44 46 ...)
```

### Save Logging

```
RESTSaveResponseToFile: 4523 bytes -> 'C:/temp/response.json' (Content-Type: application/json)
```
