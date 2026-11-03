#!/bin/bash
#######################################################################
#   RRRRRR    OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT    AA       #
#   RR   RR  OO    OO SS       EE          TT       TT      AAAA      #
#   RR   RR  OO    OO SS       EE          TT       TT     AA  AA     #
#   RRRRRR   OO    OO  SSSSSS  EEEEEE      TT       TT    AA    AA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AAAAAAAA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AA    AA    #
#   RR    RR  OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA    #
#                                                                     #
# Rosetta                                                             #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Rosetta_Install_Debian_13_Trixie.sh
#
# Purpose:
#   This is used to install the Rosetta application.
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
#   1.2 - 22 January 2026 - Updated for the Trixie install.
#   1.3 - 12 August 2026 - Added creation of gcode folder.
#   1.4 - 22 August 2026 - Moved more install steps to use
#         this program.
#   1.5 - 14 October 2026 - Two-box network: no gateway/DNS on the
#         wired connection; Rosetta_Change_Network.sh flashes the card,
#         sets it to 10.10.10.10 and moves the Pi to 10.10.10.100.
#   1.6 - 16 October 2026 - The card's W5/W6 jumper change moves to
#         the end, after a shutdown (the Pi and card share one 5V
#         supply).
#   1.7 - 20 October 2026 - Adds the folder shortcuts
#         (Rosetta_Add_Shortcuts.sh).
#   1.8 - 23 October 2026 - Step 11: records the machine's serial
#         number (Rosetta_Set_Serial_Number.sh).
#   1.9 - 24 October 2026 - First line names bash; a failed step
#         exits with an error code (exit $? after an echo was 0);
#         Rosetta_Update.sh and RosettaSet_v1.ini copied without sudo, so
#         they belong to reuben, not root.
#   2.0 - 02 November 2026 - Renamed from
#         REB_Install_Debian_13_Trixie.sh (Rosetta); uses $HOME, not
#         a fixed /home/reuben, so it suits any login (rosetta).
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rosetta
# system.  Use of this system constitutes consent to the terms
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
echo -e "${TITLE}#   RRRRRR    OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT    AA       #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO SS       EE          TT       TT      AAAA      #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO SS       EE          TT       TT     AA  AA     #${NOCOLOR}"
echo -e "${TITLE}#   RRRRRR   OO    OO  SSSSSS  EEEEEE      TT       TT    AA    AA    #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO       SS EE          TT       TT    AAAAAAAA    #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO       SS EE          TT       TT    AA    AA    #${NOCOLOR}"
echo -e "${TITLE}#   RR    RR  OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA    #${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Use of this system constitutes consent to the MIT/X Consortium License ${NOCOLOR}"
echo -e "${TITLE}as it applies to the Rosetta system.                                   ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Installation program                                                   ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 1 - Setup the wired Ethernet connection (to connect to the Mesa   ${NOCOLOR}"
echo -e "${TITLE}card)                                                                  ${NOCOLOR}"

# Add the wired Ethernet network connection
echo -e "${CMNTTEXT}Add the wired Ethernet network connection${NOCOLOR}"

# 192.168.1.120 for now - a new Mesa card answers at its factory
# address, 192.168.1.121. Rosetta_Change_Network.sh (Step 2) moves this
# connection to 10.10.10.100 once the card is set up. No gateway or DNS:
# nothing but the Pi and the Mesa cards is on this network, and a
# gateway here would clash with a home network that also uses
# 192.168.1.x - the Pi's internet is on Wi-Fi.
# Remove any left by an earlier run of this installer first - with
# several of the same name, nmcli and Rosetta_Change_Network.sh change only one.
for uuid in $(nmcli -t -f UUID,NAME con show | awk -F: '$2 == "Wired Ethernet" {print $1}'); do
    nmcli con delete "$uuid"
done
nmcli con add type ethernet con-name "Wired Ethernet" ipv4.address 192.168.1.120/24 ipv4.method manual
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: nmcli failed.                                             ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                   ${NOCOLOR}"
    exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 2 - Update the Mesa card configuration                            ${NOCOLOR}"

# Create the location where they are to be
echo -e "${CMNTTEXT}Create the directory${NOCOLOR} /usr/lib/firmware/hm2/hostmot2"
cd /usr/lib/firmware
sudo mkdir hm2
cd hm2
sudo mkdir hostmot2

# Copy the files
echo -e "${CMNTTEXT}Copy the files to /usr/lib/firmware/hm2/hostmot2                    ${NOCOLOR}"
cd /usr/lib/firmware/hm2/hostmot2
sudo cp $HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/MesaCard/7i92t_Rosetta.bin .
sudo cp $HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/MesaCard/7i92t_Rosetta.pin .
sudo cp $HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/MesaCard/PIN_Rosetta_34.vhd .

