import imutils
import cv2
from threading import Thread
from imutils import face_utils
import dlib
from pygame import mixer
import time

class DrowsinessDetectionSystem:
    def __init__(self):
        self.detection_active = False
        self.alarm_status = False
        self.alarm_status2 = False
        self.flag = 0
        self.frame_check = 30
        self.thresh = 0.3
        self.yawn_thresh = 20
        self.lStart, self.lEnd = 42, 48
        self.rStart, self.rEnd = 36, 42
        self.predictor = self.load_predictor()
        
        mixer.init()
        mixer.music.load("music.wav")
        
        self.yawn_count = 0
        self.yawn_start_time = None
        self.last_yawn_time = None

    def load_predictor(self):
        predictor_path = "models/shape_predictor_68_face_landmarks.dat"
        return dlib.shape_predictor(predictor_path)

    def start_detection(self):
        self.detection_active = True
        print("Drowsiness detection started.")

    def stop_detection(self):
        self.detection_active = False
        print("Drowsiness detection stopped.")

    def detect(self, gray_frame, scale_factor):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=scale_factor, minNeighbors=5)
        return faces

    def process_frame(self, frame):
        if not self.detection_active:
            return frame

        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        subjects = self.detect(gray, 1.1)

        frame_height, frame_width = frame.shape[:2]

        for (x, y, w, h) in subjects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            shape = self.predictor(gray, dlib.rectangle(x, y, x + w, y + h))
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[self.lStart:self.lEnd]
            rightEye = shape[self.rStart:self.rEnd]
            leftEAR = self.eye_aspect_ratio(leftEye)
            rightEAR = self.eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0

            distance = self.lip_distance(shape)

            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
            lip = shape[48:60]
            cv2.drawContours(frame, [lip], -1, (0, 255, 0), 1)

            # Eye closure detection
            if ear < self.thresh:
                self.flag += 1
                if self.flag >= self.frame_check:
                    cv2.putText(frame, "ALERT! Wake up!", (frame_width - 200, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if not self.alarm_status:
                        self.alarm_status = True
                        t = Thread(target=self.alarm, args=("Wake up! You seem drowsy.",))
                        t.daemon = True
                        t.start()
            else:
                self.flag = 0
                self.alarm_status = False
                mixer.music.stop()

            # Yawn detection logic with duration check
            if distance > self.yawn_thresh:
                cv2.putText(frame, "Yawn Alert", (frame_width - 200, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if self.yawn_start_time is None:
                    self.yawn_start_time = time.time()
                elif time.time() - self.yawn_start_time >= 1:
                    if not self.alarm_status2:
                        self.alarm_status2 = True
                        self.yawn_count += 1
                        self.yawn_start_time = None
                        self.last_yawn_time = time.time()

                    if self.yawn_count >= 4:
                        cv2.putText(frame, "You are sleepy, take a rest", (frame_width - 250, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        if not self.alarm_status:
                            self.alarm_status = True
                            t = Thread(target=self.alarm, args=("You are sleepy, take a rest.",))
                            t.daemon = True
                            t.start()
            else:
                self.alarm_status2 = False
                self.yawn_start_time = None

            # Reset yawn count if no yawn detected for 30 seconds
            if self.last_yawn_time and time.time() - self.last_yawn_time > 30:
                self.yawn_count = 0
                self.alarm_status = False

            # Display EAR, yawn distance, and yawn count
            cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"YAWN: {distance:.2f}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Yawn Count: {self.yawn_count}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return frame

    def eye_aspect_ratio(self, eye):
        A = cv2.norm(eye[1] - eye[5])
        B = cv2.norm(eye[2] - eye[4])
        C = cv2.norm(eye[0] - eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def lip_distance(self, shape):
        top_lip = shape[51]
        bottom_lip = shape[57]
        distance = cv2.norm(top_lip - bottom_lip)
        return distance

    def alarm(self, message):
        mixer.music.play(-1)
        print(message)
