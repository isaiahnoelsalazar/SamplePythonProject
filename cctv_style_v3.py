from flask import Flask, jsonify, render_template_string
import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

PORT = 5000
TIMEOUT = 0.4

# Optional shared secret (must match device if enabled)
SECRET = "myhousekey123"


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
<title>Home Command Center</title>

<style>
body{
    margin:0;
    background:#0f0f0f;
    font-family:Arial;
    color:white;
}

.topbar{
    position:fixed;
    top:0;
    width:100%;
    height:50px;
    background:#111;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 15px;
    z-index:10;
    border-bottom:1px solid #222;
}

.mode-btn{
    padding:6px 14px;
    border-radius:6px;
    border:1px solid #00ff99;
    background:#222;
    color:#00ff99;
    cursor:pointer;
}

.mode-btn.control{
    border-color:#ff4444;
    color:#ff4444;
    background:#330000;
}

.grid{
    margin-top:60px;
    padding:12px;
    display:grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap:12px;
}

.camera{
    background:#000;
    border:2px solid #222;
    border-radius:10px;
    overflow:hidden;
    position:relative;
    cursor:pointer;
    transition:0.2s;
}

.camera:hover{
    border-color:#00ff99;
}

.camera.control-mode:hover{
    border-color:#ff4444;
}

.label{
    position:absolute;
    top:0;
    left:0;
    background:rgba(0,0,0,0.7);
    padding:5px 10px;
    font-size:13px;
}

img{
    width:100%;
    display:block;
}

.modal{
    display:none;
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background:black;
    z-index:100;
}

.modal iframe{
    width:100%;
    height:100%;
    border:none;
}

.close-btn{
    position:absolute;
    top:10px;
    right:20px;
    font-size:26px;
    color:white;
    cursor:pointer;
    z-index:101;
}
</style>
</head>

<body>

<div class="topbar">
    <div>🖥 HOME COMMAND CENTER</div>
    <button id="modeBtn" class="mode-btn" onclick="toggleMode()">VIEW MODE</button>
</div>

<div class="grid" id="grid"></div>

<div class="modal" id="modal">
    <div class="close-btn" onclick="closeModal()">✕</div>
    <iframe id="modalFrame"></iframe>
</div>

<script>

let controlMode = false;

function toggleMode(){
    controlMode = !controlMode;
    const btn = document.getElementById("modeBtn");

    if(controlMode){
        if(!confirm("Enter CONTROL MODE?")){
            controlMode = false;
            return;
        }
        btn.innerText = "CONTROL MODE";
        btn.classList.add("control");
    }else{
        btn.innerText = "VIEW MODE";
        btn.classList.remove("control");
    }
}

async function loadDevices(){
    const response = await fetch('/devices');
    const devices = await response.json();
    const grid = document.getElementById('grid');
    grid.innerHTML = '';

    devices.forEach(device=>{
        const div = document.createElement('div');
        div.className = 'camera';
        if(controlMode) div.classList.add("control-mode");

        div.innerHTML = `
            <div class="label">${device.name} (${device.ip})</div>
            <img src="http://${device.ip}:5000/video">
        `;

        div.onclick = () => openDevice(device.ip);
        grid.appendChild(div);
    });
}

function openDevice(ip){
    const modal = document.getElementById('modal');
    const frame = document.getElementById('modalFrame');

    if(controlMode){
        frame.src = `http://${ip}:5000/`;
    } else {
        frame.src = `http://${ip}:5000/video`;
    }

    modal.style.display = "block";
}

function closeModal(){
    document.getElementById('modal').style.display = "none";
    document.getElementById('modalFrame').src = "";
}

loadDevices();
setInterval(loadDevices, 15000);

</script>

</body>
</html>
""")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)