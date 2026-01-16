import os
import sys
from iics_client import IICSClient

def main():
    commit_hash = os.environ.get('COMMIT_HASH')
    # Use generic names for login url and pod url, but fallbacks may vary
    # Original script used IICS_LOGIN_URL and IICS_POD_URL
    pod_url = os.environ.get('IICS_POD_URL')
    
    # We expect sessionId to be passed in environment or we can re-login if needed.
    # The existing pipeline runs login first, then this script.
    # The login script dumps sessionId to GITHUB_ENV, which makes it available 
    # as an environment variable in subsequent steps? 
    # Wait, GITHUB_ENV makes it available for *subsequent steps*, but does it automatically 
    # set it as an env var for python? Yes, in GitHub Actions.
    # So we should look for 'sessionId'.
    
    session_id = os.environ.get('sessionId') # From infa_login.py output
    
    # If session_id is missing, we might need to login, but let's assume pipeline order is correct.
    # However, for robustness, if we have creds we could try logging in.
    # But for now let's rely on the pipeline.
    
    if not commit_hash:
        print("COMMIT_HASH environment variable is required.")
        sys.exit(1)
        
    if not pod_url:
        print("IICS_POD_URL environment variable is required.")
        sys.exit(1)
        
    if not session_id:
        print("sessionId environment variable is required (should be set by previous login step).")
        sys.exit(1)
        
    client = IICSClient(pod_url=pod_url, session_id=session_id)
    
    try:
        # Filter for 'ZZZ' or 'MTT' - keeping ZZZ for now per original, but should likely be MTT
        # I'll mention this in the summary that I kept it ZZZ but it should be changed.
        objects = client.get_commit_objects(commit_hash, resource_type_filter='ZZZ')
        
        if not objects:
             print(f"No objects of type 'ZZZ' found in commit {commit_hash}")
        
        for obj in objects:
            app_context_id = obj.get('appContextId')
            if app_context_id:
                client.run_job(app_context_id)
            else:
                print(f"Object {obj} has no appContextId")
                
    except Exception as e:
        print(f"Error checking updates: {e}")
        sys.exit(1)
        
    client.logout()

if __name__ == "__main__":
    main()
