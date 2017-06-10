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
import time
import glob
import client
import socket
import sys
if len(sys.argv)<3:
    print("Usage ./takeimages.py SEC NUM [1]")
    exit(-1)

if len(sys.argv)==4:
    cont = True
else:
    cont = False
N = int(sys.argv[2])
S = sys.argv[1]

if cont:
    start = len(glob.glob("./capt_multi_*.jpg"))
else:
    start = 0

for i in range(start,N+start):
    if os.path.isfile("capt0000.jpg"):
        print("Deleting old image file...")
        os.system("rm -f capt0000.jpg")
    print("Configuring camera...")
    r = os.system("gphoto2 --set-config capture=on --set-config iso=3200")<<8
    if r!=0:
        print("\033[91mProblem encountered trying to set ISO.\033[0m")
    r = os.system("gphoto2 --set-config shutterspeed=bulb")<<8
    if r!=0:
        print("\033[91mProblem encountered trying to set shutterspeed.\033[0m")
    print("Taking a 30 second exposure...")
    r = os.system("gphoto2 --set-config eosremoterelease=Immediate --wait-event=%ss --set-config eosremoterelease=\"Release Full\" --wait-event-and-download=2s"%S)
    if r!=0:
        print("\033[91mProblem encountered trying to take image. Make sure camera is connected and not in use.\033[0m")
        
    print("\033[92mImage captured.\033[0m")
    d = time.strftime("%Y-%m-%d")
    os.system("mkdir images")
    os.system("mkdir images/%s" % d)
    os.system("cp capt0000.jpg images/%s/capt_multi_%05d.jpg"%(d,i))
