import pytest
from pytest_mock import mocker
import os
import sys
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

#import utils
from utils.config import get_config
from models.traceability import ProductionEvent
from utils.event import Event
#import endpoints

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
    1. the object is correctly initialized
         i.   the 'response' property is set to None
         ii.  the 'action' method is correctly assigned according to the specified event type
         iii. the 'db' property is set to the arango database 'PROGRESS_TEST' by default when no database is specified as argument
    2. TBD
    '''

    # 1.
    e = Event(ProductionEvent(event_type='JOB_STARTED')) # i.
    assert e.response == None
    del e

    e = Event(ProductionEvent(event_type='JOB_STARTED')) # ii.
    assert e.action == 'start_job'
    del e
    e = Event(ProductionEvent(event_type='JOB_PAUSED'))
    assert e.action == 'pause_job'
    del e
    e = Event(ProductionEvent(event_type='JOB_PAUSED_OFFLINE'))
    assert e.action == 'pause_job'
    del e
    e = Event(ProductionEvent(event_type='JOB_RESUMED'))
    assert e.action == 'resume_job'
    del e
    e = Event(ProductionEvent(event_type='JOB_BACK_ONLINE'))
    assert e.action == 'restore_work_session'
    del e
    e = Event(ProductionEvent(event_type='JOB_CLOSED'))
    assert e.action == 'close_job'
    del e
    e = Event(ProductionEvent(event_type='STEP_COMPLETED'))
    assert e.action == 'complete_step'
    del e
    e = Event(ProductionEvent(event_type='BATCH_COMPLETED'))
    assert e.action == 'complete_batch'
    del e

    e = Event(ProductionEvent(event_type='JOB_STARTED')) # iii.
    assert e.db.name == "PROGRESS_TEST"
    del e

    e = Event(ProductionEvent(event_type='JOB_STARTED', job_key = 12092961, phase_key = 11976627, 
                                work_order_key = 12092959, user_session_key = 12006040, user_key = 11681276,
                                work_session_key = 12093618, product_key = 11728033))
    
    # TODO: understand why can not execute the save()
    #ws = e.save()
    #print(repr(ws))


def test_endpoint_item(mocker):
    '''
    Test for the item endpoint (API router) object integration with the database API, verifies that:
    1. the status code is correctly assigned by
         a. the database connection availability (arango container start/stop)
             i.  when the arango container is running, a call to the /item returns a 200 status code
             ii. when the arango container is not running, a call to the /item returns a 500 status code
         b. a not valid command sent by the client result in a 404 status code
    '''

    from endpoints.item import router as item

    config = get_config()

    app = FastAPI(
        # openapi_url=f"{config.root_path}/openapi.json",
        root_path=config.api_root_path
    )
    app.include_router(item)
    client = TestClient(app)

    # 1.a.
    os.system('docker start arango')
    time.sleep(1.5)

    response = client.get("/item")
    assert response.status_code == 200 # i.

    os.system('docker stop arango')
    time.sleep(1.5)

    response = client.get("/item")
    assert response.status_code == 500 # ii.

    # b.
    response = client.get("/iamnotavalidcommand")
    assert response.status_code == 404

    del app
    del client
    del item



def test_endpoint_item_db_patch(my_database):
    '''
    Test for the item endpoint (API router) object, verifies that:
    '''
    
    my_db = my_database["database"]
    app   = my_database["app"]

    client = TestClient(app)

    my_db.aql.execute.return_value = [{'_key': 'iamakey', 'code': '007', 'description': 'I am a production item, take care of me!', 'type': None, 'value': None}]

    os.system('docker start arango')
    time.sleep(1.5)

    response = client.get("/item")
    #assert response.status_code == 200

    print(response.json())

    del client



def test_endpoint_traceability(mocker):
    '''
    Test for the traceability endpoint (API router) object, verifies that:
    1. the status code is correctly assigned by
         a. the database connection availability (arango container start/stop)
             i.  when the arango container is running, a call to the /item returns a 200 status code
             ii. when the arango container is not running, a call to the /item returns a 500 status code
         b. a not valid command sent by the client result in a 404 status code
    '''




def test_database():
    '''
    Test to verify that the database is passing the data validation check by Pydantic.
    '''



