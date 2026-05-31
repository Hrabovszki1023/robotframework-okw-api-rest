# OKW REST Keywords

Keyword-driven REST API testing for OKW4Robot.

---

## Keyword Overview

| Keyword | Description |
|---|---|
| `RESTStart` | Start REST service (load YAML, base URL) |
| `RESTStop` | Stop REST service |
| `RESTSelectEndpoint` | Select endpoint path |
| `RESTSetValue` | Set request body field |
| `RESTSetContext` | Navigate into nested JSON object |
| `RESTSetHeader` | Set request header |
| `RESTSendRequest` | Send HTTP request |
| `RESTVerifyValue` | Verify response field value (exact match) |
| `RESTVerifyValueWCM` | Verify response field value (wildcard: `*`, `?`) |
| `RESTVerifyValueREGX` | Verify response field value (regular expression) |
| `RESTVerifyStatus` | Verify HTTP status code |
| `RESTVerifyResponseTime` | Verify response time is below threshold |
| `RESTVerifyHeader` | Verify response header |
| `RESTMemorizeValue` | Store response field value |
| `RESTMemorizeBody` | Store entire response body |

---

## RESTStart

Starts the REST service. Loads the YAML configuration with base URL
and connection settings. Optionally loads an environment file for
variable resolution.

| Parameter | Description |
|---|---|
| `service` | Name of the YAML service definition |
| `env` | (optional) Name of the environment file |

```robot
RESTStart    NotesAPI
RESTStart    NotesAPI    env-test
RESTStart    NotesAPI    env-prod
```

### Basic YAML definition

```yaml
# NotesAPI.yaml
NotesAPI:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: https://practice.expandtesting.com/notes/api
    content_type: application/x-www-form-urlencoded
```

### YAML with environment variables

Placeholders `${VAR}` are resolved from the environment file or OS
environment variables. This keeps credentials and URLs out of the
service YAML.

```yaml
# NotesAPI.yaml — no secrets, safe for repo
NotesAPI:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: ${BASE_URL}
    content_type: ${CONTENT_TYPE}
```

```yaml
# env-test.yaml — in ~/.okw/env/, NOT in the repo
BASE_URL: https://practice.expandtesting.com/notes/api
CONTENT_TYPE: application/x-www-form-urlencoded
```

### Environment file search order

Like `~/.ssh/`, environment files are searched in a fixed order:

| Priority | Path | Purpose |
|---|---|---|
| 1 | `~/.okw/env/` | User profile (secure, not in repo) |
| 2 | `$OKW_ENV_DIR` | CI/CD override |
| 3 | `locators/` next to test | Development convenience |
| 4 | OS environment variables | Fallback for individual `${VAR}` |

### Authentication

Authentication is configured in `__self__`. The test only calls
`RESTStart` — no credentials in test code.

**Basic Auth:**

```yaml
__self__:
  base_url: ${BASE_URL}
  auth_type: basic
  auth_user: ${API_USER}
  auth_password: ${API_PASSWORD}
```

**API Key (header-based):**

```yaml
__self__:
  base_url: ${BASE_URL}
  auth_type: api_key
  auth_header: X-API-Key
  auth_key: ${API_KEY}
```

**Bearer Token (static, from env file):**

```yaml
__self__:
  base_url: ${BASE_URL}
  auth_type: bearer
  auth_token: ${AUTH_TOKEN}
```

Note: For dynamic tokens (login → token → use), use
`RESTMemorizeValue` + `RESTSetHeader` in the test — that is test
logic, not infrastructure.

### SSL / Certificates

```yaml
__self__:
  base_url: ${BASE_URL}
  verify_ssl: false                  # self-signed certs
  client_cert: ~/.okw/certs/client.pem   # mTLS client certificate
  client_key: ~/.okw/certs/client.key    # private key
  ca_bundle: ~/.okw/certs/ca-bundle.pem  # custom CA
```

Paths support `~` (home directory) and `$ENV_VAR` expansion.

### User profile directory structure

```
~/.okw/
  env/
    env-test.yaml         # credentials + URLs for test
    env-prod.yaml         # credentials + URLs for prod
  certs/
    client.pem            # client certificate
    client.key            # private key
    ca-bundle.pem         # custom CA bundle
```

