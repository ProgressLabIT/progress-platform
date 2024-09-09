*** Settings ***
Library     ../../resources/ApiAuthenticator.py


*** Test Cases ***
No one is quthenticated at startup
    ${logged_user}=    Get Logged User Key
    Log To Console    ${logged_user}

A valid user can authenticate on API
    Authenticate User    simone    simone
    ${logged_user}=    Get Logged User Key
    Log To Console    ${logged_user}
