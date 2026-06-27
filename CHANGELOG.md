# Changelog

All notable changes to this project will be documented in this file.

## [0.1.3] - 2026-06-24

### CI/CD
- Add Stage 2 release workflow (TestPyPI upload on `v*` tag)

### Docs
- Add REST test generator prompt (`prompts/okw-rest-test-generator.md`)
- Add AI Test Generation section to libdoc class docstring
- Add okw-examples link to libdoc docstring

## [0.1.2] - 2026-06-22

### CI/CD
- Add libdoc GitHub Pages workflow for auto-generated keyword docs
- Update GitHub Actions to Node.js 24 compatible versions

### Docs
- Add Libdoc link to README header

## [0.1.1] - 2026-06-22

### Fixes
- Fix relative links for PyPI rendering

## [0.1.0] - 2026-06-22

### Highlights
- Initial release: 20 keywords for REST API test automation
- Full phase model: Start → Scope → Input → Action → Verify → Memorize → Stop

### Features
- `RESTStart` / `RESTStop` — session management
- `RESTSelectEndpoint` / `RESTSetContext` — scope targeting
- `RESTSetValue`, `RESTSetValueAsString`, `RESTSetValueAsList` — input with auto type detection
- `RESTSetFile` — multipart file upload with MIME detection
- `RESTSetHeader` — custom request headers
- `RESTSendRequest` — GET, POST, PUT, PATCH, DELETE
- `RESTVerifyStatus`, `RESTVerifyValue`, `RESTVerifyResponseTime`,
  `RESTVerifyListCount` — response verification (EXACT/WCM/REGX)
- `RESTMemorizeValue`, `RESTMemorizeBody` — store values for `$MEM{KEY}` expansion
- `RESTSaveResponseToFile` — save response body to file
- Automatic retry on transient HTTP errors (YAML configurable)
- OAuth 2.0 Client Credentials flow (YAML configurable)
- Cookie handling via `requests.Session`
- Full request/response header logging in Robot log
- Environment config, authentication, and SSL support via YAML
- Capture-to-Robot converter for browser API captures

### Docs
- CONTRACT.md with public API contract
- CLAUDE.md with Cheatography format contract
- Playwright vs OKW REST comparison
- README (EN/DE) with full keyword reference
- AGPL-3.0 license
