from typing import Any
from abc import ABC, abstractmethod
from events.base_event import BaseEvent
from events.event_model import EventModel
from models.collaboration import IssueLink
from utils.collaboration import Queries


class BaseCollaborationModel(EventModel):
  issue_data: Any | None = None

class BaseCollaboration(BaseEvent, ABC):
    event_data: BaseCollaborationModel

    def get_write_collections(self):
      return list(set(super().get_write_collections() + ['Event', 'Issue', 'issue_rel', 'WorkOrder', 'Job', 'message']))

    @abstractmethod
    def apply(self):
      pass

    @abstractmethod
    def set_model(self, base_model: EventModel):
      pass

    @staticmethod
    def _build_issue_link(_from: str, link_dict: IssueLink):
      """
      Utility function to create the database records for the issue_rel edge collection
      """
      link_map = dict(
        product="Product/",
        operation="Operation/",
        phase="Phase/",
        work_order="WorkOrder/",
        project="Project/",
        user="User/",
        job="Job/",
        serial="Serial/"
      )
      target = link_map[link_dict['type']] + link_dict['key']
      return dict(_from=_from, _to=target)


    def _update_production_status(self, issue_id):
      """
      Set critical flag of work order and job related to the issue,
      checking all other issues related to them
      """
      bind_vars = dict(issue_id=issue_id)
      cursor = self.tx.aql.execute(Queries.CHECK_PRODUCTION_CRITICAL_STATUS, bind_vars=bind_vars)
      for document in cursor:
        self.tx.update_document(document)

