#! /home/cnc/Downloads
#######################################################################
#                                                                     #
#   RRRRRR     OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT   AAAA     #
#   RR   RR   OO    OO SS    SS EE          TT       TT     AA  AA    #
#   RR    RR  OO    OO SS       EE          TT       TT    AA    AA   #
#   RR   RR   OO    OO  SS      EE          TT       TT    AA    AA   #
#   RRRRRR    OO    OO   SSSS   EEEEEE      TT       TT    AA    AA   #
#   RR   RR   OO    OO      SS  EE          TT       TT    AAAAAAAA   #
#   RR    RR  OO    OO       SS EE          TT       TT    AA    AA   #
#   RR    RR  OO    OO SS    SS EE          TT       TT    AA    AA   #
#   RR    RR   OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA   #
#                                                                     #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Install.sh
#
# Purpose:
#   This is used to install the Rosetta application.
#   This program gets run after 
#       1. Downloading the Rosetta system (Rosetta.zip)
#       2. Unzipping the Rosetta system files. The command needs to be
#          run from the /home/cnc/Downloads directory.
#
#           sudo unzip Rosetta.zip -d /home/cnc/linuxcnc/config
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - dd mmm 2025, R. Colvin
#
# Copyright (c) 2025 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rosetta system.
# Use of this system constitutes consent to the terms outlined below.
#
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files (the 
# "Software"), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to 
# the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of COPYRIGHT HOLDERS
# shall not be used in advertising or otherwise to promote the sale, 
# use or other dealings in this Software without prior written 
# authorization from COPYRIGHT HOLDERS.
#
# ********************************************************************
# Colours are detailed at the end of this program
#
TITLE='\033[0;34;1;47m'     # Blue on Lt Gray
KEYNOTE='\033[0;37;0;41m'   # Lt Gray on Red
CMNTTEXT='\033[0;34;1;40m'  # Blue on Black
NOCOLOR='\e[0m'
#
# ********************************************************************
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}#                                                                     #${NOCOLOR}"
echo -e "${TITLE}#   RRRRRR     OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT   AAAA     #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR   OO    OO SS    SS EE          TT       TT     AA  AA    #${NOCOLOR}"
echo -e "${TITLE}#   RR    RR  OO    OO SS       EE          TT       TT    AA    AA   #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR   OO    OO  SS      EE          TT       TT    AA    AA   #${NOCOLOR}"
echo -e "${TITLE}#   RRRRRR    OO    OO   SSSS   EEEEEE      TT       TT    AA    AA   #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR   OO    OO      SS  EE          TT       TT    AAAAAAAA   #${NOCOLOR}"
echo -e "${TITLE}#   RR    RR  OO    OO       SS EE          TT       TT    AA    AA   #${NOCOLOR}"
echo -e "${TITLE}#   RR    RR  OO    OO SS    SS EE          TT       TT    AA    AA   #${NOCOLOR}"
echo -e "${TITLE}#   RR    RR   OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA   #${NOCOLOR}"
echo -e "${TITLE}#                                                                     #${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Use of this system constitutes consent to the MIT/X Consortium License ${NOCOLOR}"
echo -e "${TITLE}as it applies to the Rosetta system.                                   ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Installation program                                                   ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
# ********************************************************************
# Step 1 - Setup the Mesa card.
# 
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 1 - Mesa card                                                     ${NOCOLOR}"
#
# Create the location where they are to be
echo -e "${CMNTTEXT}Create the directory${NOCOLOR} /usr/lib/firmware/hm2/hostmot2"
cd /usr/lib/firmware/hm2
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: /usr/lib/firmware/hm2 does not exist.                         ${NOCOLOR}"
    echo -e "${KEYNOTE}Ensure you have unzipped the Rosetta system file successfully.       ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
