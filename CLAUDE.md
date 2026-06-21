# CLAUDE.md – robotframework-okw-api-rest

This file is loaded automatically by Claude Code for this repository.
The global `D:/work/okw/CLAUDE.md` applies in addition.

---

## Cheatography Cheat Sheet

Each OKW library has a Quick Reference Cheat Sheet on Cheatography
(e.g. `robotframework-okw-api-rest`). When keywords or features are
added, the cheat sheet must be updated manually on the website.

**URL:** `https://cheatography.com/openkeyword/`

### Cheatography Format

The editor uses a block-based layout. Each block has:
- A **title** (e.g. `Input`, `Verify`, `Retry`)
- Multiple **entries**, each with a keyword/label and a description

**Formatting rules for descriptions:**
- `{{nl}}` — forced line break (newline)
- `**text**` — bold text
- No Markdown headings, no HTML, no code blocks
- Each description is entered as a single continuous text field

**Example entry:**

```
Keyword:     RESTSetValueAsString field value
Description: Always send the value as a string (no auto-conversion). {{nl}} **Example:**{{nl}}RESTSetValueAsString  zipcode  01234  # -> "01234"{{nl}}RESTSetValueAsString  flag  true  # -> "true"
```

**Block note:** Free text at the bottom of a block (no keyword column).
Used for explanations that apply to the whole block.

### Block Structure (REST API)

| Block | Content |
|---|---|
| Setup | Install, import, requirements |
| Start / Stop | RESTStart, RESTStop |
| Scope | RESTSelectEndpoint, RESTSetContext |
| Input | RESTSetValue, RESTSetValueAsString, RESTSetValueAsList, RESTSetFile, RESTSetHeader |
| Action | RESTSendRequest (GET, POST, PUT, PATCH, DELETE) |
| Auto Type Detection | Type conversion rules |
| Verify | RESTVerifyStatus, RESTVerifyValue, WCM, REGX, Header, ResponseTime, ListCount |
| Memorize | RESTMemorizeValue, RESTMemorizeBody, $MEM{} |
| Save | RESTSaveResponseToFile |
| Tokens | $IGNORE, $EMPTY, $MEM{KEY}, $NULL |
| Arrays | RESTSetValueAsList, index syntax, RESTVerifyListCount |
| File Upload | RESTSetFile, multipart, MIME detection |
| Retry | YAML config: retry_count, retry_delay, retry_on |
| OAuth 2.0 | YAML config: auth_type, token_url, client_id/secret |
| Cookie Handling | Automatic via requests.Session |
| Header Logging | Cleartext request/response headers in Robot log |
| Phase Model | All phases with keywords |
| vs. Playwright | Side-by-side comparison |
| YAML Config | Basic, env files, authentication, SSL |

### Workflow

1. Add/change keywords or features in the library
2. Update all documentation (README, rest-keywords.md, AI prompt, libdoc)
3. Generate a `docs/cheatsheet-update-vorlage.txt` with the missing
   content in Cheatography format ({{nl}}, **bold**)
4. Copy entries from the template into the Cheatography editor
5. Delete the template file after updating (not committed to repo)

**Language:** English (cheat sheet is public-facing).
