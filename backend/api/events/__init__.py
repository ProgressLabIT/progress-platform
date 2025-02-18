#ADMIN EVENTS
from events.admin.base_admin import BaseAdmin
from events.admin.batch_canceled import BatchCanceled
from events.admin.job_reset import JobReset
from events.admin.progress_override_requested import ProgressOverrideRequested
from events.admin.time_override_requested import TimeOverrideRequested
from events.base_event import BaseEvent

#COLLABORATION EVENTS
from events.collaboration.base_collaboration import BaseCollaboration
from events.collaboration.issue_closed import IssueClosedEvent
from events.collaboration.issue_created import IssueCreatedEvent
from events.collaboration.issue_deleted import IssueDeletedEvent
from events.collaboration.issue_reopened import IssueReopenedEvent
from events.collaboration.issue_updated import IssueUpdatedEvent
from events.collaboration.message_deleted import MessageDeletedEvent
from events.collaboration.message_posted import MessagePostedEvent
from events.collaboration.message_updated import MessageUpdatedEvent

#INVENTORY EVENTS
from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.inventory_changed import InventoryChangedEvent
from events.inventory.movement_completed import MovementCompletedEvent
from events.inventory.movement_created import MovementCreatedEvent
from events.inventory.movement_deleted import MovementDeleted
from events.inventory.movement_updated import MovementUpdated
from events.inventory.warehouse_list_closed import WarehouseListClosed
from events.inventory.warehouse_list_created import WarehouseListCreated
from events.production.active_batch_changed import ActiveBatchChangedEvent

#PRODUCTION EVENTS
from events.production.base_production import BaseProductionEvent
from events.production.batch_completed import BatchCompletedEvent
from events.production.batch_created import BatchCreatedEvent

#COMMONS
from events.production.job_back_online import JobBackOnlineEvent
from events.production.job_closed import JobClosedEvent
from events.production.job_paused import JobPausedEvent
from events.production.job_paused_offline import JobPausedOffline
from events.production.job_resumed import JobResumed
from events.production.job_started import JobStartedEvent
from events.production.step_completed import StepCompletedEvent
from events.production.step_edited import StepEdited

#SERIAL EVENTS
from events.serial.base_serial import BaseSerialEvent
from events.serial.serial_batch_confirmed import SerialBatchConfirmedEvent
from events.serial.serial_booked import SerialBooked
from events.serial.serial_created import SerialCreatedEvent
from events.serial.serial_data_updated import SerialDataUpdatedEvent
from events.serial.serial_deleted import SerialDeleted
from events.serial.serial_linked import SerialLinkedEvent
from events.serial.serial_released import SerialReleasedEvent
from events.serial.serial_updated import SerialUpdatedEvent

#WIP
from events.wip.wip_booked import WIPBookedEvent
from events.wip.wip_declared import WIPDeclaredEvent
from events.wip.wip_removed import WIPRemovedEvent
from events.wip.wip_unbooked import WIPUnbookedEvent

#Work Order
from events.work_order.base_work_order import BaseWorkOrder
from events.work_order.work_order_closed import WorkOrderClosed
from events.work_order.work_order_started import WorkOrderStarted

#Work Session
from events.work_session.work_session_canceled import WorkSessionCanceledEvent
from events.work_session.work_session_closed import WorkSessionClosedEvent
from events.work_session.work_session_created import WorkSessionCreatedEvent
from utils.event import register_event_class

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

