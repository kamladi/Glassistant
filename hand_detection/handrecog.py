import cv2
import numpy as np
import math
import time

IMG_SCALE = 1

# Find contours in a thresholded image, and return the contour
# most likely to be the hand (min and max contour areas based on 320x240 video frame)
def findHandContour(img):
	MIN_CONTOUR_AREA = 3000
	MAX_CONTOUR_AREA = 10000
	(contours,hierarchy) = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

	# extract hand contour
	maxArea = MIN_CONTOUR_AREA
	largestContour = None
	for i in range(len(contours)):
		curContour = contours[i]
		area = cv2.contourArea(curContour)
		if(area > maxArea and area < MAX_CONTOUR_AREA):
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
	orientation = calculateTilt(m11, m20, m02)

	return (center, orientation)

# returns of a list of the finger defects from the hand contour.
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

# Returns the location of the end of the thumb from a hand contour.
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
	return (maxFingerDepth_finger)

# Determine if hand is facing up or down.
# collects the "mean" of the finger defects, and checks if it is
#		above or below the center of the hand.
def isHandUp(fingerTips, center):
	# collect the mean of the finger fold points
	numFingerFolds = len(fingerTips)
	sum = (0.0,0.0)
	for (start,end) in fingerTips:
		sum = np.add(sum, start)
	meanFingerFold = (sum[0] / numFingerFolds, sum[1] / numFingerFolds)

	# hand is upright if the mean fingerfold is
	# above the center of the hand
	return meanFingerFold[1] < center[1]



# DETECT_HAND main hand detection function.
def detect_hand(img, debug=False):
	# Get image dimensions.
	HEIGHT, WIDTH, _ = img.shape

	if debug:
		cv2.imshow('img', img)
		cv2.waitKey(0)

	# Add initial contrast to img.
	#mul = cv2.multiply(img, np.array(2.0))
	mul = img
	# Convert to HSV and blur.
	#gray = cv2.cvtColor(mul, cv2.COLOR_BGR2GRAY)
	gray = cv2.cvtColor(mul, cv2.COLOR_BGR2HSV)

	if debug:
		cv2.imshow('img', blur)
		cv2.waitKey(0)

	lower_thresh = np.array([0, 70, 0])
	upper_thresh = np.array([30, 171, 255])

	mask = cv2.inRange(gray, lower_thresh, upper_thresh)
	if debug:
		cv2.imshow('img', mask)
		cv2.waitKey(0)

	# remove noise
	#kernel = np.ones((5,5),np.uint8)
	kernel = np.ones((5,5),np.uint8)
	hand_img = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


	(contour, contour_area) = findHandContour(hand_img)
	print "contour area: ", contour_area
	if contour is None:
		warning = "Unable to find hand. Try moving your hand further away, or moving to a clean surface."
		return warning

	hull = cv2.convexHull(contour)

	print "hull length: %s" % len(hull)

	# find COG and angle of hand contour
	(center, orientation) = extractContourInfo(contour, IMG_SCALE)
	print "(center, orientation) = ", center, orientation

	if debug:
		# draw contour and convex hull
		drawing = np.zeros(img.shape, np.uint8)
		cv2.circle(drawing, center, 10, (255,255,255), -1)
		cv2.drawContours(drawing, [contour],0,(0,255,0),2)
		cv2.drawContours(drawing, [hull],0,(0,0,255),2)
		cv2.circle(img,center,5,[0,0,255],-1)
		(x,y),(MA,ma),angle = cv2.fitEllipse(contour)
		print "angle = %f" % angle

	# collect a list of finger defects
	fingerTips, fingerFolds = findFingertips(contour, IMG_SCALE)

	# select the finger defect most likely to be the thumb.
	thumbPt = findThumb(fingerTips, fingerFolds)
	if thumbPt:
		if debug:
			cv2.circle(drawing,thumbPt,15,[255,0,0],-1)
			cv2.imshow('img', drawing)
			cv2.waitKey(0)
		distCenterToThumb = np.linalg.norm(np.subtract(thumbPt, center))
		print "thumb dist: ", distCenterToThumb
		handUp = isHandUp(fingerTips, center)
		if handUp:
			if thumbPt[0] < center[0]:
				print "HAND UP, THUMB ON LEFT => PALM DOWN"
				return "Left hand detected. Use your right hand instead."
			else:
				# SUCCESS
				print "HAND UP, THUMB ON RIGHT => PALM UP"
				return None
		else:
			if thumbPt[0] < center[0]:
				print "HAND DOWN, THUMB ON LEFT => PALM UP"
				return "Hand is upside-down. Hand should be face up, palm up."
			else:
				print "HAND DOWN, THUMB ON RIGHT => PALM DOWN"
				return "Hand is upside-down. Hand should be face up, palm up."
		return None # sucess, no error message
	else: # no thumb found
		warning = "no thumb found"
		return warning


