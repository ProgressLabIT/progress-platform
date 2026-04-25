import secrets
import traceback
from time import time

import jwt
from arango.exceptions import DocumentGetError, DocumentUpdateError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from starlette import status

from models.auth import *
from models.org import User
from utils.config import get_config
from utils.db import db
from utils.exceptions import *

import functools
import itertools
from typing import Any

from fastapi import Depends, HTTPException
from starlette.status import HTTP_403_FORBIDDEN


scopes_description = {
  "admin": "User can access and edit users and system settings",
  # "admin.users": "User can read and modify data about other users",
  "library": "User can access and edit products",
  # "lib:r": "User can read library data such as products, processes and bills of materials",
  # "lib:w": "User can read, add, modify and delete library data such as products, processes and bills of materials",
  "production": "User can access and edit production plans",
  # "prod:r": "User can read production plans, job queues, and work order details",
  # "prod:w": "User can read, add, modify and delete data related to production plans, job queues and work orders",
  "operator": "User can access the operator panel and make production declarations"
}

ALGORITHM = "HS256"

bearer_token = OAuth2PasswordBearer(tokenUrl="/api/auth", scopes=scopes_description)

# Optional bearer — returns None when header is absent instead of raising.
# Used by endpoints that accept both a ticket (query) and a header token.
_bearer_token_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth", scopes=scopes_description, auto_error=False
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

debugging_info = dict(
  message="Could not validate credentials.",
  stacktrace=traceback.format_exc()
)

credentials_exception = HTTPException(
  status_code=status.HTTP_401_UNAUTHORIZED,
  detail=debugging_info,
  headers={"WWW-Authenticate": "Bearer"},
)

Allow = "Allow"  # acl "allow" action
Deny = "Deny"  # acl "deny" action

Everyone = "system:everyone"  # user principal for everyone
Authenticated = "system:authenticated"  # authenticated user principal


class _AllPermissions:
    """ special container class for the all permissions constant

    first try was to override the __contains__ method of a str instance,
    but it turns out to be readonly...
    """

    def __contains__(self, other):
        """ returns alway true any permission """
        return True

    def __str__(self):
        """ string representation """
        return "permissions:*"


All = _AllPermissions()


DENY_ALL = (Deny, Everyone, All)  # acl shorthand, denies anything
ALOW_ALL = (Allow, Everyone, All)  # acl shorthand, allows everything


# the exception that will be raised, if no sufficient permissions are found
# can be configured in the configure_permissions() function
permission_exception = HTTPException(
    status_code=HTTP_403_FORBIDDEN,
    detail="Insufficient permissions",
    headers={"WWW-Authenticate": "Bearer"},
)


def configure_permissions(
    active_principals_func: Any,
    permission_exception: HTTPException = permission_exception,
):
    """ sets the basic configuration for the permissions system

    active_principals_func:
        a dependency that returns the principals of the current active user
    permission_exception:
        the exception used if a permission is denied

    returns: permission_dependency_factory function,
             with some parameters already provisioned
    """
    active_principals_func = Depends(active_principals_func)

    return functools.partial(
        permission_dependency_factory,
        active_principals_func=active_principals_func,
        permission_exception=permission_exception,
    )


def permission_dependency_factory(
    permission: str,
    resource: Any,
    active_principals_func: Any,
    permission_exception: HTTPException,
):
    """ returns a function that acts as a dependable for checking permissions

    This is the actual function used for creating the permission dependency,
    with the help of fucntools.partial in the "configure_permissions()"
    function.

    permission:
        the permission to check
    resource:
        the resource that will be accessed
    active_principals_func (provisioned  by configure_permissions):
        a dependency that returns the principals of the current active user
    permission_exception (provisioned  by configure_permissions):
        exception if permission is denied

    returns: dependency function for "Depends()"
    """
    if callable(resource):
        dependable_resource = Depends(resource)
    else:
        dependable_resource = Depends(lambda: resource)

    # to get the caller signature right, we need to add only the resource and
    # user dependable in the definition
    # the permission itself is available through the outer function scope
    def permission_dependency(
        resource=dependable_resource, principals=active_principals_func
    ):
        if has_permission(principals, permission, resource):
            return resource
        raise permission_exception

    return Depends(permission_dependency)


