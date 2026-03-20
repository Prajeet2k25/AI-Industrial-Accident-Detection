import time
import math

class EmergencyDetector:
    def __init__(self):
        self.prev_center_y = None
        self.prev_time = None

        self.state = "STANDING"
        self.motionless_frames = 0
        self.falling_detected = False

    def calculate_angle(self, landmarks):
        # Shoulder (11) and Hip (23)
        x1, y1 = landmarks[11]
        x2, y2 = landmarks[23]

        dx = x2 - x1
        dy = y2 - y1

        angle = abs(math.degrees(math.atan2(dy, dx)))
        return angle

    def calculate_velocity(self, center_y):
        current_time = time.time()

        if self.prev_center_y is None:
            self.prev_center_y = center_y
            self.prev_time = current_time
            return 0

        dt = current_time - self.prev_time
        velocity = abs(center_y - self.prev_center_y) / (dt + 1e-6)

        self.prev_center_y = center_y
        self.prev_time = current_time

        return velocity

    def process(self, landmarks):
        event = None

        # Body center
        center_y = (landmarks[11][1] + landmarks[23][1]) / 2

        angle = self.calculate_angle(landmarks)
        velocity = self.calculate_velocity(center_y)

        # -----------------------------------
        # Sudden collapse detection
        # -----------------------------------
        if velocity > 0.15 and angle < 45:
            self.falling_detected = True

        # -----------------------------------
        # Motionless detection
        # -----------------------------------
        if velocity < 0.01:
            self.motionless_frames += 1
        else:
            self.motionless_frames = 0

        # -----------------------------------
        # Classification Logic
        # -----------------------------------

        # Sudden collapse + motionless
        if self.falling_detected and self.motionless_frames > 60:
            event = "SUDDEN COLLAPSE DETECTED"

        # Gradual fatigue
        elif velocity < 0.05 and 40 < angle < 70 and self.motionless_frames > 80:
            event = "POSSIBLE FATIGUE"

        # Unresponsive horizontal
        elif angle < 35 and self.motionless_frames > 100:
            event = "UNRESPONSIVE PERSON"

        return event, angle, velocity
