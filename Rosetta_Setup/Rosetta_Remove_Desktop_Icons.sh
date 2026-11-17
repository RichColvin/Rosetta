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
#   Rosetta_Remove_Desktop_Icons.sh
#
# Purpose:
#   Takes "Backup Rosetta" and "Update Rosetta" off the desktop, once
#   per machine (Rich, 17 November 2026): both stay in the Applications
#   menu's Rosetta submenu, so they're less prominent than the
#   everyday Rosetta and Rosetta Settings icons, which stay.
#
#   The desktop icons were made by hand when each machine was set up,
#   so they're found by what they run, not their names: a ~/Desktop
#   *.desktop file whose Exec runs Rosetta_Backup.sh or
#   Rosetta_Update.sh (or the old REB_Backup.sh / REB_Update.sh). Each
#   is removed only if the Applications menu has its own entry running
#   the same program (~/.local/share/applications), so nobody is left
#   without one; it's moved to ~/.config/Rosetta/removed-desktop-icons/,
#   not deleted.
#
#   Run by Rosetta_Setup/Rosetta_Update_Settings.py on every update
#   (ONE_TIME_STEPS). Writes ~/.config/Rosetta/desktop-icons-removed
#   once done and from then on does nothing, so an owner who puts an
#   icon back keeps it. --force runs it again regardless of the marker.
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

MARKER="$HOME/.config/Rosetta/desktop-icons-removed"
MENU_DIR="$HOME/.local/share/applications"
KEEP_DIR="$HOME/.config/Rosetta/removed-desktop-icons"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Desktop icons: already tidied on this machine."
    exit 0
fi

# program pattern (in Exec=), what to call it
removed=0
for item in "Backup|Back Up" "Update|Update"; do
    program="${item%%|*}"
    what="${item##*|}"
    pattern="(Rosetta|REB)_${program}\.sh"
    if ! grep -qsE "^Exec=.*$pattern" "$MENU_DIR"/*.desktop; then
        echo "Desktop icons: the Applications menu has no $what entry - leaving its desktop icon."
        continue
    fi
    for icon in "$DESKTOP_DIR"/*.desktop; do
        [ -f "$icon" ] || continue
        if grep -qsE "^Exec=.*$pattern" "$icon"; then
            mkdir -p "$KEEP_DIR"
            mv "$icon" "$KEEP_DIR/" && removed=$((removed + 1))
            echo "Desktop icons: took \"$(basename "$icon" .desktop)\" off the desktop (it's in Applications > Rosetta)."
        fi
    done
done

mkdir -p "$(dirname "$MARKER")"
date '+%Y-%m-%d %H:%M' > "$MARKER"
exit 0
