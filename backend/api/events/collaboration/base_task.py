from events.base_event import BaseEvent


class BaseTaskEvent(BaseEvent):
  _notification_subtopic = "task"
