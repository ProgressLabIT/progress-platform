from datetime import datetime

from pydantic import Field

from models.base_models import ArangoDocument, ArangoEdge
from utils.dt import timestamp

class Company(ArangoDocument):
  name: str
  ext_code: str | None = None
  description: str | None = None

class Site(ArangoDocument):
  address: str
  city: str
  province_state: str
  postal_code: str
  country: str
  description: str | None = None
  allow_shipments_to: bool = True
  allow_shipments_from: bool = True

class owns_site(ArangoEdge):
  since: datetime | None = Field(default_factory=timestamp)
  until: datetime | None = None