# Flash the Mesa card and give it its address. Rosetta_Change_Network.sh
# writes the firmware, stores 10.10.10.10 on the card (the base box's
# card - the expansion box's is set up the same way, as 10.10.10.11,
# with "Rosetta_Change_Network.sh expansion") and moves this Pi's wired
# connection to 10.10.10.100. --no-shutdown: the card's W5/W6 jumpers
# are moved at the end of this installer, after a shutdown, so the
# steps below still run.
echo -e "${CMNTTEXT}Flash the Mesa Card Configuration and set its address${NOCOLOR}"
$HOME/linuxcnc/configs/Rosetta/Rosetta_Change_Network.sh base --no-shutdown
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: setting up the Mesa card failed.                              ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 3 - Put key files in place                                        ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${CMNTTEXT}    .axisrc                                                         ${NOCOLOR}"
cd $HOME
cp $HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/axisrc .
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: copy of axisrc                                                ${NOCOLOR}"
   echo -e "${KEYNOTE}    from ~/linuxcnc/configs/Rosetta/Rosetta_Setup                    ${NOCOLOR}"
   echo -e "${KEYNOTE}    to ~/                                                            ${NOCOLOR}"
   echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

mv axisrc .axisrc
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: rename of axisrc                                              ${NOCOLOR}"
   echo -e "${KEYNOTE}    to .axisrc                                                       ${NOCOLOR}"
   echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${CMNTTEXT}    Rosetta_Update.sh                                              ${NOCOLOR}"
cp $HOME/linuxcnc/configs/Rosetta/Rosetta_Update.sh .
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: copy of Rosetta_Update.sh                                    ${NOCOLOR}"
   echo -e "${KEYNOTE}    from ~/linuxcnc/configs/Rosetta                                  ${NOCOLOR}"
   echo -e "${KEYNOTE}    to ~/                                                            ${NOCOLOR}"
   echo -e "${KEYNOTE}failed.                                                              ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${CMNTTEXT}    Create the gcode library                                       ${NOCOLOR}"
cd $HOME/linuxcnc/configs/Rosetta
mkdir gcode

echo -e "${CMNTTEXT}    RosettaSet_v1.ini                                              ${NOCOLOR}"
cd $HOME/Documents
cp $HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/RosettaSet_v1.ini .

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 4 - Install ClamAV                                                ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
cd $HOME
mkdir ClamAv
cd ClamAv
mkdir SuspiciousFiles
sudo apt install -y clamav
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install ClamAV                                      ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 5 - Install MenuLibre                                             ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
sudo apt install -y menulibre
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install MenuLibre                                   ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 6 - Install galculator                                            ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
sudo apt install -y galculator
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install galculator                                  ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 7 - Install xfce4-screenschooter                                  ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
sudo apt install -y xfce4-screenshooter
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install xfce4-screenschooter                        ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 8 - Install Claude Code                                           ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install Claude Code                                 ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

sudo apt install -y -y nodejs
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install Claude Code                                 ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install Claude Code                                 ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install Claude Code                                 ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo Install Claude Code
npm install -g @anthropic-ai/claude-code
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install Claude Code                                 ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

claude --version

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 9 - Install Chromium                                              ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
# Chromium comes from Trixie's own repository - do not add the Bookworm
# package source here; mixing Debian releases can break later upgrades.
sudo apt update

sudo apt install -y chromium
if [ $? != 0 ]; then
   echo -e "${KEYNOTE}ERROR: Could not install Chromium                                    ${NOCOLOR}"
   echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
   exit 1
fi

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 10 - Add folder shortcuts                                         ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
# Thunar Places shortcuts and bottom-bar launchers (rosette icons)
# for the Rosetta and gcode folders. Machines installed before
# this step get them from Rosetta_Update_Settings.py on their next update.
$HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/Rosetta_Add_Shortcuts.sh

echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Step 11 - Record this machine's serial number                         ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
# Optional - leave it blank if there isn't one (e.g. a self-built
# machine). The system reports its version every update, identified by
# the Pi's own hardware serial either way; this friendly number is only
# a label for talking to support. Machines installed before this step
# get asked on their next update instead.
$HOME/linuxcnc/configs/Rosetta/Rosetta_Setup/Rosetta_Set_Serial_Number.sh

# ********************************************************************
# Success
echo -e "${TITLE}System successfully installed.                                         ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"

# The Mesa card's new address (Step 2) takes effect once its W5/W6
# jumpers are moved, and they're only read when it's switched on. The
# Pi and the card share one 5V supply - switching the card on while the
# Pi runs restarts the Pi without a shutdown - so the whole machine is
# switched off for it.
echo -e "${CMNTTEXT}Last step - the Mesa card's jumpers:${NOCOLOR}"
echo -e "${CMNTTEXT}  1. Shut the Pi down (next question) and wait for the screen to go dark.${NOCOLOR}"
echo -e "${CMNTTEXT}  2. Switch the machine off.${NOCOLOR}"
echo -e "${CMNTTEXT}  3. Move the card's W5/W6 jumpers to the setting the 7i92 manual calls EEPROM.${NOCOLOR}"
echo -e "${CMNTTEXT}  4. Switch the machine on. Once the Pi has started, run${NOCOLOR}"
echo -e "${CMNTTEXT}     ~/linuxcnc/configs/Rosetta/Rosetta_Change_Network.sh check${NOCOLOR}"
echo -e "${CMNTTEXT}     - it should say the card at 10.10.10.10 answers.${NOCOLOR}"
read -r -p "Shut the Pi down now? [y/N] " answer
if [[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]; then
    sudo poweroff
fi
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
