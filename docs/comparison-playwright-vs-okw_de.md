# Playwright API Testing vs. OKW REST Keywords

> English version: [comparison-playwright-vs-okw.md](comparison-playwright-vs-okw.md)

Ein Seite-an-Seite-Vergleich von API-Testautomatisierung mit Playwright
(JavaScript) und OKW REST Keywords (Robot Framework).

---

## Das Beispiel: CRUD-Operationen auf Posts

Beide Implementierungen testen dieselbe API
(`https://jsonplaceholder.typicode.com`) mit denselben Operationen:
Create, Read, Update (PUT + PATCH), Delete.

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

**Voraussetzungen:** Node.js, npm, `@playwright/test`, JavaScript-Kenntnisse,
async/await-Verstaendnis, JSON-Object-Syntax.

**Codezeilen:** ~60

---

## OKW REST Keywords (Robot Framework)

### YAML-Konfiguration

```yaml
# locators/JSONPlaceholder.yaml
JSONPlaceholder:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: https://jsonplaceholder.typicode.com
    content_type: application/json
```

### Testdatei

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

    # READ - GET (einzeln)
    RESTSelectEndpoint     /posts/1
    RESTSendRequest        GET
    RESTVerifyStatus       200
    RESTVerifyValue        id         1

    # READ - GET (alle)
    RESTSelectEndpoint     /posts
    RESTSendRequest        GET
    RESTVerifyStatus       200

    # UPDATE - PUT (komplett)
    RESTSelectEndpoint     /posts/1
    RESTSetValue           id         1
    RESTSetValue           title      Updated Title
    RESTSetValue           body       Updated Body Content
    RESTSetValue           userId     1
    RESTSendRequest        PUT
    RESTVerifyStatus       200
    RESTVerifyValue        title      Updated Title
    RESTVerifyValue        body       Updated Body Content

    # UPDATE - PATCH (teilweise)
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

**Voraussetzungen:** Python >= 3.10, `pip install robotframework-okw-api-rest`.
Keine Programmierkenntnisse erforderlich.

**Keyword-Zeilen:** ~40

---

## Direkter Vergleich

### Wert setzen

| Playwright | OKW REST |
|---|---|
| `data: { title: 'Test', body: 'Content' }` | `RESTSetValue title Test` |
| JSON-Object-Syntax, Klammern, Anfuehrungszeichen, Kommas | Feldname + Wert, eine Zeile |

### Request senden

| Playwright | OKW REST |
|---|---|
| `const response = await request.post(url, { data: {...} });` | `RESTSendRequest POST` |
| URL-Konstruktion, async/await, Variablenzuweisung | Ein Keyword, ein Argument |

### Response pruefen

| Playwright | OKW REST |
|---|---|
| `const body = await response.json();` | `RESTVerifyValue title Test` |
| `expect(body.title).toBe('Test');` | Eine Zeile statt zwei |

### Statuscode pruefen

| Playwright | OKW REST |
|---|---|
| `expect(response.status()).toBe(201);` | `RESTVerifyStatus 201` |

---

## Feature-Vergleich

| Feature | Playwright | OKW REST |
|---|---|---|
| HTTP-Methoden (GET/POST/PUT/PATCH/DELETE) | Ja | Ja |
| Request Headers | Ja | Ja (`RESTSetHeader`) |
| Query-Parameter | Manuelle URL-Konstruktion | `RESTSetValue ?param wert` |
| Verschachtelte JSON-Bodies | Manuelles Object-Nesting | `RESTSetContext pfad` |
| Statuscode-Pruefung | Ja | Ja (`RESTVerifyStatus`) |
| Response-Feld-Pruefung | Ja | Ja (`RESTVerifyValue`) |
| Wildcard / Regex | Eigener Code noetig | Eingebaut (`WCM`, `REGX`) |
| Antwortzeit pruefen | Eigener Code noetig | `RESTVerifyResponseTime` |
| Werte speichern und wiederverwenden | Manuelle Variablen | `$MEM{KEY}` |
| Umgebungstrennung | `.env`-Dateien oder Config | `~/.okw/env/`-Konvention |
| Auth (Basic/Bearer/API Key) | Manuelles Header-Setup | YAML-Konfiguration |
| SSL / mTLS-Zertifikate | Manuelle Konfiguration | YAML-Konfiguration |
| Passwort-Maskierung im Log | Nein | Automatisch |
| Felder dynamisch weglassen | `if`-Bloecke noetig | `$IGNORE`-Token |
| GUI + API gleiche Keywords | Nein (andere API) | Ja (gleiches Keyword-Modell) |

---

## Wer sollte was verwenden?

| Situation | Playwright | OKW REST |
|---|---|---|
| Entwickler arbeitet alleine | Bevorzugt — volle Power | Funktioniert, aber eingeschraenkt |
| Tester ohne Code-Erfahrung | Huerde zu hoch | Sofort produktiv |
| BA spezifiziert Testfaelle | Kann den Code nicht lesen | Kann lesen UND schreiben |
| Team mit gemischten Skills | Nur Devs koennen aendern | Alle koennen beitragen |
| GUI + API einheitlich testen | Zwei verschiedene Frameworks | Gleiches Keyword-Modell |
| KI generiert Tests | Moeglich, fehleranfaellig | Einfache Struktur, zuverlaessig |
| Review durch Fachbereich | Sieht Code, versteht nichts | Liest sich wie Spezifikation |

---

## Der $IGNORE-Vorteil

Etwas, das kein code-basiertes Framework so elegant kann:

```robot
*** Keywords ***
Registriere Benutzer
    [Arguments]    ${name}=DefaultUser    ${email}=default@test.com    ${password}=Test1234!
    RESTSelectEndpoint     /users/register
    RESTSetValue           name         ${name}
    RESTSetValue           email        ${email}
    RESTSetValue           password     ${password}
    RESTSendRequest        POST

*** Test Cases ***
Standard Registrierung
    Registriere Benutzer
    RESTVerifyStatus    201

Eigener Name
    Registriere Benutzer    name=Zoltan
    RESTVerifyStatus    201

Fehlende Email Verursacht Fehler
    Registriere Benutzer    email=$IGNORE
    RESTVerifyStatus    400
```

Drei Tests, ein Keyword. `$IGNORE` entfernt das Feld komplett aus dem
Request — keine `if`-Bloecke, keine bedingte Logik, kein Code.

In Playwright braeuchte man:

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

## Das einheitliche Keyword-Modell

OKW nutzt dasselbe Denkmodell fuer GUI- und API-Tests:

```robot
# GUI-Test
StartApp           MeineApp
SelectWindow       LoginSeite
SetValue           Benutzername    admin
SetValue           Passwort        geheim
ClickOn            Anmelden
VerifyValue        Status          Eingeloggt
StopApp

# REST-Test (gleiche Denkweise!)
RESTStart              MeineAPI
RESTSelectEndpoint     /auth/login
RESTSetValue           username    admin
RESTSetValue           password    geheim
RESTSendRequest        POST
RESTVerifyValue        status      logged_in
RESTStop
```

Ein Modell lernen, alles testen.

---

## Fazit

Playwright ist das **bessere Werkzeug fuer Entwickler**. OKW REST ist
die **bessere Loesung fuer Teams**.

Der Wert liegt nicht in technischer Ueberlegenheit — sondern darin,
dass **mehr Menschen Tests schreiben, lesen und pflegen koennen**, ohne
Programmierer sein zu muessen.

---

## Links

- [OKW REST Keywords](../README_de.md)
- [Keyword-Spezifikation](rest-keywords.md)
- [Playwright API Testing Docs](https://playwright.dev/docs/api-testing)
