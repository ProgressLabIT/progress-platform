from robot.api.deco import keyword
from commons.Event import Event
from utils.api_manager import APIManager
from datetime import datetime


class MovementsEvents(Event):

  # "movement":{"position_to":"Position/30199840","serial_code":"1321312","qt_planned":1,"qt_confirmed":1,"product_key":"12221058",
  # "position_from":"Position/OUT","status":"completed","type":"receipt","user_key":"29682613","start":"2025-01-28T17:22:57.914Z","end":"2025-01-28T17:22:57.914Z"}

  @keyword('Movement created event')
  def movement_created_event(self, position_to, serial_code, product_key, qt_planned=1, qt_confirmed=1, position_from='OUT', status='completed', type='receipt'):
    movement_data = {
      'position_to': 'Position/'+position_to,
      'serial_code': serial_code,
      'qt_planned': qt_planned,
      'qt_confirmed': qt_confirmed,
      'product_key': product_key,
      'position_from': 'Position/'+position_from,
      'status': status,
      'type': type,
      'user_key': APIManager.getInstance().getUserKey(),
      'start': datetime.now().isoformat(),
      'end': datetime.now().isoformat()
    }
    event_data = {
      'event_type': "MOVEMENT_CREATED",
      'user_key': APIManager.getInstance().getUserKey(),
      'user_session_key': APIManager.getInstance().getSessionKey(),
      'timestamp': datetime.now().isoformat(),
      'movement': movement_data
    }
    return self.send_event(event_data)
