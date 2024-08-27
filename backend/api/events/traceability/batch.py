from commons.models.traceability import Batch, StepStatus


from utils.traceability import Queries as TraceabilityQueries

# ===================================================================
# Batch
# ===================================================================

def create_batch(self):
  if not hasattr(self, 'job'):
    self.get_job_data()

  use_serials = getattr(self.job, 'traceability_level', None)

  if use_serials and not self.job.first_phase:
    if len(self.info.batch_serials):
      batch_qt = len(self.info.batch_serials)
    else:
      raise ValueError("You must provide serials to be linked to this new batch")
  else:
    default_batch_qt = self.job.parameters.production_batch_qt
    # qt_completed must include any update from the current event being recorded
    remaining_qt = self.job.qt_planned - self.job.qt_completed
    # if production_batch_qt is zero, use total remaining quantity
    if default_batch_qt == 0:
      batch_qt = remaining_qt
    # Do not consider production batch if remaining quantity is lower
    else:
      batch_qt = min([default_batch_qt, remaining_qt])

  if batch_qt == 0:
    raise ValueError("Quantity cannot be zero or negative")

  new_batch_in = Batch(
    job_key = self.info.job_key,
    phase_key = self.info.phase_key,
    work_order_key = self.info.work_order_key,
    qt_total = batch_qt,
    start = self.info.timestamp,
    active = True
  )

  new_batch_out = self.tx.collection('Batch').insert(new_batch_in, return_new=True)['new']

  self.batch = Batch(**new_batch_out)
  self.info.new_batch_key = self.batch.key

  # Book wip from buffer
  if not self.job.first_phase:
    self.book_wip(batch_qt)
  elif use_serials:
    self.create_batch_serial_records(quantity=batch_qt)

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
    bind_vars=dict(batch_key=self.batch.key if hasattr(self, 'batch') else self.info.active_batch_key)
  ).next()

  return batch_execution_data


def current_step_was_last_to_do(self):
  total_step_count = self.get_job_steps_count()
  step_done_count = self.get_batch_step_done_count()

  return step_done_count == total_step_count
