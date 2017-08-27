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

if len(sys.argv)==1:
    sec = 10
else:
    try:
        sec = int(sys.argv[1])
    except:
        # expect test image
        sec = None
        testimage = sys.argv[1]



## Conversion functions
def dec_raw2str(raw):
    dec = float(raw)/1073741824.0*90.0
    return "%+02d:%02d:%02d" % (int(dec), int(abs(dec)%1*60), round(abs(dec)%1*60%1*60, 1))

def ra_raw2str(raw):
    ra = float(raw)/2147483648.0 *12.0
    return  "%02d:%02d:%02d" % (int(ra),  int(ra%1*60),  round(ra%1*60%1*60, 1)) 

alignment_side =  None

while alignment_side is not "e" and alignment_side is not "w":
    try:
        alignment_side = raw_input("Enter alignment side (e for east/w for west): ")
    except KeyboardInterrupt:
        quit(0)
    except:
        pass
if alignment_side == "e":
    alignment_side = "East"
elif alignment_side == "w":
    alignment_side = "West"
else:
    raise ValueError("Alignmentside not valid")

if sec is not None:
    # Take image
    if os.path.isfile("latest.jpg"):
        print("Deleting old image file...")
        os.system("rm -f latest.jpg")
    r = os.system("./takeimages.py %d 1 3200"%sec)<<8
    if r!=0:
        print("\033[91mProblem encountered trying to take image. Make sure camera is connected and not in use.\033[0m")
        quit(0)
    time.sleep(1)
    
    print("\033[92mImage captured.\033[0m")
else:
    os.system("cp %s latest.jpg" % testimage)
os.system("rm images/astrometry/*.*")
os.system("convert -resize 800x533 latest.jpg images/astrometry/latest_small.jpg")
os.system("cd images/astrometry && /usr/local/astrometry/bin/solve-field latest_small.jpg --overwrite -L 30 -H 50 -u \"arcminwidth\" --parity neg --cpulimit 10 --crpix-center")

ra,dec = None, None
try:
    with open('images/astrometry/latest_small.wcs', 'r') as f:
        content = f.read()
        while len(content):
            line = content [0:80]
            content = content[80:]
            s = line.split("=")
            if len(s) ==2:
                if s[0] == "CRVAL1  ":
                    ra = s[1].split("/")[0].strip()
                if s[0] == "CRVAL2  ":
                    dec = s[1].split("/")[0].strip()
except:
    pass
if ra != None and dec != None:
    print("\033[92mCalibration successful.\033[0m")
    ra_string, dec_string = ra_raw2str(float(ra)/360.*4294967296.), dec_raw2str(float(dec)/90.*1073741824.)
    print("Got: %s %s."% (ra_string, dec_string))

    print("Opening ssh tunnel to telescope control system...")
    os.system("ssh -L 10002:localhost:10002 observer@rein009.utsc.utoronto.ca sleep 10  & ")
    time.sleep(1)
    print("Opening connection to telescope control system...")

    try:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect(("localhost", 10002))
    except Exception as e:
        print(e)
        print("\033[91mCannot open connection to telescope control system.\033[0m")
        quit(0)

    print("Sending calibration data to telescope control system...")
    send_socket.send(alignment_side+";"+ra_string+";"+dec_string)
    time.sleep(1)

else:
    print("\033[91mCalibration failed.\033[0m")
    quit(0)

