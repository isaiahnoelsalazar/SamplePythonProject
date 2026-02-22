import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor

PORT = 5000
TIMEOUT = 0.5
SIGNATURE = "screen-share-active"

def get_local_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    network = ipaddress.IPv4Network(local_ip + '/24', strict=False)
    return network

def check_device(ip):
    url = f"http://{ip}:{PORT}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if SIGNATURE in response.text:
            return str(ip)
    except:
        pass
    return None

def scan_network():
    network = get_local_subnet()
    print(f"Scanning {network} ...")

    found = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_device, network.hosts())

    for result in results:
        if result:
            found.append(result)

    return found

if __name__ == "__main__":
    devices = scan_network()

    print("\nActive Screen Share Devices:")
    for ip in devices:
        print(f"http://{ip}:5000")