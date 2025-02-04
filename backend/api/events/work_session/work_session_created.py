from events.work_session.base_work_session import BaseWorkSession, WorkSessionEventModel
from models.event import EventType
from models.event import EventModel
from models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries
class WorkSessionCreatedModel(WorkSessionEventModel):
  event_type: str = EventType.WORK_SESSION_CREATED.name
  work_session: WorkSession | None = None

class WorkSessionCreatedEvent(BaseWorkSession):
  event_data: WorkSessionCreatedModel

  def set_model(self, base_model: EventModel):
    self.event_data = WorkSessionCreatedModel(**base_model.model_dump())

  def apply(self):
    self._get_job_data()
    # Close unallowed parallel work sessions
    bind_vars = dict(
      user_key = self.event_data.user_key,
      timestamp = self.event_data.timestamp
    )

    closed_sessions_cursor = self.tx.aql.execute(
      TraceabilityQueries.CLOSE_UNALLOWED_PARALLEL_WORK_SESSIONS,
      bind_vars=bind_vars
    )
    closed_sessions_jobs = [ws['job_key'] for ws in closed_sessions_cursor]
    if len(closed_sessions_jobs):
      self.tx.aql.execute(
        """
        FOR j IN Job
        FILTER j._key IN @jobs
        UPDATE j WITH { 'active': false } IN Job
        """,
        bind_vars=dict(jobs=closed_sessions_jobs)
      )

    # Create new work session
    new_work_session = self.tx.aql.execute(
      TraceabilityQueries.CREATE_WORK_SESSION, bind_vars=dict(
        job_key = self.job.key,
        batch_key = self.event_data.batch_key, # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
        work_order_key = self.job.wo_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        user_key = self.event_data.user_key,
        user_session_key = self.event_data.user_session_key,
        start = self.event_data.timestamp,
      )
    ).next()
    self.work_session = WorkSession(**new_work_session)
    self.event_data.work_session_key = self.work_session.key

    self.set_response(dict(
      work_session_key = self.work_session.key
    ))
