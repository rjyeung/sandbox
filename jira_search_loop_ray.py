#!/usr/bin/env python -u

import argparse
import logging
import os
import requests
import time
import json
import re
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta

from cluster_utils import check_rpm_install_status, check_upgrade_progress, get_upgrade_credentials, \
    login_cluster_ui, login_setup_ui, post_upgrade, stored, upgrade_step, upload_rpm_from_disk, \
    upload_rpm_from_object_store, get_upgrade_id, check_taguest_user
from configure_site import check_site_info, configure_site_info, do_site_validation_check
from retry_browser import RetryBrowser


mech_logger = logging.getLogger("mechanize")
mech_logger.addHandler(logging.StreamHandler(sys.stdout))
mech_logger.setLevel(logging.INFO)

dashdbhost="dashboard.tetrationanalytics.com"
dashdbuser=os.environ['TET_USER']
dashdbpass=os.environ['TET_SUPERPASSWORD']
dashdbbase="dashboard_db"
mysql_opts="-h{0} -u{1} -p{2} {3}".format(dashdbhost, dashdbuser, dashdbpass, dashdbbase)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(funcName)-25s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def jira_requests(qyery_name="", query_ext="", max_return=100, start_at=20):
    jira_search = 'https://tetration.atlassian.net/rest/api/2/search?jql='
    # return only summary, lablels, description and comment fields instead of default
    search_opt = '&maxResults={0}&startAt={1}&fields=summary,labels,description,comment'.format(max_return, start_at)
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Content-Type': 'application/json',
        'Authorization': 'Basic ****************BlockForPrivacy*******************='
    }

    response = requests.get('{0}{1}{2}'.format(jira_search,
                                               query_ext,
                                               search_opt
                                              ), headers=headers)

    # logger.info("%s CRF tickets this %s:  Total = %s, StartAt = %s, MaxResult = %s",
    #             qyery_name,
    #             search_opt,
    #             response.json().get('total'),
    #             response.json().get('startAt'),
    #             response.json().get('maxResults'))
    # logger.info(json.dumps(json.loads(response.text), indent=2))
    return response

def jira_parse(response):
    issues = response.json()['issues'];
    counter = 0
    for issue in issues:

        # print issue['fields']['labels']
        # print issue['fields']['summary']
        # print issue['key']
        # print issue['fields']['comment']


        descr_list = issue['fields']['description'].splitlines()
        mode_flag = False
        signature_found = False
        github_urls = []
        for line in descr_list:
            # Only care about Deploy, upgrade or reboot failures
            if re.search('Mode:\* (DEPLOY|UPGRADE|REBOOT)', line):
                # print issue['key']
                # print issue['fields']['summary']
                mode_flag = True
            elif re.search('TASK.*\[', line):
                signature_line = re.sub(r"\{(code|noformat)\}", '', line)
                signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", signature_line)
                signature_line = re.sub(r"[0-9][0-9]:[0-9][0-9]:[0-9][0-9] ", '', signature_line)
                signature_found = True
                # print "found task failure"
                # print str(issue['key']) + str(issue['fields']['summary'])  + ': ' +str(issue['fields']['labels'][0])
                # print line
                # print line_2
            # print "\n"

        github_urls = re.findall('http[s]?://github[\.a-zA-Z\/0-9_-]+', str(issue['fields']['comment']))
        github_link = ' '.join(github_urls)
        # print url

        if not mode_flag:
            continue
        elif signature_found:
            print str(issue['key']) + '\t' + str(issue['fields']['summary'])  + '\t'  + str(issue['fields']['labels'][0])  + '\t' + signature_line + '\t' + str(github_link)




     # response.json().get('issues')

    # logger.info("%s CRF tickets this %s:  Total = %s, StartAt = %s, MaxResult = %s",
    #             'aaa',
    #             'bbb',
    #             response.json().get('total'),
    #             response.json().get('startAt'),
    #             response.json().get('maxResults'))
    # logger.info(json.dumps(json.loads(response.text), indent=2))
    # return response


def main():
    MAX_RESULT=100
    i = 0

    while True:
        r = jira_requests("Ray", "project=CRF%20and%20issuetype=Bug%20and%20labels%20is%20NOT%20EMPTY%20and%20resolution%20!%3D%20Duplicate", MAX_RESULT, i)
        i += MAX_RESULT;
        if len(r.json().get('issues')) <= 0:
            break
        else:
            jira_parse(r)




if __name__ == '__main__':
    main()
