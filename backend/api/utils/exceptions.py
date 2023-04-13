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

class JobHasActiveBatchError(Exception): pass

class JobHasNoAssigneeError(Exception): pass

class WipNotAvailableError(Exception): pass

