# robotframework-okw-api-rest

[![PyPI](https://img.shields.io/pypi/v/robotframework-okw-api-rest)](https://pypi.org/project/robotframework-okw-api-rest/)
[![Python](https://img.shields.io/pypi/pyversions/robotframework-okw-api-rest)](https://pypi.org/project/robotframework-okw-api-rest/)
[![License](https://img.shields.io/badge/License-OKW_Community-orange.svg)](LICENSE)

> English version: [README.md](README.md)

Keyword-gesteuertes REST-API-Testing für [OKW4Robot](https://github.com/Hrabovszki1023/robotframework-okw4robot) — ein Satz Keywords für den kompletten REST-Lebenszyklus.

## Signal vs. NOISE

| Signal (dein Test) | NOISE (versteckt in YAML) |
|---|---|
| `RESTSetValue email user@test.com` | Basis-URL, Content-Type, Auth-Header |
| `RESTSendRequest POST` | requests.Session, Retry-Logik, SSL-Konfiguration |
| `RESTVerifyStatus 200` | Response-Parsing, Status-Code-Extraktion |

[Keyword-Dokumentation (Libdoc)](https://hrabovszki1023.github.io/robotframework-okw-api-rest/OkwApiRestLibrary.html)

---

## Installation

```bash
pip install robotframework-okw-api-rest
```

Oder editierbar (für Entwicklung):

```bash
pip install -e Pfad/zu/robotframework-okw-api-rest
```

### Abhängigkeiten

- Python >= 3.10
- robotframework >= 6.0
- requests >= 2.28
- PyYAML >= 6.0
- okw-contract-utils >= 0.2.0

---

## Schnelleinstieg

### 1. YAML-Konfiguration

Datei `locators/NotesAPI.yaml` anlegen:

```yaml
NotesAPI:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: https://practice.expandtesting.com/notes/api
    content_type: application/x-www-form-urlencoded
```

### 2. Testdatei

```robot
*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Gesundheitscheck
    RESTStart              NotesAPI
    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET
    RESTVerifyStatus       200
    RESTStop
```

### 3. Ausführen

```bash
robot tests/REST_NotesAPI.robot
```

---

## Keywords

| Keyword | Beschreibung |
|---|---|
| `RESTStart` | REST-Service starten (YAML laden, Basis-URL) |
| `RESTStop` | REST-Service stoppen |
| `RESTSelectEndpoint` | Endpoint-Pfad wählen |
| `RESTSetValue` | Request-Body-Feld oder Query-Parameter setzen (Auto-Typ-Erkennung) |
| `RESTSetValueAsString` | Request-Body-Feld setzen (immer String, keine Konvertierung) |
| `RESTSetValueAsList` | Request-Body-Feld als JSON-Array setzen |
| `RESTSetFile` | Datei-Feld für Multipart-Upload setzen |
| `RESTSetContext` | In verschachteltes JSON-Objekt navigieren |
| `RESTSetHeader` | Request-Header setzen |
| `RESTSendRequest` | HTTP-Request senden (GET, POST, PUT, PATCH, DELETE) |
| `RESTVerifyValue` | Response-Feldwert prüfen (exakter Vergleich) |
| `RESTVerifyValueWCM` | Response-Feldwert prüfen (Wildcard: `*`, `?`) |
| `RESTVerifyValueREGX` | Response-Feldwert prüfen (regulärer Ausdruck) |
| `RESTVerifyStatus` | HTTP-Statuscode prüfen |
| `RESTVerifyResponseTime` | Response-Zeit unter Schwellwert prüfen (ms) |
| `RESTVerifyListCount` | Anzahl Elemente in einem JSON-Array prüfen |
| `RESTVerifyHeader` | Response-Header prüfen |
| `RESTMemorizeValue` | Response-Feldwert speichern für `$MEM{name}` |
| `RESTMemorizeBody` | Gesamten Response-Body speichern |
| `RESTSaveResponseToFile` | Response-Body als lokale Datei speichern (binärsicher) |

---

## Phasenmodell

| Phase | REST Keyword | GUI-Äquivalent |
|---|---|---|
| Start | `RESTStart` | `StartApp` |
| Scope | `RESTSelectEndpoint` | `SelectWindow` |
| Eingabe | `RESTSetValue` | `SetValue` |
| Kontext | `RESTSetContext` | `SetContext` |
| Header | `RESTSetHeader` | -- |
| Datei | `RESTSetFile` | -- |
| Aktion | `RESTSendRequest` | `ClickOn` |
| Prüfen | `RESTVerifyValue` | `VerifyValue` |
| Status | `RESTVerifyStatus` | -- |
| Timing | `RESTVerifyResponseTime` | -- |
| Merken | `RESTMemorizeValue` | `MemorizeValue` |
| Speichern | `RESTSaveResponseToFile` | -- |
| Stop | `RESTStop` | `StopApp` |

---

## OKW-Token

| Token | Verhalten |
|---|---|
| `$IGNORE` | Keyword wird übersprungen (Feld wird nicht gesendet) |
| `$EMPTY` | Feld wird explizit auf leeren String gesetzt |
| `$NULL` | Feld wird explizit auf JSON `null` gesetzt |

---

## Automatische Typ-Erkennung

`RESTSetValue` konvertiert Werte automatisch in den passenden JSON-Typ:

```robot
RESTSetValue    name        Zoltan       # → String "Zoltan"
RESTSetValue    count       42           # → Integer 42
RESTSetValue    price       3.14         # → Float 3.14
RESTSetValue    active      true         # → Boolean true
RESTSetValue    comment     $NULL        # → null
```

`RESTSetValueAsString` verwenden wenn ein Wert String bleiben muss:

```robot
RESTSetValueAsString    zipcode    01234    # → String "01234" (nicht Integer)
RESTSetValueAsString    flag       true     # → String "true" (nicht Boolean)
```

Query-Parameter (`?`-Prefix) sind immer Strings — keine Typ-Konvertierung.

---

## JSON-Arrays

Zwei Wege um Array-Felder zu setzen:

```robot
# Kurzes Array — eine Zeile
RESTSetValueAsList     tags      wichtig    dringend    arbeit

# Array-Index — ein Wert pro Zeile (Auto-Typ)
RESTSetValue           scores[0]    42
RESTSetValue           scores[1]    87
RESTSetValue           scores[2]    15

# Leeres Array
RESTSetValueAsList     items
```

Array-Länge prüfen mit `RESTVerifyListCount`:

```robot
RESTVerifyListCount    todos    3        # todos hat 3 Elemente
RESTVerifyListCount    items    0        # items ist leer
```

---

## Datei-Upload

Dateien via Multipart Form-Data hochladen:

```robot
RESTSelectEndpoint     /api/documents
RESTSetValue           title       Jahresbericht
RESTSetFile            file        ${CURDIR}/testdata/report.pdf
RESTSendRequest        POST
RESTVerifyStatus       200
```

Wenn Dateien vorhanden sind, wechselt `RESTSendRequest` automatisch
auf Multipart-Encoding. Textfelder werden als Formularfelder mitgesendet.

```robot
# Mehrere Dateien, gleicher Feldname
RESTSetFile    attachments    foto1.jpg
RESTSetFile    attachments    foto2.jpg

# Expliziter MIME-Type
RESTSetFile    data    export.bin    application/octet-stream
```

Der MIME-Type wird automatisch aus der Dateiendung erkannt. Pfade unterstützen `~` und `$ENV_VAR`.
Dateiinhalt wird im Robot-Log angezeigt (Text lesbar, Binär als Hex).

---

## Query-Parameter

Felder mit `?`-Prefix werden als URL-Query-Parameter gesendet:

```robot
RESTSetValue    ?page     1          # Query-Parameter: ?page=1
RESTSetValue    name      Zoltan     # Body-Feld
```

Query-Parameter funktionieren mit allen HTTP-Methoden und werden von `RESTSetContext` nicht beeinflusst.

---

## Werte merken und wiederverwenden

Response-Werte speichern und in nachfolgenden Requests nutzen:

```robot
# Token aus Login-Response speichern
RESTMemorizeValue    data.token    TOKEN

# Im nächsten Request verwenden
RESTSetHeader        x-auth-token    $MEM{TOKEN}
RESTSelectEndpoint   /notes/$MEM{NOTE_ID}
```

---

## Verschachtelte Request-Bodies

Mit `RESTSetContext` verschachtelte JSON-Strukturen aufbauen:

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

Erzeugt: `{"customer": {"name": "Zoltan", "email": "z@test.com", "address": {"street": "Hauptstr. 1", "city": "Berlin"}}}`.

---

## Endpoint-Keywords-Muster

Endpoints als wiederverwendbare Keywords mit Defaultwerten kapseln:

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

Fehlende Email
    Registriere Benutzer    email=$IGNORE
    RESTVerifyStatus    400
```

Drei Stufen: kein Argument = Default wird gesendet, eigener Wert = überschreibt Default, `$IGNORE` = Feld wird nicht gesendet.

---

## Umgebungskonfiguration

Credentials und URLs werden per Environment-Datei vom Service-YAML
getrennt — wie `~/.ssh/` die Keys aus den Projekten heraushalt.

### Service-YAML (sicher für Repo)

```yaml
NotesAPI:
  __self__:
    class: okw_api_rest.library.OkwApiRestLibrary
    base_url: ${BASE_URL}
    content_type: ${CONTENT_TYPE}
```

### Environment-Datei (im Userprofil, NICHT im Repo)

```yaml
# ~/.okw/env/env-test.yaml
BASE_URL: https://practice.expandtesting.com/notes/api
CONTENT_TYPE: application/x-www-form-urlencoded
```

### Testdatei

```robot
RESTStart    NotesAPI    env-test
```

### Suchordnung für Env-Dateien

| Priorität | Pfad | Zweck |
|---|---|---|
| 1 | `~/.okw/env/` | Userprofil (sicher) |
| 2 | `$OKW_ENV_DIR` | CI/CD Override |
| 3 | `locators/` neben Test | Entwicklung |
| 4 | OS-Umgebungsvariablen | Fallback |

---

## Authentifizierung

Im YAML `__self__` konfiguriert — keine Credentials im Testcode.

```yaml
# Basic Auth
auth_type: basic
auth_user: ${API_USER}
auth_password: ${API_PASSWORD}

# API Key
auth_type: api_key
auth_header: X-API-Key
auth_key: ${API_KEY}

# Bearer Token (statisch)
auth_type: bearer
auth_token: ${AUTH_TOKEN}
```

**OAuth 2.0 Client Credentials** (Maschine-zu-Maschine):

```yaml
auth_type: oauth2_client_credentials
token_url: https://auth.example.com/oauth/token
client_id: ${CLIENT_ID}
client_secret: ${CLIENT_SECRET}
scope: read write
```

`RESTStart` holt den Token automatisch — der Testcode merkt nichts von OAuth.

Für dynamische Token (Login-Flow) `RESTMemorizeValue` + `RESTSetHeader` verwenden.

---

## SSL / Zertifikate

```yaml
verify_ssl: false                        # Self-signed Certs
client_cert: ~/.okw/certs/client.pem     # mTLS
client_key: ~/.okw/certs/client.key
ca_bundle: ~/.okw/certs/ca-bundle.pem    # Custom CA
```

Pfade unterstützen `~` und `$ENV_VAR` Expansion.

### Verzeichnisstruktur im Userprofil

```
~/.okw/
  env/
    env-test.yaml       # Credentials + URLs
    env-prod.yaml
  certs/
    client.pem          # Client-Zertifikat
    client.key          # Private Key
    ca-bundle.pem       # Custom CA
```

---

## Response-Zeit prüfen

Prüfen ob die API innerhalb akzeptabler Zeit antwortet:

```robot
RESTSendRequest        GET
RESTVerifyResponseTime    500      # Antwort muss unter 500ms sein
RESTVerifyResponseTime    $IGNORE  # Prüfung überspringen
```

---

## Request/Response Logging

`RESTSendRequest` protokolliert Request und Response automatisch mit
vollständigen Headers und formatiertem Body im Robot-Log. Sensible Felder
(`password`, `token`, `secret`) werden im Request-Body mit `***` maskiert.
Headers werden im Klartext geloggt für maximale Beobachtbarkeit.

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
      Set-Cookie: accessToken=eyJ...; Path=/; HttpOnly
    Response Body:
{
  "accessToken": "eyJ...",
  "username": "emilys"
}
```

---

## Retry bei Fehler

Automatische Wiederholung bei transienten HTTP-Fehlern (429, 502, 503, etc.).
Im YAML konfiguriert — der Testcode bleibt unverändert.

```yaml
MeineAPI:
  __self__:
    base_url: https://api.example.com
    content_type: application/json
    retry_count: 3
    retry_delay: 1000
    retry_on: 429,502,503
```

| Einstellung | Standard | Beschreibung |
|---|---|---|
| `retry_count` | 0 (aus) | Maximale Anzahl Wiederholungen |
| `retry_delay` | 1000 | Wartezeit zwischen Versuchen in Millisekunden |
| `retry_on` | (keine) | Status-Codes die einen Retry auslösen |

---

## Vollständiges Beispiel: Login + CRUD

```robot
*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Login Und Note Erstellen
    RESTStart              NotesAPI

    # Login
    RESTSelectEndpoint     /users/login
    RESTSetValue           email        user@example.com
    RESTSetValue           password     Secret123!
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTMemorizeValue      data.token   TOKEN

    # Note anlegen
    RESTSelectEndpoint     /notes
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           title        Meine Notiz
    RESTSetValue           description  Erstellt durch OKW
    RESTSetValue           category     Work
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTMemorizeValue      data.id      NOTE_ID

    # Note löschen
    RESTSelectEndpoint     /notes/$MEM{NOTE_ID}
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSendRequest        DELETE
    RESTVerifyStatus       200

    RESTStop
```

---

## KI-Testgenerierung

Testfälle können mit jeder KI (Claude, ChatGPT, Copilot, ...) generiert werden.
Die System-Prompts für die Testgenerierung werden zentral in
[`robotframework-okw4robot/prompts/`](https://github.com/Hrabovszki1023/robotframework-okw4robot/tree/main/prompts) gepflegt.

---

## Lauffähige Beispiele

[okw-examples/rest-api/](https://github.com/Hrabovszki1023/okw-examples/tree/main/rest-api/) — Health Check, CRUD, Authentifizierung, Tokens.

## Handbuch

[OKW4Robot Handbuch](https://hrabovszki1023.github.io/okw-examples/) — Schritt-für-Schritt-Anleitung.

## Dokumentation

- [Keyword-Spezifikation](https://github.com/Hrabovszki1023/robotframework-okw-api-rest/blob/main/docs/rest-keywords.md) — vollständige Keyword-Referenz
- [Keyword-API (libdoc)](https://hrabovszki1023.github.io/robotframework-okw-api-rest/OkwApiRestLibrary.html) — automatisch generiert aus Docstrings

## Lizenz

- **Community** (nicht-kommerziell): siehe [LICENSE](LICENSE)
- **Kommerziell**: Kontakt über den Rechteinhaber
