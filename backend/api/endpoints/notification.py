from collections.abc import AsyncIterable
from fastapi import Request, APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent
from managers.server_event_manager import ServerEventManager

router = APIRouter()

@router.get("/notification/{topic}", response_class=EventSourceResponse)
async def message_stream(request: Request, topic: str) -> AsyncIterable[ServerSentEvent]:
    async for event in ServerEventManager.getInstance().push_events(request, topic):
        yield event
