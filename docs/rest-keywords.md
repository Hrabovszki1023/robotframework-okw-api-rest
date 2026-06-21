# OKW REST Keywords

Keyword-driven REST API testing for OKW4Robot.

---

## Keyword Overview

| Keyword | Description |
|---|---|
| `RESTStart` | Start REST service (load YAML, base URL) |
| `RESTStop` | Stop REST service |
| `RESTSelectEndpoint` | Select endpoint path |
| `RESTSetValue` | Set request body field (auto type: int, float, bool, null) |
| `RESTSetValueAsString` | Set request body field (always string, no conversion) |
| `RESTSetValueAsList` | Set request body field as JSON array |
| `RESTSetFile` | Set file field for multipart form-data upload |
| `RESTSetContext` | Navigate into nested JSON object |
| `RESTSetHeader` | Set request header |
| `RESTSendRequest` | Send HTTP request |
| `RESTVerifyValue` | Verify response field value (exact match) |
| `RESTVerifyValueWCM` | Verify response field value (wildcard: `*`, `?`) |
| `RESTVerifyValueREGX` | Verify response field value (regular expression) |
| `RESTVerifyStatus` | Verify HTTP status code |
| `RESTVerifyResponseTime` | Verify response time is below threshold |
| `RESTVerifyListCount` | Verify number of elements in a JSON array |
| `RESTVerifyHeader` | Verify response header |
| `RESTMemorizeValue` | Store response field value |
| `RESTMemorizeBody` | Store entire response body |
| `RESTSaveResponseToFile` | Save response body to a local file (binary-safe) |

---

## OKW Tokens

| Token | Behavior |
|---|---|
| `$IGNORE` | Keyword becomes a no-op (field is not sent) |
| `$EMPTY` | Set field explicitly to empty string |
| `$NULL` | Set field explicitly to JSON `null` |

Tokens work in `RESTSetValue`, `RESTSetValueAsString`, `RESTSetFile`, `RESTSetHeader`,
`RESTVerifyValue`, `RESTVerifyValueWCM`, `RESTVerifyValueREGX`,
`RESTVerifyStatus`, `RESTVerifyResponseTime`, `RESTVerifyListCount`,
`RESTVerifyHeader`, and `RESTSaveResponseToFile`.

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

**OAuth 2.0 Client Credentials:**

For machine-to-machine API access. `RESTStart` automatically fetches
an access token from the token server and sets
`Authorization: Bearer <token>` on every request.

```yaml
# locators/MeineAPI.yaml — safe for repo (only placeholders)
MeineAPI:
  __self__:
    base_url: https://api.example.com
    auth_type: oauth2_client_credentials
    token_url: https://auth.example.com/oauth/token
    client_id: ${CLIENT_ID}
    client_secret: ${CLIENT_SECRET}
    scope: read write
```

```yaml
# ~/.okw/env/env-test.yaml — NOT in repo
CLIENT_ID: my-service-account
CLIENT_SECRET: geheim123
```

| Setting | Required | Description |
|---|---|---|
| `auth_type` | yes | Must be `oauth2_client_credentials` |
| `token_url` | yes | Full URL of the OAuth token endpoint |
| `client_id` | yes | Client ID (from API provider) |
| `client_secret` | yes | Client Secret (from API provider) |
| `scope` | no | Space-separated scopes (default: none) |

**How the connection works** (YAML ↔ env file ↔ test):

```
locators/MeineAPI.yaml          ~/.okw/env/env-test.yaml
  client_id: ${CLIENT_ID}   →     CLIENT_ID: my-service-account
  client_secret: ${CLIENT_SECRET} → CLIENT_SECRET: geheim123

Test file:
  RESTStart    MeineAPI    env-test
               ↑            ↑
               │            └── loads env file, resolves ${...} placeholders
               └── loads YAML config
```

1. `RESTStart MeineAPI env-test` loads the service YAML
2. Loads `~/.okw/env/env-test.yaml` and replaces all `${VAR}` placeholders
3. Detects `auth_type: oauth2_client_credentials`
4. Sends `POST token_url` with `grant_type=client_credentials` + credentials
5. Stores the returned `access_token` — added to every request automatically

