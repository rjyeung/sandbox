import argparse
import subprocess
import logging
import sys
import re
import os
import time
from pprint import pprint
#import paramiko
import requests
import json

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(funcName)-25s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# logger.setLevel(logging.DEBUG)
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
        logger.debug('Scp file {file} from remote server {remote_host} to orchestrator1 ({orch1}) /tmp folder'.format(
            file=remotepath, remote_host=server_next_hop, orch1=ip_addr))
        #client = paramiko.SSHClient()
        #client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #client.connect(hostname=ip_addr, username=os.environ['TET_USER'], password=os.environ['TET_USER'])
        #stdin, stdout, stderr = client.exec_command(command)
        logger.debug("...... ssh -o StrictHostKeyChecking=no {user}@{host} {cmd}".format(
            user=os.environ['TET_USER'], host=ip_addr, cmd=command))
        output1, errors1 = subprocess.Popen(
            "ssh -o StrictHostKeyChecking=no {user}@{host} {cmd}".format(user=os.environ['TET_USER'], host=ip_addr, cmd=command),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output1)
        logger.debug(errors1)
        time.sleep(10)

        # Copy from Orchestrator /tmp dir to local
        #sftp = client.open_sftp()
        #sftp.get('/tmp/'+os.path.basename(remotepath), localpath)
        #sftp.close()
        #client.close()
        logger.debug('Scp file {file} from orchestrator1 ({orch1}) /tmp to local host {localfile}'.format(
            file='/tmp/'+os.path.basename(remotepath), orch1=ip_addr, localfile=localpath))
        logger.debug("...... scp -v -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
            user=os.environ['TET_USER'], host=ip_addr, file='/tmp/'+os.path.basename(remotepath), localfile=localpath))
        output2, errors2 = subprocess.Popen(
            "scp -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
                user=os.environ['TET_USER'], host=ip_addr, file='/tmp/'+os.path.basename(remotepath), localfile=localpath),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output2)
        logger.debug(errors2)
    except Exception as e:
        logger.error(e)
        raise e

