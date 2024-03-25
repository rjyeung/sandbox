#!/bin/bash
SSH_OPTS_P22="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR"
SSH_OPTS_MIXED="${SSH_OPTS_P22}"
timestamp=$(date +"%Y%m%d_%H%M%S")
prefix="log_$1_$timestamp"
# Array pretending to be a Pythonic dictionary in the format of $server:$filepath
server_filepath_array=( 
  "appServer-1:/local/logs/haproxy/haproxy.log" 
  "appServer-1:/local/logs/nginx/access.log" 
  "appServer-1:/local/logs/nginx/error.log" 
  "appServer-1:/var/log/ui/web-1.log"
  "appServer-2:/local/logs/haproxy/haproxy.log"
  "appServer-2:/local/logs/nginx/access.log" 
  "appServer-2:/local/logs/nginx/error.log" 
  "appServer-2:/var/log/ui/web-1.log"
  "adhoc-1:/var/log/jupyterhub/jupyterhub.log"
  "adhoc-1:/local/logs/tetration/acs/current"
  "adhoc-2:/var/log/jupyterhub/jupyterhub.log"
  "adhoc-2:/local/logs/tetration/acs/current"
  "happobat-1:/local/logs/tetration/adhocsched/current"
  "happobat-1:/local/logs/tetration/adhoc_ams_ext/current"
  "happobat-2:/local/logs/tetration/adhocsched/current"
  "happobat-2:/local/logs/tetration/adhoc_ams_ext/current"
)

server_array=($(printf "%s\n" "${server_filepath_array[@]}" | cut -d: -f1 | sort -u))
#echo "${server_array[@]}"

if [ $# -eq 1 ]; then
  if [[ $1 =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then 
    #echo "Detected IP address..."
    orch_ip=$1
  elif [[ $1 =~ "tetrationanalytics.com" ]]; then
    orch_ip='orch-'$1
  else
    #echo "Appending tetrationanalytics.com to endpoint name..."
    orch_ip='orch-'$1'.tetrationanalytics.com'
  fi
else
  echo "ERROR: Try sh get_cluster_log.sh \$ClusterName\n\t\
        Example: sh get_cluster_log.sh grigori\n"
  exit 
fi
echo "orch_ip = $orch_ip"

###### Copying server log file locally into home directory with proper permission ######
echo "Collect logs locally in directory /home/$tet_superuser/$prefix"
printf "  Server      : Filepath \n" 
printf "  ----------- : ------------------------------- \n" 
for entry in "${server_filepath_array[@]}" ; do
  server="${entry%%:*}"
  filepath="${entry##*:}"
  printf "  %s : %s \n" "$server" "$filepath" 
  ssh $SSH_OPTS_MIXED $tet_user@$orch_ip sudo -u $tet_superuser ssh $SSH_OPTS_P22 $server \
    sudo install -m 777 -D $filepath /home/$tet_superuser/$prefix/$filepath
done

###### Scp local server log directories to orchestrator  ######
echo "SCP directories from local servers to orchestrator direcotry: /home/$tet_superuser/$prefix "
ssh $SSH_OPTS_MIXED $tet_user@$orch_ip sudo -u $tet_superuser mkdir -p /home/$tet_superuser/$prefix
for svr in "${server_array[@]}" ; do
  ssh $SSH_OPTS_MIXED $tet_user@$orch_ip sudo -u $tet_superuser scp $SSH_OPTS_MIXED -r -p -q $tet_superuser@$svr:/home/$tet_superuser/$prefix /home/$tet_superuser/$prefix/$svr
done

###### Zipping orchestrator logs and scp over ######
echo "Zip orchestrator log directory to /tmp/${prefix}.tar.gz"
ssh $SSH_OPTS_MIXED $tet_user@$orch_ip sudo -u $tet_superuser tar -czf /tmp/${prefix}.tar.gz -C /home/$tet_superuser/ ./$prefix 
echo "Scp /tmp/${prefix}.tar.gz file over "
scp $SSH_OPTS_MIXED $tet_user@$orch_ip:/tmp/${prefix}.tar.gz .
echo "Done."
