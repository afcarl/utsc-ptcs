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
import os
import sys
import time
import socket

if len(sys.argv)==4:
    sec = int(sys.argv[1])
    inc = int(sys.argv[2])
    n = int(sys.argv[3])
else:
    print("Usage: ./focus.py SEC FOCUSINC FOCUSN")
    print("                  ^-- integration time")
    print("                      ^-- increment per trial")
    print("                               ^-- trial in each direction")
    print("                                   total = 4 * FOCUSN")
    quit(0)
        
print("Opening ssh tunnel to telescope control system...")
os.system("ssh -L 10002:localhost:10002 observer@rein009.utsc.utoronto.ca sleep 10  & ")
time.sleep(0.5)
try:
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_socket.connect(("localhost", 10002))
except Exception as e:
    print(e)
    print("\033[91mCannot open connection to telescope control system.\033[0m")
    quit(0)
os.system("rm images/focus/*.*")

focus = 0
piccount = 0
for direction in [1, -1, -1, 1]:
    for i in range(n):
        print("Taking image %d/%d."%(piccount+1,n*4))
        r = os.system("./takeimages.py %d 1 3200"%sec)<<8
        if r!=0:
            print("\033[91mProblem encountered trying to take image. Make sure camera is connected and not in use.\033[0m")
            quit(0)
        time.sleep(0.25)
        os.system("convert images/latest_full.jpg -gravity Center -crop 15\%%\! images/focus/pic%04d_focus%+04d.jpg"%(piccount,focus))
        send_socket.send("Focus"+";"+"%d"%(direction*inc))
        focus += direction*inc
        piccount += 1
        time.sleep(0.5)

#else:
#    print("\033[91mCalibration failed.\033[0m")
#quit(0)

