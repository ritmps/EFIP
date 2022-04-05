import cv2
from cv2 import VideoCapture
import imutils  
import numpy as np  

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
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

print(gstreamer_pipeline(flip_method=0))
cap = VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
#cap = cv2.VideoCapture(0) # getting video from webcam
while cap.isOpened():
    ret, img = cap.read()

    cv2.imshow("Frame",img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('p'):
        cv2.imwrite("frame.jpg", img)
        print("frame captured")
        cv2.waitKey(-1) #wait until any key is pressed
cap.release()
cv2.destroyAllWindows()
image_hsv = None   # global
#pixel = (20,60,80) # some stupid default
# mouse callback function
def pick_color(event,x,y,flags,param):
    global upper, lower, pixel
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = image_hsv[y,x]

        #you might want to adjust the ranges(+-10, etc):
        upper =  np.array([pixel[0] + 10, pixel[1] + 70, pixel[2] + 90])
        lower =  np.array([pixel[0] - 10, pixel[1] - 70, pixel[2] - 90])
        print(pixel, lower, upper)

        image_mask = cv2.inRange(image_hsv,lower,upper)
        cv2.imshow("mask",image_mask)
        cv2.waitKey(0)

def main():
    import sys
    global upper, lower, pixel
    global image_hsv, pixel # so we can use it in mouse callback
    image_src = cv2.imread("frame.jpg")  # pick.py my.png
    image_src = imutils.resize(image_src, height=800)
    if image_src is None:
        print ("the image read is None............")
        return
    cv2.imshow("bgr",image_src)

    ## NEW ##
    cv2.namedWindow('hsv')
    cv2.setMouseCallback('hsv', pick_color)

    # now click into the hsv img , and look at values:
    image_hsv = cv2.cvtColor(image_src,cv2.COLOR_BGR2HSV)
    cv2.imshow("hsv",image_hsv)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cap = cv2.VideoCapture(0)
    while True:
        ret,frame = cap.read()


        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        image_mask = cv2.inRange(hsv,lower,upper)
        contours, _ = cv2.findContours(image_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    

        detections = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:
                #cv2.drawContours(roi, [cnt], -1, (0, 255, 0), 2)
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(image_mask, (x, y),(x + w, y + h), (100, 155, 0), 2)

        #detections.append({x, y})

        #print(detections)
        cv2.imshow("mask",image_mask)
        
        #result = cv2.bitwise_and(frame, frame, mask=mask)

        #cv2.imshow("video", frame)
        #cv2.imshow("mask", result)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
cap.release()


main()