*** Settings ***
Library     ../../resources/ApiAuthenticator.py
Resource    ../../resources/definitions.resource


*** Test Cases ***
No one is authenticated at startup
    ${logged_user}=    Get Logged User Key
    Log To Console    ${logged_user}
    Should Be Equal As Strings    ${logged_user}    ${no_token_defined}

A valid user can authenticate on API
    Authenticate User    ${api_username}    ${api_username}
    ${logged_user_key}=    Get Logged User Key
    Log To Console    ${logged_user_key}
    Logged username matches    ${logged_user_key}    ${api_username}

A valid user can start a session
    Authenticate User    ${api_username}    ${api_username}
    ${logged_user_key}=    Get Logged User Key
    Log To Console    ${logged_user_key}
    ${session_key}=    Start Session    ${logged_user_key}
    Log To Console    ${session_key}
    Should Not Be Empty    ${session_key}


*** Keywords ***
Logged username matches
    [Arguments]    ${logged_user_key}    ${expected_username}
    ${logged_user}=    Get Logged Username From Key    ${logged_user_key}
    Log To Console    ${logged_user}
    Should Be Equal As Strings    ${logged_user}    ${expected_username}
