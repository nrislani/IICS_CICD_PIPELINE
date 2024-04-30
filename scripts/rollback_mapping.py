import requests
import os
import sys
import json
from helper_functions import iics_login
from helper_functions import iics_rollback_mapping

LOGIN_URL = os.environ['IICS_LOGIN_URL']
POD_URL =  os.environ['IICS_POD_URL']

UAT_IICS_USERNAME = os.environ['UAT_IICS_USERNAME']
UAT_IICS_PASSWORD = os.environ['UAT_IICS_PASSWORD']

PATH_NAME = os.environ['PATH_NAME']
MAPPING_TASK_NAME = os.environ['OBJECT_NAME']

SESSION_ID = iics_login(LOGIN_URL, UAT_IICS_USERNAME, UAT_IICS_PASSWORD)

# TODO: Fix the naming conventions here because they are all over the place
SUCCESS = iics_rollback_mapping(POD_URL, SESSION_ID, PATH_NAME, MAPPING_TASK_NAME)

if SUCCESS != 0:
    print("Unable to rollback to previous version")
    exit(99)