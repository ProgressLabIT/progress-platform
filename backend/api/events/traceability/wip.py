from commons.models.serial import Serial
from commons.models.traceability import WIP
from commons.utils.serial import Queries as SerialQueries
from utils.exceptions import WipNotAvailableError
from utils.traceability import Queries as TraceabilityQueries


# ===================================================================
# WIP
# ===================================================================

def declare_wip(self):
  if not self.job:
    self.get_job_data()

  self.info.next_phase_key = self.tx.aql.execute(
    TraceabilityQueries.GET_NEXT_PHASE_IN_WORK_ORDER,
    bind_vars=dict(wo_key=self.info.work_order_key, phase_key=self.info.phase_key)
  ).next()

  # Prepare new wip data and make a single call to the database with insert_many
  # Insert many requires passing dicts (does not use default db serializer)
  if getattr(self.job, 'traceability_level', None):
    bind_vars = dict(batch_key = self.info.completed_batch_key)
    serial_to_declare_cursor = self.tx.aql.execute(SerialQueries.GET_BATCH_SERIALS, bind_vars=bind_vars)
    serial_to_declare = [Serial(**serial) for serial in serial_to_declare_cursor]
    
    new_wip_data = [dict(
      _from = f'Phase/{self.info.phase_key}',
      _to = f'Phase/{self.info.next_phase_key}',
      batch_key = self.info.completed_batch_key,
      wo_key = self.info.work_order_key,
      product_key = self.info.product_key,
      quantity = 1,
      serial_key = s.key
    ) for s in serial_to_declare]

  else:
    new_wip_data = [dict(
      _from=f'Phase/{self.info.phase_key}',
      _to=f'Phase/{self.info.next_phase_key}',
      batch_key=self.info.completed_batch_key,
      wo_key=self.info.work_order_key,
      product_key=self.info.product_key,
      quantity=self.info.completed_batch_qt
    )]

  self.tx.collection('wip').insert_many(new_wip_data)

  self.update_wip_availability_for_phases(phase_keys=[self.info.next_phase_key])

def remove_wip(self, quantity):
  """
  Remove upstream wip records related to the completed batch
  """
  booked_wips_cursor = self.tx.collection('wip').find(dict(
    _to=f'Job/{self.info.job_key}',
  ))
  booked_wips = [WIP(**wip) for wip in booked_wips_cursor]
  # Here we sort the wip by quantity in ascending order to remove as many full records as possible, starting from the smallest one.
  # NEXT: In the future, when serial number management will be implemented, this logic will have to be reviewed to account for specific wip selection.
  booked_wips = sorted(booked_wips, key=lambda wip: wip.quantity)

  # Remove/reduce wip, record by record up to declared quantity
  for wip in booked_wips:
    if quantity >= wip.quantity:
      # Remove entire wip for job
      self.tx.collection('wip').delete(wip.key)
      quantity -= wip.quantity
      if quantity == 0:
        break
    else:
      # Partially remove wip by reducing the quantity
      unbooking_percentage = quantity / wip.quantity
      self.tx.collection('wip').update(dict(
        _key=wip.key,
        quantity=wip.quantity - quantity,
        value=wip.value * (1 - unbooking_percentage)
      ))
      quantity = 0
      break

  if quantity > 0:
    raise WipNotAvailableError(f"Not enough booked wip to remove. Needed { quantity } more")

def book_wip_serials(self):
  # Reset job/batch links in wip and batch_serial so that it works
  # when serials are changed or the quantity reduced
  reset_wip_match = dict(_to=f'Job/{self.info.job_key}')
  reset_wip_update = dict(_to=f'Phase/{self.info.phase_key}', active=False)
  self.tx.collection('wip').update_match(reset_wip_match, reset_wip_update)

  reset_batch_serial_match = dict(_from=f'Batch/{self.batch.key}')
  self.tx.collection('batch_serial').delete_match(reset_batch_serial_match)

  # Book and link to batch new serials, checking they are all available
  free_wip_cursor = self.tx.aql.execute(
    TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
    bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
  )
  free_wip_serials = [WIP(**wip).serial_key for wip in free_wip_cursor]

  serials_to_update = []
  unavailable_serials = []
  for serial_key in self.info.batch_serials:
    target = serials_to_update if serial_key in free_wip_serials else unavailable_serials
    target.append(serial_key)

  if len(unavailable_serials):
    raise WipNotAvailableError(f'Serials {unavailable_serials} are not available')
  else:
    self.tx.aql.execute(
      SerialQueries.BOOK_SERIAL_WIP,
      bind_vars=dict(
        serial_keys=serials_to_update,
        job_key=self.info.job_key
      )
    )
    self.send_link_batch_serial_event()
  
  self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])