sudo mkdir hostmot2
# if [ $? != 0 ]; then
#    echo -e "${KEYNOTE}ERROR: mkdir /usr/lib/firmware/hm2/hostmot2 failed.                  ${NOCOLOR}"
#    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
#    exit $?
# fi
#
# Copy the files
echo -e "${CMNTTEXT}Copy the files to /usr/lib/firmware/hm2/hostmot2${NOCOLOR}"
#
cd /usr/lib/firmware/hm2/hostmot2
#
sudo cp /home/cnc/linuxcnc/configs/Rosetta_MesaCard/7i92t_rosetta.bin .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of 7i92t_rosetta.bin to /usr/lib/firmware/hm2/hostmot2   ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
sudo cp /home/cnc/linuxcnc/configs/Rosetta_MesaCard/7i92t_rosetta.pin .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of 7i92t_rosetta.pin to /usr/lib/firmware/hm2/hostmot2   ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
sudo cp /home/cnc/linuxcnc/configs/Rosetta_MesaCard/PIN_Rosetta_34.vhd .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of PIN_Rosetta_34.vhd to /usr/lib/firmware/hm2/hostmot2  ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
# Flash the Mesa card
echo -e "${CMNTTEXT}Flash the Mesa Card Configuration${NOCOLOR}"
# 
mesaflash --device 7i92t --addr 192.168.1.121 --write 7i92t_rosetta.bin --reload
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: mesaflash failed.                                             ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
# ********************************************************************
# Step 2 - Setup Rosetta file directories for LinuxCNC
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 2 - Setup Rosetta file directories for LinuxCNC                   ${NOCOLOR}"
#
# Set the security for the main directory
echo -e "${CMNTTEXT}Set the security for /home/cnc/linuxcnc/configs/Rosetta/Rosetta     ${NOCOLOR}"
sudo chmod 777 -R /home/cnc/linuxcnc/configs/Rosetta
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: chmod for /home/cnc/linuxcnc/configs/Rosetta                  ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
# 
# Set the security for the subdirectories
echo -e "${CMNTTEXT}Set the security for /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes${NOCOLOR}"
sudo chmod 777 -R /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: chmod for /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes     ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
# 
echo -e "${CMNTTEXT}Set the security for /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display${NOCOLOR}"
sudo chmod 777 -R /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: chmod for /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display  ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
# ********************************************************************
# Step 3 - Set desktop icons
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 3 - Setup desktop icons                                           ${NOCOLOR}"
cd /home/cnc/Desktop
echo -e "${CMNTTEXT}Set the Rosetta.desktop icon                                        ${NOCOLOR}"
sudo cp "/home/cnc/linuxcnc/configs/Rosetta_Setup/Rosetta.desktop" .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of Rosetta desktop icon                                  ${NOCOLOR}"
    echo -e "${KEYNOTE}    from /home/cnc/linuxcnc/configs/Rosetta_Setup/                   ${NOCOLOR}"
    echo -e "${KEYNOTE}    to /home/cnc/Desktop failed.                                     ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
echo -e "${CMNTTEXT}Set the Restore Rosetta Config Files desktop icon                       ${NOCOLOR}"
sudo cp "/home/cnc/linuxcnc/configs/Rosetta_Setup/Restore Rosetta Config Files.desktop" .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of Restore Rosetta Config Files.desktop                  ${NOCOLOR}"
    echo -e "${KEYNOTE}    from /home/cnc/linuxcnc/configs/Rosetta_Setup/                   ${NOCOLOR}"
    echo -e "${KEYNOTE}    to /home/cnc/Desktop failed.                                     ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
sudo chmod 777 /home/cnc/Desktop/*.desktop
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: chmod for /home/cnc/Desktop/*.desktop failed                  ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
# ********************************************************************
# Step 4 - Backup key files
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Backup /home/cnc/linuxcnc/Backup/Rosetta                               ${NOCOLOR}"
cd /home/cnc/linuxcnc
sudo mkdir Backup
cd Backup
sudo mkdir Rosetta
cd Rosetta
#
cd /home/cnc/linuxcnc/Backup/Rosetta/
sudo cp /home/cnc/linuxcnc/configs/Rosetta/*.* .
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Backup /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Axes                  ${NOCOLOR}"
cd /home/cnc/linuxcnc/Backup/Rosetta/
sudo mkdir Rosetta_Axes
cd Rosetta_Axes
cd /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Axes
sudo cp /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes/*.* .
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Backup /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Custom                ${NOCOLOR}"
cd /home/cnc/linuxcnc/Backup/Rosetta/
sudo mkdir Rosetta_Custom
cd Rosetta_Custom
cd /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Custom
sudo cp /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Custom/*.* .
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Backup /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Display               ${NOCOLOR}"
cd /home/cnc/linuxcnc/Backup/Rosetta/
sudo mkdir Rosetta_Display
cd Rosetta_Display
cd /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Display
sudo cp /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display/*.* .
## ********************************************************************
# Success
echo -e "${TITLE}System successfully installed.                                         ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
#
# ********************************************************************
# Nothing follows
exit 0
# ********************************************************************
# Display Colours
#
#             Fore    Back
# Colors       Gnd     Gnd
# ----------- ----    ----
# Black         30      40
# Red           31      41
# Green         32      42
# Yellow        33      43
# Blue          34      44
# Purple        35      45
# Cyan          36      46
# Lt Gray       37      47
#
# Highlight          Code
# ------------------ ----
# Simple text           0
# Bold text             1
# Low intensity text    2
# Underline text        4
# Blinking text         5
# Strickthrough Text    9
