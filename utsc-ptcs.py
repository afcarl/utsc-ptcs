#!/usr/bin/python
# UTSC | PTCS 
# University of Toronto Scarborough | Python Telescope Control System
#
# Copyright (c) 2014 Eric Dapp, Caden Armstrong, Hanno Rein
#
# UTSC | PCTS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# UTSC | PCTS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with UTSC | PCTS.  If not, see <http://www.gnu.org/licenses/>.
#
import serial
#from PIL import ImageTk, Image
import select

import os
import curses
import socket
import struct
import time
import datetime
import sys
import select
import signal
import client
import threading
import subprocess
import ephem
import smbus
import math
i2cbus = smbus.SMBus(1) 
toronto = ephem.city('Toronto')
from conversions import *
focusstepperinc = 4
try:
    with open(".focussteppercount","r") as f:
        focussteppercount = int(f.read())
except:
    focussteppercount = 0

relaymap = [22,18,13,7,11,15,19]
try:
    import RPi.GPIO as GPIO;
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD); 
    # Servo
    GPIO.setup(16, GPIO.OUT)
    GPIO.output(16, 1)
    GPIO.setup(12, GPIO.OUT)
    servostatus = 4.75
    servoPWM = GPIO.PWM(12, 50)
    servoPWM.start(100.)
    # Stepper
    GPIO.setup(29, GPIO.OUT)
    GPIO.setup(31, GPIO.OUT)
    GPIO.setup(33, GPIO.OUT)
    GPIO.setup(37, GPIO.OUT)
    GPIO.output(29, 0)
    GPIO.output(31, 0)
    GPIO.output(33, 0)
    GPIO.output(37, 0)
    # Relays
    for n,pin in enumerate(relaymap):
        GPIO.setup(pin, GPIO.OUT)
        if n<4: # only turn off dome, not other equipment
            GPIO.output(pin, 1)
except:
    print("cannot access GPIO ports")

acceleration_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
acceleration_socket.bind(("",8086))
acceleration_socket.setblocking(0)
def read_word_2c(adr):
    try:
        high = i2cbus.read_byte_data(0x68, adr)
        low = i2cbus.read_byte_data(0x68, adr+1)
        val = (high << 8) + low
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val
    except:
        return 0

def convword(data):
    high = ord(data[0])
    low = ord(data[1])
    val = (high << 8) + low
    if (val >= 0x8000):
        val = -((65535 - val) + 1)
    val /= 16384.0
    return val

def norm(v):
    n = math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])
    if n>0.:
        return [v[0]/n,v[1]/n,v[2]/n]
    else:
        return [0.,0.,0.]

voltage_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
voltage_socket.bind(("",8087))
voltage_socket.setblocking(0)
from curses import wrapper

def stepperMove(inc):
    for si in range(abs(inc)):
            if inc > 0:
                GPIO.output(29, 0) # A
                GPIO.output(31, 1) # A-
                GPIO.output(33, 0) # B
                GPIO.output(37, 1) # B-
            else:
                GPIO.output(29, 1)
                GPIO.output(31, 0)
                GPIO.output(33, 1)
                GPIO.output(37, 0)
            time.sleep(0.01) # sleep 1 second
            GPIO.output(29, 1)
            GPIO.output(31, 0)
            GPIO.output(33, 0)
            GPIO.output(37, 1)
            time.sleep(0.01) # sleep 1 second
            if inc < 0:
                GPIO.output(29, 0) # A
                GPIO.output(31, 1) # A-
                GPIO.output(33, 0) # B
                GPIO.output(37, 1) # B-
            else:
                GPIO.output(29, 1)
                GPIO.output(31, 0)
                GPIO.output(33, 1)
                GPIO.output(37, 0)
            time.sleep(0.01) # sleep 1 second 
            GPIO.output(29, 0)
            GPIO.output(31, 1)
            GPIO.output(33, 1)
            GPIO.output(37, 0)
            time.sleep(0.01) # sleep 1 second 
    GPIO.output(29, 0)
    GPIO.output(31, 0)
    GPIO.output(33, 0)
    GPIO.output(37, 0)
    global focussteppercount
    focussteppercount += inc
    statusUpdate("Stepper (f/F)", "%d" % focussteppercount)
    with open(".focussteppercount","w") as f:
        f.write("%d"%focussteppercount)

