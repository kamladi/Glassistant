import numpy as np
import argparse
import time
import imutils
import cv2
import zhuocv as zc
import helper

# ap = argparse.ArgumentParser()
# ap.add_argument("-v", "--video",
# help = "path to the (optional) video file")
# args = vars(ap.parse_args())

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = False, help = "Path to the image")
args = vars(ap.parse_args())


blueLower = np.array([110, 60, 30])
blueUpper = np.array([130, 255, 255])

if not args.get("image", False):
    camera = cv2.VideoCapture(0)

while True:
    (grabbed, frame) = camera.read()

    if not grabbed:
        break

    # frame = cv2.imread(args["image"])

    IMG_SIZE = 600.0
    BLUR_FACTOR = 3
    RESIZE_RATIO = frame.shape[0]/IMG_SIZE
    MONITOR_RATIO = 1.456
    MONITOR_PRESENT = False
    MID_BUTTON_PRESENT = False

    frame = imutils.resize(frame, width = int(IMG_SIZE))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    blue = cv2.inRange(hsv, blueLower, blueUpper)

    # DoB = zc.get_DoB(hsv, 8, 1, method = "Average")
    # mask_blue = zc.color_inrange(DoB, 'HSV', H_L = 0, H_U = 120, S_L = 50, S_U = 255, V_L = 40, V_U = 105)
    # mask_blue2 = zc.color_inrange(DoB, 'HSV', H_L = 0, H_U = 90, S_L = 0, S_U = 200, V_L = 40, V_U = 105)
    res = cv2.bitwise_and(frame,frame, mask = blue)

    blue = cv2.GaussianBlur(blue, (BLUR_FACTOR, BLUR_FACTOR), 0)

    (_, cnts, _) = cv2.findContours(blue.copy(),
    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    mask_small = np.zeros(frame.shape[:2], dtype=np.uint8)

    if len(cnts) > 0:
        cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[0]
        rect = np.int32(cv2.boxPoints(cv2.minAreaRect(cnt)))

        cv2.drawContours(mask_small, [rect], -1, 255, -1)
        MONITOR_PRESENT = True

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
        warp = cv2.warpPerspective(blue, M, (maxWidth, maxHeight))
        warp_frame = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))

        ## work with warp from here on ##
        ## Check monitor orientation
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
        # print orientation
        # print monitor_mid_pos

        ## GET CIRCULAR BUTTONS ON THE MONITOR
        # res2 = cv2.bitwise_and(blue, blue, mask = mask_small)
        (_, comp_cnts, _) = cv2.findContours(warp.copy(),
        cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # A list of circles that can be the middle button
        #[(center, radius), (center, radius), ...]
        possible_button = []
        for cnt_idx, cnt in enumerate(comp_cnts):
            # print(cnt)
            approx = cv2.approxPolyDP(cnt,0.02*cv2.arcLength(cnt,True),True)

            if (len(approx) > 5) and (len(approx) < 12):
                (x,y),radius = cv2.minEnclosingCircle(cnt)
                center = (int(x),int(y))
                radius = int(radius)
                # print ("diameter: %d; 1/6 of monitor width: %d" % (radius * 2, monitor_width/6))
                # Button can't be too small
                if (radius * 2 >= monitor_width/6) and (radius * 2 < monitor_width):
                    possible_button.append((center, radius))
                # img = cv2.circle(warp_frame,center,radius,(0,255,0),2)

        ## check if it's the middle button
        if len(possible_button) == 0:
            print "Error: no button found!"
        else:
            for button in possible_button:
                # print button
                center = button[0]
                radius = button[1]
                # img = cv2.circle(warp_frame,center,radius,(0,255,0),2)

                delta = 8
                if orientation == "portrait":
                    if monitor_width/2 - delta <= center[0] <= monitor_width/2 + delta:
                        # print ("button x: %d; monitor mid: %d; range: (%d, %d)" %
                        #         (center[0], monitor_mid_pos[0], monitor_mid_pos[0] - delta, monitor_mid_pos[0] + delta))
                        img = cv2.circle(warp_frame,center,radius,(0,255,0),2)
                        MID_BUTTON_PRESENT = True
                if orientation == 'landscape':
                    if ((monitor_width/2 - delta) <= center[1] <= (monitor_width/2 + delta)):
                        # print (monitor_width/2, center[1])
                        img =  cv2.circle(warp_frame,center,radius,(0,255,0),2)
                        MID_BUTTON_PRESENT = True

            # cv2.imshow("warp_frame", warp_frame)
    if (MID_BUTTON_PRESENT and MONITOR_PRESENT):
        print("detect monitor at orientation: %s" % orientation)
        cv2.drawContours(frame, [rect], -1, 255, 2)
    # cv2.imshow("res", DoB)
    # cv2.imshow("mask", blue)
    # cv2.imshow("mask2", res2)
    # cv2.imshow("warp", warp)
    cv2.imshow("frame" , frame)

# cv2.imwrite(args["image"] + "mask.jpg", blue)
# cv2.imwrite(args["image"] + "small_mask.jpg", warp)
# cv2.imwrite(args["image"] + "detect.jpg", warp_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
# cv2.waitKey(0)


camera.release()
cv2.destroyAllWindows()
