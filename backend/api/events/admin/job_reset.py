from events.admin.base_admin import BaseAdmin
from utils.dt import timestamp

from utils.traceability import Queries as TraceabilityQueries
from utils.serial import Queries as SerialQueries
from utils.exceptions import WipNotAvailableError

class JobReset(BaseAdmin):

  @classmethod
  def get_write_collections(self):
    return list(set(super().get_write_collections() + ['Batch', 'wip', 'batch_serial', 'Serial']))

  @classmethod
  def get_read_collections(self):
    return super().get_read_collections()


  def apply(self):
    self._get_job_data()

    # Cancel Batches
    job_batches_cursor = self.tx.aql.execute("""
      FOR b IN Batch
      FILTER b.job_key == @job_key && b.canceled == null
      UPDATE b WITH { canceled: @event_key } IN Batch
      LET updated = NEW
      RETURN updated._key
    """, bind_vars = dict(
      job_key = self.job.key,
      event_key = self.id
    ))
    job_batch_keys = [b for b in job_batches_cursor]

    # Check there's enough free available downstream wip of job.last_phase before resetting the job
    available_wip = self.tx.aql.execute(
      TraceabilityQueries.GET_AVAILABLE_WIP_UPSTREAM_AND_DOWNSTREAM_OF_JOB,
      bind_vars = dict(job_key=self.job.key)
    ).next()

    free_wip_qt_downstream = sum(w['quantity'] for w in available_wip['downstream_free_wip'])

    if self.job.traceability_level:
      # Updates will be rolled back if the availability check will fail.

      # Delete Serial Links
      cursor = self.tx.aql.execute("""
        FOR b IN @batch_keys
        FOR s, e IN 1..1 OUTBOUND CONCAT('Batch/', b) batch_serial
        LET serial_key = s._key
        REMOVE e IN batch_serial
        RETURN serial_key
      """, bind_vars=dict(batch_keys=job_batch_keys))
      job_serial_keys = [s for s in cursor]

      # Check all serials are available in the phase buffer downstream
      wip_serials_count = self.tx.aql.execute("""
        FOR w IN wip
        FILTER
          w.serial_key IN @job_serial_keys
          AND w._from == CONCAT('Phase/', @phase_key)
        RETURN 1
        """,
        bind_vars = dict(
          job_serial_keys = job_serial_keys,
          phase_key = self.job.phase_key
        ),
        count=True
      ).count()

      # Cancel Serials (if first phase)
      if self.job.first_phase:
        serial_updates = [dict(_key=s, deleted=True) for s in job_serial_keys]
        self.tx.collection('Serial').update_many(serial_updates)

      else:
        # Delete data from serials
        self.tx.aql.execute(
          SerialQueries.REMOVE_PHASE_DATA_FROM_SERIALS,
          bind_vars = dict(
            serial_keys = job_serial_keys,
            phase_keys = [self.job.phase_key]
          )
        )

        # Make serials available as wip from previous phase
        new_wip_records = [dict(
          _from = f"Phase/{available_wip['previous_phase_key']}",
          _to = f"Phase/{self.job.phase_key}",
          batch_key = None,
          wo_key = self.job.wo_key,
          product_key = self.job.product_key,
          quantity = 1,
          serial_key = s,
          forced = self.id
        ) for s in job_serial_keys]

        self.tx.collection('wip').insert_many(new_wip_records)

    else: # No traceability - updates will be rolled back if there's no availability
      # Add upstream wip
      self.tx.collection('wip').insert(dict(
        _from = f"Phase/{available_wip['previous_phase_key']}",
        _to = f"Phase/{self.job.phase_key}",
        batch_key = None,
        wo_key = self.job.wo_key,
        product_key = self.job.product_key,
        quantity = self.job.qt_released,
        forced = self.id
      ))

    availability_check_ref = wip_serials_count if self.job.traceability_level else free_wip_qt_downstream

    if not self.job.last_phase and availability_check_ref < self.job.qt_released:
      raise WipNotAvailableError("You can't reset the job because its output is being worked on in following phases. Reset those jobs first.")

    # Cancel StepExecutionData and WorkSession records
    match = dict(job_key = self.job_key, canceled = None)
    update = dict(canceled = self.id)
    self.tx.collection('StepExecutionData').update_match(match, update)
    self.tx.collection('WorkSession').update_match(match, update)

    # Delete downstream wip
    if not self.job.last_phase:
      self.tx.aql.execute("""
        FOR w IN wip
        FILTER w.batch_key in @batch_keys
        REMOVE w IN wip
      """, bind_vars=dict(batch_keys=job_batch_keys))

    # Update job as created
    job_update = dict(
      _key = self.job_key,
      qt_completed = 0,
      qt_released = 0,
      stage = 'created',
      start = None,
      end = None,
      progress = 0
    )
    self.tx.collection('Job').update(job_update)

