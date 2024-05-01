import argparse
import subprocess
import logging
import sys
import re
import os
import time
import requests
import ast
from pprint import pprint


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(funcName)-25s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

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

def copy_file_to_local(ip_addr=None, remotepath=None, localpath=None, server_next_hop='orchestrator.service.consul'):
    """Copy file from Orchestrator (or other secondary server) to Orchestrator 1 then to local"""

    try:
        # Copy from active Orchestrator to Orchestrator-1 /tmp directory
        # command='ssh $TET_USER@' + ip + ' sudo -u $TET_SUPERUSER scp orchestrator.service.consul:' + remotepath + ' /tmp'
        command = 'sudo -u ' + os.environ['TET_SUPERUSER'] + ' scp -v -o StrictHostKeyChecking=no ' + server_next_hop +':' + remotepath + ' /tmp'
        logger.info('Scp file {file} from remote server {remote_host} to hop server ({hop_host}) /tmp folder'.format(
            file=remotepath, remote_host=server_next_hop, hop_host=ip_addr))
        #client = paramiko.SSHClient()
        #client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #client.connect(hostname=ip_addr, username=os.environ['TET_USER'], password=os.environ['TET_USER'])
        #stdin, stdout, stderr = client.exec_command(command)
        logger.info("Executing: ssh -o StrictHostKeyChecking=no {user}@{host} {cmd}".format(
            user=os.environ['TET_USER'], host=ip_addr, cmd=command))
        output, errors = subprocess.Popen(
            "ssh -o StrictHostKeyChecking=no {user}@{host} {cmd}".format(user=os.environ['TET_USER'], host=ip_addr, cmd=command),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output)
        logger.debug(errors)
        time.sleep(10)

        # Copy from Orchestrator /tmp dir to local
        #sftp = client.open_sftp()
        #sftp.get('/tmp/'+os.path.basename(remotepath), localpath)
        #sftp.close()
        #client.close()
        logger.info('Scp file {file} from hop server ({hop_host}) /tmp to local host {localfile}'.format(
            file='/tmp/'+os.path.basename(remotepath), hop_host=ip_addr, localfile=localpath))
        logger.info("Executing: scp -v -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
            user=os.environ['TET_USER'], host=ip_addr, file='/tmp/'+os.path.basename(remotepath), localfile=localpath))
        output, errors = subprocess.Popen(
            "scp -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
                user=os.environ['TET_USER'], host=ip_addr, file='/tmp/'+os.path.basename(remotepath), localfile=localpath),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output)
        logger.debug(errors)
    except Exception as e:
        logger.info(output)
        logger.info(errors)
        logger.error(e)
        raise e

def get_log_file_to_list(file_path=None):
    """Return a list of strings of a file"""
    log_list = open(file_path).readlines()
    # pprint (log_list)
    return log_list

