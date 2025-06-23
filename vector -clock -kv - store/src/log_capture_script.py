import subprocess
import time

def collect_logs(service_name):
    print(f"📦 Capturing logs from {service_name}...")
    with open(f"{service_name}_log.txt", "w") as f:
        subprocess.run(["docker-compose", "logs", service_name], stdout=f)
    print(f"✅ {service_name} logs saved to {service_name}_log.txt")

def main():
    print("⏳ Waiting 2 seconds before collecting logs...")
    time.sleep(2)
    for service in ["node1", "node2", "node3"]:
        collect_logs(service)
    print("\n✅ All node logs collected successfully.")

if __name__ == "__main__":
    main()
