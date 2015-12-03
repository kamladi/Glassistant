from __future__ import print_function
import argparse
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = True, help = "Path to the image")
args = vars(ap.parse_args())

image = cv2.imread(args["image"])
corner = image[0:100, 0:100]

image[0:100, 0:100] = (255, 0, 0)

cv2.imshow("Corner", corner)
cv2.imshow("Updated", image)
cv2.waitKey(0)
