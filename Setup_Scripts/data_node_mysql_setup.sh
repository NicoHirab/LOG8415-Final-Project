#!/bin/bash

# Install dependencies
sudo apt-get update
sudo apt-get install libncurses5 libclass-methodmaker-perl -y 

sudo wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.6/mysql-cluster-community-data-node_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-cluster-community-data-node_7.6.6-1ubuntu18.04_amd64.deb

sudo touch /etc/my.cnf
sudo chmod a+w /etc/my.cnf

echo "
[mysql_cluster]
ndb-connectstring=10.0.1.4:1186
" > /etc/my.cnf

sudo mkdir -p /usr/local/mysql/data

sudo touch /etc/systemd/system/ndbd.service
sudo chmod a+w /etc/systemd/system/ndbd.service

# Add the instructions for systemd to start, stop and restart ndb_mgmd
echo "
[Unit]
Description=MySQL NDB Data Node Daemon
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndbd
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/ndbd.service

sudo chmod 600 /etc/my.cnf

# Reload systemd manager, enable ndb_mgmd and start ndb_mgmd
sudo systemctl daemon-reload
sudo systemctl enable ndbd
sudo systemctl start ndbd


