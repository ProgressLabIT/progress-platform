from robot.api.deco import keyword
from commons.Event import Event
from utils.api_manager import APIManager
from datetime import datetime


class SerialsEvents(Event):

  @keyword('Serial created event')
  def serial_created_event(self, product_key, counter_key, data = None):
      serial_data = {
          'created_by': 'User/'+APIManager.getInstance().getUserKey(),
          'product_key': product_key,
          'counter_key': counter_key,
          'user_key': APIManager.getInstance().getUserKey(),
          'data': []
      }
      event_data = {
          'event_type': "SERIAL_CREATED",
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'timestamp': datetime.now().isoformat(),
          'serial_data': serial_data
      }
      return self.send_event(event_data)

  @keyword('Serial updated event')
  def serial_updated_event(self, serial_key, data = None):
      serial_data = {
          '_key': serial_key,
          'data': []
      }
      event_data = {
          'event_type': "SERIAL_DELETED",
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'timestamp': datetime.now().isoformat(),
          'serial_data': serial_data
      }
      return self.send_event(event_data)

  @keyword('Serial deleted event')
  def serial_deleted_event(self, serial_key, delete_children = False):
      serial_data = {
          '_key': serial_key,
      }
      event_data = {
          'event_type': "SERIAL_DELETED",
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey(),
          'timestamp': datetime.now().isoformat(),
          'delete_children': delete_children,
          'serial_data': serial_data
      }
      return self.send_event(event_data)
