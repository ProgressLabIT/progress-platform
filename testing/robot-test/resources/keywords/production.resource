*** Settings ***
Library     String
Library     ../WorkOrderAPI.py
Library     ../AdminAPI.py
Library     ../JobAPI.py
Library     ../ApiAuthenticator.py

*** Keywords ***
Generate random serial code
    RETURN    Generate Random String    8    [NUMBERS]

Delete work order
    [Arguments]    ${workorder_key}
    Force delete work order    ${workorder_key}

Create work order
    [Arguments]    ${product_key}    ${create_quantity}
    ${wo_code} =    Get Time    epoch
    ${workorder_response} =    Do create work order    WO${wo_code}    ${product_key}    ${create_quantity}
    Log    ${workorder_response}
    ${workorder_key} =    Set Variable    ${workorder_response['work_order']['_key']}
    Log    ${workorder_key}
    ${job_key} =    Set Variable        ${workorder_response['jobs'][0]['_key']}
    Log    ${job_key}
    ${phase_key} =    Set Variable        ${workorder_response['jobs'][0]['phase_key']}
    Log    ${phase_key}
    RETURN    ${workorder_key}    ${job_key}    ${phase_key}

Assign job
    [Arguments]    ${job_key}    ${create_quantity}
    ${logged_user_key}=    Get Logged User Key
    Do assign job    ${job_key}    ${logged_user_key}    ${create_quantity}
