import requests
import time
import sys
from urllib.parse import urljoin

NODES = {
    "node1": "http://localhost:5001",
    "node2": "http://localhost:5002",
    "node3": "http://localhost:5003"
}

def robust_request(method, url, **kwargs):
    """Retry failed requests automatically"""
    for attempt in range(3):
        try:
            response = requests.request(
                method,
                url,
                timeout=20,
                headers={'Content-Type': 'application/json'},
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt == 2:
                raise
            time.sleep(2)

def wait_for_nodes():
    print("Checking node availability...")
    for name, url in NODES.items():
        try:
            resp = robust_request('GET', f"{url}/health")
            print(f"✓ {name} ready | Clock: {resp.json()['timestamp']}")
        except Exception as e:
            print(f"❌ {name} unavailable: {str(e)}")
            return False
    return True

def test_causal_consistency():
    print("\n=== Testing Causal Consistency ===")
    
    try:
        # Initial write
        print("Writing x=5 to node1...")
        write_resp = robust_request('POST', f"{NODES['node1']}/write", 
                                  json={"key": "x", "value": 5})
        print(f"Write successful. Clock: {write_resp.json()['timestamp']}")
        time.sleep(1)  # Allow replication

        # Read and causally update
        print("Reading from node2...")
        read_resp = robust_request('GET', f"{NODES['node2']}/read?key=x")
        read_data = read_resp.json()
        print(f"Read value: {read_data['value']} | Clock: {read_data['timestamp']}")

        print("Updating to x=10 at node2...")
        update_resp = robust_request('POST', f"{NODES['node2']}/write",
                                    json={
                                        "key": "x",
                                        "value": read_data['value'] + 5,
                                        "context": read_data['timestamp']
                                    })
        print(f"Update successful. Clock: {update_resp.json()['timestamp']}")
        time.sleep(1)

        # Verify
        final_resp = robust_request('GET', f"{NODES['node3']}/read?key=x")
        final = final_resp.json()
        print(f"Final value at node3: {final['value']} | Clock: {final['timestamp']}")
        assert final['value'] == 10, "Causal consistency violation"
        print("✓ Causal consistency verified")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

def test_out_of_order_delivery():
    print("\n=== Testing Out-of-Order Delivery Handling ===")
    try:
        print("Writing x=100 to node1...")
        write_resp = robust_request('POST', f"{NODES['node1']}/write", 
                                  json={"key": "x", "value": 100})
        print(f"Write successful. Clock: {write_resp.json()['timestamp']}")
        time.sleep(0.5)

        print("Reading from node2...")
        read_resp = robust_request('GET', f"{NODES['node2']}/read?key=x")
        read_data = read_resp.json()
        print(f"Read value: {read_data['value']} | Clock: {read_data['timestamp']}")

        print("Updating to x=200 at node2...")
        update_resp = robust_request('POST', f"{NODES['node2']}/write",
                                    json={
                                        "key": "x",
                                        "value": 200,
                                        "context": read_data['timestamp']
                                    })
        print(f"Update successful. Clock: {update_resp.json()['timestamp']}")
        time.sleep(3)

        final_resp = robust_request('GET', f"{NODES['node3']}/read?key=x")
        final = final_resp.json()
        print(f"Final value at node3: {final['value']} | Clock: {final['timestamp']}")
        assert final['value'] == 200, "Out-of-order causal delivery failed"
        print("✓ Out-of-order delivery handled correctly")

    except Exception as e:
        print(f"❌ Out-of-order test failed: {str(e)}")
        raise

if __name__ == "__main__":
    if not wait_for_nodes():
        sys.exit(1)

    try:
        test_causal_consistency()
        test_out_of_order_delivery()
        print("\n🚀 All tests passed!")
    except Exception as e:
        print(f"\n❌ Testing aborted: {str(e)}")
        sys.exit(1)
