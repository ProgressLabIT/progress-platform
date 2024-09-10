*** Settings ***
Library     ../../resources/ApiAuthenticator.py


*** Test Cases ***
No one is quthenticated at startup
    ${logged_user}=    Get Logged User Key
    Log To Console    ${logged_user}

A valid user can authenticate on API
    Authenticate User    simone    simone
    ${logged_user_key}=    Get Logged User Key
    Log To Console    ${logged_user_key}
    Logged username matches    ${logged_user_key}    simone


*** Keywords ***
Logged username matches
    [Arguments]    ${logged_user_key}    ${expected_username}
    ${logged_user}=    Get Logged Username From Key    ${logged_user_key}
    Log To Console    ${logged_user}
    Should Be Equal As Strings    ${logged_user}    ${expected_username}
