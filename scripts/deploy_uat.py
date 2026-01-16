import os
import sys
from iics_client import IICSClient

def main():
    uat_commit_hash = os.environ.get('UAT_COMMIT_HASH')
    pod_url = os.environ.get('IICS_POD_URL')
    
    # This script is for UAT, so it should use the UAT session ID
    session_id = os.environ.get('uat_sessionId')
    
    if not uat_commit_hash:
        print("UAT_COMMIT_HASH environment variable is required.")
        sys.exit(1)

    if not pod_url:
        print("IICS_POD_URL environment variable is required.")
        sys.exit(1)
        
    if not session_id:
        print("uat_sessionId environment variable is required.")
        sys.exit(1)
        
    client = IICSClient(pod_url=pod_url, session_id=session_id)
    
    try:
        # 1. Pull the commit to UAT
        client.pull_by_commit(uat_commit_hash)
        
        # 2. Get the objects from the commit to run tests
        objects = client.get_commit_objects(uat_commit_hash, resource_type_filter='ZZZ')
        
        # 3. test each object
        for obj in objects:
            app_context_id = obj.get('appContextId')
            if app_context_id:
                 client.run_job(app_context_id)
            else:
                 print(f"Skipping object {obj} (no appContextId)")
                 
    except Exception as e:
        print(f"Error in UAT update and test: {e}")
        sys.exit(1)
        
    client.logout()

if __name__ == "__main__":
    main()