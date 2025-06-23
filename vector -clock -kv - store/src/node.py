from flask import Flask, Response, request, jsonify
import threading
import requests
import os
import time

app = Flask(__name__)

class Node:
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}
        self.vector_clock = {n: 0 for n in nodes}
        self.lock = threading.RLock()
        self.buffer = []
        threading.Thread(target=self.buffer_watcher, daemon=True).start()
        print(f"Node {node_id} initialized with nodes {nodes}")

    def increment_clock(self):
        self.vector_clock[self.node_id] += 1
        return self.vector_clock.copy()

    def can_deliver(self, msg_clock, sender):
        for node in msg_clock:
            if node == sender:
                if msg_clock[node] != self.vector_clock[node] + 1:
                    return False
            else:
                if msg_clock[node] > self.vector_clock[node]:
                    return False
        return True

    def apply_replication(self, data):
        key = data['key']
        value = data['value']
        sender = data['sender']
        timestamp = data['timestamp']

        self.data[key] = value
        for n in self.nodes:
            self.vector_clock[n] = max(self.vector_clock[n], timestamp[n])
#        self.increment_clock()
        print(f"[{self.node_id}] Applied replication: {key}={value}, clock={self.vector_clock}")

    def buffer_watcher(self):
        while True:
            with self.lock:
                to_retry = list(self.buffer)
                self.buffer.clear()
                for msg in to_retry:
                    if self.can_deliver(msg["timestamp"], msg["sender"]):
                        self.apply_replication(msg)
                    else:
                        self.buffer.append(msg)
            time.sleep(1)

    def replicate(self, key, value, timestamp):
        def _replicate():
            for node in self.nodes:
                if node != self.node_id:
                    try:
                        # Artificial delay to force out-of-order delivery
                        if key == "x" and value == 100 and node == "node3":
                            delay = 2
                            print(f"[{self.node_id}] Simulating delayed delivery of x=100 to {node} by {delay}s")
                            time.sleep(delay)

                        url = f"http://{node}:5000/receive"
                        print(f"[{self.node_id}] Replicating to {url} key={key}, value={value}")
                        requests.post(
                            url,
                            json={
                                "key": key,
                                "value": value,
                                "sender": self.node_id,
                                "timestamp": timestamp
                            },
                            timeout=3
                        )
                    except Exception as e:
                        print(f"[{self.node_id}] Replication to {node} failed: {str(e)}")
        threading.Thread(target=_replicate, daemon=True).start()

# Initialize node
node = Node(os.getenv("NODE_ID"), os.getenv("NODES").split(","))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "node": os.getenv("NODE_ID"),
        "timestamp": node.vector_clock
    }), 200

@app.route('/write', methods=['POST'])
def write():
    try:
        print(f"\n[{node.node_id}] Received write request")
        data = request.get_json()
        if not data or 'key' not in data:
            return jsonify({"error": "Bad request"}), 400

        key = data['key']
        value = data['value']

        # Process write and increment clock
        with node.lock:
            # Merge incoming context if available
            if 'context' in data:
                incoming = data['context']
                for n in node.nodes:
                    node.vector_clock[n] = max(node.vector_clock[n], incoming.get(n, 0))
                print(f"[{node.node_id}] Merged context from client: {incoming}")

            node.data[key] = value
            clock = node.increment_clock()
            print(f"[{node.node_id}] Write: {key}={value}, clock={clock}")

        # Replicate if this is a client-initiated write
        if 'sender' not in data:
            node.replicate(key, value, clock)

        return jsonify({
            "status": "success",
            "timestamp": clock
        }), 200

    except Exception as e:
        print(f"[{node.node_id}] Write error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/receive', methods=['POST'])
def receive():
    try:
        data = request.get_json()
        print(f"\n[{node.node_id}] Received replication: {data}")
        with node.lock:
            if node.can_deliver(data["timestamp"], data["sender"]):
                node.apply_replication(data)
            else:
                print(f"[{node.node_id}] Cannot deliver yet, buffering...")
                node.buffer.append(data)

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[{node.node_id}] Replication error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/read', methods=['GET'])
def read():
    key = request.args.get("key")
    return jsonify({
        "value": node.data.get(key),
        "timestamp": node.vector_clock
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    app.run(host='0.0.0.0', port=port, threaded=True)