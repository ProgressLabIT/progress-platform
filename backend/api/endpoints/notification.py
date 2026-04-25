from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from managers.server_event_manager import ServerEventManager
from models.auth import TokenData
from utils import auth

router = APIRouter()


class SseTicketRequest(BaseModel):
  topic: str


class SseTicketResponse(BaseModel):
  ticket: str
  expires_in: int


def _enforce_topic_access(topic: str, token_data: TokenData) -> TokenData:
  """Raise 403 if a `user:<key>` topic does not match the JWT's consumer_key.

  Split out as a plain function (not an async generator) so the raised
  HTTPException propagates cleanly through FastAPI's exception handler
  chain BEFORE the streaming response starts. Raising inside the SSE
  async generator wraps the exception in an ExceptionGroup and yields
  a 500 to the client — not what we want.
  """
  if topic.startswith("user:"):
    _, _, suffix = topic.partition(":")
    if suffix != token_data.consumer_key:
      raise HTTPException(
        status_code=403,
        detail="Forbidden: user topic does not match session user",
      )
  return token_data


@router.post("/notification/ticket", response_model=SseTicketResponse)
async def mint_ticket(
  body: SseTicketRequest,
  token_data: TokenData = Depends(auth.verify_token),
):
  """Issue a short-lived SSE ticket for the given topic.

  The caller must hold a valid session JWT (Authorization header). The
  returned ticket is scoped to the requested topic and the calling user,
  and expires in `expires_in` seconds. Pass it as `?ticket=<value>` when
  opening the SSE stream.

  For `user:<key>` topics, the caller's consumer_key must match `<key>` —
  a user cannot mint a ticket that lets them eavesdrop on another user's
  personal notification stream.
  """
  if body.topic.startswith("user:"):
    _, _, suffix = body.topic.partition(":")
    if suffix != token_data.consumer_key:
      raise HTTPException(
        status_code=403,
        detail="Forbidden: topic does not match session user",
      )
  ticket = auth.issue_sse_ticket(token_data.consumer_key, body.topic)
  return SseTicketResponse(ticket=ticket, expires_in=auth.SSE_TICKET_TTL_SECONDS)


async def _verify_stream_access(
  topic: str,
  ticket: str | None = Query(default=None),
  header_token_data: TokenData | None = Depends(auth.verify_token_optional),
) -> None:
  """Dependency that accepts either a ticket (query) or an Authorization header.

  Ticket path (preferred for browser EventSource): validates the short-lived
  scoped ticket returned by POST /notification/ticket.

  Header path (server-to-server or future header-capable clients): validates
  a full session JWT and enforces user-topic owner match.
  """
  if ticket is not None:
    auth.verify_sse_ticket(ticket, topic)
    return
  if header_token_data is not None:
    _enforce_topic_access(topic, header_token_data)
    return
  raise auth.credentials_exception


@router.get("/notification/{topic}", response_class=EventSourceResponse)
async def message_stream(
  request: Request,
  topic: str,
  _: None = Depends(_verify_stream_access),
) -> AsyncIterable[ServerSentEvent]:
  """Server-Sent Events stream for the given notification `topic`.

  Authorization rules:
    * Auth is REQUIRED. Pass either `?ticket=<short-JWT>` (issued by
      POST /notification/ticket, preferred for browser EventSource clients)
      or an `Authorization: Bearer <JWT>` header (for server-to-server).
    * For `user:<key>` topics, the caller's consumer_key MUST match `<key>`.
      The owner-match is enforced at ticket issuance; the header path checks
      it here directly.
    * Non-user topics (task, inventory, ...) require auth but are not
      owner-scoped in v1.
  """
  async for event in ServerEventManager.getInstance().push_events(request, topic):
    yield event
