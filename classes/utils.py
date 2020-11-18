import serial 
import time
import math

def mm2pulse(mm):
    return int(mm * ((48*64*2)/(math.pi * 6.36619 * 2)))
