import pytest
from pytest_mock import mocker

from models.traceability import ProductionEvent
#from utils.event import Event


# Tests for the Event class

@pytest.mark.connect_db
def test_init(connect_database):
    '''
    Test for the __init__ method of the Event class. Verifies that:
    -> the object is correctly initialized
        i.   the 'response' property is set to None
        ii.  the 'action' method is correctly assigned according to the specified event type
        iii. the 'db' property is set to the arango database 'PROGRESS_TEST' by default when no database is specified as argument
    '''

    Event = connect_database["Event"]

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


@pytest.mark.patch_db
def test_save(my_database, mocker):
    '''
    Test for the save method in the Event class. Verifies that:
         i.   the correct action method related to the event type is called, e.g. 'complete_batch' is called when event type is 'BATCH_COMPLETED'
         ii.  the update_job_last_online method is called
         iii. the update_work_order method is called 
    '''

    Event = my_database["Event"]


    e = Event(ProductionEvent(event_type='BATCH_COMPLETED'))
    
    e.complete_batch = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()
    
    ws = e.save()
    
    e.complete_batch.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.

    
    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='STEP_COMPLETED'))
    
    e.complete_step = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()
    
    ws = e.save()
    
    e.complete_step.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.


    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='JOB_STARTED'))
    
    e.start_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()
    
    ws = e.save()
    
    e.start_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.


    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='JOB_CLOSED'))
    
    e.close_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.close_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.


    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='JOB_PAUSED'))
    
    e.pause_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.pause_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.


    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='JOB_PAUSED_OFFLINE'))
    
    e.pause_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.pause_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.


    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='JOB_RESUMED'))
    
    e.resume_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.resume_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.


    e.update_work_order.reset_mock()
    e.update_job_last_online.reset_mock()

    e = Event(ProductionEvent(event_type='JOB_BACK_ONLINE'))
    
    e.restore_work_session = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.restore_work_session.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    
    
    
    
    tx.commit_transaction.assert_called()
