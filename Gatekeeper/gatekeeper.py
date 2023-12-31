import os
from flask import Flask, request
import requests
import json

app = Flask(__name__)

PROXY_HOST = "10.0.1.8"

@app.route('/read-query', methods=['POST'])
def execute_read_query():
    method_id = request.args.get('method_id')
    query = request.get_json()['query']

    url = f"http://{PROXY_HOST}:5000/read-query?method_id={method_id}"

    payload = json.dumps({"query": query})

    response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)

    return response.text

@app.route('/write-query', methods=['POST'])
def execute_write_query():
    query = request.get_json()['query']

    url = f"http://{PROXY_HOST}:5000/write-query"

    payload = json.dumps({"query": query})

    response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)

    return response.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)