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
#   Rosetta_Add_Shut_Down.sh
#
# Purpose:
#   Adds "Shut Down" (Rosetta_Shut_Down.sh - checks Rosetta's programs
#   are closed, then powers the Pi off properly; icon
#   Rosetta_Setup/Images/Rosetta_Shut_Down.png), once per machine, in
#   two places:
#     - the Applications menu's Rosetta submenu: writes
#       ~/.local/share/applications/rosetta-shut-down.desktop and lists
#       it in the submenu's <Menu> (menulibre-rose-engine-butler) in
#       ~/.config/menus/xfce-applications.menu, as
#       Rosetta_Add_Rosette_Designer.sh does (backup:
#       xfce-applications.menu.before-shut-down);
#     - the bottom bar (the Xfce panel holding the File Manager
#       launcher): a launcher after the Gcode folder launcher
#       (Rosetta_Add_Shortcuts.sh), or after File Manager if that isn't
#       there.
#   Rich, 17 November 2026: the desktop's own Shut Down is hidden under
#   Applications > System > Log Out, and switching off a running Pi
#   risks the SD card.
#
#   Run by the installer, and by Rosetta_Setup/Rosetta_Update_Settings.py
#   on every update (ONE_TIME_STEPS) - which is how machines built
#   before it get it. Each part checks first and never adds a second
#   copy. Writes ~/.config/Rosetta/shut-down-added once both are done
#   and from then on does nothing, so an owner who removes one doesn't
#   get it back; without the Rosetta submenu or a desktop session
#   (e.g. over ssh) the marker isn't written and the next update tries
#   again. --force runs it again regardless of the marker.
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
MARKER="$HOME/.config/Rosetta/shut-down-added"
ENTRY="$HOME/.local/share/applications/rosetta-shut-down.desktop"
MENU="$HOME/.config/menus/xfce-applications.menu"
PANEL_DIR="$HOME/.config/xfce4/panel"
ICON="$REPO_DIR/Rosetta_Setup/Images/Rosetta_Shut_Down.png"
LAUNCH="$REPO_DIR/Rosetta_Shut_Down.sh"

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Shut Down: already added on this machine."
    exit 0
fi

# --- The Rosetta submenu ---------------------------------------------
menu_done=false
mkdir -p "$(dirname "$ENTRY")" "$(dirname "$MARKER")" || exit 1
cat > "$ENTRY" <<DESKTOP_ENTRY || exit 1
[Desktop Entry]
Version=1.1
Type=Application
Name=Shut Down
Comment=Shut the Rosetta computer down properly before switching the power off
Icon=$ICON
Exec=bash $LAUNCH
Path=$REPO_DIR/
Terminal=false
Categories=X-XFCE;menulibre-rose-engine-butler;
DESKTOP_ENTRY

python3 - "$MENU" <<'ADD_TO_MENU'
import re, shutil, sys
path = sys.argv[1]
entry = "rosetta-shut-down.desktop"
try:
    text = open(path).read()
except OSError:
    print("Shut Down menu entry: no " + path + " - Rosetta submenu not found.")
    sys.exit(2)
block = re.search(r"<Menu>\s*<Name>menulibre-rose-engine-butler</Name>.*?</Menu>", text, re.S)
if not block:
    print("Shut Down menu entry: the Rosetta submenu isn't in " + path + ".")
    sys.exit(2)
if entry in block.group(0):
    sys.exit(0)
last = block.group(0).rfind("</Include>")
if last < 0:
    print("Shut Down menu entry: the Rosetta submenu has no entries to add beside.")
    sys.exit(2)
cut = block.start() + last + len("</Include>")
line_start = text.rfind("\n", 0, text.rfind("<Include>", 0, cut)) + 1
indent = text[line_start:text.find("<Include>", line_start)]
addition = "\n%s<Include>\n%s\t<Filename>%s</Filename>\n%s</Include>" % (indent, indent, entry, indent)
shutil.copy2(path, path + ".before-shut-down")
open(path, "w").write(text[:cut] + addition + text[cut:])
ADD_TO_MENU
if [ $? = 0 ]; then
    echo "Shut Down: in the menu (Applications > Rosetta)."
    menu_done=true
