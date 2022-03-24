import cv2
import numpy as np

cap = cv2.VideoCapture(0)


while True:

    ret,frame = cap.read()

    frame = cv2.resize(frame,(1200,700))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_range = np.array([10,100,20])
    upper_range = np.array([25,255,255])
    

    mask = cv2.inRange(hsv, lower_range, upper_range)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("video", frame)
    cv2.imshow("mask", result)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
