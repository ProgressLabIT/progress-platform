from traceback import format_exc
from fastapi import HTTPException

class HTTPError(HTTPException):
  def __init__(self, status_code: int, message: str):
    super().__init__(
      status_code=status_code,
      detail=dict(
        status=status_code,
        message=message,
        error=format_exc()
      )
    )

class UserNotFoundError(Exception): pass

class UserDisabledError(Exception): pass

class UserPasswordMismatchError(Exception): pass

class UserAlreadyLoggedInError(Exception): pass

class TokenSignatureMismatchError(Exception): pass

class TokenRevokedError(Exception): pass

class TokenExpiredError(Exception): pass

class TokenSignatureVerificationError(Exception): pass

class TokenNotFoundError(Exception): pass

class JobIsActiveError(Exception): pass

class JobIsStartedError(Exception): pass

class JobIsNotStartedError(Exception): pass

class JobHasActiveBatchError(Exception): pass

class JobHasNoAssigneeError(Exception): pass

class JobHasNoActiveBatchError(Exception): pass

class JobHasNoAssigneeError(Exception): pass

class WipNotAvailableError(Exception): pass

