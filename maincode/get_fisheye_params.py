import math
import numpy as np
import cv2
import pandas as pd
import vpi
import argparse
import os
import csv
import tqdm

verbose = False

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

def load_images_from_directory():
    global images, imgWidth, imgHeight, directory

    images = []

    # i = number of iterations of the for loop
    i = 1

    with tqdm.tqdm(desc='Loading images', ncols=100, total=len(os.listdir(directory))) as loading_images:
        for filename in os.listdir(directory):
            img = cv2.imread(os.path.join(directory, filename))

            if i == 1:
                imgWidth, imgHeight = img.shape[1], img.shape[0]
                if verbose:
                    print(f'[INFO] Image size: {imgWidth}x{imgHeight}')
            elif img.shape[1] != imgWidth or img.shape[0] != imgHeight:
                exit(f'[ERROR] Image {i} has a different size than image 1. All images must be the same size. Exiting...')
            
            # Read only images and not other file types
            if img is not None:
                images.append(img)
                i += 1
            
            loading_images.update(1)
        
    return images

def find_calibration_matrix(images):
    global checkerboardDim, args

    if verbose:
        print(f'[INFO] Number of images: {len(images)}')

    # Find the checkerboard corners in each image
    i = 1
    corners2D = []
    skipped_image_numbers = []

    with tqdm.tqdm(desc='Finding checkerboard corners', ncols=100, total=len(images)) as finding_corners:
        for img in images:
            if verbose:
                print(f'[INFO] Finding checkerboard corners in image number {i}')
            # Find the checkerboard pattern on the image, saving the 2D coordinates of checkerboard vertices in cbVertices. Vertex is the point where 4 squares (2 white and 2 black) meet.
            found, corners = cv2.findChessboardCorners(img, tuple(checkerboardDim), flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
            if found:
                if verbose:
                    print(f'[INFO] Found checkerboard corners in image number {i}')
                # Needs to perform further corner refinement?
                if args.s != None and args.s >= 2:
                    if verbose:
                        print(f'[INFO] Refining checkerboard corners in image number {i}')
                    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.0001)
                    imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                    corners = cv2.cornerSubPix(imgGray, corners, (args.s//2, args.s//2), (-1,-1), criteria)
                corners2D.append(corners)
                i += 1
            elif i <= len(images):
                print(f'\n[WARN] Checkerboard pattern not found in image number {i}, skipping...')
                skipped_image_numbers.append(i)
                i += 1
                continue
            
            if verbose and i == len(images):
                print(f'\n[WARN] Checkerboard pattern not found in images: {skipped_image_numbers}')
        
            finding_corners.update(1)
  
    # Create the vector that stores 3D coordinates for each checkerboard pattern on a space
    # where X and Y are orthogonal and run along the checkerboard sides, and Z==0 in all points on
    # checkerboard.
    cbCorners = np.zeros((1, checkerboardDim[0] * checkerboardDim[1], 3))
    cbCorners[0,:,:2] = np.mgrid[0:checkerboardDim[0], 0:checkerboardDim[1]].T.reshape(-1,2)
    corners3D = [cbCorners.reshape(-1,1,3) for i in range(len(corners2D))]

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

def generate_lut(camMatrix, distortion):
    global imgWidth, imgHeight, checkerboardDim, verbose

    # Generate look-up tables for remapping the camera image
    mapx, mapy = cv2.fisheye.initUndistortRectifyMap(camMatrix, distortion, None, camMatrix, (imgWidth, imgHeight), cv2.CV_32FC1)
    
    # Combine mapx and mapy into a single map
    remap_lut = np.zeros((imgHeight, imgWidth, 2), dtype=np.float32)
    for x in tqdm.tqdm(range(0, imgWidth), ncols=100, desc='Generating remap look-up table'):
        for y in range(imgHeight):
            # if verbose:
            #     print(f'[INFO] ROW: {x}\n' \
            #           f'       COLUMN: {y}\n' \
            #           f'       COORD: ({round(mapx[y, x])}, {round(mapy[y, x])})\n')
            remap_lut[y, x, 0] = mapx[y, x]
            remap_lut[y, x, 1] = mapy[y, x]
    
    x, y, z = remap_lut.shape
    out_arr = np.column_stack((np.repeat(np.arange(x), y), remap_lut.reshape(x * y, -1)))
    out_df = pd.DataFrame(out_arr, columns=['col', 'x', 'y'])
    print(f'[INFO] Saving lookup table to remap_lut.csv...')
    out_df.to_csv('remap_lut.csv', index=False, header=False)

    # Create a look-up table for remapping the camera image
    # with open('lut.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     for x in range(mapx.shape[1]):
    #         print(f'[INFO] {x}')
    #         writer.writerow(mapx[:,x])
    # print(f'[INFO] mapx[0,0]: {mapx[0,0]}')
    # print(f'[INFO] mapy[0,0]: {mapy[0,0]}')

if __name__ == '__main__':
    parse_args()
    images = load_images_from_directory()
    intrinsicMatrix, distortionCoeffs = find_calibration_matrix(images)
    generate_lut(intrinsicMatrix, distortionCoeffs)