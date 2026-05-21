# Reference: WebService Keywords (TAMARA)

Source: Internal TAMARA framework documentation.
Purpose: Inspiration for OKW API REST adapter keyword design.

---

## Overview

The TAMARA framework provides keyword-driven web service testing for
SOAP, REST, and Kafka. All keywords follow a consistent pattern:

| Phase | Keyword | Purpose |
|---|---|---|
| 1. Select | `Wähle Service Operation` | Choose service + operation/resource |
| 2. Input | `Setze Service Eingabe` | Set request data (fields, elements) |
| 2b. Context | `Beende Service Eingabe` | End nested context (SOAP only) |
| 3. Send | `Sende Service Eingabe` | Execute the request |
| 4. Navigate | `Wähle Service Ausgabe` | Navigate response structure |
| 5. Verify | `Prüfe Service Ausgabe` | Verify response values |
| 5b. Store | `Merke Service Ausgabe` | Memorize response values |

Additional (Kafka only):
- `Abonniere Service Ausgabe` — Subscribe to topics
- `Hole Service Ausgabe` — Fetch messages

---

## 1. Wähle Service Operation (Select Service Operation)

Selects a service and its operation/resource.

### SOAP

```
Wähle Service Operation: "Kundenservice" = "sucheKunde"
```

### REST

HTTP method is encoded in angle brackets before the resource path:

```
Wähle Service Operation: "Kundenservice" = "<GET>kunde"
Wähle Service Operation: "Kundenservice" = "<GET>kunde/1"
Wähle Service Operation: "Kundenservice" = "<POST>kunde"
Wähle Service Operation: "Kundenservice" = "<PUT>kunde/1"
Wähle Service Operation: "Kundenservice" = "<DELETE>kunde/1"
```

### Kafka

```
Wähle Service Operation: "KafkaService" = "TopicTest"
```

---

## 2. Setze Service Eingabe (Set Service Input)

Sets request data. Behavior differs by service type.

### SOAP — Simple value

```
Setze Service Eingabe: "Name" = "Meier"
Setze Service Eingabe: "Vorname" = "Hans"
```

### SOAP — Complex element (context navigation)

`ELEMENT` navigates into a nested XML structure:

```
Setze Service Eingabe: "ELEMENT" = "ANFRAGE"
Setze Service Eingabe: "ELEMENT" = "kunde"
Setze Service Eingabe: "ELEMENT" = "adresse"
Setze Service Eingabe: "ort" = "Nürnberg"
Setze Service Eingabe: "plz" = "90449"
Setze Service Eingabe: "strasse" = "Südwestpark 50"
Beende Service Eingabe: "ELEMENT" = "adresse"
```

`Beende Service Eingabe` pops back to the parent element.

### REST — Form data

```
Setze Service Eingabe: "name" = "Meier"
Setze Service Eingabe: "vorname" = "Hans"
```

### REST — File upload

```
Setze Service Eingabe: "datei#DATEI" = "C:\Temp\upload.pdf"
Setze Service Eingabe: "datei#DATEI#BASE64" = "C:\Temp\upload.pdf"
```

### Kafka — Key-value messages

```
Setze Service Eingabe: "Schlüssel1" = "Wert1"
```

---

## 3. Sende Service Eingabe (Send Service Input)

Sends the prepared request to the service.

```
Sende Service Eingabe: "KONFIGURATION" = "STANDARD"
```

The `KONFIGURATION` parameter references a named configuration
(connection settings, timeouts, auth, etc.) defined in the test
object list.

---

## 4. Wähle Service Ausgabe (Select Service Output)

Navigates the response structure to set the context for
subsequent verify/memorize keywords.

### SOAP — Navigate response elements

```
Wähle Service Ausgabe: "ELEMENT" = "ANTWORT"
Wähle Service Ausgabe: "ELEMENT" = "kunde"
```

### SOAP — Select by content

```
Wähle Service Ausgabe: "kunde" = "id<IST>1"
```

### REST — Navigate JSON response

```
Wähle Service Ausgabe: "ELEMENT" = "ANTWORT"
Wähle Service Ausgabe: "OBJEKT" = "Kunde"
Wähle Service Ausgabe: "ARRAY" = "Kinder"
Wähle Service Ausgabe: "OBJEKT#POSITION" = "1"
Wähle Service Ausgabe: "OBJEKT#INHALT" = "name<IST>Meier"
```

Same navigation model as `Wähle JSON` (see reference-json-keywords.md).

---

## 5. Prüfe Service Ausgabe (Verify Service Output)

### Simple value check (SOAP + REST)

```
Prüfe Service Ausgabe: "vorname" = "Hans"
Prüfe Service Ausgabe: "vorname" = "H*"          // Wildcard
```

### HTTP status code (REST only)

```
Prüfe Service Ausgabe: "HTTPSTATUSCODE" = "200"
Prüfe Service Ausgabe: "HTTPSTATUSCODE" = "201"
Prüfe Service Ausgabe: "HTTPSTATUSCODE" = "404"
```

