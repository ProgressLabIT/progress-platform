import re
from typing import Any

from pydantic import Field, field_validator

from models.base_models import ArangoDocument

KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
KEY_MAX_LENGTH = 64


class CustomData(ArangoDocument):
    value: Any = Field(
        ...,
        description=(
            "The stored value for this custom-data entry. Can be any JSON-serialisable type "
            "(string, number, boolean, object, array). Interpretation is left to the consuming application."
        ),
        examples=["https://erp.example.com/api/v2"],
    )
    description: str | None = Field(
        None,
        description="Human-readable description of what this custom-data entry represents and how it is used.",
        examples=["Base URL of the ERP integration endpoint, used by the sync workflow."],
    )

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
