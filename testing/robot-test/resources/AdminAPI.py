from robot.api.deco import keyword
from commons.Api import Api
from utils.api_manager import APIManager
from datetime import datetime


class AdminAPI(Api):

    @keyword('Force delete work order')
    def force_delete_work_order(self, wo_key):
        return self.delete('force-delete-work-order/'+wo_key)
