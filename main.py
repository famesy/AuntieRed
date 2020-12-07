import serial
import threading
import time
import math
import cv2
import sys
import os
from utils import *
from cammy import Camera
from pyfiglet import Figlet
from lazyme.string import color_print
from func import * 
# ['pink', 'yellow', 'cyan', 'magenta', 'blue', 'gray', 'default', 'black', 'green', 'white', 'red']
# ['blue', 'pink', 'gray', 'black', 'yellow', 'cyan', 'green', 'magenta', 'white', 'red']
# ['hide', 'bold', 'italic', 'default', 'fast_blinking', 'faint', 'strikethrough', 'underline', 'blinking', 'reverse']
class Robot:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.scale = 1.10
        self.off_x = 0
        self.off_y = 8
        self.z = 600
        self.pic_enable = 0
        self.arduino_enable = 0
    def connect_to_pic(self,port,baudrate):
        self.ser_pic = serial.Serial(port = port,
                                    baudrate = baudrate,
                                    bytesize = serial.EIGHTBITS, 
                                    parity = serial.PARITY_NONE,
                                    stopbits = serial.STOPBITS_ONE,
                                    timeout = 0.5
                                    )
        self.ser_pic.rts = 0
        self.ser_pic.flushInput()
        self.ser_pic.flushOutput()
        self.pic_enable = 1
    def connect_to_arduino(self,port,baudrate):
        self.ser_arduino = serial.Serial(port = port,
                                    baudrate = baudrate,
                                    timeout = 0.5
                                    )
        time.sleep(1)
        self.ser_arduino.flushInput()
        self.ser_arduino.flushOutput() 
        self.arduino_enable = 1
    def read_data(self,device):
        if device == 'pic':
            message_pic = self.ser_pic.readline().strip().decode('ascii')
            return message_pic
        if device == 'arduino':
            message_arduino = self.ser_arduino.readline().strip().decode('ascii')
            return message_arduino
    def go_to(self,x = None,y = None,z = None,tau = None,unit = 'mm'):
        finish_status_pic = 1
        finish_status_arduino = 1
        if (x == None):
            x = self.x
        if (y == None):
            y = self.y
        if (z == None):
            z = self.z
        print(self.x, x)
        print(self.y, y)
        if self.pic_enable and (not((self.x == x) & (self.y == y))):
            finish_status_pic = 0
            previous_x = mm2pulse(self.x)
            previous_y = mm2pulse(self.y)
            if unit == 'mm':
                self.x = x
                self.y = y
                x = mm2pulse(x)
                y = mm2pulse(y)
            if unit == 'pulse':
                self.x = pulse2mm(x)
                self.y = pulse2mm(y)
            packet = bytearray(b'\xff')
            packet.extend((1).to_bytes(1, byteorder='big'))
            packet.extend((x).to_bytes(2, byteorder='big'))
            packet.extend((y).to_bytes(2, byteorder='big'))
            packet.extend((1).to_bytes(1, byteorder='big'))
            if tau == None:
                print(mm2pulse(self.x),mm2pulse(self.y),x,y)
                tau = int(cal_time(previous_x,previous_y,x,y)*100)
            print('this is tau',tau)
            self.ser_pic.flushInput()
            self.ser_pic.flushOutput() 
            self.ser_pic.write(packet)
        if self.arduino_enable and (self.z != z):
            finish_status_arduino = 0
            if (not self.pic_enable) | (tau == None):
                tau = 500
            if tau < 300:
                tau = 300
            self.z = z
            z = z * 10
            packet = bytearray(b'\xff\x01')
            packet.extend((z).to_bytes(2, byteorder='big'))
            packet.extend((255).to_bytes(2, byteorder='big'))
            packet.extend((tau).to_bytes(2, byteorder='big'))
            self.ser_arduino.flushInput()
            self.ser_arduino.flushOutput() 
            self.ser_arduino.write(packet)
        start = time.time()
        while(1):
            now = time.time()
            print(finish_status_pic,finish_status_arduino)
            if (now -start) > 15:
                break
            if (self.pic_enable):
                message_pic = self.ser_pic.readline().decode('ascii').strip()
                # if (message_pic == 'Already position'):
                print(message_pic)
                if len(message_pic) > 5:
                    finish_status_pic = 1
            if (self.arduino_enable):
                message_arduino = self.ser_arduino.readline().decode('ascii').strip()
                print(message_arduino)
                # if (message_arduino == 'ZArrived'):
                if len(message_arduino) > 5:
                    finish_status_arduino = 1
            if ((finish_status_pic & finish_status_arduino) == 1):
                    break            
    def set_home(self):
        if (self.arduino_enable):
            self.ser_arduino.write(bytes([255, 0, 255, 1, 0 ,0,0 ,0]))
            self.z = 600
            while(1):
                message_arduino = self.ser_arduino.readline()
                if (message_arduino.strip().decode('ascii') == 'sethome'):
                    break
        if (self.pic_enable):
            packet = bytearray(b'\xff\x00')
            self.ser_pic.write(packet)
            self.x = 0
            self.y = 0
            while(1):
                message_pic = self.ser_pic.readline()
                if (message_pic.strip().decode('ascii') == 'Set Home'):
                # if len(message_pic.strip().decode('ascii')) > 6:
                    break
            self.timer_on()
    def timer_on(self):
        self.ser_pic.write(b'\xff\x02')
    def reset(self):
        if (self.pic_enable):
            self.ser_pic.rts = 1
            self.ser_pic.rts = 0
        if (self.arduino_enable):
            self.ser_arduino.dtr = 0
            time.sleep(0.25)
            self.ser_arduino.dtr = 1
            time.sleep(1)
    def get_rod(self):
        if (self.arduino_enable and self.pic_enable):
            self.ungrip()
            self.go_to(z=600,tau=300)
            self.go_to(x=1536,y=7373,unit='pulse')
            self.go_to(z=210,tau=500)
            time.sleep(0.5)
            self.grip()
            time.sleep(0.5)
            self.go_to(z=600,tau=500)
    def grip(self):
        if self.arduino_enable:
            self.ser_arduino.flushInput()
            self.ser_arduino.flushOutput() 
            self.ser_arduino.write(bytes([255, 2, 18, 19, 0 ,0,0 ,0]))
            start = time.time()
            while(1):
                now = time.time()
                if (now -start) > 10:
                    break
                message_arduino = self.ser_arduino.readline()
                if len((message_arduino.strip().decode('ascii'))) > 3:
                    break
    def ungrip(self):
        if self.arduino_enable:
            self.ser_arduino.flushInput()
            self.ser_arduino.flushOutput() 
            self.ser_arduino.write(bytes([255, 3, 18, 19, 0 ,0,0 ,0]))
            start = time.time()
            while(1):
                now = time.time()
                if (now -start) > 10:
                    break
                message_arduino = self.ser_arduino.readline()
                if len((message_arduino.strip().decode('ascii'))) > 2:
                    break
    def place_rod(self):
        if (self.arduino_enable and self.pic_enable):
            self.rotate(0)
            self.grip()
            self.go_to(z=600,tau=500)
            self.go_to(x=1550,y=7373,unit='pulse')
            self.go_to(z=225,tau=500)
            time.sleep(0.5)
            self.ungrip()
            time.sleep(0.5)
            self.go_to(z=600,tau=500)
    def rotate(self,deg,tau = 500):
        if (self.arduino_enable):
            packet = bytearray(b'\xff\x04')
            packet.extend((self.z).to_bytes(2, byteorder='big'))
            packet.extend((deg).to_bytes(2, byteorder='big'))
            packet.extend((tau).to_bytes(2, byteorder='big'))
            self.ser_arduino.flushInput()
            self.ser_arduino.flushOutput() 
            self.ser_arduino.write(packet)
            start = time.time()
            while(1):
                now = time.time()
                if (now -start) > 3:
                    break
                    message_arduino = self.ser_arduino.readline().decode('ascii').strip()
                    if (message_arduino == 'RotateArrived') or (len(message_arduino.strip().decode('ascii')) > 6):
                    # if len(message_arduino.strip().decode('ascii')) > 6:
                        break
    def get_image(self):
        self.camera = Camera(port = 1)
        for x in [20, 50, 75]:
            for y in range(40,361,60):
                print('(go to {},{})'.format(x,y))
                self.go_to(x,y,600)
                time.sleep(1)
                pic = self.camera.get_pic()
                # cv2.imshow("test",pic)
                # print(pic)
                # cv2.imwrite('images/raw_data_2/{}_{}.png'.format(x, y),pic)
                try:
                    pic = self.camera.perspectrive_with_aruco(pic)
                    cv2.imwrite('images/raw_data_2/{}_{}.png'.format(x, y),pic)
                except:
                    print('fail')
                time.sleep(1)
        self.camera.median_multiple_images()
    def symbol_for_wtf(self):
        def update(arg):
            pass
        try:
            self.camera = Camera(port = 1)
        except:
            pass
        pic = self.camera.take_pic()
        print('fame')
        map_img = cv2.imread('images/process_data/test.png')
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
            abc = crop_img(pic,crop_percent_t,crop_percent_b,crop_percent_r,crop_percent_l)
            cv2.imshow('Tuning',abc)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        x,y = match_symbol(map_img,abc)
        cv2.circle(map_img,(y,x),5,(255,0,255),10)
        cv2.imshow('fucker',map_img)
        cv2.waitKey(0)
        # except:
            # print('fucking noob bobo putang inamo')
