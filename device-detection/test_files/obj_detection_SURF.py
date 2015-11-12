import cv2
import numpy as np
from matplotlib import pyplot as plt
import imutils

surf = cv2.xfeatures2d.SURF_create(500)
MIN_MATCH_COUNT = 10

monitor = cv2.imread('bp_monitor.jpg')
# test = cv2.imread('test_img.jpg')
gray = cv2.cvtColor(monitor, cv2.COLOR_BGR2GRAY)
gray = imutils.resize(gray, width = 500)
kp1, des1 = surf.detectAndCompute(gray, None)

camera = cv2.VideoCapture(0)

while True:
    (grabbed, frame) = camera.read()

    if not grabbed:
        break

    test_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    test_gray = imutils.resize(test_gray, width = 500)
    kp2, des2 = surf.detectAndCompute(test_gray, None)

    if (des2 != None):
        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks=50)   # or pass empty dictionary

        flann = cv2.FlannBasedMatcher(index_params,search_params)
        matches = flann.knnMatch(des1,des2,k=2)

        good = []
        for m,n in matches:
            if m.distance < 0.7*n.distance:
                good.append(m)

        if len(good)>MIN_MATCH_COUNT:
            src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
            dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if (mask != None):
                matchesMask = mask.ravel().tolist()

            h,w = gray.shape
            pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
            if (M != None):
                dst = cv2.perspectiveTransform(pts,M)
                test_gray = cv2.polylines(test_gray,[np.int32(dst)],True,100,3, cv2.LINE_AA)
        else:
            print "Not enough matches are found - %d/%d" % (len(good),MIN_MATCH_COUNT)
            matchesMask = None

        draw_params = dict(matchColor = (0,255,0), # draw matches in green color
                           singlePointColor = None,
                           matchesMask = matchesMask, # draw only inliers
                           flags = 2)

        img3 = cv2.drawMatches(gray,kp1,test_gray,kp2,good,None,**draw_params)

        cv2.imshow("result", img3)
    # cv2.imshow("camera", test_gray)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
# cv2.imwrite("compare.jpg", img3)
# plt.imshow(img3, 'gray'),plt.show()

# monitor = cv2.drawKeypoints(gray, kp, gray.copy(), flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
# cv2.imwrite('keypoints.jpg', monitor)
