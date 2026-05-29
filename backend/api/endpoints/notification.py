from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from managers.server_event_manager import ServerEventManager
from models.auth import TokenData
from utils import auth

router = APIRouter()


class SseTicketRequest(BaseModel):
  topic: str | None = Field(
    default=None,
    description="Single NATS / SSE topic the caller wants to subscribe to (e.g. `user:user42`, `task`, `inventory`). Legacy single-topic path — provide either this or `topics`.",
    examples=["user:user42"],
  )
  topics: list[str] | None = Field(
    default=None,
    description="Set of topics for a multiplexed stream (one EventSource carrying every subscribed topic). Provide either this or `topic`.",
    examples=[["task", "message", "user:user42"]],
  )


class SseTicketResponse(BaseModel):
  ticket: str = Field(
    ...,
    description="Short-lived signed JWT scoped to the requested topic. Pass as `?ticket=<value>` when opening the SSE stream.",
    examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyNDIiLCJ0b3BpYyI6InVzZXI6dXNlcjQyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"],
  )
  expires_in: int = Field(
    ...,
    description="Number of seconds until the ticket expires.",
    examples=[60],
  )


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


@router.post(
  "/notification/ticket",
  response_model=SseTicketResponse,
  responses={
    401: {"description": "Missing or invalid session JWT"},
    403: {"description": "Caller's consumer_key does not match the requested user:<key> topic"},
  },
)
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
  personal notification stream. This holds for every topic in a `topics` set.

  Provide exactly one of `topic` (legacy single-topic stream) or `topics`
  (multiplexed stream).

  **Emits:** *(SSE stream — emits are downstream NATS subjects)*

  **Required scope:** `notification:stream:subscribe`
  """
  if (body.topic is None) == (body.topics is None):
    raise HTTPException(
      status_code=422,
      detail="Provide exactly one of `topic` or `topics`.",
    )

  if body.topics is not None:
    if not body.topics:
      raise HTTPException(status_code=422, detail="`topics` must be non-empty.")
    for topic in body.topics:
      _enforce_topic_access(topic, token_data)
    ticket = auth.issue_sse_ticket_multi(token_data.consumer_key, body.topics)
  else:
    _enforce_topic_access(body.topic, token_data)
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


async def _verify_multi_stream_access(
  topics: str = Query(
    ...,
    description="Comma-separated set of topics to multiplex over this one stream (e.g. `task,message,user:user42`).",
    examples=["task,message,user:user42"],
  ),
  ticket: str | None = Query(default=None),
  header_token_data: TokenData | None = Depends(auth.verify_token_optional),
) -> list[str]:
  """Parse + authorize the requested topic set BEFORE the SSE stream starts.

  Returning the parsed topic list (and raising here, in a dependency, rather
  than inside the streaming async generator) keeps 401/403/422 responses clean
  — raising inside the generator would wrap the error and yield a 500.
  """
  topic_list = [t for t in (topics.split(",") if topics else []) if t]
  if not topic_list:
    raise HTTPException(
      status_code=422,
      detail="`topics` must be a non-empty comma-separated list.",
    )

  if ticket is not None:
    auth.verify_sse_ticket_multi(ticket, topic_list)
  elif header_token_data is not None:
    for topic in topic_list:
      _enforce_topic_access(topic, header_token_data)
  else:
    raise auth.credentials_exception

  return topic_list


@router.get(
  "/notification/stream",
  response_class=EventSourceResponse,
  responses={
    401: {"description": "No valid ticket or Authorization header provided"},
    403: {"description": "Ticket or JWT consumer_key does not match a requested user:<key> topic"},
    422: {"description": "`topics` query param missing or empty"},
  },
)
async def multi_stream(
  request: Request,
  topic_list: list[str] = Depends(_verify_multi_stream_access),
) -> AsyncIterable[ServerSentEvent]:
  """Multiplexed Server-Sent Events stream for a SET of topics.

  One browser tab opens ONE EventSource here carrying every topic it cares
  about, instead of one connection per topic — which otherwise exhausts the
  browser's per-host HTTP/1.1 connection budget the moment a second tab opens.

  Authorization (in `_verify_multi_stream_access`) mirrors the single-topic
  stream, applied to every topic:
    * Ticket path (preferred, browser EventSource): `?ticket=<jwt>` from
      POST /notification/ticket with a `topics` body. The ticket's granted
      topics must cover every requested topic.
    * Header path (server-to-server): `Authorization: Bearer <JWT>`; each
      `user:<key>` topic must match the caller's consumer_key.

  Emitted events keep the same `event: <topic>` name as /notification/{topic},
  so clients route them per topic with no payload change.

  **Emits:** *(SSE stream — emits are downstream NATS subjects)*

  **Required scope:** `notification:stream:subscribe`
  """
  async for event in ServerEventManager.getInstance().push_events_multi(request, topic_list):
    yield event


@router.get(
  "/notification/{topic}",
  response_class=EventSourceResponse,
  responses={
    401: {"description": "No valid ticket or Authorization header provided"},
    403: {"description": "Ticket or JWT consumer_key does not match the requested user:<key> topic"},
  },
)
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

  **Emits:** *(SSE stream — emits are downstream NATS subjects)*

  **Required scope:** `notification:stream:subscribe`
  """
  async for event in ServerEventManager.getInstance().push_events(request, topic):
    yield event
