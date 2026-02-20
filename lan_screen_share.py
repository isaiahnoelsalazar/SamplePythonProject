from flask import Flask, Response
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
        <title>Local Screen Share</title>
    </head>
    <body>
        <img src="/video" width="100%">
    </body>
    </html>
    """


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    print(f"\nShare this link on your local network:")
    print(f"http://{local_ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)