import httpx
from robot.api.deco import keyword
from utils.api_auth_manager import APIAuthManager
from utils.db import db
from utils import config

class ApiAuthenticator:
    def __init__(self) -> None:
        self.client = httpx.Client()
        self.conf = config.get_config()

    @keyword('Authenticate user')
    def authenticate_user(self, username, password):
        return APIAuthManager.getInstance().authenticate(self.conf.api_url, username=username, pwd=password)

    def get_logged_user_key(self):
      try:
        response = self.client.get(self.conf.api_url+'/api/whoami', headers=APIAuthManager.getInstance().getAuthHeader())
        if (response.json()['status'] == 200):
           return response.json()['detail']['user_key']
        return "unrecognized"
      except ValueError:
         return "no token defined"

    def get_logged_username_from_key(self, user_key):
       try:
          user = db.collection('User').get(user_key)
          return user['username']
       except:
         return "user not found"

    if __name__ == "__main__":
      user = db.collection('User').get('29212414')
      print(user['username'])

