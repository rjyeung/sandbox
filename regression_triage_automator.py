import argparse
import subprocess
import logging
import sys
import re
import os
import time
from pprint import pprint
import requests
import json

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(funcName)-25s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

JIRA_BASE = 'https://tetration.atlassian.net/rest/api/2/issue/'
JIRA_LINK_BASE = 'https://tetration.atlassian.net/rest/api/2/issueLink'
JIRA_HEADERS = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Content-Type': 'application/json',
    'Authorization': 'Basic ****************BlockForPrivacy*******************='
}
JIRA_HEADERS_2 = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    "X-Atlassian-Token": "nocheck",
    'Authorization': 'Basic ****************BlockForPrivacy*******************='
}

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
# logging.basicConfig(level=logging.WARNING)

def copy_file_from_sever_to_local(ip_addr=None, remotepath=None, localpath=None, user=None):
    """Copy file from remote server to local"""

    try:
        logger.debug('Scp file {file} from server ({sever}) to local host {localfile}'.format(
            file=remotepath, sever=ip_addr, localfile=localpath))
        logger.debug("...... scp -v -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
            user=user, host=ip_addr, file=remotepath, localfile=localpath))
        output, errors = subprocess.Popen(
            "scp -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
                user=user, host=ip_addr, file=remotepath, localfile=localpath),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output)
        logger.debug(errors)
    except Exception as e:
        logger.error(e)
        raise e

