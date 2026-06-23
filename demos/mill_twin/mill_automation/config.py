"""Mill-automation service configuration via pydantic-settings.

Env-var prefix: MILL_AUTO_
  MILL_AUTO_API_BASE_URL, MILL_AUTO_TOKEN_PATH, MILL_AUTO_NATS_URL,
  MILL_AUTO_TORQUE_LIMIT_NM, MILL_AUTO_DWELL_SECONDS, MILL_AUTO_LATCH_SECONDS,
  MILL_AUTO_BREAKAGE_FLOOR_NM, MILL_AUTO_BREAKAGE_CONFIRM_TICKS,
  MILL_AUTO_TORQUE_LEAF, MILL_AUTO_FEED_RATE_LEAF,
  MILL_AUTO_LINKED_SERIAL_KEY, MILL_AUTO_LINKED_WORK_ORDER_KEY,
  MILL_AUTO_LINKED_OPERATION_KEY, MILL_AUTO_ISSUE_TYPE_KEY,
  MILL_AUTO_CREATED_BY, MILL_AUTO_USER_KEY, MILL_AUTO_USER_SESSION_KEY,
  MILL_AUTO_ENABLED

All fields have defaults so the service can be imported in tests without a
running broker or secrets volume.  NATS connection and token read happen at
startup, never at import time.
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class MillAutomationSettings(BaseSettings):
    # Progress API base URL.  POST target: {api_base_url}/event
    api_base_url: str = "http://api:8000/api"

    # Path to the JWT bearer-token file (Docker secret default).
    token_path: str = "/run/secrets/mill_automation_jwt"

    # NATS broker URL for the automation's OWN connection (D-09).
    nats_url: str = "nats://broker:4222"

    # --- Torque-overload detector knobs (D-01, D-03, D-04) ---
    # Nominal OP-20 semi-finish torque ~27.4 N·m; 45 N·m gives redline headroom.
    torque_limit_nm: float = 45.0
    # Sustained-violation dwell before firing (monotonic clock, D-01).
    dwell_seconds: float = 5.0
    # Minimum interval between two consecutive overload Issues (D-04).
    latch_seconds: float = 60.0

    # --- Tool-breakage detector knobs (D-02) ---
    # Torque below this while feed_rate > 0 → snapped tool.
    breakage_floor_nm: float = 5.0
    # Number of consecutive sub-floor ticks before firing (1 = single-tick, no dwell).
    breakage_confirm_ticks: int = 1

    # --- Subject-leaf identifiers (D-10) ---
    torque_leaf: str = "spindle_torque"
    feed_rate_leaf: str = "feed_rate"

    # --- Issue link keys (D-05, D-06) — env-driven with demo defaults ---
    linked_serial_key: str = Field(default="WING-DEMO-001", alias="MILL_AUTO_LINKED_SERIAL_KEY")
    linked_work_order_key: str = Field(
        default="WO-DEMO-001", alias="MILL_AUTO_LINKED_WORK_ORDER_KEY"
    )
    linked_operation_key: str = Field(
        default="OP-DEMO-001", alias="MILL_AUTO_LINKED_OPERATION_KEY"
    )

    # --- Issue metadata (D-06) ---
    # Fallback only.  The live value is read from `binding_file` on every fire;
    # this env value is used when the file is absent or omits the key.  Empty +
    # empty file → the automation skips firing (logs why) rather than 422-ing.
    issue_type_key: str = ""

    # Path to a JSON file holding the live-editable Issue binding (issue_type_key
    # + serial/work_order/operation link keys).  Re-read on EVERY fire — never
    # cached — so the operator can retarget the Issue type / linked records at any
    # moment without restarting the service.  Missing/invalid file or key → the
    # env values above are used.  Mounted from the config volume (/config).
    binding_file: str = "/config/mill_automation.json"

    # --- Identity (D-07) — env-configured to match the JWT's user ---
    # The API authorises from the JWT; these fields are stored on the Issue
    # document for audit.  The client does NOT decode the token.
    created_by: str = "User/USR-MILL-AUTOMATION"
    user_key: str = "USR-MILL-AUTOMATION"
    user_session_key: str = "mill-automation"

    # Kill switch (mirrors SPARKPLUG_AUTOMATIONS_ENABLED).
    enabled: bool = Field(default=True, alias="MILL_AUTO_ENABLED")

    model_config = SettingsConfigDict(
        env_prefix="mill_auto_",
        env_file=_ENV_FILE,
        secrets_dir="/run/secrets",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache()
def get_config() -> MillAutomationSettings:
    return MillAutomationSettings()
