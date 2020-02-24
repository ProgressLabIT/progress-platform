from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from ..models import FlexModel

class UserCredentials(FlexModel):
  login: str = None
  psw: str = None

class User(UserCredentials):
	id: str = Field(None, alias="_id")
	name: str = None
	surname: str = None
	pic: str = None


