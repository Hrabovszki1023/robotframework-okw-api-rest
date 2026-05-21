*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Gesundheitscheck Der API
    RESTStart              NotesAPI

    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        message      Notes API is Running

    RESTStop

Fehlende Authentifizierung
    RESTStart              NotesAPI

    RESTSelectEndpoint     /notes
    RESTSendRequest        GET

    RESTVerifyStatus       401
    RESTVerifyValueWCM     message      *authentication token*

    RESTStop

Fehlender Pflichtfeld Bei Registrierung
    RESTStart              NotesAPI

    RESTSelectEndpoint     /users/register
    RESTSetValue           name         Zoltan
    RESTSendRequest        POST

    RESTVerifyStatus       400
    RESTVerifyValue        success      False

    RESTStop

Verify Mit Wildcard
    RESTStart              NotesAPI

    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValueWCM     message      *API*Running*

    RESTStop

Verify Mit Regex
    RESTStart              NotesAPI

    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValueREGX    status       ^\\d+$

    RESTStop
