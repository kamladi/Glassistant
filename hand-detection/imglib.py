import cv2
import numpy as np
import math
import time

IMG_SCALE = 1

def findLargestContour(img):
	SMALLEST_AREA = 600
	(contours,hierarchy) = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

	# extract largest contour
	maxArea = SMALLEST_AREA
	largestContour = None
	for i in range(len(contours)):
		curContour = contours[i]
		area = cv2.contourArea(curContour)
		if(area > maxArea):
			maxArea = area
			largestContour = curContour
	return (largestContour, maxArea)


def calculateTilt(m11, m20, m02):
	diff = m20 - m02
	if diff == 0:
		if m11 == 0:
			return 0
		elif m11 > 0:
			return 45
		else: # m11 < 0
			return -45

	theta = 0.5 * math.atan2(2*m11, diff)
	tilt = round(math.degrees(theta))

	if diff > 0 and m11 == 0:
		return 0
	elif diff < 0 and m11 == 0:
		return -90
	elif diff > 0 and m11 > 0: # 0 to 45 degrees
		return tilt
	elif diff > 0 and m11 < 0: # -45 to 0 degrees
		return 180+tilt # change to counter-clockwise angle
	elif diff < 0 and m11 > 0: # 45 to 90
		return tilt
	elif diff < 0 and m11 < 0: # -90 to -45
		return 180 + tilt # change to counter-clockwise angle

		print "Error in calculating spatial moments angle"
	return 0

# find COM and angle of hand contour
def extractContourInfo(contour, scale):
	moments = cv2.moments(contour, 1)
	m00 = moments['m00']
	m10 = moments['m10']
	m01 = moments['m01']

	center = None
	if m00 != 0:
		xCenter = round(m10/m00)*scale
		yCenter = round(m01/m00)*scale
		center = (int(xCenter),int(yCenter))

	m11 = moments['m11']
	m20 = moments['m20']
	m02 = moments['m02']
	axisAngle = calculateTilt(m11, m20, m02)

	return (center, axisAngle)

def findFingertips(contour, scale):
	convexHull = cv2.convexHull(contour, returnPoints = False)
	defects = cv2.convexityDefects(contour, convexHull)
	count_defects = 0
	fingerTips = []
	fingerFolds = []
	for i in range(defects.shape[0]):
		s,e,f,d = defects[i,0]
		start = tuple(contour[s][0])
		end = tuple(contour[e][0])
		far = tuple(contour[f][0])
		a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
		b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
		c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
		angle = math.acos((b**2 + c**2 - a**2)/(2*b*c)) * 57
		if angle <= 90:
			fingerTips.append((start,end))
			fingerFolds.append(far)
	return fingerTips, fingerFolds

def findThumb(fingerTips, fingerFolds):
	maxFingerDepth = -1
	maxFingerDepth_finger = None
	for i in xrange(len(fingerTips)):
		start = fingerTips[i][0]
		end = fingerTips[i][1]
		depth = fingerFolds[i]
		distToStart = np.linalg.norm(np.subtract(start, depth))
		distToEnd = np.linalg.norm(np.subtract(end, depth))
		if distToStart > maxFingerDepth or distToEnd > maxFingerDepth:
			# Whichever defect has the longest depth has the thumb,
			# but the thumb is the shorter of the two depths
			# (the longer depth would be the index finger)
			if distToStart > distToEnd:
				maxFingerDepth_finger = fingerTips[i][1]
				maxFingerDepth = distToStart
			else:
				maxFingerDepth_finger = fingerTips[i][0]
				maxFingerDepth = distToEnd
	return maxFingerDepth_finger

def isHandUp(fingerFolds, center):
	# collect the mean of the finger fold points
	numFingerFolds = len(fingerFolds)
	sum = (0.0,0.0)
	for fingerFold in fingerFolds:
		sum = np.add(sum, fingerFold)
	meanFingerFold = (sum[0] / numFingerFolds, sum[1] / numFingerFolds)

	# hand is upright if the mean fingerfold is
	# above the center of the hand
	return meanFingerFold[1] < center[1]

