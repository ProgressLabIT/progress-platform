from models.event import EventModel
from arango.database import StandardDatabase, TransactionDatabase

class BaseEvent:
  db: StandardDatabase
  tx: TransactionDatabase
  info: EventModel
  response: int | str | dict | list
