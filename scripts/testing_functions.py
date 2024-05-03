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

def test_mtt(url, session_id, app_context_id):

    HEADERS_V2 = {"Content-Type": "application/json; charset=utf-8", "icSessionId": session_id }
    BODY = {"@type": "job","taskId": app_context_id,"taskType": "ZZZ"}

    t = requests.post(url + "/api/v2/job/", headers = HEADERS_V2, json = BODY )

    if t.status_code != 200:
        print("Exception caught: " + t.text)
        sys.exit(99)

    test_json = t.json()
    PARAMS = "?runId=" + str(test_json['runId'])
    #"?taskId=" + test_json['taskId']

    STATE=0
    
    while STATE == 0:
        time.sleep(20)
        a = requests.get(url + "/api/v2/activity/activityLog" + PARAMS, headers = HEADERS_V2)
        
        activity_log = a.json()

        STATE = activity_log[0]['state']

    if STATE != 1:
        print("Mapping task: " + activity_log[0]['objectName'] + " failed. ")
        RC = 99
    else:
        print("Mapping task: " + activity_log[0]['objectName'] + " completed successfully. ")
        RC = 0

    return RC