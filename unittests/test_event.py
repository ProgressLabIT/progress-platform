import pytest
from pytest_mock import mocker

import time

from models.traceability import ProductionEvent, Batch, WorkSession 
from models.production import Job
from utils.dt import timestamp
from datetime import datetime



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
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='STEP_COMPLETED'))
    
    e.complete_step = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()
    
    ws = e.save()
    
    e.complete_step.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='JOB_STARTED'))
    
    e.start_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()
    
    ws = e.save()
    
    e.start_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='JOB_CLOSED'))
    
    e.close_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.close_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='JOB_PAUSED'))
    
    e.pause_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.pause_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='JOB_PAUSED_OFFLINE'))
    
    e.pause_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.pause_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='JOB_RESUMED'))
    
    e.resume_job = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.resume_job.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


    e = Event(ProductionEvent(event_type='JOB_BACK_ONLINE'))
    
    e.restore_work_session = mocker.Mock()
    e.update_job_last_online = mocker.Mock()
    e.update_work_order = mocker.Mock()

    ws = e.save()
    
    e.restore_work_session.assert_called() # i.
    e.update_job_last_online.assert_called() # ii.
    e.update_work_order.assert_called() # iii.
    e.tx.commit_transaction.assert_called()
    del e


@pytest.mark.connect_db
def test_save_integration():
    pass


@pytest.mark.connect_db
def test_create_work_session(connect_database, mocker):
    '''
    Test for the create_work_session method in the Event class. Verifies that:
    i. the worksession specified by the keys attached to Event is returned by the method
    ii. the worksession specified by the keys attached is actually created in the database
    *. the created worksession is an active worksession (the worksession has attribute active = True)  
    '''

    Event = connect_database["Event"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))

    e.tx = e.db.begin_transaction(write=e.write_collections)

    e.info.job_key = "12101234"
    e.info.work_order_key = "12104321"
    e.info.user_key = "12109999"
    e.info.user_session_key = "12101111"
    e.info.timestamp = None

    ret = e.create_work_session()

    # i. assert that the worksession is correctly returned by the method
    assert ret.job_key == "12101234"
    assert ret.work_order_key == "12104321"
    assert ret.user_key == "12109999"
    assert ret.user_session_key == "12101111"
    assert ret.active == True # *

    # ii. assert that the worksession is actually created in the database
    match=dict(
      job_key=e.info.job_key,
      work_order_key = e.info.work_order_key,
      user_key = e.info.user_key,
      user_session_key = e.info.user_session_key,
      active=True
    )
    data_from_db = e.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)

    assert work_session.job_key == "12101234"
    assert work_session.work_order_key == "12104321"
    assert work_session.user_key == "12109999"
    assert work_session.user_session_key == "12101111"
    assert work_session.active == True # *

    # commit and close the transaction
    e.tx.commit_transaction()

    del e


@pytest.mark.connect_db
def test_get_current_work_session(connect_database, mocker):
    '''
    Test for the get_current_work_session method in the Event class. Verifies that:
    1. when a worksession with specified job key (the current worksession) exists
         i.  if the worksession is active (active = True), the correct worksession is returned (-> by asserting the returned worksession _key)
         ii. if the worksession is not active (active = False), a runtime exception occurs
    2. when a worksession with specified job key (the current worksession) does not exist, a runtime exception occurs
    '''

    Event = connect_database["Event"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))
    
    # specify a job key for testing purpose and attach the key to the event object
    spec_job_key = "12101234"
    e.info.job_key = spec_job_key

    # 1.
    # insert a test worksession in the database
    e.tx = e.db.begin_transaction(write=e.write_collections) # i.
    ws_test=dict(
      _key="12109876",
      job_key= spec_job_key,
      user_session_key="12100000",
      user_key="12100000",
      active=True
    )
    e.tx.collection('WorkSession').insert(ws_test)

    ret = e.get_current_work_session()
    assert ret.key == "12109876"

    e.tx = e.db.begin_transaction(write=e.write_collections) # ii.
    error = 0
    ws_test=dict(
        _key="12109877",
        job_key= spec_job_key,
        user_session_key="12100000",
        user_key="12100000",
        active=False
    )
    e.tx.collection('WorkSession').insert(ws_test)
    try:
        ret = e.get_current_work_session()
    except:
        error = 1
    
    assert error == 1

    # 2.
    e.tx.collection('WorkSession').delete(ws_test)
    error = 0
    try:
        ret = e.get_current_work_session()
    except:
        error = 1
    
    assert error == 1
    
    # commit and close the transaction
    e.tx.commit_transaction()

    del e


@pytest.mark.connect_db
def test_close_work_session(connect_database, mocker):
    '''
    Test for the close_work_session method in the Event class. 
    Verifies that for the worksession identified by the current worksession key (e.info.work_session_key)
         i.  the worksession is deactivated (-> assert active = False)
         ii. the ending time is updated to the current timestamp (-> being initialized to None, the value of end is updated to e.info.timestamp)
    '''

    Event = connect_database["Event"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))

    # specify a worksession key for testing purpose and attach the key to the event object
    spec_worksession_key = "12109876"
    e.info.work_session_key = spec_worksession_key
    e.info.timestamp = datetime(2022, 5, 10)

    # insert a test worksession in the database
    e.tx = e.db.begin_transaction(write=e.write_collections)
    ws_test=dict(
      _key = spec_worksession_key,
      job_key = "12101234",
      user_session_key = "12100000",
      user_key = "12100000",
      active = True,
      end = None
    )
    e.tx.collection('WorkSession').insert(ws_test)

    ret = e.close_work_session()

    match=dict(
      _key = spec_worksession_key,
      job_key = "12101234",
      user_session_key = "12100000",
      user_key = "12100000",
      active=False,
      end = datetime(2022, 5, 10)
    )
    data_from_db = e.tx.collection('WorkSession').find(match).next()
    work_session = WorkSession(**data_from_db)

    assert work_session.active == False # i.
    assert work_session.end == datetime(2022, 5, 10) # ii.

    # commit and close the transaction
    e.tx.commit_transaction()

    del e


