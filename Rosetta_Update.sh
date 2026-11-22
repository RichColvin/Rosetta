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
# Rosetta                                                             #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Rosetta_Update.sh
#
# Purpose:
#   This updates the files pulled from GitHub.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
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
#   1.6 - 02 November 2026 - Renamed from REB_Update.sh (Rosetta);
#             finds the repo itself instead of a fixed
#             /home/reuben path.
#   1.7 - 16 November 2026 - Before anything changes, asks the user
#             to close Rosetta (LinuxCNC), Rosetta Settings, the
#             Rosette Designer, Back Up / Restore and Checkout, and
#             waits until they are (Rich): otherwise they'd keep
#             running the old program, and apt could replace
#             LinuxCNC's files under it. It asks rather than closing
#             them - LinuxCNC may be cutting, Settings may have
#             unsaved tuning, a backup may be copying.
#   1.8 - 17 November 2026 - also asks for the Geometric Chuck
#             Designer to be closed.
#   1.9 - 22 November 2026 - after "apt upgrade", also installs
#             packages it kept back (an upgrade needing a new
#             package, e.g. libcamera0.7 -> 0.8), but only when the
#             only packages it would remove are automatically
#             installed libraries and none is part of LinuxCNC;
#             otherwise it lists them and leaves them for support.
#   2.0 - 22 November 2026 - then runs "apt autoremove" (e.g. old
#             standard kernels), after marking the running kernel's
#             packages as installed in their own right, and only
#             when nothing it would remove is LinuxCNC's or the
#             running kernel's; otherwise it lists them.
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rosetta
# system.  Use of this system constitutes consent to the terms
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
echo -e "${TITLE}Check that Rosetta's programs are closed                               ${NOCOLOR}"

# Rosetta's programs that are open now, one name per line (this user's
# processes only). Python programs are matched by the script they run,
# so an editor with the file open doesn't count.
rosetta_programs_open() {
    local me
    me=$(id -u)
    pgrep -u "$me" -x linuxcncsvr >/dev/null && echo "Rosetta (LinuxCNC)"
    pgrep -u "$me" -f "python[0-9.]* [^ ]*Rosetta_Settings\.py" >/dev/null && echo "Rosetta Settings"
    pgrep -u "$me" -f "python[0-9.]* [^ ]*Rosetta_Rosette_Designer\.py" >/dev/null && echo "Rosette Designer"
    pgrep -u "$me" -f "python[0-9.]* [^ ]*Rosetta_GeoChuck_Designer\.py" >/dev/null && echo "Geometric Chuck Designer"
    pgrep -u "$me" -f "python[0-9.]* [^ ]*Rosetta_Backup\.py" >/dev/null && echo "Back Up to USB / Restore from USB"
    pgrep -u "$me" -f "python[0-9.]* [^ ]*Rosetta_Checkout\.py" >/dev/null && echo "Checkout"
    return 0
}

while true; do
    still_open=$(rosetta_programs_open)
    if [ -z "$still_open" ]; then
        break
    fi
    echo -e "${KEYNOTE}Please close these programs before updating - they would keep running ${NOCOLOR}"
    echo -e "${KEYNOTE}the old version until restarted:                                     ${NOCOLOR}"
    while IFS= read -r name; do
        echo "    $name"
    done <<< "$still_open"
    if [ ! -t 0 ]; then
        echo -e "${KEYNOTE}PROGRAM TERMINATED PREMATURELY - close them and run the update again.${NOCOLOR}"
        exit 1
    fi
    read -r -p "Press Enter once they are closed, or type Q and Enter to cancel: " answer
    case "$answer" in
        [qQ]*)
            echo -e "${KEYNOTE}Update cancelled - nothing was changed.                              ${NOCOLOR}"
            exit 1
            ;;
    esac
done
echo -e "${TITLE}Rosetta's programs are closed                                          ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Pull latest files from GitHub                                          ${NOCOLOR}"
# The repo: this script's own folder, or - for the copy the installer
# puts in the home folder - the standard place (before the Rosetta
# renaming, 02 November 2026, that was RoseEngineButler).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if [ -d "$SCRIPT_DIR/.git" ]; then
    REPO_DIR="$SCRIPT_DIR"
elif [ -d "$HOME/linuxcnc/configs/Rosetta/.git" ]; then
    REPO_DIR="$HOME/linuxcnc/configs/Rosetta"
else
    REPO_DIR="$HOME/linuxcnc/configs/RoseEngineButler"
fi
cd "$REPO_DIR"

# Set aside any local changes to tracked files - e.g. the operator's tool
# table (Rosetta_Custom/Rosetta_Tool.tbl) or HAL additions (Rosetta_Custom/Rosetta_Custom.hal)
# - so they can't make the pull fail, then put them back afterwards.
# (This used to stash and never restore, so those edits looked lost after
# every update.)
stashes_before=$(git stash list | wc -l)
git stash push -m "Rosetta_Update $(date '+%Y-%m-%d %H:%M')"
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
        echo -e "${KEYNOTE}They are saved - see 'git stash list' (Rosetta_Update ...) and the   ${NOCOLOR}"
        echo -e "${KEYNOTE}Support Manual page 'Updating Rosetta' to restore them.              ${NOCOLOR}"
    fi
