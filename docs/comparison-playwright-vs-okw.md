# Playwright API Testing vs. OKW REST Keywords

> Deutsche Version: [comparison-playwright-vs-okw_de.md](comparison-playwright-vs-okw_de.md)

A side-by-side comparison of API test automation with Playwright (JavaScript)
and OKW REST Keywords (Robot Framework).

---

## The Example: CRUD Operations on Posts

Both implementations test the same API (`https://jsonplaceholder.typicode.com`)
with the same operations: Create, Read, Update (PUT + PATCH), Delete.

---

## Playwright (JavaScript)

```javascript
const { test, expect } = require('@playwright/test');
const BASE_URL = 'https://jsonplaceholder.typicode.com';

// CREATE - POST
test('CREATE - Add a new post', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/posts`, {
        data: {
            title: 'This is API testing',
            body: 'This is a sample POST request',
            userId: 1
        },
    });
    expect(response.status()).toBe(201);
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('id');
    expect(responseBody.title).toBe('This is API testing');
});

// READ - GET (single)
test('READ - Get a post by ID', async ({ request }) => {
    const postId = 1;
    const response = await request.get(`${BASE_URL}/posts/${postId}`);
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    expect(responseBody.id).toBe(postId);
});

// READ - GET (all)
test('READ - Get all posts', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/posts`);
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    expect(Array.isArray(responseBody)).toBe(true);
    expect(responseBody.length).toBeGreaterThan(0);
});

// UPDATE - PUT (full update)
test('UPDATE - Update a post (PUT)', async ({ request }) => {
    const postId = 1;
    const response = await request.put(`${BASE_URL}/posts/${postId}`, {
        data: {
            id: postId,
            title: 'Updated Title',
            body: 'Updated Body Content',
            userId: 1,
        },
    });
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    expect(responseBody.title).toBe('Updated Title');
    expect(responseBody.body).toBe('Updated Body Content');
});

// UPDATE - PATCH (partial update)
test('UPDATE - Partially update a post (PATCH)', async ({ request }) => {
    const postId = 1;
    const response = await request.patch(`${BASE_URL}/posts/${postId}`, {
        data: {
            title: 'Partially Updated Title'
        },
    });
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    expect(responseBody.title).toBe('Partially Updated Title');
});

// DELETE - DELETE
test('DELETE - Delete a post', async ({ request }) => {
    const postId = 1;
    const response = await request.delete(`${BASE_URL}/posts/${postId}`);
    expect(response.status()).toBe(200);
});
```

**Requirements:** Node.js, npm, `@playwright/test`, JavaScript knowledge,
async/await understanding, JSON object syntax.

**Lines of code:** ~60

---

## OKW REST Keywords (Robot Framework)

### YAML Configuration

```yaml
# locators/JSONPlaceholder.yaml
JSONPlaceholder:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: https://jsonplaceholder.typicode.com
    content_type: application/json
```

### Test File

```robot
*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
CRUD Operationen Auf Posts
    RESTStart              JSONPlaceholder

    # CREATE - POST
    RESTSelectEndpoint     /posts
    RESTSetValue           title      This is API testing
    RESTSetValue           body       This is a sample POST request
    RESTSetValue           userId     1
    RESTSendRequest        POST
    RESTVerifyStatus       201
    RESTVerifyValue        title      This is API testing
    RESTMemorizeValue      id         POST_ID

    # READ - GET (single)
    RESTSelectEndpoint     /posts/1
    RESTSendRequest        GET
    RESTVerifyStatus       200
    RESTVerifyValue        id         1

    # READ - GET (all)
    RESTSelectEndpoint     /posts
    RESTSendRequest        GET
    RESTVerifyStatus       200

    # UPDATE - PUT (full)
    RESTSelectEndpoint     /posts/1
    RESTSetValue           id         1
    RESTSetValue           title      Updated Title
    RESTSetValue           body       Updated Body Content
    RESTSetValue           userId     1
    RESTSendRequest        PUT
    RESTVerifyStatus       200
    RESTVerifyValue        title      Updated Title
    RESTVerifyValue        body       Updated Body Content

    # UPDATE - PATCH (partial)
    RESTSelectEndpoint     /posts/1
    RESTSetValue           title      Partially Updated Title
    RESTSendRequest        PATCH
    RESTVerifyStatus       200
    RESTVerifyValue        title      Partially Updated Title

    # DELETE
    RESTSelectEndpoint     /posts/1
    RESTSendRequest        DELETE
    RESTVerifyStatus       200

    RESTStop
```

**Requirements:** Python >= 3.10, `pip install robotframework-okw-api-rest`.
No programming knowledge needed.

**Lines of keywords:** ~40

---

## Side-by-Side Comparison

### Setting a Value

| Playwright | OKW REST |
|---|---|
| `data: { title: 'Test', body: 'Content' }` | `RESTSetValue title Test` |
| JSON object syntax, braces, quotes, commas | Field name + value, one per line |

### Sending a Request

| Playwright | OKW REST |
|---|---|
| `const response = await request.post(url, { data: {...} });` | `RESTSendRequest POST` |
| URL construction, async/await, variable assignment | One keyword, one argument |

### Verifying the Response

| Playwright | OKW REST |
|---|---|
| `const body = await response.json();` | `RESTVerifyValue title Test` |
| `expect(body.title).toBe('Test');` | One line instead of two |

### Verifying the Status Code

| Playwright | OKW REST |
|---|---|
| `expect(response.status()).toBe(201);` | `RESTVerifyStatus 201` |

---

## Feature Comparison

| Feature | Playwright | OKW REST |
|---|---|---|
| HTTP methods (GET/POST/PUT/PATCH/DELETE) | Yes | Yes |
| Request headers | Yes | Yes (`RESTSetHeader`) |
| Query parameters | Manual URL construction | `RESTSetValue ?param value` |
| Nested JSON body | Manual object nesting | `RESTSetContext path` |
| Status code assertion | Yes | Yes (`RESTVerifyStatus`) |
| Response field assertion | Yes | Yes (`RESTVerifyValue`) |
| Wildcard / regex match | Custom code needed | Built-in (`WCM`, `REGX`) |
| Response time check | Custom code needed | `RESTVerifyResponseTime` |
| Store and reuse values | Manual variable handling | `$MEM{KEY}` |
| Environment separation | `.env` files or config | `~/.okw/env/` convention |
| Auth (Basic/Bearer/API Key) | Manual header setup | YAML configuration |
| SSL / mTLS certificates | Manual config | YAML configuration |
| Password masking in logs | No | Automatic |
| Skip fields dynamically | `if` blocks needed | `$IGNORE` token |
| GUI + API same keywords | No (different API) | Yes (same keyword model) |

---

## Who Should Use What?

| Situation | Playwright | OKW REST |
|---|---|---|
| Developer working alone | Preferred — full power | Works, but limited |
| Tester without coding skills | Barrier too high | Immediately productive |
| BA specifies test cases | Cannot read the code | Can read AND write |
| Team with mixed skill levels | Only devs can change tests | Everyone can contribute |
| GUI + API unified testing | Two different frameworks | Same keyword model |
| AI generates tests | Possible, error-prone | Simple structure, reliable |
| Review by domain experts | Sees code, understands nothing | Reads like a specification |

---

## The $IGNORE Advantage

Something no code-based framework can do as elegantly:

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

Missing Email Causes Error
    Register User    email=$IGNORE
    RESTVerifyStatus    400
```

Three tests, one keyword. `$IGNORE` removes the field from the request
entirely — no `if` blocks, no conditional logic, no code.

In Playwright, you would need:

```javascript
function buildPayload(overrides = {}) {
    const defaults = { name: 'DefaultUser', email: 'default@test.com', password: 'Test1234!' };
    const merged = { ...defaults, ...overrides };
    return Object.fromEntries(
        Object.entries(merged).filter(([_, v]) => v !== null)
    );
}
```

---

## The Unified Keyword Model

OKW uses the same mental model for GUI and API testing:

```robot
# GUI Test
StartApp           MyApp
SelectWindow       LoginPage
SetValue           Username    admin
SetValue           Password    secret
ClickOn            Login
VerifyValue        Status      Logged In
StopApp

# REST Test (same thinking!)
RESTStart              MyAPI
RESTSelectEndpoint     /auth/login
RESTSetValue           username    admin
RESTSetValue           password    secret
RESTSendRequest        POST
RESTVerifyValue        status      logged_in
RESTStop
```

Learn one model, test everything.

---

## Conclusion

Playwright is the **better tool for developers**. OKW REST is the
**better solution for teams**.

The value is not in technical superiority — it is in enabling **more
people to write, read, and maintain tests** without being a programmer.

---

## Links

- [OKW REST Keywords](../README.md)
- [Keyword Specification](rest-keywords.md)
- [Playwright API Testing Docs](https://playwright.dev/docs/api-testing)
