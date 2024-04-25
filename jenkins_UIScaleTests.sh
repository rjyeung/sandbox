#!/bin/bash -e
# 1. Run Rails server on master
# 2. Spin up workers and run Protractor on each


# Step 1: Start Rails server
echo "====================== STEP 1: Start Rails Server ======================"
# Load RVM if available
if [ -x /usr/local/rvm/scripts/rvm ]; then
  source /usr/local/rvm/scripts/rvm
  test -e $WORKSPACE/ui/.ruby-version && rvm use $(cat $WORKSPACE/ui/.ruby-version)
fi

test -d $WORKSPACE/deploy-ansible || mkdir $WORKSPACE/deploy-ansible

cd $WORKSPACE/deploy-ansible
test -d .git || git clone --depth 1 git@github.com:TetrationAnalytics/deploy-ansible.git .

git fetch -p
git checkout ${deploy_ansible_branch}
git reset --hard origin/${deploy_ansible_branch}

cd $WORKSPACE/ui

export RAILS_ENV=test

rm -rf tmp/*

bash -lc 'make clean'
bash -lc 'make install'

git-lfs pull

# See https://github.com/SeleniumHQ/docker-selenium/issues/87
export DBUS_SESSION_BUS_ADDRESS=/dev/null

RAILS_ENV=test bundle exec rake e2e:scale_server

# Step 2: Run workers in parallel
echo "====================== STEP 2: Run workers in parallel ======================"
USERNAME=tetter
HOSTLIST="10.4.66.61 10.4.66.62"
for HOSTNAME in $HOSTLIST; do
  (
  echo $SUPERPASSWORD > .pass
  echo "Running tests in worker VM ${HOSTNAME}"
  sshpass -f.pass rsync -avz --delete -e ssh  $WORKSPACE/ui ${USERNAME}@${HOSTNAME}:  &> ${HOSTNAME}.log
  sshpass -f.pass ssh -T -l ${USERNAME} ${HOSTNAME} "${SCRIPT}" &>> ${HOSTNAME}.log <<EOF
    echo "Starting test at \$(date) on Server \$(uname -n)" 
    killall chrome
    killall Xvfb
    cd ui/spec/angular
    rm -f tmp/reports/xmloutput*xml
    export http_proxy=http://172.28.126.190:3128
    export https_proxy=http://172.28.126.190:3128

    echo "~~~~~~~~Start npm"
    npm install && npm run update-webdriver

    Xvfb :2 -screen 0 1920x1080x24 &
    export DISPLAY=:2.0

    echo "~~~~~~~~Run tests" 
    npm run scale-admin -- --params.login.user=oshokut+10@tetrationanalytics.com --params.login.password=oshokut123
    #nohup npm run scale-admin -- --params.login.user=oshokut+10004@tetrationanalytics.com --params.login.password=oshokut123 > /dev/null &
    #nohup npm run scale-admin -- --params.login.user=oshokut+10006@tetrationanalytics.com --params.login.password=oshokut123 > /dev/null &
    killall chrome
    killall Xvfb
EOF
) & 
done
wait

# Step 3: print logs
echo "====================== STEP 3: Print Logs in Sequnece ======================"
pwd
for HOSTNAME in $HOSTLIST; do
( 
  rm -f ${HOSTNAME}_report.xml
  #echo $SUPERPASSWORD > .pass
  sshpass -f.pass scp ${USERNAME}@${HOSTNAME}:/home/${USERNAME}/ui/spec/angular/tmp/reports/xmloutput*xml ./${HOSTNAME}_report.xml
  sed "s/^/${HOSTNAME} - /" ${HOSTNAME}.log 
  
)
done

echo All subshells finishe

# Step 3: Cleanup kill Rails server
# once all workers are done, kill rails
# bundle exec rake e2e:kill_rails


