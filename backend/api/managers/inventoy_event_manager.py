from models.inventory import InventoryCommandType
from fastapi.encoders import jsonable_encoder

class InventoryEventManager:
    __instance = None

    def __init__(self) -> None:
       self.event = None
       self.tx = None

    @staticmethod
    def getInstance():
      if InventoryEventManager.__instance == None:
        InventoryEventManager.__instance = InventoryEventManager()
      return InventoryEventManager.__instance


    def handle_event(self, event, event_command, **event_parameters):
      self.event = event
      self.tx = event.tx
      match event_command:
        case InventoryCommandType.ADD_MOVEMENT:
           ...
        case InventoryCommandType.UPDATE_MOVEMENT:
           ...
        case InventoryCommandType.DELETE_MOVEMENT:
           ...
        case _:
           print("Error")
