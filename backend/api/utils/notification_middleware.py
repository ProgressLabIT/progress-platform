from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from utils.server_event_manager import ServerEventManager

class NotificationMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app
    ):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # do something with the request object, for example
        content_type = request.headers.get('Content-Type')
        print(content_type)

        # process the request and get the response
        response = await call_next(request)
        self.notify_change(request=request)

        return response

    def notify_change(self, request: Request):
        if (request['method']=='GET'):
            return
        ServerEventManager.getInstance().notifyGlobalRefresh()

