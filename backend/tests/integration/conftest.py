"""Configuration for integration tests."""

import pytest


def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "stress: marks tests as stress tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and name."""
    for item in items:
        # Mark all tests in integration folder as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark performance tests
        if "performance" in str(item.fspath) or "performance" in item.name:
            item.add_marker(pytest.mark.performance)

        # Mark stress tests
        if "stress" in item.name.lower():
            item.add_marker(pytest.mark.stress)
            item.add_marker(pytest.mark.slow)
