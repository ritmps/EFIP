# EFIP
## **For information about our project and more in depth info on each file in this repository, visit our repo's wiki!**

Tracking code for the extended freshman imaging project.

---

## Docker Container
### Running a Container
```
sudo docker run -it --rm --net=host --runtime nvidia -e DISPLAY= -v /tmp/.X11-unix/:/tmp/.X11-unix nvcr.io/nvidia/l4t-base:r34.1.1
```

---

## Download Repository
> Clone and open EFIP library.
```
git clone --recursive https://github.com/ramancini04/EFIP.git
cd EFIP
```

## Setup
> Install the required packages.
```
pip install -r requirements.txt
```

---

## RTP
### IMPORTANT WARNING:
Under <ins>**NO CIRCUMSTANCES**</ins> should you <ins>**EVER**</ins> share your personal IP address with any untrusted sources online. We do not store personal IP information in any code within this repository and IP information should <ins>**NEVER**</ins> be stored here if you have the intent of forking and/or pushing this repo to GitHub.
> *Your IP address is essential for sending and receiving information online. But, if a hacker knows your IP address, they can use it to seize very valuable information, including your location and online identity. Using this information as a starting point, they could potentially hack your device, steal your identity, and more.*

Source: https://nordvpn.com/blog/what-can-someone-do-with-your-ip-address/

### GStreamer
Make sure that GStreamer is installed on both the host computer and the NVidia Jetson Nano. Installation steps can be found at the websites below:
- [MacOS]()
- [Linux]()
- [Windows]()

### Running RTP on NVidia Jetson Nano
To start the RTP stream, run the following commands:
```
cd ./EFIP/RTSP/
```
```
python3 rtp-stream.py -i "0.0.0.0" -p "5004"
```
*Make sure to replace 0.0.0.0 with your host computer's IP address. A guide on how to find your host computer's IP address can be found in the section labeled [Finding Your Computer's IP Address](https://github.com/ritmps/EFIP#finding-your-computers-ip-address)*

### Viewing an RTP stream on the host computer
To view the RTP stream that you just started on the NVidia Jetson Nano, run the following command in a terminal:
```
gst-launch-1.0 -v udpsrc port=5004 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! decodebin ! videoconvert ! autovideosink
```

---

## Finding Your Computer's IP Address
### Finding IP over SSH
The easiest way to find your host computer's IP address in relation to this guide is if you are connected to your NVidia Jetson Nano over SSH. If you are SSH'd into your NVidia Jetson Nano, you can run the following command in the terminal to return your host computer's IP address:
```
echo $SSH_CLIENT | awk '{ print $1}'
```

### Linux
Your IP address can be found by running the following command in a terminal and looking under the section labeled with the type of connection you are using.
```
ifconfig
```

### MacOS
Your IP address can be found by 

### Windows
Your IP address can be found by taking the follwing steps:
1. Click the Windows "Start" button in the taskbar on your screen
2. Click on "Settings"
3. Click on "Network & Internet"
4. Go to the "Wi-Fi" tab
5. Click on the wireless network which you are currently connected to
6. Scroll down to the "Properties" section
7. Your IPv4 address should be listed next to "IPv4 address:"

---

## Description of Files
### color_picker.py
- Press "p" to pause the frame. Press "p" to start it again. Press "q" to quit the stream.
- On the hsv window, click the center of the object you want to track. 
- Press "q"(sometimes you have to hit it twice) to quit
- The code will output 3 arrays with 3 values each. 
- The second array is the lower hsv values, the third array is the upper hsv values

### ball_tracking_final.py
- edit the ball_tracking_final.py to include the lower and upper values from the color_picker.py output arrays
- place those values in green_lower and green_upper
- output includes x and y values

