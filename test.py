import cv2
from utils import *

def longest_skeletonize(img):
    # kernel = np.ones((30,30),np.uint8)
    # img = cv2.dilate(img,kernel,50)
    # cv2.imshow('fame',img)
    # cv2.waitKey(0)
    thin = cv2.ximgproc.thinning(img,1)
    endpoint_old = list(find_endpoints(thin))
    endpoint = []
    for point in endpoint_old:
        endpoint.append(list(point))
    for i in endpoint:
        cv2.circle(thin,(i[1],i[0]),5,255)
    # cv2.imshow('fame',thin)
    # cv2.waitKey(0)
    final_path = []
    for end_idx in range(len(endpoint)):
        now_point = endpoint[end_idx]
        n_path_array = list(np.argwhere(thin == 255))
        path_array = []
        for i in n_path_array:
            path_array.append(list(i))
        all_possible_path = [[now_point]]
        prev_point_list = [now_point]
        while 1:
            buff_all_possible_path = []
            for path in all_possible_path:
                now_point = path[-1]
                now_x,now_y = now_point[0],now_point[1]
                checker = [[now_x+1,now_y],[now_x-1,now_y],[now_x,now_y+1],[now_x,now_y-1],
                        [now_x+1,now_y+1],[now_x+1,now_y-1],[now_x-1,now_y+1],[now_x-1,now_y-1]]
                check_list =[]
                for point in checker:
                    if (point in path_array) and (point not in prev_point_list):
                        check_list.append(point)
                        prev_point_list.append(point)
                if len(check_list) > 0:
                    for i in check_list:
                        buff_path = path.copy()
                        buff_path.append(i)
                        buff_all_possible_path.append(buff_path)
            for buff_path in buff_all_possible_path:
                if buff_path[-1] in endpoint:
                    final_path.append(buff_path)
            if len(buff_all_possible_path) == 0:
                break
            all_possible_path = buff_all_possible_path.copy()
    max_length = max([len(path) for path in final_path])
    for i in final_path:
        if len(i) == max_length:
            path = i
            break
    map_blank = np.zeros(img.shape,np.uint8)
    for point in path:
        map_blank[point[0],point[1]] = 255
    return map_blank

if __name__ == '__main__':
    img = cv2.imread('full_path.png',0)
    kernel = np.ones((30,30),np.uint8)
    img = cv2.dilate(img,kernel,50)
    # cv2.imshow('fame',img)
    # cv2.waitKey(0)
    thin = cv2.ximgproc.thinning(img,1)
    endpoint_old = list(find_endpoints(thin))
    endpoint = []
    for point in endpoint_old:
        endpoint.append(list(point))
    for i in endpoint:
        cv2.circle(thin,(i[1],i[0]),5,255)
    # cv2.imshow('fame',thin)
    # cv2.waitKey(0)
    final_path = []
    for end_idx in range(len(endpoint)):
        now_point = endpoint[end_idx]
        n_path_array = list(np.argwhere(thin == 255))
        path_array = []
        for i in n_path_array:
            path_array.append(list(i))
        all_possible_path = [[now_point]]
        prev_point_list = [now_point]
        while 1:
            buff_all_possible_path = []
            for path in all_possible_path:
                now_point = path[-1]
                now_x,now_y = now_point[0],now_point[1]
                checker = [[now_x+1,now_y],[now_x-1,now_y],[now_x,now_y+1],[now_x,now_y-1],
                        [now_x+1,now_y+1],[now_x+1,now_y-1],[now_x-1,now_y+1],[now_x-1,now_y-1]]
                check_list =[]
                for point in checker:
                    if (point in path_array) and (point not in prev_point_list):
                        check_list.append(point)
                        prev_point_list.append(point)
                if len(check_list) > 0:
                    for i in check_list:
                        buff_path = path.copy()
                        buff_path.append(i)
                        buff_all_possible_path.append(buff_path)
            for buff_path in buff_all_possible_path:
                if buff_path[-1] in endpoint:
                    final_path.append(buff_path)
            if len(buff_all_possible_path) == 0:
                break
            all_possible_path = buff_all_possible_path.copy()
    max_length = max([len(path) for path in final_path])
    for i in final_path:
        if len(i) == max_length:
            path = i
            break
    map_blank = np.zeros(img.shape,np.uint8)
    for point in path:
        map_blank[point[0],point[1]] = 255
    cv2.imshow('result',map_blank)
    cv2.waitKey(0)
    # longest_skeletonize(img)