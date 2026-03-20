from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
from ultralytics import YOLO
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
import threading
import time
import requests
import os

app = Flask(__name__)

# -----------------------------
# RTSP STREAMS
# -----------------------------
CAM1 = "rtsp://172.20.10.3:8554/cam1"
CAM2 = "rtsp://172.20.10.3:8554/cam2"
CAM3 = "rtsp://172.20.10.3:8554/cam3"
CAM4 = "rtsp://172.20.10.3:8554/cam4"

system_status = "SYSTEM NORMAL"

# -----------------------------
# ENV VARIABLES (SAFE 🔐)
# -----------------------------
ACCOUNT_SID = os.getenv("TWILIO_SID")
AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
MY_PHONE = os.getenv("MY_PHONE")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)

# -----------------------------
# ESP32 BUZZER
# -----------------------------
ESP32_BUZZER = "http://172.20.10.2/buzz"

def trigger_buzzer():
    try:
        requests.get(ESP32_BUZZER, timeout=2)
        print("BUZZER TRIGGERED")
    except:
        print("ESP32 NOT REACHABLE")

# -----------------------------
# MODEL PATH FIX 🔥
# -----------------------------
MODEL_PATH = os.path.join(os.getcwd(), "best.pt")
fire_model = YOLO(MODEL_PATH)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# -----------------------------
# ALERT FUNCTIONS
# -----------------------------
def send_sms(camera):
    try:
        twilio_client.messages.create(
            body=f"🚨 ALERT: Accident detected on {camera}",
            from_=TWILIO_NUMBER,
            to=MY_PHONE
        )
        print("SMS SENT")
    except Exception as e:
        print("SMS ERROR:", e)

def send_email(camera):
    try:
        msg = MIMEText(f"🚨 Accident detected on {camera}")
        msg["Subject"] = "Industrial Accident Alert"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_RECEIVER

        server = smtplib.SMTP_SSL("smtp.gmail.com",465)
        server.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_RECEIVER, msg.as_string())
        server.quit()

        print("EMAIL SENT")
    except Exception as e:
        print("EMAIL ERROR:", e)

# -----------------------------
# DETECTIONS
# -----------------------------
def detect_collapse(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if not results.pose_landmarks:
        return False

    lm = results.pose_landmarks.landmark
    shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
    ankle = lm[mp_pose.PoseLandmark.LEFT_ANKLE]

    if abs(shoulder.y - ankle.y) < 0.15 and abs(shoulder.x - ankle.x) > 0.25:
        return True

    return False

def detect_fire(frame):
    results = fire_model(frame)

    for r in results:
        for box in r.boxes:
            conf = float(box.conf)
            if conf > 0.30:
                x1,y1,x2,y2 = map(int,box.xyxy[0])
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),3)
                return True

    return False

# -----------------------------
# STREAM
# -----------------------------
def generate_frames(rtsp, cam_name):

    global system_status
    cap = cv2.VideoCapture(rtsp)

    frame_count = 0
    last_alert = 0
    fire_memory = 0
    collapse_memory = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Reconnecting...")
            time.sleep(1)
            cap.release()
            cap = cv2.VideoCapture(rtsp)
            continue

        frame_count += 1
        detected = False

        if frame_count % 6 == 0:

            if detect_fire(frame):
                fire_memory = 30
                detected = True
                system_status = "🚨 FIRE DETECTED"

            elif detect_collapse(frame):
                collapse_memory = 30
                detected = True
                system_status = "🚨 COLLAPSE DETECTED"

        if fire_memory > 0:
            fire_memory -= 1
            cv2.putText(frame,"FIRE DETECTED",(40,60),
                        cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)

        elif collapse_memory > 0:
            collapse_memory -= 1
            cv2.putText(frame,"COLLAPSE DETECTED",(40,60),
                        cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)

        if detected and time.time() - last_alert > 25:
            print("🚨 ALERT:", cam_name)

            threading.Thread(target=send_sms,args=(cam_name,)).start()
            threading.Thread(target=send_email,args=(cam_name,)).start()
            threading.Thread(target=trigger_buzzer).start()

            last_alert = time.time()

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    return jsonify({"status": system_status})

@app.route("/cam1")
def cam1():
    return Response(generate_frames(CAM1,"CAM1"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/cam2")
def cam2():
    return Response(generate_frames(CAM2,"CAM2"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/cam3")
def cam3():
    return Response(generate_frames(CAM3,"CAM3"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/cam4")
def cam4():
    return Response(generate_frames(CAM4,"CAM4"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5050,debug=True)
