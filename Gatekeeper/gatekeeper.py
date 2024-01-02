# Import necessary libraries
import os
from flask import Flask, request
import requests
import json

# Create a Flask application
app = Flask(__name__)

# Define the proxy host address
PROXY_HOST = "10.0.1.8"

# Define a route for handling read queries
@app.route('/read-query', methods=['POST'])
def execute_read_query():
    # Extract method_id and query from the request
    method_id = request.args.get('method_id')
    query = request.get_json()['query']

    # Construct the URL for the proxy server handling read queries
    url = f"http://{PROXY_HOST}:5001/read-query?method_id={method_id}"

    # Prepare the payload (query) in JSON format
    payload = json.dumps({"query": query})

    # Send a POST request to the proxy server
    response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)

    # Return the response received from the proxy server
    return response.text

# Define a route for handling write queries
@app.route('/write-query', methods=['POST'])
def execute_write_query():
    # Extract the query from the request
    query = request.get_json()['query']

    # Construct the URL for the proxy server handling write queries
    url = f"http://{PROXY_HOST}:5001/write-query"

    # Prepare the payload (query) in JSON format
    payload = json.dumps({"query": query})

    # Send a POST request to the proxy server
    response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)

    # Return the response received from the proxy server
    return response.text

# Run the Flask application if this script is executed directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
