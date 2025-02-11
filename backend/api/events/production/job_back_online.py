from events.production.base_production import BaseProductionEvent, BaseProductionModel
from utils.dt import timestamp
from models.event import EventModel, EventInfoModel
from models.event import EventType


class JobBackOnlineEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str

  @classmethod
  def get_event_type(cls):
    return EventType.JOB_BACK_ONLINE

  def apply(self):
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
