import serial 
import time
import math
import numpy as np
import cv2
def mm2pulse(mm):
    return int(mm * ((48*64*2)/(math.pi * 6.36619 * 2)))

def crop_img(img, scale=1.0):
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x - width_scaled / 2, center_x + width_scaled / 2
    top_y, bottom_y = center_y - height_scaled / 2, center_y + height_scaled / 2
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


def line_intersection(line1, line2):
    # reference https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return [int(x), int(y)]

def gey_thresh_canny(img):
    med_val = np.median(img)
    lower = int(max(0 ,0.7*med_val))
    upper = int(min(255,1.3*med_val))
    return lower,upper

def upgrade_border(img, thickness):
    if (len(img.shape)) != 2:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blank = np.zeros(img.shape,np.uint8)
    contours, hierarchy = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(blank, contours, -1, 255, thickness)
    return blank

def remove_noise_binary(img):
    kernel = np.ones((5,5),np.uint8)
    denoised = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    return denoised

def remove_small_area(img,min_area):
    if (len(img.shape) == 3):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blank = np.zeros(img.shape,np.uint8)
    img = img.astype(np.uint8)
    contours, hier = cv2.findContours(img,cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if min_area<cv2.contourArea(cnt):
            cv2.drawContours(blank,[cnt],0,255,1)
            cv2.drawContours(blank,[cnt],0,255,-1)
    return blank

def seperate_contour(img):
    if (len(img.shape) == 3):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    seperate_img = []
    cnt, hierarchy = cv2.findContours(img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(cnt)):
        output_canvas = np.zeros(img.shape, dtype=np.uint8)
        cv2.drawContours(output_canvas, cnt, i, (255,255,255), -1)
        seperate_img.append(output_canvas)
        # white_pixel_list.append(np.argwhere(output_canvas == 255))
    return seperate_img

def find_minmax_intensity(img1,img2):
    value = []
    for pixel in np.argwhere(img2 == 255):
        value.append(img1[pixel[0],pixel[1]])
    print(min(value))
    print(max(value))
    return min(value), max(value)

def map_value(value,from_min,from_max,to_min,to_max):
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def a_in_b(img_a,img_b):
    pixel_a = np.argwhere(img_a == 255)
    pixel_b = np.argwhere(img_b == 255)
    lst = []
    for pixel in pixel_a:
        if pixel in pixel_b:
            lst.append(pixel)
    return lst

def find_nearest_white(target, pixel_with_height,image):
    nonzero = cv2.findNonZero(image)
    distances = np.sqrt((nonzero[:,:,0] - target[0]) ** 2 + (nonzero[:,:,1] - target[1]) ** 2)
    nearest_index = np.argmin(distances)
    for i in pixel_with_height:
        if nonzero[nearest_index][0][1] == i[0][0] and nonzero[nearest_index][0][0] == i[0][1]:
            return i[1]

def find_endpoints(skel):
    # make out input nice, possibly necessary
    skel = skel.copy()
    skel[skel!=0] = 1
    skel = np.uint8(skel)
    cv2.waitKey(0)
    # apply the convolution
    kernel = np.uint8([[1,  1, 1],
                       [1, 10, 1],
                       [1,  1, 1]])
    src_depth = -1
    filtered = cv2.filter2D(skel,src_depth,kernel)
    return np.argwhere(filtered==11)


def find_endpoints(skel):
    # make out input nice, possibly necessary
    skel = skel.copy()
    skel[skel!=0] = 1
    skel = np.uint8(skel)
    cv2.waitKey(0)
    # apply the convolution
    kernel = np.uint8([[1,  1, 1],
                       [1, 10, 1],
                       [1,  1, 1]])
    src_depth = -1
    filtered = cv2.filter2D(skel,src_depth,kernel)
    return np.argwhere(filtered==11)

def fill_white(img,ex_or_in):
    # make out input nice, possibly necessary
    img = img.copy()
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    outside_contours = []
    inside_contours = []
    for con,hie in zip(contours,hierarchy[0]):
        if hie[3] == -1:
            outside_contours.append(con)
        if hie[2] == -1:
            inside_contours.append(con)
    if (ex_or_in == 'in'):
        cv2.drawContours(img, inside_contours, -1, 255, -1)
    if (ex_or_in == 'ex'):
        cv2.drawContours(img, outside_contours, -1, 255, -1)
    return img

def simplify_contour(img):
    blank = np.zeros(img.shape, np.uint8)
    contours, hierarchy = cv2.findContours(img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        epsilon = 0.008 * cv2.arcLength(cnt,True)
        approx = cv2.approxPolyDP(cnt,epsilon,True)
        cv2.drawContours(blank, [approx], -1, 255, -1)
    # contours, hierarchy = cv2.findContours(img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    # for cnt in contours:
    #     hull = cv2.convexHull(cnt)
    #     cv2.drawContours(blank, [hull], -1, 255, -1)
    blank_thin = cv2.ximgproc.thinning(blank)
    while (len(find_endpoints((blank_thin))) != 2):
        blank = cv2.erode(blank,None,iterations=1)
        blank_thin = cv2.ximgproc.thinning(blank)
        # print('fame')
    return blank

def match_symbol(map_img,icon_img):
    if (len(map_img.shape)) != 2:
        map_img = cv2.cvtColor(map_img,cv2.COLOR_BGR2GRAY)

    if (len(icon_img.shape)) != 2:
        icon_img = cv2.cvtColor(icon_img,cv2.COLOR_BGR2GRAY)

    # Initiate SIFT detector
    sift = cv2.SIFT_create()
    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(map_img, None)
    kp2, des2 = sift.detectAndCompute(icon_img, None)
    # BFMatcher with default params
    bf = cv2.BFMatcher()
    matches = bf.match(des1,des2)
    # Apply ratio test
    matches = sorted(matches, key = lambda x:x.distance)
    # get only 10% of matches
    for_matches_cnt = int(len(matches)*0.1)
    x_sum = 0
    y_sum = 0
    for i in range(for_matches_cnt):
        x_sum += kp2[matches[i].trainIdx].pt[0]
        y_sum += kp2[matches[i].trainIdx].pt[1]
    x_tot = int(x_sum/for_matches_cnt)
    y_tot = int(y_sum/for_matches_cnt)
    return x_tot,y_tot

def cm2pulse(cm):
    mm = cm * 10
    return int(mm * ((48*64*2)/(math.pi * 6.36619 * 2)))

def pulse2mm(pulse):
    return (pulse*math.pi*6.36619*2)/(48*64*2)
# 61471
if __name__ == '__main__':
    print(mm2pulse(80))
    print(mm2pulse(160))
    print(mm2pulse(220))