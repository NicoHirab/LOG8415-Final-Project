#!/bin/bash

sudo apt-get update
sudo apt install -y python3-pip

git clone https://github.com/NicoHirab/LOG8415-Final-Project.git
cd LOG8415-Final-Project/Gatekeeper

pip install -r requirements.txt

python3 gatekeeper.py