*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI
Library    String

Suite Setup       Erzeuge Testbenutzer
Suite Teardown    Loesche Testbenutzer

*** Variables ***
${SERVICE}    NotesAPI

*** Test Cases ***
Login Erfolgreich
    RESTSelectEndpoint     /users/login
    RESTSetValue           email        ${EMAIL}
    RESTSetValue           password     ${PASSWORD}
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValue        message      Login successful
    RESTVerifyValue        data.name    OKWIntTest
    RESTVerifyValue        data.email   ${EMAIL}
    RESTMemorizeValue      data.token   TOKEN

Note Erstellen Und Pruefen
    [Setup]    Login Ausfuehren

    RESTSelectEndpoint     /notes
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           title        OKW Testnotiz
    RESTSetValue           description  Erstellt durch REST Integration Test
    RESTSetValue           category     Work
    RESTSendRequest        POST

    RESTVerifyStatus       200
    RESTVerifyValue        message      Note successfully created
    RESTVerifyValue        data.title   OKW Testnotiz
    RESTVerifyValueWCM     data.description    *Integration*
    RESTMemorizeValue      data.id      NOTE_ID

Note Lesen
    [Setup]    Login Ausfuehren

    RESTSelectEndpoint     /notes/$MEM{NOTE_ID}
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        data.title       OKW Testnotiz
    RESTVerifyValue        data.category    Work

Note Aktualisieren
    [Setup]    Login Ausfuehren

    RESTSelectEndpoint     /notes/$MEM{NOTE_ID}
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSetValue           title        Aktualisierte Notiz
    RESTSetValue           description  Aktualisierte Beschreibung
    RESTSetValue           category     Personal
    RESTSetValue           completed    false
    RESTSendRequest        PUT

    RESTVerifyStatus       200
    RESTVerifyValue        data.title       Aktualisierte Notiz
    RESTVerifyValue        data.category    Personal

Note Loeschen
    [Setup]    Login Ausfuehren

    RESTSelectEndpoint     /notes/$MEM{NOTE_ID}
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSendRequest        DELETE

    RESTVerifyStatus       200
    RESTVerifyValue        message      Note successfully deleted

*** Keywords ***
Erzeuge Testbenutzer
    ${random}=    Generate Random String    8    [LOWER][NUMBERS]
    ${email}=     Set Variable    okwint_${random}@test.com
    Set Suite Variable    ${EMAIL}       ${email}
    Set Suite Variable    ${PASSWORD}    Test1234!

    RESTStart              ${SERVICE}

    RESTSelectEndpoint     /users/register
    RESTSetValue           name         OKWIntTest
    RESTSetValue           email        ${EMAIL}
    RESTSetValue           password     ${PASSWORD}
    RESTSendRequest        POST

    RESTVerifyStatus       201
    RESTVerifyValue        message      User account created successfully

Login Ausfuehren
    RESTSelectEndpoint     /users/login
    RESTSetValue           email        ${EMAIL}
    RESTSetValue           password     ${PASSWORD}
    RESTSendRequest        POST
    RESTMemorizeValue      data.token   TOKEN

Loesche Testbenutzer
    RESTSelectEndpoint     /users/login
    RESTSetValue           email        ${EMAIL}
    RESTSetValue           password     ${PASSWORD}
    RESTSendRequest        POST
    RESTMemorizeValue      data.token   TOKEN

    RESTSelectEndpoint     /users/delete-account
    RESTSetHeader          x-auth-token    $MEM{TOKEN}
    RESTSendRequest        DELETE

    RESTStop
