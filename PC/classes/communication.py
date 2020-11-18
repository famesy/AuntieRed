import serial 
import time
import math

def mm2pulse(mm):
    return int(mm * ((48*64*2)/(math.pi * 6.36619 * 2)))

class Robot:
    def __init__(self, name = 'Famesy', port_pic = None, port_arduino = None, baud_pic = None, baud_arduino = None, mode = 0):
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
        if ((self.mode == 0)|(self.mode == 2)):
            self.ser_pic = serial.Serial(port = self.port_pic,
                                    baudrate = self.baud_pic,
                                    bytesize = serial.EIGHTBITS, 
                                    parity = serial.PARITY_NONE,
                                    stopbits = serial.STOPBITS_ONE,
                                    timeout = 1
                                    )
            self.ser_pic.rts = 0
            self.ser_pic.isOpen()
        if ((self.mode == 1)|(self.mode == 2)):
            self.ser_arduino = serial.Serial(port = self.port_arduino,
                                    baudrate = self.baud_arduino,
                                    bytesize = serial.EIGHTBITS, 
                                    parity = serial.PARITY_NONE,
                                    stopbits = serial.STOPBITS_ONE,
                                    timeout = 1
                                    )
        
    def __str__(self):
        return '''
        My name is {}
        PIC     Port = {} Baud = {}
        Arduino Port = {} Baud = {}
        '''.format(self.name,self.port_pic,self.baud_pic,self.port_arduino,self.baud_arduino)

    def go_to(self, x = 1000, y = 1000, z = 1000):
        if ((self.mode == 0)|(self.mode == 2)):
            packet = bytearray(b'\xff')
            # mode(0-255)
            packet.extend((1).to_bytes(1, byteorder='big'))
            # x (0-65535)
            packet.extend((x).to_bytes(2, byteorder='big'))
            # y (0-65535)   
            packet.extend((y).to_bytes(2, byteorder='big'))
            self.ser_pic.write(packet)
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
        if ((self.mode == 0)|(self.mode == 2)):
            packet = bytearray(b'\xff\x00')
            self.ser_pic.write(packet)
        if ((self.mode == 1)|(self.mode == 2)):
            pass

    def reset(self):
        if ((self.mode == 0)|(self.mode == 2)):
            self.ser_pic.rts = 1
            self.ser_pic.rts = 0
        if ((self.mode == 1)|(self.mode == 2)):
            pass
    
    def timer_on(self):
        self.ser_pic.write(b'\xff\x02')

    def command_line_menus(self):
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
                self.x = mm2pulse(int(input('x : ')))
                self.y = mm2pulse(int(input('Y : ')))
                self.go_to(self.x, self.y)
            if (ans == '3'):
                self.timer_on()


if __name__ == '__main__':
    padang = Robot(name = 'Padang', port_pic= 'COM6', baud_pic = 115200, mode = 0)
    padang.command_line_menus()


