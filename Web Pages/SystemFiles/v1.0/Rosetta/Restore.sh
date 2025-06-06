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
#   This restores the files to their original settings.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools.
#
# Version
#   1.0 - dd mmm 2025, R. Colvin
#
# Copyright Colvin Tools
# ********************************************************************
#
sSpaces='   '
echo -e "\e[1;33;1;44m>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<\e[0m"
# Restoring files for /home/cnc/linuxcnc/configs/Rosetta/
echo -e "\e[0;33;1;44m Restoring files\e[0m"
echo -e "$sSpaces" "\e[0;33;1;44m from /home/cnc/linuxcnc/Backup/Rosetta/\e[0m"
echo -e "$sSpaces" "\e[0;33;1;44m to /home/cnc/linuxcnc/configs/Rosetta/\e[0m"
cd /home/cnc/linuxcnc/configs/Rosetta/
sudo cp /home/cnc/linuxcnc/Backup/Rosetta/*.* .
# Restoring files for /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes
echo -e "\e[0;33;1;44m Restoring files\e[0m"
echo -e "$sSpaces" "\e[0;33;1;44m from /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Axes/\e[0m"
echo -e "$sSpaces" "\e[0;33;1;44m to /home/cnc/linuxcnc/configs/Rosetta/Rosetta_Axes/\e[0m"
cd Rosetta_Axes
sudo cp /home/cnc/linuxcnc/Backup/Rosetta/Rosetta_Axes/*.* .
