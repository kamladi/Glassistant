import sys
import cv2                              
import numpy as np
import pickle
from cv_pickle import CVPickle

class CVError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class Assistant():

    def __init__(self, *args, **kw):
        #super( Assistant, self ).__init__( *args, **kw )
        self.i = 0

   
    def handle_frame(self, header, raw_data):

        # PERFORM Cognitive Assistant Processing
        sys.stdout.write("processing: \n%s\n" % header)
        step = header["step"]


        img_array = np.asarray(bytearray(raw_data), dtype=np.int8) 
        cv_image = cv2.imdecode(img_array, -1)

        result = {}
        step = int(float(step))
        print "ste"
        print step
        if step == 0:
            result = self.initial_check(cv_image)
        elif step == 1:
            print "initi setup"
            result = self.initial_setup(cv_image)
        elif step == 2:
            result = self.arm_check(cv_image)
        elif step == 3:
            result = self.error_read(cv_image)

        return result



    def initial_check(self, img):

        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        avr = np.average(hsv_image)
            
        ## TODO: check for noise

        if avr < 55:
            return {  "warning" : "Light not good enough.",
                      "next_step" : 0,
              "debug": avr }
        else:
            detector = cv2.SIFT(300)
            kp, desc = detector.detectAndCompute(img, None)
            
            if len(desc) > 3700:
                return {  "warning" : "Room looks too busy.",
                          "next_step" : 10}
            else:
                return {  "warning" : "Room looks good. Please hold the device and look at it",
                          "next_step" : 1 }

        return { "warning" : "There is a problem with the application.",
                 "next_step" : -1 }


    def filter_matches(self, kp1, kp2, matches, ratio = 0.75):
        mkp1, mkp2 = [], []
        for m in matches:
            if len(m) == 2 and m[0].distance < m[1].distance * ratio:
                m = m[0]
                mkp1.append( kp1[m.queryIdx] )
                mkp2.append( kp2[m.trainIdx] )
        kp_pairs = zip(mkp1, mkp2)
        return kp_pairs

    def extract_cached_descriptors(self, name):

        fname = "../assistant/" + name + ".xml"

        try:
            f = open(fname, 'r')
            temp = pickle.load(f)
            kp, desc = CVPickle().unpickle_keypoints(temp)
        except:
            raise CVError("Error getting the cached descriptors")

        f.close()

        return kp, desc

    def extract_image_descriptors(self, img):
        detector = cv2.SIFT(300)
        kp, desc = detector.detectAndCompute(img, None)
        return kp, desc


    def initial_setup(self, img):
        
        # default warning
        warning = "Please make sure that you are holding the device upright \
                    and to the center of your eyesight."

        try:
     
            img_device = cv2.imread("../assistant/device.jpg", 0)
            img_scene = img
            # extract device - cached for now
            kp1, desc1 = self.extract_cached_descriptors("device.jpg")
            # extract scene
            kp2, desc2 = self.extract_image_descriptors(img_scene)   

            print 'Scene - %d features' % (len(kp2))

            matcher = cv2.BFMatcher(cv2.NORM_L2)
            raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2
            kp_pairs = self.filter_matches(kp1, kp2, raw_matches)

            mkp1, mkp2 = zip(*kp_pairs)
            
            p1 = np.float32([kp.pt for kp in mkp1])
            p2 = np.float32([kp.pt for kp in mkp2])
            
            if len(kp_pairs) >= 4:
                H, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)
            else:
                raise CVError("Could not find Homography")
            

            if H is None:
                warning = "Device is not visible"
                raise CVError("Could not find Homography")

            h1, w1 = img_device.shape[:2]
            h2, w2 = img_scene.shape[:2]
            #vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
            #vis[:h1, :w1] = img_device
            #vis[:h2, w1:w1+w2] = img_scene
            #vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
         
            corners = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]])
            corners = np.int32( cv2.perspectiveTransform(corners.reshape(1, -1, 2), H).reshape(-1, 2) + (w1, 0) )
            
            # sanity checking for sizes
            # if the area is too small, it is 
            # probably a bad result
             (tl, tr, br, bl) = corners
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[0] - bl[0]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[0] - tl[0]) ** 2))
             
            # ...and now for the height of our new image
            heightA = np.sqrt(((tr[1] - br[1]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[1] - bl[1]) ** 2) + ((tl[1] - bl[1]) ** 2))
             
            # take the maximum of the width and height values to reach
            # our final dimensions
            maxWidth = max(int(widthA), int(widthB))
            maxHeight = max(int(heightA), int(heightB))

            if maxWidth < 5 or maxHeight < 5:
                warning = "Device is not visible"
                raise CVError("Result area is too small")


            """
            sample corners
            [[2284 1671]
             [2596 1165]
             [3231 1573]
             [2878 2083]]
            """
            ## check correct orientation
            x1,y1 = corners[0]
            x2,y2 = corners[1]
            x3,y3 = corners[2]
            x4,y4 = corners[3]

            if y1 > y4 or y2 > y3:
                warning = "Incorrect device orientation"
                raise CVError("Incorrect device orientation")
            else:
                return {  "warning": "Device looks okay. Please put it on your arm.",
                          "next_step": 2 }

        except CVError as e:
            print e
            return {  "warning": warning,
                      "next_step": 1  }

    def arm_check(self, img):
        
        # default warning
        warning = "Please make sure that the device is on your wrist and you are looking at it."

        # TODO: find the palm/thumb and identify side
        # TODO: identify hand

        try:
     
            img_device = cv2.imread("../assistant/device.jpg", 0)
            img_scene = img
            # extract device - cached for now
            kp1, desc1 = self.extract_cached_descriptors("device.jpg")
            # extract scene
            kp2, desc2 = self.extract_image_descriptors(img_scene)   

            print 'Scene - %d features' % (len(kp2))

            matcher = cv2.BFMatcher(cv2.NORM_L2)
            raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2
            kp_pairs = self.filter_matches(kp1, kp2, raw_matches)

            mkp1, mkp2 = zip(*kp_pairs)
            
            p1 = np.float32([kp.pt for kp in mkp1])
            p2 = np.float32([kp.pt for kp in mkp2])
            
            if len(kp_pairs) >= 4:
                H, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)
            else:
                raise CVError("Could not find Homography")
            
            h1, w1 = img_device.shape[:2]
            h2, w2 = img_scene.shape[:2]
            #vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
            #vis[:h1, :w1] = img_device
            #vis[:h2, w1:w1+w2] = img_scene
            #vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
         
            corners = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]])
            corners = np.int32( cv2.perspectiveTransform(corners.reshape(1, -1, 2), H).reshape(-1, 2) + (w1, 0) )
            """
            sample corners
            [[2284 1671]
             [2596 1165]
             [3231 1573]
             [2878 2083]]
            """
            ## check correct orientation
            x1,y1 = corners[0]
            x2,y2 = corners[1]
            x3,y3 = corners[2]
            x4,y4 = corners[3]

            if y1 > y4 or y2 > y3:
                warning = "Incorrect device orientation"
                raise CVError("Could not find Homography")
            else:
                arm_side = "Right"
                if y1 < y2:
                    arm_side = "Left"

                return {  "warning": arm_side + " arm looks okay. Please press the" +
                                                "button to to start measurement.",
                          "next_step": 3 }

        except CVError as e:
            print e
            return {  "warning": warning,
                      "next_step": 2  }


    def error_read(self, img):
        return {  "warning": "Keep your arm steady and look at it during the measurement",
                  "next_step": 3  }

