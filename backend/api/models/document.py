from datetime import datetime
from enum import Enum

from pydantic import Field

from models.base_models import ArangoDocument, ArangoEdge
from utils.dt import timestamp


class DocumentType(str, Enum):
  TRANSPORT_DOCUMENT: 'td'
  SALES_ORDER: 'so'
  PURCHASE_ORDER: 'po'
  RETURN_REQUEST: 'rr'
  CUSTOMER_INVOICE: 'si'
  SUPPLIER_INVOICE: 'ci'


class transport_document(ArangoDocument):
  source_site: str = Field(alias='_from') # can be of any company
  destination_site: str = Field(alias='_to')
  document_number: str
  document_date: datetime | None = Field(default_factory=timestamp)
  shipment_date: datetime | None = None
