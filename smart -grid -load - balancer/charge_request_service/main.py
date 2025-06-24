from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
LOAD_BALANCER_URL = os.getenv('LOAD_BALANCER_URL', 'http://load_balancer:5000')

@app.route('/request-charge', methods=['POST'])
def handle_charge_request():
    try:
        data = request.json
        # Basic validation
        if not data or 'vehicle_id' not in data or 'kwh' not in data:
            return jsonify({'error': 'Invalid request'}), 400
            
        # Forward to load balancer
        response = requests.post(f'{LOAD_BALANCER_URL}/route', json=data)
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)