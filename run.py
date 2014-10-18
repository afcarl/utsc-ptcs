#!/usr/bin/python
import serial
import sys
import os
import time
import curses
from curses.textpad import Textbox, rectangle
import SocketServer
import struct
import time

class Menu():                                                          
    def __init__(self, telescope):
        self.telescope = telescope
        self.position = 0                                                    
        self.menuitems = [
            ('o','Open serial port',                telescope.open_port), 
            ('e','Set alignment side',              telescope.set_alignment_side), 
            ('r','Target right ascension',          telescope.set_target_rightascension), 
            ('d','Target declination',              telescope.set_target_declination), 
            ('a','Align from target/next stellarium slew', telescope.align_from_target), 
            ('g','Go to target',                    telescope.go_to_target), 
            ('v','Void alignment',                  telescope.void_alignment),
            ('b','Return to previous target',       telescope.previous_alignment),
            ('s','Open/close server commands',      telescope.toggle_server),
            ('p','Write observation data to file',  telescope.write_observation_data),
            ('c','Custom commands',                 telescope.send_custom_command),
            ('q','Exit',                            exit)
            ]
        
        self.window = curses.newwin(len(self.menuitems)+2,67,4,2)                                  
        self.window.keypad(1)                                                
        self.window.timeout(100)    # in ms
        
    
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
                for (index,m) in enumerate(self.menuitems):
                    if ord(m[0])==key:
                        self.position=index
                        m[2]()

            if self.telescope.server is not None:
                self.telescope.server.handle_request()


class Status():                                                          
    def __init__(self, telescope):
        self.telescope = telescope
        self.window = curses.newwin(8,67,18,2)                                  
        self.message = "PTCS initialized."
        self.last_telescope_update = 0
       
        self.telescope_state= [
            ['Alignment state',              '!AGas;', ""],  
            ['Side of the sky',              '!AGai;', ""],
            ['Current right ascension',      '!CGra;', ""],
            ['Current declination',          '!CGde;', ""],
            ['Target right ascension',       '!CGtr;', ""],
            ['Target declination',           '!CGtd;', ""]
        ]
        self.window_telescope = curses.newwin(3+len(self.telescope_state),67,26,2)                                  

        
    def display(*args):                                                       
        self = args[0]
        if len(args)>1:
            self.message = args[1]
        self.window.clear()
        self.window.border(0)
        # Time
        self.window.addstr(1, 2, "UTC Time")                    
        self.window.addstr(1, 15, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))                    
        # Port
        self.window.addstr(2, 2, "Port")                    
        portname = "Not open"
        if self.telescope.serialport:
            portname = self.telescope.serialport.name
        self.window.addstr(2, 15, portname )                    
        # Server
        self.window.addstr(3, 2, "Server")                    
        serverstatus = "Not running"
        if self.telescope.server:
            serverstatus = "Running (%s:%d)" % self.telescope.server.server_address
        self.window.addstr(3, 15, serverstatus )                    
        # Status Text
        self.window.addstr(4, 2, "---------------------------------------------------")                    
        self.window.addstr(5, 2, "Status")                    
        self.window.addstr(5, 15, self.message)                    
        self.window.refresh()
        
        
        self.window_telescope.clear()
        self.window_telescope.border(0)
        
        if self.telescope.serialport is not None or True:
            if time.time() - self.last_telescope_update > 2.: # only update the infos every 2 seconds
                self.last_telescope_update = time.time()
                # TODO UPDATE Telescope state

        self.window_telescope.addstr(1, 2, "Telescope readout:")                    
        for (index,element) in enumerate(self.telescope_state):
            self.window_telescope.addstr(index+2, 2, element[0])                    
            self.window_telescope.addstr(index+2, 30, element[2])                    

        self.window_telescope.refresh()

    def get_telescope_status(self):

        self.telescope.serialport.readline()
        self.telescope.serialport.write('!AGas;') # GetAlignmentState
        self.telescope.serialport.write('!AGai;') # GetAlginmentSide
        self.telescope.serialport.write('!CGra;') # GetRA
        self.telescope.serialport.write('!CGde;') # GetDec
        self.telescope.serialport.write('!CGtr;') # GetTargetRA
        self.telescope.serialport.write('!CGtd;') # GetTargetDec
        f = self.telescope.serialport.readline()
        
        return [a, b, c, d, e, f]


