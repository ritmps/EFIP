import sys
import cv2
import argparse
import threading
import time
import os

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

def read_cam():
    global img, stop_thread

    firstloop = True
    stop_thread = False

    cap = cv2.VideoCapture(gstreamer_in())

    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('Src opened, %dx%d @ %d fps' % (w, h, fps))

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

                if firstloop and ret_val:
                    t = threading.Thread(target=capture_img)
                    t.start()
                    firstloop = False
                elif firstloop and not ret_val:
                    break
                elif not firstloop and not ret_val:
                    stop_thread = True
                    t.join()
                    break
                out.write(img)
                cv2.waitKey(1)
            except KeyboardInterrupt:
                stop_thread = True
                t.join()
                break
    else:
        print("pipeline open failed")

    print("successfully exit")
    cap.release()
    out.release()
    t.join()

if __name__ == '__main__':
    parse_args()
    read_cam()