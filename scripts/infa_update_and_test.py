# This sample source code is offered only as an example of what can or might be built using the IICS Github APIs, 
# and is provided for educational purposes only. This source code is provided "as-is" 
# and without representations or warrantees of any kind, is not supported by Informatica.
# Users of this sample code in whole or in part or any extraction or derivative of it 
# assume all the risks attendant thereto, and Informatica disclaims any/all liabilities 
# arising from any such use to the fullest extent permitted by law.

import requests
import os
import json
import time
import sys
from helper_functions import iics_login, iics_pull_by_commit
from testing_functions import test_mtt

UAT_COMMIT_HASH = os.environ['UAT_COMMIT_HASH']

LOGIN_URL = os.environ['IICS_LOGIN_URL']
URL = os.environ['IICS_POD_URL']

UAT_IICS_USERNAME = os.environ['UAT_IICS_USERNAME']
UAT_IICS_PASSWORD = os.environ['UAT_IICS_PASSWORD']

SESSION_ID = iics_login(LOGIN_URL, UAT_IICS_USERNAME, UAT_IICS_PASSWORD )

HEADERS = {"Content-Type": "application/json; charset=utf-8", "INFA-SESSION-ID": SESSION_ID }

iics_pull_by_commit(URL, SESSION_ID, UAT_COMMIT_HASH)

# Get all the objects for commit
r = requests.get(URL + "/public/core/v3/commit/" + UAT_COMMIT_HASH, headers = HEADERS)

if r.status_code != 200:
    print("Exception caught: " + r.text)
    exit(99)
    
request_json = r.json()

# Only get Mapping Tasks
r_filtered = [x for x in request_json['changes'] if ( x['type'] == 'MTT') ]

# This loop runs tests for each one of the mapping tasks
# This loop runs tests for each one of the mapping tasks
for x in r_filtered:
    state = test_mtt(URL, SESSION_ID, x['appContextId'])

    if state != 0:
        print("Testing failed")
        exit(99)

requests.post(URL + "/public/core/v3/logout", headers = HEADERS)