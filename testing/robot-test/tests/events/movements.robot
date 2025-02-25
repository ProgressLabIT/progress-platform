*** Settings ***
Library     ../../resources/MovementsEvents.py
Resource    ../../resources/definitions.resource
Resource    ../../resources/keywords/serials.resource

*** Variables ***
${serial_code}    Generate random serial code

*** Test Cases ***
Send movement created event
    ${response}=    Movement Created Event    position_to=${movement_position_to}    serial_code=${serial_code}    product_key=${movement_product_key}    qt_planned=1    qt_confirmed=1    position_from=${movement_position_from}    status=${movement_status}    type=${movement_type}
    Log To Console    ${response}

