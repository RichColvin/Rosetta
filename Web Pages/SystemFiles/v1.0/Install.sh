#! /home/cnc/Downloads
# ##################################################
# Rosetta Application
#
# This installs the Rosetta application
#    2025-03-03 - R. Colvin - initial file
#
# 		  	  Fore	  Back
# Colors   	   Gnd     Gnd
# ----------- ----    ----
# Black     	30		40
# Red     		31		41
# Green   		32		42
# Yellow  		33		43
# Blue    		34		44
# Purple  		35		45
# Cyan    		36		46
# Lt Gray   	37		47
#
# Highlight		     Code
# ------------------ ----
# Simple text	 		0
# Bold text				1
# Low intensity text	2
# Underline text		4
# Blinking text			5
# Strickthrough Text	9
#
TITLE='\033[0;34;1;47m'		# Blue on Lt Gray
KEYNOTE='\033[0;37;0;41m'	# Lt Gray on Red
COMMENT='\033[0;30;0;47m'	# Black on Lt Gray
NOCOLOR='\e[0m'
#
# ##################################################
# Step 1 - Setup the Mesa card.
# 
echo -e "${TITLE}##################################################${NOCOLOR}"
echo -e "${TITLE}Step 1 - Mesa card${NOCOLOR}"
#
# Create the location where they are to be
echo -e "${COMMENT}Creating location /usr/lib/firmware/hm2/hostmot2${NOCOLOR}"
cd /usr/lib/firmware/hm2
sudo mkdir hostmot2
#
# Copy the files
echo -e "${COMMENT}Copying the files to /usr/lib/firmware/hm2/hostmot2${NOCOLOR}"
cd /usr/lib/firmware/hm2/hostmot2
sudo cp /home/cnc/Downloads/7i92t_rosetta.bin .
sudo cp /home/cnc/Downloads/7i92t_rosetta.pin .
sudo cp /home/cnc/Downloads/PIN_Rosetta_34.vhd .
#
# Flash the Mesa card
echo -e "${COMMENT}Flashing the Mesa Card Configuration${NOCOLOR}"
mesaflash --device 7i92t --addr 192.168.1.121 --write 7i92t_rosetta.bin --reload
#
# ##################################################
# Step 2 - Copy Rosetta Files
echo -e "${TITLE}##################################################${NOCOLOR}"
echo -e "${TITLE}Step 2 - Rosetta configuration for LinuxCNC${NOCOLOR}"
#
# Unzip the files to where they are to be
echo -e "${COMMENT}Unzip the files to /home/cnc/lnuxcnc/configs/Rosetta${NOCOLOR}"
sudo unzip Rosetta.zip -d /home/cnc/lnuxcnc/configs 
#
# Set the security for the subdirectories
echo -e "${COMMENT}All all access to /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes${NOCOLOR}"
sudo chmod 777 -R /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes
echo -e "${COMMENT}All all access to /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display${NOCOLOR}"
sudo chmod 777 -R /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Display
