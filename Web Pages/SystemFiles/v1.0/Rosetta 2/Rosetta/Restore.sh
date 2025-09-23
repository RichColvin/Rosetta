#! /home/cnc/linuxcnc/
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
#   Restore.sh
#
# Purpose:
#   This is used to restore the Rosetta application back to the 
#   defaults.
#
#   This program gets run when the user wants to reset everything.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 08 Jun 2025, R. Colvin
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
TITLE='\033[0;34;1;47m'		# Blue on Lt Gray
KEYNOTE='\033[0;37;0;41m'	# Lt Gray on Red
CMNTTEXT='\033[0;34;1;40m'	# Blue on Black
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
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 1 - Restoring files    									         ${NOCOLOR}"
echo -e "${TITLE}     from /home/cnc/linuxcnc/Backup/Rosetta					         ${NOCOLOR}"
echo -e "${TITLE}     to   /home/cnc/linuxcnc/configs/Rosetta					         ${NOCOLOR}"
cd /home/cnc/linuxcnc/configs/Rosetta/
sudo cp /home/cnc/linuxcnc/Backup/Rosetta/*.* .
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 2 - Restoring files    									         ${NOCOLOR}"
echo -e "${TITLE}     from /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Axes    	         ${NOCOLOR}"
echo -e "${TITLE}     to   /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes  	         ${NOCOLOR}"
cd /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes
sudo cp /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Axes/*.* .
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 3 - Restoring files    									         ${NOCOLOR}"
echo -e "${TITLE}     from /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Custom    	         ${NOCOLOR}"
echo -e "${TITLE}     to   /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Custom 	         ${NOCOLOR}"
cd /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Custom
sudo cp /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Custom/*.* .
#
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 4 - Restoring files    									         ${NOCOLOR}"
echo -e "${TITLE}     from /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Display   	         ${NOCOLOR}"
echo -e "${TITLE}     to   /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display 	         ${NOCOLOR}"
cd /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display
sudo cp /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Display/*.* .
# ********************************************************************
# Success
echo -e "${TITLE}System successfully restored.                                          ${NOCOLOR}"
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
