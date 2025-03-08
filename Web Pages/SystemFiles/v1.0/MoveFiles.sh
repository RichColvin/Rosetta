#! /home/cnc/Downloads
# ##################################################
# Rosetta Application
#
# This moves files to where they are needed
#    2025-03-03 - R. Colvin - initial file
# ##################################################
# Step 1a
# Files needed for configuring the system and the Mesa card.
# 
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>> Step 1a <<<<<<<<<<<<<<<<<<\e[0m"
# Create the location where they are to be
echo -e "\e[0;33;1;44m Creating location for the files to reside\e[0m"
cd /usr/lib/firmware/hm2
sudo mkdir hostmot2
#
# Copy the files
echo -e "\e[0;33;1;44m Copying the files to /usr/lib/firmware/hm2/hostmot2 \e[0m"
cd /usr/lib/firmware/hm2/hostmot2
sudo cp /home/cnc/Downloads/7i92t_rosetta.bin .
sudo cp /home/cnc/Downloads/7i92t_rosetta.pin .
sudo cp /home/cnc/Downloads/PIN_Rosetta_34.vhd .
# ##################################################
# Step 1b
# Files needed to define the system and Mesa card connectons.
#
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>> Step 1b <<<<<<<<<<<<<<<<<<\e[0m"
# Create the location where they are to be
echo -e "\e[0;33;1;44m Creating location for the files to reside \e[0m"
cd /home/cnc
sudo mkdir linuxcnc
cd linuxcnc
sudo mkdir configs
cd configs
sudo mkdir Rosetta
#
# Copy the files
echo -e "\e[0;33;1;44m Copying the files to /home/cnc/linuxcnc/configs/Rosettta\e[0m"
cd /home/cnc/linuxcnc/configs/Rosetta
sudo cp /home/cnc/Downloads/Rosetta.hal .
sudo cp /home/cnc/Downloads/Rosetta.ini .
sudo cp /home/cnc/Downloads/custom.hal .
sudo cp /home/cnc/Downloads/custom_gvcp.hal .
sudo cp /home/cnc/Downloads/custom_postgui.hal .
sudo cp /home/cnc/Downloads/shutdown.hal .
sudo cp /home/cnc/Downloads/tool.tbl .
# ##################################################
# Step 1c
# Files get used for changing the image on the destop icon for
# starting the system.
#
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>> Step 1c <<<<<<<<<<<<<<<<<<\e[0m"
# Copy the files
echo -e "\e[0;33;1;44m Copying the files to /home/cnc/linuxcnc/configs \e[0m"
cd /home/cnc/linuxcnc/configs
sudo cp /home/cnc/Downloads/RosettaLogo-Silver.gif .
sudo cp /home/cnc/Downloads/RosettaLogo-Black.gif .
# ##################################################
# Step 1d
# File gets used in the startup before the main screen appears. 
# It replaces the default image file.
#
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>> Step 1d <<<<<<<<<<<<<<<<<<\e[0m"
# Copy the files
echo -e "\e[0;33;1;44m Copying the files to /home/cnc/linuxcnc/configs \e[0m"
cd /home/cnc/linuxcnc/configs
sudo cp /home/cnc/Downloads/RosettaStartupImage.gif .
# ##################################################
