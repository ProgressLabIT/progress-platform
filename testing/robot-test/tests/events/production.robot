*** Settings ***
Library     ../../resources/ProductionEvents.py
Library     ../../resources/WorkOrderAPI.py
Library     ../../resources/AdminAPI.py
Library     ../../resources/JobAPI.py
Resource    ../../resources/definitions.resource
Library     ../../resources/ApiAuthenticator.py
Resource    ../../resources/keywords/production.resource

Suite Setup    Create and assign work order
Suite Teardown    Delete work order    ${workorder_key}

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
    ${workorder}    ${job}    ${phase} =    Create work order    ${workorder_product_key}    ${workorder_create_quantity}
    Set Suite Variable    ${workorder_key}    ${workorder}
    Set Suite Variable    ${job_key}    ${workorder}
    Set Suite Variable    ${phase_key}    ${workorder}
    Assign job    ${job_key}    ${workorder_create_quantity}
    RETURN    ${workorder_key}    ${job_key}    ${phase_key}