def has_permission(
    user_principals: list, requested_permission: str, resource: Any
):
    """ checks if a user has the permission for a resource

    The order of the function parameters can be remembered like "Joe eat apple"

    user_principals: the principals of a user
    requested_permission: the permission that should be checked
    resource: the object the user wants to access, must provide an ACL

    returns bool: permission granted or denied
    """
    acl = normalize_acl(resource)

    for action, principal, permissions in acl:
        if isinstance(permissions, str):
            permissions = {permissions}
        if requested_permission in permissions:
            if principal in user_principals:
                return action == Allow
    return False


def list_permissions(user_principals: list, resource: Any):
    """ lists all permissions of a user for a resouce

    user_principals: the principals of a user
    resource: the object the user wants to access, must provide an ACL

    returns dict: every available permission of the resource as key
                  and True / False as value if the permission is granted.
    """
    acl = normalize_acl(resource)

    acl_permissions = (permissions for _, _, permissions in acl)
    as_iterables = ({p} if not is_like_list(p) else p for p in acl_permissions)
    permissions = set(itertools.chain.from_iterable(as_iterables))

    return {
        str(p): has_permission(user_principals, p, acl) for p in permissions
    }


# utility functions


def normalize_acl(resource: Any):
    """ returns the access controll list for a resource

    If the resource is not an acl list itself it needs to have an "__acl__"
    attribute. If the "__acl__" attribute is a callable, it will be called and
    the result of the call returned.

    An existing __acl__ attribute takes precedence before checking if it is an
    iterable.
    """
    acl = getattr(resource, "__acl__", None)
    if callable(acl):
        return acl()
    elif acl is not None:
        return acl
    elif is_like_list(resource):
        return resource
    return []


def is_like_list(something):
    """ checks if something is iterable but not a string """
    if isinstance(something, str):
        return False
    return hasattr(something, "__iter__")

# ----------------------------------------------------------------------

def get_password_hash(password):
    return pwd_context.hash(password)

# ----------------------------------------------------------------------

def verify_password(plain_password, hashed_password):
  return pwd_context.verify(plain_password, hashed_password)


# ----------------------------------------------------------------------

def _verify_token_base(token_str: str) -> TokenData:
  """Verify JWT signature, DB record, and revocation. Raises credentials_exception on any failure."""
  try:
    try:
      token_json = jwt.decode(token_str, get_config().jwt_secret, algorithms=[ALGORITHM])

    except jwt.ExpiredSignatureError:
      print('Token expired')
      raise TokenExpiredError

    except jwt.InvalidSignatureError:
      print('TokenSignatureVerificationError')
      raise TokenSignatureVerificationError

    except:
      raise Exception(traceback.format_exc())

    try:
      token_data = TokenData(**token_json)
    except:
      raise Exception(traceback.format_exc())

    try:
      token_record = TokenRecord( **db.collection('Token').get(token_data.token_key) )
    except:
      print('TokenNotFoundError')
      raise TokenNotFoundError

    if not token_str.split('.')[-1] == token_record.signature:
      print('TokenSignatureMismatchError')
      raise TokenSignatureMismatchError

    if token_record.revoked:
      print('TokenRevokedError')
      raise TokenRevokedError

  except Exception as e:
    print(e)
    traceback.print_exc()
    raise credentials_exception

  return token_data


def verify_token(token_str: str = Depends(bearer_token)):
  """Verify JWT from Authorization header. Raises 401 if absent or invalid."""
  token_data = _verify_token_base(token_str)
  if token_data.context == TokenContext.API:
    raise credentials_exception  # Service tokens cannot use user endpoints
  if token_data.context == TokenContext.SSE_TICKET:
    raise credentials_exception  # SSE tickets cannot be used on normal endpoints
  return token_data


def verify_token_optional(
  header_token: str | None = Depends(_bearer_token_optional),
) -> "TokenData | None":
  """Verify JWT from Authorization header; return None when header is absent."""
  if not header_token:
    return None
  token_data = _verify_token_base(header_token)
  if token_data.context in (TokenContext.API, TokenContext.SSE_TICKET):
    return None
  return token_data


# SSE ticket TTL — short enough that a leaked ticket in access logs is
# harmless before anyone could act on it; long enough for native EventSource
# built-in reconnect backoff to succeed without needing a new ticket.
SSE_TICKET_TTL_SECONDS = 90


