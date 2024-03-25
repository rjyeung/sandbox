#!/bin/bash
SSH_OPTS_P22="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR"
SSH_OPTS_MIXED="${SSH_OPTS_P22}"
NOW=$(date +"%Y-%m-%d_%T")
DIR="log_$1_$NOW"

if [ $# -eq 1 ]; then
    if [[ $1 =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then 
      echo "Detected IP address..."
      ORCH_IP=$1
    elif [[ $1 =~ "tetrationanalytics.com" ]]; then
      CLUSTER=$1
      ORCH_IP='orch-'$CLUSTER
    else
      echo "Appending tetrationanalytics.com to endpoint name..."
      CLUSTER=$1'.tetrationanalytics.com'
      ORCH_IP='orch-'$CLUSTER
    fi
else
    echo "ERROR: Try sh get_cluster_log.sh \$ClusterName\n\t\
Example: sh get_cluster_log.sh grigori\n"
    exit 
fi

echo "ORCH_IP = $ORCH_IP"
mkdir -p $DIR
echo "Log are collected in $DIR directory"

## Going through appServer-1 and gather all files in /local/logs directory
#fileArray=($(ssh $SSH_OPTS_MIXED $TET_USER@$ORCH_IP sudo -u $TET_SUPERUSER ssh $SSH_OPTS_P22 appServer-1 sudo find /local/logs/ -type f))
#echo "${fileArray[@]}"  # Note double-quotes to avoid extra parsing of funny characters in filenames
#for file in "${fileArray[@]}"
#do
#  echo $file
#  appSvr='appServer-1'
#  mkdir -p $DIR/$appSvr/`dirname $file` 
#  ssh $SSH_OPTS_MIXED $TET_USER@$ORCH_IP sudo -u $TET_SUPERUSER ssh $SSH_OPTS_P22 $appSvr \
#    sudo cat $file > $DIR/$appSvr/$file &
#done
#wait
#exit

#appServer logs
appSvrCnt=2
for i in $(eval echo "{1..$appSvrCnt}")
do
  appSvr='appServer-'$i
  ssh $SSH_OPTS_MIXED $TET_USER@$ORCH_IP sudo -u $TET_SUPERUSER ssh $SSH_OPTS_P22 $appSvr \
    sudo cat /local/logs/haproxy/haproxy.log > $DIR/$appSvr.haproxy.txt
  ssh $SSH_OPTS_MIXED $TET_USER@$ORCH_IP sudo -u $TET_SUPERUSER ssh $SSH_OPTS_P22 $appSvr \
    sudo cat /var/log/ui/web-1.log > $DIR/$appSvr.web-1.txt
done

#adhoc server logs
adhocSvrCnt=2
for i in $(eval echo "{1..$adhocSvrCnt}")
do
  adhocSvr='adhoc-'$i
  ssh $SSH_OPTS_MIXED $TET_USER@$ORCH_IP sudo -u $TET_SUPERUSER ssh $SSH_OPTS_P22 $adhocSvr \
    sudo cat /var/log/jupyterhub/jupyterhub.log > $DIR/$adhocSvr.jupyterhub.log
  ssh $SSH_OPTS_MIXED $TET_USER@$ORCH_IP sudo -u $TET_SUPERUSER ssh $SSH_OPTS_P22 $adhocSvr \
    sudo cat /local/logs/tetration/acs/current > $DIR/$adhocSvr.current
done


#for file in $(find /etc -type f) ; do
#    echo "Display content of files in /etc/ directory"
#    echo "############START OF FILE#########"
#    echo ${file}
#    echo " "
#    cat ${file}
#    echo "##########END OF FILE########"
#    echo " "
#done