---

## RESTStop

Stops the REST service and releases resources.

```robot
RESTStop
```

---

## RESTSelectEndpoint

Selects the API endpoint for the next request. Resets any previously
set values, context, and headers. Path is relative to `base_url`
from the YAML.

| Parameter | Description |
|---|---|
| `path` | Endpoint path (e.g. `/users/register`) |

```robot
RESTSelectEndpoint    /users/register
RESTSelectEndpoint    /users/login
RESTSelectEndpoint    /notes
RESTSelectEndpoint    /notes/{id}
```

Calling `RESTSelectEndpoint` clears the request state (values, context,
headers) — analogous to `SelectWindow` clearing the GUI context.

---

## RESTSetValue

Sets a field in the request body or a query parameter. When a context
is active, body fields are set relative to the context path.

| Parameter | Description |
|---|---|
| `field` | Field name (JSON key) — prefix with `?` for query parameter |
| `value` | Field value |

### Body fields (default)

```robot
RESTSetValue    name       Zoltan
RESTSetValue    email      z@test.com
RESTSetValue    password   Test1234!
```

### Query parameters (`?` prefix)

Fields prefixed with `?` are sent as URL query parameters instead of
body fields. The `?` prefix is stripped before building the URL.

```robot
RESTSetValue    ?name      Zoltan       # → ?name=Zoltan
RESTSetValue    ?city      Berlin       # → &city=Berlin
RESTSetValue    ?page      1            # → &page=1
```

Query parameters work with all HTTP methods. They are appended to
the endpoint URL as `?key=value&key=value`.

### Mixed: query parameters + body

```robot
RESTSelectEndpoint    /users/search
RESTSetValue          ?role       admin        # query param
RESTSetValue          ?active     true         # query param
RESTSetValue          filter      name=Z*      # body field
RESTSendRequest       PUT
```

Result: `PUT /users/search?role=admin&active=true` with body `{"filter": "name=Z*"}`.

### With active context

```robot
RESTSetContext    customer
RESTSetValue      name      Zoltan       # → customer.name (body)
RESTSetValue      email     z@test.com   # → customer.email (body)
```

Context applies only to body fields — query parameters are always
top-level and not affected by `RESTSetContext`.

### OKW tokens

- `$IGNORE` — skip this keyword (no-op)
- `$EMPTY` — set explicitly to empty string

---

## RESTSetContext

Sets the context for subsequent `RESTSetValue` and `RESTVerifyValue`
calls. Fields are resolved relative to the context path.

| Parameter | Description |
|---|---|
| `path` | JSON path to the sub-object |

```robot
RESTSetContext    customer
RESTSetContext    customer.address
RESTSetContext    items[0]
```

Each `RESTSetContext` replaces the previous context (flat, no stack).
`RESTSelectEndpoint` clears the context.

Use blank lines to visually separate context blocks in the test:

```robot
RESTSelectEndpoint    /orders

RESTSetContext        customer
RESTSetValue          name       Zoltan
RESTSetValue          email      z@test.com

RESTSetContext        customer.address
RESTSetValue          street     Hauptstr. 1
RESTSetValue          city       Berlin

RESTSetContext        items[0]
RESTSetValue          product    Widget A
RESTSetValue          quantity   3

RESTSendRequest       POST
```

---

## RESTSetHeader

Sets a request header for the next `RESTSendRequest`. Multiple headers
can be set. Headers persist until `RESTSelectEndpoint` is called.

| Parameter | Description |
|---|---|
| `header` | Header name |
| `value` | Header value |

```robot
RESTSetHeader    x-auth-token    $MEM{TOKEN}
RESTSetHeader    Accept          application/json
```

---

## RESTSendRequest

Sends the prepared HTTP request to the selected endpoint.

| Parameter | Description |
|---|---|
| `method` | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |

```robot
RESTSendRequest    POST
RESTSendRequest    GET
RESTSendRequest    PUT
RESTSendRequest    DELETE
```

After sending, the response is stored internally. All subsequent
`RESTVerify*` and `RESTMemorize*` keywords operate on this response.

### Request/Response Logging

`RESTSendRequest` automatically logs the request and response as
formatted JSON in the Robot log. Sensitive fields (`password`,
`token`, `secret`) are masked with `***` in the request body.

