*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Test Cases ***
Gesundheitscheck Mit Env Aus Userprofil
    [Documentation]    Env file loaded from ~/.okw/env/env-home.yaml
    RESTStart              NotesAPI_env    env-home

    RESTSelectEndpoint     /health-check
    RESTSendRequest        GET

    RESTVerifyStatus       200
    RESTVerifyValue        message      Notes API is Running

    RESTStop
