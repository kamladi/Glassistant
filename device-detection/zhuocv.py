#!/usr/bin/env python
#
# Cloudlet Infrastructure for Mobile Computing
#   - Task Assistance
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import cv2
import numpy as np

def get_DoB(img, k1, k2, method = 'Average'):
    '''
    Get difference of blur of an image (@img) with @method.
    The two blurred image are with kernal size @k1 and @k2.
    @method can be one of the strings: 'Gaussian', 'Average'.
    '''
    if k1 == 1:
        blurred1 = img
    elif method == 'Gaussian':
        blurred1 = cv2.GaussianBlur(img, (k1, k1), 0)
    elif method == 'Average':
        blurred1 = cv2.blur(img, (k1, k1))
    if k2 == 1:
        blurred2 = img
    elif method == 'Gaussian':
        blurred2 = cv2.GaussianBlur(img, (k2, k2), 0)
    elif method == 'Average':
        blurred2 = cv2.blur(img, (k2, k2))
    difference = cv2.subtract(blurred1, blurred2)
    return difference

def color_inrange(img, color_space, hsv = None, B_L = 0, B_U = 255, G_L = 0, G_U = 255, R_L = 0, R_U = 255,
                                                H_L = 0, H_U = 90, S_L = 0, S_U = 255, V_L = 40, V_U = 105,
                                                L = 0, U = 255):
    if color_space == 'BGR':
        lower_range = np.array([B_L, G_L, R_L], dtype=np.uint8)
        upper_range = np.array([B_U, G_U, R_U], dtype=np.uint8)
        mask = cv2.inRange(img, lower_range, upper_range)
    elif color_space == 'HSV':
        if hsv is None:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if H_L <= H_U:
            lower_range = np.array([H_L, S_L, V_L], dtype=np.uint8)
            upper_range = np.array([H_U, S_U, V_U], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_range, upper_range)
        else:
            lower_range1 = np.array([H_L, S_L, V_L], dtype=np.uint8)
            upper_range1 = np.array([180, S_U, V_U], dtype=np.uint8)
            mask1 = cv2.inRange(hsv, lower_range1, upper_range1)
            lower_range2 = np.array([0, S_L, V_L], dtype=np.uint8)
            upper_range2 = np.array([H_U, S_U, V_U], dtype=np.uint8)
            mask2 = cv2.inRange(hsv, lower_range2, upper_range2)
            mask = np.bitwise_or(mask1, mask2)
    elif color_space == 'single':
        lower_range = np.array([L], dtype=np.uint8)
        upper_range = np.array([U], dtype=np.uint8)
        mask = cv2.inRange(img, lower_range, upper_range)

    return mask
