# RTSP

Grabbed from 

<https://forums.developer.nvidia.com/t/jetson-nano-faq/82953>

## To build:

1. Download `test-launch.c` from: <https://github.com/GStreamer/gst-rtsp-server/blob/1.14.5/examples/test-launch.c>
    
    NB this is an older version from the RSTP repo. The current version fails to build correctly due to some header thing. I'll investigate this later.
2. Build `test-launch` with
```
sudo apt-get install libgstrtspserver-1.0 libgstreamer1.0-dev
gcc test-launch.c -o test-launch $(pkg-config --cflags --libs gstreamer-1.0 gstreamer-rtsp-server-1.0)
```

3. Run `test-launch` with
```
./test-launch "nvarguscamerasrc sensor-id=0  ! video/x-raw(memory:NVMM),width=1920,height=1080,framerate=60/1 ! nvvidconv ! nvv4l2h264enc ! h264parse ! rtph264pay name=pay0 pt=96"
```

4. Connect to `rtsp://<SERVER_IP_ADDRESS>:8554/test` from VLC

## Useful Commands

`gst-inspect-1.0` - lists all plugin modules

`gst-inspect-1.0 any_plugin` - gives source and sink for `any_plugin`

## NOTES:

### The `gst` accleration guide is here

<https://developer.nvidia.com/embedded/dlc/l4t-accelerated-gstreamer-guide-32-1>

describes the gazillion streamer pipeline things.

### Another Approach

<https://forums.developer.nvidia.com/t/how-to-stream-csi-camera-using-rtsp/161046/5>

but with some thoughts here:

<https://forums.developer.nvidia.com/t/change-video-settings-on-rtsp-streaming/200307>

and UDP 

<https://forums.developer.nvidia.com/t/gstreamer-tcpserversink-2-3-seconds-latency/183388/5>
### tests maybe?

```
./test-launch nvarguscamerasrc sensor-id=0  ! "video/x-raw(memory:NVMM),width=1920,height=1080,framerate=60/1" ! nvv4l2h264enc ! h264parse ! rtph264pay name=pay0 pt=96
```


```
./test-launch "nvarguscamerasrc sensor-id=0  ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=60/1' ! nvvidconv ! nvv4l2h264enc ! h264parse ! rtph264pay name=pay0 pt=96" 
stream ready at rtsp://127.0.0.1:8554/test

(test-launch:24522): GStreamer-CRITICAL **: 13:53:02.776: gst_element_make_from_uri: assertion 'gst_uri_is_valid (uri)' failed
Opening in BLOCKING MODE 

(test-launch:24522): GStreamer-CRITICAL **: 13:53:22.794: gst_element_make_from_uri: assertion 'gst_uri_is_valid (uri)' failed
Opening in BLOCKING MODE 
```
### RTP/AVP

`.sdp` file from 
<https://stackoverflow.com/questions/13154983/gstreamer-rtp-stream-to-vlc>

### Nvidia video streaming

specific code under video directory
https://github.com/dusty-nv/jetson-utils
Used in/with jetson-inference repo

### RTSP w/ Gstreamer in python with OpenCV

This is older but seems to use an idea similar to what is in test-launch.c
https://github.com/prabhakar-sivanesan/OpenCV-rtsp-server/blob/master/stream.py

