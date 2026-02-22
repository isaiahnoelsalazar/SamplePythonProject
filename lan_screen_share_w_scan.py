import pyautogui
from flask import Flask, Response, request, jsonify
import cv2
import numpy as np
import mss
import socket

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
    return f"""
    <html>
    <head>
        <title>Remote Control</title>
    </head>
    <body style="margin:0; overflow:hidden;">
        <img id="screen" src="/video" width="100%">

        <script>
        const img = document.getElementById("screen");

        // Mouse Click
        img.addEventListener("click", function(e) {{
            const rect = img.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (img.naturalWidth / rect.width);
            const y = (e.clientY - rect.top) * (img.naturalHeight / rect.height);

            fetch("/control", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ action: "click", x: x, y: y }})
            }});
        }});

        // Keyboard
        document.addEventListener("keydown", function(e) {{
            fetch("/control", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ action: "key", key: e.key }})
            }});
        }});
        </script>
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
    # return "screen-share-active"
    return {
        "status": "online",
        "name": socket.gethostname()
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)