### HTTP header (REST only)

```
Prüfe Service Ausgabe: "Content-Type#HTTPHEADER" = "text/html; charset=utf-8"
```

### Key existence (REST/JSON only)

```
Prüfe Service Ausgabe: "Name#VORHANDEN" = "JA"
```

### Type + value (REST/JSON only)

```
Prüfe Service Ausgabe: "Name#TYP:String" = "Meier"
Prüfe Service Ausgabe: "Alter#TYP:Zahl" = "29"
Prüfe Service Ausgabe: "verheiratet#TYP:Boolean" = "true"
```

### Array count (REST/JSON only)

```
Prüfe Service Ausgabe: "ANZAHL" = "2"
Prüfe Service Ausgabe: "ANZAHL:1" = "Max"
```

### Object search in array (REST/JSON only)

```
Prüfe Service Ausgabe: "OBJEKT#ANZAHL:1" = "vorname<IST>Peter"
Prüfe Service Ausgabe: "OBJEKT#ANZAHL:1" = "adresse<MIT>ort<IST>Nürnberg"
```

### File comparison (REST + SOAP)

```
Prüfe Service Ausgabe: "DATEI" = "%AUTOMATISIERUNG%/Referenzdaten/Kunde.json"
```

### SOAP-specific: Node count

```
Prüfe Service Ausgabe: "kunde#ANZAHL" = "2"
Prüfe Service Ausgabe: "kind#ANZAHL:1" = "Max"
Prüfe Service Ausgabe: "kind#LISTE" = "<LEER><UND>Max<UND>Max<UND>Moritz"
Prüfe Service Ausgabe: "kind#LISTE#REIHENFOLGE" = "Max<UND>Moritz<UND>Max<UND><LEER>"
```

---

## 5b. Merke Service Ausgabe (Memorize Service Output)

### REST — Memorize HTTP body

```
Merke Service Ausgabe: "BODY" = "gemerkterWert"
```

Stores the entire HTTP response body.

### REST — Memorize HTTP header

```
Merke Service Ausgabe: "Content-Type#HTTPHEADER" = "gemerkterWert"
```

### SOAP — Memorize node value

```
Merke Service Ausgabe: "name" = "gemerkterWert"
```

