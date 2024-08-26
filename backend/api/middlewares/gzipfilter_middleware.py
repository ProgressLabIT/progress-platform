from starlette.middleware.gzip import GZipMiddleware, GZipResponder

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class GZipFilterMiddleware(GZipMiddleware):

    def __init__(
        self, app: ASGIApp, minimum_size: int = 500, compresslevel: int = 9, filtered_api: str = None
    ) -> None:
        self.filtered_api = filtered_api
        self.app = app
        self.minimum_size = minimum_size
        self.compresslevel = compresslevel

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and self.filtered_api not in scope["path"]:
            headers = Headers(scope=scope)
            if "gzip" in headers.get("Accept-Encoding", ""):
                responder = GZipResponder(
                    self.app, self.minimum_size, compresslevel=self.compresslevel
                )
                await responder(scope, receive, send)
                return
        await self.app(scope, receive, send)
