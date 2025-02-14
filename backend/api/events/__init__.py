from utils.event import register_event_class

from events.base_event import BaseEvent

#COLLABORATION EVENTS
from events.collaboration.base_collaboration import BaseCollaboration
from events.collaboration.issue_created import IssueCreated
from events.collaboration.issue_updated import IssueUpdated
from events.collaboration.issue_closed import IssueClosed
from events.collaboration.issue_reopened import IssueReopened
from events.collaboration.issue_deleted import IssueDeleted
from events.collaboration.message_posted import MessagePosted
from events.collaboration.message_updated import MessageUpdated
from events.collaboration.message_deleted import MessageDeleted

#ADMIN EVENTS
from events.admin.base_admin import BaseAdmin
from events.admin.time_override_requested import TimeOverrideRequested
from events.admin.progress_override_requested import ProgressOverrideRequested
from events.admin.batch_canceled import BatchCanceled
from events.admin.job_reset import JobReset

#SERIAL EVENTS
from events.serial.base_serial import BaseSerialEvent
from events.serial.serial_created import SerialCreatedEvent
from events.serial.serial_updated import SerialUpdatedEvent
from events.serial.serial_deleted import SerialDeleted
from events.serial.serial_linked import SerialLinked
from events.serial.serial_batch_confirmed import SerialBatchConfirmedEvent
from events.serial.serial_booked import SerialBooked
from events.serial.serial_data_updated import SerialDataUpdatedEvent
from events.serial.serial_released import SerialReleasedEvent


#INVENTORY EVENTS
from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.movement_created import MovementCreatedEvent
from events.inventory.movement_updated import MovementUpdated
from events.inventory.movement_deleted import MovementDeleted
from events.inventory.movement_completed import MovementCompletedEvent
from events.inventory.warehouse_list_created import WarehouseListCreated
from events.inventory.warehouse_list_closed import WarehouseListClosed
from events.inventory.inventory_changed import InventoryChangedEvent

#PRODUCTION EVENTS
from events.production.base_production import BaseProductionEvent
from events.production.job_started import JobStartedEvent
from events.production.job_paused import JobPausedEvent
from events.production.job_paused_offline import JobPausedOffline
from events.production.job_resumed import JobResumed
from events.production.job_back_online import JobBackOnlineEvent
from events.production.active_batch_changed import ActiveBatchChangedEvent
from events.production.step_completed import StepCompletedEvent
from events.production.step_edited import StepEdited
from events.production.batch_completed import BatchCompletedEvent

#COMMONS
from events.production.commons.batch import Batch
from events.production.commons.job import Job
from events.production.commons.serial import Serial


#WIP
from events.wip.base_wip import BaseWIP
from events.wip.wip_booked import WIPBooked
from events.wip.wip_unbooked import WIPUnbooked
from events.wip.wip_declared import WIPDeclared
from events.wip.wip_removed import WIPRemoved

#Work Order
from events.work_order.base_work_order import BaseWorkOrder
from events.work_order.work_order_started import WorkOrderStarted
from events.work_order.work_order_closed import WorkOrderClosed

#Work Session
from events.work_session.base_work_session import BaseWorkSession
from events.work_session.work_session_started import WorkSessionStartedEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from events.work_session.work_session_canceled import WorkSessionCanceledEvent

#Batch
from events.batch.base_batch import BaseBatchEvent
from events.batch.batch_created import BatchCreatedEvent


# Get all classes defined in this module's namespace
all_classes = list(locals().values())

# Filter for classes that inherit from BaseEvent and have event_type property
for cls in all_classes:
  if (isinstance(cls, type) and  # Check if it's a class
    issubclass(cls, BaseEvent) and  # Check if it inherits from BaseEvent
    cls != BaseEvent and  # Skip the base class itself
    hasattr(cls, 'get_event_type')):  # Has get_event_type method
    # Register the event class with its type
    register_event_class(cls.get_event_type(), cls)

