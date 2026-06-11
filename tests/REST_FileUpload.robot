*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI

*** Variables ***
${IGNORE}    $IGNORE

*** Test Cases ***
Einzelne Datei hochladen
    [Documentation]    Upload einer Textdatei via Multipart Form-Data
    RESTStart              Httpbin
    RESTSelectEndpoint     /post
    RESTSetValue           description    OKW Upload Test
    RESTSetFile            file           ${CURDIR}/testdata/upload.txt
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTVerifyValue        files.file     Hello OKW File Upload Test\n
    RESTVerifyValue        form.description    OKW Upload Test
    RESTStop

Datei mit explizitem MIME-Type
    [Documentation]    Upload mit manuell gesetztem Content-Type
    RESTStart              Httpbin
    RESTSelectEndpoint     /post
    RESTSetFile            data    ${CURDIR}/testdata/upload.txt    text/plain
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTVerifyValue        files.data    Hello OKW File Upload Test\n
    RESTStop

Mehrere Dateien gleiches Feld
    [Documentation]    Zwei Dateien unter dem gleichen Feldnamen (multiple)
    RESTStart              Httpbin
    RESTSelectEndpoint     /post
    RESTSetFile            attachments    ${CURDIR}/testdata/upload.txt
    RESTSetFile            attachments    ${CURDIR}/testdata/upload.txt
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTStop

File Upload mit IGNORE
    [Documentation]    RESTSetFile mit $IGNORE wird uebersprungen
    RESTStart              Httpbin
    RESTSelectEndpoint     /post
    RESTSetFile            file    ${IGNORE}
    RESTSendRequest        POST
    RESTVerifyStatus       200
    RESTStop
