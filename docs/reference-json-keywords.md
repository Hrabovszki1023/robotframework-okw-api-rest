# Reference: JSON Keywords (TAMARA)

Source: Internal TAMARA framework documentation.
Purpose: Inspiration for OKW API REST adapter keyword design.

---

## Overview

Three JSON keyword groups for navigating, verifying, and memorizing
values in JSON documents. All keywords operate on a **context model** —
a selected JSON element that subsequent keywords refer to.

| Keyword | Purpose |
|---|---|
| `Wähle JSON` | Select/navigate to a JSON element (set context) |
| `Prüfe JSON` | Verify a JSON value or structure |
| `Merke JSON` | Memorize a JSON value for later use |

---

## Wähle JSON (Select JSON)

Selects a JSON document or navigates to a sub-element.
All subsequent JSON keywords operate on the selected context.

### DOKUMENT — Load a JSON document

```
Wähle JSON: "DOKUMENT" = "<HOLEWERT=jsonDokument>"
```

Load a JSON string as the active document. Root element is selected.

### DOKUMENT — Back to root

```
Wähle JSON: "DOKUMENT" = "WURZEL"
```

Reset context to the root of the current document.

### DOKUMENT#DATEI — Load from file

```
Wähle JSON: "DOKUMENT#DATEI" = "%AUTOMATISIERUNG%/Testdaten/Beispieldatei.json"
```

### OBJEKT — Select object by key

```
Wähle JSON: "OBJEKT" = "Kunde"
```

Selects the object at key `Kunde` in the current context.

```json
{
    "Kunde": {        // <- selected
        "Name": "Meier",
        "Vorname": "Hans"
    },
    "Kinder": ["Max", "Moritz"]
}
```

### OBJEKT#POSITION — Select object in array by position

```
Wähle JSON: "ARRAY" = "Kinder"
Wähle JSON: "OBJEKT#POSITION" = "1"
```

Position is **1-based**.

### OBJEKT#INHALT — Select object in array by content

```
Wähle JSON: "OBJEKT#INHALT" = "name<IST>Meier"
Wähle JSON: "OBJEKT#INHALT" = "adresse<MIT>ort<IST>Nürnberg<UND>plz<IST>90478"
```

Content query DSL:
- `key<IST>value` — key-value pair match
- `<UND>` — AND multiple pairs
- `<MIT>` — descend into sub-object
- `<NULL>`, `<LEER>`, `<OBJEKT>`, `<ARRAY>` — special value matchers
- Wildcards `*`, `?` supported

### ARRAY — Select array by key

```
Wähle JSON: "ARRAY" = "Kinder"
```

### ARRAY#POSITION — Select array in array by position

```
Wähle JSON: "ARRAY" = "Kinder"
Wähle JSON: "ARRAY#POSITION" = "1"
```

### Full navigation example

```
Wähle JSON: "DOKUMENT" = "{'Kunde':{'Name':'Meier'},'Auftrag':{'Auftragsnummer':1234}}"

Wähle JSON: "OBJEKT" = "Kunde"
Prüfe JSON: "Name" = "Meier"

Wähle JSON: "DOKUMENT" = "WURZEL"

Wähle JSON: "OBJEKT" = "Auftrag"
Prüfe JSON: "Auftragsnummer" = "1234"
```

---

## Prüfe JSON (Verify JSON)

### Basic value check

```
Prüfe JSON: "Name" = "Meier"
Prüfe JSON: "Vorname" = "H*"           // Wildcard
Prüfe JSON: "Geburtstag" = "<LEER>"    // Empty string
Prüfe JSON: "Adresse" = "<OBJEKT>"     // Is an object
Prüfe JSON: "Kontakt" = "<LEERESOBJEKT>"
Prüfe JSON: "Hobbies" = "<ARRAY>"      // Is an array
Prüfe JSON: "Kinder" = "<LEERESARRAY>"
```

Example JSON:

```json
{
    "Name": "Meier",
    "Vorname": "Hans",
    "Geburtstag": "",
    "Adresse": { "Strasse": "Musterstr. 10", "Plz": "12345", "Ort": "Musterort" },
    "Kontakt": {},
    "Hobbies": ["Lesen", "Sport"],
    "Kinder": []
}
```

### Type + value check

```
Prüfe JSON: "Name#TYP:String" = "Meier"
Prüfe JSON: "Alter#TYP:Zahl" = "29"
Prüfe JSON: "verheiratet#TYP:Boolean" = "true"
Prüfe JSON: "Beruf#TYP:String" = "<LEER>"
```

Types: `String`, `Zahl` (Number), `Boolean`.

### Key existence check

```
Prüfe JSON: "Kunde#VORHANDEN" = "JA"
Prüfe JSON: "Adresse#VORHANDEN" = "NEIN"
```

### ANZAHL — Array element count

```
Prüfe JSON: "ANZAHL" = "3"
```

Prerequisite: current context must be an array.

### ANZAHL:n — Count matching elements

```
Prüfe JSON: "ANZAHL:2" = "Hans"       // 2 elements equal "Hans"
Prüfe JSON: "ANZAHL:2" = "*a*"        // 2 elements match wildcard
Prüfe JSON: "ANZAHL:2" = "<LEER>"     // 2 empty strings
```

### OBJEKT#ANZAHL:n — Count objects with content

```
Prüfe JSON: "OBJEKT#ANZAHL:2" = "name<IST>Meier"
Prüfe JSON: "OBJEKT#ANZAHL:1" = "adresse<MIT>ort<IST>Nürnberg<UND>plz<IST>90478"
Prüfe JSON: "OBJEKT#ANZAHL:1" = "kontodaten<IST><LEERESOBJEKT>"
```

Example JSON (array of objects):

```json
[
    {
        "name": "Meier",
        "vorname": "Hans",
        "adresse": { "ort": "Nürnberg", "plz": "90478" },
        "kontodaten": {}
    },
    {
        "name": "Meier",
        "vorname": "Horst",
        "kontodaten": { "kontonummer": "1234567890" }
    }
]
```

---

## Merke JSON (Memorize JSON)

### Memorize a value

```
Merke JSON: "Name" = "GemerkterName"
```

Stores the value of key `Name` under symbolic name `GemerkterName`.
Access later via `<HOLEWERT=GemerkterName>` (equivalent to OKW's `$MEM{GemerkterName}`).

### ANZAHL — Memorize array count

```
Merke JSON: "ANZAHL" = "GemerkteAnzahl"
```

Stores the number of elements in the current array context.

---

## Content Query DSL Summary

Used in `OBJEKT#INHALT`, `OBJEKT#ANZAHL:n`, and similar keywords:

| Token | Meaning | Example |
|---|---|---|
| `<IST>` | Key-value separator | `name<IST>Meier` |
| `<UND>` | AND combinator | `name<IST>Meier<UND>vorname<IST>Hans` |
| `<MIT>` | Descend into sub-object | `adresse<MIT>ort<IST>Berlin` |
| `<NULL>` | JSON null | `wert<IST><NULL>` |
| `<LEER>` | Empty string `""` | `wert<IST><LEER>` |
| `<OBJEKT>` | Non-empty object | `wert<IST><OBJEKT>` |
| `<LEERESOBJEKT>` | Empty object `{}` | `wert<IST><LEERESOBJEKT>` |
| `<ARRAY>` | Non-empty array | `wert<IST><ARRAY>` |
| `<LEERESARRAY>` | Empty array `[]` | `wert<IST><LEERESARRAY>` |
| `*`, `?` | Wildcards | `name<IST>Me?er` |
