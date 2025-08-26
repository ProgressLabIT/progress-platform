import shutil
from functools import cached_property
from pathlib import Path

from events.inventory.movement_completed import MovementCompletedEvent
from events.production.base_production import BaseProductionEvent
from events.production.batch_created import BatchCreatedEvent
from events.production.batch_released import BatchReleasedEvent
from events.production.job_closed import JobClosedEvent
from events.serial.serial_linked import SerialLinkedEvent
from events.serial.serial_updated import SerialUpdatedEvent
from events.serial.serial_released import SerialReleasedEvent
from events.wip.wip_declared import WIPDeclaredEvent
from events.wip.wip_removed import WIPRemovedEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from models.event import EventInfoModel, EventType
from models.form import FormFieldValue, SerialFormFieldValue
from models.inventory import InventoryMovementReferences, InventoryMovementType
from models.production import Job
from models.traceability import *
from utils.counter import _generate_counter
from utils.production import Queries as ProductionQueries
from utils.traceability import Queries as TraceabilityQueries
from utils.serial import Queries as SerialQueries
from utils.inventory import Queries as InventoryQueries


class BatchCompletedEvent(BaseProductionEvent):
  class InfoModel(EventInfoModel):
    active_batch_key: str
    completed_batch_qt: float
    step_data: list[ExecutionDataUpdate] | None = None
    batch_serial_keys: list[str] | None = None
    job_key: str | None = None
    work_order_key: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.BATCH_COMPLETED

  # ===================================================================
  # MAIN LOGIC
  # ===================================================================

  def apply(self):
    # ===================================================================
    # VALIDATE DATA AND SET CONTEXT
    # ===================================================================
    self.batch = Batch(**self.tx.collection('Batch').get(self.info.active_batch_key))

    # Validate batch quantity
    if self.batch.qt_total != self.info.completed_batch_qt:
      raise ValueError("Active batch quantity does not match the completed quantity provided. Update the active batch first.")

    self.info.job_key = self.batch.job_key
    self.info.work_order_key = self.batch.work_order_key
    self._get_job_data()

    # Validate job status
    if self.job.stage == 'closed':
      raise ValueError("Job is already closed")

    # save into a variable since self.job gets updated in the process
    is_next_batch_available = self.job.next_batch_available

    # Increment job completed quantity
    new_job_qt_completed = self.job.qt_completed + self.batch.qt_total

    # ===================================================================
    # STORE BATCH EXECUTION DATA
    # ===================================================================

    if self.info.step_data:
      if not self.job.parameters.step_check:
        # Do this only if `step_check` is not active / Require to use `StepCompletedEvent` if it is
        self._store_batch_execution_data()
      else:
        raise ValueError("Step check is active for the job. Use `StepCompletedEvent` to store step data.")


    # ===================================================================
    # HANDLE TRACEABILITY
    # ===================================================================
    self._handle_batch_serials()


    # ===================================================================
    # GENERATE PRODUCTION/CONSUMPTION MOVEMENTS
    # ===================================================================
    # Put here to avoid proceeding if there is some inventory issue
    # Will be skipped if warehouse management is not enabled
    # ===================================================================
    self._process_inventory_changes()


    # ===================================================================
    # CLOSE WORK SESSION
    # ===================================================================
    WorkSessionClosedEvent.create_as_child(self, dict(
      work_session_end = self.info.timestamp,
      work_session_key = self.info.work_session_key
    ))

    # ===================================================================
    # UPDATE BATCH RECORD
    # ===================================================================
    self.tx.aql.execute(
      TraceabilityQueries.COMPLETE_BATCH, bind_vars=dict(
        batch_key=self.info.active_batch_key,
        qt_pass=self.info.completed_batch_qt,
        end=self.info.timestamp
      )
    )

    # ===================================================================
    # HANDLE WIP AND NOTIFY RELEASED PIECES
    # ===================================================================

    if not self.job.first_phase:
      WIPRemovedEvent.create_as_child(self, dict(
        job_key=self.info.job_key,
        quantity=self.info.completed_batch_qt,
      ))

    if not self.job.last_phase:
      # If next_phase, generate a WIP record and update job input availability state
      WIPDeclaredEvent.create_as_child(self, dict(
        job_key=self.info.job_key,
        quantity=self.info.completed_batch_qt,
        serial_keys=self.info.batch_serial_keys
      ))

    else:
      BatchReleasedEvent.create_as_child(self, dict(
        batch_key=self.info.active_batch_key,
        product_key=self.info.product_key,
        work_order_key=self.info.work_order_key,
        qt_released=self.info.completed_batch_qt,
        serial_keys=self.info.batch_serial_keys,
      ))


    # ===================================================================
    # NO REMAINING QUANTITY TO DO (LAST BATCH) -> CLOSE JOB
    # ===================================================================
    if new_job_qt_completed >= self.job.qt_planned:
      # Event will take care of closing the job
      self.job = JobClosedEvent.create_as_child(self, dict(
        job_key = self.info.job_key,
        completed_qt = new_job_qt_completed,
      ))

      # SET RESPONSE
      self.response = dict(
        message = f"Batch {self.info.active_batch_key} and Job {self.info.job_key} completed.",
        job_data = self.job
      )

    # ===================================================================
    # JOB HAS REMAINING QUANTITY -> UPDATE JOB AND CREATE NEW BATCH IF NEEDED
    # ===================================================================
    else:
      new_progress = round(100 * new_job_qt_completed / self.job.qt_planned)

      job_update = dict(
        _key = self.info.job_key,
        active_batch_key = None,
        active_batch_qt = 0,
        qt_completed = new_job_qt_completed,
        qt_released = new_job_qt_completed,
        progress = new_progress,
        active = False
      )

      # Auto new batch ignored if serials must be selected for new batch. Clients must select new serials to start the new one
      # The batch_serials event property could be confused with the ones of the batch being declared.
      create_new_batch = (
        self.job.parameters.auto_new_batch
        and is_next_batch_available
        and not (self.job.traceability_level and not self.job.first_phase)
      )

      if create_new_batch:
        self.batch = BatchCreatedEvent.create_as_child(self, dict(
          # batch_serials is not needed since auto new batch works only without serials
          job_key = self.info.job_key,
          work_order_key = self.info.work_order_key,
          phase_key = self.info.phase_key,
          product_key = self.info.product_key,
        ))
        self.work_session = WorkSessionCreatedEvent.create_as_child(self, dict(
          job_key = self.info.job_key,
          batch_key = self.batch.key,
          work_order_key = self.info.work_order_key,
          phase_key = self.info.phase_key,
          product_key = self.info.product_key,
        ))

        # Update job with new batch/work session data
        job_update.update(dict(
          active_batch_qt = self.batch.qt_total,
          active_batch_key = self.batch.key,
          last_work_session_started = self.work_session.key,
          active = True
        ))

      # Store job update
      self.job = Job(**self.tx.collection('Job').update(job_update, check_rev=False, return_new=True)['new'])


      # SET RESPONSE
      self.response = dict(
        message = f"Batch {self.batch.key} completed.",
        job_data = self.job,
        batch_data = dict(),
      )

      # Update response with batch execution data if new batch is created
      if create_new_batch:
        self.response['batch_data'] = self.get_batch_execution_data()
        new_job_data = self.tx.aql.execute(ProductionQueries.GET_WORKING_JOB_DATA, bind_vars=dict(job_key = self.info.job_key)).next()
        if ('wo_bom' in new_job_data):
          setattr(self.job, 'wo_bom', new_job_data['wo_bom'])


  # =================================================================
  # HELPER METHODS
  # =================================================================

  def _store_batch_execution_data(self):
    # This is necessary only if `step_check` is not active, since if it is, data is stored in `StepCompletedEvent`
    step_execution_data = [StepExecutionData(
      key = step.execution_record_key,
      job_key = self.info.job_key,
      user_key = self.info.user_key,
      work_session_key = self.job.last_work_session_started,
      batch_key = self.info.active_batch_key,
      step_key = step.step_key,
      completed = self.info.timestamp,
      status = StepStatus.DONE,
      form_data = step.form_data,
    ) for step in self.info.step_data]

    # Insert step execution data for form steps provided, excluding
    # unset fields in order to patch existing records, preserving
    # `modified` status if present
    step_execution_records = [x.model_dump(
      by_alias=True,
      exclude_unset=True,
      exclude_none=True
    ) for x in step_execution_data]

    self.tx.collection('StepExecutionData').insert_many(
      step_execution_records,
      overwrite_mode='update'
    )

  # =================================================================

  def _prepare_serial_data(self):
    batch_data = self.tx.aql.execute(
      TraceabilityQueries.GET_BATCH_EXECUTION_DATA,
      bind_vars=dict(batch_key=self.info.active_batch_key)
    ).next()

    serial_data = []
    for step in batch_data['step_data']:
      for field in step['form_data']:
        serial_data.append(SerialFormFieldValue(
          form_field_key = field['form_field_key'],
          custom_field_key = field['custom_field_key'],
          value = field.get('value', None),
          step_key = step['_key'],
          batch_key = self.info.active_batch_key,
          phase_key = self.job.phase_key,
        ))
    return serial_data

  # =================================================================

  @cached_property
  def batch_component_serials_map(self):
    query = """
    RETURN MERGE(
      FOR c IN contains
      FILTER c.batch_key == @batch_key
      LET parent_serial_key = PARSE_IDENTIFIER(c._from).key
      LET child_serial_key = PARSE_IDENTIFIER(c._to).key
      COLLECT component_key = DOCUMENT(c._to).product_key
      INTO component_link = { parent_serial_key, child_serial_key }
      RETURN { [component_key]: component_link }
    )
    """
    return self.tx.aql.execute(query, bind_vars=dict(
      batch_key=self.info.active_batch_key
    )).next()

  # =================================================================

  def _handle_serial_code(self, serial_key):
    if self.job.first_phase:
      serial = self.tx.collection('Serial').get(serial_key)
      if not serial.get('code', None):
        if not serial.get('counter_key', None):
          raise ValueError("Cannot generate serial code. No code or counter provided.")
        return _generate_counter(self.tx, serial['counter_key'])

    return None

  # =================================================================

  def _handle_batch_serials(self):
    # Fetch batch serial keys
    if self.job.traceability_level is not None:
      self.info.batch_serial_keys = [s['_key'] for s in self.tx.aql.execute(
        SerialQueries.GET_BATCH_SERIALS,
        bind_vars=dict(batch_key=self.info.active_batch_key)
      )]

      # Save step data into batch serials if needed
      serial_data = self._prepare_serial_data()
      for serial_key in self.info.batch_serial_keys:
        serial_code = self._handle_serial_code(serial_key)
        if len(serial_data) > 0 or serial_code is not None:
          SerialUpdatedEvent.create_as_child(self, dict(
            serial_key = serial_key,
            serial_data = serial_data,
            serial_code = serial_code,
          ))

          # Copy batch media to serials
        self._copy_batch_media_to_serials()

      if self.job.last_phase:
        # Release serials
        for serial_key in self.info.batch_serial_keys:
          SerialReleasedEvent.create_as_child(self, dict(serial_key = serial_key))

    # Link component serials if any. Works in jobs with traceability enabled and disabled.
    # If traceability is disabled for the job, component serials are linked to the batch.
    for component_key, component_serials in self.batch_component_serials_map.items():
      for component_serial in component_serials:
        SerialLinkedEvent.create_as_child(self, dict(
          parent_serial_key = component_serial['parent_serial_key'] if self.job.traceability_level is not None else None,
          child_serial_key = component_serial['child_serial_key'],
          batch_key = self.info.active_batch_key,
          wo_key = self.info.work_order_key,
          job_key = self.info.job_key,
          phase_key = self.info.phase_key,
          process_inventory = False, # inventory is handled in _process_inventory_changes()
        ))



  # =================================================================

  @cached_property
  def warehouse_management_enabled(self):
    warehouse_management_enabled = self.tx.collection('Config').get('enable_inventory_management')
    return warehouse_management_enabled is not None and warehouse_management_enabled.get('value', False)


  # =================================================================

  def _process_inventory_changes(self):
    # Check if warehouse management is enabled
    if not self.warehouse_management_enabled:
      return

    # Get work order data
    # _get_job_data() already set self.info.work_order_key
    self.wo_data = self.get_work_order_data()

    # Set references for all inventory movements
    self.movement_references = InventoryMovementReferences(
      work_order_key = self.info.work_order_key,
      job_key = self.info.job_key,
      batch_key = self.info.active_batch_key
    )

    # Get product keys for all relevant products
    # Init list with output product
    product_keys = [self.job.product_key]

    # Get components for current phase
    self.bom = [line for line in self.wo_data.wo_bom if line.phase_key == self.info.phase_key]

    # Add components to list
    for line in self.bom:
      product_keys.append(line.component_key)

    # Get inventory config for all relevant products
    self.inventory_config = self.tx.aql.execute(
      InventoryQueries.PRODUCTS_INVENTORY_CONFIG,
      bind_vars=dict(product_keys=product_keys)
    ).next()

    self._process_output()
    self._process_consumption()

  # =================================================================

  def _process_output(self):
    # Generate production movement
    if self.inventory_config.get(self.job.product_key, False) and self.job.last_phase:
      default_production_position_key = self.tx.collection('Config').get('default_production_position').get('value', 'IN')
      production_position_key = self.wo_data.output_position_key or default_production_position_key

      base_production_data = dict(
        position_to = production_position_key,
        product_key = self.job.product_key,
        movement_type = InventoryMovementType.PRODUCTION,
        references = self.movement_references,
      )

      if self.info.batch_serial_keys:
        for serial_key in self.info.batch_serial_keys:
          MovementCompletedEvent.create_as_child(self, dict(
            **base_production_data,
            qt_confirmed = 1,
            qt_planned = 1,
            serial_key = serial_key,
          ))

      else:
        MovementCompletedEvent.create_as_child(self, dict(
          **base_production_data,
          qt_confirmed = self.info.completed_batch_qt,
          qt_planned = self.info.completed_batch_qt,
        ))

  # =================================================================

  def _process_consumption(self):
    # Generate consumption movements
    default_consumption_position_key = self.tx.collection('Config').get('default_consumption_position').get('value', 'IN')

    for line in self.bom:
      # Ensure warehouse management is enabled for component
      if self.inventory_config.get(line.component_key, False):
        consumption_position_key = line.consumption_options.consumption_position_key or default_consumption_position_key
        consumption_qt = line.qt * self.info.completed_batch_qt

        # If traceability is enabled, generate movements for each serial
        if line.traceability_level is not None:

          line_serials = [link['child_serial_key'] for link in self.batch_component_serials_map.get(line.component_key, [])]
          if len(line_serials) != consumption_qt:
            raise ValueError("The number of serials provided does not match the batch quantity.")

          for serial_key in line_serials:
            MovementCompletedEvent.create_as_child(self, dict(
              position_from = consumption_position_key,
              product_key = line.component_key,
              qt_confirmed = 1,
              qt_planned = 1,
              movement_type = InventoryMovementType.CONSUMPTION,
              references = self.movement_references,
              serial_key = serial_key,
            ))

        # If traceability is not enabled, generate movement for the batch
        else:
          MovementCompletedEvent.create_as_child(self, dict(
            position_from = consumption_position_key,
            product_key = line.component_key,
            qt_confirmed = consumption_qt,
            qt_planned = consumption_qt,
            movement_type = InventoryMovementType.CONSUMPTION,
            references = self.movement_references,
          ))


  # =================================================================

  def _copy_batch_media_to_serials(self):
    # Files are in step_key/custom_field_key/form_field_key directories (3 levels down)
    # Find all level3 directories using glob pattern
    batch_dir = Path(f"/media/traceability/{self.info.work_order_key}/{self.info.active_batch_key}")
    form_fields_dirs = list(batch_dir.glob('*/*/*/'))

    # Copy each form field directory to destination
    for serial_key in self.info.batch_serial_keys:
      dest_dir = Path(f"/media/serial/{serial_key}")
      for src_dir in form_fields_dirs:
        shutil.copytree(src_dir, dest_dir / src_dir.name, dirs_exist_ok=True)
