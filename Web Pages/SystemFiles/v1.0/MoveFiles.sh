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
echo Running Step 1a
# Create the location where they are to be
echo Creating location for the files to reside
cd /usr/lib/firmware/hm2
sudo mkdir hostmot2
#
# Copy the files
echo Copying the files to /usr/lib/firmware/hm2/hostmot2
cd /usr/lib/firmware/hm2/hostmot2
sudo cp /home/cnc/Downloads/7i92t_rosettad.bin .
sudo cp /home/cnc/Downloads/7i92t_rosettad.pin .
sudo cp /home/cnc/Downloads/PIN_RosettaD_34.vhd .
# ##################################################
# Step 1b
# Files needed to define the system and Mesa card connectons.
#
echo Running Step 1b
# Create the location where they are to be
echo Creating location for the files to reside
cd /home/cnc
sudo mkdir linuxcnc
cd linuxcnc
sudo mkdir configs
#
# Copy the files
echo Copying the files to /home/cnc/linuxcnc/configs
cd /home/cnc/linuxcnc/configs
sudo cp /home/cnc/Downloads/Rosettad.hal .
sudo cp /home/cnc/Downloads/Rosettad.ini .
sudo cp /home/cnc/Downloads/custom.hal .
sudo cp /home/cnc/Downloads/custom_gvcp.hal .
sudo cp /home/cnc/Downloads/shutdown.hal .
sudo cp /home/cnc/Downloads/tool.tbl .
# ##################################################
# Step 1c
# Files get used for changing the image on the destop icon for
# starting the system.
#
echo Running Step 1c
# Copy the files
echo Copying the files to /home/cnc/linuxcnc/configs
cd /home/cnc/linuxcnc/configs
sudo cp /home/cnc/Downloads/RosettaLogo-Silver.gif .
sudo cp /home/cnc/Downloads/RosettaLogo-Black.gif .
# ##################################################
# Step 1d
# File gets used in the startup before the main screen appears. 
# It replaces the default image file.
#
echo Running Step 1d
# Copy the files
echo Copying the files to /home/cnc/linuxcnc/configs
cd /home/cnc/linuxcnc/configs
sudo cp /home/cnc/Downloads/RosettaStartupImage.gif .
# ##################################################
