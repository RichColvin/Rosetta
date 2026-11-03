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
#   Rosetta_Set_Serial_Number.sh
#
# Purpose:
#   Asks for, and records, this machine's friendly serial number (e.g.
#   "4", for talking to support) in ~/.config/Rosetta/serial. A self-built machine can
#   leave it blank - Rosetta_Report_Version.py always reports the Pi's own
#   hardware serial too, which is unique with no coordination needed,
#   so this friendly number is only a label, never required to be
#   unique.
#
#   Run by the installer (Step 11), and by Rosetta_Setup/Rosetta_Update_Settings.py
#   on every update, same as Rosetta_Add_Shortcuts.sh - this script decides
#   for itself whether there is anything to do: if the file already
#   holds a non-blank value, it just prints that value and exits.
#   Otherwise it prompts, so a machine that skipped this at install (or
#   was built before this step existed) gets asked again on its next
#   update, until a value is given. Skipped entirely (no prompt, no
#   error) if stdin isn't a terminal, so it never hangs a non-interactive
#   run.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 23 October 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

SERIAL_FILE="$HOME/.config/Rosetta/serial"

current=""
if [ -f "$SERIAL_FILE" ]; then
    current="$(tr -d '[:space:]' < "$SERIAL_FILE")"
fi

if [ -n "$current" ]; then
    echo "Serial number: already set to \"$current\"."
    exit 0
fi

if [ ! -t 0 ]; then
    echo "Serial number: not set, and this isn't an interactive session - skipping."
    echo "Run this again from a terminal to set it, or set it any time with:"
    echo "  $0"
    exit 0
fi

echo "This machine has no serial number recorded yet."
read -r -p "Enter this system's serial number (just the number, e.g. 4; press Enter to skip): " answer
answer="$(echo "$answer" | tr -d '[:space:]')"
if [ -z "$answer" ]; then
    echo "Serial number: skipped - you'll be asked again next update."
    exit 0
fi

mkdir -p "$(dirname "$SERIAL_FILE")"
echo "$answer" > "$SERIAL_FILE"
echo "Serial number: recorded as \"$answer\"."
exit 0