The test code sees nothing of this:

```robot
RESTStart              MeineAPI    env-test
RESTSelectEndpoint     /api/data
RESTSendRequest        GET
RESTVerifyStatus       200
RESTStop
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

### Retry on error

Automatic retry for transient HTTP errors. Configured in `__self__` —
the test code is not affected.

```yaml
__self__:
  base_url: ${BASE_URL}
  retry_count: 3           # max retries (default: 0 = off)
  retry_delay: 1000        # delay between retries in ms (default: 1000)
  retry_on: 429,502,503    # status codes that trigger retry
```

When a response matches a `retry_on` status code, the request is
automatically repeated up to `retry_count` times with `retry_delay`
milliseconds between attempts. The log shows each retry:

```
<<< 429 — retry 1/3 (waiting 1000ms)
<<< 429 — retry 2/3 (waiting 1000ms)
<<< 200 OK
    Response Body: {...}
```

If all retries fail, the last response is stored — subsequent
`RESTVerifyStatus` will see the error status code and the test fails.

**`retry_on` formats:**
- String: `"429,502,503"` (comma-separated)
- List: `[429, 502, 503]`
- Single value: `429`

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

**Auto type detection:** Body field values are automatically converted
to their native JSON type. The tester writes only field name and value —
the correct JSON type is determined automatically.

| Parameter | Description |
|---|---|
| `field` | Field name (JSON key) — prefix with `?` for query parameter |
| `value` | Field value (auto-typed for body fields) |

### Automatic type conversion (body fields)

| Input value | JSON result | Rule |
|---|---|---|
| `Zoltan` | `"Zoltan"` | Text → string |
| `user@test.com` | `"user@test.com"` | Text → string |
| `42` | `42` | Integer pattern → number |
| `3.14` | `3.14` | Float pattern → number |
| `true` | `true` | Boolean keyword → boolean |
| `false` | `false` | Boolean keyword → boolean |
| `null` or `$NULL` | `null` | Null keyword → null |
| `$EMPTY` | `""` | Empty string |

```robot
RESTSetValue    name        Zoltan       # → "name": "Zoltan"
RESTSetValue    count       42           # → "count": 42
RESTSetValue    price       3.14         # → "price": 3.14
RESTSetValue    active      true         # → "active": true
RESTSetValue    completed   false        # → "completed": false
RESTSetValue    comment     $NULL        # → "comment": null
RESTSetValue    email       $EMPTY       # → "email": ""
```

Values that look like a number or boolean but must be sent as a
**string** → use `RESTSetValueAsString` instead.

### Query parameters (`?` prefix)

Fields prefixed with `?` are sent as URL query parameters instead of
body fields. Query parameters are **always strings** (no type
conversion) — the `?` prefix is stripped before building the URL.

```robot
RESTSetValue    ?name      Zoltan       # → ?name=Zoltan
RESTSetValue    ?city      Berlin       # → &city=Berlin
RESTSetValue    ?page      1            # → &page=1 (string in URL)
```

Query parameters work with all HTTP methods. They are appended to
the endpoint URL as `?key=value&key=value`.

### Mixed: query parameters + body

```robot
RESTSelectEndpoint    /users/search
RESTSetValue          ?role       admin        # query param (string)
RESTSetValue          ?active     true         # query param (string)
RESTSetValue          filter      name=Z*      # body field (string)
RESTSetValue          limit       10           # body field (integer)
RESTSendRequest       PUT
```

Result: `PUT /users/search?role=admin&active=true` with body
`{"filter": "name=Z*", "limit": 10}`.

### With active context

```robot
RESTSetContext    customer
RESTSetValue      name      Zoltan       # → customer.name (string)
RESTSetValue      age       29           # → customer.age (integer)
RESTSetValue      active    true         # → customer.active (boolean)
```

Context applies only to body fields — query parameters are always
top-level and not affected by `RESTSetContext`.

### OKW tokens

- `$IGNORE` — skip this keyword (no-op)
- `$EMPTY` — set explicitly to empty string
- `$NULL` — set explicitly to JSON `null`

---

## RESTSetValueAsString

Sets a request body field **always as string**, without automatic type
conversion. Use this when a value looks like a number or boolean but
the API expects a string.

| Parameter | Description |
|---|---|
| `field` | Field name (JSON key) |
| `value` | Field value (always sent as string) |

```robot
RESTSetValueAsString    zipcode    01234    # → "zipcode": "01234"
RESTSetValueAsString    flag       true     # → "flag": "true"
RESTSetValueAsString    code       42       # → "code": "42"
RESTSetValueAsString    version    3.0      # → "version": "3.0"
```

**When to use which:**

| Situation | Keyword | Result |
|---|---|---|
| Normal value | `RESTSetValue count 42` | `"count": 42` (integer) |
| Must be string | `RESTSetValueAsString count 42` | `"count": "42"` (string) |
| Normal boolean | `RESTSetValue active true` | `"active": true` (boolean) |
| Must be string | `RESTSetValueAsString active true` | `"active": "true"` (string) |

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

`RESTSendRequest` automatically logs request and response with full
headers and formatted body in the Robot log. Sensitive fields
(`password`, `token`, `secret`) are masked with `***` in the request
body. Headers are logged in cleartext for maximum observability.

Example log output:

```
>>> POST https://dummyjson.com/auth/login
    Headers:
      Content-Type: application/json
      User-Agent: python-requests/2.31.0
    Request Body:
{
  "username": "emilys",
  "password": "***",
  "expiresInMins": "30"
}

