from flask import Flask, render_template, Response, jsonify
import cv2
from drowsiness_detection import DrowsinessDetectionSystem

# Initialize Flask app
app = Flask(__name__)

# Initialize video capture and detection system
camera = cv2.VideoCapture(0)
detection_system = DrowsinessDetectionSystem()
alert_message = ""  # Variable to store the alert message


@app.route('/')
def index():
    return render_template('index.html')


def generate_frames():
    global alert_message
    while True:
        success, frame = camera.read()
        if not success:
            break

        # Process frame through drowsiness detection system
        frame = detection_system.process_frame(frame)  # Apply detection logic

        # Update alert message
        if detection_system.alarm_status:
            alert_message = "You are sleepy, take some rest"
        elif detection_system.alarm_status2:
            alert_message = "Yawn Alert: Take a break!"
        else:
            alert_message = ""

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_detection', methods=['POST'])
def start_detection():
    detection_system.start_detection()
    return jsonify({"status": "Detection started"})


@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    detection_system.stop_detection()
    return jsonify({"status": "Detection stopped"})


@app.route('/get_alert', methods=['GET'])
def get_alert():
    return jsonify({"alert": alert_message})


if __name__ == '__main__':
    app.run(debug=False)
