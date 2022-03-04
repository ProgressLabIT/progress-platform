import pytest
from pytest_mock import mocker
import os
import sys
import time
import json

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


@pytest.mark.connect_db
def test_endpoint_item_integration(connect_database):
    '''
    Test for the item endpoint (API router) integration with the database connection, verifies that:
    1. the status code is correctly assigned by
         a.) the database connection availability (arango container start/stop)
             i.  when the arango container is running, a call to the /item returns a 200 status code
             ii. when the arango container is not running, a call to the /item returns a 500 status code
         b.) a not valid command sent by the client result in a 404 status code
    '''
    
    app = connect_database["app"]

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

    # TODO: repeat the same test for every endpoint


@pytest.mark.patch_db
def test_endpoint_item(mocker, my_database):
    '''
    Test for the item endpoint (API router) object, verifies that:
    1. in a successfull execution, returns a list 
         a.) of all production items, from 'ProductionItem' collection, and active products, from an AQL call to database
         b.) [TODO] of non duplicated items, when the database AQL call gives active products already present in the production items collection
    2. whether an exception occurs
         a.) during the AQL call, the control flow is stopped with the rising of an HTTPException
         b.) during the pydantic validation (ProductionItem model), the control flow is stopped with the rising of an HTTPException
    '''
    
    my_db  = my_database["database"]
    app    = my_database["app"]
    my_data_collection = my_database["data"]
    #my_HTTPException = my_database["HTTPException"]

    #my_HTTPException.reset_mock()

    client = TestClient(app)

    my_data = {'_key': 'iamakey', 'code': '007', 'description': 'I am a production item, take care of me!', 'type': None, 'value': None}

    # 1.
    my_db.aql.execute.return_value = [my_data] # a.

    response = client.get("/item")
    resp_list = response.json()

    assert resp_list == [my_data_collection, my_data]

    my_db.aql.execute.return_value = [my_data, my_data_collection] # b.
    
    response = client.get("/item")
    resp_list = response.json()

    assert not any(resp_list.count(element) > 1 for element in resp_list) # https://www.kite.com/python/answers/how-to-check-for-duplicates-in-a-list-in-python
    #assert resp_list == [my_data_collection, my_data]

    # 2.
    my_db.aql.execute = Exception # a.
    #my_HTTPException.reset_mock()

    #try:
    response = client.get("/item")
    resp_dict = response.json()["detail"]
    assert resp_dict["status"] == 500
    assert resp_dict["message"] == 'Could not fetch data from database'
    #except Exception as e:
    #    assert str(e) == 'BOOM!'

    #assert my_HTTPException.call_count == 1

    my_db.aql.execute = mocker.Mock()
    my_db.aql.execute.return_value = [{'I' : 1, 'do not' : 2, 'pass' : 3, 'Pydantic' : 'validation'}] # b.
    #my_HTTPException.reset_mock()

    #try:
    response = client.get("/item")
    resp_dict = response.json()["detail"]
    assert resp_dict["status"] == 500
    assert resp_dict["message"] == 'There was a problem with the data fetched from the db'
    #except Exception as e:
    #    assert str(e) == 'BOOM!'

    #assert my_HTTPException.call_count == 1

    del app
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



