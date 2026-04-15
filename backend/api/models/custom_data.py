import re
from typing import Any

from pydantic import field_validator

from models.base_models import ArangoDocument

KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
KEY_MAX_LENGTH = 64


class CustomData(ArangoDocument):
    value: Any
    description: str | None = None

    @field_validator('key', mode='before', check_fields=False)
    @classmethod
    def validate_key(cls, v):
        if v is not None:
            if not KEY_PATTERN.match(v):
                raise ValueError(
                    'Key must start with a lowercase letter and contain only lowercase letters, digits, and underscores'
                )
            if len(v) > KEY_MAX_LENGTH:
                raise ValueError(f'Key must be at most {KEY_MAX_LENGTH} characters')
        return v
