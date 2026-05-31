*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Request Mit Retry Konfiguration
    [Documentation]    Verifies retry config is loaded and normal requests work.
    ...                Retry triggers only on 429/503 — this request returns 200.
    RESTStart              DummyJSON_retry

    RESTSelectEndpoint     /todos
    RESTSetValue           ?limit    1
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyListCount    todos     1

    RESTStop
