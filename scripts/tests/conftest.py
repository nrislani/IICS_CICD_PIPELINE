"""
Pytest fixtures and shared configuration for IICS tests.
"""
import pytest
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_session_id():
    """Provides a mock session ID for testing."""
    return "mock-session-id-12345"


@pytest.fixture
def mock_pod_url():
    """Provides a mock pod URL for testing."""
    return "https://mock-pod.informaticacloud.com/saas"


@pytest.fixture
def mock_login_url():
    """Provides a mock login URL for testing."""
    return "https://mock-login.informaticacloud.com"


@pytest.fixture
def mock_commit_hash():
    """Provides a mock commit hash for testing."""
    return "abc123def456789012345678901234567890abcd"


@pytest.fixture
def mock_login_response():
    """Provides a mock login API response."""
    return {
        "userInfo": {
            "sessionId": "mock-session-id-12345",
            "name": "Test User",
            "orgId": "test-org"
        }
    }


@pytest.fixture
def mock_commit_objects():
    """Provides mock commit objects for testing."""
    return {
        "changes": [
            {
                "id": "obj-1",
                "name": "TestMapping1",
                "type": "MTT",
                "appContextId": "app-ctx-1"
            },
            {
                "id": "obj-2",
                "name": "TestMapping2",
                "type": "MTT",
                "appContextId": "app-ctx-2"
            },
            {
                "id": "obj-3",
                "name": "OtherObject",
                "type": "DSS",
                "appContextId": "app-ctx-3"
            }
        ]
    }


@pytest.fixture
def mock_job_response():
    """Provides a mock job start response."""
    return {
        "runId": 12345,
        "taskId": "task-1"
    }


@pytest.fixture
def mock_activity_log_success():
    """Provides a mock successful activity log."""
    return [
        {
            "state": 1,
            "objectName": "TestMapping1",
            "runId": 12345
        }
    ]


@pytest.fixture
def mock_activity_log_failure():
    """Provides a mock failed activity log."""
    return [
        {
            "state": 2,
            "objectName": "TestMapping1",
            "runId": 12345,
            "errorMsg": "Connection timeout"
        }
    ]
