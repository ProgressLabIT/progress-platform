import pytest
from pytest_mock import mocker

import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

print(os.path.dirname(os.path.abspath(__file__)))

os.chdir('../backend/api') # all the modules here tested refer to the backend.api
sys.path.insert(0, '') # more info here: https://stackoverflow.com/questions/57870498/cannot-find-module-after-change-directory

from utils.config import get_config
from patch_settings import *


@pytest.fixture(autouse = False)
def my_database(mocker):
    # implement a fixture that mocks the database
    
    my_db = mocker.patch('utils.db.db')
    #my_HTTPException = mocker.patch('fastapi.HTTPException')
    #my_HTTPException.return_value = Exception('BOOM!')

    my_collection = mocker.Mock()
    my_collection.all.return_value = [my_data_collection]
 
    my_db.collection.return_value = my_collection

    from endpoints.item import router as item

    config = get_config()

    app = FastAPI(
        # openapi_url=f"{config.root_path}/openapi.json",
        root_path=config.api_root_path
    )
    app.include_router(item)

    return {"database" : my_db, "app" : app}#, "HTTPException" : my_HTTPException}


@pytest.fixture(autouse = False)
def connect_database():
    # instantiate actual connection with the database
    
    from endpoints.item import router as item

    config = get_config()

    app = FastAPI(
        # openapi_url=f"{config.root_path}/openapi.json",
        root_path=config.api_root_path
    )
    app.include_router(item)

    return app


@pytest.fixture(autouse = False)
def docker_arango_start():

    os.system('docker start arango')
    
    
@pytest.fixture(autouse = False)
def docker_arango_stop():

    yield
    os.system('docker stop arango')
