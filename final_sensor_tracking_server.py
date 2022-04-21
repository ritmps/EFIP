from ast import Break
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
import keyboard

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

# Sensor pins
import RPi.GPIO as GPIO
import time
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setup(21, GPIO.IN) # set the BOARD values and not the BCM values
GPIO.setup(23, GPIO.IN)
# print(GPIO.input(21), GPIO.input(23))


# construct the argument parse and parse the arguments
isQuitting = False




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
    leftGoal = 0
    rightGoal = 0

    def __init__(self):
        pass

    def get(self):
       return self.leftGoal, self.rightGoal

    def set(self, left, right):
        self.leftGoal = left
        self.rightgoal = right

#global ball        
theBall = Ball()
theSensor = Sensor()
scoreLeft = 0
scoreRight = 0

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
        # print(BallThread.gstreamer_pipeline(flip_method=0))
        vs = VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080,format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")#BallThread.gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

        # time.sleep(2.0)

        threading.Thread.__init__(self)
        #initialize camera
        print("Ball Thread initialized")


        # print(BallThread.gstreamer_pipeline(flip_method=0))
        

        #perhaps call color picker.
        
    


# MAKE CLEANUP CODE FOR WHEN THIS THREAD IS KILLED
    def findBall(self):
        # if theres a signal from the GPIO pin, do X

        global theBall
        global isQuitting
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
        greenLower = (67, 40, 31)
        greenUpper = (87, 180, 211)
        pts = deque(maxlen=args["buffer"])
        if vs.isOpened():
            try:
                # window_handle = cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
                while not isQuitting:
                    # grab the current frame
                    ret_val, frame = vs.read()  # created an error, was frame = vs.read() at first
                    # print("It read the vs")
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
                        theBall.set(x, y)
                        # print("x coord: ", x, "y coord: ", y)
                        M = cv2.moments(c)
                        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                print('Trying to release the camera 1.0')   
                vs.release()
                cv2.destroyAllWindows()     
            except: 
                print("Unable to open camera")
                
            vs.release()
            cv2.destroyAllWindows()
        else:
            print('Trying to release the camera 2.0')

        # return true while works return false if doesnt then in the loop terminate the vs when done



    
    def run(self):
        #calls find ball over and over
        print("Ball thread go")
        while self.findBall():
            pass
        vs.release()
        cv2.destroyAllWindows()
        
    

class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print ("New connection added: ", clientAddress)
    def run(self):
        global scoreLeft
        global scoreRight
        global theBall

        print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        global isQuitting

        while not isQuitting:
            data = self.csocket.recv(2048)
            msg = data.decode()
            #print ("from client", msg)
            #print(len(msg))
            if len(msg) == 0:
                print('He pressed bye')
                 
                isQuitting = True
                break
            bx, by = theBall.get()

            rX = (bx - 31.5) * 0.00214 
            rY = (by - 11.9) * 0.00214

            # put the pin 21 and pin 23 wire on ground and vcc and see if it's outputting 0 and 1 respectively
            if GPIO.input(21) == 1:
                scoreLeft += 1
                time.sleep(1)
            if GPIO.input(23) == 1:
                scoreRight += 1
                time.sleep(1)
            
            # MAKE A VARIABLE THAT ALWAYS SENDS THE CURRENT SCORE
            msg = str(time.perf_counter()) + "," + str(rX) + ',' + str(-rY) + "," + str(scoreLeft) + "," + str(scoreRight)

            if scoreLeft == 7 or scoreRight == 7:
                scoreLeft = 0
                scoreRight = 0
            # msg = str(rX)
            # print(str(rX))
            self.csocket.send(bytes(msg,'UTF-8'))
            

        
        print ("Client at ", clientAddress , " disconnected...")

LOCALHOST = "192.168.0.112" # "129.21.55.120"
PORT = 9998
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")


server.listen(1)
clientsock, clientAddress = server.accept()
newthread = ClientThread(clientAddress, clientsock)
newthread.start()
ballThread = BallThread()
ballThread.start()


    




    
