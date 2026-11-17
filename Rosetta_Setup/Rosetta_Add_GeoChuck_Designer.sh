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
#   Rosetta_Add_GeoChuck_Designer.sh
#
# Purpose:
#   Adds "Geometric Chuck Designer" to the Applications menu's Rosetta submenu,
#   once per machine: writes ~/.local/share/applications/
#   rosetta-geochuck-designer.desktop (running Rosetta_GeoChuck_Designer.sh,
#   icon Rosetta_Setup/Images/Rosetta_GeoChuck.png), then lists it in
#   the submenu. The submenu was made with MenuLibre and names its
#   entries file by file in ~/.config/menus/xfce-applications.menu (the
#   <Menu> named menulibre-rose-engine-butler - MenuLibre's name for it
#   from before the Rosetta renaming), so an <Include><Filename> is
#   added there (backup: xfce-applications.menu.before-geochuck-designer).
#   Without that submenu the entry is still written but the marker
#   isn't, so the next update tries again.
#
#   Run by the installer, and by Rosetta_Setup/Rosetta_Update_Settings.py
#   on every update (ONE_TIME_STEPS) - which is how machines built
#   before the Geometric Chuck Designer get it. Writes
#   ~/.config/Rosetta/geochuck-designer-added once done and from then on
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
#   1.0 - 17 November 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MARKER="$HOME/.config/Rosetta/geochuck-designer-added"
ENTRY="$HOME/.local/share/applications/rosetta-geochuck-designer.desktop"
MENU="$HOME/.config/menus/xfce-applications.menu"

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Geometric Chuck Designer menu entry: already added on this machine."
    exit 0
fi

mkdir -p "$(dirname "$ENTRY")" "$(dirname "$MARKER")" || exit 1
cat > "$ENTRY" <<DESKTOP_ENTRY || exit 1
[Desktop Entry]
Version=1.1
Type=Application
Name=Geometric Chuck Designer
Comment=Design a geometric chuck pattern and save it as a G-code program
Icon=$REPO_DIR/Rosetta_Setup/Images/Rosetta_GeoChuck.png
Exec=bash $REPO_DIR/Rosetta_GeoChuck_Designer.sh
Path=$REPO_DIR/
Terminal=false
Categories=X-XFCE;menulibre-rose-engine-butler;
DESKTOP_ENTRY

# List it in the Rosetta submenu.
python3 - "$MENU" <<'ADD_TO_MENU'
import re, shutil, sys
path = sys.argv[1]
entry = "rosetta-geochuck-designer.desktop"
try:
    text = open(path).read()
except OSError:
    print("Geometric Chuck Designer menu entry: no " + path + " - Rosetta submenu not found.")
    sys.exit(2)
block = re.search(r"<Menu>\s*<Name>menulibre-rose-engine-butler</Name>.*?</Menu>", text, re.S)
if not block:
    print("Geometric Chuck Designer menu entry: the Rosetta submenu isn't in " + path + ".")
    sys.exit(2)
if entry in block.group(0):
    sys.exit(0)
last = block.group(0).rfind("</Include>")
if last < 0:
    print("Geometric Chuck Designer menu entry: the Rosetta submenu has no entries to add beside.")
    sys.exit(2)
cut = block.start() + last + len("</Include>")
line_start = text.rfind("\n", 0, text.rfind("<Include>", 0, cut)) + 1
indent = text[line_start:text.find("<Include>", line_start)]
addition = "\n%s<Include>\n%s\t<Filename>%s</Filename>\n%s</Include>" % (indent, indent, entry, indent)
shutil.copy2(path, path + ".before-geochuck-designer")
open(path, "w").write(text[:cut] + addition + text[cut:])
ADD_TO_MENU
if [ $? != 0 ]; then
    echo "Geometric Chuck Designer menu entry: written, but not listed in the Rosetta submenu - will try again next update."
    exit 0
fi
touch "$MARKER"
echo "Geometric Chuck Designer menu entry: added (Applications > Rosetta)."
