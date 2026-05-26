"""ADR-0007 simulator topology + metric set.

This file is the canonical Python encoding of the ADR-0007 specification.
Any change here MUST be reflected in `.planning/workstreams/sparkplug-demo/decisions/0007-simulator-scenario.md`
and vice versa.

Aliases follow ADR-0007 § "Aliases and birth ordering": 1-based integer index
into the per-edge metric list (edge metrics first, then device metrics in the
device order below).
"""
from dataclasses import dataclass, field
from pysparkplug import DataType


@dataclass(frozen=True)
class MetricSpec:
    name: str
    datatype: DataType
    initial: object
    # Optional human-readable note for documentation; not used at runtime.
    note: str = ""


@dataclass(frozen=True)
class DeviceSpec:
    device_id: str
    metrics: tuple[MetricSpec, ...]


@dataclass(frozen=True)
class EdgeSpec:
    edge_id: str
    edge_metrics: tuple[MetricSpec, ...]
    devices: tuple[DeviceSpec, ...]


# --- Edge-level metrics (one per edge per ADR-0007). ---

NODE_CONTROL_REBIRTH = MetricSpec(
    name="NodeControl/Rebirth",
    datatype=DataType.BOOLEAN,
    initial=False,
    note="Always false in v1 demo; flips true post-demo when rebirth UI ships.",
)

# --- Device metric specs (per ADR-0007 § Metric set per device). ---

PUMP3 = DeviceSpec(
    device_id="pump3",
    metrics=(
        MetricSpec("Running",        DataType.BOOLEAN, True),
        MetricSpec("Vibration",      DataType.FLOAT,   22.0,    "pink walk; scripted ramp at t=2:30 (slope from scenario.yaml pump3_anomaly)"),
        MetricSpec("OutletPressure", DataType.FLOAT,   4.10,    "correlates with Vibration spike"),
        MetricSpec("MotorAmps",      DataType.FLOAT,   18.5),
        MetricSpec("RunHours",       DataType.FLOAT,   14512.3, "monotonic 1/3600 per sec while Running"),
    ),
)

CONVEYOR7 = DeviceSpec(
    device_id="conveyor7",
    metrics=(
        MetricSpec("Running",     DataType.BOOLEAN, True),
        MetricSpec("Speed",       DataType.FLOAT,   1.20),
        MetricSpec("LoadCell",    DataType.FLOAT,   38.0),
        MetricSpec("PiecesCount", DataType.INT32,   17441),
    ),
)

OVEN4 = DeviceSpec(
    device_id="oven4",
    metrics=(
        MetricSpec("Running",     DataType.BOOLEAN, True),
        MetricSpec("Setpoint",    DataType.FLOAT,   220.0),
        MetricSpec("Temperature", DataType.FLOAT,   218.5,  "first-order lag toward Setpoint, tau=90s"),
        MetricSpec("EnergyKwh",   DataType.FLOAT,   8421.6, "monotonic; rate ∝ Temperature"),
    ),
)

MIXER2 = DeviceSpec(
    device_id="mixer2",
    metrics=(
        MetricSpec("Running",    DataType.BOOLEAN, False),
        MetricSpec("RPM",        DataType.INT32,   0),
        MetricSpec("BatchID",    DataType.STRING,  ""),
        MetricSpec("TankLevel",  DataType.FLOAT,   0.62),
    ),
)

# --- Edge specs. ---

EDGE1 = EdgeSpec(
    edge_id="edge1",
    edge_metrics=(NODE_CONTROL_REBIRTH,),
    devices=(PUMP3, CONVEYOR7),
)

EDGE2 = EdgeSpec(
    edge_id="edge2",
    edge_metrics=(NODE_CONTROL_REBIRTH,),
    devices=(OVEN4, MIXER2),
)

# --- Group. ---

GROUP_ID = "plant1"

EDGES: tuple[EdgeSpec, ...] = (EDGE1, EDGE2)


def assign_aliases(edge: EdgeSpec, *, reorder_devices: bool = False) -> dict[tuple[str | None, str], int]:
    """Assign 1-based aliases per ADR-0007 § Aliases and birth ordering.

    Returns: {(device_id_or_None, metric_name): alias}
      - (None, edge_metric_name) for edge-level metrics.
      - (device_id, metric_name) for device metrics.

    `reorder_devices=True` reverses the device iteration order to exercise
    the bridge's alias resolution path on rebirth (used at t=5:00 cue per
    ADR-0007 § Aliases — "alias renumbering once during the scenario by
    forcing a rebirth on edge2 with reordered metrics").
    """
    aliases: dict[tuple[str | None, str], int] = {}
    next_alias = 1
    # Edge metrics first.
    for em in edge.edge_metrics:
        aliases[(None, em.name)] = next_alias
        next_alias += 1
    devices = list(edge.devices)
    if reorder_devices:
        devices.reverse()
    for dev in devices:
        for m in dev.metrics:
            aliases[(dev.device_id, m.name)] = next_alias
            next_alias += 1
    return aliases