def add_comment_jira(jira_id, comment_text=None):
    """Add comment to jira ticket"""
    json_data = {"body": comment_text}
    response = requests.post('{0}{1}/comment'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to add comment to JIRA ticket')

def attach_file_jira(jira_id, file_path=None):
    """Attach file to jira ticket"""
    file_data = {'file': open(file_path, 'rb')}
    response = requests.post('{0}{1}/attachments'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS_2, files=file_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to attach file to JIRA ticket')

def update_summary_jira(jira_id, summary_text_to_add):
    logger.info('Update JIRA summary...')
    response = requests.get('{0}{1}'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS)
    summary_string_head = response.json()['fields']['summary'].rsplit(' - ', 1)[0]
    json_data = {
        "fields": {
            "summary": summary_string_head + ' - ' + summary_text_to_add
        }
    }
    response = requests.put('{0}{1}'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS_2, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to update JIRA summary')

def update_description_jira(jira_id, description_text_to_add):
    logger.info('Update JIRA description...')
    response = requests.get('{0}{1}'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS)
    # print response.json()['fields']['description']
    json_data = {
        "fields": {
            "description": response.json()['fields']['description'] + '\n' + description_text_to_add
        }
    }
    response = requests.put('{0}{1}'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS_2, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to update JIRA description')

def update_component_jira(jira_id, component):
    logger.info('Update JIRA component...')
    json_data =  {
        "fields" : {
            "components" : [{"name" : component}]
        }
    }
    response = requests.put('{0}{1}'.format(JIRA_BASE, jira_id), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error(response.status_code)
        logger.error('Unable to update JIRA component')

def add_dup_link_jira(new_jira_id, old_jira_id):
    logger.info('Update JIRA dup link...')
    json_data = {
        "type": {
            "name": "Duplicate"
        },
        "inwardIssue": {
            "key": new_jira_id
        },
        "outwardIssue": {
            "key": old_jira_id
        },
    }
    response = requests.post('{0}'.format(JIRA_LINK_BASE), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error(response.status_code)
        logger.error('Unable to dup JIRA issue links')

def main():
    ''' 1. Get info from Jira site with jira-id (via request call with retries, using request to preserve timestamp info)
        2. Parse and process the console log from the 1st link in job link
        3. Locate the nearest error/traceback from "Performing Post build task" line in console log
        4. If last error is from ansible, find the responsible task
        5. Update jira ticket in description
        6. Download the jira_triage.txt file from jenkins master vm with scp. (This can also be done via request)
        7. If applicable, also update jira ticket.
    '''

    global logger

    parser = argparse.ArgumentParser()
    parser.add_argument('--jira_id', '-j', default=None, help='Jira id')
    parser.add_argument('--user', '-u', default=None, help='Jenkins username')
    parser.add_argument('--password', '-p', default=None, help='Jenkins password')
    parser.add_argument('--debug', '-d', action='store_true', help='If debugging, no ticket updating.')
    args = parser.parse_args()
    username = args.user
    password = args.password

    if args.jira_id is not None and args.user is not None and args.password is not None:
        response = requests.get('{0}{1}'.format(JIRA_BASE, args.jira_id), headers=JIRA_HEADERS)

        # Get crf summary
        summary = response.json()['fields']['summary']

        jira_descr_list = response.json()['fields']['description'].splitlines()
        for line in jira_descr_list:
            if re.search(r"Check:", line):
                path_string = re.match(r"\*Check:\* +.*/job/(.*)", line).group(1)
                logger.debug("Path string found from CRF = {0}".format(path_string))
                full_path = '/local/jenkins/builds/' + path_string.strip() + '/archive/jira_triage.txt'
                # print (full_path)
            elif re.search(r"Job:", line):
                job_string = re.match(r"\*Job:\* +([\S]+)", line).group(1)
                logger.debug("Job found from CRF = {0}".format(job_string))
                job_string = job_string.split('|')[0].replace('[', '')
                # job_string += '/console'
                break
        # pprint (jira_descr_list)
        # http: // jenkins - vm.tetrationanalytics.com:8080 / job / HA_regress_fw_upgrade / 7342 / consoleText
        # response = requests.get('{0}'.format(job_string), headers=JENKIN_HEADERS_2)

        jira_text=''
        signature_line = ''
        found_text = ''
        log_list = []
        log_list_before_postbuild = []
        found_first_error_flag = False
        trouble_ip = ''
        task_fail = False
        capture_line_count = 0
        range=50
        retry = 10
        while retry>0 and len(job_string)>0:
            try:
                response = requests.get(job_string+'/console', auth=(username, password))
                if response.status_code >= 200 or response.status_code <= 299:
                    log_list = response.text.split('\n')
                    break
                else:
                    logger.warning("Retries %s left, response status code is , %s", retry, e)
            except Exception as e:
                logger.warning("Retries %s left, exception in getting jenkins console log, %s", retry, response.status_code)

            if retry <= 0:
                logger.error ("Request call raised exception or have non 200 status code ")
            time.sleep(60)
            retry = retry - 1

        # We are seeing multiple 'Performing Post build task' lines.  Get console log til the 1st occurrence.
        # Also scan onward for signatures
        for line in log_list:
            line=(re.sub("<.*?>", '', line, 999999999))   # Remove html tags
            match_fw_update_1 = re.search(r"(Timed out waiting for NIHUU mount).*(Firmware update has timed out)", line)
            if re.search('Performing Post build task', line):
                break
            elif re.search('Help us localize this page', line):
                break
            elif re.search('Page generated:', line):
                break
            elif match_fw_update_1:
                signature_line = match_fw_update_1.group(1) + '...' + match_fw_update_1.group(2)
                found_text = found_text + line + "\n...\n"
            elif re.search('ERROR', line):
                found_text = found_text + line + "\n...\n"

            log_list_before_postbuild.append(line)

        # Do it in reversed to gather last portion of consol log for jira description, 
        # also scan for signature for ansible failed tasks
        for line in reversed(log_list_before_postbuild):
            # Remove html tags
            line=(re.sub("<.*?>", '', line, 999999999))
            match_1 = re.search(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) .* failed=[1-9]", line)
            match_2 = re.search(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) .* unreachable=[1-9]", line)

            if found_first_error_flag == False:
                jira_text = line + "...\n" + jira_text
                capture_line_count += 1
                if re.search('(Traceback|ImcException)', line):
                    found_first_error_flag = True
                    break
                elif re.search('(FAILED:|ERROR:)', line):
                    found_first_error_flag = True
                    break
                elif match_1:
                    trouble_ip = match_1.group(1)
                    found_first_error_flag = True
                elif match_2:
                    trouble_ip = match_2.group(1)
                    found_first_error_flag = True
                 
            if capture_line_count > range and len(trouble_ip) == 0:
                break

            if len(trouble_ip) > 0:
                if re.search(r"(failed|fatal): \[%s\]" % trouble_ip, line):
                    jira_text = line + "...\n" + jira_text
                    task_fail = True
                elif re.search(r"(TASK[:]? \[(.*)\])", line) and task_fail:
                    jira_text = line + "...\n" + jira_text
                    signature_line = re.search(r"(TASK[:]? \[(.*)\])", line).group(1)
                    break
                elif re.search(r"GATHERING FACTS", line) and task_fail:
                    jira_text = line + "...\n" + jira_text
                    break

        logger.info(jira_text)

        if len(jira_text) > 0 and not args.debug:
            jira_text = "From jenkins console log:\n{code}\n" + jira_text + "\n{code}\n"
            update_description_jira(args.jira_id, description_text_to_add=jira_text)

        if len(found_text) > 0 and not args.debug:
            found_text = "Also found following in jenkins console log:\n{code}\n" + found_text + "\n{code}\n"
            add_comment_jira(args.jira_id, comment_text=found_text)

        if len(signature_line) > 0 and not args.debug:
            tmp_text = 'Signature_from_regression_triage_automator = '+signature_line.strip()
            add_comment_jira (args.jira_id, comment_text=tmp_text)

        try:
            os.remove('./jira_triage.txt')
        except OSError:
            pass

        copy_file_from_sever_to_local(ip_addr='jenkins-vm.tetrationanalytics.com', remotepath=full_path, localpath='.', user='jenkins')
        try:
            f = open("./jira_triage.txt")
            # Do something with the file
            string = f.read()
            if len(string) > 0 and not args.debug:
                jira_text = "From jira triage log:\n{code}\n" + string + "\n{code}\n"
                update_description_jira(args.jira_id, description_text_to_add=jira_text)
                logger.info (jira_text)
        except IOError:
            logger.warning("File jira_triage.txt not accessible")

    else:
        logger.error('Script argument need to have CRF id, jenkins username, and jenkins password')
        sys.exit(1)


if __name__ == '__main__':
    return_value = main()
    sys.exit(return_value)
