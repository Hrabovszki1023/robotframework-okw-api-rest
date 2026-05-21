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
| `RESTSetValue` | Set request body field or query parameter (`?` prefix) |
| `RESTSetContext` | Navigate into nested JSON object |
| `RESTSetHeader` | Set request header |
| `RESTSendRequest` | Send HTTP request (GET, POST, PUT, PATCH, DELETE) |
| `RESTVerifyValue` | Verify response field value (exact match) |
| `RESTVerifyValueWCM` | Verify response field value (wildcard: `*`, `?`) |
| `RESTVerifyValueREGX` | Verify response field value (regular expression) |
| `RESTVerifyStatus` | Verify HTTP status code |
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
| Memorize | `RESTMemorizeValue` | `MemorizeValue` |
| Stop | `RESTStop` | `StopApp` |

---

## OKW Tokens

| Token | Behavior |
|---|---|
| `$IGNORE` | Keyword becomes a no-op (field is not sent) |
| `$EMPTY` | Set field explicitly to empty string |

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