Access stored values via `<HOLEWERT=gemerkterWert>` (equivalent to OKW's `$MEM{gemerkterWert}`).

---

## Complete REST Example

```
// 1. Select service + HTTP method + resource
Wähle Service Operation: "Kundenservice" = "<GET>kunde/1"

// 2. Send request (no input data for GET)
Sende Service Eingabe: "KONFIGURATION" = "STANDARD"

// 3. Verify status
Prüfe Service Ausgabe: "HTTPSTATUSCODE" = "200"

// 4. Navigate response
Wähle Service Ausgabe: "ELEMENT" = "ANTWORT"
Wähle Service Ausgabe: "OBJEKT" = "Kunde"

// 5. Verify values
Prüfe Service Ausgabe: "Name" = "Meier"
Prüfe Service Ausgabe: "Vorname" = "Hans"

// 6. Memorize for later use
Merke Service Ausgabe: "BODY" = "kundeJson"
```

## Complete SOAP Example

```
// 1. Select service + operation
Wähle Service Operation: "Kundenservice" = "sucheKunde"

// 2. Build request (nested XML)
Setze Service Eingabe: "ELEMENT" = "ANFRAGE"
Setze Service Eingabe: "ELEMENT" = "kunde"
Setze Service Eingabe: "Name" = "Meier"
Setze Service Eingabe: "Vorname" = "Hans"

// 3. Send
Sende Service Eingabe: "KONFIGURATION" = "STANDARD"

// 4. Navigate response
Wähle Service Ausgabe: "ELEMENT" = "ANTWORT"
Wähle Service Ausgabe: "ELEMENT" = "kunde"

// 5. Verify
Prüfe Service Ausgabe: "name" = "Meier"
Prüfe Service Ausgabe: "kunde#ANZAHL" = "2"

// 6. Memorize
Merke Service Ausgabe: "name" = "gemerkterWert"
```

---

## OKW Keyword Naming Convention

All technology-specific keywords use the technology name as **prefix**.
This ensures alphabetical grouping in keyword lists, libdoc, and
autocomplete:

```
REST...          KAFKA...          SOAP...
RESTStart        KAFKAStart        SOAPStart
RESTStop         KAFKAStop         SOAPStop
RESTSelect...    KAFKASelect...    SOAPSelect...
RESTSet...       KAFKASet...       SOAPSet...
RESTSend...      KAFKAProduce      SOAPSend...
RESTVerify...    KAFKAVerify...    SOAPVerify...
RESTMemorize...  KAFKAMemorize...  SOAPMemorize...
```

---

## OKW REST Keywords (Final)

| Keyword | Description |
|---|---|
| `RESTStart` | Start REST service (load YAML, base URL) |
| `RESTStop` | Stop REST service |
| `RESTSelectEndpoint` | Select endpoint (e.g. `/users/register`) |
| `RESTSetValue` | Set request field |
| `RESTSetContext` | Navigate into nested object |
| `RESTSetHeader` | Set request header |
| `RESTSendRequest` | Send HTTP request (POST, GET, PUT, DELETE) |
| `RESTVerifyValue` | Verify response field value |
| `RESTVerifyStatus` | Verify HTTP status code |
| `RESTVerifyHeader` | Verify response header |
| `RESTMemorizeValue` | Store response field value |
| `RESTMemorizeBody` | Store entire response body |

### Alphabetical listing (as shown in libdoc/autocomplete)

```
RESTMemorizeBody
RESTMemorizeValue
RESTSelectEndpoint
RESTSendRequest
RESTSetContext
RESTSetHeader
RESTSetValue
RESTStart
RESTStop
RESTVerifyHeader
RESTVerifyStatus
RESTVerifyValue
```

---

## Mapping TAMARA → OKW

| TAMARA Keyword | OKW Keyword | Notes |
|---|---|---|
| `Wähle Service Operation` | `RESTSelectEndpoint` | Endpoint path as parameter |
| `Setze Service Eingabe` | `RESTSetValue` | Flat key-value for request body |
| `Setze Service Eingabe: "ELEMENT"` | `RESTSetContext` | Navigate nested JSON structures |
| `Beende Service Eingabe: "ELEMENT"` | — | Not needed (flat context, no stack) |
| `Sende Service Eingabe` | `RESTSendRequest` | HTTP method as parameter (POST, GET, ...) |
| `Wähle Service Ausgabe: "ELEMENT"` | `RESTSetContext` | Navigate response JSON |
| `Wähle Service Ausgabe: "OBJEKT"` | `RESTSetContext` | Navigate response JSON |
| `Prüfe Service Ausgabe` | `RESTVerifyValue` | Verify response field |
| `Prüfe Service Ausgabe: "HTTPSTATUSCODE"` | `RESTVerifyStatus` | Verify HTTP status code |
| `Prüfe Service Ausgabe: "#HTTPHEADER"` | `RESTVerifyHeader` | Verify response header |
| `Prüfe Service Ausgabe: "#VORHANDEN"` | `RESTVerifyValue` | With `YES`/`NO` existence model |
| `Merke Service Ausgabe` | `RESTMemorizeValue` | Store response field |
| `Merke Service Ausgabe: "BODY"` | `RESTMemorizeBody` | Store full response body |
| `Merke Service Ausgabe: "#HTTPHEADER"` | `RESTMemorizeValue` | Header as field path |
| `<HOLEWERT=name>` | `$MEM{name}` | OKW value expansion |
| `<LEER>` | `$EMPTY` | OKW token |
| `<NULL>` | — | New token needed |
| `*`, `?` wildcards | WCM match mode | Already in OKW |

---

## Cross-Technology Phase Model

| Phase | REST | KAFKA | SOAP | GUI |
|---|---|---|---|---|
| Start | `RESTStart` | `KAFKAStart` | `SOAPStart` | `StartApp` |
| Scope | `RESTSelectEndpoint` | `KAFKASelectTopic` | `SOAPSelectOperation` | `SelectWindow` |
| Input | `RESTSetValue` | `KAFKASetValue` | `SOAPSetValue` | `SetValue` |
| Context | `RESTSetContext` | — | `SOAPSetContext` | `SetContext` |
| Action | `RESTSendRequest` | `KAFKAProduce` | `SOAPSendRequest` | `ClickOn` |
| Receive | — | `KAFKAConsume` | — | — |
| Verify | `RESTVerifyValue` | `KAFKAVerifyValue` | `SOAPVerifyValue` | `VerifyValue` |
| Memorize | `RESTMemorizeValue` | `KAFKAMemorizeValue` | `SOAPMemorizeValue` | `MemorizeValue` |
| Stop | `RESTStop` | `KAFKAStop` | `SOAPStop` | `StopApp` |

---

## OKW REST Example: ExpandTesting Notes API

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

API Login Und Note Erstellen
    RESTStart              NotesAPI

    RESTSelectEndpoint     /users/login
    RESTSetValue           email        practice@expandtesting.com
    RESTSetValue           password     NewPassword1!
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTMemorizeValue      data.token   TOKEN

    RESTSelectEndpoint     /notes
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           title        Meine Notiz
    RESTSetValue           description  Inhalt der Notiz
    RESTSetValue           category     Work
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValue        data.title   Meine Notiz

    RESTStop

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

    RESTSendRequest        POST

    RESTVerifyStatus       201
    RESTVerifyValue        data.customer.name   Zoltan

    RESTStop
```
