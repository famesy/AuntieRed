import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt
from cv2 import aruco
from utils import *

class Camera:
    def __init__(self,port):
        if (port != None):
            try:
                self.cam = cv2.VideoCapture(port, cv2.CAP_DSHOW)
                self.cam.set(3, 1920)
                self.cam.set(4, 1080)
            except:
                print("error occur")
    
    def get_pic(self):
        ret, frame = self.cam.read()
        return frame
    
    def take_pic(self):
        while 1:
            ret, frame = self.cam.read()
            frame_2 = frame.copy()
            x_1,y_1 = 520,320
            x_2,y_2 = 700,500
            cv2.rectangle(frame_2, (x_1,y_1), (x_2,y_2), (255,0,255), 1) 
            cv2.imshow('show',frame_2)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                return frame[y_1:y_2,x_1:x_2]

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
        def update(x):
            pass
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
        cv2.imwrite('images/process_data/test.png',bgr)
        bgr = cv2.imread('images/process_data/test.png')
        print(bgr.shape)
        cv2.imshow('abc',bgr)
        cv2.waitKey(0)
        cv2.namedWindow('Tuning')
        cv2.createTrackbar('crop_percent_t','Tuning',1000,1000,update)
        cv2.createTrackbar('crop_percent_b','Tuning',1000,1000,update)
        cv2.createTrackbar('crop_percent_r','Tuning',1000,1000,update)
        cv2.createTrackbar('crop_percent_l','Tuning',1000,1000,update)
        while(1):
            crop_percent_t = cv2.getTrackbarPos('crop_percent_t','Tuning')/1000
            crop_percent_b = cv2.getTrackbarPos('crop_percent_b','Tuning')/1000
            crop_percent_r = cv2.getTrackbarPos('crop_percent_r','Tuning')/1000
            crop_percent_l = cv2.getTrackbarPos('crop_percent_l','Tuning')/1000
            abc = crop_img(bgr,crop_percent_t,crop_percent_b,crop_percent_r,crop_percent_l)
            cv2.imshow('Tuning',abc)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        img_flip_lr = cv2.flip(abc, 1)
        img_rotate_90_counterclockwise = cv2.rotate(img_flip_lr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        cv2.destroyAllWindows()
        cv2.imwrite('images/process_data/test.png',img_rotate_90_counterclockwise)
        cv2.waitKey(0)

    def get_path(self,img,canny_lower_threshold,canny_upper_threshold,dilate_iteration):
        original_img = img
        height, width, _ = original_img.shape
        height_ratio, width_ratio = 40/height, 40/width
        gray_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
        gray_img_v2 = cv2.medianBlur(gray_img,5)
        gray_img_v2 = cv2.fastNlMeansDenoising(gray_img_v2, None,3,7,21)
        edge_img = cv2.Canny(gray_img,canny_lower_threshold,canny_upper_threshold)
        dilate_img = cv2.dilate(edge_img,None,iterations = dilate_iteration)
        blank = np.zeros(gray_img.shape)
        cv2.imshow('test',edge_img)
        cv2.waitKey(0)
        cv2.imshow('test',dilate_img)
        cv2.waitKey(0)
        contours, hierarchy = cv2.findContours(dilate_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        outside_contours = []
        inside_contours = []
        gradient_tab = blank.copy()
        external_maze = blank.copy()
        for con,hie in zip(contours,hierarchy[0]):
            if hie[3] == -1:
                outside_contours.append(con)
            if hie[2] == -1:
                inside_contours.append(con)
        cv2.drawContours(gradient_tab, inside_contours, -1, (255,255,255), -1)
        cv2.drawContours(external_maze, outside_contours, -1, (255,255,255), -1)
        gradient = remove_small_area(gradient_tab,7000)
        external_maze = remove_small_area(external_maze,7000)
        cv2.imshow('test',gradient)
        cv2.waitKey(0)
        cv2.imshow('test',external_maze)
        cv2.waitKey(0)
        external_maze = simplify_contour(external_maze)
        thin_path = cv2.ximgproc.thinning(external_maze)
        thin_gradient = cv2.bitwise_and(gradient,thin_path)
        seperate_gradient_img = seperate_contour(gradient)
        path_no_height = thin_path - thin_gradient
        tailpoint_thinning = find_endpoints(thin_path)
        X = []
        Y = []
        Z = []
        height_list = []
        pixel_have_path = []
        for cnt_gradient in range(len(seperate_gradient_img)):
            seperate_gradient_and_thin_path = cv2.bitwise_and(thin_path,seperate_gradient_img[cnt_gradient])
            min_intensity,max_intensity = find_minmax_intensity(gray_img_v2,seperate_gradient_img[cnt_gradient])
            if (max_intensity-min_intensity < 5):
                path_no_height = cv2.bitwise_or(path_no_height,seperate_gradient_and_thin_path)
                continue
            all_white_pixel = np.argwhere(seperate_gradient_and_thin_path == 255)
            for pix_location in all_white_pixel:
                height = map_value(gray_img_v2[pix_location[0],pix_location[1]],min_intensity,max_intensity,20,10)
                height_list.append(height)
                pixel_have_path.append(list(pix_location))
        now_point = list(tailpoint_thinning[0])
        prev_point = now_point.copy()
        n_path_array = list(np.argwhere(thin_path == 255))
        path_array = []
        for i in n_path_array:
            path_array.append(list(i))
        buffer_arr = []
        last_height = None
        prev_point_array = []
        while(1):
            now_x,now_y = now_point[0],now_point[1]
            print(now_x,now_y)
            checker = [[now_x+1,now_y],[now_x-1,now_y],[now_x,now_y+1],[now_x,now_y-1],
                        [now_x+1,now_y+1],[now_x+1,now_y-1],[now_x-1,now_y+1],[now_x-1,now_y-1],]
            for check in checker:
                if (check != prev_point) and (check in path_array) and (check not in prev_point_array):
                    prev_point = now_point.copy()
                    prev_point_array.append(prev_point)
                    now_point = check.copy()
                    buffer_arr.append(check)
                    if (check in pixel_have_path):
                        height_idx = pixel_have_path.index(check)
                        for pix in buffer_arr:
                            X.append(pix[0]*width_ratio)
                            Y.append(pix[1]*height_ratio)
                            Z.append(height_list[height_idx])
                        last_height = height_list[height_idx]
                        buffer_arr= []
                    break
            if (np.array(now_point) == np.array(tailpoint_thinning[1])).all():
                for pix in buffer_arr:
                            X.append(pix[0]*width_ratio)
                            Y.append(pix[1]*height_ratio)
                            Z.append(last_height)
                break
        
        # sampling every 40 pixel
        new_X = [X[0]]
        new_Y = [Y[0]]
        new_Z = [Z[0]]
        for i in range(1,len(X)-1):
            if (i%30 == 0):
                new_X.append(X[i])
                new_Y.append(Y[i])
                new_Z.append(Z[i])

        new_X.append(X[-1])
        new_Y.append(Y[-1])
        new_Z.append(Z[-1])

        goal = cv2.imread('chess.png')
        goal_pos = match_symbol(original_img,goal)
        tester1 = np.sqrt((X[0] - goal_pos[0]) ** 2 + (Y[0] - goal_pos[1]) ** 2)
        tester2 = np.sqrt((X[-1] - goal_pos[0]) ** 2 + (Y[-1] - goal_pos[1]) ** 2)
        if (min(tester1,tester2) == tester1):
            new_X.reverse()
            new_Y.reverse()
            new_Z.reverse()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(new_X, new_Y, new_Z, c='r', marker='o')
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')
        plt.show()
        
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
    cam = Camera(1)
    cam.median_multiple_images()
    # num = 0
    # # for name in glob.glob('images/raw_data/*.jpg'):
    #     # im = cv2.imread(name)
    # #     im = cam.perspectrive_with_aruco(im)
    # #     num += 1
    # #     im = cv2.imwrite('images/raw_data_2/{}.jpg'.format(num),im)
    # pic = cam.take_pic()
    # cv2.imshow('test',pic)
    # cv2.imwrite('images/symbols/symbol.png',pic)
    # cv2.waitKey(0)
    # # im = cv2.imread('images/process_data/test2.png')
    # # canny_lower_threshold,canny_upper_threshold,dilate_iteration = cam.image_tuning(im)
    # # cam.get_path(im,canny_lower_threshold,canny_upper_threshold,dilate_iteration)