from events import (
  CollaborationEvent,
  InventoryEvent,
  ProductionActivityEvent,
  ProductionAdminEvent,
  SharedEventMethods,
)
from events.base import BaseEvent
from models.event import EventModel
from utils.db import db
import uuid


class Event(BaseEvent):
  """
  This class serves as collector of all event categories and as main "entrypoint" for the event API
  It abstracts the general logic of processing and saving events from the specifics defined in each
  of the classes it inherits from.

  Each inherited class includes a property named after each event type of its "category".
  Each event type (class property) is itself an EventMeta class instance which defines:
  - the list of collections to use in the transaction
  - the actions (class method) to be carried out specific to the event type
  """
  ######################################################################
  # INIT & SAVE
  ######################################################################

  def __init__(self, event: EventModel, database=db, tx=None):
    self.event_managers = {
                        'ProductionAdminEvent': ProductionAdminEvent(event=event, database=database, tx=tx),
                        'CollaborationEvent': CollaborationEvent(event=event, database=database, tx=tx),
                        'InventoryEvent': InventoryEvent(event=event, database=database, tx=tx),
                        'ProductionActivityEvent': ProductionActivityEvent(event=event, database=database, tx=tx),
                        #'SharedEventMethods': SharedEventMethods(event=event)
                     }

    # define action to be taken based on the event type
    # self.action = getattr(self, self.meta.action)

  def save(self, tx=None):
    for manager in self.event_managers.values():
      if manager.can_handle():
        manager.apply(tx=tx)

  def can_handle(self):
    for manager in self.event_managers.values():
      if manager.can_handle():
        return True
    return False


  def notify(self, event_tx: BaseEvent):

    #TODO: context have to be managed, figured it out
    event = Event(event_tx)
    event.save(tx=self.tx)