Example log output:

```
>>> POST https://dummyjson.com/auth/login
    Request Body:
{
  "username": "emilys",
  "password": "***",
  "expiresInMins": "30"
}

<<< 200 OK
    Response Body:
{
  "accessToken": "eyJ...",
  "username": "emilys",
  "firstName": "Emily"
}
```

The response body is logged unmasked for debugging purposes.

---

## RESTVerifyValue

Verifies a field value in the JSON response body. Dot notation
is used for nested fields. When a context is active, the field
is resolved relative to the context path.

| Parameter | Description |
|---|---|
| `field` | JSON field path (dot notation) |
| `expected` | Expected value |

```robot
RESTVerifyValue    message       User account created successfully
RESTVerifyValue    data.name     Zoltan
RESTVerifyValue    data.email    z@test.com
```

Match modes (analogous to GUI `VerifyValue`):
- **EXACT** — exact string match (default)
- `RESTVerifyValueWCM` — wildcard match (`*`, `?`)
- `RESTVerifyValueREGX` — regular expression match

```robot
RESTVerifyValueWCM     message    *successfully*
RESTVerifyValueREGX    data.id    ^[a-f0-9]{24}$
```

With context:

```robot
RESTSetContext     data
RESTVerifyValue    name     Zoltan       # → data.name
RESTVerifyValue    email    z@test.com   # → data.email
```

---

## RESTVerifyStatus

Verifies the HTTP status code of the response.

| Parameter | Description |
|---|---|
| `expected` | Expected HTTP status code |

```robot
RESTVerifyStatus    200
RESTVerifyStatus    201
RESTVerifyStatus    400
RESTVerifyStatus    404
```

---

## RESTVerifyResponseTime

Verifies that the response time is below the given threshold.
The actual response time must be **less than** the specified value
in milliseconds.

| Parameter | Description |
|---|---|
| `max_ms` | Maximum allowed response time in milliseconds |

```robot
RESTVerifyResponseTime    500
RESTVerifyResponseTime    2000
RESTVerifyResponseTime    $IGNORE
```

Use after `RESTSendRequest` to ensure the API responds within
acceptable time limits. Useful for performance testing and SLA
verification.

Example log output:

```
RESTVerifyResponseTime: 341ms < 500ms (PASS)
```

If the response time exceeds the threshold:

```
RESTVerifyResponseTime: 612ms >= 500ms (too slow).
```

---

## RESTVerifyHeader

Verifies a response header value.

| Parameter | Description |
|---|---|
| `header` | Header name |
| `expected` | Expected value |

```robot
RESTVerifyHeader    Content-Type    application/json
```

---

## RESTMemorizeValue

Stores a response field value under a symbolic name. The value can be
used later via `$MEM{name}` expansion.

| Parameter | Description |
|---|---|
| `field` | JSON field path (dot notation) |
| `name` | Symbolic name to store under |

```robot
RESTMemorizeValue    data.token    TOKEN
RESTMemorizeValue    data.id       USER_ID
```

Usage in subsequent keywords:

```robot
RESTSetHeader    x-auth-token    $MEM{TOKEN}
RESTSelectEndpoint    /users/$MEM{USER_ID}
```

---

## RESTMemorizeBody

Stores the entire response body as a string under a symbolic name.

| Parameter | Description |
|---|---|
| `name` | Symbolic name to store under |

```robot
RESTMemorizeBody    RESPONSE
```

---

## Complete Examples

### Example 1: Simple Registration

```robot
*** Test Cases ***
Erfolgreiche API Registrierung
    RESTStart              NotesAPI

    RESTSelectEndpoint     /users/register
    RESTSetValue           name         Zoltan
    RESTSetValue           email        z@test.com
    RESTSetValue           password     Test1234!
    RESTSendRequest        POST

    RESTVerifyStatus       201
    RESTVerifyValue        message      User account created successfully
    RESTVerifyValue        data.name    Zoltan

    RESTStop
```

### Example 2: Login + Authenticated Request

