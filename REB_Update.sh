#!/bin/bash
#######################################################################
#                    RRRRRR    EEEEEEEE  BBBBBBB                      #
#                    RR   RR   EE        BB    BB                     #
#                    RR   RR   EE        BB    BB                     #
#                    RRRRRR    EEEEEE    BBBBBBB                      #
#                    RR   RR   EE        BB    BB                     #
#                    RR    RR  EE        BB    BB                     #
#                    RR    RR  EEEEEEEE  BBBBBBB                      #
#                                                                     #
# Rose Engine Butler                                                  #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   REB_Update.sh
#
# Purpose:
#   This updates the files pulled from GitHub.
#
# End User Customisation:
#   THE END USER OF THE ROSE ENGINE BUTLER SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 27 October 2025
#   1.1 - 23 December 2025 - Changed text from "upgrade" to
#         "update".
#   1.2 - 22 January 2026 - Updated to run on Debian 13
#             Trixie: updated directories from
#                /home/reuben/
#             to
#                /home/reuben/
#   1.3 - 27 July 2026 - The repo remote moved from HTTPS
#             to SSH, authenticated with the reuben user's SSH key.
#             Dropped sudo from the git commands so pull/stash run as
#             reuben (whose key is registered with GitHub) instead of
#             root (which has no key and would fail publickey auth).
#   1.4 - 08 October 2026 - Refreshes the EtherLab package source's
#             signing key before "apt update" (see below): its copy
#             expired 20 September 2026, which made apt update warn.
#   1.5 - 18 October 2026 - The "local changes" warning names the
#             Support Manual page by its real title; marked runnable.
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rose Engine
# Butler system.  Use of this system constitutes consent to the terms
# outlined below.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of COPYRIGHT HOLDERS
# shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization from COPYRIGHT HOLDERS.
#
# ********************************************************************
# Colours are detailed at the end of this program
#
TITLE='\033[0;34;1;47m'     # Blue on Lt Gray
KEYNOTE='\033[0;37;0;41m'   # Lt Gray on Red
CMNTTEXT='\033[0;34;1;40m'  # Blue on Black
NOCOLOR='\e[0m'
sSpaces='   '
#
# ********************************************************************
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}#   RRRRRR    OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT    AA       #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO SS       EE          TT       TT      AAAA      #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO SS       EE          TT       TT     AA  AA     #${NOCOLOR}"
echo -e "${TITLE}#   RRRRRR   OO    OO  SSSSSS  EEEEEE      TT       TT    AA    AA    #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO       SS EE          TT       TT    AAAAAAAA    #${NOCOLOR}"
echo -e "${TITLE}#   RR   RR  OO    OO       SS EE          TT       TT    AA    AA    #${NOCOLOR}"
echo -e "${TITLE}#   RR    RR  OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA    #${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Use of this system constitutes consent to the MIT/X Consortium License ${NOCOLOR}"
echo -e "${TITLE}as it applies to the Rosetta system.                                   ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}Update the system                                                     ${NOCOLOR}"
echo -e "${TITLE}                                                                       ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Pull latest files from GitHub                                          ${NOCOLOR}"
cd /home/reuben/linuxcnc/configs/RoseEngineButler

# Set aside any local changes to tracked files - e.g. the operator's tool
# table (REB_Custom/REB_Tool.tbl) or HAL additions (REB_Custom/REB_Custom.hal)
# - so they can't make the pull fail, then put them back afterwards.
# (This used to stash and never restore, so those edits looked lost after
# every update.)
stashes_before=$(git stash list | wc -l)
git stash push -m "REB_Update $(date '+%Y-%m-%d %H:%M')"
stashes_after=$(git stash list | wc -l)
stashed=false
if [ "$stashes_after" -gt "$stashes_before" ]; then
    stashed=true
fi

git pull
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: git pull failed.                                              ${NOCOLOR}"
    if [ "$stashed" = true ]; then
        git stash pop
    fi
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit 1
fi

