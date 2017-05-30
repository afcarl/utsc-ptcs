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
import client
import socket

with open('apikey.txt', 'r') as content_file:
    apikey = content_file.read().strip()

## Conversion functions
def dec_raw2str(raw):
    dec = float(raw)/1073741824.0*90.0
    return "%+02d:%02d:%02d" % (int(dec), int(abs(dec)%1*60), round(abs(dec)%1*60%1*60, 1))

def ra_raw2str(raw):
    ra = float(raw)/2147483648.0 *12.0
    return  "%02d:%02d:%02d" % (int(ra),  int(ra%1*60),  round(ra%1*60%1*60, 1)) 

debug = False

alignment_side =  None
if debug:
    alignment_side = "e"

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


if os.path.isfile("capt0000.jpg") and debug==False:
    print("Deleting old image file...")
    os.system("rm -f capt0000.jpg")
print("Configuring camera...")
r = os.system("gphoto2 --set-config capture=on --set-config iso=3200")<<8
if r!=0:
    print("\033[91mProblem encountered trying to set ISO.\033[0m")
r = os.system("gphoto2 --set-config capture=on --set-config shutterspeed=10")<<8
if r!=0:
    print("\033[91mProblem encountered trying to set shutterspeed.\033[0m")
print("Taking a 10 second exposure...")
r = os.system("gphoto2 --set-config eosremoterelease=Immediate --wait-event=10s --wait-event-and-download=2s --force-overwrite >/dev/null")
if r!=0:
    print("\033[91mProblem encountered trying to take image. Make sure camera is connected and not in use.\033[0m")
    if debug==False:
        print("\033[91mExiting.\033[0m")
        quit(0)
    
print("\033[92mImage captured. Uploading to astrometry.net...\033[0m")
client = client.Client()
client.login(apikey)
upres = client.upload("./capt0000.jpg")
subid = upres["subid"]
print("\033[92mImage upload successful. Submission id is %s. Waiting for result...\033[0m" % subid)
try:
    calibrationDone = False
    while calibrationDone == False:
        time.sleep(5)

        res = client.send_request('submissions/%s' %subid)
        jobs = res.get('jobs',[])
        solved = None
        if len(jobs):
            for j in jobs:
                if j is not None:
                    break
            if j is not None:
                solved = j

        if solved is not None:
            res = client.send_request('jobs/%s' %solved)
            got = res.get("status") 
            if got == 'solving':
                print("Now solving...")
            elif got == 'success':
                res = client.send_request('jobs/%s/calibration' %solved)
                print("\033[92mCalibration successful.\033[0m")
                ra_string, dec_string = ra_raw2str(float(res["ra"])/360.*4294967296.), dec_raw2str(float(res["dec"])/90.*1073741824.)
                print("Got: %s %s."% (ra_string, dec_string))

                print("Opening ssh tunnel to telescope control system...")
                os.system("ssh -L 10002:localhost:10002 pi@rein009 sleep 10  & ")
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
                calibrationDone = True
            else:
                print(got)
                print("\033[91mCalibration failed.\033[0m")
                quit(0)
        else:
            print("Waiting in queue...")


except KeyboardInterrupt:
    print("\033[91mKeyboard interrupt.\033[0m")
    quit(0)
print("\033[92mAll done. Exiting.\033[0m")