fi
echo -e "${TITLE}Latest files pulled from GitHub                                        ${NOCOLOR}"
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Add any new settings to this machine's settings file                  ${NOCOLOR}"
# Adds to ~/Documents/RosettaSet_v1.ini any setting the freshly
# pulled Rosetta_Setup/RosettaSet_v1.ini has but this machine's file doesn't
# (never changing existing values). Runs after the pull so it uses the
# latest starting file. A problem here is reported but doesn't stop the
# rest of the update.
python3 "$REPO_DIR/Rosetta_Setup/Rosetta_Update_Settings.py"
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
# up; a failure here only warns, since nothing Rosetta uses comes from it.
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
# Added 22 November 2026 - "apt upgrade" never installs or removes a
# package, so it keeps back any upgrade that needs a new package (e.g.
# Raspberry Pi's camera software moving from libcamera0.7 to 0.8, which
# installs libcamera0.8 and removes libcamera0.7). "full-upgrade" can do
# that, but can also remove packages that matter, so first see what it
# would do and only go ahead when everything it removes is an
# automatically installed library ("lib..." - pulled in by another
# package, not installed in its own right) and nothing it removes is
# part of LinuxCNC. Otherwise list the packages and carry on.
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Check for packages kept back                                           ${NOCOLOR}"
held_plan=$(LC_ALL=C apt-get -s full-upgrade 2>/dev/null)
held_installs=$(echo "$held_plan" | sed -n 's/^Inst \([^ ]*\).*/\1/p')
held_removals=$(echo "$held_plan" | sed -n 's/^Remv \([^ ]*\).*/\1/p')
if [ -z "$held_installs" ] && [ -z "$held_removals" ]; then
    echo -e "${TITLE}No packages kept back                                                  ${NOCOLOR}"
else
    held_auto=$(apt-mark showauto 2>/dev/null)
    held_blocked=""
    for pkg in $held_removals; do
        name=${pkg%%:*}
        if [[ "$name" != lib* ]] || [[ "$name" == *linuxcnc* ]] \
           || ! grep -qx -e "$name" -e "$pkg" <<< "$held_auto"; then
            held_blocked="$held_blocked $pkg"
        fi
    done
    if [ -n "$held_blocked" ]; then
        echo -e "${KEYNOTE}Some packages were kept back. Installing them would remove:          ${NOCOLOR}"
        echo "   $held_blocked"
        echo -e "${KEYNOTE}so they are left as they are. Please tell Rosetta support.           ${NOCOLOR}"
    else
        echo "Installing packages kept back:" $held_installs
        [ -n "$held_removals" ] && echo "Replacing:" $held_removals
        sudo apt-get full-upgrade -y
        if [ $? != 0 ]; then
            echo -e "${KEYNOTE}WARNING: could not install the packages kept back - the Rosetta  ${NOCOLOR}"
            echo -e "${KEYNOTE}update carries on.                                               ${NOCOLOR}"
        else
            echo -e "${TITLE}Packages kept back are now installed                                   ${NOCOLOR}"
        fi
    fi
fi
# Added 22 November 2026 - remove packages nothing needs any more,
# mostly old standard kernels left behind by kernel updates. Rosetta
# boots a real-time kernel (config.txt's kernel=kernel8_rt.img, a file
# no package owns) whose drivers in /lib/modules come from its
# linux-image package; if that package were marked as automatically
# installed, autoremove could take the drivers away and with them the
# network the Mesa cards use. So mark the running kernel's packages as
# installed in their own right first, then see what autoremove would do
# and only go ahead when nothing on the list belongs to the running
# kernel (any package naming its version, e.g. 6.12.34+rpt) or to
# LinuxCNC/Mesa. Otherwise list the packages and carry on.
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Remove packages no longer needed                                       ${NOCOLOR}"
running_kernel=$(uname -r)
kernel_version=${running_kernel%%-*}
for pkg in "linux-image-$running_kernel" "linux-headers-$running_kernel"; do
    if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed" \
       && apt-mark showauto 2>/dev/null | grep -qx "$pkg"; then
        sudo apt-mark manual "$pkg" > /dev/null && echo "Kept the running kernel's $pkg"
    fi
done
unneeded=$(LC_ALL=C apt-get -s autoremove 2>/dev/null | sed -n 's/^Remv \([^ ]*\).*/\1/p')
if [ -z "$unneeded" ]; then
    echo -e "${TITLE}No packages to remove                                                  ${NOCOLOR}"
else
    unneeded_blocked=""
    for pkg in $unneeded; do
        if [[ "$pkg" == *"$kernel_version"* ]] || [[ "$pkg" == *linuxcnc* ]] \
           || [[ "$pkg" == *mesaflash* ]]; then
            unneeded_blocked="$unneeded_blocked $pkg"
        fi
    done
    if [ -n "$unneeded_blocked" ]; then
        echo -e "${KEYNOTE}apt would remove packages Rosetta may need:                          ${NOCOLOR}"
        echo "   $unneeded_blocked"
        echo -e "${KEYNOTE}so nothing is removed. Please tell Rosetta support.                  ${NOCOLOR}"
    else
        echo "Removing:" $unneeded
        sudo apt-get autoremove -y
        if [ $? != 0 ]; then
            echo -e "${KEYNOTE}WARNING: could not remove the packages no longer needed - the    ${NOCOLOR}"
            echo -e "${KEYNOTE}Rosetta update carries on.                                       ${NOCOLOR}"
        else
            echo -e "${TITLE}Packages no longer needed are removed                                  ${NOCOLOR}"
        fi
    fi
fi
echo -e "${TITLE}#######################################################################${NOCOLOR}"
echo -e "${TITLE}Update finished - Rosetta and its programs can be opened again.        ${NOCOLOR}"
