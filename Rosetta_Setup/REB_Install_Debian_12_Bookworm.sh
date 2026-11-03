#! /home/cnc/Downloads
#######################################################################
#                    RRRRRR    EEEEEEEE  BBBBBBB                      #
#                    RR   RR   EE        BB    BB                     #
#                    RR   RR   EE        BB    BB                     #
#                    RRRRRR    EEEEEE    BBBBBBB                      #
#                    RR   RR   EE        BB    BB                     #
#                    RR    RR  EE        BB    BB                     #
#                    RR    RR  EEEEEEEE  BBBBBBB                      #
#                                                                     #
# Rose Engine Butler                                                  #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Install.sh
#
# Purpose:
#   This is used to install the Rose Engine Butler application.
#   This program gets run after 
#       1. Downloading the Rose Engine Butler system 
#          (REB.zip)
#       2. Unzipping the Rose Engine Butler system files. The 
#          command needs to be run from the 
#          /home/cnc/Downloads directory.
#
#          sudo unzip REB.zip -d /home/cnc/linuxcnc/config
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 26 October 2025
#   1.1 - 23 December 2025 - Changed text from "upgrade" to
#         "update".
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rose Engine
# Butler system.  Use of this system constitutes consent to the terms
# outlined below.
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
echo -e "${TITLE}#                    RRRRRR    EEEEEEEE  BBBBBBB                      #${NOCOLOR}"
echo -e "${TITLE}#                    RR   RR   EE        BB    BB                     #${NOCOLOR}"
echo -e "${TITLE}#                    RR   RR   EE        BB    BB                     #${NOCOLOR}"
echo -e "${TITLE}#                    RRRRRR    EEEEEE    BBBBBBB                      #${NOCOLOR}"
echo -e "${TITLE}#                    RR   RR   EE        BB    BB                     #${NOCOLOR}"
echo -e "${TITLE}#                    RR   RR   EE        BB    BB                     #${NOCOLOR}"
echo -e "${TITLE}#                    RR    RR  EEEEEEEE  BBBBBBB                      #${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Use of this system constitutes consent to the MIT/X Consortium License ${NOCOLOR}"
echo -e "${TITLE}as it applies to the Rose Engine Butler system.                        ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Installation program                                                   ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
# ********************************************************************
# Step 1 - Setup the Mesa card.
# 
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 1 - Update the Mesa card                                          ${NOCOLOR}"
#
# Create the location where they are to be
echo -e "${CMNTTEXT}Create the directory${NOCOLOR} /usr/lib/firmware/hm2/hostmot2"
cd /usr/lib/firmware/hm2
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: /usr/lib/firmware/hm2 does not exist.                         ${NOCOLOR}"
    echo -e "${KEYNOTE}Ensure you have unzipped the REB system file                         ${NOCOLOR}"
    echo -e "${KEYNOTE}successfully.                                                        ${NOCOLOR}"
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
echo -e "${CMNTTEXT}Copy the files to /usr/lib/firmware/hm2/hostmot2                    ${NOCOLOR}"
#
cd /usr/lib/firmware/hm2/hostmot2
#
sudo cp /home/cnc/linuxcnc/configs/RoseEngineButler/REB_Setup/MesaCard/7i92t_REB.bin .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of                                                       ${NOCOLOR}"
    echo -e "${KEYNOTE}   7i92t_REB.bin to /usr/lib/firmware/hm2/hostmot2                   ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
sudo cp /home/cnc/linuxcnc/configs/RoseEngineButler/REB_Setup/MesaCard/7i92t_REB.pin .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of                                                       ${NOCOLOR}"
    echo -e "${KEYNOTE}   7i92t_REB.pin to /usr/lib/firmware/hm2/hostmot2                   ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
sudo cp /home/cnc/linuxcnc/configs/RoseEngineButler/REB_Setup/MesaCard/PIN_REB_34.vhd .
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: copy of                                                       ${NOCOLOR}"
    echo -e "${KEYNOTE}   PIN_REB_34.vhd to /usr/lib/firmware/hm2/hostmot2                  ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
# Flash the Mesa card
echo -e "${CMNTTEXT}Flash the Mesa Card Configuration${NOCOLOR}"
# 
mesaflash --device 7i92t --addr 192.168.1.121 --write 7i92t_REB.bin --reload
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: mesaflash failed.                                             ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
#
# ********************************************************************
# Step 2 - Setup Rose Engine Butler file directories for LinuxCNC
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 2 - Setup Rose Engine Butler file directories for LinuxCNC        ${NOCOLOR}"
#
# Set the security for the main directory
sudo chmod 777 -R /home/cnc/linuxcnc/configs/RoseEngineButler
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: chmod for /home/cnc/linuxcnc/configs/RoseEngineButler         ${NOCOLOR}"
    echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit $?
fi
echo -e "${CMNTTEXT}Security set on /home/cnc/linuxcnc/configs/RoseEngineButler         ${NOCOLOR}"
echo -e "${CMNTTEXT}--------------------------------------------------------------------${NOCOLOR}"
#
# ********************************************************************
# Step 3 - Put key files in place
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 3 - Put key files in place                                        ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
cd /home/cnc
echo -e "${CMNTTEXT}    .axisrc                                                         ${NOCOLOR}"
sudo cp /home/cnc/linuxcnc/configs/RoseEngineButler/REB_Setup/axisrc .
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: copy of axisrc                                                ${NOCOLOR}"
   echo -e "${KEYNOTE}    from /home/cnc/linuxcnc/configs/RoseEngineButler/REB_Setup       ${NOCOLOR}"
   echo -e "${KEYNOTE}    to /home/cnc/                                                    ${NOCOLOR}"
   echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit $?
fi
sudo mv axisrc .axisrc
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: rename of axisrc to .axisrc failed.                           ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit $?
fi
echo -e "${CMNTTEXT}    REB_Update.sh                                                  ${NOCOLOR}"
sudo cp /home/cnc/linuxcnc/configs/RoseEngineButler/REB_Update.sh .
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: copy of REB_Update.sh                                        ${NOCOLOR}"
   echo -e "${KEYNOTE}    from /home/cnc/linuxcnc/configs/RoseEngineButler                ${NOCOLOR}"
   echo -e "${KEYNOTE}    to /home/cnc/                                                    ${NOCOLOR}"
   echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit $?
fi
#
# ********************************************************************
# Step 4 - Install ClamAV
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 4 - Install ClamAV                                                ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
cd /home/cnc
mkdir ClamAv
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not create /home/cnc/ClamAV                             ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit $?
fi
cd ClamAv
mkdir SuspiciousFiles
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not create /home/cnc/ClamAV/SuspiciousFiles             ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit $?
fi
sudo apt install clamav
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install clamav                                      ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit $?
fi
#
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
