#!/bin/bash
# To run it, do bash script
for host in 10.4.82.{4..100}; do  # for loop and the {} operator
  echo ">>>>>>>>>>> Updating ${host}" \

  # Setting up paswword-less login to slaves
  sshpass -p $TET_SUPERPASSWORD ssh -o StrictHostKeyChecking=no tetter@${host} 'mkdir -p .ssh'
  cat ~/.ssh/id_rsa.pub | sshpass -p $TET_SUPERPASSWORD ssh -o StrictHostKeyChecking=no tetter@${host} 'cat >> .ssh/authorized_keys'

  # Set up/Tear down paswword-less sudo previlege for tetter in slaves
  # Set up
  sshpass -p $TET_SUPERPASSWORD ssh -o StrictHostKeyChecking=no root@${host} 'chmod 640 /etc/sudoers && echo tetter ALL=\(ALL\) NOPASSWD: ALL >> /etc/sudoers && chmod 440 /etc/sudoers'
  # Tear down
  #sshpass -p $TET_SUPERPASSWORD ssh -o StrictHostKeyChecking=no root@${host} 'chmod 640 /etc/sudoers && sed -i "/tetter ALL=(ALL) NOPASSWD: ALL/d" /etc/sudoers && chmod 440 /etc/sudoers && cat /etc/sudoers'

  # Perform apt-get 
  ssh -o StrictHostKeyChecking=no tetter@${host} 'sudo apt-get update'
  ssh -o StrictHostKeyChecking=no tetter@${host} 'sudo apt-get install corkscrew -y'
  ssh -o StrictHostKeyChecking=no tetter@${host} 'sudo apt-get install xvfb -y'

done
