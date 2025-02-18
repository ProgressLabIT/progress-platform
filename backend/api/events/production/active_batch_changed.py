

from events.production.base_production import BaseProductionEvent
from events.wip.wip_booked import WIPBookedEvent
from events.wip.wip_unbooked import WIPUnbookedEvent
from models.event import EventInfoModel, EventType
from models.production import Job
from models.traceability import *
from utils.serial import Queries as SerialQueries


class ActiveBatchChangedEvent(BaseProductionEvent):

  class InfoModel(EventInfoModel):
    job_key: str
    new_active_batch_qt: int
    batch_serials: list[str]

  @classmethod
  def get_event_type(cls):
    return EventType.ACTIVE_BATCH_CHANGED

  def apply(self):
    self._get_job_data()
    self.get_active_batch()

    active_batch_qt_delta = self.info.new_active_batch_qt - self.job.active_batch_qt

    if active_batch_qt_delta == 0 and not len(self.info.batch_serials):
      raise ValueError("Active batch quantity already matches the quantity requested")

    else:
      if self.job.traceability_level:
        if self.job.first_phase:
          # Create or delete batch_serial records if necessary
          # TODO: Refactor to use serial service
          #
          # JUST IN CASE the batch serials do not match the active quantity
          # ensure we're removing the right number of serials to get to the derised quantity
          batch_serials_qt = self.tx.aql.execute(
            SerialQueries.GET_BATCH_SERIALS,
            bind_vars = dict(batch_key = self.batch.key),
            count = True
          ).count()

          serials_delta = self.info.new_active_batch_qt - batch_serials_qt

          if serials_delta > 0:
            self._create_batch_serial_records(quantity=serials_delta)
          else:
            bind_vars = dict(
              batch_key = self .event_data.batch_key,
              to_delete = abs(serials_delta)
            )
            cursor = self.tx.aql.execute(
              SerialQueries.DELETE_BATCH_SERIALS,
              bind_vars=bind_vars
            )
            # TODO: Use named graph with auto deletion of edges to avoid the following
            self.tx.aql.execute(SerialQueries.CLEANUP_SERIAL_BATCH_LINKS)

        # Has serials but not first phase
        else:
          shared_event_data = dict(
            job_key=self.job.key,
            phase_key=self.job.phase_key,
            batch_key=self.batch.key,
            work_order_key=self.job.wo_key,
            batch_serials=self.info.batch_serials
          )
          if self.info.batch_serials is not None and len(self.info.batch_serials) == self.info.new_active_batch_qt:
            WIPBookedEvent.create_as_child(self, dict(
              **shared_event_data,
              quantity=self.info.new_active_batch_qt,
            ))
          else:
            raise ValueError(f"The serials provided do not match the update requested. New qt: {self.new_active_batch_qt}. Serials provided: {self.batch_serials}")
      # No serial, only update batch quantity
      else:
        if not self.job.first_phase:
          if active_batch_qt_delta > 0:
            WIPBookedEvent.create_as_child(self, dict(
              **shared_event_data,
              quantity=active_batch_qt_delta,
            ))
          else: # active_batch_qt_delta < 0:
            WIPUnbookedEvent.create_as_child(self, dict(
              **shared_event_data,
              quantity=abs(active_batch_qt_delta)
            ))
        # no else here, if first phase and no serial no need to manage other collections
        # just proceed with batch/job updates

    # Update Batch
    self.batch = Batch(**self.tx.collection('Batch').update(dict(
      _key=self.batch.key,
      qt_total=self.info.new_active_batch_qt
    ), return_new=True)['new'])

    # Update Job
    self.job = Job(**self.tx.collection('Job').update(dict(
      _key=self.job.key,
      active_batch_qt=self.info.new_active_batch_qt
    ), return_new=True)['new'])

    # Set response
    self.response = dict(
      message=f"Active batch { self.info.active_batch_key } has been correctly updated with quantity { self.info.new_active_batch_qt }",
      job_data=self.job,
      batch_data=self.get_batch_execution_data()
    )
