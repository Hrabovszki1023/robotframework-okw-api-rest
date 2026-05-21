*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Login Mit Gueltigem Benutzer
    RESTStart              DummyJSON

    RESTSelectEndpoint     /auth/login
    RESTSetValue           username        emilys
    RESTSetValue           password        emilyspass
    RESTSetValue           expiresInMins   30
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValue        username        emilys
    RESTVerifyValue        email           emily.johnson@x.dummyjson.com
    RESTVerifyValue        firstName       Emily
    RESTVerifyValue        lastName        Johnson

    RESTMemorizeValue      accessToken     TOKEN

    RESTStop

Authentifizierter Zugriff Auf Profil
    RESTStart              DummyJSON

    # Login
    RESTSelectEndpoint     /auth/login
    RESTSetValue           username        emilys
    RESTSetValue           password        emilyspass
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTMemorizeValue      accessToken     TOKEN

    # Profil abrufen mit Bearer Token
    RESTSelectEndpoint     /auth/me
    RESTSetHeader          Authorization   Bearer $MEM{TOKEN}
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        username        emilys
    RESTVerifyValue        firstName       Emily
    RESTVerifyValue        role            admin

    RESTStop

Zugriff Ohne Token Wird Abgelehnt
    RESTStart              DummyJSON

    RESTSelectEndpoint     /auth/me
    RESTSendRequest        GET

    RESTVerifyStatus       401
    RESTVerifyValue        message         Access Token is required

    RESTStop

Todo Erstellen
    RESTStart              DummyJSON

    RESTSelectEndpoint     /todos/add
    RESTSetValue           todo            OKW REST Test
    RESTSetValue           completed       false
    RESTSetValue           userId          1
    RESTSendRequest        POST

    RESTVerifyStatus       201
    RESTVerifyValue        todo            OKW REST Test
    RESTVerifyValue        userId          1

    RESTStop

Todos Mit Query Parameter Abrufen
    RESTStart              DummyJSON

    RESTSelectEndpoint     /todos
    RESTSetValue           ?limit          3
    RESTSetValue           ?skip           0
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        limit           3
    RESTVerifyValue        total           254

    RESTStop

Token Refresh
    RESTStart              DummyJSON

    # Login
    RESTSelectEndpoint     /auth/login
    RESTSetValue           username        emilys
    RESTSetValue           password        emilyspass
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTMemorizeValue      refreshToken    REFRESH

    # Token erneuern
    RESTSelectEndpoint     /auth/refresh
    RESTSetValue           refreshToken    $MEM{REFRESH}
    RESTSetValue           expiresInMins   30
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValueREGX    accessToken     ^eyJ.+
    RESTVerifyValueREGX    refreshToken    ^eyJ.+

    RESTStop
