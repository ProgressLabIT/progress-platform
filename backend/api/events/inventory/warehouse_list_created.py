from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.movement_planned import MovementPlannedEvent
from events.inventory.movement_completed import MovementCompletedEvent
from models.event import EventInfoModel
from models.inventory import MovementListNew, InventoryMovementReferences, MovementStatus, MovementListNewStatus

class WarehouseListCreatedEvent(BaseInventoryEvent):

  class InfoModel(EventInfoModel):
    new_movement_list: MovementListNew


  @classmethod
  def get_event_type(cls):
    return 'WAREHOUSE_LIST_CREATED'

  @classmethod
  def get_tx_collections(cls):
    return [
      'MovementList',
      'movement',
      'Serial',
      'Counter',
      'is_in_position'
    ]

  @classmethod
  def _merge_references(
    cls,
    list_references: InventoryMovementReferences,
    movement_references: InventoryMovementReferences
    ) -> InventoryMovementReferences:
    """
    Add references from list if not present in the movement.
    This implies an important assumption: movement references do NOT conflict with the list references.
    TODO: enforce consistency either at the model level or in this function.
    """

    merged = dict()
    for attr in InventoryMovementReferences.__fields__.keys():
      list_attr = getattr(list_references, attr, None)
      movement_attr = getattr(movement_references, attr, None)
      merged[attr] = movement_attr if movement_attr is not None else list_attr

    return InventoryMovementReferences(**merged)



  def apply(self):
    # ===============================================
    # Check if the list code is already used
    # ===============================================
    list_code_exists = self.tx.collection('MovementList').find(dict(code=self.info.new_movement_list.code, type=self.info.new_movement_list.type)).count()
    if list_code_exists:
      raise ValueError(
        f"List of type '{self.info.new_movement_list.type.value}' with code '{self.info.new_movement_list.code}' already exists."
      )

    # ===============================================
    # Create the list
    # ===============================================
    # Do not include movements and by_code in the list DB record
    movement_list_record = self.info.new_movement_list.model_dump(exclude={'movements', 'by_code'})
    new_list_key = self.tx.collection('MovementList').insert(movement_list_record)['_key']

    # ===============================================
    # Add product keys if by_code == True
    # ===============================================
    if self.info.new_movement_list.by_code:
      product_codes = [m.product_code for m in self.info.new_movement_list.movements]
      try:
        products_key_map = self.tx.aql.execute("""
          RETURN MERGE(
            FOR p IN Product
            FILTER p.code IN @codes
            RETURN {[p.code]: p._key}
          )""",
          bind_vars=dict(codes=product_codes)
        ).next()
      except StopIteration:
        raise ValueError("Could not find any product with the codes provided")

      for movement in self.info.new_movement_list.movements:
        product_key = products_key_map.get(movement.product_code, None)
        if product_key is None:
          raise ValueError(f"Could not find product with code {movement.product_code}")
        movement.product_key = product_key

    # ===============================================
    # Create the movements
    # ===============================================
    for m in self.info.new_movement_list.movements:
      # Build common arguments
      common_args = dict(
        movement_type = self.info.new_movement_list.type,
        serial_key = m.serial_key,
        qt_planned = m.qt_planned,
        movement_list_key = new_list_key,
        movement_list_item = m.movement_list_item,
        position_from = m.position_from,
        position_to = m.position_to,
        product_key = m.product_key,
        references = self._merge_references(list_references=self.info.new_movement_list.references, movement_references=m.references),
        extra = getattr(m, 'extra', self.info.new_movement_list.extra)
      )

      # Choose event class and add status-specific fields
      if self.info.new_movement_list.status == MovementListNewStatus.PLANNED:
        event_class = MovementPlannedEvent
        event_args = dict(**common_args, serial_code=m.serial_code, status=MovementStatus.PLANNED)
      elif self.info.new_movement_list.status == MovementListNewStatus.COMPLETED:
        event_class = MovementCompletedEvent
        event_args = dict(**common_args, qt_confirmed=m.qt_confirmed)
      else:
        # Should never happen, since MovementListNewStatus allows only PLANNED and COMPLETED
        raise ValueError(f"Invalid movement list status: {self.info.new_movement_list.status}")

      event_class.create_as_child(self, event_args)
      print("Created movement: from {m.position_from} to {m.position_to} for product {m.product_key} and serial {m.serial_key} with quantity {m.qt_confirmed}")

    self.response = new_list_key

