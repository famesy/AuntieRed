import numpy as np
import math
import matplotlib.pyplot as plt

def path2pointanddeg(X,Y,Z,find_another_angle = 1):
    '''
    filter pos
    '''
    angle_list = []
    xyz_list = []
    previous_pos = [0,0,0]
    previous_angle = 0
    for x,y,z in zip(X,Y,Z):
        now_pos = [x[0],y[0],z[0]]
        diff_x = now_pos[0]-previous_pos[0]
        diff_y = now_pos[1]-previous_pos[1]
        if (diff_x**2 + diff_y**2)**(0.5) < 5:
            continue
        angle = math.degrees(math.atan2(diff_y, diff_x))
        if angle < 0:
            angle += 360
        '''
        find another possible angle
        '''
        find_another_angle = 1
        if (find_another_angle):
            if angle > 180:
                another_angle = angle - 180
            else:
                another_angle = angle + 180

            if abs(previous_angle - another_angle) < abs(previous_angle - angle):
                angle = another_angle
        print('dif x = {} dif y = {}'.format(diff_x, diff_y))
        print('angle = {}'.format(angle))
        xyz_list.append([x[0],y[0],z[0]])
        angle_list.append(angle)
        previous_pos = now_pos
        previous_angle = angle
    return xyz_list,angle_list
        
    #     print('angle', angle)
    # previous_pos = [0,0]
    # angle_list = []
    # for x,y in zip(X,Y):
    #     now_pos = [x[0],y[0]]
    #     angle = math.degrees(math.atan2(now_pos[1]-previous_pos[1], now_pos[0]-previous_pos[0]))
    #     print('dif x = {} dif y = {}'.format(now_pos[1]-previous_pos[1], now_pos[0]-previous_pos[0]))
    #     print('angle', angle)
    #     previous_pos = now_pos
    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(X, Y, Z, c='r', marker='o')
    # ax.set_xlabel('X Label')
    # ax.set_ylabel('Y Label')
    # ax.set_zlabel('Z Label')
    # plt.show()

path = list(np.load('numpy_arr/path_xyz.npy'))
X = []
Y = []
Z = []
for i in path:
    X.append([i[0]])
    Y.append([i[1]])
    Z.append([i[2]])

xyz_list,angle_list = path2pointanddeg(X,Y,Z)
print(angle_list)