def issue_sse_ticket(consumer_key: str, topic: str) -> str:
  """Mint a short-lived, topic-scoped, stateless SSE ticket (signed JWT)."""
  now = datetime.utcnow()
  claims = {
    "sub": consumer_key,
    "topic": topic,
    "ctx": TokenContext.SSE_TICKET.value,
    "iat": now,
    "exp": now + timedelta(seconds=SSE_TICKET_TTL_SECONDS),
  }
  return jwt.encode(claims, get_config().jwt_secret, algorithm=ALGORITHM)


def verify_sse_ticket(ticket: str, path_topic: str) -> str:
  """Validate an SSE ticket. Returns consumer_key; raises 401 on any failure."""
  try:
    payload = jwt.decode(ticket, get_config().jwt_secret, algorithms=[ALGORITHM])
  except Exception:
    raise credentials_exception
  if payload.get("ctx") != TokenContext.SSE_TICKET.value:
    raise credentials_exception
  if payload.get("topic") != path_topic:
    raise credentials_exception
  sub = payload.get("sub")
  if not sub:
    raise credentials_exception
  return sub


def verify_print_service_token(token_str: str = Depends(bearer_token)):
  token_data = _verify_token_base(token_str)
  # The print service authenticates via POST /api/auth (OAuth2 password grant),
  # which always issues USER_SESSION context tokens — there is no separate service
  # account token context. The scope check below is the primary guard; the context
  # check here ensures API-context tokens (future service tokens) are rejected.
  if token_data.context != TokenContext.USER_SESSION:
    raise credentials_exception
  if "print_service" not in (token_data.scope or "").split():
    raise credentials_exception
  return token_data

# ----------------------------------------------------------------------

def revoke_token(token_key, db=db):
  try:
    db.collection('Token').update(dict(_key=token_key, revoked=True))
  except DocumentUpdateError:
    pass
  except:
    traceback.print_exc()
    print(vars())

# ----------------------------------------------------------------------


def issue_token(
  consumer_key: str,
  seconds_until_expired: int | None = None,
  expiration_date: datetime | None = None,
  scope: str | None = None,
  consumer_type: ConsumerType = ConsumerType.USER,
  context: TokenContext = TokenContext.USER_SESSION,
):
  now = datetime.utcnow()
  token_key = secrets.token_hex(6)
  access_token_data = TokenData(
    token_key = token_key,
    consumer_key = consumer_key,
    consumer_type = consumer_type,
    context = context,
    scope = scope,
    issued_at = now,
    expires_at = now + timedelta(seconds=seconds_until_expired) if seconds_until_expired != None else expiration_date
  )

  access_token = jwt.encode(
    access_token_data.dict(by_alias=True, exclude_none=True),
    get_config().jwt_secret,
    algorithm=ALGORITHM
  )

  return access_token, access_token_data


# ----------------------------------------------------------------------


def verify_user(password, username=None, user_key=None, db=db):
  # Verify User exists in DB
  try:
    if username:
      user = User( **db.collection('User').find(dict(username=username)).next() )

    elif user_key:
      user = User( **db.collection('User').get(user_key) )

    else:
      raise TypeError('Username or user key must be provided')

    #Verify use is enabled
    if not user.active or user.trash:
      raise UserDisabledError

    # Verify password
    if not verify_password(password, user.psw_hash):
      raise UserPasswordMismatchError

    return user

  except StopIteration:
    raise UserNotFoundError

  except DocumentGetError:
    raise UserNotFoundError

  except Exception as e:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message="Error while validating credentials.",
          error=e,
          stacktrace=traceback.format_exc()
        ),
      )
# ----------------------------------------------------------------------

def close_session(session_key, token_key, db=db):
  try:
    tx = db.begin_transaction(write=['Token', 'UserSession'])

    session_update = dict(
      _key=session_key,
      active=False,
      logout_at=datetime.now(tz.UTC)
    )
    tx.collection('UserSession').update(session_update, return_new=True)['new']
    revoke_token(token_key, tx)
    tx.commit_transaction()
  except Exception:
    tx.abort_transaction()



class Queries:

  INSERT_USER_SESSION = """
    FOR u IN User
      FILTER u._key == @user_key
      LET session_data = {
        active: true,
        token_key: @token_key,
        user_key: u._key,
        login_at: DATE_ISO8601(DATE_NOW()),
        logout_at: null,
        scope: u.scope,
        name: u.name,
        surname: u.surname
      }
      INSERT session_data IN UserSession RETURN NEW
  """

Permission = configure_permissions(verify_token)
