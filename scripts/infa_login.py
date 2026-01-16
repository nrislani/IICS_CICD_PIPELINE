import os
import sys
from iics_client import IICSClient

def main():
    # Environment variables
    username = os.environ.get('IICS_USERNAME')
    password = os.environ.get('IICS_PASSWORD')
    login_url = os.environ.get('IICS_LOGIN_URL') or "https://dm-em.informaticacloud.com" # Default if not set
    
    # Check for UAT specific env vars if needed, or if this script is general purpose
    # The original script logged in twice (once for DEV/default, once for UAT) and saved both sessionIds
    # to GITHUB_ENV.
    
    uat_username = os.environ.get('UAT_IICS_USERNAME')
    uat_password = os.environ.get('UAT_IICS_PASSWORD')
    
    env_file = os.getenv('GITHUB_ENV')
    if not env_file:
        print("GITHUB_ENV not defined, cannot save session IDs.")
        return

    # Login to Primary (DEV)
    if username and password:
        try:
            client = IICSClient(login_url=login_url, username=username, password=password)
            session_id = client.login()
            with open(env_file, "a") as myfile:
                myfile.write(f"sessionId={session_id}\n")
            print("Successfully logged in to Primary/DEV")
        except Exception as e:
            print(f"Failed to login to Primary/DEV: {e}")
            sys.exit(1)

    # Login to UAT
    if uat_username and uat_password:
        try:
            # UAT might use the same login URL or different, assume same for now or env var
            client_uat = IICSClient(login_url=login_url, username=uat_username, password=uat_password)
            uat_session_id = client_uat.login()
            with open(env_file, "a") as myfile:
                myfile.write(f"uat_sessionId={uat_session_id}\n")
            print("Successfully logged in to UAT")
        except Exception as e:
            print(f"Failed to login to UAT: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
