"""Spike: alias renumbering on edge2 rebirth resolves cleanly per D-08.

Given the live ADR-0007 simulator is publishing,
When we kill+restart the simulator container (forcing fresh bdSeq + alias
     renumbering on edge2 per ADR-0007 § "Aliases and birth ordering"),
Then within 30s of restart, NDATA frames published by edge2 are correctly
     resolved by the bridge — at least one `progress.sparkplug.plant1.edge2.<device>.metric.<name>.data`
     arrives with a non-null `name` field, AND no session.suspect with
     reason="seq_gap" or alias-miss appears for edge2 during this window.
"""
import asyncio

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_alias_renumber_on_rebirth_resolves_cleanly(
    nats_subscriber,
    resolve_container,
):
    await asyncio.sleep(2.0)

    # Try Swarm naming first (production deploy), then compose naming.
    try:
        container = resolve_container("progress_sparkplug_sim")
    except RuntimeError:
        container = resolve_container("sparkplug_sim")
    # Mark "before" state.
    baseline_count = len(nats_subscriber)
    # Restart the sim — fresh bdSeq + alias renumber on edge2.
    container.restart(timeout=5)

    # Wait up to 30s for the bridge to (a) re-register edge2's session and
    # (b) publish at least one decoded NDATA on a typed metric subject.
    deadline = asyncio.get_event_loop().time() + 30.0
    edge2_metrics: list[dict] = []
    while asyncio.get_event_loop().time() < deadline and not edge2_metrics:
        await asyncio.sleep(0.5)
        edge2_metrics = [
            e for e in nats_subscriber[baseline_count:]
            if e.get("kind") == "metric.data"
            and ".edge2." in e["subject"]
            and e["payload"].get("name") is not None
        ]

    assert edge2_metrics, (
        f"expected at least one edge2 metric.data with non-null name within 30s; "
        f"got {len(nats_subscriber[baseline_count:])} frames after restart, "
        f"of which 0 were edge2 metric.data"
    )

    # Ensure no alias-miss-derived suspect notification appeared for edge2.
    edge2_suspects = [
        e for e in nats_subscriber[baseline_count:]
        if e.get("kind") == "session.suspect"
        and (e["payload"] or {}).get("payload_ref", {}).get("edge") == "edge2"
    ]
    assert not edge2_suspects, (
        f"unexpected session.suspect for edge2 during alias-renumber window: "
        f"{[e['payload'] for e in edge2_suspects]}"
    )
