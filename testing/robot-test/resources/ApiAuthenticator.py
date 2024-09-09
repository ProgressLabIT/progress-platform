import httpx
from robot.api.deco import keyword
from utils.api_auth_manager import APIAuthManager

class ApiAuthenticator:
    def __init__(self) -> None:
        self.client = httpx.Client()

    @keyword('Authenticate user')
    def authenticate_user(self, username, password):
        return APIAuthManager.getInstance().authenticate('http://localhost:8000', username=username, pwd=password)

    def get_logged_user_key(self):
      try:
        response = self.client.get('http://localhost:8000/api/whoami', headers=APIAuthManager.getInstance().getAuthHeader())
        if (response.json()['status'] == 200):
           return response.json()['detail']['user_key']
        return "unrecognized"
      except ValueError:
         return "no token defined"

    def get_loggeg_user_from_key(self, user_key):
       try:
          user = User(**db.collection('User').get(user_key))
          return user
       except:
         return "user not found"

