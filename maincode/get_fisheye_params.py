from tkinter.tix import DirList
import numpy as np
import cv2
import pandas as pd
import argparse
import os
import tqdm
import glob

verbose = True

# PARSE ARGUMENTS
def parse_args():
    global directory, checkerboardDim, args

    parser = argparse.ArgumentParser(description='Find fisheye parameters of a camera from a set of images.')
    parser.add_argument('-d', '--directory', default="Images", help="Directory to save images\n(Default: Images)")
    parser.add_argument('-w', '--checkerboard_width', type=int, default=8, help="Checkerboard width\n(Default: 8)")
    parser.add_argument('-H', '--checkerboard_height', type=int, default=6, help="Checkerboard height\n(Default: 6)")
    parser.add_argument('-s', metavar='win', type=int, help='Search window width around checkerboard verted used in refinement, default is 0 (disable refinement)')
    args = parser.parse_args()
    directory = args.directory
    # Subtract one from the width and height to account for the fact that opencv uses the number of interior vertices
    checkerboard_width = args.checkerboard_width - 1
    checkerboard_height = args.checkerboard_height - 1
    # Store the dimensions of the checkerboard in a numpy array
    checkerboardDim = np.array([checkerboard_width, checkerboard_height])
    if verbose:
        print(f'[INFO] Checkerboard dimensions: {checkerboardDim}')


# LOAD IN ALL IMAGES AND DETECT CHECKERBOARD. OUTPUT CHECKERBOARD 2D AND 3D CORNERS
def load_images_from_directory():
    global imgWidth, imgHeight, directory

    images = []
    corners2D = []
    skipped_image_numbers = []

    # i = number of iterations of the for loop
    i = 1

    # Get a list of images in the directory (output as 'image_name.png')
    images = [os.path.basename(x) for x in glob.glob(f'{directory}/*.png')]
    
    if verbose:
        print(f'[INFO] Found {len(images)} images in {directory}')
        print(f'[INFO] images:\n{images}')
    
    # Define size of the loading bar
    if args.s != None and args.s >= 2:
        bar_size = (len(os.listdir(directory)) * (4 + 1))
    else:
        bar_size = (len(os.listdir(directory)) * 4)

    with tqdm.tqdm(desc='Getting Calibration Matrix', ncols=100, total=bar_size) as calibrating:
        for filename in images:
            if verbose:
                calibrating.write(f'[INFO] Current image filename: {os.path.join(directory, filename)}')

            # Load image
            img = cv2.imread(os.path.join(directory, filename))
            # Update loading bar after operation is complete
            calibrating.update(1)

            # Record the image width and height of the first image
            if i == 1:
                imgWidth, imgHeight = img.shape[1], img.shape[0]
                if verbose:
                    calibrating.write(f'[INFO] Image size: {imgWidth}x{imgHeight}')
            
            # If images are not the same size, stop the program
            elif img.shape[1] != imgWidth or img.shape[0] != imgHeight:
                exit(f'[ERROR] Image {i} has a different size than image 1. All images must be the same size. Exiting...')
            
            # Read only images and not other file types
            if img is not None:
                if verbose:
                    calibrating.write(f'[INFO] Finding checkerboard corners in image number {i}')
                # Find the checkerboard pattern on the image, saving the 2D coordinates of checkerboard vertices in cbVertices. Vertex is the point where 4 squares (2 white and 2 black) meet.
                found, corners = cv2.findChessboardCorners(img, tuple(checkerboardDim), flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
                # Update loading bar after operation is complete
                calibrating.update(1)

                if found:
                    if verbose:
                        calibrating.write(f'[INFO] Found checkerboard corners in image number {i}')
                    # Needs to perform further corner refinement?
                    if args.s != None and args.s >= 2:
                        if verbose:
                            calibrating.write(f'[INFO] Refining checkerboard corners in image number {i}')
                        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.0001)
                        imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                        corners = cv2.cornerSubPix(imgGray, corners, (args.s//2, args.s//2), (-1,-1), criteria)
                        # Update loading bar after operation is complete
                        calibrating.update(1)
                    corners2D.append(corners)
                    # Update loading bar after operation is complete
                    calibrating.update(1)
                    i += 1
                
                # If the checkerboard pattern is not found, skip the image
                elif i <= len(images):
                    calibrating.write(f'\n[WARN] Checkerboard pattern not found in image number {i}, skipping...')
                    skipped_image_numbers.append(i)
                    if args.s != None and args.s >= 2:
                        # If refinement is enabled, update the loading bar to reflect the skipped image
                        calibrating.update(1)
                    # Update loading bar after operation is complete
                    calibrating.update(1)
                    i += 1
                    continue
                
                if verbose and i == len(images):
                    calibrating.write(f'\n[WARN] Checkerboard pattern not found in images: {skipped_image_numbers}')
                    i += 1
            
            calibrating.update(1)
    # Create the vector that stores 3D coordinates for each checkerboard pattern on a space
    # where X and Y are orthogonal and run along the checkerboard sides, and Z==0 in all points on
    # checkerboard.
    cbCorners = np.zeros((1, checkerboardDim[0] * checkerboardDim[1], 3))
    cbCorners[0,:,:2] = np.mgrid[0:checkerboardDim[0], 0:checkerboardDim[1]].T.reshape(-1,2)
    corners3D = [cbCorners.reshape(-1,1,3) for i in range(len(corners2D))]

    return corners2D, corners3D


# FIND FISHEYE PARAMETERS
def find_calibration_matrix(corners2D, corners3D):
    global checkerboardDim, args

     # Calculate fisheye lens calibration parameters
    camMatrix = np.eye(3)
    coeffs = np.zeros((4,))
    rms, camMatrix, coeffs, rvecs, tvecs = cv2.fisheye.calibrate(corners3D, corners2D, (imgWidth, imgHeight), camMatrix, coeffs, flags=cv2.fisheye.CALIB_FIX_SKEW)
    
    # Print out calibration results
    if verbose:
        print(f'\n==================================================\n' \
            f'Rms error: \n{rms}\n' \
            f'\n' \
            f'Fisheye coefficients: \n{coeffs}\n' \
            f'\n' \
            f'Camera matrix: \n{camMatrix}\n' \
            f'==================================================\n')
    
    return camMatrix, coeffs


# SAVE LOOKUP TABLES TO CSV FILE
def generate_lut(camMatrix, distortion):
    global imgWidth, imgHeight, checkerboardDim, verbose

    # Generate look-up tables for remapping the camera image
    mapx, mapy = cv2.fisheye.initUndistortRectifyMap(camMatrix, distortion, None, camMatrix, (imgWidth, imgHeight), cv2.CV_32FC1)
    if verbose:
        print(f'[INFO] Shape of mapx: {mapx.shape}\n' \
            f'[INFO] Shape of mapy: {mapy.shape}')

    # Save the look-up tables to a csv file
    out_arr = np.concatenate((mapx, mapy), axis=0)
    if verbose:
        print(f'[INFO] Shape of output array: {out_arr.shape}')
    out_df = pd.DataFrame(out_arr)
    print(f'[INFO] Saving lookup table to remap_lut.csv...')
    out_df.to_csv('remap_lut.csv', index=False, header=False)

if __name__ == '__main__':
    parse_args()
    corners2D, corners3D = load_images_from_directory()
    intrinsicMatrix, distortionCoeffs = find_calibration_matrix(corners2D, corners3D)
    generate_lut(intrinsicMatrix, distortionCoeffs)