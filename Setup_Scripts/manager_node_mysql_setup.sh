#!/bin/bash

set -e
# Install dependencies
sudo apt update
sudo apt install libaio1 libmecab2 libncurses5 -y


sudo wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster-community-management-server_8.0.31-1ubuntu22.04_amd64.deb
sudo dpkg -i mysql-cluster-community-management-server_8.0.31-1ubuntu22.04_amd64.deb


sudo mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir conf
sudo mkdir mysqld_data
sudo mkdir ndb_data
cd conf

sudo touch my.cnf
sudo chmod a+w my.cnf

echo "[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306" > my.cnf

sudo touch config.ini
sudo chmod a+w config.ini

echo "
[ndbd default]
noofreplicas=3
datadir=/opt/mysqlcluster/deploy/ndb_data


[ndb_mgmd]
hostname=10.0.1.4
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1


[ndbd]
hostname=10.0.1.5 # Hostname/IP of the first data node
NodeId=2			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=10.0.1.6 # Hostname/IP of the second data node
NodeId=3			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=10.0.1.7 # Hostname/IP of the second data node
NodeId=4			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[mysqld]
# SQL node options:
hostname=10.0.1.4 # In our case the MySQL server/client is on the same Droplet as the cluster manager
NodeId=50
" > config.ini


sudo touch /etc/systemd/system/ndb_mgmd.service
sudo chmod a+w /etc/systemd/system/ndb_mgmd.service

sudo echo "
[Unit]
Description=MySQL NDB Cluster Management Server
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini --initial
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/ndb_mgmd.service

sudo systemctl daemon-reload
sudo systemctl enable ndb_mgmd
sudo systemctl start ndb_mgmd

# Download MySQL Server
sudo wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.6/mysql-cluster_7.6.6-1ubuntu18.04_amd64.deb-bundle.tar
sudo mkdir install
tar -xvf mysql-cluster_7.6.6-1ubuntu18.04_amd64.deb-bundle.tar -C install/
cd install

# Install MySQL Server
sudo dpkg -i mysql-common_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-cluster-community-client_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-client_7.6.6-1ubuntu18.04_amd64.deb

# Configure installation to avoid using MySQL prompt
sudo debconf-set-selections <<< 'mysql-cluster-community-server_7.6.6 mysql-cluster-community-server/root-pass password root'
sudo debconf-set-selections <<< 'mysql-cluster-community-server_7.6.6 mysql-cluster-community-server/re-root-pass password root'

# Install the rest of the packages
sudo dpkg -i mysql-cluster-community-server_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-server_7.6.6-1ubuntu18.04_amd64.deb


# Configure client to connect to the master node

sudo touch /etc/mysql/my.cnf
sudo chmod a+w /etc/mysql/my.cnf

sudo echo "
[mysqld]
ndbcluster                   

[mysql_cluster]
ndb-connectstring=10.0.1.4:1186
" > /etc/mysql/my.cnf

sudo chmod 600 /etc/mysql/my.cnf


# Restart MySQL Server
sudo systemctl restart mysql
sudo systemctl enable mysql

