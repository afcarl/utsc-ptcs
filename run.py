#!/usr/bin/python
import serial
import sys
import os
import time
import curses
from curses.textpad import Textbox, rectangle
import socket
import struct
import time

class Menu(object):                                                          
    def __init__(self, telescope):
        self.telescope = telescope
        self.window = curses.newwin(17,65,2,2)                                  
        self.window.keypad(1)                                                
        
        self.position = 0                                                    
        self.menuitems = [
            ('o','Open Port',                   telescope.open_port), 
            ('e','Set Alignment Side',          None), 
            ('r','Target Right Ascension',      None), 
            ('d','Target Declination',          None), 
            ('a','Align from Target/(align from next stellarium slew)',None), 
            ('g','GoTo Target',                 None), 
            ('u','Update Current Info',         None),
            ('v','Void alignment',              None),
            ('b','Return to previous target',   None),
            ('s','Open/close server commands',  None),
            ('f','Change output filename',      None),
            ('p','Print observation data',      None),
            ('c','Custom commands',             None),
            ('q','Exit',                        exit)
            ]
    
    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.menuitems):                               
            self.position = len(self.menuitems)-1                                

    def display(self):                                                       
        while True:                                                          
            self.window.border(0)
            self.telescope.status.display()
            for index, item in enumerate(self.menuitems):                        
                if index == self.position:                                   
                    mode = curses.A_REVERSE                                  
                else:                                                        
                    mode = curses.A_NORMAL                                   

                msg = ' %s - %s ' % (item[0],item[1])                            
                self.window.addstr(1+index, 1, msg, mode)                    

            key = self.window.getch()                                        

            if key in [curses.KEY_ENTER, ord('\n')]:                         
                self.menuitems[self.position][2]()                           
            elif key == curses.KEY_UP:                                       
                self.navigate(-1)                                            
            elif key == curses.KEY_DOWN:                                     
                self.navigate(1)                                             
            else:
                for m in self.menuitems:
                    if ord(m[0])==key:
                        m[2]()


class Status(object):                                                          
    def __init__(self, telescope):
        self.telescope = telescope
        self.window = curses.newwin(8,65,22,2)                                  
        self.window.keypad(1)                                                
        self.message = "Window initialized."
        
    def display(*args):                                                       
        self = args[0]
        if len(args)>1:
            self.message = args[1]
        self.window.border(0)
        # Time
        self.window.addstr(1, 2, "UTC Time:")                    
        self.window.addstr(1, 22, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))                    
        # Port
        self.window.addstr(2, 2, "Port:")                    
        portname = "Not open"
        if self.telescope.port:
            portname = self.telescope.port.name
        self.window.addstr(2, 22, portname )                    
        # Status
        self.window.addstr(3, 2, "---------------------------------------------------")                    
        self.window.addstr(4, 2, "Status:")                    
        self.window.addstr(4, 22, self.message)                    
        self.window.refresh()


class Telescope():
    def __init__(self, stdscreen):
        self.port = None
        self.screen = stdscreen                                              
        stdscreen.border()
        self.screen.immedok(True)
        main_menu_items = [                                                  
                ('beep', curses.beep),                                       
                ('flash', curses.flash),                                     
                ]                                                            
        self.status = Status(self)                       
        self.status.display()
        self.menu = Menu(self)                       
        self.menu.display()

    def set_status(self, message):
        self.status.display(message)

    def get_param(self, prompt):
        win = curses.newwin(5, 60, 5, 5)
        curses.echo()
        win.border(0)
        win.addstr(1,2,prompt)
        r = win.getstr(3,2,55)
        curses.noecho()
        self.screen.clear()
        return r

    def open_port(self):
        self.set_status("Trying to open port.")
        if os.uname()[0]=="Darwin":
            default_port_name = '/dev/tty.usbserial'
        else:
            default_port_name = '/dev/ttyUSB0'
        port_name = self.get_param("Set port to open [leave blank for '"+default_port_name+"']")
        try:
            if port_name == '':
                port_name = default_port_name
            self.port = serial.Serial(port_name, 19200, timeout = 0.1) 
            self.set_status("Successfully opened serial port.")
        except:
            self.set_status("Opening serial port failed.")
            self.port = None
    
    def set_target_declination(self):
        dec = self.get_param("Set target Declination [+dd:mm:ss]")
        if self.port is not None:
            self.port.write('!CStd' + dec + ';')
        else:
            self.set_status

