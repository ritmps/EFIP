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
