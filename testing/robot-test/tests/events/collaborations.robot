*** Settings ***
Library     ../../resources/CollaborationsEvents.py
Resource    ../../resources/definitions.resource

*** Variables ***
${issue_key}    value
${message_key}    value
*** Test Cases ***
Send critical product issue created event
    ${response}=    Product Issue Created Event    issue_type_key=3142793    product_key=10090138    operation_key=11513    phase_key=10090140    critical=True
    Log To Console    ${response}
    Set Suite Variable    ${issue_key}    ${response['issue_key']}
    Log To Console    ${issue_key}

Send issue updated event
    ${response}=    Issue Updated Event    issue_key=${issue_key}    data=[]
    Log To Console    ${response}

Mark issue as critical
    ${response}=    Mark issue critical event    issue_key=${issue_key}    critical=True
    Log To Console    ${response}

Mark issue as not critical
    ${response}=    Mark issue critical event    issue_key=${issue_key}    critical=False
    Log To Console    ${response}

Send issue closed event
    ${response}=    Issue Closed Event    issue_key=${issue_key}
    Log To Console    ${response}

Reopen issue as critical
    ${response}=    Issue Reopened Event    issue_key=${issue_key}    critical=True
    Log To Console    ${response}

ReSend issue closed event
    ${response}=    Issue Closed Event    issue_key=${issue_key}
    Log To Console    ${response}

Reopen issue as not critical
    ${response}=    Issue Reopened Event    issue_key=${issue_key}    critical=False
    Log To Console    ${response}

Send message posted event
    ${response}=    Message Posted Event    issue_key=${issue_key}    content="Hello"
    Log To Console    ${response}
    Set Suite Variable    ${message_key}    ${response['message_key']}
    Log To Console    ${message_key}

Send message updated event
    ${response}=    Message Updated Event    message_key=${message_key}    issue_key=${issue_key}    content="Hello"
    Log To Console    ${response}

Send message deleted event
    ${response}=    Message Deleted Event    message_key=${message_key}    issue_key=${issue_key}
    Log To Console    ${response}

Send issue deleted event
    ${response}=    Issue Deleted Event    issue_key=${issue_key}
    Log To Console    ${response}
