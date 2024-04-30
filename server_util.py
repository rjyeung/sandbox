#!/usr/bin/env python

import logging
import mechanize
import urllib2
from BeautifulSoup import BeautifulSoup
from packaging import version
import json
import argparse
import ssl
import sys
from tetpyclient import RestClient
import requests.packages.urllib3
reload(sys)
sys.setdefaultencoding('utf8')
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--function', help='utility function')
parser.add_argument('-d', '--debug', type=bool, default=False, help='Debug Flag')

parser.add_argument('-s', '--scope',  default='', help='use as standalone and following arguments will follow')
parser.add_argument('-sd', '--scale_dir', default='/local/scale', help='scale folder path')
parser.add_argument('-aksp', '--api_key_secret_path', default='/local/scale/server/api_key_secret.txt', help='api key secret file path')
parser.add_argument('-sh', '--sensor_hostname', default='scale', help='container name prefix')
parser.add_argument('-sop', '--sensor_os_platform', default='Ubuntu', help='choice of Ubuntu CentOS Windows Oracle SUSE')
parser.add_argument('-sov', '--sensor_os_version', default='16.04', help='os specific version 16.04 7.4')
parser.add_argument('-sv', '--sensor_version', default='latest', help='set specific version, e.g. 3.0.1.16.devel')
parser.add_argument('-st', '--sensor_type', default='3', help='choice of 1 2 3 which represents legacy, sensor, enforcer')
parser.add_argument('-sf', '--sensor_filepath', default='./', help='location to save the downloaded sensor file')
parser.add_argument('-cn', '--cluster_name', default='max', help='cluster name')
parser.add_argument('-cui', '--cluster_uiip', default='', help='if specified, will use the ui ip instead of domain name')
parser.add_argument('-cu', '--cluster_user', default='team-x-all', help='username')
parser.add_argument('-cp', '--cluster_password', default='', help='current password')
parser.add_argument('-cpo', '--cluster_password_old', default='', help='old password')
parser.add_argument('-cak', '--cluster_api_key', default='', help='generated key')
parser.add_argument('-cas', '--cluster_api_secret', default='', help='generated secrete')
parser.add_argument('-cad', '--cluster_api_description', default='sensor_scale_test', help='api description')

logger = logging.getLogger(__name__)


