*** Settings ***
Library     ../../resources/ApiAuthenticator.py
Resource    ../../resources/definitions.resource
Suite Setup    Authenticate User and Start Session    ${api_username}    ${api_username}
Suite Teardown    Logout
