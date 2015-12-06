import cv2
import numpy as np

# No-Op function
def nothing(x):
    pass

# Creating a window for later use
cv2.namedWindow('result')

# Starting with 100's to prevent error while masking
h_low,s_low,v_low = 50,50,50
h_high,s_high,v_high = 100,100,100

# Creating track bar
cv2.createTrackbar('h_low', 'result',0,179,nothing)
cv2.createTrackbar('s_low', 'result',0,255,nothing)
cv2.createTrackbar('v_low', 'result',0,255,nothing)
cv2.createTrackbar('h_high', 'result',0,179,nothing)
cv2.createTrackbar('s_high', 'result',0,255,nothing)
cv2.createTrackbar('v_high', 'result',0,255,nothing)

while(1):
    frame = cv2.imread('data/hand_small_table.jpg', cv2.IMREAD_COLOR)
    HEIGHT, WIDTH, _ = frame.shape
    frame = cv2.resize(frame, (WIDTH/3,HEIGHT/3))

    #converting to HSV
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    # get info from track bar and appy to result
    h_low = cv2.getTrackbarPos('h_low','result')
    s_low = cv2.getTrackbarPos('s_low','result')
    v_low = cv2.getTrackbarPos('v_low','result')
    h_high = cv2.getTrackbarPos('h_high','result')
    s_high = cv2.getTrackbarPos('s_high','result')
    v_high = cv2.getTrackbarPos('v_high','result')

    # Normal masking algorithm
    lower = np.array([h_low,s_low,v_low])
    upper = np.array([h_high,s_high,v_high])

    mask = cv2.inRange(hsv,lower, upper)

    result = cv2.bitwise_and(frame,frame,mask = mask)

    cv2.imshow('result',result)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

print "H = [%d,%d]" % (h_low,h_high)
print "S = [%d,%d]" % (s_low,s_high)
print "V = [%d,%d]" % (v_low,v_high)
cv2.destroyAllWindows()
