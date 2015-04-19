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
import Image
import os

def rename(name, num):
    renamecmd = "mv %s %s%i.jpg"%("capt0000.jpg",name,num)
    os.system(renamecmd)

def capture_image():
    cmd = "gphoto2 --capture-image-and-download --force-overwrite"
    os.system(cmd)


def capture_bulb_image():
    cmd = "gphoto2 --set-config shutterspeed=bulb"
    os.system(cmd)
    cmd = "gphoto2 --set-config bulb=1 eosremoterelease=Immediate --wait-event=120s --set-config eosremoterelease=Off --wait-event-and-download=2s"
    os.system(cmd)


numphoto = int(raw_input("Number of shots:"))
filename = raw_input("Filename(and path) start:")
for a in range(0,numphoto):
    capture_image()
    rename(filename, a)
#image = Image.open("capt0000.jpg")
#image.show()
