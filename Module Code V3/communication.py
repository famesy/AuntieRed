import serial 
import time
import math
import cv2
from utils import *
from cammy import Camera

class Robot:
    def __init__(self, name = 'Famesy', port_pic = None, port_arduino = None, baud_pic = None, baud_arduino = None, mode = 0, camera_on = 0):
        '''
        mode 0 = pic only
        mode 1 = arduino only
        mode 2 = both
        '''
        self.off_x = 22
        self.off_y = 15
        self.x = 0
        self.y = 0
        self.z = 600
        self.angle = 0
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
                                    stopbits = serial.STOPBITS_ONE,
                                    timeout = 0.5
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
            self.ser_arduino.flushOutput() 
        
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
        if self.z == z:
            finish_status_arduino = 1
        if (self.x == x)&(self.y == y):
            finish_status_pic = 1
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
            self.ser_pic.flushInput()
            self.ser_pic.flushOutput() 
            print('pc sent this packet = {}'.format(packet))
            self.ser_pic.write(packet)
            time.sleep(0.1)
        if ((self.mode == 1)|(self.mode == 2)):
            if tau < 300:
                tau = 300
            z = z * 10
            print('this is time',tau)
            packet = bytearray(b'\xff\x01')
            packet.extend((z).to_bytes(2, byteorder='big'))
            packet.extend((self.angle).to_bytes(2, byteorder='big'))
            packet.extend((tau).to_bytes(2, byteorder='big'))
            print(z,tau)
            print('pc sent this packet = {}'.format(packet))
            self.ser_arduino.flushInput()
            self.ser_arduino.flushOutput() 
            self.ser_arduino.write(packet)
        while(1):
            if ((self.mode == 0)|(self.mode == 2)):
                message_pic = self.ser_pic.readline()
                print('pic' + message_pic.strip().decode('ascii'))
                # if (message_pic.strip().decode('ascii') == 'Already position'):
                if len(message_pic.strip().decode('ascii')) > 5:
                    finish_status_pic = 1
            if ((self.mode == 1)|(self.mode == 2)):
                message_arduino = self.ser_arduino.readline()
                print('arrduino' + message_arduino.strip().decode('ascii'))
                # if (message_arduino.strip().decode('ascii') == 'ZArrived'):
                if len(message_arduino.strip().decode('ascii')) > 5:
                    finish_status_arduino = 1
            if (self.mode == 2):
                if ((finish_status_pic | finish_status_arduino) == 1):
                    break
            else:
                if ((finish_status_pic | finish_status_arduino) == 1):
                    break

    def go_to_xy(self,x,y):
        packet = bytearray(b'\xff')
        # mode(0-255)
        packet.extend((1).to_bytes(1, byteorder='big'))
        # x (0-65535)
        packet.extend((x).to_bytes(2, byteorder='big'))
        # y (0-65535)   
        packet.extend((y).to_bytes(2, byteorder='big'))
        packet.extend((1).to_bytes(1, byteorder='big'))
        self.ser_pic.flushInput()
        self.ser_pic.flushOutput() 
        print('pc sent this packet = {}'.format(packet))
        self.ser_pic.write(packet)
        while(1):
            message_pic = self.ser_pic.readline()
            print('pic' + message_pic.strip().decode('ascii'))
            if (message_pic.strip().decode('ascii') == 'Already position'):
            # if len(message_pic.strip().decode('ascii')) > 5:
                break
        
    
    def go_to_z(self,z,tau):
        z = z * 10
        tau = tau*100
        packet = bytearray(b'\xff\x01')
        packet.extend((z).to_bytes(2, byteorder='big'))
        packet.extend((self.angle).to_bytes(2, byteorder='big'))
        packet.extend((tau).to_bytes(2, byteorder='big'))
        self.ser_arduino.flushInput()
        self.ser_arduino.flushOutput() 
        self.ser_arduino.write(packet)
        while(1):
            message_arduino = self.ser_arduino.readline()
            print('arrduino' + message_arduino.strip().decode('ascii'))
            if (message_arduino.strip().decode('ascii') == 'ZArrived'):
            # if len(message_arduino.strip().decode('ascii')) > 5:
                break

    def rotate(self,deg,tau = 500):
        packet = bytearray(b'\xff\x04')
        packet.extend((self.z).to_bytes(2, byteorder='big'))
        packet.extend((deg).to_bytes(2, byteorder='big'))
        packet.extend((tau).to_bytes(2, byteorder='big'))
        self.ser_arduino.flushInput()
        self.ser_arduino.flushOutput() 
        self.ser_arduino.write(packet)
        while(1):
            if ((self.mode == 1)|(self.mode == 2)):
                message_arduino = self.ser_arduino.readline()
                print(message_arduino.strip().decode('ascii'))
                if (message_arduino.strip().decode('ascii') == 'RotateArrived'):
                # if len(message_arduino.strip().decode('ascii')) > 7:
                    break

    def grip(self):
        self.ser_arduino.flushInput()
        self.ser_arduino.flushOutput() 
        self.ser_arduino.write(bytes([255, 2, 18, 19, 0 ,0,0 ,0]))
        while(1):
            if ((self.mode == 1)|(self.mode == 2)):
                message_arduino = self.ser_arduino.readline()
                print(message_arduino.strip().decode('ascii'))
                # if (message_arduino.strip().decode('ascii') == 'RotateArrived'):
                if len((message_arduino.strip().decode('ascii'))) > 3:
                    break

    def ungrip(self):
        self.ser_arduino.flushInput()
        self.ser_arduino.flushOutput() 
        self.ser_arduino.write(bytes([255, 3, 18, 19, 0 ,0,0 ,0]))
        while(1):
            if ((self.mode == 1)|(self.mode == 2)):
                message_arduino = self.ser_arduino.readline()
                print(message_arduino.strip().decode('ascii'))
                # if (message_arduino.strip().decode('ascii') == 'RotateArrived'):
                if len((message_arduino.strip().decode('ascii'))) > 2:
                    break

    def set_home(self):
        if ((self.mode == 1)|(self.mode == 2)):
            self.ser_arduino.write(bytes([255, 0, 255, 1, 0 ,0,0 ,0]))
            self.z = 600
            self.angle = 0
            while(1):
                message_arduino = self.ser_arduino.readline()
                print('arduino say ' + message_arduino.strip().decode('ascii'))
                if (message_arduino.strip().decode('ascii') == 'sethome'):
                # if len(message_arduino.strip().decode('ascii')) > 5:
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
                # if len(message_pic.strip().decode('ascii')) > 6:
                    break
            self.timer_on()

    def get_rod(self):
        # self.ungrip()
        self.go_to_z(600,3)
        self.go_to_xy(1536,7373)
        self.go_to_z(210,5)
        time.sleep(0.5)
        self.grip()
        time.sleep(0.5)
        self.go_to_z(600,5)
    
    def place_rod(self):
        self.rotate(0)
        self.grip()
        self.go_to_z(600,5)
        self.go_to_xy(1436,7373)
        self.go_to_z(220,5)
        time.sleep(0.5)
        self.ungrip()
        time.sleep(0.5)
        self.go_to_z(600,5)


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
            4 : get rod
            5 : place rod
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
            if (ans == '4'):
                self.get_rod()
            if (ans == '5'):
                self.place_rod
            if (ans == 'cam'):
                for x in [20,50,80]:
                    for y in range(40,361,40):
                        print('(go to {},{})'.format(x,y))
                        self.go_to_xy(mm2pulse(x),mm2pulse(y))
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
                self.get_rod()
                path = list(np.load('numpy_arr/path_xyz.npy'))
                X = []
                Y = []
                Z = []
                for i in path:
                    X.append([i[0]])
                    Y.append([i[1]])
                    Z.append([i[2]])

                path,angles = path2pointanddeg(X,Y,Z)
                angles[0] = 0
                self.go_to_xy(x = mm2pulse(path[0][0]) - self.off_x ,y = mm2pulse(path[0][1] + self.off_y))
                self.go_to_z(240,5)
                # self.go_to(path[::-1][0][1]+127)
                # self.rotate(0)
                for xyz,angle in zip(path,angles):
                    self.rotate(int(angle))
                    x = int(xyz[0]+self.off_x)
                    y = int(xyz[1]+self.off_y)
                    z = int(xyz[2])*10
                    self.go_to(x,y,z+115)
                    time.sleep(0.25)
                # self.place_rod()
                # for xyz,angle in zip(path[::-1][1:],angles[::-1][1:]):
                    # x = int(xyz[0]+self.off_x)
                    # y = int(xyz[1]+self.off_y)
                    # z = int(xyz[2])*10
                    # self.go_to(x,y,z+210)
                    # self.rotate(int(angle))
                    # self.go_to_xy(mm2pulse(x),mm2pulse(y))
                    # time.sleep(1)
                self.place_rod()
                # self.reset()
                # time.sleep(1)
                # self.set_home()
            if (ans == 'offset'):
                self.off_x = int(input('x = '))
                self.off_y = int(input('y = '))

        


if __name__ == '__main__':
    padang = Robot(name = 'Padang', port_pic= 'COM6', baud_pic = 115200,port_arduino = 'COM3',baud_arduino = 38400, mode = 2,camera_on= 1)
    padang.command_line_menu()
