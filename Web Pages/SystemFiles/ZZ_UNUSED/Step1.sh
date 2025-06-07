#! /home/cnc/Downloads
# ##################################################
# Rosetta Application
#
# This sets up autologin and disables screen locking
#    2025-03-08 - R. Colvin - initial file
# ##################################################
# Step 1
# Files needed for configuring the system and the Mesa card.
# 
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>> Step 1 <<<<<<<<<<<<<<<<<<\e[0m"
# Copy the file
echo -e "\e[0;33;1;44m Original file in /etc/lightdm renamed to be lightdm-backup.conf \e[0m"
cd /etc/lightdm
sudo mv lightdm.conf lightdm-backup.conf
echo -e "\e[0;33;1;44m Copying the updated lightdm file \e[0m"
sudo cp /home/cnc/Downloads/lightdm.conf .
# ##################################################
# Step 1d
# File gets used in the startup before the main screen appears. 
# It replaces the default image file.
#
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>> Step 2 <<<<<<<<<<<<<<<<<<\e[0m"
# Copy the files
echo -e "\e[0;33;1;44m Disable light-locker \e[0m"
echo "Hidden=true" | sudo tee -a /etc/xdg/autostart/light-locker.desktop
sudo dpkg-reconfigure lightdm
echo -e "\e[0;33;1;44m Manual Steps \e[0m"
echo "Open Applications | Settings | Power Manager"
echo "      On the Display tab,"
echo "            Turn Display power manager off."
echo "            Set Blank after to 60 minutes"
echo "      On the Security tab"
echo "            Set Automatically lock the session to Never"
echo "            Uncheck Lock screen when system is going to sleep"
echo ""
echo "then reboot the system"
# ##################################################