def process_frame(img):
	# Get image dimensions.
	HEIGHT, WIDTH, _ = img.shape
	M = cv2.getRotationMatrix2D((WIDTH/2,HEIGHT/2),35,1)
	img = cv2.warpAffine(img,M,(WIDTH,HEIGHT))
	#img = cv2.resize(img, (HEIGHT/3,WIDTH/3))
	cv2.imshow('img', img)
	time.sleep(2)

	# Add initial contrast to img.
	#mul = cv2.multiply(img, np.array(2.0))
	mul = img
	# Convert to HSV and blur.
	#gray = cv2.cvtColor(mul, cv2.COLOR_BGR2GRAY)
	gray = cv2.cvtColor(mul, cv2.COLOR_BGR2HSV)
	blur = cv2.GaussianBlur(gray, (35,35),0)
	cv2.imshow('img', blur)
	cv2.waitKey(1)
	time.sleep(2)

	lower_thresh = np.array([0, 40, 60])
	upper_thresh = np.array([20, 150, 255])
	#lower_thresh1 = np.array([0, 0, 0])
	#upper_thresh1 = np.array([100, 100, 100])

	mask = cv2.inRange(blur, lower_thresh, upper_thresh)
	#_, mask = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	cv2.imshow('img', mask)
	cv2.waitKey(1)
	time.sleep(2)
	#mask1 = cv2.inRange(blur, lower_thresh1, upper_thresh1)

	# remove noise
	kernel = np.ones((5,5),np.uint8)
	hand_img = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


	(contour, contour_area) = findLargestContour(hand_img)
	if contour is None:
		print "unable to find contour"
		return
	print "hand area: ", contour_area
	hull = cv2.convexHull(contour)

	print "hull length: %s" % len(hull)

	# find COG and angle of hand contour
	(center, axisAngle) = extractContourInfo(contour, IMG_SCALE)
	print "(center, axisAngle) = ", center, axisAngle

	# draw contour and convex hull
	drawing = np.zeros(img.shape, np.uint8)
	cv2.circle(drawing, center, 10, (255,255,255), -1)
	cv2.drawContours(drawing, [contour],0,(0,255,0),2)
	cv2.drawContours(drawing, [hull],0,(0,0,255),2)
	cv2.circle(img,center,5,[0,0,255],-1)
	(x,y),(MA,ma),angle = cv2.fitEllipse(contour)
	print "angle = %f" % angle
	fingerTips, fingerFolds = findFingertips(contour, IMG_SCALE)

	# for i in xrange(len(fingerTips)):
	# 	cv2.line(drawing, fingerTips[i][0], fingerFolds[i], (0,255,255), 2)
	# 	cv2.line(drawing, fingerTips[i][1], fingerFolds[i], (0,255,255), 2)
	# 	cv2.circle(drawing, fingerFolds[i], 10, (255,255,0), -1)
	# 	depth1 = np.linalg.norm(np.subtract(fingerTips[i][0],fingerFolds[i]))
	# 	depth2 = np.linalg.norm(np.subtract(fingerTips[i][1],fingerFolds[i]))
	# 	print "depth at %d: %.2f" % (i, max(depth1,depth2))

	thumbPt = findThumb(fingerTips, fingerFolds)
	if thumbPt:
		print "Thumb Pt: ", thumbPt
		distCenterToThumb = np.linalg.norm(np.subtract(thumbPt, center))
		if distCenterToThumb < 200 or 500 < distCenterToThumb:
			print "invalid thumb location"
			return
		handUp = isHandUp(fingerFolds, center)
		if handUp:
			if thumbPt[0] < center[0]:
				print "HAND UP, THUMB ON LEFT => PALM DOWN"
			else:
				print "HAND UP, THUMB ON RIGHT => PALM UP"
		else:
			if thumbPt[0] < center[0]:
				print "HAND DOWN, THUMB ON LEFT => PALM UP"
			else:
				print "HAND DOWN, THUMB ON RIGHT => PALM DOWN"

		cv2.circle(drawing,thumbPt,15,[255,0,0],-1)
		[vx,vy,x,y] = cv2.fitLine(contour, cv2.cv.CV_DIST_L2,0,0.01,0.01)
		lefty = int((-x*vy/vx) + y)
		righty = int(((WIDTH-x)*vy/vx)+y)
		cv2.line(drawing,(WIDTH-1,righty),(0,lefty),(0,255,0),2)
		cv2.imshow('img', drawing)
		cv2.waitKey(0)
		time.sleep(1)
	else: # no thumb found
		print "no thumb found"


