#!/bin/sh

gst-launch-1.0 "videotestsrc ! ffenc_mpeg4 ! video/x-raw, width=1920, height=1080 ! videoconvert ! timeoverlay valignment=4 halignment=1 ! nvvidconv ! video/x-raw(memory:NVMM), width=1920, height=1080 ! tee name=t ! nvv4l2h265enc EnableTwopassCBR=1 insert-sps-pps=1 idrinterval=15 iframeinterval=1000 bitrate=64000000 vbv-size=1600000 maxperf-enable=1 preset-level=1 ! h265parse ! rtph265pay config-interval=1 pt=96 ! udpsink host=IP.address port=PORTsync=0 async=0 t. ! nvegltransform ! nveglglessink max-lateness=11000 sync=0"