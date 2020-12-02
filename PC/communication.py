import serial 
import time
import math
import cv2
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

    def go_to(self, x = 0, y = 0, z = 0):
        finish_status_pic = 0
        finish_status_arduino = 0
        if ((self.mode == 0)|(self.mode == 2)):
            packet = bytearray(b'\xff')
            # mode(0-255)
            packet.extend((1).to_bytes(1, byteorder='big'))
            # x (0-65535)
            packet.extend((x).to_bytes(2, byteorder='big'))
            # y (0-65535)   
            packet.extend((y).to_bytes(2, byteorder='big'))
            packet.extend((1).to_bytes(1, byteorder='big'))
            err_x = 9999
            err_y = 9999
            self.ser_pic.flushInput()
            self.ser_pic.flushOutput() 
            print('pc sent this packet = {}'.format(packet))
            self.ser_pic.write(packet)
            time.sleep(0.1)
        if ((self.mode == 1)|(self.mode == 2)):
            packet = bytearray(b'\xff\x01')
            # x (0-65535)
            packet.extend((z).to_bytes(2, byteorder='big'))
            # # y (0-65535)   
            packet.extend((255).to_bytes(2, byteorder='big'))
            self.ser_arduino.write(packet)
        while(1):
            if ((self.mode == 0)|(self.mode == 2)):
                message_pic = self.ser_pic.readline()
                print(message_pic)
                if (message_pic.strip().decode('ascii') == 'Already position'):
                    finish_status_pic = 1
            if ((self.mode == 1)|(self.mode == 2)):
                message_arduino = self.ser_arduino.readline()
                if (message_arduino.strip().decode('ascii') == 'Zarrived'):
                    finish_status_arduino = 1
            if (self.mode == 2):
                if ((finish_status_pic & finish_status_arduino) == 1):
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
        finish_status_pic = 0
        finish_status_arduino = 0
        if ((self.mode == 0)|(self.mode == 2)):
            packet = bytearray(b'\xff\x00')
            self.ser_pic.write(packet)
        if ((self.mode == 1)|(self.mode == 2)):
            self.ser_arduino.write(bytes([255, 0, 255, 1, 0 ,0 ]))
        # while(1):
        #     if ((self.mode == 0)|(self.mode == 2)):
        #         message_pic = self.ser_pic.readline()
        #         if (message_pic.strip().decode('ascii') == 'Set Home'):
        #             finish_status_pic = 1
        #     if ((self.mode == 1)|(self.mode == 2)):
        #         message_arduino = self.ser_arduino.readline()
        #         print(message_arduino.strip().decode('ascii'))
        #         if (message_arduino.strip().decode('ascii') == 'sethome'):
        #             finish_status_arduino = 1
        #     if (self.mode == 2):
        #         if ((finish_status_pic & finish_status_arduino) == 1):
        #             break
        #     else:
        #         if ((finish_status_pic | finish_status_arduino) == 1):
        #             break

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
                    self.x = mm2pulse(int(input('x : ')))
                    self.y = mm2pulse(int(input('Y : ')))
                if ((self.mode == 1)|(self.mode == 2)):
                    self.z = int(input('Z : '))
                self.go_to(self.x, self.y, self.z)
            if (ans == '3'):
                self.timer_on()
            if (ans == 'bruh'):
                for x in range(20,101,20):
                    for y in range(20,401,20):
                        print('(go to {},{})'.format(x,y))
                        self.go_to(mm2pulse(x),mm2pulse(y))
                        if (self.camera_on == 1):
                            time.sleep(1)
                            pic = self.camera.get_pic()
                            print(pic)
                            pic = self.camera.perspectrive_with_aruco(pic)
                            try:
                                cv2.imwrite('images/raw_data_2/{}_{}.png'.format(x, y),pic)
                            except:
                                pass
                            time.sleep(1)
                self.camera.median_multiple_images()
            if (ans == 'bra'):
                next_flag = 1
                i = 1200
                while(1):
                        time.sleep(.001)
                        message_arduino = self.ser_arduino.readline()
                        time.sleep(.001)
                        print(message_arduino.strip().decode('ascii'))
                        if (message_arduino.strip().decode('ascii') == 'Zarrived'):
                            i += 200
                            next_flag = 1
                        if(next_flag == 1):
                            if(i > 4000):
                                i = 1200
                            time.sleep(.001)
                            self.go_to(0,0,i)
                            time.sleep(.001)
                            next_flag = 0
    


if __name__ == '__main__':
    padang = Robot(name = 'Padang', port_pic= 'COM6', baud_pic = 115200,port_arduino = 'COM10',baud_arduino = 115200, mode = 0,camera_on= 1)
    padang.command_line_menu()
