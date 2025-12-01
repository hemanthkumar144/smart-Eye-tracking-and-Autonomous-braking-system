import cv2
import mediapipe as mp
import math
import time
import serial

arduino = serial.Serial('COM4', 9600)

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1
)

def distance(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def eye_aspect_ratio_mediapipe(landmarks, eye):
    left_corner  = landmarks[eye[0]]
    right_corner = landmarks[eye[1]]

    upper1 = landmarks[eye[2]]
    lower1 = landmarks[eye[3]]

    upper2 = landmarks[eye[4]]
    lower2 = landmarks[eye[5]]

    vertical = distance(upper1, lower1) + distance(upper2, lower2)
    horizontal = distance(left_corner, right_corner)

    return vertical / (2.0 * horizontal)

cap = cv2.VideoCapture(1)

EAR = 0.0
closed_start_time = None
stage = 0

# Set timings for each stage
STAGE1_TIME = 1.5   # seconds
STAGE2_TIME = 3.0
STAGE3_TIME = 5.0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_face_mesh.process(rgb)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        left_eye  = [33, 133, 160, 144, 158, 153]
        right_eye = [362, 263, 387, 373, 385, 380]

        EAR_left  = eye_aspect_ratio_mediapipe(landmarks, left_eye)
        EAR_right = eye_aspect_ratio_mediapipe(landmarks, right_eye)
        EAR = (EAR_left + EAR_right) / 2

        if EAR < 0.19:  # Eyes closed
            if closed_start_time is None:
                closed_start_time = time.time()

            closed_duration = time.time() - closed_start_time

            # Stage updates based on duration
            if closed_duration >= STAGE3_TIME:
                stage = 3
                arduino.write(b'3')
            elif closed_duration >= STAGE2_TIME:
                stage = 2
                arduino.write(b'2')
            elif closed_duration >= STAGE1_TIME:
                stage = 1
                arduino.write(b'1')

        else:  # Eyes open → reset everything
            closed_start_time = None
            stage = 0
            arduino.write(b'0')

    # ------------ Display Text ------------
    cv2.putText(frame, f"EAR: {EAR:.2f}", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    if closed_start_time:
        cv2.putText(frame, f"Closed Time: {time.time() - closed_start_time:.2f}s",
                    (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
    else:
        cv2.putText(frame, "Closed Time: 0", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

    cv2.putText(frame, f"Stage: {stage}", (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,128,255), 2)

    cv2.imshow("Driver Monitor - Project 2.0", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
5
