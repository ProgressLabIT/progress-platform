from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from managers.notification_manager import NotificationManager

class NotificationMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app
    ):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # process the request and get the response
        response = await call_next(request)
        self.notify_change(request=request)

        return response

    def notify_change(self, request: Request):
        if (request['method']=='GET'):
            return
        NotificationManager.getInstance().notifyGlobalRefresh()

