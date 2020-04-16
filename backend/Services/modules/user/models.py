from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from utils.base_models import FlexModel

class UserCredentials(FlexModel):
  username: str = None
  psw: str = None


class UserRoles(BaseModel):
  admin: bool = False
  operator: bool = False
  manager: bool = False


class User(FlexModel):
  id: str = Field(None, alias="_id")
  active = True
  name: str = None
  surname: str = None
  # pic: str = None
  roles: UserRoles = UserRoles()
  last_user_session: str = None
  logged_in: bool = False



