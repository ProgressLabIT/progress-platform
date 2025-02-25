from robot.api.deco import keyword
from commons.Api import Api
from utils.api_manager import APIManager
from datetime import datetime


class WorkOrderAPI(Api):

    @keyword('Do create work order')
    def do_create_work_order(self, wo_code, product_key, qt_planned, start_from = datetime.now().isoformat(), due_by = datetime.now().isoformat(), project_code = None):
        workorder_data = {
            'wo_code': wo_code,
            'product_key': product_key,
            'qt_planned': qt_planned,
            'start_from': start_from,
            'due_by': due_by,
            'project_code': project_code
        }
        return self.post('work-order', workorder_data)
