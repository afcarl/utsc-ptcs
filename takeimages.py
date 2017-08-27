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
#
#  killall gvfsd-gphoto2

import os
import time
import glob
import client
import socket
import sys
if len(sys.argv)<2:
    print("Usage ./takeimages.py SEC NUM ISO")
    exit(-1)
iso = "3200"
N = 1
S = sys.argv[1]
if len(sys.argv)>2:
    N = int(sys.argv[2])
    if len(sys.argv)>3:
        iso = sys.argv[3]

d = time.strftime("%Y-%m-%d")

start = len(glob.glob("./images/%s/full*.jpg"%d))
    
r = os.system("gphoto2 --set-config /main/imgsettings/imageformat=8")<<8
if r!=0:
    print("\033[91mProblem encountered trying to set image format.\033[0m")

for i in range(start,N+start):
    if os.path.isfile("capt0000.jpg"):
        print("Deleting old image file...")
        os.system("rm -f capt0000.jpg")
    print("Configuring camera...")
    r = os.system("gphoto2 --set-config capture=on --set-config iso=%s"%iso)<<8
    if r!=0:
        print("\033[91mProblem encountered trying to set ISO.\033[0m")
    r = os.system("gphoto2 --set-config shutterspeed=bulb")<<8
    if r!=0:
        print("\033[91mProblem encountered trying to set shutterspeed.\033[0m")
    r = os.system("gphoto2 --set-config eosremoterelease=Immediate --wait-event=%ss --set-config eosremoterelease=\"Release Full\" --wait-event-and-download=5s | sed -n '/UNKNOWN/!p'"%S)
    if r!=0:
        print("\033[91mProblem encountered trying to take image. Make sure camera is connected and not in use.\033[0m")
        
    print("\033[92mImage %d/%d captured.\033[0m"%(i-start+1,N))
    os.system("mkdir -p images/%s" % d)
    os.system("cp capt0000.jpg images/%s/full_%05d_iso%s_shutter%ss.jpg"%(d,i,iso,S))
    os.system("cp capt0001.cr2 images/%s/full_%05d_iso%s_shutter%ss.cr2"%(d,i,iso,S))
    os.system("convert -resize 2000x1333 capt0000.jpg images/%s/medium_%05d_iso%s_shutter%ss.jpg"%(d,i,iso,S))
    os.system("convert -resize 800x533 capt0000.jpg images/%s/small_%05d_iso%s_shutter%ss.jpg"%(d,i,iso,S))
    os.system("mv capt0001.cr2 latest.cr2")
    os.system("mv capt0000.jpg latest.jpg")
    os.system("ln -f -s %s/small_%05d_iso%s_shutter%ss.jpg images/latest_small.jpg"%(d,i,iso,S))
    os.system("ln -f -s %s/medium_%05d_iso%s_shutter%ss.jpg images/latest_medium.jpg"%(d,i,iso,S))
    os.system("ln -f -s %s/full_%05d_iso%s_shutter%ss.jpg images/latest_full.jpg"%(d,i,iso,S))

