import cv2
import numpy as np
from matplotlib import pyplot as plt

# Define camera matrix K
intrinsic = np.array([[584.053567693393, 0.0, 491.107498914361],
              [0.0, 586.778383380614, 254.236382017895],
              [0.0, 0.0, 1.0]])

# Define distortion coefficients d
distort = np.array([-0.318443099339647,  0.0945554774567145,  0.0, 0.0])

# Read an example image and acquire its size
img = cv2.imread('Images/3.5frame1.jpg')
h, w = img.shape[:2]

# Generate new camera matrix from parameters
newcameramatrix, roi = cv2.getOptimalNewCameraMatrix(intrinsic, distort, (w,h), 0)

# Generate look-up tables for remapping the camera image
mapx, mapy = cv2.initUndistortRectifyMap(intrinsic, distort, None, newcameramatrix, (w, h), 5)

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
