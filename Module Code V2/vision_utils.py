import cv2
import numpy as np
import imutils

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

def get_between_area(img,min_area,max_area):
    if (len(img.shape) == 3):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blank = np.zeros(img.shape,np.uint8)
    img = img.astype(np.uint8)
    contours, hier = cv2.findContours(img,cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if min_area<cv2.contourArea(cnt)<max_area:
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

def get_contour_centroid_list(img):
    contours, hier = cv2.findContours(img,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    symbol_center_list = []
    for cnt in contours:
        cnt_moment = cv2.moments(cnt)
        cx = int(cnt_moment['m10']/cnt_moment['m00'])
        cy = int(cnt_moment['m01']/cnt_moment['m00'])
        symbol_center_list.append((cx,cy))
    return symbol_center_list

def find_endpoints(skel):
    # make out input nice, possibly necessary
    skel = skel.copy()
    skel[skel!=0] = 1
    skel = np.uint8(skel)
    # apply the convolution
    kernel = np.uint8([[1,  1, 1],
                       [1, 10, 1],
                       [1,  1, 1]])
    src_depth = -1
    filtered = cv2.filter2D(skel,src_depth,kernel)
    return np.argwhere(filtered==11)
    
def map_value(value,from_min,from_max,to_min,to_max):
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def check_in_region(main_point,check_point,radius):
    center_x,center_y = main_point[0],main_point[1]
    x,y = check_point[1],check_point[0]
    return ((x - center_x)**2 + (y - center_y)**2) < radius^2

def find_minmax_intensity(img1,img2):
    value = []
    for pixel in np.argwhere(img2 == 255):
        value.append(img1[pixel[0],pixel[1]])
    print('min intensity is{}'.format(min(value)))
    print('max intensity is{}'.format(max(value)))
    return min(value), max(value)

if __name__ == '__main__':
    #Open template and get canny
    template = cv2.imread('images/symbols/chess.png',0)
    img_gray = cv2.imread('images/process_data/test2.png',0)
    
    # Store width and height of template in w and h 
    w, h = template.shape[::-1] 
    found = None
    
    for scale in np.linspace(0.2, 1.0, 20)[::-1]: 
    
        # resize the image according to the scale, and keep track 
        # of the ratio of the resizing 
        resized = imutils.resize(img_gray, width = int(img_gray.shape[1] * scale)) 
        r = img_gray.shape[1] / float(resized.shape[1]) 
    
        # if the resized image is smaller than the template, then break 
        # from the loop 
        # detect edges in the resized, grayscale image and apply template  
        # matching to find the template in the image 
        edged = cv2.Canny(resized, 50, 200)
        result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
        (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result) 
        # if we have found a new maximum correlation value, then update 
        # the found variable if found is None or maxVal > found[0]: 
        if resized.shape[0] < h or resized.shape[1] < w: 
                break
        found = (maxVal, maxLoc, r) 
    
    # unpack the found varaible and compute the (x, y) coordinates 
    # of the bounding box based on the resized ratio 
    (_, maxLoc, r) = found 
    (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r)) 
    (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r)) 
    
    # draw a bounding box around the detected result and display the image 
    cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2) 
    cv2.imshow("Image", image) 
    cv2.waitKey(0) 
