
from utils.api_auth_manager import APIAuthManager
from utils.db import db
from utils import config
from utils import models
import httpx

class WorkOrderManager:

    def __init__(self) -> None:
        self.client = httpx.Client()
        self.conf = config.get_config()

    def create_work_order(self,  product_code, wo_code, product_key, qt_planned):
        models.work_order_post


    #TEST
    if __name__ == "__main__":
        model = models.work_order_post
        model['wo_code'] = 'stocazzo'
        model['qt_planned'] = 12