class Server(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data

#    def __init__(self,telescope):
#        self.telescope = telescope
#        self.running = False
#        self.conn = None
#        self.socket = None
#        self.TCP_IP = '127.0.0.1'
#        self.TCP_PORT = 10001
#        BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
#
#    def toggle(self):
#        if self.running:
#            self.close()
#        else:
#            self.open()
#
#    def open(self):
#        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        self.socket.bind((self.TCP_IP, self.TCP_PORT))
#        self.socket.settimeout(None)
#        self.socket.listen(1)
#        self.conn, self.addr = self.socket.accept()
#        self.running = True
#        self.telescope.set_status("Server port open.")
#    def close(self):
#        self.running = False
#        conn.close()
#        self.telescope.set_status("Server port closed.")

class Telescope():
    def __init__(self, stdscreen):
        self.server = None
        self.serialport = None
        self.logfilename = "observations.log"
        self.screen = stdscreen                                              
        curses.curs_set(0)
        self.screen.addstr(1, 2, "UTSC | PTCS", curses.A_BOLD)
        self.screen.addstr(2, 2, "University of Toronto Scarborough | Python Telescope Control System", curses.A_BOLD)
        #self.screen.border()
        self.screen.refresh()
        self.screen.immedok(True)
        main_menu_items = [                                                  
                ('beep', curses.beep),                                       
                ('flash', curses.flash),                                     
                ]                                                            
        self.status = Status(self)                       
        self.status.display()
        self.menu = Menu(self)                       
        self.menu.display()
    
    def toggle_server(self):
        if self.server == None:
            self.server = SocketServer.TCPServer(("127.0.0.1", 10001), Server)
            self.server.timeout = 0.001
            self.set_status("Server started.")
        else:
            self.server = None
            self.set_status("Server shut down.")
        
    
    def set_status(self, message):
        self.status.display(message)

    def get_param(self, prompt):
        win = curses.newwin(5, 62, 5, 5)
        curses.echo()
        curses.curs_set(2)
        win.border(0)
        win.addstr(1,2,prompt)
        r = win.getstr(3,2,55)
        curses.noecho()
        curses.curs_set(0)
        self.screen.refresh()
        return r

    def open_port(self):
        if os.uname()[0]=="Darwin":
            default_port_name = '/dev/tty.usbserial'
        else:
            default_port_name = '/dev/ttyUSB0'
        port_name = self.get_param("Serial port to open [leave blank for '"+default_port_name+"']")
        try:
            if port_name == '':
                port_name = default_port_name
            self.serialport = serial.Serial(port_name, 19200, timeout = 0.1) 
            self.set_status("Successfully opened serial port.")
        except:
            self.set_status("Opening serial port failed.")
            self.serialport = None
    
    def send(self,data):
        if len(data)<1:
            return False
        elif self.serialport is not None:
            self.serialport.write(data)
            self.set_status("Sent '%s' to telescope."%data)
            return True
        else:
            self.set_status("Did NOT send data to telescope (port not open).")
            return False
    
    def set_alignment_side(self):
        direction = self.get_param("Set alignment side [West/East]")
        if direction == "West" or direction == "East": 
            self.send('!ASas' + direction + ';')
        else:
            self.set_status("Not a valid alignment side.")

    def set_target_rightascension(self):
        ra = self.get_param("Set target Right Ascension [hh:mm:dd]")
        if len(ra)>0:
            self.send('!CStr' + ra + ';')
        else:
            self.set_status("Did not receive user input.")

    def set_target_declination(self):
        dec = self.get_param("Set target Declination [+dd:mm:ss]")
        if len(dec)>0:
            self.send('!CStd' + dec + ';')
        else:
            self.set_status("Did not receive user input.")

    def align_from_target(self):
        self.send('!AFrn;')

    def go_to_target(self):
        self.send('!GTrd;')
    
    def void_alignment(self):
        self.send('!AVoi;')

    def previous_alignment(self):
        self.send('!GTol;')
    
    def send_custom_command(self):
        command = self.get_param("Command (ommit ! and ;):")
        if len(command)>0:
            command = "!" + command + ";"
            self.send(command)
        else:
            self.set_status("Did not receive user input.")

    def write_observation_data(self):
        with open(self.logfilename, 'a') as f:
            self.serialport.readline()
            self.serialport.write('!CGra;') # GetRA
            curra = serialport.readline().split(';')[0]
            self.serialport.write('!CGde;') # GetDec
            curdec = serialport.readline().split(';')[0]
            self.serialport.write('!CGtr;') # GetTargetRA
            tarra = serialport.readline().split(';')[0]
            self.serialport.write('!CGtd;') # GetTargetDec
            tardec = serialport.readline().split(';')[0]
            printstr = alignra + " " + aligndec+ " " + tarra+ " " + tardec+ " " + curra+ " " + curdec +"\n"
            f.write(printstr)
            self.set_status("Observation data saved.")
        
if __name__ == '__main__':                                                       
    curses.wrapper(Telescope)

exit()
current_info = [';']

# Server stuff




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


def manage_string(string):
    new_string = ''
    for i in string:
        if i != ';':
            new_string += i
        else:
            break
    
    return new_string



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




conn = None
addr = None
server_running = False
stell_align = False
RA = None
DEC = None

good = True
while good: 

    for i in range(len(help_list)):
        screen.addstr(i + 3, 4, help_list[i])
    for i in range(len(current_info_titles)):
        x = i+25
        if x <= screen.getmaxyx()[0]:
            screen.addstr(i + 25, 4, current_info_titles[i])
    current_info_box()
    current_time = time.time()
    if serialport is not None:
        if current_time - start_time > 2:
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
                serialport.write('!CStd' + DEC + ';')
                alignDEC = DEC
                print serialport.readline()
                serialport.write('!CStr' + RA + ';')
                alignRA = RA
                print serialport.readline()
                serialport.write('!AFrn;')
                print serialport.readline()
                print "Alignment complete"
            elif DEC is not None and RA is not None:
                print "Go to object"
                serialport.write('!CStd' + DEC + ';')
                print serialport.readline()
                serialport.write('!CStr' + RA + ';')
                print serialport.readline()
                serialport.write('!GTrd;')
                print serialport.readline()
                print "goto complete"


##########################    
# Main comamnds

    
