# Factory fixtures are registered via pytest_plugins in the root conftest.py
# (testing/pytest/conftest.py) so they are available to all test subdirectories.
# Do NOT re-register them here — that causes double-registration errors.