if __name__ == '__main__':                                                       
    curses.wrapper(Telescope)
print "done"
exit()
current_info = [';']

# Server stuff
TCP_IP = '127.0.0.1'
TCP_PORT = 10001
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))


def current_info_box():
    if current_info == [';']:
        pass
    else:
        new_c_i = []
        for i in range(len(current_info)):
            x = manage_string(current_info[i])
            new_c_i.append(x)
        for i in range(len(current_info)):
            screen.addstr(i + 25, 35, new_c_i[i])

def get_status():
     if port is not None:
          port.readline()
          port.write('!AGas;') # GetAlignmentState
          a = port.readline()
          port.write('!AGai;') # GetAlginmentSide
          b = port.readline()
          port.write('!CGra;') # GetRA
          c = port.readline()
          port.write('!CGde;') # GetDec
          d = port.readline()
          port.write('!CGtr;') # GetTargetRA
          e = port.readline()
          port.write('!CGtd;') # GetTargetDec
          f = port.readline()
          
          #return str(port.readline())
          return [a, b, c, d, e, f]
     else:
          nc = "Not connected."
          return [nc,nc,nc,nc,nc,nc]

def print_obs(name, alignra, aligndec):
    if alignra is not None and aligndec is not None:
        with open(name, 'a') as f:
            port.readline()
            port.write('!CGra;') # GetRA
            curra = port.readline().split(';')[0]
            port.write('!CGde;') # GetDec
            curdec = port.readline().split(';')[0]
            port.write('!CGtr;') # GetTargetRA
            tarra = port.readline().split(';')[0]
            port.write('!CGtd;') # GetTargetDec
            tardec = port.readline().split(';')[0]
            printstr = alignra + " " + aligndec+ " " + tarra+ " " + tardec+ " " + curra+ " " + curdec +"\n"
            f.write(printstr)
    else:
        print "No alignment saved"
        

def manage_string(string):
    new_string = ''
    for i in string:
        if i != ';':
            new_string += i
        else:
            break
    
    return new_string


def open_server():
    s.listen(1)
    print "Listening on", TCP_IP, TCP_PORT
    conn,addr = s.accept()
    conn.settimeout(1)
    return (conn,addr)

def unpack_command(command):
    """ Unpack the data recieved from stellarium, and converts into coordinates in RA and DEC"""
    print command
    data = struct.unpack('<hhQIi',command)
    RA_raw = data[-2]  # a value of 0x100000000 = 0x0 means 24h=0h,
                       # a value of 0x80000000 means 12h
                       # 12h = 2147483648 
    DEC_raw = data[-1] # a value of -0x40000000 means -90 degrees
                       # a value of 0x0 means 0 degrees
                       #  a value of 0x40000000 means 90 degrees
                       # 90d = 1073741824
    dec = float(DEC_raw)/1073741824.0*90.0
    if dec > 0:
        dec_string = "+" + str(int(dec)) + ":" + str(int(dec%1*60)) + ":" + str(round(dec%1*60%1*60, 1)) # convert from decimal into dms
    else:
        dec_string = str(int(dec)) + ":" + str(int(dec%1*60)) + ":" + str(round(dec%1*60%1*60, 1)) # convert from decimal into dms
    ra = float(RA_raw)/2147483648.0 *12.0
    ra_string = str(int(ra)) + ":" + str(int(ra%1*60)) + ":" + str(round(ra%1*60%1*60, 1)) # convert from decimal into hms
    return (ra_string,dec_string)

