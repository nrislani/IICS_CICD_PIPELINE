import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IICSClient:
    def __init__(self, login_url=None, pod_url=None, username=None, password=None, session_id=None):
        self.login_url = login_url
        self.pod_url = pod_url
        self.username = username
        self.password = password
        self.session_id = session_id
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        if self.session_id:
             self.headers["INFA-SESSION-ID"] = self.session_id
             self.headers["icSessionId"] = self.session_id


    def login(self):
        """
        Logs in to IICS and sets the session ID.
        """
        if not self.login_url or not self.username or not self.password:
            raise ValueError("Login URL, username, and password are required for login.")

        url = f"{self.login_url}/saas/public/core/v3/login"
        body = {"username": self.username, "password": self.password}
        
        logger.info(f"Logging in to {self.login_url} as {self.username}")
        
        try:
            response = requests.post(url, json=body)
            response.raise_for_status()
            data = response.json()
            self.session_id = data['userInfo']['sessionId']
            self.headers["INFA-SESSION-ID"] = self.session_id
            self.headers["icSessionId"] = self.session_id # Used in v2 APIs
            
            # If pod_url was not explicitly set, we could potentially set it from login response if available,
            # but usually it's passed or derived. The previous code didn't seem to get it from login.
            logger.info("Login successful")
            return self.session_id
        except requests.Exceptions as e:
            logger.error(f"Login failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def pull_by_commit(self, commit_hash):
        """
        Syncs a commit to the org using pullByCommitHash.
        """
        if not self.pod_url or not self.session_id:
             raise ValueError("Pod URL and Session ID are required.")

        url = f"{self.pod_url}/public/core/v3/pullByCommitHash"
        body = {"commitHash": commit_hash}
        
        logger.info(f"Syncing commit {commit_hash} to Org")
        
        try:
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
            pull_json = response.json()
            pull_action_id = pull_json['pullActionId']
            
            self._wait_for_pull_completion(pull_action_id)
            
        except Exception as e:
            logger.error(f"Pull by commit failed: {e}")
            raise

    def pull_by_commit_object(self, commit_hash, object_id):
        """
        Syncs a specific object from a commit.
        """
        if not self.pod_url or not self.session_id:
             raise ValueError("Pod URL and Session ID are required.")

        url = f"{self.pod_url}/public/core/v3/pull"
        body = {"commitHash": commit_hash, "objects": [{"id": object_id}]}
        
        logger.info(f"Syncing object {object_id} from commit {commit_hash}")
        
        try:
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
            pull_json = response.json()
            pull_action_id = pull_json['pullActionId']
            
            self._wait_for_pull_completion(pull_action_id)
        except Exception as e:
            logger.error(f"Pull object failed: {e}")
            raise

    def _wait_for_pull_completion(self, pull_action_id):
        """
        Waits for a pull action to complete.
        """
        status = 'IN_PROGRESS'
        url = f"{self.pod_url}/public/core/v3/sourceControlAction/{pull_action_id}"
        
        while status == 'IN_PROGRESS':
            logger.info("Checking pull status...")
            time.sleep(10)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            status = data['status']['state']
            
        if status != 'SUCCESSFUL':
            raise Exception(f"Pull failed with status: {status}")
        
        logger.info("Pull successful")

    def get_commit_objects(self, commit_hash, resource_type_filter=None):
        """
        Gets objects for a specific commit.
        """
        if not self.pod_url or not self.session_id:
             raise ValueError("Pod URL and Session ID are required.")

        url = f"{self.pod_url}/public/core/v3/commit/{commit_hash}"
        logger.info(f"Getting objects for commit {commit_hash}")
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        
        changes = data.get('changes', [])
        if resource_type_filter:
            # The original code used 'ZZZ' which likely needs to be 'MTT' (Mapping Task) or passed in.
            # Allowing generic filter.
            return [x for x in changes if x.get('type') == resource_type_filter]
        
        return changes

    def run_job(self, task_id, task_type="ZZZ"):
        """
        Runs a job (Mapping Task, etc.) and waits for completion.
        """
        if not self.pod_url or not self.session_id:
             raise ValueError("Pod URL and Session ID are required.")

        # V2 API typically used for job execution
        url = f"{self.pod_url}/api/v2/job/"
        # The 'icSessionId' header is required for v2, which we added in login/init
        
        body = {"@type": "job", "taskId": task_id, "taskType": task_type}
        
        logger.info(f"Starting job for task {task_id} of type {task_type}")
        
        response = requests.post(url, headers=self.headers, json=body)
        response.raise_for_status()
        job_data = response.json()
        
        run_id = job_data.get('runId')
        if not run_id:
             # Depending on API, sometimes runId is directly returned or wrapper
             raise Exception("Could not retrieve runId from job start response")

        return self._wait_for_job_completion(run_id)

    def _wait_for_job_completion(self, run_id):
        """
        Waits for a job to complete using activityLog.
        """
        state = 0 # 0 usually means running in IICS V2 API context for activity monitoring? 
                  # Actually ActivityLog state: 1=Success, 2=Failed, 3=Warning?
                  # The original code looped while state == 0.
        
        url = f"{self.pod_url}/api/v2/activity/activityLog?runId={run_id}"
        
        while state == 0:
            time.sleep(20)
            logger.info(f"Checking job status for runId {run_id}...")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            activity_log = response.json()
            
            if activity_log:
                state = activity_log[0]['state']
            else:
                logger.warning("Activity log empty, retrying...")
        
        if state != 1:
            object_name = activity_log[0].get('objectName', 'Unknown')
            error_msg = activity_log[0].get('errorMsg', 'No error message')
            logger.error(f"Job {object_name} failed. State: {state}, Error: {error_msg}")
            raise Exception(f"Job failed with state {state}")
            
        logger.info("Job completed successfully")
        return 0

    def logout(self):
        """
        Logs out from IICS.
        """
        if self.pod_url and self.session_id:
            try:
                url = f"{self.pod_url}/public/core/v3/logout"
                requests.post(url, headers=self.headers)
                logger.info("Logged out successfully")
            except Exception as e:
                logger.warning(f"Logout failed (might already be expired): {e}")

    def rollback_mapping(self, path_name, mapping_name, object_type="DTEMPLATE"):
        """
        Rolls back a mapping to its previous commit version.
        """
        if not self.pod_url or not self.session_id:
            raise ValueError("Pod URL and Session ID are required.")

        logger.info(f"Rolling back mapping {mapping_name} in path {path_name}")

        # 1. Get commit history to find previous hash
        # NOTE: Query uses 'DTemplate' while body uses 'DTEMPLATE' in original code. 
        # I'll stick to what was there but clean it up.
        query = f"path=='{path_name}/{mapping_name}' and type=='{object_type}'"
        history_url = f"{self.pod_url}/public/core/v3/commitHistory?q={query}"
        
        try:
            r = requests.get(history_url, headers=self.headers)
            r.raise_for_status()
            commit_json = r.json()
            
            if len(commit_json.get('commits', [])) < 2:
                raise Exception("No previous commit found to rollback to.")
                
            previous_hash = commit_json['commits'][1]['hash']
            
            # 2. Lookup object to get ID
            lookup_url = f"{self.pod_url}/public/core/v3/lookup"
            body = {"objects": [{"path": f"{path_name}/{mapping_name}", "type": object_type.upper()}]}
            
            o = requests.post(lookup_url, headers=self.headers, json=body)
            o.raise_for_status()
            object_json = o.json()
            
            if not object_json.get('objects'):
                raise Exception(f"Object {mapping_name} not found in path {path_name}")
                
            object_id = object_json['objects'][0]['id']
            
            logger.info(f"Previous hash found: {previous_hash}. Object ID: {object_id}")
            
            # 3. Pull previous version
            return self.pull_by_commit_object(previous_hash, object_id)
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise

