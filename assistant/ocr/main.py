from skimage.io import imread
from skimage.io import imsave
import numpy as np
from matplotlib import pyplot as plt
from pylab import cm
import scipy
#import cv2
from PIL import Image
import pytesseract
#print(pytesseract.image_to_string(Image.open('glass1.jpg')))
#print(pytesseract.image_to_string(Image.open('glass2.jpg')))
#print(pytesseract.image_to_string(Image.open('glass3.jpg')))
#print(pytesseract.image_to_string(Image.open('glass4.jpg')))
#print(pytesseract.image_to_string(Image.open('glass5.jpg')))
#print(pytesseract.image_to_string(Image.open('glass6.jpg')))
#print(pytesseract.image_to_string(Image.open('test1.png')))


f = plt.figure(figsize=(12,3))
image = imread('glass7.jpg', as_grey=True)
imsave('glass_gs.jpg', image)
#print(np.mean(image))
imagethr = np.where(image > 0.6 ,0.,1.0)

#sub1 = plt.subplot(1,4,1)
#plt.imshow(imagethr, cmap=cm.gray)
#sub1.set_title("Threshold Image")
#plt.show()


imsave('glass_thr.jpg', imagethr)
print(pytesseract.image_to_string(Image.open('glass_thr.jpg')))