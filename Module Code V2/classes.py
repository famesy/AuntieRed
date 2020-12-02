import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt
from cv2 import aruco
from utils import *

class Camera:
    def __init__(self,port):
        if (port != None):
            self.cam = cv2.VideoCapture(port, cv2.CAP_DSHOW)
            self.cam.set(cv2.CV_CAP_PROP_FRAME_WIDTH, 1920)
            self.cam.set(cv2.CV_CAP_PROP_FRAME_HEIGHT, 1080)
    
    def get_pic(self):
        ret, frame = self.cam.read()
        return frame
        
    def perspectrive_with_aruco(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        line_checker = np.zeros(gray.shape, np.uint8)
        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        parameters =  aruco.DetectorParameters_create()
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        # aruco ids
        top_row =    [16,15,14,13,12]
        left_row =   [16,1,2,3,4]
        right_row =  [12,11,10,9,8]
        bottom_row = [4,5,6,7,8]
        all_rows = []
        lines = []
        for row in [top_row,left_row,right_row,bottom_row]:
            original_row = row.copy()
            set_of_id = set([num[0] for num in ids.tolist()])
            row = list(set(row).intersection(set_of_id))
            row = [ele for ele in original_row if ele in row]
            if (len(row) < 2):
                return None
            all_rows.append([row[0],row[-1]])
        for end_points_ids in all_rows:
            start_point_corners = corners[[num[0] for num in ids.tolist()].index(end_points_ids[0])][0]
            end_points_corners  = corners[[num[0] for num in ids.tolist()].index(end_points_ids[1])][0]
            start_point =   (int((start_point_corners[0][0] + start_point_corners[1][0] + start_point_corners[2][0] + start_point_corners[3][0]) / 4),
                            int((start_point_corners[0][1] + start_point_corners[1][1] + start_point_corners[2][1] + start_point_corners[3][1]) / 4))
            end_point =     (int((end_points_corners[0][0] + end_points_corners[1][0] + end_points_corners[2][0] + end_points_corners[3][0]) / 4),
                            int((end_points_corners[0][1] + end_points_corners[1][1] + end_points_corners[2][1] + end_points_corners[3][1]) / 4))
            lines.append([start_point,end_point])
        top_left     = line_intersection(lines[0], (lines[1]))
        top_right    = line_intersection(lines[0],(lines[2]))
        bottom_left  = line_intersection(lines[3],(lines[1]))
        bottom_right = line_intersection(lines[3],(lines[2]))
        pts1 = np.float32([top_left,top_right,bottom_left,bottom_right])
        pts2 = np.float32([[0, 0], [0, 400], [400, 0], [400, 400]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        result = cv2.warpPerspective(img, matrix, (400, 400))
        return result

    def median_multiple_images(self):
        b_list = []
        g_list = []
        r_list = []
        for name in glob.glob('images/raw_data_2/*.png'):
            img = cv2.imread(name)
            print(img[0].shape)
            b_list.append(img[:,:,0])
            g_list.append(img[:,:,1])
            r_list.append(img[:,:,2])
        b_list = np.asarray(b_list)
        g_list = np.asarray(g_list)
        r_list = np.asarray(r_list)
        b_med = np.median(b_list, axis=0)
        g_med = np.median(g_list, axis=0)
        r_med = np.median(r_list, axis=0)
        bgr = np.dstack((b_med,g_med,r_med))
        print(bgr.shape)
        bgr = crop_img(bgr,0.9)
        cv2.imwrite('images/process_data/test.png',bgr)
        cv2.waitKey(0)

    def image_tuning(self,img_bruh):
        img_bruh = cv2.resize(img_bruh,(400,400))
        def update(x):
            pass
        img = np.zeros((1500,1500,3), np.uint8)
        cv2.namedWindow('Tuning')
        cv2.createTrackbar('canny_upper_threshold','Tuning',160,300,update)
        cv2.createTrackbar('canny_lower_threshold','Tuning',30,300,update)
        cv2.createTrackbar('dilate_iteration','Tuning',2,50,update)
        while(1):
            canny_lower_threshold = cv2.getTrackbarPos('canny_lower_threshold','Tuning')
            canny_upper_threshold = cv2.getTrackbarPos('canny_upper_threshold','Tuning')
            dilate_iteration = cv2.getTrackbarPos('dilate_iteration','Tuning')
            img_test = cv2.bilateralFilter(img_bruh,9,75,75).copy()
            
            gray_img = cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY)
            edge_img = cv2.Canny(gray_img,canny_lower_threshold,canny_upper_threshold)
            dilate_img = cv2.dilate(edge_img,None,iterations = dilate_iteration) 
            cv2.imshow('Tuning',cv2.hconcat([edge_img, dilate_img]))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        return canny_lower_threshold,canny_upper_threshold,dilate_iteration


if __name__ == '__main__':
    cam = Camera(None)
    num = 0
    # for name in glob.glob('images/raw_data/*.jpg'):
    # im = cv2.imread(name)
    #     im = cam.perspectrive_with_aruco(im)
    #     num += 1
    #     im = cv2.imwrite('images/raw_data_2/{}.jpg'.format(num),im)
    cam.median_multiple_images()
    # im = cv2.imread('images/process_data/test2.png')
    # canny_lower_threshold,canny_upper_threshold,dilate_iteration = cam.image_tuning(im)
    # cam.get_path(im,canny_lower_threshold,canny_upper_threshold,dilate_iteration)