def updateDomeStatus():
    dome = "---"
    try:
        if not GPIO.input(relaymap[0]):
            dome = "<<<"
        elif not GPIO.input(relaymap[1]):
            dome = ">>>"
        elif not GPIO.input(relaymap[2]):
            dome = "^^^"
        elif not GPIO.input(relaymap[3]):
            dome = "vvv"
    except:
        pass

    statusUpdate("Dome movement",dome)

    peri = ""
    try:
        if not GPIO.input(relaymap[4]):
            peri += "on  /"
        else:
            peri += "off /"
        if not GPIO.input(relaymap[5]):
            peri += " on  /"
        else:
            peri += " off /"
        if not GPIO.input(relaymap[6]):
            peri += " on  /"
        else:
            peri += " off /"
        if servostatus == 10.:
            peri += " open"
        else:
            peri += " closed"
    except:
        pass

    statusUpdate("Lights/Scope/Camera/Cover",peri) 

def statusUpdate(k, value):
    ncurses_lock.acquire()
    for index, key in enumerate(statusitems):      
        if key == k:
            statuswin.move(1+index, 5+statustitlelen);   
            statuswin.clrtoeol(); 
            try:
                statuswin.addstr(1+index, 5+statustitlelen, value.replace('\n', ' '))           
            except:
                statuswin.addstr(1+index, 5+statustitlelen, "Cannot display string")           
    statuswin.border(0)
    statuswin.addstr(0, 1, " Status ")                    
    statuswin.refresh()
    ncurses_lock.release()

messagesN = 10
messagesi = 1
messages = []
messageswin = None
def showMessage(value):
    global messagesi
    atcl_asynch = value.split(chr(0x9F))
    if len(atcl_asynch)>1:
        for a in atcl_asynch:
            if len(a)>0:
                showMessage(a.replace('\n',' '))
        return
    else:
        value = atcl_asynch[0]
    if len(value)>2:
        if value[0:2]=="O7":
            return
    global messageswin
    ncurses_lock.acquire()
    if len(messages) >= messagesN:
        messages.pop(0)
        messagesi +=1 
    messages.append(value)
    for index, key in enumerate(reversed(messages)):      
        messageswin.move(1+index, 2);   
        messageswin.clrtoeol(); 
        messageswin.addstr(1+index, 2, "%4d : " % (messagesi+len(messages)-index-1))           
        try:
            if "ERROR" in key:
                messageswin.addstr(1+index, 2+7, key, curses.A_STANDOUT)           
            elif "WARNING" in key:
                messageswin.addstr(1+index, 2+7, key, curses.A_BOLD)           
            else:
                messageswin.addstr(1+index, 2+7, key)           
        except:
                messageswin.addstr(1+index, 2+7, "Cannot display string")           
    messageswin.border(0)
    messageswin.refresh()
    ncurses_lock.release()
    
vlcproc1 = None
vlcproc2 = None
import psutil

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

telescope_port = None    
telescope_states= [
    ['',  '!AGas;'],  
    ['',  '!AGai;'],
    ['',  '!CGra;'],
    ['',  '!CGde;'],
    ['',  '!CGtr;'],
    ['',  '!CGtd;']
]

special = [
        [chr(0xB1), "ATCL_ENTER"],
        [chr(0x8F), "ATCL_ACK"],
        [chr(0xA5), "ATCL_NACK"],
        [chr(0x9A), "ATCL_STATUS"],
        [chr(0x9B), "ATCL_WARNING"],
        [chr(0x9C), "ATCL_ALERT"],
        [chr(0x9D), "ATCL_INTERNAL_ERROR"],
        [chr(0x9E), "ATCL_SYNTAX_ERROR"],
        [chr(0x9F), "ATCL_IDC_ASYNCH"],
        [chr(0xA0), "ATCL_IDC_VERIFY"],
        [chr(0xA1), "ATCL_IDC_FRAMING(1)"],
        [chr(0xA2), "ATCL_IDC_COMM_OVERRUN(1)"],
        [chr(0xA3), "ATCL_IDC_CMND_OVERRUN(1)"],
        [chr(0xA4), "ATCL_CMND_TIMEOUT(1)"],
        [chr(0xA6), "ATCL_ID_CMND"],
        [chr(0xA7), "ATCL_ID_LINK"],
        [chr(0xA8), "ATCL_ID_DING"],
        [chr(0xAA), "ATCL_CHANGE_NOTIFY"],
        ]