def add_comment_jira(crf_id, comment_text=None):
    """Add comment to jira ticket"""
    json_data = {"body": comment_text}
    response = requests.post('{0}{1}/comment'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to add comment to JIRA ticket')

def attach_file_jira(crf_id, file_path=None):
    """Attach file to jira ticket"""
    file_data = {'file': open(file_path, 'rb')}
    response = requests.post('{0}{1}/attachments'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS_2, files=file_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to attach file to JIRA ticket')

def extract_fw_upgrade_status(log_list):
    """Extract firmware upgrade status for all BMs from log_list with contents from fwmgr/current file"""
    fw_upgrade_status_dict = {}
    cimc_dict = {}
    for log_line in reversed(log_list):
        m1 = re.search("200 GET /api/v1.0/firmware/upgrade/status\?serial=([a-zA-Z0-9\-]+)", log_line)
        m2 = re.search('Returning firmware update status: (.*)', log_line)
        m3 = re.search('cimcinfo for ([a-zA-Z0-9\-]+):.*cimc_ip\': u\'([0-9\.]+)', log_line)
        if m1:
            serial_num = m1.group(1)
            if serial_num not in fw_upgrade_status_dict.keys():
                logger.debug("Find firmware upgrade status for " + serial_num)
                next_line_matters_flag = True
            else:
                continue
        elif m2 and next_line_matters_flag:
            fw_upgrade_status_dict[serial_num] = m2.group(1)
            next_line_matters_flag = False
        elif m3:
            serial_num = m3.group(1)
            cimc_ip = m3.group(2)
            cimc_dict[serial_num] = cimc_ip
    logger.debug("Found fw_upgrade_status_dict: {}".format(fw_upgrade_status_dict))
    logger.debug("Found cimc_dict: {}".format(cimc_dict))
    return fw_upgrade_status_dict, cimc_dict


def detect_fw_upgrade_fail(fw_upgrade_status_dict):
    failed_fw_upgrade_dict = {}
    for serial_num, status_str in fw_upgrade_status_dict.items():
        if re.search('fail|error|exception|timed out|bad', status_str, re.IGNORECASE):
            logger.info("Found firmware upgrade failure for Serial " + serial_num)
            failed_fw_upgrade_dict[serial_num]=status_str

    logger.debug("Found failed_fw_upgrade_dict: {}".format(failed_fw_upgrade_dict))
    return failed_fw_upgrade_dict


def format_fw_upgrade_status_jira(status_str):
    fw_upgrade_status_list = ast.literal_eval(status_str)
    msg = "{noformat}" + '\n'.join(reversed(fw_upgrade_status_list)) + "{noformat}"
    return msg


def main():
    ''' 1. Get jira info form RF-id input
        2. ssh to all orchestrators and get fwmgr/current
        3. Find all firmware upgrade failures in all BM, and update jira ticket with status and info
        4. Find "Updating fwupdate status with Timeout Error", and obtain bm id
        5. Grep "update_fw_{bm_id}" from log, ignore 4 often recurring message
        6. Parse and update log file
        7. Update Jira for timeout errors
    '''

    global logger

    parser = argparse.ArgumentParser()
    parser.add_argument('--rf_id', '-i', default=None, help='RF id')
    parser.add_argument('--debug', '-d', action='store_true', help='If debugging, no ticket updating, no database insert')
    args = parser.parse_args()

    if args.rf_id is not None:
        response = requests.get('{0}{1}'.format(JIRA_BASE, args.rf_id), headers=JIRA_HEADERS)
        branch = None
        orch_ip_string = None

        # Get Orchestrator IP
        jira_descr_list = response.json()['fields']['description'].splitlines()
        for line in jira_descr_list:
            if re.search(r"Cluster:", line):
                cluster = re.match(r"\*Cluster:\* +([a-zA-Z0-9\-_]+)", line).group(1)
                logger.debug("Cluster found from RF = {0}".format(cluster))
            elif re.search(r"Orchestrator:", line):
                orch_ip_string = re.match(r"\*Orchestrator:\* +([0-9\.\"\,]+)", line).group(1)
                logger.debug("Orchestrator found from RF = {0}".format(orch_ip_string))
                break

        orch_list = ['orchestrator-1', 'orchestrator-2', 'orchestrator-3']
        for orch_ip in list(orch_ip_string.replace('"', '').split(",")):
            # Download the fwmgr/current log from orchestrator
            # Parse out 'Orchestrator state' from log, and obtain last state
            # Grab lines before and after last 'Orchestrator state' from log
            logger.info('##########  For Cluster {0},   Orchestrator IP: {1} ##########'.format(cluster, orch_ip))

            for orchestrator in orch_list:
                logger.info("orchestrator = {}".format(orchestrator))
                logger.info('========== STEP 1: Getting fwmgr/current log {0} {1} {2} =========='.format(cluster, orch_ip, orchestrator))
                try:
                    log_file1_name = '{0}_{1}_{2}_fwmgr_current.log'.format(args.rf_id, orch_ip, orchestrator)
                    copy_file_to_local(orch_ip, '/local/logs/tetration/fwmgr/current',
                               './{0}'.format(log_file1_name), orchestrator)

                    log_list = get_log_file_to_list('./{0}'.format(log_file1_name))
                except:
                    logger.warn("Exception raised copying fwmgr log from {0} to local via {1}".format(orchestrator, orch_ip))
                    continue
                logger.info('========== STEP 2: Check if firmware update failure occurs in  from fwmgr/current log ==========')
                fw_upgrade_status_dict, cimc_dict = extract_fw_upgrade_status(log_list);
                failed_fw_upgrade_dict = detect_fw_upgrade_fail(fw_upgrade_status_dict)
                for serial, status_str in failed_fw_upgrade_dict.items():
                    logger.info('========== Found Firmware upgrade error, update JIRA if debug mode is not enabled. ==========')
                    jira_text = "From {0} {1}, detect failed firmware upgrade.\nFirmware upgrade status for {2} (CIMC IP: {3}).\n".format(
                        orch_ip, orchestrator, serial, cimc_dict[serial])
                    jira_text += format_fw_upgrade_status_jira(status_str)
                    logger.info(jira_text)
                    if not args.debug:
                        add_comment_jira(args.rf_id, comment_text=jira_text)
                # continue;

                logger.info('========== STEP 3: Check if timeout error occurs in  from fwmgr/current log ==========')
                # Go through the log file once to determine if we are seeing timeout error, and get bm_id
                bm_id_set = set()
                for log_line in log_list:
                    if re.search("update_fw_.*update_fwupdate_status: Updating fwupdate status with Timeout Error", log_line) or \
                        re.search('update_fw_.*The read operation timed out', log_line):
                        # bm_id = re.search(r"(update_fw_[a-zA-Z0-9]+)", log_line).group(1)
                        bm_id_set.add(re.search(r"(update_fw_[a-zA-Z0-9]+)", log_line).group(1))

                if len(bm_id_set) == 0:
                    logger.info('No timeout error occurs.')
                else:
                    logger.debug("BM serial numbers to look for = ".format(str(bm_id_set)))

                # Go through the log file again to extract all related lines.
                for bm_id in bm_id_set:
                    jira_str = ""
                    m1_new_flag = m2_new_flag = m3_new_flag = m4_new_flag = True
                    for log_line in log_list:
                        if re.search(bm_id, log_line):
                            m1 = re.search("monitor_fwupdate: Getting fwupdate from cimc", log_line)
                            m2 = re.search("monitor_fwupdate: fwupdate", log_line)
                            m3 = re.search("monitor_fwupdate: comp_upd_status", log_line)
                            m4 = re.search("monitor_fwupdate: fwupdate start time", log_line)
                            m_cimc = re.search("([0-9\.]+) cimcendpoint.py", log_line)
                            if m1_new_flag and m1:
                                m1_new_flag = False
                                jira_str += log_line
                            elif m2_new_flag and m2:
                                m2_new_flag = False
                                jira_str += log_line
                            elif m3_new_flag and m3:
                                m3_new_flag = False
                                jira_str += log_line
                            elif m4_new_flag and m4:
                                m4_new_flag = False
                                jira_str += log_line
                            elif m1 or m2 or m3 or m4:
                                jira_str += '.'
                            elif m_cimc:
                                cimc_ip = m_cimc.group(1)
                                jira_str += log_line
                            else:
                                jira_str += log_line

                    logger.info('========== Found Timeout error, update JIRA if debug mode is not enabled. ==========')
                    if len(jira_str) < 32000:
                        jira_text = "From {0} {1} (CIMC_IP = {2}), we found {3} Timeout error in fwmgr log.\n".format(orch_ip, orchestrator, cimc_ip, bm_id)
                        jira_text += "{noformat}" + jira_str + "{noformat}"
                        # print jira_text
                        if not args.debug:
                            add_comment_jira(args.rf_id, comment_text=jira_text)
                    else:
                        with open("./{0}_fwmgr_log_extract_{1}.txt".format(orchestrator, bm_id), "w") as text_file:
                            text_file.write("From {0} {1} (CIMC_IP = {2}), we found {3} Timeout error in fwmgr log.\n".format(orch_ip, orchestrator, cimc_ip, bm_id))
                            text_file.write(jira_str)
                        if not args.debug:
                            attach_file_jira(args.rf_id, file_path="./{0}_fwmgr_log_extract_{1}.txt".format(orchestrator, bm_id))

    else:
        logger.error('Script argument need to have RF id')
        sys.exit(1)


if __name__ == '__main__':
    logger.info("Entering rf_fwmgr_triage_automator.py")
    return_value = main()
    logger.info("Exiting rf_fwmgr_triage_automator.py")
    sys.exit(return_value)
