from fastapi import Request, APIRouter
from managers.server_event_manager import ServerEventManager
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware


router = APIRouter()

@router.get("/notification/{topic}")
async def message_stream(request: Request, topic: str):
    return EventSourceResponse(ServerEventManager.getInstance().push_events(request, topic))
