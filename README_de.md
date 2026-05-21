# robotframework-okw-api-rest

> English version: [README.md](README.md)

Keyword-gesteuertes REST-API-Testing fuer [OKW4Robot](https://github.com/Hrabovszki1023/robotframework-okw4robot).

Ein Satz Keywords deckt den kompletten REST-API-Testlebenszyklus ab:
**Start -> Scope -> Input -> Action -> Verify -> Memorize -> Stop**.

---

## Installation

```bash
pip install robotframework-okw-api-rest
```

Oder editierbar (fuer Entwicklung):

```bash
pip install -e Pfad/zu/robotframework-okw-api-rest
```

### Abhaengigkeiten

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

### 3. Ausfuehren

```bash
robot tests/REST_NotesAPI.robot
```

---

## Keywords

| Keyword | Beschreibung |
|---|---|
| `RESTStart` | REST-Service starten (YAML laden, Basis-URL) |
| `RESTStop` | REST-Service stoppen |
| `RESTSelectEndpoint` | Endpoint-Pfad waehlen |
| `RESTSetValue` | Request-Body-Feld oder Query-Parameter (`?`-Prefix) setzen |
| `RESTSetContext` | In verschachteltes JSON-Objekt navigieren |
| `RESTSetHeader` | Request-Header setzen |
| `RESTSendRequest` | HTTP-Request senden (GET, POST, PUT, PATCH, DELETE) |
| `RESTVerifyValue` | Response-Feldwert pruefen (exakter Vergleich) |
| `RESTVerifyValueWCM` | Response-Feldwert pruefen (Wildcard: `*`, `?`) |
| `RESTVerifyValueREGX` | Response-Feldwert pruefen (regulaerer Ausdruck) |
| `RESTVerifyStatus` | HTTP-Statuscode pruefen |
| `RESTVerifyHeader` | Response-Header pruefen |
| `RESTMemorizeValue` | Response-Feldwert speichern fuer `$MEM{name}` |
| `RESTMemorizeBody` | Gesamten Response-Body speichern |

---

## Phasenmodell

| Phase | REST Keyword | GUI-Aequivalent |
|---|---|---|
| Start | `RESTStart` | `StartApp` |
| Scope | `RESTSelectEndpoint` | `SelectWindow` |
| Eingabe | `RESTSetValue` | `SetValue` |
| Kontext | `RESTSetContext` | `SetContext` |
| Header | `RESTSetHeader` | -- |
| Aktion | `RESTSendRequest` | `ClickOn` |
| Pruefen | `RESTVerifyValue` | `VerifyValue` |
| Status | `RESTVerifyStatus` | -- |
| Merken | `RESTMemorizeValue` | `MemorizeValue` |
| Stop | `RESTStop` | `StopApp` |

---

## OKW-Token

| Token | Verhalten |
|---|---|
| `$IGNORE` | Keyword wird uebersprungen (Feld wird nicht gesendet) |
| `$EMPTY` | Feld wird explizit auf leeren String gesetzt |

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

# Im naechsten Request verwenden
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

Drei Stufen: kein Argument = Default wird gesendet, eigener Wert = ueberschreibt Default, `$IGNORE` = Feld wird nicht gesendet.

---

## Umgebungskonfiguration

Credentials und URLs werden per Environment-Datei vom Service-YAML
getrennt — wie `~/.ssh/` die Keys aus den Projekten heraushalt.

### Service-YAML (sicher fuer Repo)

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

### Suchordnung fuer Env-Dateien

| Prioritaet | Pfad | Zweck |
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

Fuer dynamische Token (Login-Flow) `RESTMemorizeValue` + `RESTSetHeader` verwenden.

---

## SSL / Zertifikate

```yaml
verify_ssl: false                        # Self-signed Certs
client_cert: ~/.okw/certs/client.pem     # mTLS
client_key: ~/.okw/certs/client.key
ca_bundle: ~/.okw/certs/ca-bundle.pem    # Custom CA
```

Pfade unterstuetzen `~` und `$ENV_VAR` Expansion.

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

## Vollstaendiges Beispiel: Login + CRUD

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

    # Note loeschen
    RESTSelectEndpoint     /notes/$MEM{NOTE_ID}
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSendRequest        DELETE
    RESTVerifyStatus       200

    RESTStop
```

---

## Dokumentation

- [Keyword-Spezifikation](docs/rest-keywords.md) -- vollstaendige Keyword-Referenz
- [Keyword-API (libdoc)](docs/OkwApiRestLibrary.html) -- automatisch generiert aus Docstrings

---

## Lizenz

Siehe [LICENSE](LICENSE).
