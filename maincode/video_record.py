from cv2 import VideoCapture
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time


def gstreamer_pipeline(
        # create camera pipeline
        sensor_id=0,
        capture_width=1920,
        capture_height=1080,
        display_width=960,
        display_height=540,
        framerate=30,
        flip_method=0
):
    return (
            "nvarguscamerasrc sensor-id=%d !"
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                sensor_id,
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


intrinsic = np.array([[584.053567693393, 0.0, 491.107498914361],
                      [0.0, 586.778383380614, 254.236382017895],
                      [0.0, 0.0, 1.0]])
distort = np.array([-0.318443099339647, 0.0945554774567145, 0.0, 0.0])

print(gstreamer_pipeline(flip_method=0))
cap = VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

time.sleep(2.0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Display the resulting frame
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) == ord('q'):
        break
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()