@pytest.mark.patch_db
def test_create_batch(my_database, mocker):
    '''
    Test for the create_batch method in the Event class. Verifies that:
         1. the WIP is booked (-> book_wip method is called) when 
             i.  the phase is not the first phase (-> first_phase attribute of the job is set to False)
             ii. the phase has the default null value (-> first_phase attribute of the job is set to None)
         2. the WIP is not booked (-> book_wip method is called) when the phase is the first phase
             -> first_phase attribute of the job is set to True
         *. returns a pydantic validated Batch object from the batch collection
    '''

    # Load fixture patches
    Event = my_database["Event"]
    my_job = my_database["job"]
    my_batch = my_database["batch"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))

    # Set mocks and patches
    e.get_job_data = mocker.Mock()
    e.get_job_data.return_value = my_job

    e.info.job_key = '12345678'
    e.info.phase_key = '99999999'
    e.info.work_order_key = '00000000'
    e.info.timestamp = timestamp()

    e.tx = mocker.MagicMock()
    e.tx.collection('Batch').insert.return_value = {'new' : my_batch} # *
    
    e.book_wip = mocker.Mock()

    # 1.
    my_job.first_phase = False # i.
    e.create_batch()
    e.book_wip.assert_called()
    
    e.book_wip.reset_mock()
    my_job.first_phase = None # ii.
    e.create_batch()
    e.book_wip.assert_called()
    e.book_wip.reset_mock()

    # 2.
    my_job.first_phase = True
    e.create_batch()
    e.book_wip.assert_not_called()
    del e


@pytest.mark.connect_db
def test_get_current_batch(connect_database):
    '''
    Test for the get_current_batch method in the Event class. Verifies that:
    1. when a batch with specified job key (the current batch) exists
         i.  if the batch is active (active = True), the correct batch is returned (-> by asserting the returned batch _key)
         ii. if the batch is not active (active = False), a runtime exception occurs
    2. when a batch with specified job key (the current batch) does not exist, a runtime exception occurs
    '''

    Event = connect_database["Event"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))

    # specify a worksession key for testing purpose and attach the key to the event object
    spec_job_key = "12101234"
    e.info.job_key = spec_job_key

    # 1.
    # insert a test batch in the database
    e.tx = e.db.begin_transaction(write=e.write_collections) # i.
    batch_test=dict(
      _key="12109876",
      job_key = spec_job_key,
      work_order_key = "12100000",
      phase_key = "12100000",
      start = datetime(2022, 5, 10),
      active = True,
    )
    e.tx.collection('Batch').insert(batch_test)

    ret = e.get_current_batch()

    assert ret.key == "12109876"

    e.tx = e.db.begin_transaction(write=e.write_collections) # ii.
    batch_test=dict(
      _key="12109877",
      job_key = spec_job_key,
      work_order_key = "12100000",
      phase_key = "12100000",
      start = datetime(2022, 5, 10),
      active = False,
    )
    e.tx.collection('Batch').insert(batch_test)
    try:
        ret = e.get_current_batch()
    except:
        error = 1
    
    assert error == 1

    # 2.
    e.tx.collection('Batch').delete(batch_test)
    error = 0
    try:
        ret = e.get_current_batch()
    except:
        error = 1
    
    assert error == 1
    
    # commit and close the transaction
    e.tx.commit_transaction()

    del e


@pytest.mark.connect_db
def test_get_batch_step_done_count(connect_database):
    '''
    Test for the get_batch_step_done_count method in the Event class. 
    -> Verifies that the correct number of items in the StepExecutionData collection, filtered by 'done' status and a specified (current) batch key, is returned.
    '''
    
    Event = connect_database["Event"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))

    e.info.current_batch_key = "12093656"

    e.tx = e.db.begin_transaction(write=e.write_collections)
    ret = e.get_batch_step_done_count()

    assert ret == 10
    

@pytest.mark.patch_db
def test_current_step_was_last_to_do(my_database, mocker):
    '''
    Test for the current_step_was_last_to_do method in the Event class. Verifies that:
    1. returns 1 when get_job_step_sequence returns a number of elements equal to the get_batch_step_done_count return value (i., ii.)
    2. returns 0 when get_job_step_sequence returns a number of elements different from the get_batch_step_done_count return value
    '''

    Event = my_database["Event"]

    e = Event(ProductionEvent(event_type='JOB_STARTED'))

    e.get_job_step_sequence = mocker.Mock()
    e.get_batch_step_done_count = mocker.Mock()

    # 1.
    e.get_job_step_sequence.return_value = ["0", "1", "2", "3"] # i. case of non empty list
    e.get_batch_step_done_count.return_value = 4

    ret = e.current_step_was_last_to_do()

    assert ret == 1

    e.get_job_step_sequence.return_value = [] # ii. case of empty list
    e.get_batch_step_done_count.return_value = 0

    ret = e.current_step_was_last_to_do()

    assert ret == 1

    # 2.
    e.get_job_step_sequence.return_value = ["0", "1", "2", "3"]
    e.get_batch_step_done_count.return_value = 3

    ret = e.current_step_was_last_to_do()

    assert ret == 0

@pytest.mark.dev
@pytest.mark.connect_db
def test_create_batch_time_record(connect_database):
    pass