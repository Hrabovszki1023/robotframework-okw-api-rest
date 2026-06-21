*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
CRUD Operationen Auf Posts
    [Documentation]    CRUD = Create Read Update Delete.
    ...                Testet alle vier Grundoperationen auf Posts:
    ...                POST (anlegen), GET (lesen), PUT/PATCH (aendern), DELETE (loeschen).
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
