#!/bin/bash

# Install sysbench

sudo apt update
sudo apt install -y sysbench

# Start Analysis
sudo wget https://downloads.mysql.com/docs/sakila-db.tar.gz -O /home/ubuntu/sakila-db.tar.gz
sudo tar -xvf /home/ubuntu/sakila-db.tar.gz -C /home/ubuntu/

# Upload Sakila database to MySQL
sudo mysql -u root -proot -e "SOURCE /home/ubuntu/sakila-db/sakila-schema.sql;"
sudo mysql -u root -proot -e "SOURCE /home/ubuntu/sakila-db/sakila-data.sql;"

# Benchmark using Sysbench
sudo sysbench oltp_read_write --tables=8 --threads=6 --time=360 --max-requests=0 --mysql-db=sakila --mysql-user=root --mysql-password=root prepare
sudo sysbench oltp_read_write --tables=8 --threads=6 --time=360 --max-requests=0 --mysql-db=sakila --mysql-user=root --mysql-password=root --mysql_storage_engine=NDBCLUSTER run > results.txt
sudo sysbench oltp_read_write --mysql-db=sakila --mysql-user=root --mysql-password=root cleanup