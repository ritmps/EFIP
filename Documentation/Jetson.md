# Jetson

Jetson setup notes.

## Crucial docs

<https://developer.nvidia.com/embedded/learn/jetson-nano-2gb-devkit-user-guide>

## SDK manager

NVIDIA SDK Manager is a tool that allows you to install the NVIDIA drivers and CUDA toolkit in a customized fashion. It is well documented here:

<https://developer.nvidia.com/nvidia-sdk-manager>

### Pros and cons

* Pros
    * Configurable, easy to use.
* Cons
    * Not as easy to use as the Disk Image.
    * Needs a Docker container on non-Linux systems.
    * Docker doesn't allow USB devices to be mounted on macOS.
        <https://github.com/moby/hyperkit/issues/149>

@FP did explore it on macOS and Linux. It works fine. But, for simpler setups, I recommend using the Disk Image.

### Docker steps

- Install Docker :)
- DL SDK Manager container from <https://developer.nvidia.com/nvidia-sdk-manager>
    I used the 18.04 image.
- Install container via `docker load -i ./sdkmanager-1.8.0.10363-Ubuntu_18.04_docker.tar.gz`
- Tag it `docker tag sdkmanager:1.8.0.10363-Ubuntu_18.04 sdkmanager:latest`
- Run it `docker run -it --rm sdkmanager --help`
- See <https://docs.nvidia.com/sdk-manager/docker-containers/index.html>

### Links and notes

<https://docs.nvidia.com/sdk-manager/docker-containers/index.html>


## Disk Image

From here, you can set up headless or with a GUI. For the 2GB Jetson, headless is highly recommended. X11 rendering is slow and painful. I'd recommend using VSCode.

Follow these main instructions for setting up - <https://developer.nvidia.com/embedded/learn/jetson-nano-2gb-devkit-user-guide#id-.JetsonNano2GBDeveloperKitUserGuidevbatuu_v1.0-SetupviaSDCardImage(Recommended)>

Basically, the steps are:

* Download the image.
* Burn image onto new SD card (64GB at least) using Etcher or other burner.
* Insert SD card into Jetson Nano.
* Connect micro USB cable to Jetson Nano and host USB.
* Connect hard wire Ethernet for setup to Jetson Nano.
* If necessary, do factory reset on Nano (see below).
* On macOS / Linux, use `screen` to connect to terminal over usb port.
    * Mac example: `sudo screen /dev/cu.usbmodem14247200216373 115200 -L`
    * **NOTE** the password prompt that shows up is for the **CLIENT USER** for the `sudo`. It has _nothing_ to do with the Jetson.
* Hit `space` a few times and follow the setup instructions. In the beginning, you can set up via the hardwired ethernet. 
* After the machine reboots, you might want to also do an `sudo apt update && sudo apt upgrade` to get the latest packages.
* [#TODO] - how to set up `ssh` keys, `ssh-copy-id`, and VSCode remote host.

## SSH setup

[#TODO]

## Jumper / recovery mode

<https://dev.to/asacasa/howto-recovery-mode-for-nvidia-jetson-nano-developer-kit-ceo>

Jumper the GND and FC-REC pin on the jumpers _under_ the Nano card.

## Headless WiFi

<https://desertbot.io/blog/jetson-nano-headless-wifi-setup>

but

```
sudo nmcli dev wifi rescan # to scan 
sudo nmcli dev wifi # to show wifi hotspots
sudo nmcli device wifi connect SSID password PASSWORD #  to connect
```