```robot
*** Test Cases ***
API Login Und Note Erstellen
    RESTStart              NotesAPI

    # Login
    RESTSelectEndpoint     /users/login
    RESTSetValue           email        practice@expandtesting.com
    RESTSetValue           password     NewPassword1!
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTMemorizeValue      data.token   TOKEN

    # Note anlegen (mit Auth-Token)
    RESTSelectEndpoint     /notes
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           title        Meine Notiz
    RESTSetValue           description  Inhalt der Notiz
    RESTSetValue           category     Work
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValue        data.title   Meine Notiz

    RESTStop
```

### Example 3: Nested Request Body

```robot
*** Test Cases ***
Verschachtelte Bestellung
    RESTStart              OrderAPI

    RESTSelectEndpoint     /orders

    RESTSetContext         customer
    RESTSetValue           name         Zoltan
    RESTSetValue           email        z@test.com

    RESTSetContext         customer.address
    RESTSetValue           street       Hauptstr. 1
    RESTSetValue           city         Berlin

    RESTSetContext         items[0]
    RESTSetValue           product      Widget A
    RESTSetValue           quantity     3

    RESTSetContext         items[1]
    RESTSetValue           product      Widget B
    RESTSetValue           quantity     1

    RESTSendRequest        POST

    RESTVerifyStatus       201

    RESTSetContext         data.customer
    RESTVerifyValue        name         Zoltan

    RESTSetContext         data.customer.address
    RESTVerifyValue        city         Berlin

    RESTStop
```

### Example 4: Error Cases

```robot
*** Test Cases ***
Fehlende Pflichtfelder
    RESTStart              NotesAPI

    RESTSelectEndpoint     /users/register
    RESTSetValue           name         Zoltan
    RESTSendRequest        POST

    RESTVerifyStatus       400
    RESTVerifyValue        success      false
    RESTVerifyValue        message      Invalid input data

    RESTStop

Ungueltige Authentifizierung
    RESTStart              NotesAPI

    RESTSelectEndpoint     /notes
    RESTSendRequest        GET

    RESTVerifyStatus       401
    RESTVerifyValue        message      Unauthorized Request

    RESTStop
```

### Example 5: Query Parameters

```robot
*** Test Cases ***
Benutzer Suche Mit Query Parametern
    RESTStart              NotesAPI

    RESTSelectEndpoint     /users/search
    RESTSetValue           ?name        Zoltan
    RESTSetValue           ?role        admin
    RESTSetValue           ?page        1
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        data[0].name    Zoltan

    RESTStop

Benutzer Aktualisieren Mit Query Und Body
    RESTStart              NotesAPI

    RESTSelectEndpoint     /users/update
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           ?notify      true
    RESTSetValue           name         Zoltan Neu
    RESTSetValue           email        neu@test.com
    RESTSendRequest        PUT

    RESTVerifyStatus       200
    RESTVerifyValue        data.name    Zoltan Neu

    RESTStop
```

### Example 6: JWT Login + Bearer Auth (DummyJSON)

```robot
*** Test Cases ***
Login Und Profil Abrufen
    RESTStart              DummyJSON

    # Login
    RESTSelectEndpoint     /auth/login
    RESTSetValue           username        emilys
    RESTSetValue           password        emilyspass
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyResponseTime    2000
    RESTMemorizeValue      accessToken     TOKEN

    # Profil mit Bearer Token abrufen
    RESTSelectEndpoint     /auth/me
    RESTSetHeader          Authorization   Bearer $MEM{TOKEN}
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        username        emilys
    RESTVerifyValue        role            admin
    RESTVerifyResponseTime    1000

    RESTStop
```

---

## Phase Model

| Phase | REST Keyword | GUI Equivalent |
|---|---|---|
| Start | `RESTStart` | `StartApp` |
| Scope | `RESTSelectEndpoint` | `SelectWindow` |
| Input | `RESTSetValue` | `SetValue` |
| Context | `RESTSetContext` | `SetContext` |
| Header | `RESTSetHeader` | — |
| Action | `RESTSendRequest` | `ClickOn` |
| Verify | `RESTVerifyValue` | `VerifyValue` |
| Status | `RESTVerifyStatus` | — |
| Timing | `RESTVerifyResponseTime` | — |
| Memorize | `RESTMemorizeValue` | `MemorizeValue` |
| Stop | `RESTStop` | `StopApp` |
