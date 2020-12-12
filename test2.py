import numpy as np
import cv2
from matplotlib import pyplot as plt

def match_symbol(base_im,sym_im):
    if (len(base_im.shape)) != 2:
        base_im = cv2.cvtColor(base_im,cv2.COLOR_BGR2GRAY)

    if (len(sym_im.shape)) != 2:
        sym_im = cv2.cvtColor(sym_im,cv2.COLOR_BGR2GRAY)

    # Initiate SIFT detector
    sift = cv2.SIFT_create()
    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(base_im,None)
    kp2, des2 = sift.detectAndCompute(sym_im,None)

    # FLANN parameters
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks=1000)   # or pass empty dictionary
    flann = cv2.FlannBasedMatcher(index_params,search_params)
    matches = flann.knnMatch(des1,des2,k=2)
    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)
    x = 0
    y = 0
    points = [kp1[m.queryIdx].pt for m in good ]
    for point in points:
        x += point[0]
        y += point[1]
    x = int(x/len(points))
    y = int(y/len(points))
    return x,y

if __name__ == '__main__':
    img = cv2.imread('images/matcher/5.jpg',0)
    symbol = cv2.imread('images/symbols/hexa.png',0)
    match_symbol(img,symbol)
