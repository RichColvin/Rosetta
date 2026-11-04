#!/usr/bin/env python3
#######################################################################
#   RRRRRR    OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT    AA       #
#   RR   RR  OO    OO SS       EE          TT       TT      AAAA      #
#   RR   RR  OO    OO SS       EE          TT       TT     AA  AA     #
#   RRRRRR   OO    OO  SSSSSS  EEEEEE      TT       TT    AA    AA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AAAAAAAA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AA    AA    #
#   RR    RR  OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA    #
#                                                                     #
# Rosetta                                                             #
#######################################################################
#
# File:
#   Rosetta_Report_Version.py
#
# Purpose:
#   Run by Rosetta_Update_Settings.py on every update. Reports which Rosetta
#   O/S version this machine is running, so Colvin Tools can see who is
#   still using the system and what version they're on (useful if they
#   call for support).
#
#   Identified by this Pi's own hardware serial (HARDWARE_ID_PATHS
#   below) - unique with no coordination needed, so it's always
#   included and never collides, even for a self-built machine. The
#   friendly serial number an owner can set (Rosetta_Set_Serial_Number.sh,
#   ~/.config/Rosetta/serial - e.g. "4") is reported alongside it as a
#   label only, for talking to support; it does NOT need to be unique,
#   since the hardware ID is what actually identifies the machine.
#
#   POSTs the report as JSON to REPORT_URL
#   (https://support.roseenginebutler.com/reb_report.php, a small PHP
#   script that appends each report to a log file server-side). Every
#   report is also always logged locally first
#   (~/.config/Rosetta/report_log.jsonl), regardless of whether the POST
#   succeeds, so nothing is lost if a machine is offline at update time
#   - send_report only ever sends the report built THIS run, though; it
#   doesn't replay older lines from the log if a previous send failed
#   (a possible later addition once we've seen how often that happens
#   in practice).
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
#   1.1 - 23 October 2026 - REPORT_URL is live
#         (support.roseenginebutler.com/reb_report.php)
#   1.2 - 02 November 2026 - Rosetta: new REPORT_URL; reads the
#         "O/S ..." label with or without the old "REB " in front
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

import json
import os
import re
import time
import urllib.error
import urllib.request

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL_UI_PATH = os.path.join(REPO_DIR, "Rosetta_Display", "Rosetta_Panel_v1.ui")

SERIAL_PATH = os.path.expanduser("~/.config/Rosetta/serial")
REPORT_LOG_PATH = os.path.expanduser("~/.config/Rosetta/report_log.jsonl")

# Checked in order; the first that exists wins. Both are standard ways
# to read a Raspberry Pi's own unique board serial.
HARDWARE_ID_PATHS = (
    "/proc/cpuinfo",
    "/sys/firmware/devicetree/base/serial-number",
)

REPORT_URL = "https://colvintools.com/Rosetta/Support/reb_report.php"
REPORT_TIMEOUT_SECONDS = 10

# The label said "REB O/S ..." until the Rosetta rebranding (02 November
# 2026); either form is read.
VERSION_LABEL_PATTERN = re.compile(r">(?:REB )?O/S ([^<]+?) - ([^<]+?)</property>")


def read_hardware_id():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Serial"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    try:
        with open("/sys/firmware/devicetree/base/serial-number", "rb") as f:
            return f.read().split(b"\x00", 1)[0].decode("ascii", "replace")
    except OSError:
        pass
    return None


def read_friendly_serial():
    try:
        with open(SERIAL_PATH, "r") as f:
            value = f.read().strip()
    except OSError:
        return None
    return value or None


def read_version():
    '''
    Pulls "1.0 beta 1" and "20 October 2026" out of the main panel's
    "O/S 1.0 Beta 1.2 - 26 October 2026" label (Rosetta_Panel_v1.ui) - the
    one CLAUDE.md's update procedure keeps current, so it's read here
    rather than kept as a separate copy that could drift.
    '''
    try:
        with open(PANEL_UI_PATH, "r") as f:
            text = f.read()
    except OSError:
        return None, None
    match = VERSION_LABEL_PATTERN.search(text)
    if not match:
        return None, None
    return match.group(1).strip(), match.group(2).strip()


def build_report():
    version, version_date = read_version()
    return {
        "hardware_id": read_hardware_id(),
        "serial_number": read_friendly_serial(),
        "version": version,
        "version_date": version_date,
        "reported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def send_report(report):
    '''
    Logs the report locally first (so it's never lost even if the POST
    below fails or there's no network), then POSTs it to REPORT_URL.
    A failed POST only warns - it must never stop the rest of the
    update.
    '''
    os.makedirs(os.path.dirname(REPORT_LOG_PATH), exist_ok=True)
    with open(REPORT_LOG_PATH, "a") as f:
        f.write(json.dumps(report) + "\n")
    print("Version report logged to " + REPORT_LOG_PATH + ": " + json.dumps(report))

    if not REPORT_URL:
        return
    request = urllib.request.Request(
        REPORT_URL, data=json.dumps(report).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=REPORT_TIMEOUT_SECONDS) as response:
            print("Version report sent to " + REPORT_URL + " (" + str(response.status) + ")")
    except (urllib.error.URLError, OSError) as e:
        print("WARNING: could not send version report to " + REPORT_URL + ": " + str(e))


def report_version():
    try:
        send_report(build_report())
        return 0
    except OSError as e:
        print("WARNING: could not report this machine's version: " + str(e))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(report_version())
