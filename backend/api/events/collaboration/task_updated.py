from datetime import date

from fastapi import HTTPException
from pydantic import BaseModel, model_validator
from typing import Any

from events.base_event import BaseEvent, EventInfoModel
from models.event import EventType
from models.collaboration import TaskAssignment, TaskAssignmentRole


class TaskFieldUpdate(BaseModel):
  form_field_key: str
  value: Any | None = None
class TaskUpdatedEvent(BaseEvent):

  class InfoModel(EventInfoModel):
    task_key: str
    title: str | None = None
    description: str | None = None
    assigned_to: list[TaskAssignment] | None = None
    start_from: date | None = None
    due_by: date | None = None
    form_fields: list[TaskFieldUpdate] | None = None

    @model_validator(mode='after')
    def validate_assignments(self):
      # Ensure single owner if assignments are provided
      if self.assigned_to is None:
        return self

      owners = [a for a in self.assigned_to if a.role == TaskAssignmentRole.OWNER]
      if len(self.assigned_to) > 0 and len(owners) != 1:
        raise ValueError('You must provide one and only one owner when specifying assignments')

      # Set top level owner key for easier access
      self.owner_key = None if len(owners) == 0 else owners[0].user_key

      # Reorder assignments to put owner first
      if owners:
        owner = owners[0]
        participants = [a for a in self.assigned_to if a.role == TaskAssignmentRole.PARTICIPANT]
        self.assigned_to = [owner] + participants
      return self

  @classmethod
  def get_tx_collections(cls):
    return ['Task']

  @classmethod
  def get_event_type(self):
    return EventType.TASK_UPDATED

  # ------------------------------------------------------------
  # Helpers
  # ------------------------------------------------------------

  def _merge_form_fields(self):
    # Merge form fields from the original task with the new form field values
    current_task = self.tx.collection('Task').get(self.info.task_key)
    if not current_task or not current_task.get('form_fields'):
      return None

    # Start with existing fields and only update values that changed
    merged_fields = []
    for existing_field in current_task['form_fields']:
      new_field = existing_field.copy()
      for field in self.info.form_fields:
        if field.form_field_key == existing_field['form_field_key'] and field.value != existing_field['value']:
          new_field['value'] = field.value
          new_field['last_updated'] = self.event_key
          break
      merged_fields.append(new_field)

    return merged_fields

  # ------------------------------------------------------------
  # Apply
  # ------------------------------------------------------------

  def apply(self):
    # Exclude null values unless explicitly set and convert to dictionary
    updates = dict(_key=self.info.task_key)

    if self.info.title:
      updates['title'] = self.info.title
    if self.info.description:
      updates['description'] = self.info.description
    if self.info.assigned_to is not None:
      updates['assigned_to'] = self.info.assigned_to
      updates['owner_key'] = self.info.owner_key
    if self.info.start_from:
      updates['start_from'] = self.info.start_from
    if self.info.due_by:
      updates['due_by'] = self.info.due_by
    if self.info.form_fields:
      updates['form_fields'] = self._merge_form_fields()

    if len(updates) == 1: # _key only
      raise HTTPException(status_code=400, detail="No updates provided")

    else:
      updated_task = self.tx.collection('Task').update(updates, return_new=True)['new']

      self.response = dict(
        message=f"Task {self.info.task_key} updated successfully",
        detail=updated_task
      )
