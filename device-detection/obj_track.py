import numpy as np
import argparse
import time
import imutils
import cv2
import zhuocv as zc
import helper
from matplotlib import pyplot as plt
import datetime

IMG_SIZE = 600.0
BLUR_FACTOR = 3
MONITOR_RATIO = 1.456


def colorThreshMask(frame, lowVal, highVal):
    #convert to hsv and apply color threshold
    #returns a mask of the frame based on the low and high threshold values
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(hsv, lowVal, highVal)

    return blue

def warpFrame(frame, rect, mask):
    # Given a frame and a points of a rectangular contour, warp the rectangle to straighten
    # returns (warped image of the mask, warped image of the frame)

    #create a new mask for the warped image
    mask_small = np.zeros(frame.shape[:2], dtype=np.uint8)

    cv2.drawContours(mask_small, [rect], -1, 255, -1)

    ## WARP THE MONITOR
    pts = rect.reshape(4, 2)
    warp_rect = np.zeros((4, 2), dtype = "float32")
    s = pts.sum(axis=1)
    warp_rect[0] = pts[np.argmin(s)]
    warp_rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis = 1)
    warp_rect[1] = pts[np.argmin(diff)]
    warp_rect[3] = pts[np.argmax(diff)]

    # now that we have our rectangle of points, let's compute
    # the width of our new image
    (tl, tr, br, bl) = warp_rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))

    # ...and now for the height of our new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))

    # take the maximum of the width and height values to reach
    # our final dimensions
    maxWidth = max(int(widthA), int(widthB))
    maxHeight = max(int(heightA), int(heightB))

    # construct our destination points which will be used to
    # map the screen to a top-down, "birds eye" view
    dst = np.array([
    	[0, 0],
    	[maxWidth - 1, 0],
    	[maxWidth - 1, maxHeight - 1],
    	[0, maxHeight - 1]], dtype = "float32")

    # calculate the perspective transform matrix and warp
    # the perspective to grab the screen
    M = cv2.getPerspectiveTransform(warp_rect, dst)
    warp = cv2.warpPerspective(mask, M, (maxWidth, maxHeight))
    warp_frame = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))

    return (warp, warp_frame)

