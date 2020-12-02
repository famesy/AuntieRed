import serial
import time
import threading 
import math

def mm2pulse(mm):
    return int(mm * ((48*64*2)/(math.pi * 6.36619 * 2)))

class Robot:
    def __init__(self,controller_enable,pic_com=None,pic_baud=None,arduino_com=None,arduino_baud=None):
        self.pic_enable = 0
        self.arduino_enable = 0
        if ((controller_enable == 'pic')|(controller_enable == 'both')):
            self.pic_enable = 1
            self.pic_com = pic_com
            self.pic_baud = pic_baud
            self.ser_pic = serial.Serial(port = self.pic_com, 
                                        baudrate = self.pic_baud,
                                        timeout = 0.5)
            self.ser_pic.rts = 0
            self.pic_ready = 1
            self.pic_home = 1
        if ((controller_enable == 'arduino')|(controller_enable == 'both')):
            self.arduino_enable = 1
            self.arduino_com = arduino_com
            self.arduino_baud = arduino_baud
            self.ser_arduino = serial.Serial(port = self.arduino_com,
                                            baudrate = self.arduino_baud,
                                            timeout = 0.5)
            time.sleep(1)
            self.arduino_ready = 1
            self.arduino_home = 1

    def __str__(self):
        return 'Hello Master How Can I Help You?'
        
    def reset(self):
        if (self.pic_enable):
            self.pic_home = 1
            self.ser_pic.rts = 1
            self.ser_pic.rts = 0
        if (self.arduino_enable):
            print(self.arduino_home)
            self.arduino_home = 1
            self.ser_arduino.dtr = 0
            self.ser_arduino.dtr = 1

    def set_home(self):
            if (self.pic_enable and self.pic_home):
                packet = bytearray(b'\xff\x00')
                self.ser_pic.write(packet)
            if (self.arduino_enable and self.arduino_home):
                self.ser_arduino.write(bytes([255, 0, 255, 1, 0 ,0 ]))

    def check_status(self):
        if (self.pic_enable):
            message_pic = self.ser_pic.readline().strip().decode('ascii')
            if (message_pic == 'Set Home'):
                self.pic_home = 0
                self.set_home()
            elif (message_pic == 'Already position'):
                self.pic_ready = 1
        if (self.arduino_enable):
            message_arduino = self.ser_arduino.readline().strip().decode('ascii')
            if (message_arduino == 'sethome'):
                self.arduino_home = 0
            elif (message_arduino == 'Zarrived'):
                self.arduino_ready = 1

    def go_to(self,x=None,y=None,z=None):
        if (self.pic_enable and self.pic_ready):
            packet = bytearray(b'\xff')
            # mode(0-255)
            packet.extend((1).to_bytes(1, byteorder='big'))
            # x (0-65535)
            packet.extend((x).to_bytes(2, byteorder='big'))
            # y (0-65535)   
            packet.extend((y).to_bytes(2, byteorder='big'))
            packet.extend('\x01')
            self.ser_pic.write(packet)
            self.pic_ready = 0
        if (self.arduino_enable and self.arduino_ready):
            print('hi')
            self.ser_arduino.flushInput()
            self.ser_arduino.flushOutput()
            packet = bytearray(b'\xff\x01')
            # x (0-65535)
            packet.extend((z*10).to_bytes(2, byteorder='big'))
            # # y (0-65535)   
            packet.extend((255).to_bytes(2, byteorder='big'))
            self.ser_arduino.write(packet)
            self.arduino_ready = 0
    
    def timer_on(self):
        self.ser_pic.write(b'\xff\x02')

def Receiveprocesser(robot):
    while(1):
        robot.check_status()

def GoPosLooper(robot,paths):
    for path in paths:
        robot.go_to(z= path[0])
        while(robot.arduino_ready == 0):
            pass

if __name__ == "__main__":
    padang = Robot(controller_enable='arduino',arduino_com='COM10',arduino_baud=115200)
    print(padang)
    recieve_processer = threading.Thread(target=Receiveprocesser,args = [padang])
    recieve_processer.start()
    print('''This is Temporary Menu
    0 : set_home
    1 : reset
    2 : go to (mm)
    3 : timer on
    4 : test looper
    5 : terminate processer
    ''')
    while(1):
        ans = input('Answer : ')
        if (ans == '0'):
            padang.set_home()
        if (ans == '1'):
            padang.reset()
        if (ans == '2'):
            # try:
            if (padang.pic_enable):
                x = mm2pulse(int(input('x : ')))
                y = mm2pulse(int(input('Y : ')))
                z = 0
            if (padang.arduino_enable):
                z = int(input('Z : '))
            try:
                padang.go_to(x, y, z)
            except:
                padang.go_to(z=z)
        if (ans == '3'):
            padang.timer_on()
        if (ans == '4'):
            path_list = []
            for x in range(100,400,20):
                for y in range(100,400,20):
                    path_list.append([x,y])
            processer_go_looper = threading.Thread(target=GoPosLooper,args = [padang,path_list])
            processer_go_looper.start()
        if (ans == '6'):
            path_list = []
            for time in range(5):
                for z in range(160,400,40):
                    path_list.append([z])
            processer_go_looper = threading.Thread(target=GoPosLooper,args = [padang,path_list])
            processer_go_looper.start()