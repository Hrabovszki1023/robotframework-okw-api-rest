# OKW REST API — Offene Punkte (Stand 2026-06-01)

---

## Typ-System (JSON-Werte)

| # | Umsetzung | Feature | Keyword/Loesung |
|---|---|---|---|
| 1 | Erledigt | Auto-Typ-Erkennung | `RESTSetValue` erkennt int, float, bool automatisch |
| 2 | Erledigt | String erzwingen | `RESTSetValueAsString` (neues Keyword) |
| 3 | Erledigt | Null-Wert | `$NULL` Token in `RESTSetValue` → `null` |
| 4 | Erledigt | Array von Primitiven | `RESTSetValueAsList` + Array-Index `field[0]` |
| 5 | Erledigt | Leeres Array | `RESTSetValueAsList field` (ohne Werte) → `[]` |
| 6 | Zurueckgestellt | Leeres Object | `$EMPTY_OBJECT` Token → `{}` — kein realer Anwendungsfall bisher |

---

## Keywords (Postman-Vergleich)

| # | Umsetzung | Feature | Keyword/Loesung |
|---|---|---|---|
| 7 | Erledigt | Array-Laenge pruefen | `RESTVerifyListCount field count` |
| 8 | Erledigt | Retry bei Fehler | YAML-Config: `retry_count`, `retry_delay`, `retry_on` |
| 9 | Klaerung | Cookie-Handling | Cookie-Jar ueber Requests hinweg (Session-APIs wie AQUA). Manche APIs senden Session nur als `Set-Cookie` Header, nicht im JSON-Body. Optionen: (A) `RESTMemorizeHeader`, (B) automatischer Cookie-Jar via `requests.Session` |
| 10 | Erledigt | File Upload | `RESTSetFile` — Multipart Form-Data, Auto-MIME, Mehrfach-Upload |
| 11 | Offen | OAuth 2.0 Flow | Auth-Type in YAML |

---

## Capture-Konverter (okw-capture-rest2robot)

| # | Umsetzung | Feature | Details |
|---|---|---|---|
| 12 | Erledigt | Domain-Filter (`--domain`) | Fertig, lokal, nicht committed |
| 13 | Erledigt | Ein Capture = ein Testfall | Fertig, lokal, nicht committed |
| 14 | Offen | Cache-Buster `?_=` rausfiltern | Timestamp-Query-Parameter entfernen |
| 15 | Offen | Wiederholende Header zusammenfassen | z.B. `X-Api-Client` in YAML statt pro Step |
| 16 | Erledigt | Testname-Parameter (`--testname`) | Fertig, lokal, nicht committed |
| 17 | Klaerung | Chrome Capture Plugin | Noch nicht ausprobiert, Quelle/Format unklar |

---

## Dokumentation

| # | Umsetzung | Feature | Details |
|---|---|---|---|
| 18 | Erledigt | REST-Keywords.md | Alle 18 Keywords + Token-Tabelle + Retry + Arrays |
| 19 | Erledigt | README (EN/DE) | Alle Abschnitte aktuell |
| 20 | Erledigt | Libdoc regenerieren | HTML + JSON mit allen 18 Keywords |
| 21 | Erledigt | AI-Prompt aktualisieren | Typ-Erkennung, Arrays, Retry, ListCount |
| 22 | Erledigt | Capture-Workflow Doku | docs/capture-workflow.md, lokal, nicht committed |
| 23 | Erledigt | Contract-Pruefung | Alle Dateien konsistent: Keywords, Tokens, Phasenmodell |

---

## Bewusst draussen

| Feature | Begruendung |
|---|---|
| Pre-Request Scripts | Widerspricht OKW-Prinzip: deklarativ, kein Code im Test |
| JSON-Block-Eingabe | Fehleranfaellig, OKW loest das ueber Name+Wert |
| GraphQL / SOAP / WebSocket / gRPC | Jeweils eigene Libraries |
| Mock Server | Gehoert nicht in die Test-Library |
