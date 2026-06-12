*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
OAuth2 Client Credentials Token Holen
    [Documentation]    RESTStart holt automatisch einen OAuth2 Token via Client Credentials
    RESTStart              OAuth2Demo
    RESTSelectEndpoint     /api/test
    RESTSendRequest        GET
    RESTStop

OAuth2 Token Fehler Bei Falschem Server
    [Documentation]    OAuth2 meldet Fehler wenn Token-Server nicht erreichbar
    ${status}=    Run Keyword And Return Status
    ...    RESTStart    OAuth2Test
    Should Be Equal    ${status}    ${FALSE}
    [Teardown]    Run Keyword And Ignore Error    RESTStop