def custom_command(command):
    command = "!" + command + ";"
    port.write(command)
    print port.readline()


current_info_titles = ['Alignment State:', 'Side of the Sky:',
                       'Current Right Ascension:', 'Current Declination:',
                       'Target Right Ascension:', 'Target Declination:',
                       ' ']

conn = None
addr = None
server_running = False
stell_align = False
RA = None
DEC = None
alignRA = None
alignDEC = None
tarRA = None
tarDEC = None
filename = "observations.txt"
screen = curses.initscr()
screen.timeout(50) #stops getch() from blocking
start_time = time.time()

good = True
while good: 

    screen.clear()
    screen.border(0)
    screen.addstr(2, 2, "UTSC Python Telescope control system")
    for i in range(len(help_list)):
        screen.addstr(i + 3, 4, help_list[i])
    for i in range(len(current_info_titles)):
        x = i+25
        if x <= screen.getmaxyx()[0]:
            screen.addstr(i + 25, 4, current_info_titles[i])
    current_info_box()
    current_time = time.time()
    if port is not None:
        if current_time - start_time > 2:
            current_info = get_status()
            start_time = current_time # only update the infos every 2 seconds
    screen.refresh()
    key = screen.getch()

##########################
# Server stuff
    if server_running:
        data = None
        try:
            data = conn.recv(BUFFER_SIZE)
        except: # connection timeout, assume no data sent
            data = None
        if data is not None:
            RA, DEC = unpack_command(data) 
            data = None
            #conn.send(data)  TODO: return to stellarium the current RA and DEC from the telescope
            if stell_align and DEC is not None and RA is not None:
                stell_align = False
                print "Aligning"
                port.write('!CStd' + DEC + ';')
                alignDEC = DEC
                print port.readline()
                port.write('!CStr' + RA + ';')
                alignRA = RA
                print port.readline()
                port.write('!AFrn;')
                print port.readline()
                print "Alignment complete"
            elif DEC is not None and RA is not None:
                print "Go to object"
                port.write('!CStd' + DEC + ';')
                print port.readline()
                port.write('!CStr' + RA + ';')
                print port.readline()
                port.write('!GTrd;')
                print port.readline()
                print "goto complete"


##########################    
# Main comamnds

# Exit
    if key == 27 or key == ord('q'): #27=ESC
        good = False


    # Set target right ascension
    if key == ord('r'):
        ra = get_param("Set target Right Ascension [hh:mm:dd]")
        if port is not None:
             port.write('!CStr' + ra + ';')

    # Set alignment side
    if key == ord('e'):
        direction = get_param("Set alignment side [West/East]")
        if direction == "West" or direction == "East": # Check for valid input
            if port is not None:
                 port.write('!ASas' + direction + ';')

    # Align from target
    if key == ord('a'):
        if port is not None:
            if server_running:
                stell_align = True
            else:
                port.write('!AFrn;')
                alignRA = tarRA
                alignDEC = tarDEC

    # Goto target
    if key == ord('g'):
        if port is not None:
             port.write('!GTrd;')
             print port.readline()
    
    # Void alignment
    if key == ord('v'):
        if port is not None:
             port.write('!AVoi;')

    # previous alignment
    if key == ord('b'):
        if port is not None:
             port.write('!GTol;')
    
    # Open Server
    if key == ord('s'):
        if server_running:
            server_running = False
            print "Closing connection"
            conn.close()
        else:
            conn, addr = open_server()
            server_running = True
            print "Server open"
    
    # Change output filename
    if key == ord('f'):
        if port is not None:
            filename = get_param("Output Filename")

    # Print alignment RA, DEC, Target RA, DEC and Current RA, DEC to filename
    if key == ord('p'):
        if port is not None:
            print_obs(filename, alignRA, alignDEC)
            print "Printed"

    if key == ord('c'):
        if port is not None:
            command = get_param("Command: (ommit ! and ;)")
            custom_command(command)

    # Update information
    if key == ord('u'):
        current_info = get_status()

curses.endwin()
s.close()
