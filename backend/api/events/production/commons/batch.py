from models.traceability import Batch, StepStatus
from utils.traceability import Queries as TraceabilityQueries

# ===================================================================
# Batch
# ===================================================================


class BaseBatchEvent:

  def get_active_batch(self):
    match = dict(
      _key=self.job.active_batch_key,
      active=True
    )

    try:
      data_from_db = self.tx.collection('Batch').find(match).next()
      self.batch = Batch(**data_from_db)
      self.info.active_batch_key = self.batch.key
      self.info.active_batch_qt = self.batch.qt_total
    except StopIteration:
      pass

  def get_batch_step_done_count(self):
    # Instead of looking at total count, use distinct to
    # bypass potential duplicate STEP_COMPLETED events on the same step
    # within the same batch

    bind_vars = dict(
      batch_key=self.batch.key,
      status=StepStatus.DONE
    )

    step_done_count = self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_STEP_DONE_COUNT,
      bind_vars=bind_vars
    ).next()

    return step_done_count


  def get_batch_execution_data(self):

    batch_execution_data = self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_EXECUTION_DATA,
      # in self info can be under new_batch_key or active_batch_key, taking it from self.batch makes it more consistent.
      bind_vars=dict(batch_key=self.batch.key if hasattr(self, 'batch') and hasattr(self.batch, 'key') else self.info.active_batch_key)
    ).next()

    return batch_execution_data


  def _check_all_batch_steps_done(self):
    return self.tx.aql.execute(
      TraceabilityQueries.ALL_BATCH_STEPS_DONE,
      bind_vars=dict(batch_key=self.batch.key, job_key=self.job.key)
    ).next()
