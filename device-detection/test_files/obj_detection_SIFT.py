import cv2
import numpy as np
from matplotlib import pyplot as plt

monitor = cv2.imread('bp_monitor.jpg')
test = cv2.imread('test_img.jpg')
gray = cv2.cvtColor(monitor, cv2.COLOR_BGR2GRAY)
test_gray = cv2.cvtColor(test, cv2.COLOR_BGR2GRAY)

sift = cv2.xfeatures2d.SIFT_create()
kp1, des1 = sift.detectAndCompute(gray, None)
kp2, des2 = sift.detectAndCompute(test_gray, None)

bf = cv2.BFMatcher()
matches = bf.knnMatch(des1, des2, k=2)

good = []
for m,n in matches:
    if m.distance < 0.95*n.distance:
        good.append([m])

src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)

img3 = cv2.drawMatchesKnn(monitor,kp1,test,kp2,good, monitor, flags=2)
plt.imshow(img3),plt.show()

# monitor = cv2.drawKeypoints(gray, kp, gray.copy(), flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
# cv2.imwrite('keypoints.jpg', monitor)
