import os
import sys
from iics_client import IICSClient

def main():
    login_url = os.environ.get('IICS_LOGIN_URL') or "https://dm-em.informaticacloud.com"
    pod_url =  os.environ.get('IICS_POD_URL')
    
    uat_username = os.environ.get('UAT_IICS_USERNAME')
    uat_password = os.environ.get('UAT_IICS_PASSWORD')
    
    path_name = os.environ.get('PATH_NAME')
    mapping_name = os.environ.get('OBJECT_NAME')
    
    # We can use the session ID if already logged in, or login here.
    # The original script logged in explicitly.
    
    if not all([pod_url, uat_username, uat_password, path_name, mapping_name]):
        print("Missing required environment variables for rollback.")
        sys.exit(1)
        
    client = IICSClient(login_url=login_url, pod_url=pod_url, username=uat_username, password=uat_password)
    
    try:
        client.login()
        # Rollback logic
        client.rollback_mapping(path_name, mapping_name)
        print(f"Successfully rolled back {mapping_name} in {path_name}")
    except Exception as e:
        print(f"Unable to rollback: {e}")
        sys.exit(1)
    finally:
        client.logout()

if __name__ == "__main__":
    main()