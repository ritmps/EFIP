# Arducam notes

- - -
**Remember - don't disconnect without powering down.**
- - -

## Setup


- `wget https://github.com/ArduCAM/MIPI_Camera/releases/download/v0.0.3/install_full.sh` (From releases down there)
- `chmod +x install_full.sh`
- `./install_full.sh -m imx477`
- Reboot OK...
- `ls /dev/video*` - you should see a device called `video0` or similar
- `sudo apt-get install v4l-utils`
- `v4l2-ctl --list-formats-ext`
```
ioctl: VIDIOC_ENUM_FMT
Index       : 0
Type        : Video Capture
Pixel Format: 'RG10'
Name        : 10-bit Bayer RGRG/GBGB
    Size: Discrete 4032x3040
        Interval: Discrete 0.033s (30.000 fps)
    Size: Discrete 3840x2160
        Interval: Discrete 0.033s (30.000 fps)
    Size: Discrete 1920x1080
        Interval: Discrete 0.017s (60.000 fps)
```
- Current `pip` is for 3.7, NVIDIA has 3.6.9 installed by default.
So get 
- `wget https://bootstrap.pypa.io/pip/3.6/get-pip.py`
- `sudo python3 get-pip.py` - you might get cache warnings. You're installing `pip` for all, so ignore them.
- `sudo pip install v4l2`
- `sudo pip install v4l2-fix` if bug.
- If it doesn't exist already, `mkdir ~/GitHub` then `cd ~/GitHub` and ... 
- `git clone https://github.com/ArduCAM/MIPI_Camera.git`  
- 
### test
```
SENSOR_ID=0 # 0 for CAM0 and 1 for CAM1 ports
FRAMERATE=60 # Framerate can go from 2 to 60 for 1920x1080 mode
NUMBER_OF_SNAPSHOTS=20
gst-launch-1.0 -e nvarguscamerasrc num-buffers=$NUMBER_OF_SNAPSHOTS sensor-id=$SENSOR_ID ! "video/x-raw(memory:NVMM),width=1920,height=1080,framerate=$FRAMERATE/1" ! nvjpegenc ! multifilesink location=%03d_rpi_v3_imx477_cam$SENSOR_ID.jpeg
```

## Gstreamer

GStreamer framework is a set of libraries that allow you to create and control multimedia applications.

<https://gitlab.freedesktop.org/gstreamer/gst-docs/-/tree/master>


### gst-launch

<https://gstreamer.freedesktop.org/documentation/application-development/appendix/programs.html?gi-language=c>

### rstp streamer

<https://stackoverflow.com/questions/13744560/using-gstreamer-to-serve-rtsp-stream-working-example-sought>

<https://stackoverflow.com/questions/13154983/gstreamer-rtp-stream-to-vlc>


### mp4 cap

SENSOR_ID=0 # 0 for CAM0 and 1 for CAM1 ports
FRAMERATE=60 # Framerate can go from 2 to 60 for 1920x1080 mode
gst-launch-1.0 -e nvarguscamerasrc sensor-id=$SENSOR_ID ! "video/x-raw(memory:NVMM),width=1920,height=1080,framerate=$FRAMERATE/1" ! nvv4l2h264enc ! h264parse ! mp4mux ! filesink location=rpi_v3_imx477_cam$SENSOR_ID.mp4

## Useful commands tl;dr

- Camera information

`v4l2-ctl --list-formats-ext -d /dev/video0`


## Sites
<https://www.arducam.com/product-category/nvidia-jetson-nano-nx-officially-supported-sensors/>

<https://www.arducam.com/product/arducam-for-jetson-imx477-hq-camera-board-12-3mp-camera-board-for-nvidia-jetson-nano-xavier-nx-raspberry-pi-compute-module-b0279/>

<https://github.com/ArduCAM/MIPI_Camera/releases>

```
wget https://github.com/ArduCAM/MIPI_Camera/releases/download/v0.0.3/install_full.sh
```

<https://www.arducam.com/docs/camera-for-jetson-nano/>

