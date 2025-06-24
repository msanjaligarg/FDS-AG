import requests
import random
import time
import threading
import os

CHARGE_SERVICE_URL = os.getenv("CHARGE_SERVICE_URL", "http://localhost:5000")
#CHARGE_SERVICE_URL = "http://charge_request_service:5000"
VEHICLES = [f"EV-{i:04d}" for i in range(1, 1001)]

def simulate_vehicle(vehicle_id):
    while True:
        try:
            kwh = random.randint(5, 30)
            response = requests.post(
                f"{CHARGE_SERVICE_URL}/request-charge",
                json={"vehicle_id": vehicle_id, "kwh": kwh}
            )
            print(f"Vehicle {vehicle_id} charged {kwh}kWh: {response.status_code}")
            print(f"Vehicle {vehicle_id} error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Error for {vehicle_id}: {str(e)}")
        
        time.sleep(random.randint(5, 30))

if __name__ == '__main__':
    print("Starting load test...")
    
    # Start 10 vehicles making requests
    for i in range(10):
        threading.Thread(
            target=simulate_vehicle,
            args=(random.choice(VEHICLES),),
            daemon=True
        ).start()
    
    # Keep main thread alive
    while True:
        time.sleep(1)