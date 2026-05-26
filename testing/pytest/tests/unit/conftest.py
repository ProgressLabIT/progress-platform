"""Override autouse parent fixtures so unit tests run without Docker.

The repo-root conftest declares session-scope autouse fixtures that spin up an
ArangoDB testcontainer and patch backend modules. That makes sense for
integration tests but is wasteful for pure-Python units that only exercise
library code via httpx.MockTransport, in-memory state machines, etc.

Pytest resolves fixtures by walking up from the test file; a same-named fixture
in this conftest wins over the parent's. Each override yields a sentinel value
or no-op so the dependency chain still resolves but skips all Docker / DB work.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def arango_container():
    yield None


@pytest.fixture(scope="session", autouse=True)
def db(arango_container):
    yield None


@pytest.fixture(scope="session", autouse=True)
def mock_nats(db):
    yield


@pytest.fixture(scope="session", autouse=True)
def _capture_config_defaults(db):
    yield


@pytest.fixture(autouse=True)
def truncate_collections(db):
    yield
