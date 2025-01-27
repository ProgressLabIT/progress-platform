from robot.api.deco import keyword
from commons.Event import Event
from utils.api_manager import APIManager
from datetime import datetime



class ProductionEvents(Event):

    #{"event_type":"JOB_STARTED","user_key":"29682613","user_session_key":"42413842","job_key":"42399150",
    # "product_key":"14190259","work_order_key":"42399121","phase_key":"14190261","active_batch_key":null,
    # "project_code":null,"step_key":null,"form_data":[],"completed_batch_qt":null,
    # "timestamp":"2025-01-25T13:34:24.242Z","batch_serials":[],"step_changed_qt":null,"new_active_batch_qt":null}

    @keyword('Job started event')
    def job_started_event(self, job_key, product_key, work_order_key, phase_key):
      event_data = {
          'event_type': "JOB_STARTED",
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'job_key': job_key,
          'product_key': product_key,
          'work_order_key': work_order_key,
          'phase_key': phase_key,
          'timestamp': datetime.now().isoformat(),
      }
      return self.send_event(event_data)

    #{"event_type":"JOB_PAUSED","user_key":"29682613","user_session_key":"42413842","job_key":"42399150",
    # "product_key":"14190259","work_order_key":"42399121","phase_key":"14190261","active_batch_key":"42410204",
    # "project_code":null,"step_key":null,"form_data":[],"completed_batch_qt":null,"timestamp":"2025-01-25T13:34:26.517Z","batch_serials":[],"step_changed_qt":null,"new_active_batch_qt":null}

    @keyword('Job paused event')
    def job_paused_event(self, job_key, product_key, work_order_key, phase_key):
      event_data = {
          'event_type': "JOB_PAUSED",
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'job_key': job_key,
          'product_key': product_key,
          'work_order_key': work_order_key,
          'phase_key': phase_key,
          'timestamp': datetime.now().isoformat(),
      }
      return self.send_event(event_data)

    #{"event_type":"JOB_RESUMED","user_key":"29682613","user_session_key":"42413843","job_key":"42399150",
    # "product_key":"14190259","work_order_key":"42399121","phase_key":"14190261","active_batch_key":"42410204",
    # "project_code":null,"step_key":null,"form_data":[],"completed_batch_qt":null,"timestamp":"2025-01-25T13:36:42.938Z",
    # "batch_serials":[],"step_changed_qt":null,"new_active_batch_qt":null}

    @keyword('Job resumed event')
    def job_resumed_event(self, job_key, product_key, work_order_key, phase_key):
      event_data = {
          'event_type': "JOB_RESUMED",
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'job_key': job_key,
          'product_key': product_key,
          'work_order_key': work_order_key,
          'phase_key': phase_key,
          'timestamp': datetime.now().isoformat(),
      }
      return self.send_event(event_data)

    #{"event_type":"STEP_COMPLETED","user_key":"29682613","user_session_key":"42413843",
    # "job_key":"42399150","product_key":"14190259","work_order_key":"42399121","phase_key":"14190261",
    # "active_batch_key":"42410204","project_code":null,"step_key":"24160782",
    # "form_data":[{"form_field_key":"e61c088b-02ce-447b-a20d-fd89fa43ddc4","custom_field_key":"40887756","value":"asd"}],
    # "completed_batch_qt":null,"timestamp":"2025-01-25T13:49:24.164Z","batch_serials":[],
    # "step_changed_qt":null,"new_active_batch_qt":null}

    @keyword('Step completed event')
    def step_completed_event(self, job_key, product_key, work_order_key, phase_key, step_key, form_data=[], batch_serials=[]):
      event_data = {
          'event_type': "STEP_COMPLETED",
          'timestamp': datetime.now().isoformat(),
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'job_key': job_key,
          'product_key': product_key,
          'work_order_key': work_order_key,
          'phase_key': phase_key,
          'step_key': step_key,
          'form_data': form_data,
          'batch_serials': batch_serials,
      }
      return self.send_event(event_data)

    #{"event_type":"ACTIVE_BATCH_CHANGED","user_key":"29682613","user_session_key":"42413843","job_key":"42399150",
    # "product_key":"14190259","work_order_key":"42399121","phase_key":"14190261","active_batch_key":"42410205",
    # "project_code":null,"step_key":null,"form_data":[],"completed_batch_qt":null,"timestamp":"2025-01-25T13:50:12.729Z",
    # "batch_serials":[],"step_changed_qt":null,"new_active_batch_qt":4}

    @keyword('Active batch changed event')
    def active_batch_changed_event(self, job_key, product_key, work_order_key, phase_key, new_active_batch_qt):
      event_data = {
          'event_type': "ACTIVE_BATCH_CHANGED",
          'timestamp': datetime.now().isoformat(),
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'job_key': job_key,
          'product_key': product_key,
          'work_order_key': work_order_key,
          'phase_key': phase_key,
          'new_active_batch_qt': new_active_batch_qt,
      }
      return self.send_event(event_data)