padang = Robot()
position_stack = []
state = 0
def input_cui():
    global state
    play_sound('start')
    time.sleep(3)
    color_print('Welcome How Can I Serve You?',color='green',underline=True)
    while(True):
        # os.system('cls')
        color_print(Figlet(font='slant').renderText('PADANG  NO . 1'),color='red',bold=True)
        color_print('Main Menu', color='red',bold = True,underline = True)
        color_print('0 : Connect To PIC & Arduino', color='yellow')
        color_print('1 : Set Home', color='green')
        color_print('2 : Set Position', color='cyan')
        color_print('3 : Reset', color='blue')
        color_print('4 : Get Picture And Median', color='pink')
        color_print('5 : Find Path', color='magenta')
        color_print('6 : Path Following', color='red')
        color_print('7 : Set Offset', color='yellow')
        color_print('8 : Exit', color='green')
        ans = input("Ans = ")
        if( ans != '3'):
            play_sound('menu')
        if ans == '0':
            try:
                padang.connect_to_pic('COM6',115200)
                color_print('Connect To PIC Success!!',color='green')
            except:
                try:
                    if (padang.ser_arduino.isOpen()):
                        color_print('Already Connect To PIC',color='green')
                    else:
                        color_print('Pls Connect To PIC!!',color='red')
                except:
                    color_print('Connect To PIC FAIL!!',color='red')
            try:
                padang.connect_to_arduino('COM3',38400)
                color_print('Connect To Arduino Success!!',color='green')
            except:
                try:
                    padang.connect_to_arduino('COM10',38400)
                    color_print('Connect To Arduino Success!!',color='green')
                except:
                    try:
                        if (padang.ser_arduino.isOpen()):
                            color_print('Already Connect To Arduino',color='green')
                        else:
                            color_print('Pls Connect To Arduino!!',color='red')
                    except:
                        color_print('Connect To Arduino FAIL!!',color='red')
        time.sleep(1)
        if ans == '1':
            state = 1
        if ans == '2':
            color_print('Enter Your Position',color='green', underline = True, bold = True)
            if (padang.pic_enable):
                x = int(input("X :"))
                y = int(input("Y :"))
            if (padang.arduino_enable):
                z = int(input("Z :"))
            if (padang.pic_enable and padang.arduino_enable):
                position_stack.append([x,y,z])
            elif (padang.pic_enable):
                position_stack.append([x,y,padang.z])
            elif (padang.arduino_enable):
                position_stack.append([padang.x,padang.y,z])
            state = 2
        if ans == '3':
            play_sound('reset')
            padang.reset()
            state = 0
        if ans == '4':
            state = 4
        if ans == '5':
            img = cv2.imread('images/process_data/test.png')
            get_path(img,plot=False)
        if ans == '6':
            state = 3
        if ans == '7':
            padang.off_x = int(input("X :"))
            padang.off_y = int(input("Y :"))
            padang.off_y = float(input("Scale :"))
        if ans == '8':
            sys.exit()
        if ans == '9':
            padang.grip()
        if ans == '10':
            padang.symbol_for_wtf()

