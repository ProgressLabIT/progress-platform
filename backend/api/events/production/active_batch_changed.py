

from models.traceability import *
from models.production import Job
from events.production.base_production import BaseProductionEvent, BaseProductionModel
from models.event import EventModel

from utils.serial import Queries as SerialQueries

class ActiveBatchChangedModel(BaseProductionModel):
  ...

class ActiveBatchChanged(BaseProductionEvent):



  def apply(self):
    self._get_job_data()
    self.get_active_batch()

    if not self.info.work_session_key:
      self.info.work_session = self.get_current_work_session()
      self.info.work_session_key = self.info.work_session.key

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
          if self.info.batch_serials is not None and len(self.info.batch_serials) == self.info.new_active_batch_qt:
            self.book_wip_serials()
          else:
            raise ValueError(f"The serials provided do not match the update requested. New qt: {self.new_active_batch_qt}. Serials provided: {self.batch_serials}")
      # No serial, only update batch quantity
      else:
        if not self.job.first_phase:
          if active_batch_qt_delta > 0:
            self.book_wip(active_batch_qt_delta)
          else: # active_batch_qt_delta < 0:
            self.unbook_wip(abs(active_batch_qt_delta))
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
    self.set_response(dict(
      message=f"Active batch { self.info.active_batch_key } has been correctly updated with quantity { self.info.new_active_batch_qt }",
      job_data=self.job,
      batch_data=self.get_batch_execution_data()
    ))
