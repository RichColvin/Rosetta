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
#   Rosetta_Shut_Down.py
#
# Purpose:  "Shut Down" - powers the Raspberry Pi off properly, so the
#   power can be switched off without risking the SD card. Switching
#   off a running Pi can leave files half written; one machine's
#   corrupted files (November 2026) were put down to that. The
#   desktop's own Shut Down is hidden under Applications > System >
#   Log Out, so Rosetta adds this to the Rosetta submenu and the
#   bottom bar (Rosetta_Setup/Rosetta_Add_Shut_Down.sh).
#
#   First checks that Rosetta's programs are closed - LinuxCNC saves
#   the stepgen scales to RosettaSet_v1.ini as it exits, and Rosetta
#   Settings and the Rosette Designer save as they close - and that no
#   update or software install is running. Like Rosetta_Update.sh, it
#   asks the operator to close them and never closes them itself.
#   Then asks once, writes out anything waiting to go to the SD card
#   (sync) and powers off (systemctl poweroff - allowed for the
#   desktop's login without a password - else xfce4-session-logout
#   --halt).
#
#   --dry-run shows the windows but doesn't power off.
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

import os
import subprocess
import sys
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(REPO_DIR, "Rosetta_Setup", "Images", "Rosetta_Shut_Down.png")

# (pgrep arguments, what to tell the operator) - the same programs
# Rosetta_Update.sh asks to have closed, plus an update or install.
OPEN_CHECKS = (
    (["-x", "linuxcncsvr"], "Rosetta (LinuxCNC)"),
    (["-f", r"python[0-9.]* [^ ]*Rosetta_Settings\.py"], "Rosetta Settings"),
    (["-f", r"python[0-9.]* [^ ]*Rosetta_Rosette_Designer\.py"], "Rosette Designer"),
    (["-f", r"python[0-9.]* [^ ]*Rosetta_Backup\.py"], "Back Up to USB / Restore from USB"),
    (["-f", r"python[0-9.]* [^ ]*Rosetta_Checkout\.py"], "Checkout"),
    (["-f", r"Rosetta_Update\.sh"], "Rosetta Update"),
)
# Software being installed - by anyone, not just this login.
INSTALL_PROCESSES = ("apt", "apt-get", "dpkg", "unattended-upgr")

# How long to wait after the screen goes dark before switching off.
SWITCH_OFF_WAIT_SECONDS = 10


def _running(args, everyone=False):
    who = [] if everyone else ["-u", str(os.getuid())]
    try:
        return subprocess.run(["pgrep"] + who + args, capture_output=True).returncode == 0
    except OSError:
        return False


def open_programs():
    """The names of Rosetta's programs (and installs) still running."""
    found = [name for args, name in OPEN_CHECKS if _running(args)]
    if any(_running(["-x", name], everyone=True) for name in INSTALL_PROCESSES):
        found.append("A software update or install")
    return found


def _dialog(message_type, text, detail, buttons):
    """A message box; buttons = [(label, response)], the last the default."""
    dialog = Gtk.MessageDialog(message_type=message_type, text=text)
    dialog.set_title("Shut Down")
    if os.path.exists(ICON):
        dialog.set_icon_from_file(ICON)
    dialog.format_secondary_text(detail)
    for label, response in buttons:
        dialog.add_button(label, response)
    dialog.set_default_response(buttons[-1][1])
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.set_keep_above(True)
    response = dialog.run()
    dialog.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration()
    return response


def wait_for_programs_closed():
    """True once nothing is open; False if the operator cancels."""
    while True:
        still_open = open_programs()
        if not still_open:
            return True
        response = _dialog(
            Gtk.MessageType.WARNING, "Please close these first",
            "\n".join("   " + name for name in still_open) + "\n\n"
            "They save their settings as they close. Close them, then press Check Again.",
            [("Cancel", Gtk.ResponseType.CANCEL), ("Check Again", Gtk.ResponseType.OK)])
        if response != Gtk.ResponseType.OK:
            return False


def power_off(dry_run):
    subprocess.run(["sync"])
    if dry_run:
        print("Dry run: would power off now (systemctl poweroff).")
        return True
    for command in (["systemctl", "poweroff"], ["xfce4-session-logout", "--halt"]):
        try:
            if subprocess.run(command).returncode == 0:
                return True
        except OSError:
            pass
    return False


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    if not wait_for_programs_closed():
        return 1
    response = _dialog(
        Gtk.MessageType.QUESTION, "Shut down the Rosetta computer?",
        "When the screen has gone dark, wait %d seconds, then switch the power off."
        % SWITCH_OFF_WAIT_SECONDS,
        [("Cancel", Gtk.ResponseType.CANCEL), ("Shut Down", Gtk.ResponseType.OK)])
    if response != Gtk.ResponseType.OK:
        return 1
    # Something may have been opened while the question was up.
    if not wait_for_programs_closed():
        return 1
    if power_off(dry_run):
        return 0
    _dialog(Gtk.MessageType.ERROR, "The computer couldn't be shut down",
            "Use Applications > System > Log Out, then Shut Down.",
            [("OK", Gtk.ResponseType.OK)])
    return 1


if __name__ == "__main__":
    sys.exit(main())
