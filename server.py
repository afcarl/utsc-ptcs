#!/usr/bin/env python

import socket
import struct

# TODO:
# 1. create alginment wizard from local client
# 2. get stellarium to be able to 'goto' on telescope
# 3. fix movement errors with telescope mount
    # - Try the periodic error correction which will involve the use of the guide camera
    # - Manual calculation of error and correct with motor steps

def unpack_command(command):
    """ Unpack the data recieved from stellarium, and converts into coordinates in RA and DEC"""
    data = struct.unpack('<hhQIi',command)
    RA_raw = data[-2]  # a value of 0x100000000 = 0x0 means 24h=0h,
                       # a value of 0x80000000 means 12h
                       # 12h = 2147483648 
    DEC_raw = data[-1] # a value of -0x40000000 means -90 degrees
                       # a value of 0x0 means 0 degrees
                       #  a value of 0x40000000 means 90 degrees
                       # 90d = 1073741824
    dec = int(DEC_raw)/1073741824.0*90
    dec_string = str(int(dec)) + "d" + str(int(dec%1*60)) + "m" + str(round(dec%1*60%1*60, 2)) + "s" # convert from decimal into dms
    ra = int(RA_raw)/2147483648.0 *12
    ra_string = str(int(ra)) + "h" + str(int(ra%1*60)) + "m" + str(round(ra%1*60%1*60, 2)) + "s" # convert from decimal into hms
    return (ra_string,dec_string)

TCP_IP = '127.0.0.1'
TCP_PORT = 10001
BUFFER_SIZE = 32  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
print "Listening on", TCP_IP, TCP_PORT

conn, addr = s.accept()
print 'Connection address:', addr
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data: break
    print "received data:",unpack_command(data) 
    #conn.send(data)  TODO: return to stellarium the current RA and DEC from the telescope
conn.close()
