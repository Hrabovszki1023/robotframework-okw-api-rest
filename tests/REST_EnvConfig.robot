*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Gesundheitscheck Mit Environment Variablen
    RESTStart              NotesAPI_env    env-test

    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        message      Notes API is Running

    RESTStop
