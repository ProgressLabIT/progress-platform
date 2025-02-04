from events.work_session.base_work_session import BaseWorkSession, WorkSessionEventModel
from models.event import EventModel, EventType, EventInfoModel
from models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries


class WorkSessionStartedEvent(BaseWorkSession):
  class InfoModel(WorkSessionEventModel):
    pass


  @classmethod
  def get_event_type(cls):
    return EventType.WORK_SESSION_STARTED

  @property
  def tx_collections(self):
    return list(set(super().tx_collections + [
      'WorkSession',
    ]))

  def apply(self):
      # Close unallowed parallel work sessions
    bind_vars = dict(
      user_key = self.info.user_key,
      timestamp = self.info.timestamp
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
        job_key = self.info.job_key,
        batch_key = self.info.batch_key, # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
        work_order_key = self.info.work_order_key,
        phase_key = self.info.phase_key,
        product_key = self.info.product_key,
        user_key = self.info.user_key,
        user_session_key = self.info.user_session_key,
        start = self.info.timestamp,
      )
    ).next()

    self.response = WorkSession(**new_work_session)