if __name__ == '__main__':
    cui = threading.Thread(target=input_cui, daemon=True)
    cui.start()
    while(1):
        if state == 1:
            padang.set_home()
            state = 0
        if state == 2:
            pos = position_stack.pop(0)
            padang.go_to(pos[0],pos[1],pos[2])
            play_sound("end")
            state = 0
        if state == 3:
            play_sound('start')
            padang.get_rod()
            path = list(np.load('numpy_arr/path_xyz.npy'))[::-1]
            X = []
            Y = []
            Z = []
            for i in path:
                X.append([i[0]])
                Y.append([i[1]])
                Z.append([i[2]])
            
            path,angles = path2pointanddeg(X,Y,Z)
            print(angles)
            # angles[0] = 0
            map_img_original = cv2.imread('images/process_data/test.png')
            padang.go_to(x = (path[0][0]*padang.scale) + padang.off_x ,y = (path[0][1]*padang.scale) + padang.off_y)
            try:
                map_img = map_img_original.copy()
                height_ratio,width_ratio = np.load('numpy_arr/ratio.npy')[0],np.load('numpy_arr/ratio.npy')[1]
                cv2.circle(map_img,(int(y/width_ratio),int(x/height_ratio)),5,(255,0,255),5)
                cv2.imshow('realtime pos',map_img)
                cv2.waitKey(1)
            except:
                print('error')
            padang.go_to(z=(int(path[0][2])*10+120),tau=500)
            # self.go_to(path[::-1][0][1]+127)
            padang.rotate(0)
            for xyz,angle in zip(path[1:],angles[1:]):
                padang.rotate(int(angle))
                x = int((xyz[0]*padang.scale)+padang.off_x)
                y = int((xyz[1]*padang.scale)+padang.off_y)
                z = int(xyz[2])*10
                try:
                    map_img = map_img_original.copy()
                    cv2.circle(map_img,(int(y/width_ratio),int(x/height_ratio)),5,(255,0,255),5)
                    cv2.imshow('realtime pos',map_img)
                    cv2.waitKey(1)
                except:
                    pass
                padang.go_to(x,y,z+120)
                time.sleep(0.25)
            play_sound('end')
            cv2.destroyAllWindows()
            for xyz,angle in zip(path[::-1][1:],angles[::-1][1:]):
                x = int((xyz[0]*padang.scale)+padang.off_x)
                y = int((xyz[1]*padang.scale)+padang.off_y)
                z = int(xyz[2])*10
                try:
                    map_img = map_img_original.copy()
                    cv2.circle(map_img,(int(y/width_ratio),int(x/height_ratio)),5,(255,0,255),5)
                    cv2.imshow('realtime pos',map_img)
                    cv2.waitKey(1)
                except:
                    pass
                padang.go_to(x,y,z+115)
                padang.rotate(int(angle))
                time.sleep(0.25)
            padang.place_rod()
            # self.reset()
            # time.sleep(1)
            # self.set_home()
            play_sound('end')
            state = 0
        if state == 4:
            padang.get_image()
            state = 0