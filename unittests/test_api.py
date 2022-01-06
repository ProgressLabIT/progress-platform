import pytest
from pytest_mock import mocker
import os
import sys

os.chdir('../backend/api') # all the modules here tested refer to the backend.api
sys.path.insert(0, '') # more info here: https://stackoverflow.com/questions/57870498/cannot-find-module-after-change-directory

#import utils
from models.traceability import ProductionEvent

from utils.event import Event

def test_ProductionEvent():
    '''
    Test for the ProductionEvent class in the models.traceability module. Verifies that:
    1. the object initialization will throw an exception when an invalid event type (string) is given as input argument
    2. the object will be created when a valid event type (e.g. 'JOB_STARTED') is given as input argument
    '''

    # 1.
    error = 0
    try:
        ProductionEvent(event_type='I_AM_NOT_A_VALID_EVENT_TYPE')
    except:
        error = 1

    assert error == 1

    # 2.
    error = 0
    try:
        ProductionEvent(event_type='JOB_STARTED')
    except:
        error = 1

    assert error == 0


def test_Event():
    '''
    Test for the Event class in the utils.event module. Verifies that:
    1. TBD
    '''

    e = Event(ProductionEvent(event_type='JOB_STARTED'))


