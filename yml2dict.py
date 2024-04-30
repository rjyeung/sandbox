import yaml
# checkout and download yaml for python 

# you should probably put this config in a seperate file
# but for this example it is just a multi-line string
yamlConfigFile = """
cars:
    car0:
        type: toyota
        hp: 129
        mpg:
            city: 30
            highway: 35
        cost: 15,000
    car1:
        type: gm
        hp: 225
        mpg:
            city: 20
            highway: 25
        cost: 20,000
    car2:
        type: chevy
        hp: 220
        mpg:
            city: 22
            highway: 24
        cost: 21,000
"""

yamlInputFile = """
#-------------------------------------------------------------------------
# TETRATION MANIFEST
#-------------------------------------------------------------------------
# build attribute indicates how the binaries are included in the mother-RPM
# auto:   Builds that are invoked through make all and make release
# manual: Build that are managed manually like UI or sensors
# static: Some open-source components

# NOTE(jvimal): Enclose your component's version within double-quotes so it's
# parsed as a string instead of floating point.

version: 2.2.1.8.devel
qcow_rpm_version: 0.0.1
adhoc_rpm_version:
  version: 2.2.1.8.devel
  build: auto
base_rpm_version:
  version: 2.2.1.8.devel
  build: auto
firmware_rpm_version:
  version: 2.0.10e
  build: static
collector:
  version: 2.2.1.8.devel
  build: auto
pipeline:
  version: 2.2.1.8.devel
  build: auto
policy_engine:
  version: 2.2.1.8.devel
  build: auto
adm:
  version: 2.2.1.8.devel
  build: auto
ui_app:
  version: 2.2.1.8.devel
  build: auto
ui_base_vm:
  version: 2.2.1.8.devel
  build: auto
ui-setup:
  version: 2.2.1.8.devel
  build: auto
deploy_ansible:
  version: 2.2.1.8.devel
  build: auto
tetration:
  version: 2.2.1.8.devel
  build: auto
hadoop_tsdb:
  version: 2.2.1.8.devel
  build: auto
orchestrator:
  version: 2.2.1.8.devel
  build: auto
applib:
  version: 2.2.1.8.devel
  build: auto
appset:
  version: 2.2.1.8.devel
  build: auto
publisher:
  version: 2.2.1.8.devel
  build: auto
scheduler:
  version: 2.2.1.8.devel
  build: auto
ams_ext_server:
  version: 2.2.1.8.devel
  build: auto
acs:
  version: 2.2.1.8.devel
  build: auto
adhoc_proxy:
  version: 2.2.1.8.devel
  build: auto
amsclient:
  version: 2.2.1.8.devel
  build: auto
openapiclient:
  version: 2.2.1.8.devel
  build: auto
appsecuritylib:
  version: 2.2.1.8.devel
  build: auto
kim:
  version: 2.2.1.8.devel
  build: auto
kafka_writer:
  version: 2.2.1.8.devel
  build: auto
software_sensor:
  version: 2.2.1.8.devel-1
  win_version: 2.2.1.8.devel.win64
  build: auto
lightsensor:
  version: 2.2.1.8.devel
  build: auto
aix_lw_sensor:
  version: 2.1.1.3
  build: static
netflowsensor:
  version: 2.2.1.8.devel
  build: auto
switch_agent:
  version: 2.2.1.8.devel
  build: auto
bosun:
  version: 0.2.8
  build: static
bosunconf:
  version: 2.2.1.8.devel
  build: auto
opentsdb:
  version: 2.3.0
  build: static
gnuplot:
  version: 4.2.6-2
  build: static
gd:
  version: 2.0.35-11
  build: static
druid:
  version: 0.9.2.1-tet-8
  build: static
druid_tsdb:
  version: 2.2.1.8.devel
  build: auto
spark:
  version: 1.6.2-tet-1
  build: static
hdfs:
  version: 2.4.0.2.1.2.1-474
  build: static
hbase:
  version: 0.99.1234-1
  build: static
ambariclient:
  version: 0.5.7-tet1
  build: static
wss:
  version: 2.2.1.8.devel
  build: auto
snapshot:
  version: 2.2.1.8.devel
  build: auto
cimc_upload_server:
  version: 2.2.1.8.devel
  build: auto
fwmgr:
  version: 2.2.1.8.devel
  build: auto
switch_wss:
  version: 2.2.1.8.devel
  build: auto
collectd_opentsdb:
  version: "1.2"
  build: static
user_guide:
  version: 2.2.1.8.devel
  build: auto
ittest:
  version: 2.2.1.8.devel
  build: auto
upgrade_restapi:
  version: 2.2.1.8.devel
  build: auto
add_server_restapi:
  version: 2.2.1.8.devel
  build: auto
dataexpress:
  version: 1.0-SNAPSHOT
  build: manual
python_venv:
  version: 2.7.9
  build: static
venv:
  version: 2.2.1.8.devel
  build: auto
spark-indexer:
  version: 2.2.1.8.devel
  build: auto
tsdb_dump:
  version: 2.2.1.8.devel
  build: auto
grafana:
  version: 4.4.3
  build: static
collectd:
  version: 5.5.0
  rpm_build_version: 3
  deb_build_version: 2
  # Use the command sha256sum to get the checksum of a file.
  rpm_sha256: 65db08539cc63c088d693aecc6aac62c8187453788863db7af01080e0233517e
  deb_sha256: 073c57262dd5db10ced38b37337bb7b2147bdee55a3ab46154e691bd06de7e44
  build: static
sysstat:
  version: 7.0.2-13
  build: static
megacli:
  version: 8.07.14-1
  build: static
monit:
  version: "5.14"
  build: static
hpolicy:
  version: 2.2.1.8.devel
  build: auto
fmea:
  version: 2.2.1.8.devel
  build: auto
tetops:
  version: 2.2.1.8.devel
  build: auto
aptly:
  version: 0.9.7
  build: static
oracle:
  version: 2.2.1.8.devel
  build: auto
api_server:
  version: 2.2.1.8.devel
  build: auto
intent_service:
  version: 2.2.1.8.devel
  build: auto
haproxy:
  version: 1.5.4-2
  build: static
keepalived:
  version: 1.2.23-5
  build: static
consul:
  version: "0.7.5"
  consul_template_version: "0.16.0"
  python_consul_version: "0.6.3"
  build: static
enforcement_coordinator:
  version: 2.2.1.8.devel
  build: auto
efe:
  version: 2.2.1.8.devel
  build: auto
IntentEnforcementEngine:
  version: 2.2.1.8.devel
  build: auto
ingestion:
  version: 2.2.1.8.devel
  build: auto
vault:
  version: "0.6.5"
  build: static
qcow:
  version: 2.2.1.8.devel
  build: static
diagnostics:
  version: 2.2.1.8.devel
  build: auto
ps_pipeline:
  version: 2.2.1.8.devel
  build: auto
ps_rest_server:
  version: 2.2.1.8.devel
  build: auto
kafka:
  version: "2.11-0.10.2.0"
  build: static
flink:
  version: "2.11-1.2.0"
  build: static
tim:
  version: 2.2.1.8.devel
  build: auto
apm_pipeline:
  version: 2.2.1.8.devel
  build: auto
apm_agent:
  version: 2.2.1.8.devel
  build: auto
apm_gatekeeper:
  version: 2.2.1.8.devel
  build: auto
gordon:
  version: 2.2.1.8.devel
  build: auto
vmock:
  version: 2.2.1.8.devel
  build: auto
"""

# the yaml file will be converted to a dict
# for sub sections the dict will nest dicts
theDict = yaml.load(yamlInputFile)
print (theDict)

print ("\n\n\n")
print (theDict['collectd'])

# to list the car types (like car1, car2, etc
print ("\n\n\n")
print (theDict['collectd'].keys())
# output:
# ['car2', 'car0', 'car1']

# to display the type and cost of the vehicles
print ("\n\n\n")
for c in theDict['collectd'].keys():
    print (c, "=", theDict['collectd'][c])
    #print theDict['collectd'][c]['type'], "cost:", theDict['cars'][c]['cost']