<<< 200 OK
    Headers:
      Content-Type: application/json; charset=utf-8
      Set-Cookie: accessToken=eyJ...; Path=/; HttpOnly
    Response Body:
{
  "accessToken": "eyJ...",
  "username": "emilys",
  "firstName": "Emily"
}
```

All headers (request and response) are logged unmasked for debugging.
Cookies sent via `Set-Cookie` are automatically stored and resent by
the underlying `requests.Session` — no manual cookie handling needed.

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

## RESTVerifyListCount

Verifies the number of elements in a JSON array field.
The field must resolve to a list in the response. Context-aware.

| Parameter | Description |
|---|---|
| `field` | JSON field path (must be an array) |
| `expected` | Expected number of elements |

```robot
RESTVerifyListCount    todos      3
RESTVerifyListCount    data       5
RESTVerifyListCount    items      0
RESTVerifyListCount    $IGNORE    0
```

Example log output:

```
RESTVerifyListCount: todos has 3 elements (PASS)
```

If the count does not match:

```
RESTVerifyListCount: 'todos' has 5 elements, expected 3.
```

If the field is not a list:

```
RESTVerifyListCount: 'name' is not a list (got str).
```

---

## RESTSetValueAsList

Sets a request body field as a JSON array from variable arguments.
All values are auto-typed. Without arguments, creates an empty array.

| Parameter | Description |
|---|---|
| `field` | Field name (JSON key) |
| `*values` | Zero or more values for the array |

```robot
RESTSetValueAsList    tags      wichtig    dringend    arbeit
RESTSetValueAsList    scores    42         87          15
RESTSetValueAsList    flags     true       false       true
RESTSetValueAsList    items                                      
```

Results:
- `"tags": ["wichtig", "dringend", "arbeit"]`
- `"scores": [42, 87, 15]` (auto-typed integers)
- `"flags": [true, false, true]` (auto-typed booleans)
- `"items": []` (empty array, no arguments)

### Alternative: Array index syntax

For longer arrays or mixed-type arrays, use index syntax in
`RESTSetValue`:

```robot
RESTSetValue    scores[0]    42
RESTSetValue    scores[1]    87
RESTSetValue    scores[2]    15
```

Both approaches produce the same JSON: `"scores": [42, 87, 15]`.

---

## RESTSetFile

Sets a file field for multipart form-data upload. When files are
present, `RESTSendRequest` automatically switches from JSON to
multipart encoding. Text fields set via `RESTSetValue` are sent as
form fields alongside the files.

| Parameter | Description |
|---|---|
| `field` | Form field name (e.g. `file`, `avatar`, `attachments`) |
| `filepath` | Path to the file to upload |
| `mime_type` | (optional) MIME type override (auto-detected from extension) |

```robot
RESTSetFile    avatar     C:/img/photo.jpg
RESTSetFile    document   report.pdf                   application/pdf
```

### Multiple files

Call `RESTSetFile` multiple times — files accumulate until
`RESTSelectEndpoint` resets them.

```robot
RESTSetFile    attachments    file1.jpg
RESTSetFile    attachments    file2.jpg
```

Multiple files with the **same field name** are supported (like
`<input type="file" multiple>`) — internally stored as a list of
tuples, not a dict.

### Mixed: files + text fields

```robot
RESTSelectEndpoint    /api/documents
RESTSetValue          title       Annual Report
RESTSetValue          category    Finance
RESTSetFile           file        report.pdf
RESTSendRequest       POST
```

Text fields from `RESTSetValue` are sent as `data=` form fields.
The `Content-Type` header is **not set manually** — `requests`
generates `multipart/form-data` with the correct boundary.

### MIME type detection

The MIME type is auto-detected from the file extension using Python's
`mimetypes.guess_type()`. An optional third argument overrides it:

| Extension | Auto-detected MIME type |
|---|---|
| `.jpg`, `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.pdf` | `application/pdf` |
| `.txt` | `text/plain` |
| `.csv` | `text/csv` |
| `.json` | `application/json` |
| unknown | `application/octet-stream` |

### File paths

- Absolute and relative paths are supported
- `~` expands to the user's home directory
- `$ENV_VAR` and `${CURDIR}` (Robot variable) are expanded
- Missing files raise `FileNotFoundError` before sending the request

### Log output

```
>>> POST https://api.example.com/upload
    File: file: report.pdf (application/pdf, 1.2 MB)
          Content: (binary, first 20 bytes: 25 50 44 46 2d 31 2e 34 ...)
    Request Body:
{"title": "Annual Report", "category": "Finance"}
```

Text files show readable content:

```
    File: data: notes.txt (text/plain, 45 B)
          Content: 'Hello World\nSecond line\n'
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

