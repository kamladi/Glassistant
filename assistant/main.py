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

class Assistant:
    
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
            print "OK"


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
            return {  "warning" : "Room looks good.",
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

        fname = name + ".xml"

        try:
            f = open(fname, 'r')
            temp = pickle.load(f)
            kp, desc = CVPickle().unpickle_keypoints(temp)
        except:
            raise CVError("Error getting the cached descriptors")

        f.close()

        return kp, desc

    def extract_image_descriptors(self, img):
        detector = cv2.SURF(400, 5, 5)
        kp, desc = detector.detectAndCompute(img, None)
        return kp, desc


    def initial_setup(self, img):
        
        # default warning
        warning = "Please make sure that you are holding the device upright \
                    and to the center of your eyesight."

        try:
     
            img_device = cv2.imread("device.jpg", 0)
            img_scene = img
            # extract device - cached for now
            kp1, desc1 = self.extract_cached_descriptors("device.jpg")
            # extract scene
            kp2, desc2 = self.extract_image_descriptors(img_scene)   

            print 'Scene - %d features' % (len(kp1), len(kp2))

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
            vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
            vis[:h1, :w1] = img_device
            vis[:h2, w1:w1+w2] = img_scene
            vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
         
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
                return {  "warning": "Device looks okay. Please put it on your arm.",
                          "next_step": 1 }

        except CVError as e:
            print e
            return {  "warning": warning,
                      "next_step": 1  }

