import pytest
from pytest_mock import mocker

from models.traceability import ProductionEvent
from utils.event import Event


# Tests for the Event class

def test_init():
    '''
    Test for the __init__ method of the Event class. Verifies that:
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

    # 2.
    e = Event(ProductionEvent(event_type='JOB_STARTED', job_key = 12092961, phase_key = 11976627, 
                                work_order_key = 12092959, user_session_key = 12006040, user_key = 11681276,
                                work_session_key = 12093618, product_key = 11728033))
    
    # TODO: understand why can not execute the save()
    #ws = e.save()
    #print(repr(ws))


