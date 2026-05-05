from datetime import date, time, datetime
from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

from models.base_models import ArangoDocument
from utils.dt import timestamp


_YEAR_TOKENS = {'%Y', '%y', '%G'}
_MONTH_TOKENS = {'%m'}
_WEEK_TOKENS = {'%V', '%U', '%W'}
_DOY_TOKENS = {'%j'}
_DOM_TOKENS = {'%d'}


class Counter(ArangoDocument):
  name: str | None = Field(
    "",
    description="Human-readable name for this counter sequence. Used to identify the counter in the UI and via the `name` query parameter.",
    examples=["Work Order Counter"],
  )
  next_tick: int | None = Field(
    1,
    description="The integer value that will be used on the next counter tick. Automatically incremented after each use.",
    examples=[1],
  )
  template: list[str] = Field(
    default_factory=list,
    description=(
      "Ordered list of template tokens that form the counter string. "
      "Tokens are strftime-style date codes (e.g. `%Y`, `%m`, `%d`) or literal strings. "
      "Example: `['WO-', '%Y', '-', '%m', '-']` yields `WO-2026-05-`."
    ),
    examples=[["WO-", "%Y", "-", "%m", "-"]],
  )
  frequency: str | None = Field(
    None,
    description=(
      "Reset frequency for the tick counter. Accepted values: `year`, `month`, `week`, `day`, `none` (or `null` for no reset). "
      "The template must include tokens that uniquely identify each reset cycle."
    ),
    examples=["month"],
  )
  reset_date: datetime | None = Field(
    None,
    description="UTC timestamp of the most recent counter reset. `null` if the counter has never been reset.",
    examples=["2026-05-01T00:00:00Z"],
  )

  @model_validator(mode='after')
  def _template_covers_reset_period(self):
    if self.frequency in (None, 'none'):
      return self

    tokens = set(self.template or [])
    has_year = bool(tokens & _YEAR_TOKENS)
    has_month = bool(tokens & _MONTH_TOKENS)
    has_week = bool(tokens & _WEEK_TOKENS)
    has_doy = bool(tokens & _DOY_TOKENS)
    has_dom = bool(tokens & _DOM_TOKENS)

    if self.frequency == 'year':
      ok = has_year
    elif self.frequency == 'month':
      ok = has_year and (has_month or has_doy)
    elif self.frequency == 'week':
      ok = has_year and (has_week or has_doy or (has_month and has_dom))
    elif self.frequency == 'day':
      ok = has_year and (has_doy or (has_month and has_dom))
    else:
      ok = True

    if not ok:
      raise ValueError(
        "Template tokens are insufficient for the selected reset frequency: "
        "the template must uniquely identify each reset cycle (e.g. year for "
        "yearly reset; year + month for monthly; year + week for weekly; "
        "year + day-of-year for daily)."
      )
    return self
