from flask import Flask, render_template_string
import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

PORT = 5000
SIGNATURE = "screen-share-active"
TIMEOUT = 0.4


def get_local_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    return ipaddress.IPv4Network(local_ip + '/24', strict=False)


def check_device(ip):
    try:
        r = requests.get(f"http://{ip}:{PORT}/health", timeout=TIMEOUT)
        if SIGNATURE in r.text:
            return str(ip)
    except:
        pass
    return None


def discover_devices():
    network = get_local_subnet()
    devices = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_device, network.hosts())

    for result in results:
        if result:
            devices.append(result)

    return devices


@app.route('/')
def dashboard():
    devices = discover_devices()

    html = """
    <html>
    <head>
        <title>Home CCTV Wall</title>
        <style>
            body {
                background: #111;
                margin: 0;
                font-family: Arial;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                gap: 10px;
                padding: 10px;
            }
            .camera {
                background: black;
                border: 2px solid #333;
                border-radius: 8px;
                overflow: hidden;
            }
            img {
                width: 100%;
                height: auto;
            }
            .label {
                color: white;
                padding: 5px;
                font-size: 14px;
                background: #222;
            }
        </style>
    </head>
    <body>
        <div class="grid">
            {% for ip in devices %}
            <div class="camera">
                <div class="label">Device {{ ip }}</div>
                <img src="http://{{ ip }}:5000/video">
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """

    return render_template_string(html, devices=devices)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)