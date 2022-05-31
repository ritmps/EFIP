### EFIP
Tracking code for the extended freshman imaging project 

### Install
> Clone and open EFIP library.
```
git clone --recursive https://github.com/ramancini04/EFIP.git
cd EFIP
```

### Setup
> Install the required packages.
```
pip install -r requirements.txt
```

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

