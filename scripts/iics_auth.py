import os
import sys
import argparse
from iics_client import IICSClient

def main():
    parser = argparse.ArgumentParser(description='IICS Authentication Script')
    parser.add_argument('--target', choices=['dev', 'uat', 'all'], default='all',
                        help='Target environment to login to (default: all)')
    args = parser.parse_args()

    # TEST MESSAGE - Version from MAIN branch - Jan 22 15:32
    print("=" * 80)
    print("🔧 IICS AUTH SCRIPT - RUNNING FROM MAIN BRANCH - VERSION 2026-01-22 15:32")
    print("=" * 80)

    # Environment variables
    username = os.environ.get('IICS_USERNAME')
    password = os.environ.get('IICS_PASSWORD')
    login_url = os.environ.get('IICS_LOGIN_URL') or "https://dm-em.informaticacloud.com" # Default if not set
    
    uat_username = os.environ.get('UAT_IICS_USERNAME')
    uat_password = os.environ.get('UAT_IICS_PASSWORD')
    
    env_file = os.getenv('GITHUB_ENV')
    if not env_file:
        print("GITHUB_ENV not defined, cannot save session IDs.")
        # We might want to allow running locally without GITHUB_ENV, but for now just print 
        # return # Don't return, maybe we just want to test login?
    
    # Login to Primary (DEV)
    if args.target in ['dev', 'all']:
        if not (username and password):
            print("IICS_USERNAME and IICS_PASSWORD environment variables are required for DEV login.")
            sys.exit(1)

        try:
            client = IICSClient(login_url=login_url, username=username, password=password)
            session_id, base_api_url = client.login()
            if env_file:
                with open(env_file, "a") as myfile:
                    myfile.write(f"sessionId={session_id}\n")
                    if base_api_url:
                        myfile.write(f"IICS_POD_URL={base_api_url}\n")
            print("Successfully logged in to Primary/DEV")
        except Exception as e:
            print(f"Failed to login to Primary/DEV: {e}")
            sys.exit(1)

    # Login to UAT
    if args.target in ['uat', 'all']:
        # If explicitly requested UAT, fail if no creds
        if not (uat_username and uat_password):
            if args.target == 'uat':
                print("UAT_IICS_USERNAME and UAT_IICS_PASSWORD environment variables are required for UAT login.")
                sys.exit(1)
            else:
                # 'all' mode: skip if missing (backward compatibility or optional UAT)
                print("Skipping UAT login (credentials not provided)")
                return

        try:
            # UAT might use the same login URL or different, assume same for now or env var
            client_uat = IICSClient(login_url=login_url, username=uat_username, password=uat_password)
            uat_session_id, uat_base_api_url = client_uat.login()
            if env_file:
                with open(env_file, "a") as myfile:
                    myfile.write(f"uat_sessionId={uat_session_id}\n")
                    if uat_base_api_url:
                        # For UAT, we might want to overwrite IICS_POD_URL or use a specific one.
                        # Since deploy_uat.py uses IICS_POD_URL, and runs in a separate job/step 
                        # where DEV envs might not be active or we want to target UAT, overwriting is correct 
                        # for the context of the UAT job.
                        myfile.write(f"IICS_POD_URL={uat_base_api_url}\n")
            print("Successfully logged in to UAT")
        except Exception as e:
            print(f"Failed to login to UAT: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
