import sys
import cv2
import argparse

def gstreamer_out(
    # create camera pipeline
    host,
    port
):
    return (
        "appsrc ! "
        "video/x-raw, format=BGR ! "
        "queue ! "
        "videoconvert ! "
        "video/x-raw,format=BGRx ! "
        "nvvidconv ! "
        "nvv4l2h264enc ! "
        "h264parse ! "
        "rtph264pay pt=96 config-interval=1 ! "
        "udpsink host=%s port=%s"
        % (
            host,
            port,
        )
    )

def read_cam():
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', default="0.0.0.0", help="Host's port\n(Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', default="5004", help="Host's port\n(Default: 5004)")
    args = parser.parse_args()
    inputhost = args.host
    inputport = args.port

    print(f'Host: {inputhost}\nPort: {inputport}')

    cap = cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1920, height=1080, format=(string)NV12, framerate=60/1 ! nvvidconv flip-method=0 ! video/x-raw, width=1920, height=1080, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink')

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
            ret_val, img = cap.read()
            if not ret_val:
                break
            out.write(img)
            cv2.waitKey(1)
    else:
     print("pipeline open failed")

    print("successfully exit")
    cap.release()
    out.release()


if __name__ == '__main__':
    read_cam()