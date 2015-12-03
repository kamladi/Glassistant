import sys
import cv2
import numpy as np
from instruction_messages import INSTRUCTIONS
from hand_detection.handrecog import detect_hand
from device_detection.obj_track import detect_monitor

class CVError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class Assistant:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode

    def handle_frame(self, header, raw_data):
        if self.test_mode:
            return self.handle_test(header, raw_data)

        # PERFORM Cognitive Assistant Processing
        sys.stdout.write("TEST processing: \n%s\n" % header)
        step = header["step"]

        img_array = np.asarray(bytearray(raw_data), dtype=np.int8)
        cv_image = cv2.imdecode(img_array, -1)

        result = {}
        step = int(float(step))
        print "step ", step
        if step == 0:
            # STEP 0: INITIAL CHECK
            print "initial check"
            warning = self.initial_check(cv_image)
            if warning is None:
                result["next_step"] = step + 1
                result["message"] = INSTRUCTIONS[step + 1]
            else:
                result["next_step"] = step
                result["message"] = warning
        elif step == 1:
             # STEP 1: CHECK MONITOR UPRIGHT
            print "detect monitor"
            warning = detect_monitor(cv_image)
            if warning is None:
                result["next_step"] = step + 1
                result["message"] = INSTRUCTIONS[step + 1]
            else:
                result["next_step"] = step
                result["message"] = warning
        elif step == 2:
            # STEP 2: MONITOR ON RIGHT HAND, PALM UP
            warning = detect_hand(cv_image)
            if warning is None:
                result["next_step"] = step + 1
                result["message"] = INSTRUCTIONS[step + 1]
            else:
                result["next_step"] = step
                result["message"] = warning
        elif step == 3:
            # STEP 3: DISTANCE BTWN CUFF AND WRIST
            # Stay on current step, client will skip step when user says "OK"
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        elif step == 4:
            # STEP 4: STRAP TIGHTENED
            # Stay on current step, client will skip step when user says "OK"
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        elif step == 5:
            # STEP 5: ELBOW ON SURFACE
            # Stay on current step, client will skip step when user says "OK"
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        elif step == 6:
            # STEP 6: LEFT HAND ON HEART
            # Stay on current step, client will skip step when user says "OK"
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        elif step == 7:
            # STEP 7: CUFF ON SAME LEVEL AS LEFT HAND / START MEASUREMENT
            # Stay on current step, client will skip step when user says "OK"
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        elif step == 8:
            # STEP 8: ALL INDICATORS ON, STABLE READING ON SCREEN
            # Stay on current step, client will skip step when user says "OK"
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        elif step == 9:
            # STEP 9: STABLE READING ON SCREEN
            result["next_step"] = step
            result["message"] = INSTRUCTIONS[step]
        else:
            # Invalid step number
            result = {
                "message": "Invalid step",
                "next_step": -1
            }
        return result

    # handler for debug mode
    def handle_test(self, header, raw_data):
        sys.stdout.write("processing: \n%s\n" % header)
        step = int(float(header["step"]))

        if step == 0:
            result = {  "message" : "Room looks good.",
                      "next_step" : 1 }

        elif step == 1:
            print "initial setup"
            result = {  "message": "Device looks okay. Please put it on your arm.",
                          "next_step": 1 }
        elif step == 2:
            print "OK"

        return result


    def initial_check(self, img):
        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        avr = np.average(hsv_image)

        ## TODO: check for noise

        if avr < 55:
            return "Light not good enough"
        else:
            return None
