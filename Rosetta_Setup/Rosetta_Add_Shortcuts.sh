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
#   Rosetta_Add_Shortcuts.sh
#
# Purpose:
#   Adds two folder shortcuts, once per machine:
#     - Thunar's Places panel (~/.config/gtk-3.0/bookmarks):
#       "Rosetta" (the repo) and "Gcode" (its gcode folder). Until the
#       Rosetta renaming (02 November 2026) the first was
#       "RoseEngineButler"; Rosetta_Update_Settings.py renames it.
#     - Two launchers on the Xfce panel that holds the File Manager
#       launcher (the pop-up bar at the bottom of the screen), placed
#       right after it, opening the same folders in Thunar - icons
#       Rosetta_Setup/Images/Rosetta_Folder.png and Rosetta_Folder-Gcode.png.
#
#   Run by the installer, and by Rosetta_Setup/Rosetta_Update_Settings.py on
#   every update (that runs the freshly pulled copy, unlike
#   Rosetta_Update.sh's own steps, which only change on the update after) -
#   which is how machines built before these shortcuts existed (S/N 1
#   and S/N 2) get them. Once both are in place it writes
#   ~/.config/Rosetta/shortcuts-added and from then on does nothing, so an
#   owner who removes a shortcut doesn't get it back. Each part also
#   checks first and never adds a second copy. If the panel can't be
#   reached (no desktop session - e.g. run over ssh) it says so and
#   tries again on the next update. --force runs it again regardless of
#   the marker.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 20 October 2026
#   1.1 - 02 November 2026 - Rosetta renaming: the repo shortcut is
#         named "Rosetta", launcher files rosetta-<id>.desktop
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
GCODE_DIR="$REPO_DIR/gcode"
MARKER="$HOME/.config/Rosetta/shortcuts-added"
BOOKMARKS="$HOME/.config/gtk-3.0/bookmarks"
PANEL_DIR="$HOME/.config/xfce4/panel"

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Folder shortcuts: already added on this machine."
    exit 0
fi

# --- Thunar's Places panel -------------------------------------------
mkdir -p "$(dirname "$BOOKMARKS")"
touch "$BOOKMARKS"
add_bookmark() {
    local uri="file://$1" name="$2"
    if grep -q "^$uri\( \|$\)" "$BOOKMARKS"; then
        echo "Folder shortcuts: Places already has $name."
    else
        echo "$uri $name" >> "$BOOKMARKS"
        echo "Folder shortcuts: added $name to Thunar's Places."
    fi
}
add_bookmark "$REPO_DIR" "Rosetta"
add_bookmark "$GCODE_DIR" "Gcode"

# --- Launchers on the bottom bar -------------------------------------
panel_done=false
if ! command -v xfconf-query > /dev/null || ! xfconf-query -c xfce4-panel -p /panels > /dev/null 2>&1; then
    echo "Folder shortcuts: the Xfce panel settings can't be reached (no desktop"
    echo "session?) - the bottom-bar launchers will be added on the next update."
else
    # The panel (and position) of the File Manager launcher.
    target_panel=""
    after_id=""
    for panel in $(xfconf-query -c xfce4-panel -p /panels | grep -E '^[0-9]+$'); do
        for id in $(xfconf-query -c xfce4-panel -p /panels/panel-$panel/plugin-ids | grep -E '^[0-9]+$'); do
            if grep -qs 'FileManager' "$PANEL_DIR/launcher-$id/"*.desktop; then
                target_panel=$panel
                after_id=$id
            fi
            if grep -qs "^Exec=thunar \"$REPO_DIR\"$" "$PANEL_DIR/launcher-$id/"*.desktop; then
                panel_done=true
            fi
        done
    done

    if [ "$panel_done" = true ]; then
        echo "Folder shortcuts: the bottom-bar launchers are already there."
    elif [ -z "$target_panel" ]; then
        echo "Folder shortcuts: no panel with a File Manager launcher was found -"
        echo "bottom-bar launchers not added."
        panel_done=true     # nowhere sensible to put them; don't keep trying
    else
        last=$(xfconf-query -c xfce4-panel -l | grep -oE '^/plugins/plugin-[0-9]+' \
               | grep -oE '[0-9]+$' | sort -n | tail -1)
        repo_id=$((last + 1))
        gcode_id=$((last + 2))
        add_launcher() {
            local id=$1 name=$2 folder=$3 icon=$4 comment=$5
            mkdir -p "$PANEL_DIR/launcher-$id"
            cat > "$PANEL_DIR/launcher-$id/rosetta-$id.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$name
Comment=$comment
Exec=thunar "$folder"
Icon=$icon
Terminal=false
StartupNotify=true
EOF
            xfconf-query -c xfce4-panel -p /plugins/plugin-$id -n -t string -s launcher
            xfconf-query -c xfce4-panel -p /plugins/plugin-$id/items -n -a -t string -s "rosetta-$id.desktop"
        }
        add_launcher $repo_id "Rosetta" "$REPO_DIR" \
            "$REPO_DIR/Rosetta_Setup/Images/Rosetta_Folder.png" "Open the Rosetta folder"
        add_launcher $gcode_id "Gcode" "$GCODE_DIR" \
            "$REPO_DIR/Rosetta_Setup/Images/Rosetta_Folder-Gcode.png" "Open the Gcode programs folder"

        # The panel's plugin list with the two new ones after File Manager.
        args=()
        for id in $(xfconf-query -c xfce4-panel -p /panels/panel-$target_panel/plugin-ids | grep -E '^[0-9]+$'); do
            args+=(-t int -s "$id")
            if [ "$id" = "$after_id" ]; then
                args+=(-t int -s "$repo_id" -t int -s "$gcode_id")
            fi
        done
        xfconf-query -c xfce4-panel -p /panels/panel-$target_panel/plugin-ids "${args[@]}"
        if pgrep -x xfce4-panel > /dev/null; then
            xfce4-panel -r
        fi
        echo "Folder shortcuts: added the Rosetta and Gcode launchers to the"
        echo "bottom bar (hover at the bottom middle of the screen)."
        panel_done=true
    fi
fi

if [ "$panel_done" = true ]; then
    mkdir -p "$(dirname "$MARKER")"
    date '+%Y-%m-%d %H:%M' > "$MARKER"
fi
exit 0
