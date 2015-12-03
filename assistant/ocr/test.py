import numpy as np
import cv2
from PIL import Image
import pytesseract


img = cv2.imread("glass3_lowres.jpg",cv2.IMREAD_GRAYSCALE)
cv2.imshow('img',img)
cv2.waitKey(0)

thresh,img = cv2.threshold(img,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

cv2.imshow('img',img)
cv2.waitKey(0)

kernel = np.ones((2,2),np.uint8)
#img = cv2.erode(img, kernel,iterations = 1)
img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

cv2.imshow('img',img)
cv2.waitKey(0)

(contours,hierarchy) = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
print "num contours: ", len(contours)

# TEMP_IMAGE = "tmp.bmp"
# cv2.imwrite(TEMP_IMAGE, img)
# str1 = pytesseract.image_to_string(Image.open(TEMP_IMAGE))
# os.remove(TEMP_IMAGE)