def detect_monitor(frame):
    # Takes in a frame
    # returns two booleans: (is the monitor present, is the monitor upright)
    MONITOR_PRESENT = False
    MID_BUTTON_PRESENT = False
    UPRIGHT = False
    SCREEN_PRESENT = False

    blueLower = np.array([110, 60, 30])
    blueUpper = np.array([130, 255, 255])
    # frame = cv2.imread(args["image"])
    frame = imutils.resize(frame, width = int(IMG_SIZE))
    blue = colorThreshMask(frame, blueLower, blueUpper)

    # ZHUOCV's implementation
    # DoB = zc.get_DoB(hsv, 8, 1, method = "Average")
    # mask_blue = zc.color_inrange(DoB, 'HSV', H_L = 0, H_U = 120, S_L = 50, S_U = 255, V_L = 40, V_U = 105)
    # mask_blue2 = zc.color_inrange(DoB, 'HSV', H_L = 0, H_U = 90, S_L = 0, S_U = 200, V_L = 40, V_U = 105)

    res = cv2.bitwise_and(frame,frame, mask = blue)
    blue = cv2.GaussianBlur(blue, (BLUR_FACTOR, BLUR_FACTOR), 0)
    (cnts, _) = cv2.findContours(blue.copy(),
    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(cnts) > 0:
        MONITOR_PRESENT = True
        cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[0]
        rect = np.int32(cv2.cv.BoxPoints(cv2.minAreaRect(cnt)))
        # rect = cnt

        (warp, warp_frame) = warpFrame(frame, rect, blue)

        # work with warp from here on ##
        # Check monitor orientation
        if (warp.shape[0] < warp.shape[1]):
            orientation = 'landscape'
        else:
            orientation = 'portrait'

        monitor_width = min(warp.shape[0], warp.shape[1])
        monitor_height = max(warp.shape[0], warp.shape[1])
        if orientation == 'portrait':
            monitor_mid_pos = (rect[1, 0] + monitor_width/2.0, 0)
        else:
            monitor_mid_pos = (0, rect[2, 1] + monitor_width/2.0)
        # print "width: %d; height: %d" % (monitor_width, monitor_height)

        ## GET CIRCULAR BUTTONS ON THE MONITOR
        # res2 = cv2.bitwise_and(blue, blue, mask = mask_small)
        (comp_cnts, _) = cv2.findContours(warp.copy(),
        cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # A list of circles that can be the middle button
        #[(center, radius), (center, radius), ...]
        possible_button = []
        for cnt_idx, cnt in enumerate(comp_cnts):
            approx = cv2.approxPolyDP(cnt,0.02*cv2.arcLength(cnt,True),True)

            if (len(approx) > 5) and (len(approx) < 12):
                (x,y),radius = cv2.minEnclosingCircle(cnt)
                center = (int(x),int(y))
                radius = int(radius)
                # print ("diameter: %d; 1/6 of monitor width: %d" % (radius * 2, monitor_width/6))

                # Button can't be too small
                if (radius * 2 >= monitor_width/6) and (radius * 2 < monitor_width/2):
                    possible_button.append((center, radius))
                # img = cv2.circle(warp_frame,center,radius,(0,255,0),2)

        # check if it's the middle button
        if len(possible_button) == 0:
            return "Error: no button found!"
        else:
            for button in possible_button:
                center = button[0]
                radius = button[1]

                delta = 8
                # if the circle is at the center of the monitor with the right size
                # it is the middle button
                if orientation == "portrait":
                    if monitor_width/2 - delta <= center[0] <= monitor_width/2 + delta:
                        if (center[1] > monitor_height/2):
                            UPRIGHT = True
                        img = cv2.circle(warp_frame,center,radius,(0,255,0),2)
                        MID_BUTTON_PRESENT = True
                if orientation == 'landscape':
                    if ((monitor_width/2 - delta) <= center[1]
                        <= (monitor_width/2 + delta)):
                        img =  cv2.circle(warp_frame,center,radius,(0,255,0),2)
                        MID_BUTTON_PRESENT = True
            # cv2.imshow("warp_frame", warp_frame)
    else:
        return "Warning: No contour detected in view"

    if (MID_BUTTON_PRESENT and MONITOR_PRESENT):
        # double check if the monitor is present by checking if there's a screen on the monitor
        SCREEN_PRESENT = detect_screen_check(warp_frame)
        if (SCREEN_PRESENT):
            # print("{:%Y-%b-%d %H:%M:%S}: detect monitor at orientation: {}".format(datetime.datetime.now(),orientation))
            cv2.drawContours(frame, [rect], -1, 255, 2)
        else: 
            return "Warning: No screen detected on the monitor. Monitor might not be present"
        cv2.imshow("warp", warp_frame)

    # print((MID_BUTTON_PRESENT and MONITOR_PRESENT and SCREEN_PRESENT))
    return ((MID_BUTTON_PRESENT and MONITOR_PRESENT and SCREEN_PRESENT), UPRIGHT)
    # print ("button: {}; monitor: {}; screen: {}".format(MID_BUTTON_PRESENT, MONITOR_PRESENT, SCREEN_PRESENT))
    # cv2.imshow("mask", blue)
    # cv2.imshow("frame", frame)
    # cv2.imwrite(args["image"] + "mask.jpg", blue)
    # cv2.imwrite(args["image"] + "small_mask.jpg", warp)
    # cv2.imwrite(args["image"] + "detect.jpg", warp_frame)

def detect_screen_check(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    size = frame.shape[0] * frame.shape[1]

    edges = cv2.Canny(gray, 90, 180)
    kernel = np.ones((3,3),np.uint8)
    edges = cv2.dilate(edges,kernel,iterations = 1)
    # opening = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)

    # cv2.imshow("edges", edges)

    (cnts, _) = cv2.findContours(edges.copy(),
    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(cnts) > 0:
        cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[0]
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)

        if (3 <= len(approx) <= 10 and (size/3*2 < cv2.contourArea(cnt))):
            cv2.drawContours(frame, [cnt], -1, 255, 2)
            return True
        # print(len(approx))
    return False
    
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required = False, help = "Path to the image")
    args = vars(ap.parse_args())
    frame = cv2.imread(args["image"])

    if not args.get("image", False):
        camera = cv2.VideoCapture(0)

    while True:
        (grabbed, frame) = camera.read()

        if not grabbed:
            break
        detect_monitor(frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    # cv2.waitKey(0)

    camera.release()
    cv2.destroyAllWindows()
