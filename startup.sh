#!/bin/bash

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install python3-pip git -y

											   
project=$(sudo gcloud config list project 2>/dev/null | grep project | awk '{print $3}')    
secret=$(sudo gcloud secrets list --project=$project | awk 'NR==2 {print $1}')

echo $project>gcm-test/project

sudo gcloud secrets access versions latest --secret=$secret --project=$project > $secret
echo "\n" >> $secret
chmod 400 $secret
ssh-add $secret

git clone git@github.com:wheecious/gcm-test.git
cd gcm-test/hamster
#git switch terraform_no_kube

pip3 install -r requirements.txt

chmod +x hamster.py
python3 hamster.py &
