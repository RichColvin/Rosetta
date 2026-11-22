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
#   Rosetta_Update_Done.py
#
# Purpose:  the message box shown at the end of an update
#   (Rosetta_Update.sh), so the operator sees how it went without
#   reading the terminal: the version of Rosetta now installed and the
#   one before it, how many system packages changed, whether the
#   computer should be restarted, anything the update couldn't do, and
#   a button to the User Manual's What's New page. When the update
#   stopped part way (--failed), says so and what to do.
#
#   Arguments (all optional), given by Rosetta_Update.sh:
#     --before "1.0 Beta 1.17 - 21 November 2026"  version before the pull
#     --packages N       system packages installed, upgraded or removed
#     --restart          a kernel, firmware or core library changed
#     --files-changed    the pull brought new Rosetta files
#     --notice TEXT      something to point out (repeatable)
#     --failed TEXT      the update stopped - TEXT says where
#
# Version
#   1.0 - 22 November 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The following MIT/X Consortium License applies to the Rosetta
# system.  Use of this system constitutes consent to the terms
# outlined below.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
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

import argparse
import os
import re
import sys
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(REPO_DIR, "Rosetta_Setup", "Images", "Rosetta_Update.png")
PANEL_UI_PATH = os.path.join(REPO_DIR, "Rosetta_Display", "Rosetta_Panel_v1.ui")
# The main panel's "O/S 1.0 Beta 1.18 - 22 November 2026" label (the
# same pattern as Rosetta_Report_Version.py's; "REB O/S" before the
# renaming).
VERSION_LABEL_PATTERN = re.compile(r">(?:REB )?O/S ([^<]+?)</property>")
WHATS_NEW_PAGE = "ReleaseNotes"
WHATS_NEW = 1


def installed_version():
    """'1.0 Beta 1.18 - 22 November 2026', or None if it can't be read."""
    try:
        with open(PANEL_UI_PATH, "r") as f:
            match = VERSION_LABEL_PATTERN.search(f.read())
    except OSError:
        return None
    return match.group(1).strip() if match else None


def message(args):
    """(message type, headline, detail text) for the box."""
    now = installed_version()
    now_text = "O/S " + now if now else "the newest version"
    if args.failed:
        return (Gtk.MessageType.ERROR, "The update did not finish",
                args.failed + "\n\n"
                "Rosetta can still be used as it was. Try the update again "
                "later; if it keeps stopping, contact Rosetta support.\n\n"
                "Installed now: " + now_text + ".")
    lines = []
    if args.before and now and args.before != now:
        headline = "Rosetta has been updated"
        lines.append("Now installed:  O/S " + now)
        lines.append("Before:  O/S " + args.before)
    else:
        headline = "Rosetta is up to date"
        lines.append("Installed:  " + now_text)
        if args.files_changed:
            lines.append("Rosetta's files were updated (same version number).")
        elif args.before:
            lines.append("This was already the newest version of Rosetta.")
    if args.packages > 0:
        lines.append("%d system package%s updated."
                     % (args.packages, " was" if args.packages == 1 else "s were"))
    else:
        lines.append("No system packages needed updating.")
    lines.append("")
    if args.restart:
        lines.append("Please restart the computer before using Rosetta - "
                     "the update changed part of the operating system. "
                     "Use Shut Down, then switch the power off and on again.")
    else:
        lines.append("Rosetta and its programs can be opened again.")
    kind = Gtk.MessageType.INFO
    if args.notice:
        kind = Gtk.MessageType.WARNING
        lines.append("")
        lines.append("Please note:")
        lines.extend("  • " + text for text in args.notice)
    return kind, headline, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", default="")
    parser.add_argument("--packages", type=int, default=0)
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--files-changed", action="store_true")
    parser.add_argument("--notice", action="append", default=[])
    parser.add_argument("--failed", default="")
    args = parser.parse_args()
    kind, headline, detail = message(args)
    print(headline + "\n" + detail)
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return 0
    dialog = Gtk.MessageDialog(message_type=kind, text=headline)
    dialog.set_title("Update Rosetta")
    if os.path.exists(ICON):
        dialog.set_icon_from_file(ICON)
    dialog.format_secondary_text(detail)
    if not args.failed:
        dialog.add_button("What's New", WHATS_NEW)
    dialog.add_button("OK", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.set_keep_above(True)
    while dialog.run() == WHATS_NEW:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import rosetta_manuals
            rosetta_manuals.open_manual(WHATS_NEW_PAGE)
        except Exception as error:
            print("Could not open What's New:", error)
    dialog.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main())
