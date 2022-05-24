import cv2
import numpy as np
from matplotlib import pyplot as plt

# Define camera matrix K
K = np.array([[992.46197947,   0.0,         493.33704126],
 [  0.0,         993.3449798,  241.17160184],
 [  0.0,           0.0,           1.0        ]])

# Define distortion coefficients d
d = np.array([-0.20136948,  0.33106627,  0.0008198,  -0.00110601, -0.51758667])

# Read an example image and acquire its size
img = cv2.imread('/Users/nickduggan/Desktop/IMAGING/foos.jpg')
h, w = img.shape[:2]

# Generate new camera matrix from parameters
newcameramatrix, roi = cv2.getOptimalNewCameraMatrix(K, d, (w,h), 0)

# Generate look-up tables for remapping the camera image
mapx, mapy = cv2.initUndistortRectifyMap(K, d, None, newcameramatrix, (w, h), 5)

# Remap the original image to a new image
newimg = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)

# Display old and new image
fig, (oldimg_ax, newimg_ax) = plt.subplots(1, 2)
oldimg_ax.imshow(img)
oldimg_ax.set_title('Original image')
newimg_ax.imshow(newimg)
newimg_ax.set_title('Unwarped image')
plt.show()

# moo
