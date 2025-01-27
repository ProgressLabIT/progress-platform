from robot.api.deco import keyword
from commons.Event import Event
from utils.api_manager import APIManager
from datetime import datetime


class CollaborationsEvents(Event):


  @keyword('Product Issue created event')
  def product_issue_created_event(self, issue_type_key, product_key, operation_key, phase_key, critical = False, issue_data = [], close_within = 0):
      linked_to = [
          {
              'type': 'product',
              'key': product_key
          },
          {
              'type': 'operation',
              'key': operation_key
          },
          {
              'type': 'phase',
              'key': phase_key
          }
      ]
      issue_data = {
          'issue_type_key': issue_type_key,
          'critical': critical,
          'data': issue_data,
          'created_by': 'User/'+APIManager.getInstance().getUserKey(),
          'close_within': close_within,
          'linked_to': linked_to,
      }
      event_data = {
          'event_type': "ISSUE_CREATED",
          'timestamp': datetime.now().isoformat(),
          'issue_data': issue_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Issue updated event')
  def issue_updated_event(self, issue_key, data = []):
      issue_data = {
          '_key': issue_key,
          'data': data
      }
      event_data = {
          'event_type': "ISSUE_UPDATED",
          'timestamp': datetime.now().isoformat(),
          'issue_data': issue_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Issue deleted event')
  def issue_deleted_event(self, issue_key, delete_children = False):
      issue_data = {
          '_key': issue_key,
      }
      event_data = {
          'event_type': "ISSUE_DELETED",
          'timestamp': datetime.now().isoformat(),
          'issue_data': issue_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Mark issue critical event')
  def mark_issue_critical_event(self, issue_key, critical):
      issue_data = {
          '_key': issue_key,
          'critical': critical
      }
      event_data = {
          'event_type': "ISSUE_UPDATED",
          'timestamp': datetime.now().isoformat(),
          'issue_data': issue_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Issue closed event')
  def issue_closed_event(self, issue_key):
      issue_data = {
          '_key': issue_key,
      }
      event_data = {
          'event_type': "ISSUE_CLOSED",
          'timestamp': datetime.now().isoformat(),
          'issue_data': issue_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Issue reopened event')
  def issue_reopened_event(self, issue_key, critical = False):
      issue_data = {
          '_key': issue_key,
          'critical': critical
      }
      event_data = {
          'event_type': "ISSUE_REOPENED",
          'timestamp': datetime.now().isoformat(),
          'issue_data': issue_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Message posted event')
  def message_posted_event(self, issue_key, content):
      message_data = {
          'sender': 'User/'+APIManager.getInstance().getUserKey(),
          'recipient': 'Issue/'+issue_key,
          'content': content
      }
      event_data = {
          'event_type': "MESSAGE_POSTED",
          'timestamp': datetime.now().isoformat(),
          'message_data': message_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Message updated event')
  def message_updated_event(self, message_key, issue_key, content):
      message_data = {
          '_key': message_key,
          '_id': 'message/'+message_key,
          '_from': 'User/'+APIManager.getInstance().getUserKey(),
          '_to': 'Issue/'+issue_key,
          'content': content,
          'updated': datetime.now().isoformat()
      }
      event_data = {
          'event_type': "MESSAGE_UPDATED",
          'timestamp': datetime.now().isoformat(),
          'message_data': message_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)

  @keyword('Message deleted event')
  def message_deleted_event(self, message_key, issue_key):
      message_data = {
          '_key': message_key,
          '_id': 'message/'+message_key,
          '_from': 'User/'+APIManager.getInstance().getUserKey(),
          '_to': 'Issue/'+issue_key
      }
      event_data = {
          'event_type': "MESSAGE_DELETED",
          'timestamp': datetime.now().isoformat(),
          'message_data': message_data,
          'user_key': APIManager.getInstance().getUserKey(),
          'user_session_key': APIManager.getInstance().getSessionKey()
      }
      return self.send_event(event_data)
