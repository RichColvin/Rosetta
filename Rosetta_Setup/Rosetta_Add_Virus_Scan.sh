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
#   Rosetta_Add_Virus_Scan.sh
#
# Purpose:
#   Schedules the weekly ClamAV virus scan, once per machine - until
#   now a hand step (the Support Manual's Virus Scanning page, which
#   had the builder add a line with "sudo crontab -e"). Writes
#   /etc/cron.d/rosetta-virus-scan: each Monday at 03:00, at the
#   lowest priority and only if LinuxCNC isn't running, clamscan scans
#   the login's home folder and /media (any inserted USB stick), moves
#   anything found to ~/ClamAv/SuspiciousFiles and logs to
#   ~/ClamAv/ScanLog.txt. The home folder is written out in full
#   (/home/rosetta, or /home/reuben on older machines): the scan runs
#   as root, for whom ~ would mean /root.
#
#   A machine whose root schedule already has a clamscan line (added
#   by hand) is left as it is, so the scan doesn't run twice. ClamAV's
#   virus signatures update themselves (the clamav-freshclam service);
#   nothing is needed for that.
#
#   Run by the installer (Step 4, after ClamAV is installed), and by
#   Rosetta_Setup/Rosetta_Update_Settings.py on every update
#   (ONE_TIME_STEPS) - which is how machines built before it get it;
#   it asks for the login's password (sudo). Writes
#   ~/.config/Rosetta/virus-scan-added once done and from then on
#   does nothing, so an owner who removes the schedule doesn't get it
#   back. --force runs it again regardless of the marker (and rewrites
#   the schedule). Rosetta_Install_Check.py checks the result.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 24 November 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

MARKER="$HOME/.config/Rosetta/virus-scan-added"
CRON_FILE="${ROSETTA_CRON_FILE:-/etc/cron.d/rosetta-virus-scan}"
SCAN_DIR="$HOME/ClamAv"

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Virus scan: already scheduled on this machine."
    exit 0
fi
mkdir -p "$SCAN_DIR/SuspiciousFiles" "$(dirname "$MARKER")" || exit 1

if ! command -v clamscan > /dev/null; then
    echo "Virus scan: ClamAV isn't installed (sudo apt install clamav) - will try again next update."
    exit 0
fi

if [ "$1" != "--force" ] && sudo crontab -l 2>/dev/null | grep -v '^[[:space:]]*#' | grep -q clamscan; then
    echo "Virus scan: root's schedule already has a scan (added by hand) - left as it is."
    date '+%Y-%m-%d %H:%M' > "$MARKER"
    exit 0
fi

# cron.d lines name the user to run as (root - so the scan can read
# and move any file); the file must be owned by root and not writable
# by others, or cron ignores it.
tmp="$(mktemp)" || exit 1
cat > "$tmp" <<CRON_LINES
# Rosetta weekly virus scan - written by Rosetta_Setup/Rosetta_Add_Virus_Scan.sh.
# Each Monday at 03:00, unless LinuxCNC is running. Results: $SCAN_DIR/ScanLog.txt
SHELL=/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin
0 3 * * 1 root pgrep -x linuxcncsvr >/dev/null || nice -n 19 ionice -c3 clamscan -r -i --exclude-dir=$SCAN_DIR --move=$SCAN_DIR/SuspiciousFiles --log=$SCAN_DIR/ScanLog.txt $HOME /media
CRON_LINES
if sudo install -o root -g root -m 644 "$tmp" "$CRON_FILE"; then
    rm -f "$tmp"
    echo "Virus scan: scheduled for Mondays at 03:00 ($CRON_FILE)."
    date '+%Y-%m-%d %H:%M' > "$MARKER"
else
    rm -f "$tmp"
    echo "Virus scan: couldn't write $CRON_FILE - will try again next update."
fi
exit 0
