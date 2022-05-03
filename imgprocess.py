import math
import cv2
import numpy as np
from skimage.color import rgb2gray

'''
handles the actual computer vision part
'''

def get_lines(img):
    # convert to grayscale, blur, then get canny edges
    img = np.uint8(255 * rgb2gray(img))
    img = cv2.blur(img, (5, 5))
    edges = cv2.Canny(img, 50, 200)

    # get hough transform lines
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 125, None)

    # plots hough transform lines over blurred img for testing
    plot = np.stack((img,) * 3, axis=-1)
    xys = []
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
            pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
            xys.append([pt1, pt2])
            cv2.line(plot, pt1, pt2, (0,0,255), 1, cv2.LINE_AA)
    return plot