def telescope_response(ret):
    if ret is None or len(ret)==0:
        return
    mask =  0b10000000
    ret = ret.strip().strip(';')
    nextMessageColor = None
    for i in range(len(ret)):
        if ord(ret[i])&mask==128:
            if i>0:
                showMessage(ret[0:i].strip(';'))
            for c,n in special:
                if ret[i] == c:
                    if n not in ["ATCL_STATUS","ATCL_ACK","ATCL_IDC_ASYNCH"]:
                        showMessage(n)
                    break
            if len(ret)>i:
                telescope_response(ret[i+1:])
            return
    showMessage(ret)


def telescope_cmd(cmd,hideResponse=False):
    if telescope_port is not None:
        ret = telescope_port.read(2048) # empty buffer
        telescope_response(ret)
        telescope_port.write(cmd) 
        for i in range(10): # wait 100ms max
            time.sleep(0.01)
            ret = telescope_port.read(2048).strip() 
            if len(ret)>0:
                if not hideResponse:
                    telescope_response(ret);
                return ret
    return None

stop_threads = False
ncurses_lock = threading.Lock()
telescope_lock = threading.Lock()
def telescope_communication():
    global telescope_port
    global telescope_states
    while stop_threads==False:
        if telescope_port is not None:
            ra, dec = None, None
            telescope_lock.acquire()
            for (index,element) in enumerate(telescope_states):
                value, command = element
                ret = telescope_cmd(command,hideResponse=True) 
                if ret is not None:
                    atcl_asynch = ret.split(chr(0x9F))
                    if len(atcl_asynch)>1:
                        ret = atcl_asynch[0]
                    if len(ret)>0:
                        if ret[0] == chr(0x8F):
                            ret = "ATCL_ACK"
                        elif ret[0] == chr(0xA5):
                            ret = "ATCL_NACK"
                        else:
                            if ret[-1] == ";":
                                ret = ret[:-1]
                            try:
                                if command == '!CGra;':
                                    ra = ra_str2raw(ret)
                                if command == '!CGde;':
                                    dec = dec_str2raw(ret)
                            except:
                                ra, dec = None, None
                    else:
                        ret = "N/A"
                else:
                    ret = "N/A"
                
                if "Internal error" in ret:
                    show_message(ret)
                    ret = "N/A"
                telescope_states[index][0] = ret
            telescope_lock.release()
            statusUpdate("Alignment state/side", telescope_states[0][0]+" / "+telescope_states[1][0])
            statusUpdate("Current coordinates", telescope_states[2][0]+"  "+telescope_states[3][0])
            statusUpdate("Target coordinates", telescope_states[4][0]+"  "+telescope_states[5][0])
            if ra is not None and dec is not None:
                if stellarium_socket is not None:
                    if stellarium_conn is not None:
                        data = struct.pack('<hhQIii',24,0,int(round(time.time() * 1000)), ra, dec, 0)
                        stellarium_conn.send(data)
        time.sleep(3)

    return


