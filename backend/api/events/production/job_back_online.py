from events.production.base_production import BaseProduction, BaseProductionModel
from utils.dt import timestamp
from events.event_model import EventModel
from events.event_type import EventType
class JobBackOnlineModel(BaseProductionModel):
  event_type: str = EventType.JOB_BACK_ONLINE.name

class JobBackOnline(BaseProduction):
  event_data: JobBackOnlineModel

  def set_model(self, base_model: EventModel):
    self.event_data = JobBackOnlineModel(**base_model.model_dump())

  def apply(self):
    updated_work_session = dict(
      _key=self.event_data.work_session_key,
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
