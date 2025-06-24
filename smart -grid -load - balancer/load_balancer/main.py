from flask import Flask, request, jsonify
import requests
import threading
import time
from prometheus_client import start_http_server, Gauge
import os


app = Flask(__name__)
# Initialize substations list (add before route_request())
substations = os.getenv('SUBSTATIONS', '').split(',')
print(f"Loaded substations: {substations}")  # Debug log

#substations = []  # Will be populated from environment variables

# Metrics
substation_loads = Gauge('substation_load_percentage', 'Current load percentage', ['substation_id'])

def poll_substations():
    while True:
        for substation in substations:
            try:
                response = requests.get(f'http://{substation}/metrics')
                # Parse load from Prometheus metrics
                # (In real implementation, parse the actual metrics endpoint)
                substation_loads.labels(substation_id=substation).set(response.json().get('load', 0))
            except:
                substation_loads.labels(substation_id=substation).set(-1)
        time.sleep(5)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/route', methods=['POST'])
def route_request():
    if not substations:
        return jsonify({'error': 'No substations available'}), 503
        
    # Find substation with lowest load
    best_substation = min(substations, key=lambda x: get_load(x))
    print(f"Routing to {best_substation}")
    
    try:
        response = requests.post(f'http://{best_substation}/charge', json=request.json)
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({'error': 'Substation unavailable'}), 503
    

def get_load(substation_url):
    try:
        response = requests.get(f'http://{substation_url}/metrics', timeout=1)
        metrics = response.json()
        return metrics.get("load", 100)  # Use 100% as fallback if not found
    except Exception:
        return 100  # Consider maxed out if not reachable

if __name__ == '__main__':
    # Start background thread for polling
    threading.Thread(target=poll_substations, daemon=True).start()
    
    # Start metrics server
    start_http_server(8000)
    
    # Start Flask app
   # app.run(host='0.0.0.0', port=5000)
    app.run(host='0.0.0.0', port=5000, threaded=True)
