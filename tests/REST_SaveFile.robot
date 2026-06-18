*** Settings ***
Library    okw_api_rest.library.OkwApiRestLibrary    WITH NAME    RESTAPI
Library    OperatingSystem

Suite Setup       RESTStart    DummyJSON
Suite Teardown    RESTStop

*** Variables ***
${IGNORE}    $IGNORE

*** Test Cases ***
Response Als Datei Speichern
    RESTSelectEndpoint         /products/1
    RESTSendRequest            GET
    RESTVerifyStatus           200
    RESTSaveResponseToFile     %{TEMP}/okw_test_product.json
    File Should Exist          %{TEMP}/okw_test_product.json
    ${size}=    Get File Size    %{TEMP}/okw_test_product.json
    Should Be True    ${size} > 0
    [Teardown]    Remove File    %{TEMP}/okw_test_product.json

Response Speichern Mit IGNORE
    RESTSelectEndpoint         /products/1
    RESTSendRequest            GET
    RESTSaveResponseToFile     ${IGNORE}
