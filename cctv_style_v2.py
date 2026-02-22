from flask import Flask, jsonify, render_template_string
import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

PORT = 5000
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
        if r.status_code == 200:
            data = r.json()
            return {
                "ip": str(ip),
                "name": data.get("name", str(ip))
            }
    except:
        pass
    return None


def discover_devices():
    network = get_local_subnet()
    devices = []

    with ThreadPoolExecutor(max_workers=60) as executor:
        results = executor.map(check_device, network.hosts())

    for result in results:
        if result:
            devices.append(result)

    return devices


@app.route('/devices')
def devices():
    return jsonify(discover_devices())


@app.route('/')
def dashboard():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Home CCTV Wall</title>
<style>
body {
    margin:0;
    background:#0f0f0f;
    font-family:Arial;
}
.grid {
    display:grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap:12px;
    padding:12px;
}
.camera {
    background:#000;
    border:2px solid #222;
    border-radius:10px;
    overflow:hidden;
    position:relative;
    cursor:pointer;
}
.camera:hover {
    border-color:#00ff99;
}
.label {
    position:absolute;
    top:0;
    left:0;
    background:rgba(0,0,0,0.7);
    color:#00ff99;
    padding:5px 10px;
    font-size:13px;
}
img {
    width:100%;
    display:block;
}
.modal {
    display:none;
    position:fixed;
    z-index:100;
    left:0;
    top:0;
    width:100%;
    height:100%;
    background:black;
}
.modal img {
    width:100%;
    height:100%;
    object-fit:contain;
}
</style>
</head>
<body>

<div class="grid" id="grid"></div>

<div class="modal" id="modal" onclick="closeModal()">
    <img id="modalImg">
</div>

<script>
async function loadDevices(){
    const response = await fetch('/devices');
    const devices = await response.json();
    const grid = document.getElementById('grid');
    grid.innerHTML = '';

    devices.forEach(device => {
        const div = document.createElement('div');
        div.className = 'camera';
        div.innerHTML = `
            <div class="label">${device.name} (${device.ip})</div>
            <img src="http://${device.ip}:5000/video">
        `;
        div.onclick = () => openModal(`http://${device.ip}:5000/video`);
        grid.appendChild(div);
    });
}

function openModal(src){
    document.getElementById('modalImg').src = src;
    document.getElementById('modal').style.display = 'block';
}

function closeModal(){
    document.getElementById('modal').style.display = 'none';
}

loadDevices();
setInterval(loadDevices, 15000);
</script>

</body>
</html>
""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)