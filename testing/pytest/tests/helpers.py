"""Shared test assertion helpers for the Progress Platform test suite.

Per D-07: Query the Event collection to verify child events were dispatched
without coupling to child apply() logic.
"""


def assert_event_dispatched(db, event_type: str, **filters):
    """Assert at least one Event record exists with given type and matching info fields.

    Per D-07: Query the Event collection to verify child events were dispatched
    without coupling to child apply() logic.

    Args:
        db: ArangoDB StandardDatabase from the `db` fixture.
        event_type: The EventType string value to search for (e.g. "BATCH_COMPLETED").
        **filters: Additional fields to match on the Event document.

    Returns:
        The first matching Event document.

    Raises:
        AssertionError: If no matching Event document is found.
    """
    query_filter = {"event_type": event_type, **filters}
    results = list(db.collection("Event").find(query_filter))
    assert results, (
        f"Expected {event_type} event dispatched, found none (filters: {filters})"
    )
    return results[0]