alignment_mode = "goto"
stellarium_socket = None
stellarium_conn = None
def stellarium_communication():
    global stellarium_socket
    global stellarium_conn
    global alignment_mode
    while stop_threads==False:
        # Poll socket for Stellarium
        if stellarium_socket is not None:
            if stellarium_conn is None:
                try:
                    stellarium_conn, addr = stellarium_socket.accept()
                    stellarium_conn.settimeout(0)
                    #socket.setblocking(0)
                except socket.error as e:
                    pass
            else:
                time.sleep(0.01)
                data = ""
                try:
                    data = stellarium_conn.recv(1024)
                    if len(data)==20:   # goto command
                        data = struct.unpack('<hhQIi',data)
                        ra_string, dec_string = ra_raw2str(data[-2]), dec_raw2str(data[-1])
                        showMessage("Received from stellarium: %s %s" % (ra_string,dec_string))
                        if dec_string[-2:]=="60":
                            dec_string = dec_string[:-2]+"59"
                        telescope_lock.acquire()
                        telescope_cmd('!CStr' + ra_string + ';')
                        telescope_cmd('!CStd' + dec_string + ';')
                        if alignment_mode=="align":
                            telescope_cmd('!AFrn;')
                            alignment_mode = "goto"
                            statusUpdate("Alignment mode", "GoTo next coordinates.")
                        elif alignment_mode=="goto": 
                            telescope_cmd('!GTrd;')
                        telescope_lock.release()
                    elif len(data)==0:
                        # Disconnected
                        showMessage("Stellarium disconnected. Waiting for new connection.")
                        stellarium_conn = None
                        pass
                    else:
                        showMessage("Unknown command received from stellarium. Length %d."%len(data))
                except socket.error as e:
                    # No data received.
                    pass
        else:
            stellarium_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stellarium_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = 10001
            try:
                stellarium_socket.settimeout(0)
                stellarium_socket.bind(("127.0.0.1", port))
                stellarium_socket.listen(1)
            except socket.error as e:
                showMessage("Stellarium socket error (%s)"%e.strerror)
                stellarium_socket = None
                time.sleep(1)
        time.sleep(0.1)


autoalignment_socket = None
autoalignment_conn = None
def autoalignment_communication():
    global autoalignment_socket
    global autoalignment_conn
    while stop_threads==False:
        # Poll socket for Autoalignment
        if autoalignment_socket is not None:
            if autoalignment_conn is None:
                try:
                    autoalignment_conn, addr = autoalignment_socket.accept()
                    autoalignment_conn.settimeout(0)
                    #socket.setblocking(0)
                except socket.error as e:
                    pass
            else:
                time.sleep(0.01)
                data = ""
                try:
                    data = autoalignment_conn.recv(2048)
                    if len(data)==0:
                        #Disconnected
                        autoalignment_conn = None
                    else:
                        data_split = data.split(";")
                        if data_split[0]=="East" or data_split[0]=="West":
                            telescope_lock.acquire()
                            direction, ra_string, dec_string = data_split
                            showMessage("Auto alignment coordinates received: (%s) %s %s" %(direction, ra_string, dec_string))
                            telescope_cmd('!ASas' + direction + ';')
                            if dec_string[-2:]=="60":
                                dec_string = dec_string[:-2]+"59"
                            telescope_cmd('!CStr' + ra_string + ';')
                            telescope_cmd('!CStd' + dec_string + ';')
                            telescope_cmd('!AFrn;')
                            alignment_mode = "goto"
                            statusUpdate("Alignment mode", "GoTo next coordinates.")
                            telescope_lock.release()
                        elif data_split[0]=="Focus":
                            try:
                                steps = int(data_split[1])
                            except:
                                showMessage("Unknown stepper command received.")
                            if abs(steps)>20:
                                showMessage("Too many steps received.")
                            else:
                                stepperMove(steps)
                            showMessage("Focus increment: %d"%steps)
                        else:
                            showMessage("Unknown command received.")
                except socket.error as e:
                    # No data received
                    pass
        else:
            autoalignment_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            autoalignment_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = 10002
            try:
                autoalignment_socket.settimeout(0)
                autoalignment_socket.bind(("127.0.0.1", port))
                autoalignment_socket.listen(1)
            except socket.error as e:
                showMessage("Auto alignment socket error (%s)"%e.strerror)
                autoalignment_socket = None
                time.sleep(1)
        time.sleep(0.1)



def finish():
    print("Finishing...")
    try:
        for n,pin in enumerate(relaymap):
            if n<4: # only turn off dome, not other equipment
                GPIO.output(pin, 1)
        #GPIO.cleanup()
    except:
        pass
    global stop_threads
    stop_threads = True
    if stellarium_socket is not None:
        if stellarium_conn is not None:
            stellarium_conn.close()
            try:
                stellarium_socket.shutdown(socket.SHUT_RD)
            except:
                pass
        stellarium_socket.close()
    if autoalignment_socket is not None:
        if autoalignment_conn is not None:
            autoalignment_conn.close()
            try:
                autoalignment_socket.shutdown(socket.SHUT_RD)
            except:
                pass
        autoalignment_socket.close()
    exit(1)
    return
    
