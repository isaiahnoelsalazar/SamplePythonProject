import pyautogui
from flask import Flask, Response, request, jsonify
import cv2
import numpy as np
import mss
import socket
import os
import signal

app = Flask(__name__)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


local_ip = get_local_ip()


def generate_frames():
    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while True:
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            frame = buffer.tobytes()

            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'


@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Remote Control</title>
        <style>
            html, body {
                margin:0;
                background:black;
                height:100%;
                overflow:hidden;
                display:flex;
                justify-content:center;
                align-items:center;
            }

            #screen {
                max-width:100%;
                max-height:100%;
                object-fit:contain;
            }
        </style>
    </head>
    <body>
        <img id="screen" src="/video">

        <script>
        const img = document.getElementById("screen");

        img.addEventListener("click", function(e) {
            const rect = img.getBoundingClientRect();
            const scaleX = img.naturalWidth / rect.width;
            const scaleY = img.naturalHeight / rect.height;

            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;

            fetch("/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "click", x: x, y: y })
            });
        });

        document.addEventListener("keydown", function(e) {
            fetch("/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "key", key: e.key })
            });
        });
        </script>
    </body>
    </html>
    """


@app.route('/no-control')
def no_control():
    return """
    <html>
    <head>
        <style>
            html, body {
                margin:0;
                background:black;
                height:100%;
                overflow:hidden;
                display:flex;
                justify-content:center;
                align-items:center;
            }

            img {
                max-width:100%;
                max-height:100%;
                object-fit:contain;
            }
        </style>
    </head>
    <body>
        <img src="/video">
    </body>
    </html>
    """


@app.route('/control', methods=['POST'])
def control():
    data = request.json
    action = data.get("action")

    if action == "click":
        x = int(data["x"])
        y = int(data["y"])
        pyautogui.click(x, y)

    elif action == "move":
        x = int(data["x"])
        y = int(data["y"])
        pyautogui.moveTo(x, y)

    elif action == "key":
        key = data["key"]
        pyautogui.press(key)

    return jsonify({"status": "ok"})


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/health')
def health():
    return {
        "status": "online",
        "name": socket.gethostname()
    }


@app.route('/end')
def end():
    os.kill(os.getpid(), signal.SIGINT)
    return "end"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)