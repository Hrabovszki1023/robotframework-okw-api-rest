# robotframework-okw-api-rest

> Deutsche Version: [README_de.md](README_de.md)

Keyword-driven REST API testing for [OKW4Robot](https://github.com/Hrabovszki1023/robotframework-okw4robot).

One set of keywords covers the complete REST API test lifecycle:
**Start -> Scope -> Input -> Action -> Verify -> Memorize -> Stop**.

---

## Installation

```bash
pip install robotframework-okw-api-rest
```

Or editable (for development):

```bash
pip install -e path/to/robotframework-okw-api-rest
```

### Dependencies

- Python >= 3.10
- robotframework >= 6.0
- requests >= 2.28
- PyYAML >= 6.0
- okw-contract-utils >= 0.2.0

---

## Quick Start

### 1. YAML Configuration

Create a file `locators/NotesAPI.yaml`:

```yaml
NotesAPI:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: https://practice.expandtesting.com/notes/api
    content_type: application/x-www-form-urlencoded
```

### 2. Test File

```robot
*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Health Check
    RESTStart              NotesAPI
    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET
    RESTVerifyStatus       200
    RESTStop
```

### 3. Run

```bash
robot tests/REST_NotesAPI.robot
```

---

## Keywords

| Keyword | Description |
|---|---|
| `RESTStart` | Start REST service (load YAML, base URL) |
| `RESTStop` | Stop REST service |
| `RESTSelectEndpoint` | Select endpoint path |
| `RESTSetValue` | Set request body field or query parameter (auto type detection) |
| `RESTSetValueAsString` | Set request body field (always string, no conversion) |
| `RESTSetValueAsList` | Set request body field as JSON array |
| `RESTSetContext` | Navigate into nested JSON object |
| `RESTSetHeader` | Set request header |
| `RESTSendRequest` | Send HTTP request (GET, POST, PUT, PATCH, DELETE) |
| `RESTVerifyValue` | Verify response field value (exact match) |
| `RESTVerifyValueWCM` | Verify response field value (wildcard: `*`, `?`) |
| `RESTVerifyValueREGX` | Verify response field value (regular expression) |
| `RESTVerifyStatus` | Verify HTTP status code |
| `RESTVerifyResponseTime` | Verify response time is below threshold (ms) |
| `RESTVerifyListCount` | Verify number of elements in a JSON array |
| `RESTVerifyHeader` | Verify response header |
| `RESTMemorizeValue` | Store response field value for `$MEM{name}` |
| `RESTMemorizeBody` | Store entire response body |

---

## Phase Model

| Phase | REST Keyword | GUI Equivalent |
|---|---|---|
| Start | `RESTStart` | `StartApp` |
| Scope | `RESTSelectEndpoint` | `SelectWindow` |
| Input | `RESTSetValue` | `SetValue` |
| Context | `RESTSetContext` | `SetContext` |
| Header | `RESTSetHeader` | -- |
| Action | `RESTSendRequest` | `ClickOn` |
| Verify | `RESTVerifyValue` | `VerifyValue` |
| Status | `RESTVerifyStatus` | -- |
| Timing | `RESTVerifyResponseTime` | -- |
| Memorize | `RESTMemorizeValue` | `MemorizeValue` |
| Stop | `RESTStop` | `StopApp` |

---

## OKW Tokens

| Token | Behavior |
|---|---|
| `$IGNORE` | Keyword becomes a no-op (field is not sent) |
| `$EMPTY` | Set field explicitly to empty string |
| `$NULL` | Set field explicitly to JSON `null` |

---

## Auto Type Detection

`RESTSetValue` automatically converts values to their native JSON type:

```robot
RESTSetValue    name        Zoltan       # → string "Zoltan"
RESTSetValue    count       42           # → integer 42
RESTSetValue    price       3.14         # → float 3.14
RESTSetValue    active      true         # → boolean true
RESTSetValue    comment     $NULL        # → null
```

Use `RESTSetValueAsString` when a value must remain a string:

```robot
RESTSetValueAsString    zipcode    01234    # → string "01234" (not integer)
RESTSetValueAsString    flag       true     # → string "true" (not boolean)
```

Query parameters (`?` prefix) are always strings — no type conversion.

---

## JSON Arrays

Two ways to set array fields:

```robot
# Short array — one line
RESTSetValueAsList     tags      important    urgent    work

# Array index — one value per line (auto-typed)
RESTSetValue           scores[0]    42
RESTSetValue           scores[1]    87
RESTSetValue           scores[2]    15

# Empty array
RESTSetValueAsList     items
```

Verify array length with `RESTVerifyListCount`:

```robot
RESTVerifyListCount    todos    3        # todos has 3 elements
RESTVerifyListCount    items    0        # items is empty
```

---

## Query Parameters

Fields prefixed with `?` are sent as URL query parameters:

```robot
RESTSetValue    ?page     1          # query param: ?page=1
RESTSetValue    name      Zoltan     # body field
```

Query parameters work with all HTTP methods and are not affected by `RESTSetContext`.

---

## Value Memorization

Store response values and reuse them in subsequent requests:

```robot
# Store token from login response
RESTMemorizeValue    data.token    TOKEN

# Use in next request
RESTSetHeader        x-auth-token    $MEM{TOKEN}
RESTSelectEndpoint   /notes/$MEM{NOTE_ID}
```

---

## Nested Request Bodies

Use `RESTSetContext` to build nested JSON structures:

```robot
RESTSelectEndpoint    /orders

RESTSetContext        customer
RESTSetValue          name       Zoltan
RESTSetValue          email      z@test.com

RESTSetContext        customer.address
RESTSetValue          street     Hauptstr. 1
RESTSetValue          city       Berlin

RESTSendRequest       POST
```

Produces: `{"customer": {"name": "Zoltan", "email": "z@test.com", "address": {"street": "Hauptstr. 1", "city": "Berlin"}}}`.

---

## Endpoint Keywords Pattern

Wrap endpoints as reusable keywords with default values:

```robot
*** Keywords ***
Register User
    [Arguments]    ${name}=DefaultUser    ${email}=default@test.com    ${password}=Test1234!
    RESTSelectEndpoint     /users/register
    RESTSetValue           name         ${name}
    RESTSetValue           email        ${email}
    RESTSetValue           password     ${password}
    RESTSendRequest        POST

*** Test Cases ***
Default Registration
    Register User
    RESTVerifyStatus    201

Custom Name Only
    Register User    name=Zoltan
    RESTVerifyStatus    201

Missing Email
    Register User    email=$IGNORE
    RESTVerifyStatus    400
```

Three levels: no argument = default sent, custom value = override, `$IGNORE` = field not sent.

---

## Environment Configuration

Separate credentials and URLs from the service YAML using environment
files — like `~/.ssh/` keeps keys out of your projects.

### Service YAML (safe for repo)

```yaml
NotesAPI:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: ${BASE_URL}
    content_type: ${CONTENT_TYPE}
```

### Environment file (in user profile, NOT in repo)

```yaml
# ~/.okw/env/env-test.yaml
BASE_URL: https://practice.expandtesting.com/notes/api
CONTENT_TYPE: application/x-www-form-urlencoded
```

### Test file

```robot
RESTStart    NotesAPI    env-test
```

### Search order for env files

| Priority | Path | Purpose |
|---|---|---|
| 1 | `~/.okw/env/` | User profile (secure) |
| 2 | `$OKW_ENV_DIR` | CI/CD override |
| 3 | `locators/` next to test | Development |
| 4 | OS environment variables | Fallback |

---

## Authentication

Configured in YAML `__self__` — no credentials in test code.

```yaml
# Basic Auth
auth_type: basic
auth_user: ${API_USER}
auth_password: ${API_PASSWORD}

# API Key
auth_type: api_key
auth_header: X-API-Key
auth_key: ${API_KEY}

# Bearer Token (static)
auth_type: bearer
auth_token: ${AUTH_TOKEN}
```

For dynamic tokens (login flow), use `RESTMemorizeValue` + `RESTSetHeader`.

---

## SSL / Certificates

```yaml
verify_ssl: false                        # self-signed certs
client_cert: ~/.okw/certs/client.pem     # mTLS
client_key: ~/.okw/certs/client.key
ca_bundle: ~/.okw/certs/ca-bundle.pem    # custom CA
```

Paths support `~` and `$ENV_VAR` expansion.

### User profile structure

```
~/.okw/
  env/
    env-test.yaml       # credentials + URLs
    env-prod.yaml
  certs/
    client.pem          # client certificate
    client.key          # private key
    ca-bundle.pem       # custom CA
```

---

## Response Time Verification

Verify that the API responds within acceptable time limits:

```robot
RESTSendRequest        GET
RESTVerifyResponseTime    500      # must respond under 500ms
RESTVerifyResponseTime    $IGNORE  # skip check
```

---

## Request/Response Logging

`RESTSendRequest` automatically logs request and response as formatted
JSON in the Robot log. Sensitive fields (`password`, `token`, `secret`)
are masked with `***` in the request body.

```
>>> POST https://dummyjson.com/auth/login
    Request Body:
{
  "username": "emilys",
  "password": "***"
}

<<< 200 OK
    Response Body:
{
  "accessToken": "eyJ...",
  "username": "emilys"
}
```

---

## Retry on Error

Automatic retry for transient HTTP errors (429, 502, 503, etc.).
Configured in YAML — the test code stays unchanged.

```yaml
MyAPI:
  __self__:
    base_url: https://api.example.com
    content_type: application/json
    retry_count: 3
    retry_delay: 1000
    retry_on: 429,502,503
```

| Setting | Default | Description |
|---|---|---|
| `retry_count` | 0 (off) | Maximum number of retries |
| `retry_delay` | 1000 | Delay between retries in milliseconds |
| `retry_on` | (none) | Status codes that trigger a retry |

---

## Complete Example: Login + CRUD

```robot
*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Login And Create Note
    RESTStart              NotesAPI

    # Login
    RESTSelectEndpoint     /users/login
    RESTSetValue           email        user@example.com
    RESTSetValue           password     Secret123!
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTMemorizeValue      data.token   TOKEN

    # Create note
    RESTSelectEndpoint     /notes
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           title        My Note
    RESTSetValue           description  Created by OKW
    RESTSetValue           category     Work
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTMemorizeValue      data.id      NOTE_ID

    # Delete note
    RESTSelectEndpoint     /notes/$MEM{NOTE_ID}
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSendRequest        DELETE
    RESTVerifyStatus       200

    RESTStop
```

---

## Documentation

- [Keyword Specification](docs/rest-keywords.md) -- full keyword reference
- [Keyword API (libdoc)](docs/OkwApiRestLibrary.html) -- auto-generated from docstrings

---

## License

See [LICENSE](LICENSE).
