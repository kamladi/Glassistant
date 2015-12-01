import cv2
import numpy as np

hand_cascade = cv2.CascadeClassifier('HandCascade1.xml')

frame = cv2.imread('hand_small.jpg', cv2.IMREAD_COLOR)
HEIGHT, WIDTH, _ = frame.shape
frame = cv2.resize(frame, (WIDTH/3,HEIGHT/3))
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

hands = hand_cascade.detectMultiScale(gray, 1.3, 10)

for (x,y,w,h) in hands:
	cv2.rectangle(gray,(x,y),(x+w,y+h),(255,0,0),2)

cv2.imshow('hand', gray)
cv2.waitKey(0)
cv2.destroyAllWindows()
