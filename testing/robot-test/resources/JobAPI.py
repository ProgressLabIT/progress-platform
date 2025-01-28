from robot.api.deco import keyword
from commons.Api import Api
from utils.api_manager import APIManager
from datetime import datetime


class JobAPI(Api):


    @keyword('Do assign job')
    def do_assign_job(self,  job_key, assign_to, qt_planned):
        data = {
            '_key': job_key,
            'assigned_to': assign_to,
            'qt_planned': qt_planned,
            'notes': 'test'
        }
        job_data = {
            'action': 'update',
            'data': data
        }
        return self.post('job/update', [job_data])
