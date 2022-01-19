import pytest
from pytest_mock import mocker

import os


@pytest.fixture(autouse = False)
def my_database(mocker):
    # TODO: implement a fixture that mocks the database
    #from .item import router as item
    
    #my_db = mocker.patch('endpoints.item.db', 'collection')

    #import endpoints
    pass


@pytest.fixture(autouse = False)
def docker_arango_start():

    os.system('docker start arango')
    
    
@pytest.fixture(autouse = False)
def docker_arango_stop():

    yield
    os.system('docker stop arango')