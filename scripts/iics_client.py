"""
IICS Client module with retry logic and improved error handling.
Provides a centralized interface for all IICS API operations.
"""
import requests
import time
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from exceptions import (
    IICSAuthenticationError,
    IICSJobError,
    IICSPullError,
    IICSConfigError,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IICSClient:
    """Client for interacting with IICS REST APIs."""
    
    def __init__(
        self,
        login_url: Optional[str] = None,
        pod_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.login_url = login_url
        self.pod_url = pod_url
        self.username = username
        self.password = password
        self.session_id = session_id
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        if self.session_id:
            self.headers["INFA-SESSION-ID"] = self.session_id
            self.headers["icSessionId"] = self.session_id

    def _api_v2_base_url(self) -> str:
        if not self.pod_url:
            raise IICSConfigError("Pod URL is required.")
        base = self.pod_url.rstrip("/")
        if base.endswith("/saas"):
            base = base[: -len("/saas")]
        return base

    def _core_v3_base_urls(self) -> list[str]:
        if not self.pod_url:
            raise IICSConfigError("Pod URL is required.")
        base = self.pod_url.rstrip("/")
        if base.endswith("/saas"):
            base_no_saas = base[: -len("/saas")]
            base_with_saas = base
        else:
            base_no_saas = base
            base_with_saas = f"{base}/saas"
        if base_no_saas == base_with_saas:
            return [base_no_saas]
        return [base_no_saas, base_with_saas]

    def _core_v3_request(self, method: str, path: str, **kwargs) -> requests.Response:
        last_http_error: Optional[requests.HTTPError] = None
        for base in self._core_v3_base_urls():
            url = f"{base}{path}"
            response = requests.request(method, url, headers=self.headers, **kwargs)
            if response.status_code == 404:
                try:
                    response.raise_for_status()
                except requests.HTTPError as e:
                    last_http_error = e
                continue
            response.raise_for_status()
            return response
        if last_http_error is not None:
            raise last_http_error
        raise IICSPullError(f"Core v3 request failed for {path}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def login(self) -> str:
        """
        Logs in to IICS and sets the session ID.
        
        Returns:
            str: The session ID
            
        Raises:
            IICSConfigError: If required credentials are missing
            IICSAuthenticationError: If login fails
        """
        if not self.login_url or not self.username or not self.password:
            raise IICSConfigError("Login URL, username, and password are required for login.")

        url = f"{self.login_url}/saas/public/core/v3/login"
        body = {"username": self.username, "password": self.password}
        
        logger.info(f"Logging in to {self.login_url} as {self.username}")
        
        try:
            response = requests.post(url, json=body)
            response.raise_for_status()
            data = response.json()
            self.session_id = data['userInfo']['sessionId']
            self.headers["INFA-SESSION-ID"] = self.session_id
            self.headers["icSessionId"] = self.session_id
            
            logger.info("Login successful")
            return self.session_id
        except requests.RequestException as e:
            logger.error(f"Login failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise IICSAuthenticationError(f"Failed to authenticate: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def pull_by_commit(self, commit_hash: str) -> None:
        """
        Syncs a commit to the org using pullByCommitHash.
        
        Args:
            commit_hash: The git commit hash to sync
            
        Raises:
            IICSConfigError: If pod_url or session_id is missing
            IICSPullError: If the pull operation fails
        """
        if not self.pod_url or not self.session_id:
            raise IICSConfigError("Pod URL and Session ID are required.")

        body = {"commitHash": commit_hash}
        
        logger.info(f"Syncing commit {commit_hash} to Org")
        
        try:
            response = self._core_v3_request("POST", "/public/core/v3/pullByCommitHash", json=body)
            pull_json = response.json()
            pull_action_id = pull_json['pullActionId']
            
            self._wait_for_pull_completion(pull_action_id)
            
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning("pullByCommitHash endpoint not found (404). Falling back to pull with explicit object list.")
                self.pull_by_commit_objects(commit_hash)
                return
            logger.error(f"Pull by commit failed: {e}")
            raise IICSPullError(f"Failed to pull commit {commit_hash}: {e}") from e
        except Exception as e:
            logger.error(f"Pull by commit failed: {e}")
            raise IICSPullError(f"Failed to pull commit {commit_hash}: {e}") from e

    def pull_by_commit_objects(self, commit_hash: str) -> None:
        """Fallback sync: pulls all objects in a commit using the /pull endpoint."""
        objects = self.get_commit_objects(commit_hash)
        object_ids: list[str] = []
        for obj in objects:
            obj_id = obj.get('id')
            if obj_id:
                object_ids.append(obj_id)
 
        if not object_ids:
            raise IICSPullError(f"No object IDs found in commit {commit_hash} to pull.")

        body = {"commitHash": commit_hash, "objects": [{"id": oid} for oid in object_ids]}
        logger.info(f"Syncing {len(object_ids)} objects from commit {commit_hash}")
 
        response = self._core_v3_request("POST", "/public/core/v3/pull", json=body)
        pull_json = response.json()
        pull_action_id = pull_json['pullActionId']
        self._wait_for_pull_completion(pull_action_id)

    def pull_by_commit_object(self, commit_hash: str, object_id: str) -> None:
        """
        Syncs a specific object from a commit.
        
        Args:
            commit_hash: The git commit hash
            object_id: The ID of the object to sync
        """
        if not self.pod_url or not self.session_id:
            raise IICSConfigError("Pod URL and Session ID are required.")

        body = {"commitHash": commit_hash, "objects": [{"id": object_id}]}
        
        logger.info(f"Syncing object {object_id} from commit {commit_hash}")
        
        try:
            response = self._core_v3_request("POST", "/public/core/v3/pull", json=body)
            pull_json = response.json()
            pull_action_id = pull_json['pullActionId']
            
            self._wait_for_pull_completion(pull_action_id)
        except Exception as e:
            logger.error(f"Pull object failed: {e}")
            raise IICSPullError(f"Failed to pull object {object_id}: {e}") from e

    def _wait_for_pull_completion(self, pull_action_id: str) -> None:
        """
        Waits for a pull action to complete.
        
        Args:
            pull_action_id: The ID of the pull action to monitor
        """
        status = 'IN_PROGRESS'
        path = f"/public/core/v3/sourceControlAction/{pull_action_id}"
        
        while status == 'IN_PROGRESS':
            logger.info("Checking pull status...")
            time.sleep(10)
            response = self._core_v3_request("GET", path)
            data = response.json()
            status = data['status']['state']
            
        if status != 'SUCCESSFUL':
            raise IICSPullError(f"Pull failed with status: {status}", pull_status=status)
        
        logger.info("Pull successful")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def get_commit_objects(
        self,
        commit_hash: str,
        resource_type_filter: Optional[str] = None
    ) -> list[dict]:
        """
        Gets objects for a specific commit.
        
        Args:
            commit_hash: The git commit hash
            resource_type_filter: Optional filter for resource type (e.g., 'MTT', 'DSS')
            
        Returns:
            List of changed objects in the commit
        """
        if not self.pod_url or not self.session_id:
            raise IICSConfigError("Pod URL and Session ID are required.")

        logger.info(f"Getting objects for commit {commit_hash}")

        response = self._core_v3_request("GET", f"/public/core/v3/commit/{commit_hash}")
        data = response.json()
        
        changes = data.get('changes', [])
        if resource_type_filter:
            return [x for x in changes if x.get('type') == resource_type_filter]
        
        return changes

    def run_job(self, task_id: str, task_type: str = "MTT") -> int:
        """
        Runs a job (Mapping Task, etc.) and waits for completion.
        
        Args:
            task_id: The ID of the task to run
            task_type: The type of task (default: MTT for Mapping Task)
            
        Returns:
            0 on success
            
        Raises:
            IICSJobError: If job execution fails
        """
        if not self.pod_url or not self.session_id:
            raise IICSConfigError("Pod URL and Session ID are required.")

        url = f"{self._api_v2_base_url()}/api/v2/job/"
        body = {"@type": "job", "taskId": task_id, "taskType": task_type}
        
        logger.info(f"Starting job for task {task_id} of type {task_type}")
        
        response = requests.post(url, headers=self.headers, json=body)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Job start failed: {e}")
            logger.error(f"Response: {response.text}")
            raise
        job_data = response.json()
        
        run_id = job_data.get('runId')
        if not run_id:
            raise IICSJobError("Could not retrieve runId from job start response")

        return self._wait_for_job_completion(run_id)

    def _wait_for_job_completion(self, run_id: int) -> int:
        """
        Waits for a job to complete using activityLog.
        
        Args:
            run_id: The run ID to monitor
            
        Returns:
            0 on success
        """
        state = 0
        url = f"{self._api_v2_base_url()}/api/v2/activity/activityLog?runId={run_id}"
        
        while state == 0:
            time.sleep(20)
            logger.info(f"Checking job status for runId {run_id}...")
            response = requests.get(url, headers=self.headers)
            try:
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Activity log request failed: {e}")
                logger.error(f"Response: {response.text}")
                if response.status_code == 403:
                    logger.error("Forbidden: Check your credentials and permissions")
                raise
            activity_log = response.json()
            
            if activity_log:
                state = activity_log[0]['state']
            else:
                logger.warning("Activity log empty, retrying...")
        
        if state != 1:
            object_name = activity_log[0].get('objectName', 'Unknown')
            error_msg = activity_log[0].get('errorMsg', 'No error message')
            logger.error(f"Job {object_name} failed. State: {state}, Error: {error_msg}")
            raise IICSJobError(
                f"Job failed with state {state}",
                job_state=state,
                object_name=object_name
            )
            
        logger.info("Job completed successfully")
        return 0

    def logout(self) -> None:
        """Logs out from IICS."""
        if self.pod_url and self.session_id:
            try:
                self._core_v3_request("POST", "/public/core/v3/logout")
                logger.info("Logged out successfully")
            except Exception as e:
                logger.warning(f"Logout failed (might already be expired): {e}")

    def rollback_mapping(
        self,
        path_name: str,
        mapping_name: str,
        object_type: str = "DTEMPLATE"
    ) -> None:
        """
        Rolls back a mapping to its previous commit version.
        
        Args:
            path_name: The path where the mapping is located
            mapping_name: The name of the mapping
            object_type: The type of object (default: DTEMPLATE)
        """
        if not self.pod_url or not self.session_id:
            raise IICSConfigError("Pod URL and Session ID are required.")

        logger.info(f"Rolling back mapping {mapping_name} in path {path_name}")

        query = f"path=='{path_name}/{mapping_name}' and type=='{object_type}'"
        response = self._core_v3_request("GET", f"/public/core/v3/commitHistory?q={query}")
        commit_json = response.json()
        
        if len(commit_json.get('commits', [])) < 2:
            raise IICSPullError("No previous commit found to rollback to.")
                
        previous_hash = commit_json['commits'][1]['hash']
        
        body = {"objects": [{"path": f"{path_name}/{mapping_name}", "type": object_type.upper()}]}
        response = self._core_v3_request("POST", "/public/core/v3/lookup", json=body)
        object_json = response.json()
        
        if not object_json.get('objects'):
            raise IICSPullError(f"Object {mapping_name} not found in path {path_name}")
                
        object_id = object_json['objects'][0]['id']
        
        logger.info(f"Previous hash found: {previous_hash}. Object ID: {object_id}")
        
        return self.pull_by_commit_object(previous_hash, object_id)
