import os
import subprocess
import random
import mysql.connector
from flask import Flask, request

app = Flask(__name__)

NODES = {"master": "10.0.1.4","data_node_1":"10.0.1.5","data_node_2":"10.0.1.6","data_node_3":"10.0.1.7"}

DIRECT_HIT = 0
RANDOM_HIT = 1
QUICKEST_HIT = 2


def execute_database_query(host, query):
    try:
        with mysql.connector.connect(user='root',password='root', host=host, database="sakila") as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        return f"Failed executing query: {err}"


def perform_direct_hit(query):
    return execute_database_query(NODES["master"], query)


def perform_random_hit(query):
    selected_node_name = random.choice([node for node in NODES.keys() if node != "master"])

    ping_command = f"ping -c 1 -W 1 {NODES[selected_node_name]}".split(' ')
    try:
        output = subprocess.check_output(ping_command).decode().strip()
        timing = output.split("\n")[-1].split()[3].split('/')
        ping_time = float(timing[1])  # average
        print(f"Ping time: {ping_time}")
    except Exception as e:
        print(e)
        ping_time = None

    return execute_database_query(NODES[selected_node_name], selected_node_name, query)


def perform_quickest_hit(query):
    best_node_name = NODES["master"]
    best_ping_time = float('inf')

    for node_name in [node for node in NODES.keys() if node != "master"]:
        node = NODES[node_name]

        ping_command = f"ping -c 1 -W 1 {node}".split(' ')
        try:
            output = subprocess.check_output(ping_command).decode().strip()
            timing = output.split("\n")[-1].split()[3].split('/')
            ping_time = float(timing[1])  # average
            print(f"Ping time for {node_name}: {ping_time}")
        except Exception as e:
            print(e)
            ping_time = None

        if ping_time is not None and ping_time < best_ping_time:
            best_node_name = node_name
            best_ping_time = ping_time

    response = execute_database_query(NODES[best_node_name], best_node_name, query)
    response['ping_time'] = best_ping_time
    return response


@app.route('/read-query', methods=['POST'])
def handle_read_query():
    method_type = int(request.args.get('method_type', DIRECT_HIT))
    query = request.get_json()['query']

    if method_type == DIRECT_HIT:
        return perform_direct_hit(query)
    elif method_type == RANDOM_HIT:
        return perform_random_hit(query)
    elif method_type == QUICKEST_HIT:
        return perform_quickest_hit(query)
    else:
        return perform_direct_hit(query)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
