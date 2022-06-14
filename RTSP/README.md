# RTSP

Grabbed from 

<https://forums.developer.nvidia.com/t/jetson-nano-faq/82953>

## To build -

1. Download `test-launch.c` from: <https://github.com/GStreamer/gst-rtsp-server/blob/1.14.5/examples/test-launch.c>
    
    NB this is an older version from the RSTP repo. The current version fails to build correctly due to some header thing. I'll investigate this later.
1. Build `test-launch` with
```
sudo apt-get install libgstrtspserver-1.0 libgstreamer1.0-dev
gcc test-launch.c -o test-launch $(pkg-config --cflags --libs gstreamer-1.0 gstreamer-rtsp-server-1.0)
```

1. Run `test-launch` with
```
$ ./test-launch "videotestsrc ! nvvidconv ! nvv4l2h264enc ! h264parse ! rtph264pay name=pay0 pt=96"
```

1. Connect to `rtsp://<SERVER_IP_ADDRESS>:8554/test` from VLC


## RTP/AVP

`.sdp` file from 
<https://stackoverflow.com/questions/13154983/gstreamer-rtp-stream-to-vlc>

## sh files

That is an insanely long command.