def book_wip(self, quantity) -> None:
  if quantity == 0:
    raise ValueError("Cannot book a quantity of zero")

  # Traceability Enabled -> Book specific serials in case of phases following the first
  if getattr(self.job, 'traceability_level', None) and self.info.batch_serials != None and not self.job.first_phase:
    if len(self.info.batch_serials) == quantity:
      self.book_wip_serials()
    else:
      raise ValueError("The number of serials provided does not match the requested quantity. Provided quantity: {quantity}. Provided serials: {self.info.batch_serials}")
  
  # Traceability 
  else:
    free_wips_cursor = self.tx.aql.execute(
      TraceabilityQueries.RETRIEVE_AVAILABLE_WIP,
      bind_vars=dict(phase_key=self.info.phase_key, wo_key=self.info.work_order_key)
    )
    free_wips = [WIP(**wip) for wip in free_wips_cursor]
    free_wips = sorted(free_wips, key=lambda wip: wip.quantity)

    # TODO: change using while loop like in events/admin.py@override_progress
    for wip in free_wips:
      if quantity >= wip.quantity:
        # Book entire batch for job
        self.tx.collection('wip').update(dict(
          _key = wip.key,
          _to = f'Job/{self.info.job_key}',
          active = True
        ))
        quantity -= wip.quantity
        if quantity == 0:
          break

      else:
        # Partially book batch for job
        booking_percentage = quantity / wip.quantity
        self.tx.collection('wip').update(dict(
          _key=wip.key,
          quantity=wip.quantity - quantity,
          value=wip.value * (1 - booking_percentage)
        ))

        # Add wip record with partially booked batch
        new_wip = WIP(
          from_doc=wip.from_doc,
          to_doc=f'Job/{self.info.job_key}',
          wo_key=wip.wo_key,
          batch_key=wip.batch_key,
          product_key=wip.product_key,
          quantity=quantity,
          value=wip.quantity * booking_percentage,
          active=True
        )
        self.tx.collection('wip').insert(new_wip)
        quantity = 0
        break

    if quantity > 0:
      raise WipNotAvailableError(f"Not enough free wip available to book. Needed { quantity } more")

  # Update input availability for jobs in this phase
  # Execute both with and without traceability
  self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])
  

def unbook_wip(self, quantity):
  if quantity == 0:
    return

  booked_wips_cursor = self.tx.collection('wip').find(dict(
    _to=f'Job/{self.info.job_key}',
  ))
  booked_wips = [WIP(**wip) for wip in booked_wips_cursor]
  booked_wips = sorted(booked_wips, key=lambda wip: wip.quantity)

  for wip in booked_wips:
    if quantity >= wip.quantity:
      # Unbook entire batch for job
      self.tx.collection('wip').update(dict(
        _key = wip.key,
        _to = f'Phase/{self.info.phase_key}'
      ))
      quantity -= wip.quantity
      if quantity == 0:
        break
    else:
      # Partially unbook batch for job
      unbooking_percentage = quantity / wip.quantity
      self.tx.collection('wip').update(dict(
        _key=wip.key,
        quantity=wip.quantity - quantity,
        value=wip.value * (1 - unbooking_percentage)
      ))

      # Add free wip record with partially unbooked batch
      new_wip = WIP(
        from_doc=wip.from_doc,
        to_doc=f'Phase/{self.info.phase_key}',
        wo_key=wip.wo_key,
        batch_key=wip.batch_key,
        product_key=wip.product_key,
        quantity=quantity,
        value=wip.quantity * unbooking_percentage,
        active=True
      )
      self.tx.collection('wip').insert(new_wip)
      quantity = 0
      break

  if quantity > 0:
    raise WipNotAvailableError(f"Not enough booked wip available to unbook. Needed { quantity } more")

  # Update input availability for jobs in this phase
  self.update_wip_availability_for_phases(phase_keys=[self.info.phase_key])


def update_wip_availability_for_phases(self, phase_keys: list[str]):
  self.tx.aql.execute(
    TraceabilityQueries.UPDATE_NEXT_BATCH_AVAILABLE_STATE_FOR_JOBS_IN_PHASES,
    bind_vars=dict(wo_key=self.info.work_order_key, phase_keys=phase_keys)
  )