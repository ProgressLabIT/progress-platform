import httpx

class APIAuthManager:
    __instance = None

    def __init__(self):
       self.base_url = None
       self.token = None
       self.user_key = None

    @staticmethod
    def getInstance():
      if APIAuthManager.__instance == None:
        APIAuthManager.__instance = APIAuthManager()
      return APIAuthManager.__instance

    def getAuthHeader(self):
        if (self.token!=None):
            headers = {
                'Authorization': 'Bearer '+self.token
                }
            return headers
        raise ValueError("token not found: make sure to login first")

    def getUserKey(self):
        if (self.user_key!=None):
            return self.user_key
        raise ValueError("user key not found: make sure to login first")

    def authenticate(self, base_url, username = '', pwd = '', grant_type = '', scope = '', client_id = '', client_secret = ''):
        self.base_url = base_url
        auth_data = {
        'username': username,
        'password': pwd
        }

        response = httpx.post(self.base_url+'/api/auth', data=auth_data)
        response_json = response.json()

        if response_json != None and 'status' in response_json and response_json['status'] == 200:
            self.token = response_json['access_token']
            self.user_key = response_json['detail']['user_key']
        else:
          raise SystemError("Cannot perform login: "+str(response_json['detail']))