def globally_disable_ssl_verification():
    """
    http://legacy.python.org/dev/peps/pep-0476/
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

globally_disable_ssl_verification()


def download_rpm(cluster_browser, sensor_os_platform, sensor_os_version, sensor_version, sensor_type, sensor_filepath):
    browser = cluster_browser.browser
    headers = cluster_browser.headers
    endpoint = cluster_browser.endpoint
    url = endpoint + '/api/sensor_sw_versions.json'
    request = urllib2.Request(url, None, headers)
    response = browser.open(request)
    sensors = json.loads(response.get_data())
    if sensor_version == 'latest':
        try:
            url = endpoint + '/version.json'
            request = urllib2.Request(url, None, headers)
            response = browser.open(request)
            sensor_version = json.loads(response.get_data())['manifest']['version']
        except ValueError:
            url = endpoint + '/api/version.json'
            request = urllib2.Request(url, None, headers)
            response = browser.open(request)
            sensor_version = json.loads(response.get_data())['manifest']['version']

    file_id = "unknown"
    filename = "unknown"
    max_version = "unknown"
    for sensor in sensors:
        if sensor_os_platform in sensor['platform'] \
                and sensor_os_version in sensor['platform'] \
                and sensor['agent_type'] == int(sensor_type) \
                and sensor_version in sensor['version'] and sensor_version != "":
            file_id = sensor['id']
            filename = sensor['filename']
            break
        if version.parse(sensor['version']) > version.parse(max_version) \
                and sensor_os_platform in sensor['platform'] \
                and sensor_os_version in sensor['platform'] \
                and sensor['agent_type'] == int(sensor_type):
            max_version = sensor['version']
            file_id = sensor['id']
            filename = sensor['filename']

    browser.retrieve("%s/api/sensor_sw_versions/%s/download" % (endpoint, file_id),
                     "%s/%s" % (sensor_filepath, filename) )


def clean_rails(tet_client, container_hostname):
    limit = 5000
    offset = ''
    while True:
        resp = tet_client.get('/sensors?limit=%d&offset=%s' % (limit, offset))
        if resp.status_code != 200:
            logging.debug("Error msg - %s" % resp.text)
            break
        else:
            parsed_resp = json.loads(resp.content)
            for sensor in parsed_resp['results']:
                if container_hostname in sensor['host_name'] and 'deleted_at' not in sensor:
                    tet_client.delete('/sensors/%s' % sensor['uuid'])
            offset = parsed_resp.get('offset', "")
            if offset is None or offset == '':
                break


def latest_version(cluster_browser):
    browser = cluster_browser.browser
    headers = cluster_browser.headers
    endpoint = cluster_browser.endpoint

    try:
        url = endpoint + '/version.json'
        request = urllib2.Request(url, None, headers)
        response = browser.open(request)
        version = json.loads(response.get_data())['manifest']['version']
    except ValueError:
        url = endpoint + '/api/version.json'
        request = urllib2.Request(url, None, headers)
        response = browser.open(request)
        version = json.loads(response.get_data())['manifest']['version']

    return version


def sensor_info(tet_client, container_hostname):
    limit = 5000
    offset = ''
    counter = 0
    sensor_list = []
    while True:
        resp = tet_client.get('/sensors?limit=%d&offset=%s' % (limit, offset))
        if resp.status_code != 200:
            logging.debug("Error msg - %s" % resp.text)
            break
        else:
            parsed_resp = json.loads(resp.content)
            for sensor in parsed_resp['results']:
                if container_hostname in sensor['host_name'] and 'deleted_at' not in sensor:
                    counter += 1
                    sensor_list.append(sensor['host_name'])
            offset = parsed_resp.get('offset', "")
            if offset is None or offset == '':
                break

    return counter, ','.join(sensor_list)


def get_client(cluster_uiip, cluster_name, cluster_api_key, cluster_api_secret):
    if cluster_uiip == '':
        cluster_url = 'https://%s.tetrationanalytics.com' % cluster_name
    else:
        cluster_url = 'https://%s' % cluster_uiip
    return RestClient(cluster_url,
                      api_key=cluster_api_key, api_secret=cluster_api_secret, verify=False)


def get_browser(cluster_uiip, cluster_name, scale_dir, cluster_user, cluster_password, cluster_password_old):
    if len(cluster_uiip) > 0:
        cluster_url = 'https://%s' % cluster_uiip
    else:
        cluster_url = 'https://%s.tetrationanalytics.com' % cluster_name
    endpoint = cluster_url
    headers = {'X-CSRF-Token': '', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    browser = mechanize.Browser()
    browser.add_client_certificate(endpoint,
                                   cert_file='%s/certs/domain.crt' % scale_dir,
                                   key_file='%s/certs/domain.key' % scale_dir)
    browser.set_handle_robots(False)
    browser.set_handle_redirect(True)
    try:
        browser.open('%s/h4_users/sign_in' % endpoint)
        browser.select_form(nr=0)
        browser['h4_user[email]'] = "%s@tetrationanalytics.com" % cluster_user
        browser['h4_user[password]'] = cluster_password
        browser.submit()
        request = urllib2.Request('%s/' % endpoint, None, headers)
        result = browser.open(request)
        if "Please sign in to continue" in result.get_data():
            browser.open('%s/h4_users/sign_in' % endpoint)
            browser.select_form(nr=0)
            browser['h4_user[email]'] = "%s@tetrationanalytics.com" % cluster_user
            browser['h4_user[password]'] = cluster_password_old
            browser.submit()
            request = urllib2.Request('%s/#/maintenance/version' % endpoint, None, headers)
            result = browser.open(request)
        csrf_token = BeautifulSoup(result.get_data()).findAll(attrs={'name': 'csrf-token'})[0]['content']
        headers['X-CSRF-Token'] = csrf_token
    except Exception as e:
        logging.error(e)
    return ClusterBrowser(browser, headers, endpoint)


def create_api_key_secret(cluster_browser, api_key_secret_path, cluster_api_description):

    browser = cluster_browser.browser
    endpoint = cluster_browser.endpoint
    headers = cluster_browser.headers


    print "endpoint::::::::::::::", endpoint

    payload = {
        'description': cluster_api_description,
        'capability_names': "sensor_management,hw_sensor_management,flow_inventory_query,user_role_scope_management,user_data_upload,app_policy_management,external_integration"
    }

    try:
        url = endpoint + '/api/api_credentials.json'
        request = urllib2.Request(url, None, headers)
        response = browser.open(request)
        api_item_list = json.loads(response.get_data())

        for api_item in api_item_list:
            if api_item['description'] == cluster_api_description:
                url_delete = endpoint + '/api/api_credentials/%s.json' % api_item['id']
                request = urllib2.Request(url_delete, None, headers)
                request.get_method = lambda: 'DELETE'
                browser.open(request)
                break

        request = urllib2.Request(url, json.dumps(payload), headers)
        request.get_method = lambda: 'POST'
        response = browser.open(request)
        api_item = json.loads(response.get_data())
        with open(api_key_secret_path,'w') as api_key_secret_file:
            api_key_secret_file.write('cluster_api_key=%s\n' % api_item['api_key'])
            api_key_secret_file.write('cluster_api_secret=%s\n' % api_item['api_secret'])
            api_key_secret_file.write('cluster_api_id=%s\n' % api_item['id'])

    except ValueError:
        url = endpoint + '/api/version.json'


class ClusterBrowser():
    def __init__(self, browser, headers, endpoint):
        self.browser = browser
        self.headers = headers
        self.endpoint = endpoint


def main():
    args = parser.parse_args()

    scale_dir = args.scale_dir
    api_key_secret_path = args.api_key_secret_path
    sensor_hostname = args.sensor_hostname
    sensor_os_platform = args.sensor_os_platform
    sensor_os_version = args.sensor_os_version
    sensor_version = args.sensor_version
    sensor_type = args.sensor_type
    sensor_filepath = args.sensor_filepath
    cluster_uiip = args.cluster_uiip
    cluster_name = args.cluster_name
    cluster_user = args.cluster_user
    cluster_password = args.cluster_password
    cluster_password_old = args.cluster_password_old
    cluster_api_key = args.cluster_api_key
    cluster_api_secret = args.cluster_api_secret
    cluster_api_description = args.cluster_api_description

    cluster_browser = get_browser(cluster_uiip, cluster_name, scale_dir, cluster_user, cluster_password, cluster_password_old)
    tet_client = get_client(cluster_uiip, cluster_name, cluster_api_key, cluster_api_secret)

    if args.function == "create_api_key_secret":
        create_api_key_secret(cluster_browser, api_key_secret_path, cluster_api_description)
    else:
        if args.debug:
            level = logging.DEBUG
            logging.basicConfig(filename='%s/server/server_utils.log' % scale_dir,
                                format='%(asctime)s:%(levelname)s:%(message)s',
                                level=level)

        if args.function == "clean_rails":
            clean_rails(tet_client, sensor_hostname)

        if "sensor" in args.function:
            sensor_count, sensor_list = sensor_info(tet_client, sensor_hostname)
            if args.function == "sensor_count":
                print sensor_count
            if args.function == "sensor_list":
                print sensor_list

        if args.function == "download_rpm":
            download_rpm(cluster_browser, sensor_os_platform, sensor_os_version, sensor_version, sensor_type, sensor_filepath)

        if args.function == "latest_version":
            print latest_version(cluster_browser)


if __name__ == "__main__":
    main()
