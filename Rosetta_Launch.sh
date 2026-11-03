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
#   Rosetta_Launch.sh
#
# Purpose:
#   Desktop-launcher entry point for a LinuxCNC session. Runs
#   Rosetta_Setup/Rosetta_Generate_Local_Ini.py, which builds this machine's
#   configuration from the tracked templates and
#   ~/Documents/RosettaSet_v1.ini:
#     Rosetta.local.ini (next to Rosetta.ini - see Rosetta_Generate_Local_Ini.py's
#       header for why it must live there): axis/channel assignment,
#       units, speed limits, jog speeds, backlash;
#     Rosetta.local.hal and Rosetta_Display/Rosetta_PostGUI_v1.local.hal: Mesa
#       card(s), each role on its channel, limit jacks, E-stop button,
#       signal tower, sounds;
#     Rosetta_Display/Rosetta_Splash.local.ngc: the start-up preview drawing.
#   Then starts LinuxCNC on Rosetta.local.ini. If the generator reports a
#   problem it exits non-zero and LinuxCNC isn't started (set -e). The
#   tracked templates are never changed, so a `git pull` never clobbers
#   a machine-local setting.
#
#   Point the desktop launcher's Exec= at this script instead of at
#   `linuxcnc Rosetta.ini` directly.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 01 August 2026
#   1.1 - 18 October 2026 - Purpose brought up to date.
#   1.2 - 02 November 2026 - Renamed from REB_Launch.sh (Rosetta);
#         finds the repo from its own folder.
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rosetta
# system. Use of this system constitutes consent to the terms
# outlined below.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
#       The above copyright notice and this permission notice shall be
#       included in all copies or substantial portions of the
#       Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Except as contained in this notice, the name of COPYRIGHT HOLDERS
# shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization from COPYRIGHT HOLDERS.
#######################################################################

set -e

# The repo is the folder this script is in (not a fixed /home/<login>
# path - the login is changing from reuben to rosetta).
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
LOCAL_INI="$REPO_DIR/Rosetta.local.ini"

python3 "$REPO_DIR/Rosetta_Setup/Rosetta_Generate_Local_Ini.py"
exec linuxcnc "$LOCAL_INI"
