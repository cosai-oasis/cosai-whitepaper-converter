import pytest

# Auto-apply the integration marker to every test in this directory.
pytestmark = pytest.mark.integration


def pytest_collection_modifyitems(items):
    """Ensure all tests collected from tests/integration/ carry the integration marker."""
    for item in items:
        if "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
