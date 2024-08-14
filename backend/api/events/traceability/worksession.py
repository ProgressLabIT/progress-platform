from commons.models.traceability import WorkSession
from utils.traceability import Queries as TraceabilityQueries

# ===================================================================
# WorkSession
# ===================================================================

def create_work_session(self):
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
      job_key = self.job.key,
      batch_key = self.batch.key, # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
      work_order_key = self.job.wo_key,
      phase_key = self.job.phase_key,
      product_key = self.job.product_key,
      user_key = self.info.user_key,
      user_session_key = self.info.user_session_key,
      start = self.info.timestamp,
    )
  ).next()
  self.work_session = WorkSession(**new_work_session)
  self.info.work_session_key = self.work_session.key


def get_current_work_session(self):
  match=dict(
    job_key=self.info.job_key,
    active=True
  )
  data_from_db = self.tx.collection('WorkSession').find(match).next()
  work_session = WorkSession(**data_from_db)
  return work_session


def close_work_session(self, end=None):
  if end == None:
    end = self.info.timestamp

  updated_work_session = WorkSession(**self.tx.aql.execute(
    TraceabilityQueries.CLOSE_WORK_SESSION, bind_vars = dict(
      job_key = self.info.job_key,
      end = end,
  )).next())

  self.work_session = updated_work_session
  self.info.work_session_key = updated_work_session.key

  return updated_work_session