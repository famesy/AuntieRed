import serial 
import time
import math
import cv2
from utils import *
from test import Camera

def mm2pulse(mm):
    return int(mm * ((48*64*2)/(math.pi * 6.36619 * 2)))

class Robot:
    def __init__(self, name = 'Famesy', port_pic = None, port_arduino = None, baud_pic = None, baud_arduino = None, mode = 0, camera_on = 0):
        '''
        mode 0 = pic only
        mode 1 = arduino only
        mode 2 = both
        '''
        self.x = 0
        self.y = 0
        self.z = 0
        self.name = name
        self.port_pic = port_pic
        self.port_arduino = port_arduino
        self.baud_pic = baud_pic
        self.baud_arduino = baud_arduino
        self.mode = mode
        self.camera_on = camera_on
        if (camera_on == 1):
            self.camera = Camera(port = 1)
        if ((self.mode == 0)|(self.mode == 2)):
            self.ser_pic = serial.Serial(port = self.port_pic,
                                    baudrate = self.baud_pic,
                                    bytesize = serial.EIGHTBITS, 
                                    parity = serial.PARITY_NONE,
                                    stopbits = serial.STOPBITS_ONE
                                    )
            self.ser_pic.rts = 0
            self.ser_pic.isOpen()
            self.ser_pic.set_buffer_size(rx_size = 12800, tx_size = 12800)
            self.ser_pic.flushInput()
            self.ser_pic.flushOutput() 
        if ((self.mode == 1)|(self.mode == 2)):
            self.ser_arduino = serial.Serial(port = self.port_arduino,
                                    baudrate = self.baud_arduino,
                                    timeout = 0.5
                                    )
            self.ser_arduino.set_buffer_size(rx_size = 12800, tx_size = 12800)
            time.sleep(1)
            self.ser_arduino.flushInput()
        
    def __str__(self):
        return '''
        My name is {}
        PIC     Port = {} Baud = {}
        Arduino Port = {} Baud = {}
        '''.format(self.name,self.port_pic,self.baud_pic,self.port_arduino,self.baud_arduino)

    def go_to(self, x = None, y = None, z = None,tau = 500):
        finish_status_pic = 0
        finish_status_arduino = 0
        if x == None:
            x = self.x
        if y == None:
            y = self.y
        if z == None:
            z = self.z
        past_x = mm2pulse(self.x)
        past_y = mm2pulse(self.y)
        past_z = self.z
        self.x = x
        self.y = y
        self.z = z
        if ((self.mode == 0)|(self.mode == 2)):
            x = mm2pulse(x)
            y = mm2pulse(y)
            packet = bytearray(b'\xff')
            # mode(0-255)
            packet.extend((1).to_bytes(1, byteorder='big'))
            # x (0-65535)
            packet.extend((x).to_bytes(2, byteorder='big'))
            # y (0-65535)   
            packet.extend((y).to_bytes(2, byteorder='big'))
            packet.extend((1).to_bytes(1, byteorder='big'))
            tau = int(cal_time(past_x,past_y,x,y) * 100)
            print(cal_time(past_x,past_y,x,y) * 100)
            self.ser_pic.flushInput()
            self.ser_pic.flushOutput() 
            print('pc sent this packet = {}'.format(packet))
            self.ser_pic.write(packet)
            time.sleep(0.1)
        if ((self.mode == 1)|(self.mode == 2)):
            z = z * 10
            print('this is time',tau)
            packet = bytearray(b'\xff\x01')
            packet.extend((z).to_bytes(2, byteorder='big'))
            packet.extend((0).to_bytes(2, byteorder='big'))
            packet.extend((tau).to_bytes(2, byteorder='big'))
            print('pc sent this packet = {}'.format(packet))
            self.ser_arduino.write(packet)
        while(1):
            if ((self.mode == 0)|(self.mode == 2)):
                message_pic = self.ser_pic.readline()
                print(message_pic.strip().decode('ascii'))
                if (message_pic.strip().decode('ascii') == 'Already position'):
                    finish_status_pic = 1
            if ((self.mode == 1)|(self.mode == 2)):
                message_arduino = self.ser_arduino.readline()
                print(message_arduino.strip().decode('ascii'))
                if (message_arduino.strip().decode('ascii') == 'ZArrived'):
                    finish_status_arduino = 1
            if (self.mode == 2):
                if ((finish_status_pic | finish_status_arduino) == 1):
                    break
            else:
                if ((finish_status_pic | finish_status_arduino) == 1):
                    break

        if ((self.mode == 1)|(self.mode == 2)):
            self.z = z
            pass

    def rotate(self,deg):
        pass

    def grip(self,condi):
        if (condi == 0):
            pass
        if (condi == 1):
            pass

    def set_home(self):
        if ((self.mode == 1)|(self.mode == 2)):
            print(bytes([255, 0, 255, 1, 0 ,0 ]))
            self.ser_arduino.write(bytes([255, 0, 255, 1, 0 ,0,0 ,0]))
            self.z = 0
            while(1):
                message_arduino = self.ser_arduino.readline()
                print('arduino say ' + message_arduino.strip().decode('ascii'))
                if (message_arduino.strip().decode('ascii') == 'sethome'):
                    break
        if ((self.mode == 0)|(self.mode == 2)):
            packet = bytearray(b'\xff\x00')
            self.ser_pic.write(packet)
            self.x = 0
            self.y = 0
            while(1):
                message_pic = self.ser_pic.readline()
                print('pic say ' + message_pic.strip().decode('ascii'))
                if (message_pic.strip().decode('ascii') == 'Set Home'):
                    break

    def reset(self):
        if ((self.mode == 0)|(self.mode == 2)):
            self.ser_pic.rts = 1
            self.ser_pic.rts = 0
        if ((self.mode == 1)|(self.mode == 2)):
            self.ser_arduino.dtr = 0
            time.sleep(0.25)
            self.ser_arduino.dtr = 1
    
    def timer_on(self):
        self.ser_pic.write(b'\xff\x02')

    def command_line_menu(self):
        print(self)
        while(1):
            print('''
            0 : set_home
            1 : reset
            2 : go to (mm)
            3 : timer on
            ''')
            ans = input('Answer : ')
            if (ans == '0'):
                self.set_home()
            if (ans == '1'):
                self.reset()
            if (ans == '2'):
                # try:
                if ((self.mode == 0)|(self.mode == 2)):
                    x = int(input('x : '))
                    y = int(input('Y : '))
                if ((self.mode == 1)|(self.mode == 2)):
                    z = int(input('Z : '))
                if (self.mode == 0):
                    self.go_to(x, y)
                elif (self.mode == 1):
                    self.go_to(z=z)
                else:
                    self.go_to(x, y, z)
            if (ans == '3'):
                self.timer_on()
            if (ans == 'cam'):
                for x in range(20,101,40):
                    for y in range(40,361,20):
                        print('(go to {},{})'.format(x,y))
                        self.go_to(x,y)
                        if (self.camera_on == 1):
                            time.sleep(1)
                            pic = self.camera.get_pic()
                            print(pic)
                            try:
                                pic = self.camera.perspectrive_with_aruco(pic)
                                cv2.imwrite('images/raw_data_2/{}_{}.png'.format(x, y),pic)
                            except:
                                pass
                            time.sleep(1)
                self.camera.median_multiple_images()
            if (ans == 'wtf'):
                path = np.load('numpy_arr/path_xyz.npy')
                print(len(list(path)))
                for xyz in path[::-1]:
                    x = int(xyz[0])
                    y = int(xyz[1])
                    z = (int(xyz[2])*10)+150
                    print(x,y,z)
                    self.go_to(x,y,z)
                for xyz in path:
                    x = int(xyz[0])
                    y = int(xyz[1])
                    z = (int(xyz[2])*10)+150
                    print(x,y,z)
                    self.go_to(x,y,z)
                    time.sleep(0.5)
        


if __name__ == '__main__':
    padang = Robot(name = 'Padang', port_pic= 'COM6', baud_pic = 115200,port_arduino = 'COM10',baud_arduino = 115200, mode = 2,camera_on= 1)
    padang.command_line_menu()
