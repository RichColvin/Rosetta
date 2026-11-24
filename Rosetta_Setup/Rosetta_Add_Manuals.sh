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
#   Rosetta_Add_Manuals.sh
#
# Purpose:
#   Adds "Rosetta User Manual" and "Rosetta Gcode Library" - the
#   offline copies of the manuals in Rosetta_User_Manual/ and
#   Rosetta_Gcode_Library/, which arrive with every git pull - once
#   per machine, in two places:
#     - the desktop (Rich, 21 November 2026), as trusted launchers so
#       Xfce doesn't ask "Untrusted application launcher" on first use
#       (the trust is the file's sha256 in the gio attribute
#       metadata::xfce-exe-checksum, like Rosetta_Renaming.py keeps);
#     - the Applications menu's Rosetta submenu (the MenuLibre <Menu>
#       named menulibre-rose-engine-butler in
#       ~/.config/menus/xfce-applications.menu, same as
#       Rosetta_Add_GeoChuck_Designer.sh; backup:
#       xfce-applications.menu.before-manuals).
#   Each opens the manual's index.html in the default web browser
#   (xdg-open) straight from disk - no Internet connection needed.
#
#   Run by Rosetta_Setup/Rosetta_Update_Settings.py on every update
#   (ONE_TIME_STEPS) - which is how existing machines get them. Writes
#   ~/.config/Rosetta/manuals-added once everything is in place and
#   from then on does nothing, so an owner who removes an icon doesn't
#   get it back. If the desktop session can't be reached (e.g. run over
#   ssh, so the trust can't be set) or the Rosetta submenu is missing,
#   it says so and tries again on the next update. --force runs it
#   again regardless of the marker.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 21 November 2026
#   1.1 - 24 November 2026 - also finds a Rosetta submenu named
#         menulibre-rosetta (a machine whose submenu was made by
#         hand in MenuLibre after the Rosetta renaming)
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MARKER="$HOME/.config/Rosetta/manuals-added"
APPS_DIR="$HOME/.local/share/applications"
MENU="$HOME/.config/menus/xfce-applications.menu"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null)"
if [ -z "$DESKTOP_DIR" ] || [ "$DESKTOP_DIR" = "$HOME" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Manuals: icons already added on this machine."
    exit 0
fi

# write_entry <file> <name> <comment> <page> <icon>
write_entry() {
    cat > "$1" <<DESKTOP_ENTRY
[Desktop Entry]
Version=1.1
Type=Application
Name=$2
Comment=$3
Icon=$REPO_DIR/Rosetta_Setup/Images/$5
Exec=xdg-open $REPO_DIR/$4
Terminal=false
Categories=X-XFCE;menulibre-rose-engine-butler;
DESKTOP_ENTRY
}

ENTRIES=(
    "rosetta-user-manual.desktop|Rosetta User Manual|The Rosetta User Manual (works without the Internet)|Rosetta_User_Manual/index.html|Rosetta_User_Manual.png"
    "rosetta-gcode-library.desktop|Rosetta Gcode Library|The Rosetta Gcode Library (works without the Internet)|Rosetta_Gcode_Library/index.html|Rosetta_Gcode_Library.png"
)

all_done=true
mkdir -p "$APPS_DIR" "$DESKTOP_DIR" "$(dirname "$MARKER")" || exit 1

for item in "${ENTRIES[@]}"; do
    IFS='|' read -r file name comment page icon <<< "$item"

    # --- Applications menu entry ---
    write_entry "$APPS_DIR/$file" "$name" "$comment" "$page" "$icon" || exit 1

    # --- Desktop icon, trusted ---
    target="$DESKTOP_DIR/$file"
    if [ ! -f "$target" ]; then
        write_entry "$target" "$name" "$comment" "$page" "$icon" || exit 1
        chmod +x "$target"
    fi
    digest="$(sha256sum "$target" | cut -d' ' -f1)"
    if gio set "$target" metadata::xfce-exe-checksum "$digest" 2>/dev/null; then
        echo "Manuals: $name is on the desktop."
    else
        echo "Manuals: $name is on the desktop, but it couldn't be marked trusted"
        echo "(no desktop session?) - will try again on the next update."
        all_done=false
    fi
done

# --- List both in the Rosetta submenu ---
python3 - "$MENU" <<'ADD_TO_MENU'
import re, shutil, sys
path = sys.argv[1]
entries = ["rosetta-user-manual.desktop", "rosetta-gcode-library.desktop"]
try:
    text = open(path).read()
except OSError:
    print("Manuals: no " + path + " - Rosetta submenu not found.")
    sys.exit(2)
block = re.search(r"<Menu>\s*<Name>menulibre-(?:rose-engine-butler|rosetta)</Name>.*?</Menu>", text, re.S)
if not block:
    print("Manuals: the Rosetta submenu isn't in " + path + ".")
    sys.exit(2)
missing = [e for e in entries if e not in block.group(0)]
if not missing:
    sys.exit(0)
last = block.group(0).rfind("</Include>")
if last < 0:
    print("Manuals: the Rosetta submenu has no entries to add beside.")
    sys.exit(2)
cut = block.start() + last + len("</Include>")
line_start = text.rfind("\n", 0, text.rfind("<Include>", 0, cut)) + 1
indent = text[line_start:text.find("<Include>", line_start)]
addition = "".join("\n%s<Include>\n%s\t<Filename>%s</Filename>\n%s</Include>" % (indent, indent, e, indent)
                   for e in missing)
shutil.copy2(path, path + ".before-manuals")
open(path, "w").write(text[:cut] + addition + text[cut:])
ADD_TO_MENU
if [ $? != 0 ]; then
    echo "Manuals: menu entries written, but not listed in the Rosetta submenu - will try again next update."
    all_done=false
else
    echo "Manuals: added to Applications > Rosetta."
fi

if [ "$all_done" = true ]; then
    date '+%Y-%m-%d %H:%M' > "$MARKER"
fi
exit 0
