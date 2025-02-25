import httpx
from robot.api.deco import keyword
from utils.db import db
from utils.config import get_config
from utils.api_manager import APIManager
from datetime import datetime

class Event:

    def __init__(self) -> None:
        self.client = httpx.Client()
        self.conf = get_config()

    @keyword('Send event')
    def send_event(self, event_data):
      print(event_data)
      response = self.client.post(self.conf.api_url+'/api/event', headers=APIManager.getInstance().getAuthHeader(), json=event_data)
      print(response)
      if (response.status_code == 401):
         return response.json()['detail']
      if (response.json()['status'] == 200 and 'event_key' in response.json()['detail']):
         return response.json()['detail']
      return "cannot send event"


    if __name__ == "__main__":
      APIManager.getInstance().authenticate('http://localhost:8000', username='simone', pwd='simone')
      session_data = {
          'user_key': APIManager.getInstance().getUserKey()
        }
      client = httpx.Client()
      response = client.post('http://localhost:8000/api/session', headers=APIManager.getInstance().getAuthHeader(), json=session_data)
      print(response)