## RESTSaveResponseToFile

Saves the HTTP response body to a local file. The response is written as
raw bytes, which works correctly for both binary (PDF, images, ZIP) and
text content (JSON, XML, CSV).

| Parameter | Description |
|---|---|
| `filepath` | Target file path. Supports `$MEM{name}`, `~`, `$ENV_VAR`. |

Parent directories are created automatically. If the file already exists,
it is overwritten (logged as warning).

```robot
# Save JSON response
RESTSaveResponseToFile    C:/temp/response.json

# Save with memory expansion
RESTSaveResponseToFile    $MEM{DOWNLOAD_DIR}/export.csv

# Save to home directory
RESTSaveResponseToFile    ~/downloads/report.pdf

# Skip saving
RESTSaveResponseToFile    $IGNORE
```

**Log output:**

```
RESTSaveResponseToFile: 4523 bytes -> 'C:/temp/response.json' (Content-Type: application/json; charset=utf-8)
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

### Example 7: File Upload

```robot
*** Test Cases ***
Dokument Hochladen
    RESTStart              MyAPI

    RESTSelectEndpoint     /api/documents
    RESTSetValue           title       Jahresbericht
    RESTSetValue           category    Finance
    RESTSetFile            file        ${CURDIR}/testdata/report.pdf
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValue        data.filename    report.pdf

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
| File | `RESTSetFile` | — |
| Action | `RESTSendRequest` | `ClickOn` |
| Verify | `RESTVerifyValue` | `VerifyValue` |
| Status | `RESTVerifyStatus` | — |
| Timing | `RESTVerifyResponseTime` | — |
| Memorize | `RESTMemorizeValue` | `MemorizeValue` |
| Save | `RESTSaveResponseToFile` | — |
| Stop | `RESTStop` | `StopApp` |
