# This sample source code is offered only as an example of what can or might be built using the IICS Github APIs, 
# and is provided for educational purposes only. This source code is provided "as-is" 
# and without representations or warrantees of any kind, is not supported by Informatica.
# Users of this sample code in whole or in part or any extraction or derivative of it 
# assume all the risks attendant thereto, and Informatica disclaims any/all liabilities 
# arising from any such use to the fullest extent permitted by law.

### This file contains helper functions used throughout the iics promotion pipeline

import requests
import urllib
import time
import sys
import json


def iics_login(login_domain, iics_username, iics_password):

    URL = login_domain + "/saas/public/core/v3/login"
    BODY = {"username": iics_username,"password": iics_password}

    r = requests.post(url = URL, json = BODY)

    if r.status_code != 200:
        print("Caught exception: " + r.text)

    # extracting data in json format
    data = r.json()

    # return sessionId
    return data['userInfo']['sessionId']

def iics_pull_by_commit(url, session_id, commit_hash):
        
    HEADERS = {"Content-Type": "application/json; charset=utf-8", "INFA-SESSION-ID": session_id }
    BODY={ "commitHash": commit_hash}

    print("Syncing the commit " + commit_hash + " to the UAT ORG")

    # Sync Github and UAT Org
    p = requests.post(url + "/public/core/v3/pullByCommitHash", headers = HEADERS, json=BODY)

    if p.status_code != 200:
        print("Exception caught: " + p.text)
        return 99

    pull_json = p.json()

    print(p.json())

    PULL_ACTION_ID = pull_json['pullActionId']
    PULL_STATUS = 'IN_PROGRESS'

    while PULL_STATUS == 'IN_PROGRESS':
        print("Getting pull status from Informatica")
        time.sleep(10)
        ps = requests.get(url + '/public/core/v3/sourceControlAction/' + PULL_ACTION_ID, headers = HEADERS, json=BODY)
        pull_status_json = ps.json()
        PULL_STATUS = pull_status_json['status']['state']

    if PULL_STATUS != 'SUCCESSFUL':
        print('Exception caught: Pull was not successful')
        return 99
    else:
        return 0

def iics_pull_by_commit_object(url, session_id, commit_hash, object_id):
        
    HEADERS = {"Content-Type": "application/json; charset=utf-8", "INFA-SESSION-ID": session_id }
    BODY={ "commitHash": commit_hash, "objects": [ { "id": object_id } ] }

    print("Syncing the commit " + commit_hash + " to the UAT ORG for object: " + object_id)

    # Sync Github and UAT Org
    p = requests.post(url + "/public/core/v3/pull", headers = HEADERS, json=BODY)

    if p.status_code != 200:
        print("Exception caught: " + p.text)
        return 99

    pull_json = p.json()
    PULL_ACTION_ID = pull_json['pullActionId']
    PULL_STATUS = 'IN_PROGRESS'

    while PULL_STATUS == 'IN_PROGRESS':
        print("Getting pull status from Informatica")
        time.sleep(10)
        ps = requests.get(url + '/public/core/v3/sourceControlAction/' + PULL_ACTION_ID, headers = HEADERS, json=BODY)
        pull_status_json = ps.json()
        PULL_STATUS = pull_status_json['status']['state']

    if PULL_STATUS != 'SUCCESSFUL':
        print('Exception caught: Pull was not successful')
        return 99
    else:
        return 0


def iics_rollback_mapping(url, session_id, path_name, mapping_name):

    HEADERS = {"Content-Type": "application/json; charset=utf-8", "INFA-SESSION-ID": session_id }
    ### In query/body, the Type would need parameterized to rollback various object types
    QUERY = "path=='" + path_name + "/" + mapping_name + "' and type=='DTemplate'"
    BODY = { "objects": [ { "path": path_name + "/" + mapping_name, "type": "DTEMPLATE" }]}

    r = requests.get(url + "/public/core/v3/commitHistory?q=" + QUERY, headers = HEADERS)

    if r.status_code != 200:
        print("Exception caught: " + r.text)
        return 99

    o = requests.post(url + "/public/core/v3/lookup", headers = HEADERS, json = BODY)
    if o.status_code != 200:
        print("Exception caught: " + o.text)
        return 99

    commit_json = r.json()
    object_json = o.json()

    PREVIOUS_COMMIT_HASH = commit_json['commits'][1]['hash']
    OBJECT_ID = object_json['objects'][0]['id']

    print("Rolling back to previous HASH: " + PREVIOUS_COMMIT_HASH)

    SUCCESS = iics_pull_by_commit_object(url, session_id, PREVIOUS_COMMIT_HASH, OBJECT_ID)

    return SUCCESS
    