from enum import Enum
from collections import namedtuple

EventTypeDef = namedtuple('EventTypeDef', ['type', 'class_name'])

class EventType(Enum):

  @property
  def displayString(self):
    return self.value.type

  # Production Events
  JOB_STARTED =  EventTypeDef('JOB_STARTED', "JobStarted")
  JOB_PAUSED =  EventTypeDef('JOB_PAUSED', "JobPaused")
  JOB_PAUSED_OFFLINE =  EventTypeDef('JOB_PAUSED_OFFLINE', "JobPausedOffline")
  JOB_RESUMED =  EventTypeDef('JOB_RESUMED', "JobResumed")
  JOB_BACK_ONLINE =  EventTypeDef('JOB_BACK_ONLINE', "JobBackOnline")
  ACTIVE_BATCH_CHANGED = EventTypeDef('ACTIVE_BATCH_CHANGED', "ActiveBatchChanged")
  STEP_COMPLETED =  EventTypeDef('STEP_COMPLETED', "StepCompleted")
  STEP_EDITED =  EventTypeDef('STEP_EDITED', "StepEdited")
  BATCH_COMPLETED =  EventTypeDef('BATCH_COMPLETED', "BatchCompleted")

  # Issue Events
  ISSUE_CREATED = EventTypeDef('ISSUE_CREATED', "IssueCreated")
  ISSUE_UPDATED = EventTypeDef('ISSUE_UPDATED', "IssueUpdated")
  ISSUE_CLOSED = EventTypeDef('ISSUE_CLOSED', "IssueClosed")
  ISSUE_REOPENED = EventTypeDef('ISSUE_REOPENED', "IssueReopened")
  ISSUE_DELETED = EventTypeDef('ISSUE_DELETED', "IssueDeleted")
  MESSAGE_POSTED = EventTypeDef('MESSAGE_POSTED', "MessagePosted")
  MESSAGE_UPDATED = EventTypeDef('MESSAGE_UPDATED', "MessageUpdated")
  MESSAGE_DELETED = EventTypeDef('MESSAGE_DELETED', "MessageDeleted")

  # Admin Events
  # e.g. WorkSession time Forced, etc.
  TIME_OVERRIDE_REQUESTED = EventTypeDef('TIME_OVERRIDE_REQUESTED', "TimeOverrideRequested")
  PROGRESS_OVERRIDE_REQUESTED = EventTypeDef('PROGRESS_OVERRIDE_REQUESTED', "ProgressOverrideRequested")
  #BATCH_CANCELED = EventTypeDef('BATCH_CANCELED', "BatchCanceled")
  #STEP_CANCELED = 'STEP_CANCELED'
  JOB_RESET = EventTypeDef('JOB_RESET', "JobReset")
  ##STEP_MODIFIED = 'STEP_MODIFIED'
#
  ## Serial Events
  SERIAL_CREATED = EventTypeDef('SERIAL_CREATED', "SerialCreated")
  SERIAL_UPDATED = EventTypeDef('SERIAL_UPDATED', "SerialUpdated")
  SERIAL_DELETED = EventTypeDef('SERIAL_DELETED', "SerialDeleted")
  SERIAL_LINKED = EventTypeDef('SERIAL_LINKED', "SerialLinked")
  SERIAL_BATCH_CONFIRMED = EventTypeDef('SERIAL_BATCH_CONFIRMED','SerialBatchConfirmed')
  SERIAL_BOOKED = EventTypeDef('SERIAL_BOOKED','SerialBooked')
  SERIAL_DATA_UPDATED = EventTypeDef('SERIAL_DATA_UPDATED','SerialDataUpdated')
  SERIAL_RELEASED = EventTypeDef('SERIAL_RELEASED','SerialReleased')

#
#
  ##Inventory Events
  MOVEMENT_CREATED = EventTypeDef('MOVEMENT_CREATED', "MovementCreated")
  MOVEMENT_UPDATED = EventTypeDef('MOVEMENT_UPDATED', "MovementUpdated")
  MOVEMENT_DELETED = EventTypeDef('MOVEMENT_DELETED', "MovementDeleted")
  MOVEMENT_COMPLETED = EventTypeDef('MOVEMENT_COMPLETED', "MovementCompleted")
  WAREHOUSE_LIST_CREATED = EventTypeDef('WAREHOUSE_LIST_CREATED', "WarehouseListCreated")
  WAREHOUSE_LIST_CLOSED = EventTypeDef('WAREHOUSE_LIST_CLOSED', "WarehouseListClosed")
  INVENTORY_PRODUCED = EventTypeDef('INVENTORY_PRODUCED', "InventoryProduced")
  INVENTORY_CONSUMED = EventTypeDef('INVENTORY_CONSUMED', "InventoryConsumed")

  #Work Order
  WORK_ORDER_STARTED = EventTypeDef('WORK_ORDER_STARTED', "WorkOrderStarted")
  WORK_ORDER_CLOSED = EventTypeDef('WORK_ORDER_CLOSED', "WorkOrderClosed")

  #Work Session
  WORK_SESSION_STARTED = EventTypeDef('WORK_SESSION_STARTED', "WorkSessionStarted")
  WORK_SESSION_CLOSED = EventTypeDef('WORK_SESSION_CLOSED', "WorkSessionClosed")
  WORK_SESSION_CREATED = EventTypeDef('WORK_SESSION_CREATED', "WorkSessionCreated")
  WORK_SESSION_CANCELED = EventTypeDef('WORK_SESSION_CANCELED', "WorkSessionCanceled")

  #WIP
  WIP_BOOKED = EventTypeDef('WIP_BOOKED', "WIPBooked")
  WIP_UNBOOKED = EventTypeDef('WIP_UNBOOKED', "WIPUnbooked")
  WIP_REMOVED = EventTypeDef('WIP_REMOVED', "WIPRemoved")
  WIP_DECLARED = EventTypeDef('WIP_DECLARED', "WIPDeclared")
  #Batch
  BATCH_CREATED = EventTypeDef('BATCH_CREATED', "BatchCreated")
  BATCH_CANCELED = EventTypeDef('BATCH_CANCELED', "BatchCanceled")
