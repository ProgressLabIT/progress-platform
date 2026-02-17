from models.production import Job
from utils.float_precision import round_float

# ===================================================================
# Job
# ===================================================================


class BaseJobEvent:

  def set_job_active_state(self, active: bool):
    update_data = dict(
      _key=self.job_key,
      active=active
    )
    updated_job = self.tx.collection('Job').update(update_data, check_rev=False, return_new=True)['new']
    self.job = Job(**updated_job)

  def update_job_last_online(self):
    update_data = dict(
      _key=self.job_key,
      last_online=self.timestamp
    )
    self.tx.collection('Job').update(update_data)

  def _get_job_data(self):
    self.job = Job(**self.tx.collection('Job').get(self.info.job_key))
    self.info.work_order_key = self.job.wo_key
    self.info.phase_key = self.job.phase_key
    self.info.active_batch_key = self.job.active_batch_key
    self.info.product_key = self.job.product_key
    self.info.work_session_key = self.job.last_work_session_started if self.job.active else None


  def get_job_steps_count(self):
    return self.tx.aql.execute(
      """
      FOR job IN Job
        FILTER job._key == @job_key
        RETURN LENGTH(job.step_sequence)
      """,
      bind_vars=dict(job_key=self.info.job_key)
    ).next()


  # TODO: Use TraceabilityQueries.UPDATE_JOB_PROGRESS instead (?)
  def update_job_step_progress(self):
    self._get_job_data()

    current_batch_total_value = round_float(self.job.active_batch_qt / self.job.qt_planned)

    steps_count = self.get_job_steps_count()
    step_progress_value = round_float(current_batch_total_value / steps_count)
    step_done_count = self.get_batch_step_done_count()
    completed_qt_progress = round_float(self.job.qt_completed / self.job.qt_planned)
    total_progress = completed_qt_progress + (step_progress_value * step_done_count)

    job_update=dict(
      _key = self.job.key,
      progress = int(round_float(total_progress * 100))
    )

    job = Job(**self.tx.collection('Job').update(job_update, return_new=True)['new'])
    self.job = job

