"""
Unit tests for IICSClient class.
"""
import pytest
from unittest.mock import Mock, patch
import requests

from iics_client import IICSClient
from exceptions import (
    IICSAuthenticationError,
    IICSConfigError,
    IICSJobError,
    IICSPullError,
)


class TestIICSClientInit:
    """Tests for IICSClient initialization."""

    def test_init_with_session_id(self, mock_pod_url, mock_session_id):
        """Test client initialization with existing session ID."""
        client = IICSClient(pod_url=mock_pod_url, session_id=mock_session_id)
        
        assert client.session_id == mock_session_id
        assert client.headers["INFA-SESSION-ID"] == mock_session_id
        assert client.headers["icSessionId"] == mock_session_id

    def test_init_without_session_id(self, mock_pod_url):
        """Test client initialization without session ID."""
        client = IICSClient(pod_url=mock_pod_url)
        
        assert client.session_id is None
        assert "INFA-SESSION-ID" not in client.headers


class TestIICSClientLogin:
    """Tests for login functionality."""

    @patch('iics_client.requests.post')
    def test_login_success(
        self,
        mock_post,
        mock_login_url,
        mock_login_response
    ):
        """Test successful login."""
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_login_response)
        )
        
        client = IICSClient(
            login_url=mock_login_url,
            username="testuser",
            password="testpass"
        )
        session_id = client.login()
        
        assert session_id == mock_login_response["userInfo"]["sessionId"]
        assert client.session_id == session_id

    def test_login_missing_credentials(self, mock_login_url):
        """Test login fails without credentials."""
        client = IICSClient(login_url=mock_login_url)
        
        with pytest.raises(IICSConfigError):
            client.login()

    @patch('iics_client.requests.post')
    def test_login_api_failure(self, mock_post, mock_login_url):
        """Test login handles API errors."""
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        client = IICSClient(
            login_url=mock_login_url,
            username="testuser",
            password="testpass"
        )
        
        with pytest.raises(IICSAuthenticationError):
            client.login()


class TestIICSClientGetCommitObjects:
    """Tests for get_commit_objects functionality."""

    @patch('iics_client.requests.get')
    def test_get_commit_objects_no_filter(
        self,
        mock_get,
        mock_pod_url,
        mock_session_id,
        mock_commit_hash,
        mock_commit_objects
    ):
        """Test getting all commit objects without filter."""
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_commit_objects)
        )
        
        client = IICSClient(pod_url=mock_pod_url, session_id=mock_session_id)
        objects = client.get_commit_objects(mock_commit_hash)
        
        assert len(objects) == 3

    @patch('iics_client.requests.get')
    def test_get_commit_objects_with_filter(
        self,
        mock_get,
        mock_pod_url,
        mock_session_id,
        mock_commit_hash,
        mock_commit_objects
    ):
        """Test getting commit objects with type filter."""
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_commit_objects)
        )
        
        client = IICSClient(pod_url=mock_pod_url, session_id=mock_session_id)
        objects = client.get_commit_objects(mock_commit_hash, resource_type_filter="MTT")
        
        assert len(objects) == 2
        assert all(obj["type"] == "MTT" for obj in objects)

    def test_get_commit_objects_missing_config(self, mock_commit_hash):
        """Test get_commit_objects fails without config."""
        client = IICSClient()
        
        with pytest.raises(IICSConfigError):
            client.get_commit_objects(mock_commit_hash)


class TestIICSClientRunJob:
    """Tests for run_job functionality."""

    @patch('iics_client.requests.get')
    @patch('iics_client.requests.post')
    @patch('iics_client.time.sleep', return_value=None)
    def test_run_job_success(
        self,
        mock_sleep,
        mock_post,
        mock_get,
        mock_pod_url,
        mock_session_id,
        mock_job_response,
        mock_activity_log_success
    ):
        """Test successful job execution."""
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_job_response)
        )
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_activity_log_success)
        )
        
        client = IICSClient(pod_url=mock_pod_url, session_id=mock_session_id)
        result = client.run_job("task-1")
        
        assert result == 0

    @patch('iics_client.requests.get')
    @patch('iics_client.requests.post')
    @patch('iics_client.time.sleep', return_value=None)
    def test_run_job_failure(
        self,
        mock_sleep,
        mock_post,
        mock_get,
        mock_pod_url,
        mock_session_id,
        mock_job_response,
        mock_activity_log_failure
    ):
        """Test job execution failure."""
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_job_response)
        )
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_activity_log_failure)
        )
        
        client = IICSClient(pod_url=mock_pod_url, session_id=mock_session_id)
        
        with pytest.raises(IICSJobError) as exc_info:
            client.run_job("task-1")
        
        assert exc_info.value.job_state == 2


class TestIICSClientLogout:
    """Tests for logout functionality."""

    @patch('iics_client.requests.post')
    def test_logout_success(self, mock_post, mock_pod_url, mock_session_id):
        """Test successful logout."""
        mock_post.return_value = Mock(status_code=200)
        
        client = IICSClient(pod_url=mock_pod_url, session_id=mock_session_id)
        client.logout()
        
        mock_post.assert_called_once()

    def test_logout_without_session(self):
        """Test logout does nothing without session."""
        client = IICSClient()
        client.logout()  # Should not raise
