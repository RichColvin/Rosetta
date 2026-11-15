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
#                         Rosetta                                     #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Rosetta_Add_Rosette_Designer.sh
#
# Purpose:
#   Adds "Rosette Designer" to the Applications menu's Rosetta submenu,
#   once per machine: ~/.local/share/applications/
#   rosetta-rosette-designer.desktop, in the submenu's category
#   (menulibre-rose-engine-butler - the name MenuLibre gave it before
#   the Rosetta renaming), running Rosetta_Rosette_Designer.sh, icon
#   Rosetta_Setup/Images/Rosetta_Rosette.png.
#
#   Run by the installer, and by Rosetta_Setup/Rosetta_Update_Settings.py
#   on every update (ONE_TIME_STEPS) - which is how machines built
#   before the Rosette Designer get it. Writes
#   ~/.config/Rosetta/rosette-designer-added once done and from then on
#   does nothing, so an owner who removes the entry doesn't get it
#   back. --force runs it again regardless of the marker.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 15 November 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MARKER="$HOME/.config/Rosetta/rosette-designer-added"
ENTRY="$HOME/.local/share/applications/rosetta-rosette-designer.desktop"

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Rosette Designer menu entry: already added on this machine."
    exit 0
fi

mkdir -p "$(dirname "$ENTRY")" "$(dirname "$MARKER")" || exit 1
cat > "$ENTRY" <<DESKTOP_ENTRY || exit 1
[Desktop Entry]
Version=1.1
Type=Application
Name=Rosette Designer
Comment=Design a software rosette and save it as a G-code program
Icon=$REPO_DIR/Rosetta_Setup/Images/Rosetta_Rosette.png
Exec=bash $REPO_DIR/Rosetta_Rosette_Designer.sh
Path=$REPO_DIR/
Terminal=false
Categories=X-XFCE;menulibre-rose-engine-butler;
DESKTOP_ENTRY
touch "$MARKER"
echo "Rosette Designer menu entry: added (Applications > Rosetta)."
