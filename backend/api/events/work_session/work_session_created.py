from datetime import datetime

from events.production.base_production import BaseProductionEvent
from models.event import EventInfoModel, EventType
from models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries


class WorkSessionCreatedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    job_key: str
    work_session_end: datetime | None = None
    forced: bool | None = False

  @classmethod
  def get_event_type(cls):
    return EventType.WORK_SESSION_CREATED

  @property
  def tx_collections(self):
    return [
      'WorkSession',
    ]

  def apply(self):
    self._get_job_data()
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

    # TODO: Use JOB_PAUSED event to close other work sessions
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
        batch_key = self.info.active_batch_key,
        work_order_key = self.job.wo_key,
        phase_key = self.job.phase_key,
        product_key = self.job.product_key,
        user_key = self.info.user_key,
        user_session_key = self.info.user_session_key,
        start = self.info.timestamp,
        end = self.info.work_session_end,
        forced = self.info.event_group if self.info.forced else None,
      )
    ).next()

    self.response = WorkSession(**new_work_session)
