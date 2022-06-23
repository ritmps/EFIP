import sys
import cv2
import argparse
import threading
import time
import os
import numpy as np

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
    global inputhost, inputport, directory

    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', default="0.0.0.0", help="Host's port\n(Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', default="5004", help="Host's port\n(Default: 5004)")
    parser.add_argument('-d', '--directory', default="./Images", help="Directory to save images\n(Default: ./Images)")
    args = parser.parse_args()
    inputhost = args.host
    inputport = args.port
    directory = args.directory

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
    mapx, mapy = cv2.initUndistortRectifyMap(intrinsic, distortion, None, newcameramatrix, (width, height), 5)

    return (mapx, mapy)

# Function to undistort the image using the look up table
def undistort_img(image, lutmapx, lutmapy):
    undist = cv2.remap(image, lutmapx, lutmapy, cv2.INTER_LINEAR)
    return undist

def read_cam():
    global img, stop_thread

    firstloop = True
    stop_thread = False

    cap = cv2.VideoCapture(gstreamer_in())

    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('Src opened, %dx%d @ %d fps' % (w, h, fps))

    # Create a look up table for distortion correction
    lutmapx, lutmapy = genDistortLUT(h, w)

    gst_out = gstreamer_out(host=inputhost, port=inputport)
    print(gst_out)

    out = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(fps), (int(w), int(h)))
    if not out.isOpened():
        print("Failed to open output")
        exit()

    if cap.isOpened():
        while True:
            try:
                ret_val, img = cap.read()

                if not ret_val:
                    break
                
                # Undistort the image
                undist_img = undistort_img(img, lutmapx, lutmapy)

                out.write(undist_img)
                cv2.waitKey(1)
            except KeyboardInterrupt:
                break
    else:
        print("pipeline open failed")

    print("successfully exit")

if __name__ == '__main__':
    parse_args()
    read_cam()