import serial
import threading
import time
import math
import cv2
import random
import sys
import os
from utils import *
from cammy import Camera
from pyfiglet import Figlet
from lazyme.string import color_print
from path_generator import * 
using_symbol = False
# ['pink', 'yellow', 'cyan', 'magenta', 'blue', 'gray', 'default', 'black', 'green', 'white', 'red']
# ['blue', 'pink', 'gray', 'black', 'yellow', 'cyan', 'green', 'magenta', 'white', 'red']
# ['hide', 'bold', 'italic', 'default', 'fast_blinking', 'faint', 'strikethrough', 'underline', 'blinking', 'reverse']
class Robot:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.ui_flag = 1
        self.time = 0.1
        self.ui_value = [self.x,self.y,self.time]
        self.scale = 1.10
        self.off_x = 17
        self.off_y = 4
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
            if tau < 300:
                tau = 300
            self.ui_value = [self.x,self.y,tau/100]
            self.ui_flag = 1
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
            self.go_to(x=1536-mm2pulse(0),y=7373+mm2pulse(3),unit='pulse')
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
            self.go_to(x=1550+mm2pulse(1),y=7373+mm2pulse(3),unit='pulse')
            self.go_to(z=220,tau=500)
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
                try:
                    pic = self.camera.perspectrive_with_aruco(pic)
                    cv2.imwrite('images/raw_data/{}_{}.png'.format(x, y),pic)
                except:
                    print('fail')
                time.sleep(1)
        self.camera.median_multiple_images()
    def symbol_for_wtf(self):
        symbol = cv2.imread('images/symbols/symbol.png')
        map_img = cv2.imread('images/process_data/test.png')
        x,y = match_symbol(map_img,symbol)
        cv2.circle(map_img,(x,y),5,(255,0,255),10)
        np.save('numpy_arr/symbol_coor.npy',np.array([x,y]))
        cv2.imshow('fucker',map_img)
        cv2.waitKey(0)
    def take_symbol_pic(self):
        self.camera = Camera(port = 1)
        pic = self.camera.take_pic()
        cv2.imshow('test',pic)
        cv2.imwrite('images/symbols/symbol.png',pic)
        cv2.waitKey(0)
padang = Robot()
position_stack = []
state = 0
def mainui():
    height_ratio,width_ratio = np.load('numpy_arr/ratio.npy')[0],np.load('numpy_arr/ratio.npy')[1]
    cv2.namedWindow('MainUI')
    map_img = cv2.imread('images/process_data/test.png')
    previous_x = 0
    previous_y = 0
    pos_x = 0
    pos_y = 0
    while(1):
        map_buf = map_img.copy()
        if padang.ui_flag == 1:
            count_time = padang.ui_value[2]
            v_x = (padang.ui_value[0] - previous_x)/count_time
            v_y = (padang.ui_value[1] - previous_y)/count_time
            start_time = time.time()
            move_flag = 1
            padang.ui_flag = 0
        if move_flag == 1:
            pos_x = previous_x - v_x*(start_time-time.time())
            pos_y = previous_y - v_y*(start_time-time.time())
            if (time.time() - start_time) >= count_time:
                previous_x,previous_y = padang.ui_value[0],padang.ui_value[1]
                move_flag = 0
        color = map_img[int(pos_x/height_ratio),int(pos_y/width_ratio)]
        color = (int(color[0]),int(color[1]),int(color[2]))
        cv2.circle(map_buf,(int(pos_y/width_ratio),int(pos_x/height_ratio)),6,(0,0,0),-1)
        cv2.circle(map_buf,(int(pos_y/width_ratio),int(pos_x/height_ratio)),5,color,-1)
        cv2.imshow('MainUI',map_buf)
        cv2.waitKey(20)
def startstopui():
    # Importing Modules
    import pygame as pg
    import pygame_widgets as pw
    def start():
        state = 3
    def stop():
        play_sound('reset')
        padang.reset()
        state = 0
    # creating screen
    pg.init()
    screen = pg.display.set_mode((800, 600))
    running = True
    button_1 = pw.Button(
            screen, 100, 100, 300, 150, text='Start',
            fontSize=50, margin=20,
            inactiveColour=(0, 255, 0),
            pressedColour=(255, 255, 255), radius=20,
            onClick=start()
        )
    button_2 = pw.Button(
            screen, 100, 400, 300, 150, text='Stop',
            fontSize=50, margin=20,
            inactiveColour=(255, 0, 0),
            pressedColour=(255, 255, 255), radius=20,
            onClick=stop()
        )

    while running:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                    running = False
        button_1.listen(events)
        button_1.draw()
        button_2.listen(events)
        button_2.draw()
        pg.display.update()

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
        color_print('8 : Start Stop UI', color='green')
        color_print('9 : Map UI', color='cyan')
        color_print('10 : Take Symbol Pic', color='blue')
        color_print('11 : Match Symbol', color='pink')
        color_print('12 : Using Symbol For Rearrage Path', color='magenta')
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
            startstop = threading.Thread(target=startstopui, daemon=True)
            startstop.start()
        if ans == '9':
            gui = threading.Thread(target=mainui, daemon=True)
            gui.start()
        if ans == '10':
            padang.take_symbol_pic()
        if ans == '11':
            padang.symbol_for_wtf()
        if ans == '12':
            global using_symbol
            using_symbol = not using_symbol
        if ans == '13':
            padang.grip()
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
            print(using_symbol)
            if using_symbol:
                symbol_coor = list(np.load('numpy_arr/symbol_coor.npy'))
                path = rearrange_path(path,symbol_coor)
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
                height_ratio,width_ratio = np.load('numpy_arr/ratio.npy')[0],np.load('numpy_arr/ratio.npy')[1]
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
            play_sound('end')
            state = 0
        if state == 4:
            padang.get_image()
            state = 0