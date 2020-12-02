import cv2
import numpy as np
import math
import matplotlib.pyplot as plt
from vision_utils import *


def get_path(img):
    height, width, _ = img.shape
    height_ratio, width_ratio = 400/height, 400/width
    def update(x):
            pass

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray,3,75,75)
    # Tuning Edge Parameter
    # Tuning start
    tuning_window_name = 'tuner'
    cv2.namedWindow(tuning_window_name)
    cv2.createTrackbar('canny_upper_threshold',tuning_window_name,100,300,update)
    cv2.createTrackbar('canny_lower_threshold',tuning_window_name,60,300,update)
    cv2.createTrackbar('dilate_iteration',tuning_window_name,1,50,update)
    while(1):
        canny_lower_threshold = cv2.getTrackbarPos('canny_lower_threshold',tuning_window_name)
        canny_upper_threshold = cv2.getTrackbarPos('canny_upper_threshold',tuning_window_name)
        dilate_iteration = cv2.getTrackbarPos('dilate_iteration',tuning_window_name)        
        edge = cv2.Canny(blur,canny_lower_threshold,canny_upper_threshold)
        dilate = cv2.dilate(edge, None,iterations = dilate_iteration)
        cv2.rectangle(dilate, (0,0), (width,height), 0, 1)
        cv2.imshow(tuning_window_name,cv2.hconcat([edge,dilate]))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
    # Tuning end
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    outside_contours = []
    inside_contours = []
    gradient_original = np.zeros(dilate.shape, dtype = np.uint8)
    outside_contour_original =  np.zeros(dilate.shape, dtype = np.uint8)
    for con,hie in zip(contours,hierarchy[0]):
            if hie[3] == -1:
                outside_contours.append(con)
            if hie[2] == -1:
                inside_contours.append(con)
    cv2.drawContours(gradient_original, inside_contours, -1, (255,255,255), -1)
    cv2.drawContours(outside_contour_original, outside_contours, -1, (255,255,255), -1)
    cv2.imshow('Contours',cv2.hconcat([gradient_original,outside_contour_original]))
    cv2.waitKey(0)
    # remove small things tuning
    cv2.namedWindow(tuning_window_name)
    cv2.createTrackbar('area_threshold_inside',tuning_window_name,1000,5000,update)
    cv2.createTrackbar('area_threshold_outside',tuning_window_name,0,5000,update)
    while(1):
        area_threshold_inside  = cv2.getTrackbarPos('area_threshold_inside',tuning_window_name)*10
        area_threshold_outside = cv2.getTrackbarPos('area_threshold_outside',tuning_window_name)*10
        gradient = remove_small_area(gradient_original,area_threshold_inside)
        gradient = cv2.erode(gradient,None,10)
        outside_contour = remove_small_area(outside_contour_original,area_threshold_inside)
        cv2.imshow(tuning_window_name,cv2.hconcat([gradient,outside_contour]))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
    greater_gradient = cv2.dilate(gradient, None,iterations = 16)
    symbol_only = cv2.subtract(outside_contour,greater_gradient)
    symbol_only = remove_small_area(symbol_only,500)
    cv2.imshow('symbol',symbol_only)
    cv2.waitKey(0)
    symbol_centroid_list = get_contour_centroid_list(symbol_only)
    for cen in symbol_centroid_list:
        cv2.circle(symbol_only,cen,5,0,5)
    cv2.imshow('checker_center_of_symbol',symbol_only)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    semi_gradient_path = cv2.bitwise_and(cv2.ximgproc.thinning(outside_contour),cv2.erode(gradient,np.ones((6, 6), np.uint8) ,5))
    test_semi_path = cv2.add(gray,semi_gradient_path)
    cv2.imshow('gradient_path',test_semi_path)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # ถ้ามีปัญหาเปลี่ยนไปใช้หาจุดใกล้จุดเอา
    semi_path_end_points_list = find_endpoints(semi_gradient_path)
    full_path = semi_gradient_path.copy()
    for centroid_symbol in symbol_centroid_list:
        for end_semi_points in semi_path_end_points_list:
            if check_in_region(centroid_symbol,end_semi_points,4000):
                cv2.line(full_path,centroid_symbol,(end_semi_points[1],end_semi_points[0]),255,1)
    cv2.imshow('gradient_path',full_path)
    cv2.waitKey(0)
    full_gradient_path = cv2.bitwise_and(full_path,gradient)
    path_no_height = full_path - full_gradient_path
    seperate_gradient = seperate_contour(gradient)
    cv2.imshow('fuck',path_no_height)
    cv2.waitKey(0)
    # share same index
    pixel_have_path = []
    height_list = []
    X = []
    Y = []
    Z = []
    # 
    gray = gray
    gray = cv2.medianBlur(gray,5)
    gray = cv2.fastNlMeansDenoising(gray, None,3,7,21)
    for count_gradient in range(len(seperate_gradient)):
        seperate_gradient_and_thin_path = cv2.bitwise_and(full_gradient_path,seperate_gradient[count_gradient])
        min_intensity,max_intensity = find_minmax_intensity(gray,seperate_gradient[count_gradient])
        if (max_intensity-min_intensity < 5):
            path_no_height = cv2.bitwise_or(path_no_height,seperate_gradient_and_thin_path)
            continue
        all_white_pixel = np.argwhere(seperate_gradient_and_thin_path == 255)
        for pix_location in all_white_pixel:
            height = map_value(gray[pix_location[0],pix_location[1]],min_intensity,max_intensity,20,10)
            height_list.append(height)
            pixel_have_path.append(list(pix_location))
    tailpoint_thinning = find_endpoints(full_path)
    now_point = list(tailpoint_thinning[0])
    prev_point = now_point.copy()
    n_path_array = list(np.argwhere(full_path == 255))
    path_array = []
    for i in n_path_array:
        path_array.append(list(i))
    buffer_arr = []
    last_height = None
    prev_point_array = []
    while(1):
        now_x,now_y = now_point[0],now_point[1]
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
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(X, Y, Z, c='r', marker='o')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    plt.show()
    full_path_coordinate = []
    # yz_gray = np.zeros(gray.shape, np.uint8)
    # buffer_yz = (int(Y[0]/height_ratio),int(map_value(Z[0],10,20,0,width)))
    for x,y,z in zip(X,Y,Z):
        full_path_coordinate.append([x,y,z])
        # create y-z
    #     point = (int(y/height_ratio),int(map_value(z,10,20,0,width)))
    #     cv2.line(yz_gray,buffer_yz,point,255,1)
    #     buffer_yz = point
    # cv2.imshow('fame',yz_gray)
    # cv2.waitKey(0)

    # contours, hierarchy = cv2.findContours(yz_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # significant_points = []
    # print(len(contours))
    # for cnt in contours:
    #     epsilon = 0.025*cv2.arcLength(cnt,True)
    #     approx = cv2.approxPolyDP(cnt,epsilon,True)
    #     for point in approx:
    #         significant_points.append(point[0])
    #         cv2.circle(yz_gray,tuple(point[0]),15,128)
    #         print(len(approx))
    # cv2.imshow('fame',yz_gray)
    # cv2.waitKey(0)

    contours, hierarchy = cv2.findContours(full_gradient_path, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    significant_points_xy = []
    for cnt in contours:
        epsilon = 0.02*cv2.arcLength(cnt,True)
        approx = cv2.approxPolyDP(cnt,epsilon,True)
        for point in approx:
            significant_points_xy.append(point[0])
            cv2.circle(full_path,tuple(point[0]),5,128)
    cv2.circle(full_path,(tailpoint_thinning[0][1],tailpoint_thinning[0][0]),5,128)
    cv2.circle(full_path,(tailpoint_thinning[-1][1],tailpoint_thinning[-1][0]),5,128)
    significant_points_xy.append((tailpoint_thinning[0][1],tailpoint_thinning[0][0]))
    significant_points_xy.append((tailpoint_thinning[-1][1],tailpoint_thinning[-1][0]))
    cv2.imshow('fame',full_path)    
    cv2.waitKey(0)

    # transform to realworld unit
    for idx in range(len(significant_points_xy)):
        new_x_y = []
        new_x_y.append(significant_points_xy[idx][0])
        new_x_y.append(significant_points_xy[idx][1])
        significant_points_xy[idx] = new_x_y
    print(significant_points_xy)

    new_X = []
    new_Y = []
    new_Z = []
    line_path_point = []
    for path_point in full_path_coordinate:
        for signi_point in significant_points_xy:
            if (signi_point[1] == path_point[0]/width_ratio) and (signi_point[0] == path_point[1]/height_ratio):
                print('fame')
                line_path_point.append([path_point[0],path_point[1],path_point[2]])
                new_X.append(path_point[0])
                new_Y.append(path_point[1])
                new_Z.append(path_point[2]*10)
    print(new_X)
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot(new_X, new_Y, new_Z, label='parametric curve')
    ax.legend()
    plt.show()

    angle_list = []
    now_point = [0,0]
    for point in line_path_point:
        pass
    line_path_point_np = np.array(line_path_point)
    print(line_path_point_np)
    np.save('numpy_arr/path_xyz.npy', line_path_point_np)

if __name__ == '__main__':
    maze = cv2.imread('images/process_data/test8.png')
    get_path(maze)