def start_manual_alignment_e():
    statusUpdate("Alignment mode", "Align to next coordinates (East)")
    global alignment_mode
    alignment_mode = "align"
    telescope_lock.acquire()
    telescope_cmd('!ASasEast;')
    telescope_lock.release()
def start_manual_alignment_w():
    statusUpdate("Alignment mode", "Align to next coordinates (West)")
    global alignment_mode
    alignment_mode = "align"
    telescope_lock.acquire()
    telescope_cmd('!ASasWest;')
    telescope_lock.release()

menuwin = None

def main(stdscr):
    stdscr.clear()
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.nodelay(True)
    stdscr.keypad(True)

    stdscr.addstr(1, 2, "UTSC | PTCS", curses.A_BOLD)
    stdscr.addstr(2, 2, "University of Toronto Scarborough | Python Telescope Control System", curses.A_BOLD)
    stdscr.refresh()

    menuitems = [
            "e/w/g/!/q           : Align East-West / GoTo / Debug / Quit",
            "Left/Right/Up/Down  : Control dome",
            "1/2/3/4             : light/telescope/camera/cover",
            ]
    global menuwin
    menuwin = curses.newwin(len(menuitems)+2,curses.COLS-3,4,2)                                  
    menuwin.border(0)
    menuwin.addstr(0, 1, " Menu ")                    
    for index, item in enumerate(menuitems):                        
        msg = '%s' % (item)                            
        menuwin.addstr(1+index, 2, msg)                    
    menuwin.refresh()

   
    global statusitems
    statusitems = [
            'Time UTC/siderial/az/bank',
            'Telescope', 
            'Dome movement', 
            'Lights/Scope/Camera/Cover', 
            'Alignment mode', 
            'Stepper (f/F)', 
            'Alignment state/side',
            'Current coordinates',
            'Target coordinates',
    ] 
    global statuswin
    statuswin = curses.newwin(len(statusitems)+2,curses.COLS-3,menuwin.getbegyx()[0]+menuwin.getmaxyx()[0],2)     
    statuswin.border(0)
    statuswin.addstr(0, 1, " Status ")                    
    global statustitlelen
    statustitlelen = max([len(k) for k in statusitems])
    for index, key in enumerate(statusitems):      
        statuswin.addstr(1+index, 2, ("%%-%ds: "%(statustitlelen+1)) % key)           
    updateDomeStatus()                    
    statusUpdate("Alignment mode", "GoTo next coordinates.")
    global focussteppercount
    statusUpdate("Stepper (f/F)", "%d"%focussteppercount)
   
    global messageswin
    messageswin = curses.newwin(messagesN+2,curses.COLS-3,statuswin.getbegyx()[0]+statuswin.getmaxyx()[0],2)     
    messageswin.border(0)
    messageswin.addstr(0, 1, " Log ")                    
    messageswin.refresh()

    # Open Telescope Port
    global telescope_port
    if os.uname()[0]=="Darwin":
        port_name = '/dev/tty.usbserial'
    else:
        #port_name = '/dev/ttyS0'
        port_name = '/dev/ttyAMA0'
    try:
        telescope_port = serial.Serial(port_name, 19200, timeout = 0.01) 
        statusUpdate('Telescope', "Opened "+port_name)                    
    except:
        statusUpdate('Telescope', "Unable to open port at "+port_name)                    


    telescope_thread = threading.Thread(target=telescope_communication)
    telescope_thread.start()
    stellarium_thread = threading.Thread(target=stellarium_communication)
    stellarium_thread.start()
    autoalignment_thread = threading.Thread(target=autoalignment_communication)
    autoalignment_thread.start()

    lastkey = None
    while True:
        c = stdscr.getch()
        if lastkey is not None:
            td = datetime.datetime.now() - lastkey
            if td.microseconds > 400000 or td.seconds > 0:
                GPIO.output(relaymap[0], 1)
                GPIO.output(relaymap[1], 1)
                updateDomeStatus()                    
                lastkey = None


        if c == curses.KEY_LEFT:
            GPIO.output(relaymap[0], 0)
            updateDomeStatus()                    
            lastkey = datetime.datetime.now()
        elif c == curses.KEY_RIGHT:
            GPIO.output(relaymap[1], 0)
            updateDomeStatus()                    
            lastkey = datetime.datetime.now()
        elif c == curses.KEY_UP:
            if GPIO.input(relaymap[3])==1:
                GPIO.output(relaymap[2], not GPIO.input(relaymap[2]))
                updateDomeStatus()                    
                lastkey = datetime.datetime.now()
        elif c == curses.KEY_DOWN:
            if GPIO.input(relaymap[2])==1:
                GPIO.output(relaymap[3], not GPIO.input(relaymap[3]))
                updateDomeStatus()                    
                lastkey = datetime.datetime.now()
        elif c == ord('4'):
            global servostatus
            if servostatus == 10.:
                servostatus = 4.75
                showMessage("Servo closing telescope")
            else:
                servostatus = 10.
                showMessage("Servo opening telescope")
            servoPWM.ChangeDutyCycle(servostatus)
            time.sleep(.1)
            GPIO.output(16, 0)
            updateDomeStatus()                    
            time.sleep(1.)
            GPIO.output(16, 1)
            time.sleep(.1)
            servoPWM.ChangeDutyCycle(100.)
		
        elif c == ord('1'):
            current = GPIO.input(relaymap[4])
            GPIO.output(relaymap[4], not current)
            updateDomeStatus()                    
        elif c == ord('2'):
            current = GPIO.input(relaymap[5])
            GPIO.output(relaymap[5], not current)
            updateDomeStatus()                    
        elif c == ord('3'):
            current = GPIO.input(relaymap[6])
            GPIO.output(relaymap[6], not current)
            updateDomeStatus()                    
        elif c==-1:
            # No user interaction. 
            toronto.date = ephem.now()
            siderial = str(toronto.sidereal_time())
            ready = select.select([acceleration_socket], [], [], 0.1)
            if ready[0]:
                data = acceleration_socket.recv(4096)
                acc = norm([convword(data[0:2]), convword(data[2:4]), convword(data[4:6])])
                alt1 = 180./math.pi*math.atan2(-acc[0],math.sqrt(acc[1]*acc[1]+acc[2]*acc[2]))
                alt2 = 180./math.pi*math.atan2(-acc[1],math.sqrt(acc[2]*acc[2]+acc[0]*acc[0]))
                alt3 = 180./math.pi*math.atan2(-acc[2],math.sqrt(acc[0]*acc[0]+acc[1]*acc[1]))
            else:
                    alt1,alt2,alt3=0.,0.,0.
            ready = select.select([voltage_socket], [], [], 0.1)
            if ready[0]:
                data = voltage_socket.recv(4096)
                volt = ord(data[0])
            else:
                volt = 0.
             
            statusUpdate('Time UTC/siderial/az/bank', time.strftime("%H:%M:%S", time.gmtime())+" / "+siderial+ " / %6.3f / %6.3f / %f" %(alt1,alt3,volt))                  
            # Wait for next update
            time.sleep(0.05)
        elif c == ord('q'):
            finish()
        elif c == ord('e'):
            start_manual_alignment_e()
        elif c == ord('w'):
            start_manual_alignment_w()
        elif c == ord('!'):
            curses.echo() 
            s = menuwin.getstr(0,0, 15)
            curses.noecho() 
            if len(s)>0:
                s = "!" + s + ";"
                showMessage("Send: "+s)
                telescope_lock.acquire()
                ret = telescope_cmd(s)
                telescope_lock.release()
                if ret is None:
                    showMessage("Recv: None")
                else:
                    showMessage("Recv: "+ret)
        elif c == ord('g'):
            alignment_mode = "goto"
            statusUpdate("Alignment mode", "GoTo next coordinates.")
        elif c == ord('f') or c == ord("F"):
            if c == ord('f'):
                steps = focusstepperinc
            else:
                steps = -focusstepperinc
            stepperMove(steps)
    

wrapper(main)
finish()
