import cv2
import dlib
import time
import serial
from scipy.spatial import distance
from threading import Thread

# ---------------- Serial Setup ----------------
arduino = serial.Serial('COM4', 9600)
time.sleep(2)

# ---------------- Helper Function ----------------
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# ---------------- Dlib Setup ----------------
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Tuning parameters
EAR_THRESHOLD = 0.25
CLOSED_FRAMES = 20

counter = 0
sleep_count = 0
sleep_stage_triggered = False

# ---------------- START BUTTON FLAG ----------------
system_started = False     # <--- NEW

# ---------------- Threaded Video Capture ----------------
class VideoStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = self.cap.read()
        self.stopped = False
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.stopped = True
        self.thread.join()
        self.cap.release()

# ---------------- Initialize Video Stream ----------------
vs = VideoStream(0)
cv2.namedWindow("Driver Sleep Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Driver Sleep Detection", 800, 600)

frame_count = 0
PROCESS_EVERY = 3

print("[INFO] Press 's' to START the system.")
print("[INFO] After starting, press 'q' to quit.")

# ---------------- Main Loop ----------------
try:
    while True:
        frame_count += 1
        ret, frame = vs.read()
        if not ret or frame is None:
            continue

        # ---------------- WAIT FOR START ----------------
        if not system_started:
            cv2.putText(
                frame,
                "Press 'S' to start the system",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            cv2.imshow("Driver Sleep Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                system_started = True
                arduino.write(b'S')       # send start command
                print("[INFO] System STARTED. Motor ON.")
            continue

        # -------------------------------------------------

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        if frame_count % PROCESS_EVERY == 0:
            faces = detector(gray)

            for face in faces:
                landmarks = predictor(gray, face)

                leftEye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
                rightEye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]

                avgEAR = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0

                # ------------- EYES CLOSED -------------
                if avgEAR < EAR_THRESHOLD:
                    counter += 1

                else:
                    if counter > CLOSED_FRAMES:
                        sleep_count += 1
                        sleep_stage_triggered = False

                    counter = 0
                    arduino.write(b'N')

                # ------------- STAGE LOGIC -------------
                if counter >= CLOSED_FRAMES and not sleep_stage_triggered:
                    sleep_stage_triggered = True

                    if sleep_count == 0:
                        arduino.write(b'A')
                        print("[STAGE 1] First sleep event → Buzzer only (A)")

                    elif sleep_count == 1:
                        arduino.write(b'B')
                        print("[STAGE 2] Second sleep event → Buzzer + Hazards (B)")

                    elif sleep_count >= 2:
                        arduino.write(b'C')
                        print("[STAGE 3] Continuous sleep → Brake + Hazards + Buzzer (C)")

                cv2.putText(
                    frame,
                    f"EAR: {avgEAR:.2f} | Sleep Count: {sleep_count} | ClosedFrames: {counter}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

        cv2.imshow("Driver Sleep Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    vs.stop()
    cv2.destroyAllWindows()
    print("[INFO] System shut down.")
