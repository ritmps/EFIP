import cv2
import imutils  
import numpy as np  
cap = cv2.VideoCapture(0) # getting video from webcam
while cap.isOpened():
    ret, img = cap.read()

    cv2.imshow("Frame",img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('p'):
        cv2.imwrite("frame.jpg", img)
        print("frame captured")
        cv2.waitKey(-1) #wait until any key is pressed
cap.release()
cv2.destroyAllWindows()
image_hsv = None   # global
pixel = (20,60,80) # some stupid default
# mouse callback function
def pick_color(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = image_hsv[y,x]

        #you might want to adjust the ranges(+-10, etc):
        upper =  np.array([pixel[0] + 20, pixel[1] + 20, pixel[2] + 50])
        lower =  np.array([pixel[0] - 20, pixel[1] - 20, pixel[2] - 50])
        print(pixel, lower, upper)

        image_mask = cv2.inRange(image_hsv,lower,upper)
        cv2.imshow("mask",image_mask)
        cv2.waitKey(0)

def main():
    import sys
    global image_hsv, pixel # so we can use it in mouse callback
    image_src = cv2.imread("/Users/nickduggan/frame.jpg")  # pick.py my.png
    image_src = imutils.resize(image_src, height=800)
    if image_src is None:
        print ("the image read is None............")
        return
    cv2.imshow("bgr",image_src)

    ## NEW ##
    cv2.namedWindow('hsv')
    cv2.setMouseCallback('hsv', pick_color)

    # now click into the hsv img , and look at values:
    image_hsv = cv2.cvtColor(image_src,cv2.COLOR_BGR2HSV)
    cv2.imshow("hsv",image_hsv)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cap = cv2.VideoCapture(0)
    while True:
        ret,frame = cap.read()


        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        upper =  np.array([pixel[0] + 20, pixel[1] + 20, pixel[2] + 50])
        lower =  np.array([pixel[0] - 20, pixel[1] - 20, pixel[2] - 50])
    

        image_mask = cv2.inRange(frame,lower,upper)
        cv2.imshow("mask",image_mask)
        #result = cv2.bitwise_and(frame, frame, mask=mask)

        #cv2.imshow("video", frame)
        #cv2.imshow("mask", result)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
cap.release()


main()
