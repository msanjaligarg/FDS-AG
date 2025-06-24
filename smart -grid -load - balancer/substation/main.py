from flask import Flask, request, jsonify
from prometheus_client import start_http_server, Gauge, Counter
import random
import time
import threading
import os


app = Flask(__name__)

# Metrics
current_load = Gauge('current_load', 'Current number of active charges')
total_requests = Counter('total_requests', 'Total charging requests received')
charging_time = Gauge('charging_time_seconds', 'Time taken for charging')

active_charges = 0
MAX_CAPACITY = 10  # Max concurrent charges

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service_id": os.getenv('SERVICE_ID', 'unknown')  # Safe get with default
    }), 200

@app.route('/charge', methods=['POST'])
def handle_charge():
    global active_charges
    
    if active_charges >= MAX_CAPACITY:
        return jsonify({'error': 'Substation at capacity'}), 503
        
    active_charges += 1
    current_load.inc()
    total_requests.inc()
    
    # Simulate charging
    kwh = request.json.get('kwh', 10)
    charge_time = min(30, kwh * 2)  # 2 seconds per kWh, max 30s
    
    time.sleep(charge_time)
    charging_time.set(charge_time)
    
    active_charges -= 1
    current_load.dec()
    
    return jsonify({'status': 'charged', 'kwh': kwh})

@app.route('/metrics')
def metrics():
    return jsonify({
        'load': active_charges / MAX_CAPACITY * 100,
        'capacity': MAX_CAPACITY,
        'active': active_charges
    })

if __name__ == '__main__':
    # Start metrics server
    start_http_server(8000)
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000)