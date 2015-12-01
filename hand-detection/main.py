import cv2
import numpy as np
import math
import time
from handrecog import detect_hand

VIDEO_MODE = False

def main():
	cap = None
	counter = 0
	if VIDEO_MODE:
		#fgbg = cv2.createBackgroundSubtractorMOG()
		cap = cv2.VideoCapture(0)
		while(cap.isOpened()):
			if (counter % 30 == 0):
				ret, img = cap.read()

				#fgmask = fgbg.apply(frame)
				#cv2.imshow('frame', fgmask)
				warning = detect_hand(img, True)
				if warning:
					print warning
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break
			counter = counter + 1
		# When everything is done, release the capture
		# video_capture.release()
		# cv2.destroyAllWindows()
	else:
		img = cv2.imread('hand_med.jpg', cv2.IMREAD_COLOR)
		warning = detect_hand(img, True)
		if warning:
			print warning
		cv2.waitKey(1)

if __name__ == '__main__':
	main()

