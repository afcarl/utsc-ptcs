#!/usr'bin/python
import serial
import sys
import os
import time

port = None
current_info = [';']

def open_port():
    port_name = ''
    if os.uname()[0]=="Darwin":
         default_port_name = '/dev/tty.usbserial'
    else:
         default_port_name = '/dev/ttyUSB0'
    try:
         if port_name == '':
              port_name = default_port_name
         ser = serial.Serial(port_name, 19200, timeout = 0.1) # try a baud rate of 9600, or 4800... also look into the API for the telescope controls
         return ser
    except:
         return None

def current_info_box():
    if current_info == [';']:
        pass
    else:
        new_c_i = []
        for i in range(len(current_info)):
            x = manage_string(current_info[i])
            new_c_i.append(x)
        for i in range(len(current_info)):
            screen.addstr(i + 15, 35, new_c_i[i])

def get_status():
     if port is not None:
          port.readline()
          port.write('!AGas;')
          a = port.readline()
          port.write('!AGai;')
          b = port.readline()
          port.write('!CGra;')
          c = port.readline()
          port.write('!CGde;')
          d = port.readline()
          port.write('!CGtr;')
          e = port.readline()
          port.write('!CGtd;')
          f = port.readline()
          
          #return str(port.readline())
          return [a, b, c, d, e, f]
     else:
          nc = "Not connected."
          return [nc,nc,nc,nc,nc,nc]

def manage_string(string):
    new_string = ''
    for i in string:
        if i != ';':
            new_string += i
        else:
            break
    
    return new_string

def get_param(prompt):
    win = curses.newwin(5, 60, 5, 5)
    win.border(0)
    win.addstr(1,2,prompt)
    return win.getstr(3,2,55)


if __name__ == "__main__":
    port = open_port()
    while not port is None:
        command = "!" + str(raw_input("Command: "))
        port.write(command + ";")
        print port.readline().split(";")
    print "Port is None"
