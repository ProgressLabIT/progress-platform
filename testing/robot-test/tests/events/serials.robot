*** Settings ***
Library     ../../resources/SerialsEvents.py
Resource    ../../resources/definitions.resource

*** Variables ***
${serial_key}    value

*** Test Cases ***
Send serial created event
    #${serial_data}=    [{"step_key":"42392983","form_field_key":"602425aa-cfde-4aaa-965e-f35f09cd2805","custom_field_key":"40887756","value":"123213"},{"step_key":"42392983","form_field_key":"3c7030c8-8bc2-4e3c-aa83-5c099d080e1d","custom_field_key":"3177058"},{"step_key":"42392983","form_field_key":"64184b1d-8c60-4553-8ca3-9f29e72dac6f","custom_field_key":"11672453"},{"step_key":"42392984","form_field_key":"7f2099d0-e6d1-4800-b94d-39904117bbae","custom_field_key":"3177058"},{"step_key":"42392984","form_field_key":"090bcd20-046f-4920-af7d-430db62db927","custom_field_key":"11672453"}]
    ${response}=    Serial Created Event    product_key=42392939    counter_key=42278929    data=[]
    #${serial_key}=    Set Variable    ${response['serial_key']}
    Set Suite Variable    ${serial_key}    ${response['serial_key']}
    Log To Console    ${serial_key}

Send serial updated event
    ${response}=    Serial Updated Event    serial_key=${serial_key}    data=[]
    Log To Console    ${response}

Send serial deleted event
    ${response}=    Serial Deleted Event    serial_key=${serial_key}    delete_children=False
    Log To Console    ${response}

