import sys
import cv2
import argparse
import threading
import time
import os
import numpy as np
import imutils
from collections import deque

# Define the input stream for gstreamer
def gstreamer_in(width=1920, height=1080, fps=60):
    pipeinParams = \
        f"nvarguscamerasrc ! " \
        f"video/x-raw(memory:NVMM), width={width}, height={height}, format=(string)NV12, framerate={fps}/1 ! " \
        f"nvvidconv flip-method=0 ! "\
        f"video/x-raw, width=1920, height=1080, format=(string)BGRx ! " \
        f"videoconvert ! " \
        f"video/x-raw, format=(string)BGR ! " \
        f"appsink"
    return (pipeinParams)

# Define the output stream for gstreamer
def gstreamer_out(host, port):
    pipeoutParams = \
        f"appsrc ! " \
        f"video/x-raw, format=BGR ! " \
        f"queue ! " \
        f"videoconvert ! " \
        f"video/x-raw,format=BGRx ! " \
        f"nvvidconv ! " \
        f"nvv4l2h264enc ! " \
        f"h264parse ! " \
        f"rtph264pay pt=96 config-interval=1 ! " \
        f"udpsink host={host} port={port}"
    return (pipeoutParams)

def parse_args():
    global inputhost, inputport, directory, buffer
    global pts
    global hueL, hueU, satL, satU, valL, valU

    # greenLower = (65, 39, 46)
    # greenUpper = (85, 256, 226)

    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', default="0.0.0.0", help="Host's port\n(Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', default="5004", help="Host's port\n(Default: 5004)")
    parser.add_argument('-d', '--directory', default="./Images", help="Directory to save images\n(Default: ./Images)")
    parser.add_argument("-b", "--buffer", type=int, default=64, help="Max buffer size\n(Default: 64)")
    parser.add_argument("-hl", "--hueL", type=int, default=65, help="Hue lower bound\n(Default: 65)")
    parser.add_argument("-hu", "--hueU", type=int, default=85, help="Hue upper bound\n(Default: 85)")
    parser.add_argument("-sl", "--satL", type=int, default=39, help="Saturation lower bound\n(Default: 39)")
    parser.add_argument("-su", "--satU", type=int, default=256, help="Saturation upper bound\n(Default: 256)")
    parser.add_argument("-vl", "--valL", type=int, default=46, help="Value lower bound\n(Default: 46)")
    parser.add_argument("-vu", "--valU", type=int, default=226, help="Value upper bound\n(Default: 226)")
    args = parser.parse_args()
    inputhost = args.host
    inputport = args.port
    directory = args.directory
    buffer = args.buffer
    pts = deque(maxlen=buffer)
    hueL, hueU, satL, satU, valL, valU = args.hueL, args.hueU, args.satL, args.satU, args.valL, args.valU

    print(f'Host: {inputhost}\nPort: {inputport}')

def capture_img():
    global img, stop_thread, directory

    img_num = 0

    while True:
        cv2.imwrite(os.path.join(directory, f'capture_{img_num}.png'), img)
        time.sleep(1)
        img_num += 1
        if stop_thread:
            break

# Function to create a look up table for distortion correction
def genDistortLUT(height, width):
    intrinsic = np.array([[1199.17733051303,    0.00000000000, 985.626449326511],
                          [   0.00000000000, 1199.46005470673, 508.709722436638],
                          [   0.00000000000,    0.00000000000,   1.000000000000]])
    distortion = np.array([-0.337537993348494, 0.111347442559380, 0.0, 0.0, 0.0])

    height = int(height)
    width = int(width)

    # Generate new camera matrix from parameters
    newcameramatrix, roi = cv2.getOptimalNewCameraMatrix(intrinsic, distortion, (width, height), 0)

    # Generate look-up tables for remapping the camera image
    mapx, mapy = cv2.initUndistortRectifyMap(intrinsic, distortion, None, newcameramatrix, (width, height), cv2.CV_16SC2)
    # cv2.convertMaps(mapx, mapy, cv2.CV_32FC1)

    print(roi)

    return (mapx, mapy)

# Function to undistort the image using the look up table
def undistort_img(image, lutmapx, lutmapy):
    undist = cv2.remap(image, lutmapx, lutmapy, cv2.INTER_LINEAR)
    return undist

# Filter the image based on the hue, saturation, and value
def color_track(image):
    global hueL, hueU, satL, satU, valL, valU

    hsvLower = (hueL, satL, valL)
    hsvUpper = (hueU, satU, valU)

    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, hsvLower, hsvUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Find contours in the mask and initialize the current (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    center = None

    # Only proceed if at least one contour was found
    if len(cnts) > 0:
        # Find the largest contour in the mask, then use it to compute the minimum enclosing circle and centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        print("x coord: ", x, "y coord: ", y)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        # Only proceed if the radius meets a minimum size
        if radius > 5:
            # Draw the circle and centroid on the frame, then update the list of tracked points
            cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            cv2.circle(image, center, 5, (0, 0, 255), -1)
    
    # Update the points queue
    pts.appendleft(center)

    # Loop over the set of tracked points
    for i in range(1, len(pts)):
        # If either of the tracked points are None, ignore them
        if pts[i - 1] is None or pts[i] is None:
            continue

        # Otherwise, compute the thickness of the line and draw the connecting lines
        thickness = int(np.sqrt(buffer / float(i + 1)) * 2.5)
        cv2.line(image, pts[i - 1], pts[i], (0, 0, 255), thickness)
    
    return image

def read_cam():
    global img, stop_thread

    # First iteration of the while loop = true
    firstloop = True

    # Stop any running threads = false
    stop_thread = False

    # Read Gstreamer pipeline into OpenCV (pipein)
    cap = cv2.VideoCapture(gstreamer_in(), cv2.CAP_GSTREAMER)

    # Get the width, height and fps of the stream and print it to the console
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f'\n--------------------------------------------------\n' \
          f'Src opened, {w}x{h} @ {fps} fps' \
          f'\n--------------------------------------------------\n')

    # Create a look up table for distortion correction
    lutmapx, lutmapy = genDistortLUT(h, w)

    # Write OpenCV frames to Gstreamer stream (pipeout)
    gst_out = gstreamer_out(host=inputhost, port=inputport)
    out = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(fps), (int(w), int(h)))

    if not out.isOpened():
        print('\n--------------------------------------------------\n' \
              'Failed to open output' \
              '\n--------------------------------------------------\n')
        exit()

    if cap.isOpened():
        # Give the camera time to warm up
        time.sleep(2.0)
        while True:
            try:
                ret_val, img = cap.read()

                if not ret_val:
                    break
                
                # Undistort the image
                undist_img = undistort_img(img, lutmapx, lutmapy)

                # Image with the track
                track_img = color_track(undist_img)

                out.write(track_img)
                cv2.waitKey(1)
            except KeyboardInterrupt:
                break
    else:
        print("pipeline open failed")

    print("successfully exit")

if __name__ == '__main__':
    parse_args()
    read_cam()