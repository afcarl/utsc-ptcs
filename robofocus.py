#!/usr/bin/python
import serial
import os
import time
import curses
import socket
import struct
import time
        
port_name = ""    
if os.uname()[0]=="Darwin":
    default_port_name = '/dev/tty.usbserial'
else:
    default_port_name = '/dev/ttyS0'
try:
    if port_name == '':
        port_name = default_port_name
    serialport = serial.Serial(port_name, 9600, timeout = 0.01) 
    print "Successfully opened serial port."
except:
    print "Opening serial port failed."
            
def robofocus_send(c):            
    Z = 0
    for i in c:
        Z += ord(i)
    Z = Z%256   # checksum
    serialport.write(c+chr(Z)) 

def robofocus_read():
    r = serialport.read(1024) # empty buffer
    return robofocus_process_readout(r)

def robofocus_process_readout(r):
    if len(r)>0:
        if r[0]=="I" or r[0]=="O": # ignore in/out characters
            return robofocus_process_readout(r[1:])
    ret = ""
    if len(r)>=9:
        Z = 0
        for i in r[:8]:
            Z += ord(i)
        Z = Z%256  # checksum
        if Z==ord(r[8]):
            ret = r[:8]
        else:
            print "Checksum did not match."
    if len(r)>9:
        ret += robofocus_process_readout(r[9:])
    return ret

def robofocus_get_position():
    serialport.read(1024) # empty buffer
    robofocus_send("FS000000")
    time.sleep(0.25)
    return robofocus_read()

def robofocus_get_version():
    serialport.read(1024) # empty buffer
    robofocus_send("FV000000") 
    time.sleep(0.25)
    return robofocus_read()

def robofocus_move_in(steps):
    serialport.read(1024) # empty buffer
    robofocus_send("FI%06d"%(steps))
    print "FI%06d"%(steps)
    time.sleep(0.25)
    return robofocus_read()

def robofocus_move_out(steps):
    serialport.read(1024) # empty buffer
    robofocus_send("FO%06d"%(steps))
    time.sleep(0.25)
    return robofocus_read()

def robofocus_move(steps):
    if steps>0:
        return robofocus_move_out(steps)
    if steps<0:
        return robofocus_move_in(-steps)
    if steps<0:
        return robofocus_get_position()
    

print robofocus_get_version()
print robofocus_get_position()
print robofocus_move(1)
print robofocus_get_position()
print robofocus_move(-1)
print robofocus_get_position()

