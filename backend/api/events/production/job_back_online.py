from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType


class JobBackOnlineEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    work_order_key: str | None = None
    phase_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_BACK_ONLINE

  def apply(self):
    job_data = self.tx.collection('Job').get(self.info.job_key)
    self.info.phase_key = job_data['phase_key']
    self.info.work_order_key = job_data['work_order_key']

    updated_work_session = dict(
      _key=self.info.work_session_key,
      active=True,
      end=None
    )
    self.work_session = self.tx.collection('WorkSession').update(
      updated_work_session,
      return_new=True
    )['new']

    # update job as active
    self.set_job_active_state(True)

    self.set_response(self.job)