if [ "$stashed" = true ]; then
    if git stash pop; then
        echo -e "${TITLE}Local changes (e.g. tool table) restored                               ${NOCOLOR}"
    else
        # The update changed the same lines. Leave the files exactly as
        # pulled (no half-merged conflict markers for LinuxCNC to trip
        # over); the local changes stay safe in the stash.
        git reset --hard -q HEAD
        echo -e "${KEYNOTE}WARNING: local changes could not be re-applied automatically.       ${NOCOLOR}"
        echo -e "${KEYNOTE}They are saved - see 'git stash list' (REB_Update ...) and the       ${NOCOLOR}"
        echo -e "${KEYNOTE}Support Manual page 'Updating Rose Engine Butler' to restore them.   ${NOCOLOR}"
    fi
fi
echo -e "${TITLE}Latest files pulled from GitHub                                        ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Add any new settings to this machine's settings file                  ${NOCOLOR}"
# Adds to /home/reuben/Documents/REBset_v1.ini any setting the freshly
# pulled REB_Setup/REBset_v1.ini has but this machine's file doesn't
# (never changing existing values). Runs after the pull so it uses the
# latest starting file. A problem here is reported but doesn't stop the
# rest of the update.
python3 /home/reuben/linuxcnc/configs/RoseEngineButler/REB_Setup/REB_Update_Settings.py
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}WARNING: settings file could not be checked - see the message above.  ${NOCOLOR}"
fi
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Refresh the EtherLab package signing key                               ${NOCOLOR}"
# The EtherLab (EtherCAT) package source that LinuxCNC's setup adds is
# signed by an openSUSE key that is re-issued with a later expiry date
# from time to time; once this machine's copy expires, apt update warns
# "Signing key ... is bad ... Expired". Fetch the current copy from the
# source's own Release.key and install it - only if it is still
# EtherLab's key (same fingerprint). Skipped when the source isn't set
# up; a failure here only warns, since nothing REB uses comes from it.
ETHERLAB_FPR="5D6B2B6E61B29B37F7A5E407A94819A7CB97A204"
ETHERLAB_SOURCES="/etc/apt/sources.list.d/ethercat.sources"
if [ -f "$ETHERLAB_SOURCES" ]; then
    etherlab_url=$(sed -n 's/^URIs:[[:space:]]*//p' "$ETHERLAB_SOURCES" | head -1)
    etherlab_keyring=$(sed -n 's/^Signed-By:[[:space:]]*//p' "$ETHERLAB_SOURCES" | head -1)
    etherlab_tmp=$(mktemp)
    if [ -n "$etherlab_url" ] && [ -n "$etherlab_keyring" ] \
       && curl -fsSL "${etherlab_url%/}/Release.key" | gpg --dearmor > "$etherlab_tmp" 2>/dev/null \
       && gpg --show-keys --with-colons "$etherlab_tmp" 2>/dev/null | grep -q "^fpr:*${ETHERLAB_FPR}:"; then
        if cmp -s "$etherlab_tmp" "$etherlab_keyring"; then
            echo -e "${TITLE}EtherLab signing key is already current                                ${NOCOLOR}"
        elif sudo install -m 644 -o root -g root "$etherlab_tmp" "$etherlab_keyring"; then
            echo -e "${TITLE}EtherLab signing key refreshed                                         ${NOCOLOR}"
        else
            echo -e "${KEYNOTE}WARNING: could not install the EtherLab signing key.                 ${NOCOLOR}"
        fi
    else
        echo -e "${KEYNOTE}WARNING: could not fetch the EtherLab signing key - apt update may   ${NOCOLOR}"
        echo -e "${KEYNOTE}warn about it, but the Rosetta update carries on.                    ${NOCOLOR}"
    fi
    rm -f "$etherlab_tmp"
else
    echo -e "${TITLE}No EtherLab package source on this machine - nothing to refresh        ${NOCOLOR}"
fi
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Update the package indexes                                             ${NOCOLOR}"
sudo apt update
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: Package update failed                                         ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit 1
fi
echo -e "${TITLE}Latest package updates secured                                         ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Update the system                                                      ${NOCOLOR}"
sudo apt upgrade -y
if [ $? != 0 ]; then
    echo -e "${KEYNOTE}ERROR: System upgrade failed                                         ${NOCOLOR}"
    echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY                                       ${NOCOLOR}"
    exit 1
fi
echo -e "${TITLE}System Updated                                                         ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
