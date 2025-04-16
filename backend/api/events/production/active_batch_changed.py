

from events.production.base_production import BaseProductionEvent
from events.wip.wip_booked import WIPBookedEvent
from events.wip.wip_unbooked import WIPUnbookedEvent
from models.event import EventInfoModel, EventType
from models.production import Job
from models.serial import SerialSelection
from models.traceability import *
from utils.serial import Queries as SerialQueries
from utils.production import Queries as ProductionQueries

class ActiveBatchChangedEvent(BaseProductionEvent):

  class InfoModel(EventInfoModel):
    job_key: str
    new_active_batch_qt: int
    batch_serials: list[str] | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.ACTIVE_BATCH_CHANGED

  def apply(self):
    self._get_job_data()
    self.get_active_batch()

    active_batch_qt_delta = self.info.new_active_batch_qt - self.job.active_batch_qt

    if active_batch_qt_delta == 0 and not len(self.info.batch_serials):
      raise ValueError("Active batch quantity already matches the quantity requested")

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

    # ================================================
    # WIP MANAGEMENT
    # ================================================
    shared_event_data = dict(
      job_key=self.job.key,
      phase_key=self.job.phase_key,
      batch_key=self.batch.key,
      work_order_key=self.job.wo_key,
      batch_serials=self.info.batch_serials
    )

    # ------------------------------------------------
    # NO TRACEABILITY
    # ------------------------------------------------
    if not self.job.traceability_level:
      # No need to update wip
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

    # ------------------------------------------------
    # WITH TRACEABILITY
    # ------------------------------------------------
    else:
      # Clean up temporary component serial links, removing those linked
      # to serials that are no longer in the batch
      self.tx.aql.execute("""
        FOR c IN contains
        FILTER
          !c.confirmed
          && c.batch_key == @batch_key
          && PARSE_IDENTIFIER(c._from).key NOT IN @batch_serials
        REMOVE c IN contains
      """, bind_vars=dict(batch_key=self.batch.key, batch_serials=self.info.batch_serials))

      if self.job.first_phase:
        # Create or delete serials and batch_serial records as needed

        if active_batch_qt_delta > 0:
          # Create serials
          counter_key = None

          if self.job.serial_code_on_creation:
            try:
              counter_key = self.tx.collection('Product').get(self.job.product_key).get('counter_key', None)
            except AttributeError:
              raise ValueError("The product can't be found on the database")

            if counter_key is None and not len(self.info.batch_serials):
              raise ValueError("Can't create serial code automatically. Assign a counter to the product.")

          self._create_serial_records(
            quantity=active_batch_qt_delta,
            batch_key=self.batch.key,
            wo_key=self.job.wo_key,
            product_key=self.job.product_key,
            serial_codes=self.info.batch_serials,
            counter_key=counter_key
          )

        else:
          # Delete serials
          bind_vars = dict(
            batch_key = self.batch.key,
            to_delete = abs(active_batch_qt_delta)
          )
          # Serials may not have a code yet in first phase, so we delete them based on creation date
          cursor = self.tx.aql.execute(
            SerialQueries.DELETE_BATCH_SERIALS,
            bind_vars=bind_vars
          )
          # TODO: Use named graph with auto deletion of edges to avoid the following
          self.tx.aql.execute(SerialQueries.CLEANUP_SERIAL_BATCH_LINKS)
          self.tx.aql.execute(SerialQueries.CLEANUP_COMPONENT_LINKS)

      else:
        # Has serials but not first phase.
        # The WIPBookedEvent deletes all serial wip and rebooks the requested serials,
        # so we don't need to unbook them first.
        WIPBookedEvent.create_as_child(self, dict(
          **shared_event_data,
          quantity=self.info.new_active_batch_qt,
        ))

    # ================================================
    # RESPONSE
    # ================================================
    new_job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.info.job_key)).next()
    self.response = dict(
      message=f"Active batch { self.info.active_batch_key } has been correctly updated with quantity { self.info.new_active_batch_qt }",
      job_data=new_job_data,
      batch_data=self.get_batch_execution_data(),
    )

    if self.job.traceability_level is not None:
      self.response['batch_serials'] = [SerialSelection(**s) for s in self.tx.aql.execute(
        SerialQueries.GET_BATCH_SERIALS,
        bind_vars=dict(batch_key=self.job.active_batch_key)
      )]

