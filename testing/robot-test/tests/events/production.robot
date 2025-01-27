*** Settings ***
Library     ../../resources/ProductionEvents.py
Library     ../../resources/WorkOrderAPI.py
Library     ../../resources/AdminAPI.py
Library     ../../resources/JobAPI.py
Resource    ../../resources/definitions.resource
Library     ../../resources/ApiAuthenticator.py

Suite Setup    Create and assign work order
Suite Teardown    Delete work order

*** Variables ***
${workorder_key}    value
${job_key}    value
${phase_key}    value
${step_key}    value


*** Test Cases ***
Start job
    ${response}=    Job started event    ${job_key}    ${workorder_product_key}    ${workorder_key}    ${phase_key}
    Log To Console    ${response}

Pause job
    ${response}=    Job paused event    ${job_key}    ${workorder_product_key}    ${workorder_key}    ${phase_key}
    Log To Console    ${response}

Resume job
    ${response}=    Job resumed event    ${job_key}    ${workorder_product_key}    ${workorder_key}    ${phase_key}
    Log To Console    ${response}


Complete step
    ${response}=    Step completed event    ${job_key}    ${workorder_product_key}    ${workorder_key}    ${phase_key}    ${step_key}
    Log To Console    ${response}

Change active batch
    ${response}=    Active batch changed event    ${job_key}    ${workorder_product_key}    ${workorder_key}    ${phase_key}    ${workorder_new_batch_quantity}
    Log To Console    ${response}


*** Keywords ***
Create and assign work order
    ${wo_code} =    Get Time    epoch
    ${workorder_response} =    Create work order    WO${wo_code}    ${workorder_product_key}    ${workorder_create_quantity}
    Log    ${workorder_response}
    Set Suite Variable    ${workorder_key}    ${workorder_response['work_order']['_key']}
    Log    ${workorder_key}
    Set Suite Variable    ${job_key}    ${workorder_response['jobs'][0]['_key']}
    Log    ${job_key}
    Set Suite Variable    ${phase_key}    ${workorder_response['jobs'][0]['phase_key']}
    Log    ${phase_key}
    ${logged_user_key}=    Get Logged User Key
    Log    ${logged_user_key}
    Assign job    ${job_key}    ${logged_user_key}    ${workorder_create_quantity}

Delete work order
    Force delete work order    ${workorder_key}