else
    echo "Shut Down: menu entry written, but not listed in the Rosetta submenu - will try again next update."
fi

# --- The bottom bar --------------------------------------------------
panel_done=false
if ! command -v xfconf-query > /dev/null || ! xfconf-query -c xfce4-panel -p /panels > /dev/null 2>&1; then
    echo "Shut Down: the Xfce panel settings can't be reached (no desktop"
    echo "session?) - the bottom-bar launcher will be added on the next update."
else
    # The panel holding the File Manager launcher; the launcher goes
    # after the Gcode folder launcher if it's there, else after File Manager.
    target_panel=""
    after_id=""
    gcode_id=""
    for panel in $(xfconf-query -c xfce4-panel -p /panels | grep -E '^[0-9]+$'); do
        for id in $(xfconf-query -c xfce4-panel -p /panels/panel-$panel/plugin-ids | grep -E '^[0-9]+$'); do
            if grep -qs 'FileManager' "$PANEL_DIR/launcher-$id/"*.desktop; then
                target_panel=$panel
                after_id=$id
            fi
            if grep -qs "^Exec=thunar \"$REPO_DIR/gcode\"$" "$PANEL_DIR/launcher-$id/"*.desktop; then
                gcode_id=$id
                gcode_panel=$panel
            fi
            if grep -qs "^Exec=bash $LAUNCH$" "$PANEL_DIR/launcher-$id/"*.desktop; then
                panel_done=true
            fi
        done
    done
    if [ -n "$gcode_id" ]; then
        target_panel=$gcode_panel
        after_id=$gcode_id
    fi

    if [ "$panel_done" = true ]; then
        echo "Shut Down: the bottom-bar launcher is already there."
    elif [ -z "$target_panel" ]; then
        echo "Shut Down: no panel with a File Manager launcher was found -"
        echo "bottom-bar launcher not added."
        panel_done=true     # nowhere sensible to put it; don't keep trying
    else
        last=$(xfconf-query -c xfce4-panel -l | grep -oE '^/plugins/plugin-[0-9]+' \
               | grep -oE '[0-9]+$' | sort -n | tail -1)
        new_id=$((last + 1))
        mkdir -p "$PANEL_DIR/launcher-$new_id"
        cat > "$PANEL_DIR/launcher-$new_id/rosetta-$new_id.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Shut Down
Comment=Shut the Rosetta computer down properly before switching the power off
Exec=bash $LAUNCH
Icon=$ICON
Terminal=false
StartupNotify=true
EOF
        xfconf-query -c xfce4-panel -p /plugins/plugin-$new_id -n -t string -s launcher
        xfconf-query -c xfce4-panel -p /plugins/plugin-$new_id/items -n -a -t string -s "rosetta-$new_id.desktop"

        # The panel's plugin list with the new one after after_id.
        args=()
        for id in $(xfconf-query -c xfce4-panel -p /panels/panel-$target_panel/plugin-ids | grep -E '^[0-9]+$'); do
            args+=(-t int -s "$id")
            if [ "$id" = "$after_id" ]; then
                args+=(-t int -s "$new_id")
            fi
        done
        xfconf-query -c xfce4-panel -p /panels/panel-$target_panel/plugin-ids "${args[@]}"
        if pgrep -x xfce4-panel > /dev/null; then
            xfce4-panel -r
        fi
        echo "Shut Down: added to the bottom bar (hover at the bottom middle of the screen)."
        panel_done=true
    fi
fi

if [ "$menu_done" = true ] && [ "$panel_done" = true ]; then
    date '+%Y-%m-%d %H:%M' > "$MARKER"
fi
exit 0
