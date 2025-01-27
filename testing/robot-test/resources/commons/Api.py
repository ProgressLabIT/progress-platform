import httpx
from robot.api.deco import keyword
from utils.db import db
from utils.config import get_config
from utils.api_manager import APIManager
from datetime import datetime

class Api:

    def __init__(self) -> None:
        self.client = httpx.Client()
        self.conf = get_config()

    def post(self, api, data):
        print(data)
        response = self.client.post(self.conf.api_url+'/api/'+api, headers=APIManager.getInstance().getAuthHeader(), json=data)
        print(response)
        if (response.status_code == 401):
           return response.json()['detail']
        if (response.json()['status'] == 200):
           return response.json()['detail']
        return "cannot perfom post"

    def delete(self, api):
        response = self.client.delete(self.conf.api_url+'/api/'+api, headers=APIManager.getInstance().getAuthHeader())
        print(response)
        if (response.status_code == 401):
           return response.json()['detail']
        return "cannot perfom delete"
