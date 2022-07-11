import argparse
import time
import imutils
import cv2
import numpy as np
import sys

global HOST, PORT, directory, tag_type

verbose = True

ARUCO_DICT = {
	"DICT_4X4_50": cv2.aruco.DICT_4X4_50,
	"DICT_4X4_100": cv2.aruco.DICT_4X4_100,
	"DICT_4X4_250": cv2.aruco.DICT_4X4_250,
	"DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
	"DICT_5X5_50": cv2.aruco.DICT_5X5_50,
	"DICT_5X5_100": cv2.aruco.DICT_5X5_100,
	"DICT_5X5_250": cv2.aruco.DICT_5X5_250,
	"DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
	"DICT_6X6_50": cv2.aruco.DICT_6X6_50,
	"DICT_6X6_100": cv2.aruco.DICT_6X6_100,
	"DICT_6X6_250": cv2.aruco.DICT_6X6_250,
	"DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
	"DICT_7X7_50": cv2.aruco.DICT_7X7_50,
	"DICT_7X7_100": cv2.aruco.DICT_7X7_100,
	"DICT_7X7_250": cv2.aruco.DICT_7X7_250,
	"DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
	"DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
	"DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
	"DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
	"DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
	"DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
}

def args_parse():
    global HOST, PORT, directory, tag_type
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', type=str, default="0.0.0.0", help="Host's port\n    (Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', type=int, default=5004, help="Host's port\n    (Default: 5004)")
    parser.add_argument('-d', '--directory', type=str, default="Tags", help="Directory to ArUCo tags\n    (Default: Tags)")
    parser.add_argument('-t', '--type', type=str, default="DICT_5X5_100", help="Type of ArUCo tag to detect\n    (Default: DICT_5X5_100)")
    args = parser.parse_args()
    HOST = args.host
    PORT = args.port
    directory = args.directory
    tag_type = ARUCO_DICT[args.type]
    print(f'Host: {HOST}\nPort: {PORT}')

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

def getDistortLUT():
    # Read the csv file and store in 2D array
    remap_lut = np.loadtxt('/home/fip/GitHub/EFIP/maincode/remap_lut.csv', delimiter=',', dtype=np.float32)
    
    # Split the array into mapx and mapy
    mapx, mapy = np.vsplit(remap_lut, 2)

    return (mapx, mapy)

# Function to undistort the image using the look up table
def undistort_img(image, lutmapx, lutmapy):
    undist = cv2.remap(image, lutmapx, lutmapy, cv2.INTER_LINEAR)
    return undist

def detect_aruco(image):
	# detect aruco tags
	aruco_dict = tag_type
	parameters = cv2.aruco.DetectorParameters_create()
	corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, aruco_dict, parameters=parameters)
	return corners, ids, rejectedImgPoints

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
    lutmapx, lutmapy = getDistortLUT()

    # Write OpenCV frames to Gstreamer stream (pipeout)
    gst_out = gstreamer_out(host=HOST, port=PORT)
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
                
                if verbose:
                    undist_time_init = time.time()
                # Undistort the image
                undist_img = undistort_img(img, lutmapx, lutmapy)
                if verbose:
                    print(f'[INFO] Undistort time: {(time.time() - undist_time_init) * 1000} ms')

                # if verbose:
                #     track_time_init = time.time()
                # # Image with the track
                # track_img = color_track(undist_img)
                # if verbose:
                #     print(f'[INFO] Track time: {(time.time() - track_time_init) * 1000} ms')

                out.write(undist_img)
                cv2.waitKey(1)
            except KeyboardInterrupt:
                break
    else:
        print("pipeline open failed")

    print("successfully exit")


if __name__ == '__main__':
    args_parse()
    read_cam()