import socket, threading
import random

from collections import deque

from cv2 import VideoCapture
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time

#BALL TRACKING
# tracks objects given their hsv color values. 

# import the necessary packages
from collections import deque

from cv2 import VideoCapture
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
# construct the argument parse and parse the arguments





class Ball():
    #State of the ball
    bx = 0.0 
    by = 0.0
    

    def __init__(self) -> None:
        pass

    def get(self):
        return self.bx, self.by

    def set(self, x, y):
        self.bx = x
        self.by = y
        
class Sensor():
    # state of the sensor
    leftGoal = False
    rightgoal = False

    def __init__(self):
        pass

    def get(self):
       return leftGoal, rightGoal

    def set(self, left, right):
        self.leftGoal = left
        self.rightgoal = right

#global ball        
theBall = Ball()
theSensor = Sensor()

class BallThread(threading.Thread):
      #Ball tracking
    def gstreamer_pipeline(
        # create camera pipeline
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

    def __init__(self):

        global vs 
        print(BallThread.gstreamer_pipeline(flip_method=0))
        vs = VideoCapture(BallThread.gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

        time.sleep(2.0)

        threading.Thread.__init__(self)
        #initialize camera
        print("Ball Thread initialized")


        # print(BallThread.gstreamer_pipeline(flip_method=0))
        

        #perhaps call color picker.
        
    


# MAKE CLEANUP CODE FOR WHEN THIS THREAD IS KILLED
    def findBall(self):
        # if theres a signal from the GPIO pin, do X
        
        global theBall

        window_title = "CSI Camera"

        # To flip the image, modify the flip_method parameter (0 and 2 are the most common)
        ap = argparse.ArgumentParser()
        ap.add_argument("-v", "--video",
        help="path to the (optional) video file")
        ap.add_argument("-b", "--buffer", type=int, default=64,
        help="max buffer size")
        args = vars(ap.parse_args())
        # define the lower and upper boundaries of the "green"
        # ball in the HSV color space, then initialize the
        # list of tracked points
        greenLower = (5, 169, 107)
        greenUpper = (25, 309, 287)
        pts = deque(maxlen=args["buffer"])
        if vs.isOpened():
            try:
                window_handle = cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
                while True:
                    # grab the current frame
                    ret_val, frame = vs.read()  # created an error, was frame = vs.read() at first
                    # handle the frame from VideoCapture or VideoStream
                    frame = frame[1] if args.get("video", False) else frame
                    # if we are viewing a video and we did not grab a frame,
                    # then we have reached the end of the video
                    if frame is None:
                        break

                    #print(frame)

                    # resize the frame, blur it, and convert it to the HSV
                    # color space
                    frame = imutils.resize(frame, width=600)
                    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
                    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
                    # construct a mask for the color "green", then perform
                    # a series of dilations and erosions to remove any small
                    # blobs left in the mask
                    mask = cv2.inRange(hsv, greenLower, greenUpper)
                    mask = cv2.erode(mask, None, iterations=2)
                    mask = cv2.dilate(mask, None, iterations=2)
                        # find contours in the mask and initialize the current
                    # (x, y) center of the ball
                    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)
                    cnts = imutils.grab_contours(cnts)
                    center = None
                    # only proceed if at least one contour was found
                    x = 0
                    y = 0

                    if len(cnts) > 0:
                        # find the largest contour in the mask, then use
                        # it to compute the minimum enclosing circle and
                        # centroid
                        c = max(cnts, key=cv2.contourArea)
                        ((x, y), radius) = cv2.minEnclosingCircle(c)
                        print("x coord: ", x, "y coord: ", y)
                        M = cv2.moments(c)
                        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                        # only proceed if the radius meets a minimum size
                        if radius > 10:
                            # draw the circle and centroid on the frame,
                            # then update the list of tracked points
                            cv2.circle(frame, (int(x), int(y)), int(radius),
                                (0, 255, 255), 2)
                            cv2.circle(frame, center, 5, (0, 0, 255), -1)
                    # update the points queue
                    pts.appendleft(center)
                        # loop over the set of tracked points
                    for i in range(1, len(pts)):
                        # if either of the tracked points are None, ignore
                        # them
                        if pts[i - 1] is None or pts[i] is None:
                            continue
                        # otherwise, compute the thickness of the line and
                        # draw the connecting lines
                        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
                        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
                    theBall.set(x, y)
                    if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                        cv2.imshow(window_title, frame)
                    else:
                        break 
                    keyCode = cv2.waitKey(10) & 0xFF
                    # Stop the program on the ESC key or 'q'
                    if keyCode == 27 or keyCode == ord('q'):
                        break
            finally:
                vs.release()
                cv2.destroyAllWindows()
        else:
            print("Error: Unable to open camera")

        # return true while works return false if doesnt then in the loop terminate the vs when done



    
    def run(self):
        #calls find ball over and over
        print("Ball thread go")
        while self.findBall():
            self.findBall()
        vs.release()
        cv2.destroyAllWindows()
        
    

class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print ("New connection added: ", clientAddress)
    def run(self):
        global theBall

        print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''


        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            #print ("from client", msg)
            if msg=='bye':
              break

            
            bx, by = theBall.get()

            msg = str(bx) + ',' + str(-by)
            self.csocket.send(bytes(msg,'UTF-8'))
        
        print ("Client at ", clientAddress , " disconnected...")


LOCALHOST = "129.21.55.120"
PORT = 9998
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")


while True:
    server.listen(1)
    clientsock, clientAddress = server.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()
    ballThread = BallThread()
    ballThread.start()


    