def get_orch_cluster_status_json(ip_addr=None):
    """Get cluster status json file, and copy to local"""

    try:
        file = '/tmp/orch_cluster_status.json'
        logger.debug("Issuing 'curl -s http://orchestrator.service.consul:8889/api/v1.0/cluster/status > {0}' in {1}".format(file, ip_addr))
        command = 'curl -s http://orchestrator.service.consul:8889/api/v1.0/cluster/status > {0}'.format(file)
        output1, errors1 = subprocess.Popen(
            "ssh -o StrictHostKeyChecking=no {user}@{host} '{cmd}'".format(user=os.environ['TET_USER'], host=ip_addr, cmd=command),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output1)
        logger.debug(errors1)

        localpath = "./{0}_orch_cluster_status.json".format(ip_addr)
        logger.debug('Scp from orchestrator1 ({orch1}) {file} to local host {localfile}'.format(
            file=file, orch1=ip_addr, localfile=localpath))
        logger.debug("...... scp -v -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
            user=os.environ['TET_USER'], host=ip_addr, file='/tmp/orch_cluster_status.json', localfile=localpath))
        output2, errors2 = subprocess.Popen(
            "scp -o StrictHostKeyChecking=no {user}@{host}:{file} {localfile}".format(
                user=os.environ['TET_USER'], host=ip_addr, file=file, localfile=localpath),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        logger.debug(output2)
        logger.debug(errors2)
        return localpath
    except Exception as e:
        logger.error(e)
        raise e

def extract_bad_vm_from_status_json(file=None):
    """Extract bad VM from orch_cluster_status.json"""

    try:
        vm_list = []
        return_msg = ''
        with open(file) as f:
            data = json.load(f)
        for instance in data['instances']:
            progress = data['instances'][instance]['progress']
            if progress < 0:
                # print (instance)
                msg = 'Found VM {0} (IP: {1}, Type: {2}) with negative progress status {3}'.format(
                    data['instances'][instance]['instanceName'], instance,
                    data['instances'][instance]['instanceType'], progress)
                logger.info(msg)
                vm_list.append(instance)
                return_msg += msg + '\n'
        return (vm_list, return_msg)
    except Exception as e:
        logger.error(e)
        raise e

def get_log_file_to_list(file_path=None):
    """Return a list of strings of a file"""
    log_list = open(file_path).readlines()
    # pprint (log_list)
    return log_list

def get_dict_log_list(input_list):
    """Return a dict of line_num index and string from input list if string matches"""
    log_dict = {i: elem for i, elem in enumerate(input_list) if 'Orchestrator state' in elem}
    # pprint ('Inside get_dict_log_list')
    # pprint ('Line number: line content')
    # pprint ('Line number: line content')
    # pprint (log_dict)
    return log_dict

def get_linenum_log_list(input_list):
    """Return a dict of line_num index and string from input list if string matches"""
    log_list = [str(i)+':'+elem for i, elem in enumerate(input_list) if 'Orchestrator state set to failed' in elem]
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

def update_summary_jira(crf_id, summary_text_to_add):
    logger.info('Update JIRA summary...')
    response = requests.get('{0}{1}'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS)
    summary_string_head = response.json()['fields']['summary'].rsplit(' - ', 1)[0]
    json_data = {
        "fields": {
            "summary": summary_string_head + ' - ' + summary_text_to_add
        }
    }
    response = requests.put('{0}{1}'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS_2, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to update JIRA summary')

def update_component_jira(crf_id, component):
    logger.info('Update JIRA component...')
    json_data =  {
        "fields" : {
            "components" : [{"name" : component}]
        }
    }
    response = requests.put('{0}{1}'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error(response.status_code)
        logger.error('Unable to update JIRA component')

def add_dup_link_jira(new_crf_id, old_crf_id):
    logger.info('Update JIRA dup link...')
    json_data = {
        "type": {
            "name": "Duplicate"
        },
        "inwardIssue": {
            "key": new_crf_id
        },
        "outwardIssue": {
            "key": old_crf_id
        },
    }
    response = requests.post('{0}'.format(JIRA_LINK_BASE), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error(response.status_code)
        logger.error('Unable to dup JIRA issue links')

def assign_jira(crf_id, assignee_id):
    logger.info('Update JIRA assignee...')
    # json_data = {"accountId": assignee_id}
    # response = requests.put('{0}{1}/assignee'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS_2, json=json_data)
    json_data = { "fields": {
                      "assignee":{"accountId": assignee_id}
                 }
             }
    response = requests.put('{0}{1}'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS_2, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error('Unable to assign JIRA ticket')

def add_related_link_jira(crf_id, related_crf_id):
    logger.info('Update JIRA related link...')
    json_data = {
        "type": {
            "name": "Relates"
        },
        "inwardIssue": {
            "key": crf_id
        },
        "outwardIssue": {
            "key": related_crf_id
        },
    }
    response = requests.post('{0}'.format(JIRA_LINK_BASE), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error(response.status_code)
        logger.error('Unable to add related JIRA issue links')

def resolve_dup_jira(crf_id):
    logger.info('Resolve JIRA as duplicate...')
    # https://tetration.atlassian.net/rest/api/latest/status
    # https://docs.atlassian.com/jira/REST/server/#api/2/issue-getTransitions
    # https://docs.atlassian.com/jira/REST/server/#api/2/issue-doTransition
    json_data = {
        "update": {},
        "transition": {
            "id": "5"
        },
        "fields": {
            "resolution": {
                "name": "Duplicate"
            }
        }
    }
    response = requests.post('{0}{1}/transitions'.format(JIRA_BASE, crf_id), headers=JIRA_HEADERS, json=json_data)
    if response.status_code < 200 or response.status_code > 299:
        logger.error(response.status_code)
        logger.error('Unable to mark Duplicate and resolve JIRA issue links')


def main():
    ''' 1. Get jira info form CRF-id input
        2. ssh to main orchestort and get orchestrator.log
        3. Find last Orhestrator state, and find out next log file to look into
        4. Get 2nd log file, find out what's wrong
        5. Update Jira
    '''

    global logger

    parser = argparse.ArgumentParser()
    # parser.add_argument('--orch-ip', '-i', default=None, help='Orchestrator External IP address')
    parser.add_argument('--crf_id', '-c', default=None, help='CRF id')
    parser.add_argument('--debug', '-d', action='store_true', help='If debugging, no ticket updating, no database insert')
    args = parser.parse_args()

    if args.crf_id is not None:
        response = requests.get('{0}{1}'.format(JIRA_BASE, args.crf_id), headers=JIRA_HEADERS)
        branch = None
        orch_ip_string = None

        # Get crf summary
        summary = response.json()['fields']['summary']
        create_date = response.json()['fields']['created'].split('T')[0]

        # Get release branch
        jira_label_list = response.json()['fields']['labels']
        for label in jira_label_list:
            if re.match(r"(release-[0-9a-zA-Z._]*|main_dev)", str(label).lower().strip()):
                branch = re.match(r"(release-[0-9a-zA-Z._]*|main_dev)", str(label).lower().strip()).group(1)
                logger.debug("Branch found from CRF = {0}".format(branch))
                break

        # Get Orchestrator IP
        jira_descr_list = response.json()['fields']['description'].splitlines()
        for line in jira_descr_list:
            if re.search(r"Cluster:", line):
                cluster = re.match(r"\*Cluster:\* +([a-zA-Z0-9\-_]+)", line).group(1)
                logger.debug("Cluster found from CRF = {0}".format(cluster))
            elif re.search(r"Orchestrator:", line):
                orch_ip_string = re.match(r"\*Orchestrator:\* +([0-9\.\"\,]+)", line).group(1)
                logger.debug("Orchestrator found from CRF = {0}".format(orch_ip_string))
                break
        # pprint (jira_descr_list)

        if branch is None or orch_ip_string is None:
            logger.error('Unable to obtain branch or orchestrater IP from JIRA ticket')
            sys.exit(1)

        # for (cluster, orch_ip) in list(zip(cluster.split("_"), orch_ip_string.replace('"', '').split(","))):
        for orch_ip in list(orch_ip_string.replace('"', '').split(",")):
            # Download the orchestrator.log
            # Parse out 'Orchestrator state' from log, and obtain last state
            # Grab lines before and after last 'Orchestrator state' from log
            signature_line = None
            log_file2_found_flag = False
            log_file2_check_flag = True
            logger.info('##########  For Cluster {0},   Orchestrator IP: {1} ##########'.format(cluster, orch_ip))
            logger.info('========== STEP 1: Getting Orchestrator.log {0} {1} ==============='.format(cluster, orch_ip))
            log_file1_name = '{0}_{1}.orchestrator.log'.format(args.crf_id, orch_ip)
            copy_file_to_local(orch_ip, '/local/logs/tetration/orchestrator/orchestrator.log',
                               './{0}'.format(log_file1_name))

            logger.info('========== STEP 2: Extract fail portion from orchestrator.log ===============')
            orch_log_list = get_log_file_to_list('./{0}'.format(log_file1_name))
            # orch_state_dict = get_dict_log_list(orch_log_list)
            orch_state_fail_list = get_linenum_log_list(orch_log_list)
            # pprint (orch_state_fail_list)
            # pprint (orch_state_list[-1].lower())
            if len(orch_state_fail_list) == 0:
                logger.warning('Not finding any "Orchestrator state set to fail".  Exiting orchestrator {0}...'.format(orch_ip))
                continue

            radius = 30
            # mid_pt = int(orch_state_list[-1].split(':')[0])
            mid_pt = int(orch_state_fail_list[0].split(':')[0])
            pprint (orch_log_list[mid_pt - radius: mid_pt+radius])
            if (mid_pt - radius) > 0:
                orch_log_extract_list = orch_log_list[mid_pt - radius: mid_pt+radius]
            else:
                orch_log_extract_list = orch_log_list[0: mid_pt+radius]
            # pprint (orch_log_extract_list)
            update_log1_string = ''.join(orch_log_extract_list)
            update_log1_string = "From orchestrator log:\n{code}" + update_log1_string + "{code}\n"
            logger.info(update_log1_string)
            if not args.debug:
                add_comment_jira(args.crf_id, comment_text=update_log1_string)
                attach_file_jira(args.crf_id, file_path='./'+log_file1_name)

            logger.info('========== STEP 3: Determine 2nd log file from orchestrator.log fail portion  ===============')
            # Analyze orchestrator.log, figure out what's 2nd file and get it
            # Also some special handling when no 2nd file is needed to grab signature
            match_dict = {
                'OrchestratorError: Ansible playbook:playbooks/orchestrator_postinstall_setup.yml failed rc:2': 'orchestrator/orchestrator_postinstall_setup_pb.log',
                'OrchestratorError: Ansible playbook:playbooks/consul_server.yml failed rc:2': 'orchestrator/consul_server_pb.log',
                'OrchestratorError: Ansible playbook:playbooks/orchestrator_setup.yml failed rc:2': 'orchestrator/orchestrator_setup_pb.log',
                'OrchestratorError: Invalid Stack response from stack manager: status:error errors:\[\]': 'esxmgr/esxmgr.log',
                '\[E\] [0-9-T:]+ orchestrator.py:1005 pop from empty list': None,
                'orchestrator_state.py:[0-9]* total_instances_up ([0-9]*), len of dbstate = ([0-9]*)[\s]*\[E\] [0-9-T:]+ orchestrator.py:[0-9]+ Orchestrator state set to failed': 'special_handling_1',
                'OrchestratorError: Ansible playbook:playbooks/pre_orchestrator_setup.yml failed rc:': 'orchestrator/pre_orchestrator_setup_pb.log',
                'OrchestratorError: Ansible playbook:playbooks/orchestrator_during_instance_deploy.yml failed rc:': 'orchestrator/orchestrator_during_instance_deploy_pb.log',
                'ORC-1002: BigBang playbook run failed, check Playbooks-Orch-Bigbang log': 'orchestrator/bigbang_pb.log',
                'ORC-1005: Pre Orchestrator Setup Playbook failed, check Playbooks-Orch-pre_orchestrator_setup log': 'orchestrator/pre_orchestrator_setup_pb.log',
                'ORC-1006: Bare metal setup playbook failed, check Playbooks-Orch-bare_metal log': 'orchestrator/bare_metal_pb.log',
                'ORC-1010: Stack Manager instance bring up failed, check VM Manager log': 'vmmgr/vmmgr.log',
                'ORC-1011: Orchestrator Setup Playbook failed, check Playbooks-Orch-orchestrator_setup': 'orchestrator/orchestrator_setup_pb.log',
                'ORC-1014: Instance \S* IP:([0-9.]*) deploy failed': 'servicemgr/build.log',
                'ORC-1015: Cluster certs playbook failed, check Playbooks-Orch-cluster_certs log': 'orchestrator/cluster_certs_pb.log',
                'ORC-1016: During instance playbook failed, check Playbooks-Orch-during_instance_deploy log': 'orchestrator/orchestrator_during_instance_deploy_pb.log',
                'ORC-1017: Post deploy playbook failed, check Playbook[s]?-Orch-orchestrator_postinstall_setup': 'orchestrator/orchestrator_postinstall_setup_pb.log',
            }
            server_next_hop = 'orchestrator.service.consul'
            for key, value in match_dict.items():
                match = re.search(key, '\n'.join(orch_log_extract_list))
                if match:
                    log_file2 = value
                    log_file2_found_flag = True
                    if log_file2 == 'servicemgr/build.log':
                        server_next_hop = match.group(1)
                        logger.info("Found next hop server {0}".format(server_next_hop))
                    elif log_file2 == 'vmmgr/vmmgr.log' and 'esx' in cluster.lower():
                        log_file2 = 'esxmgr/esxmgr.log'
                    elif log_file2 == 'special_handling_1':
                        total_instances_up = match.group(1)
                        dbstate_len = match.group(2)
                        if total_instances_up != dbstate_len:
                            cluster_status_json_local_filepath = get_orch_cluster_status_json(orch_ip)
                            (bad_vm_list, bad_vm_msg)= extract_bad_vm_from_status_json(cluster_status_json_local_filepath)
                            if not args.debug:
                                add_comment_jira(args.crf_id, comment_text=bad_vm_msg)
                                attach_file_jira(args.crf_id, file_path='./' + cluster_status_json_local_filepath)
                            log_file2 = 'servicemgr/build.log'
                            server_next_hop = bad_vm_list[-1]
                    elif log_file2 is None:
                        log_file2_check_flag = False
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", match.group(0)).strip()
                        signature_line = re.sub(r"[\'\"]", '', signature_line)
                    break

            if not log_file2_found_flag:
                logger.error("Cannot find 2nd log file to look into.  Need to update match_dict or radius range maybe")
                sys.exit(1)

            if log_file2_check_flag:
                logger.info('========== STEP 4: Getting Second log file ===============')
                if server_next_hop == 'orchestrator.service.consul':
                    log_file2_name = '{0}_{1}_{2}'.format(args.crf_id, orch_ip, os.path.basename(log_file2))
                else:
                    log_file2_name = '{0}_{1}_{2}_{3}'.format(args.crf_id, orch_ip, server_next_hop, os.path.basename(log_file2))
                copy_file_to_local(orch_ip, '/local/logs/tetration/{0}'.format(log_file2),
                                   './{0}'.format(log_file2_name), server_next_hop)

                logger.info('========== STEP 5: Analyze 2nd log file, extract signature line ===============')
                # Analyze 2nd log file, and figout out what went wrong
                # Reverse log file in to a list
                # Find failed=1 msg, get ip
                # Find failed ip, msg, and get Task
                sec_log_list = get_log_file_to_list('./{0}'.format(log_file2_name))
                trouble_ip = ''
                task_fail = False
                update_log2_string = ""

                while sec_log_list:
                    line = sec_log_list.pop()
                    match_1 = re.search(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) .* failed=[1-9]", line)
                    match_2 = re.search(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) .* unreachable=[1-9]", line)
                    match_3 = re.search(r"(failed|fatal): \[%s[ \]]" % trouble_ip, line)
                    match_4 = re.search(r"TASK[:]? \[(.*)\]", line)
                    match_5 = re.search(r"GATHERING FACTS", line)
                    match_6 = re.search(r"stack.py:330 Exception in StackHandler: Terraform command", line)
                    match_7 = re.search(r"stack.py:410 exception processing create request \('Connection aborted.',"
                                        r" BadStatusLine\(\"\'\'\",\)\)", line)
                    match_8 = re.search(r"stack.py:322 Stack creation failure on baremetal", line)
                    match_9 = re.search(r"cannot change the value of \"thin_provisioned\"", line)
                    match_10 = re.search(r"^.*hwinfo.py:50 Error inside baremetal hwinfo", line)
                    match_11 = re.search(r"RUNNING HANDLER[:]? \[(.*)\]", line)

                    if match_1:
                        logger.info("Found failed ip = {0}".format(match_1.group(1)))
                        trouble_ip = match_1.group(1)
                        update_log2_string = line + "...\n" + update_log2_string
                    elif match_2:
                        logger.info("Found unreachable ip = {0}".format(match_2.group(1)))
                        trouble_ip = match_2.group(1)
                        update_log2_string = line + "...\n" + update_log2_string
                    elif match_3:
                        logger.info("Found failed/fatal entry of {0}".format(match_3.group(1)))
                        task_fail = True
                        update_log2_string = line + "...\n" + update_log2_string
                    elif task_fail and match_4:
                        logger.info("Fail task = {0}".format(match_4.group(1)))
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", line).strip()
                        break
                    elif task_fail and match_5:
                        logger.info("Fail Gathering facts")
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", line).strip()
                        break
                    elif task_fail and match_11:
                        logger.info("Fail RUNNING HANDLER = {0}".format(match_11.group(1)))
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", line).strip()
                        break
                    elif match_6:
                        logger.info("Fail StackHandler")
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", line).strip()
                        signature_line = re.sub(r"[\'\"]", '', signature_line)
                        break
                    elif match_7:
                        logger.info("Fail stack processing create request")
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", line).strip()
                        signature_line = re.sub(r"[\'\"]", '', signature_line)
                        break
                    elif match_8:
                        logger.info("Fail stack creation on baremetal")
                        # e.g: [W] 2020-03-08T09:26:04 stack.py:322 Stack creation failure on baremetal WZP233005NH
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", line).strip()
                        signature_line = signature_line.rsplit(' ', 1)[0]   # remove baremetal id at the end of line
                        break
                    elif match_9:
                        logger.info("Vcenter raised cannot change the value of thin_provisioned")
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = match_9.group(0)
                        signature_line = re.sub(r"[\'\"]", '', signature_line)
                        break
                    elif match_10:
                        logger.info("Error inside baremetal hwinfo")
                        update_log2_string = line + "...\n" + update_log2_string
                        signature_line = re.sub(r"(\[[WIDE]\]) ([0-9-T:]+ )", r"\1 ", match_10.group(0)).strip()
                        break


                update_log2_string = "From " + log_file2 + ":\n{code}" + update_log2_string + "{code}\n"
                logger.info(update_log2_string)
                if not args.debug:
                    add_comment_jira (args.crf_id, comment_text=update_log2_string)
                    attach_file_jira(args.crf_id, file_path='./'+log_file2_name)

                if signature_line is None:
                    logger.error("Cannot find signature for this failure in {0}".format(log_file2_name))
                    continue

            logger.info('========== STEP 6: Add signature into Jira ===============')
            logger.info("signature_line = {0}".format(signature_line.strip()))
            if signature_line is not None and not args.debug:
                tmp_text = 'Signature_from_crf_orch_triage_automator = '+signature_line.strip()
                add_comment_jira (args.crf_id, comment_text=tmp_text)

    else:
        logger.error('Script argument need to have CRF id')
        sys.exit(1)


if __name__ == '__main__':
    return_value = main()
    sys.exit(return_value)
