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
#                         Rosetta                                     #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Rosetta_Rosette_Designer.py
#
# Purpose:
#   The Rosette Designer (15 November 2026, Rich): a window in which
#   the operator defines a software rosette - shape, lobes, amplitude -
#   sees the cut it would make, and saves it as a G-code
#   program in the gcode folder. Running the program turns C while X
#   follows the rosette (rocking), Z does (pumping), or each follows
#   a rosette of its own (both), starting from
#   wherever the operator has put the cutter, as on a rose engine.
#   For trying a rosette before buying or making one, or for one
#   needed too rarely to be worth making. The maths and the G-code
#   are in rosetta_rosettes.py.
#
#   Standalone (started by Rosetta_Rosette_Designer.sh); only writes
#   files, so it may be open while Rosetta runs - after saving it can
#   open the program in Rosetta (axis-remote). Reads RosettaSet_v1.ini
#   for the measurement system, which axes are assigned and their
#   speed limits (warnings only). The last design is remembered in
#   ~/.config/Rosetta/rosette_designer.json. Only one copy runs at a
#   time (LOCK_PATH): starting another brings the open one forward.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 15 November 2026
#   1.1 - 15 November 2026 - rocking and pumping together (Motion:
#         Both - a rosette for X and one for Z, side by side)
#   1.2 - 15 November 2026 - Radius is the outside or the inside of
#         the cut, with where to start the cutter; only one copy runs
#         (a second start brings it forward and says so, as Settings)
#   1.3 - 15 November 2026 - notes column on the right (as Rosetta
#         Settings has); "Drawing" is now "Object Size"; opens
#         maximized, like Rosetta Settings and LinuxCNC
#   1.4 - 15 November 2026 - the notes column shares the spare width
#         with the drawings (less white space beside the cut); a
#         header like the main panel's (Rosetta, O/S version, logo)
#   1.5 - 15 November 2026 - no Phase for the first rosette: the work
#         is phased by indexing on the Rosetta panel (the pumping
#         rosette keeps its Phase, relative to the rocking one, in Both)
#   1.6 - 15 November 2026 - Object Size note: phasing holes on a
#         physical rosette made with it
#   1.7 - 15 November 2026 - Finishing pass (chosen; a percentage of C
#         speed, 10% to start) and Spring passes, in Passes mode
#   1.8 - 15 November 2026 - Running the Program note: the panel's
#         pass counter
#   1.9 - 15 November 2026 - Invert explained as the cutter on the
#         opposite side of the spindle's axis (far side cutting)
#   1.10 - 16 November 2026 - Holtzapffel shapes: lobes step by a
#         whole group for shapes made of groups, the phase is a
#         fraction of a repeat, notes on the Holtzapffel letters
#   1.11 - 16 November 2026 - Advance and Retract section (X and Z
#         distances, towards centre/headstock or away)
#   1.12 - 16 November 2026 - the form fits a 1080-line screen: number
#         boxes only as wide as a number, Depth beside Advance and
#         Retract and Object Size (Rich)
#   1.13 - 16 November 2026 - the advance directions under their
#         distances, Outside/Inside stacked (Rich)
#   1.14 - 16 November 2026 - notes: F with 1 lobe is the F-1 heart
#   1.15 - 16 November 2026 - Ellipse: a Width / length row (shown only
#         for an Ellipse), the Straight sides button becomes True
#         ellipse, and the note under the drawings gives its size and
#         foci
#   1.16 - 17 November 2026 - Ellipse set by a and b (half its length
#         and width, as in Rich's Desmos graph), always exact; On an
#         ellipse puts any shape's waves on one, spaced evenly along
#         its outline. Width / length and True ellipse are gone
#   1.17 - 17 November 2026 - an Ellipse Parameters sub heading over
#         A and B (Rich)
#   1.18 - 17 November 2026 - the rosette on an Ellipse is a column of
#         its own beside it (both rocking - Rich), with a Phase that
#         slides it along the outline; On an ellipse is gone
#   1.19 - 17 November 2026 - Phase as a percentage of a lobe (Rich;
#         over 100% moves through a group); "Advance and Retract
#         Cutter"
#   1.20 - 17 November 2026 - on an ellipse, the start radius allows
#         for the waves' depth at the start (Rich's paper chuck)
#   1.21 - 17 November 2026 - notes: the ellipse is cut relative to
#         where the cutter starts, like a physical rosette (Rich chose
#         to keep it so)
#   1.22 - 17 November 2026 - Check Circle button: saves a program
#         that draws a circle round C's axis, to set the start radius
#         (Rich)
#   1.23 - 18 November 2026 - Save for 3D Printing: the rosette itself
#         as STL and STEP files (rosetta_rosette_3d.py - Rich)
#   1.24 - 18 November 2026 - the MDF Rose Engine's mounting (drawing
#         A-08): phasing holes a quarter lobe apart, mounting slots, a
#         printed hole allowance; Machine fills in all of it
#   1.25 - 19 November 2026 - 3D Printing note: other machines' holes
#         and slots are sized in the MDF's proportion
#   1.26 - 19 November 2026 - 3D Printing note: the Lindow's have no
#         phasing holes or slots
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

import fcntl
import json
import math
import os
import re
import signal
import subprocess
import sys
import webbrowser

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, GLib

import numpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosetta_rosettes as rr
import rosetta_rosette_3d as r3d
import rosetta_settings_io

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GCODE_DIR = os.path.join(REPO_DIR, "gcode")       # Rosetta.ini's [DISPLAY]PROGRAM_PREFIX
# The header, as the main panel's: its logo, and its "O/S ..." label
# read from Rosetta_Panel_v1.ui (the label kept up to date on each
# release) rather than another copy to keep in step; the machine's S/N
# appended as the panel does (~/.config/Rosetta/serial).
LOGO_PATH = os.path.join(REPO_DIR, "Rosetta_Display", "Images", "RosettaLogo-Sm-rev.png")
PANEL_UI_PATH = os.path.join(REPO_DIR, "Rosetta_Display", "Rosetta_Panel_v1.ui")
OS_VERSION_PATTERN = re.compile(r">((?:REB )?O/S [^<]+)</property>")
SERIAL_PATH = os.path.expanduser("~/.config/Rosetta/serial")
TITLE_COLOUR = "#1a5fb4"
VERSION_COLOUR = "#c01c28"
LAST_DESIGN_PATH = os.path.expanduser("~/.config/Rosetta/rosette_designer.json")
# The check circle (_on_check_circle).
MADE_BY = "Rosette Designer"
NO_CHECK_CIRCLE = ("The check circle sets where the cutter starts for a rocking rosette (X) on the face. "
                   "With pumping alone, or cutting on the side, the start radius doesn't change the "
                   "pattern, so there's nothing to check.")
# Held (flock) by the copy that's open, with its process id - see
# _take_single_instance_lock.
LOCK_PATH = os.path.expanduser("~/.config/Rosetta/Rosette_Designer.lock")

# Settings measured in machine units: converted when the measurement
# system differs from the one a design was made in.
LENGTH_KEYS = ("amplitude", "pump_amplitude", "wrap_amplitude", "depth_per_pass", "preview_radius",
               "advance_x", "advance_z", "ellipse_a", "ellipse_b", "print_diameter", "print_thickness",
               "print_bore", "print_hole_circle", "print_hole_diameter", "print_slot_circle",
               "print_slot_width", "print_hole_allowance", "print_rim_width")
FEED_KEYS = ("plunge_feed",)

# Spin button ranges, per unit: (lower, upper, step, digits).
RANGES = {
    "inch": {"amplitude": (0.0001, 1.0, 0.001, 4), "depth_per_pass": (0.0001, 0.1, 0.001, 4),
             "plunge_feed": (0.1, 20.0, 0.1, 1), "preview_radius": (0.05, 10.0, 0.05, 3),
             "advance": (0.0, 2.0, 0.01, 3), "ellipse": (0.01, 10.0, 0.01, 4)},
    "mm": {"amplitude": (0.002, 25.0, 0.02, 3), "depth_per_pass": (0.002, 2.5, 0.02, 3),
           "plunge_feed": (2.0, 500.0, 1.0, 0), "preview_radius": (1.0, 250.0, 1.0, 1),
           "advance": (0.0, 50.0, 0.5, 2), "ellipse": (0.2, 250.0, 0.2, 3)},
}

# Save for 3D Printing (PrintDialog): where the files go, and its
# spin buttons' ranges per unit (lower, upper, step, digits).
ROSETTES_DIR = os.path.expanduser("~/Documents/Rosettes")
PRINT_RANGES = {
    "inch": {"print_diameter": (0.5, 20.0, 0.125, 3), "print_thickness": (0.04, 2.0, 0.0625, 4),
             "print_bore": (0.04, 6.0, 0.0625, 4), "print_hole_circle": (0.2, 20.0, 0.125, 3),
             "print_hole_diameter": (0.02, 1.0, 0.0005, 4), "print_slot_circle": (0.2, 20.0, 0.125, 3),
             "print_slot_width": (0.02, 1.0, 0.001, 4), "print_hole_allowance": (0.0, 0.04, 0.001, 4),
             "print_rim_width": (0.04, 3.0, 0.0625, 4)},
    "mm": {"print_diameter": (10.0, 500.0, 1.0, 1), "print_thickness": (1.0, 50.0, 0.5, 1),
           "print_bore": (1.0, 150.0, 0.5, 1), "print_hole_circle": (4.0, 500.0, 1.0, 1),
           "print_hole_diameter": (0.5, 25.0, 0.05, 2), "print_slot_circle": (4.0, 500.0, 1.0, 1),
           "print_slot_width": (0.5, 25.0, 0.1, 2), "print_hole_allowance": (0.0, 1.0, 0.05, 2),
           "print_rim_width": (1.0, 75.0, 0.5, 1)},
}

# The notes column on the right: (heading, text, User Manual anchor),
# in the order of the form's sections.
MANUAL_PAGE = "https://rosetta.colvintools.com/UserManual/index.php?n=Main.RosetteDesigner"
NOTES = (
    ("Movement",
     "Rocking moves the cutter in X, pumping moves it in Z, and Both follows a rosette with each - "
     "like two rosettes engaged at once.\n\n"
     "Cutting on sets which axis takes the cutter deeper: Z on the face, X on the side.\n\n"
     "C speed is how fast the work turns while cutting. If X or Z can't keep up at the steepest places, "
     "C slows down there; the note under the drawings says so.",
     "Movement"),
    ("Rosette",
     "Shape: the Holtzapffel letters are the patterns in Holtzapffel & Co.'s old guide to their "
     "rose cutting frame - A is a plain sine, C and D points and petals, F a Cupid's bow (F with 1 "
     "lobe, F-1, is a single heart), J and Q waves on arcs, K a waved polygon, M and N scallops on "
     "lobes, O and P groups of waves, S a scalloped heart. Plain polygon, Lotus and Tudor are not Holtzapffel letters.\n\n"
     "Lobes is counted the way the guide numbers its rosettes - the small waves round the edge, so "
     "J24 has 24 waves on 4 arcs of 6. Shapes made of groups (J, M, N, O, P, Q) only take whole "
     "groups, and Lobes steps by a group.\n\n"
     "Amplitude is how far the cutter moves, from the rosette's highest point to its lowest, measured "
     "at the object being cut.\n\n"
     "There is no phase setting: put the pattern where you want it on the work by indexing on the "
     "Rosetta panel before running the program. With Both, the pumping rosette's Phase "
     "turns it relative to the rocking rosette: as a percentage of a lobe (50% is half a lobe) - "
     "for shapes made of groups (J, M, N, O, P, Q, S) it can go past 100%, moving through the "
     "group, e.g. up to 600% for J's groups of 6 - or in degrees.\n\n"
     "Invert turns points into hollows. It is the same as running the rosette with the cutter on the "
     "opposite side of the spindle's axis of rotation - far side cutting instead of near side.\n\n"
     "Straight sides (a plain polygon rocking on the face) sets the amplitude that makes the sides "
     "straight at the Object Size radius.\n\n"
     "Ellipse (rocking only): under Ellipse Parameters, A is half its length, B half its width - an "
     "ellipse 4 long and 2 wide has A = 2, B = 1. Start the cutter at radius A from the centre and the "
     "cut is that ellipse exactly, its length along the line the cutter starts on. The note under "
     "the drawings gives its length, width and the distance between its foci.\n\n"
     "The program moves the cutter from wherever it is put, by the same amounts at any radius - as "
     "a physical ellipse rosette does - so the length always comes out 2 x (A - B) more than the "
     "width. Started further out, the cut is rounder; further in, longer and narrower, and then a "
     "peanut and a figure 8. Only started where the note says is it exactly A by B.\n\n"
     "With an Ellipse, a second rocking rosette rides on it, in the column beside it (None leaves "
     "the plain ellipse): its waves are cut in from the ellipse by its Amplitude - start the cutter "
     "where the note under the drawings says, which is A less the waves' depth where the cut starts "
     "(at Phase 0, D starts on a cusp, so the cutter goes in by the whole Amplitude). Its lobes are "
     "spaced evenly along the ellipse's outline, so on a long ellipse they don't crowd together "
     "along its sides. Its Phase slides the pattern along the outline - half a lobe moves a cleft "
     "off the end of the ellipse. With Both, the pumping rosette is a third column, its lobes "
     "spaced along the outline too, so they stay in step.\n\n"
     "Rubber: only a point for now, which follows the shape exactly.",
     "Rosette"),
    ("Depth",
     "Passes, deeper each time: put the cutter just touching the work. Each pass goes Depth per pass "
     "deeper, and at the end the cutter backs out to where it started.\n\n"
     "Finishing pass: tick it to run the last pass slower - a percentage of C speed (10% to start) - "
     "for a better finish, while the earlier passes run at full speed. Spring passes repeat the final "
     "depth to clean up the cut, at the finishing speed when Finishing pass is ticked.\n\n"
     "Turns at one depth: the cutter stays at one depth, as with a physical rosette. To go deeper, move "
     "the cutter in yourself and run the program again.",
     "Depth"),
    ("Advance and Retract Cutter",
     "To start the cutter clear of the work: set how far it moves in on X, Z or both before cutting, "
     "and which way. It moves in at the Plunge feed - the depth axis last (Z on the face, X on the "
     "side), so it enters the work along the depth direction - then cuts, then moves back out to "
     "exactly where it was put, the depth axis first. 0 = no advance.\n\n"
     "Put the cutter that far clear before running. The passes' depth is measured from where the "
     "advance ends.\n\n"
     "If the program is stopped part way, the cutter is left where it stopped - it backs out only at "
     "the normal end.",
     "Advance"),
    ("Object Size",
     "Radius is the radius on the object being made - the piece you are cutting.\n\n"
     "If you are making a rosette for later use on a rose engine, the object is that rosette: enter "
     "the radius of the rosette you want to make. Rose engines differ - some measure their rosettes "
     "across the points (Outside), others across the hollows (Inside).\n\n"
     "A physical rosette usually has phasing holes, which let it be turned relative to the work on "
     "the rose engine. The G-code program doesn't cut them - add them as you would for any rosette, "
     "or use Save for 3D Printing, which puts them in. (Patterns cut with Rosetta itself don't need "
     "them: index on the Rosetta panel instead.)\n\n"
     "Radius is used for the drawing, Straight sides and the note on where to start the cutter. The "
     "program itself cuts wherever the cutter is.",
     "ObjectSize"),
    ("Running the Program",
     "Save G-code puts the program in the gcode folder. Don't name it starting with \"Rosetta\", or "
     "M100 to M199 - those names are reserved.\n\n"
     "Open it in Rosetta and put the cutter where the pattern should be cut before starting: the "
     "program works from wherever the cutter is, the same as setting up a cut with a physical "
     "rosette.\n\n"
     "While it runs, the progress bar on the Rosetta panel shows which pass it's on - e.g. "
     "\"Program 42% - pass 2 of 3\".\n\n"
     "C isn't turned back at the end - after three turns it reads 1080 degrees.",
     "Saving"),
    ("3D Printing",
     "Save for 3D Printing saves the rosette itself - to print, or to have made - as an STL file (for "
     "a 3D printer's slicer) and a STEP file (for CAD programs and machine shops), in the Rosettes "
     "folder in Documents. Both are in millimetres, whatever units the design uses.\n\n"
     "A rocking rosette is a disc whose edge follows the pattern; a pumping rosette is a disc with a "
     "raised rim whose top rises and falls with it. Set its diameter - measured at its largest or "
     "smallest, as your rose engine's rosettes are - its thickness, the centre bore, the phasing "
     "holes and the slots for the screws that hold it to its drive gear. Machine fills in your rose "
     "engine's usual values (the MDF Rose Engine's from its rosette drawing; the Lindow's have no "
     "phasing holes or slots; for the Armbruster only the size is known, so its phasing holes and "
     "slots are put on circles in the same proportion as the MDF's - check them against your own "
     "rosettes).\n\n"
     "Phasing holes a quarter lobe apart each turn the pattern a quarter lobe on from the last - 0, "
     "1/4, 1/2, 3/4, 1 lobe... - so how far apart they are depends on the rosette's lobes: 11.25 "
     "degrees on an 8-lobe rosette, 22.5 on a 4-lobe one. On rosettes with many lobes they go 1 1/4 "
     "lobes apart instead, which phases the same. Centred at sets where round the rosette they "
     "are grouped - the MDF Rose Engine's are at the start, midway between its slots.\n\n"
     "Printed holes come out smaller than drawn: Printed hole allowance is added to the bore, the "
     "phasing holes and the slots in the STL, so they print the right size. The STEP file keeps "
     "their true sizes, for machining.\n\n"
     "Machine ratio: the rosette's wave is the Amplitude times this. On most rose engines the "
     "rosette's wave and the cut's differ, set by the machine's levers - measure yours by cutting "
     "with a rosette you know.\n\n"
     "The edge is shaped for a point rubber: a real rubber's rounded nose cuts it a little softer "
     "than designed. Seen from the top as printed, the rosette matches the drawing - for shapes that "
     "aren't the same both ways round (the F-1 heart, S), check which face goes towards you on a "
     "paper chuck first.\n\n"
     "Printers hold about 0.1 mm (0.004\"), so very fine waves may not print, and plastic wears "
     "against the rubber - a printed rosette suits trying a design before making it in metal or "
     "wood.\n\n"
     "Pumping rosettes are printed lying flat, so the patterned rim is built up in layers that leave "
     "ridges: print at the smallest layer height your printer can, and use a rubber that rides over "
     "what ridges remain, e.g. one with a roller bearing on its nose.",
     "Print"),
)
NOTES_HEADING_COLOUR = "#1a5fb4"     # as Rosetta Settings' notes

# Drawing colours: X's rosette, Z's rosette, guides, background, the work.
AXIS_INK = {"X": (0.10, 0.10, 0.35), "Z": (0.60, 0.15, 0.10)}
INK = AXIS_INK["X"]
GUIDE = (0.70, 0.70, 0.75)
BACKGROUND = (1.0, 1.0, 1.0)
WOOD = (0.93, 0.85, 0.70)

# Column headings for the rosette controls: the first rosette (by
# motion; an Ellipse has its own), the rosette on the Ellipse, and the
# pumping rosette in Both.
FIRST_HEADINGS = {"rock": "Rocking rosette (X)", "pump": "Pumping rosette (Z)",
                  "both": "Rocking rosette (X)"}
ELLIPSE_HEADING = "Ellipse (X)"
WRAP_HEADING = "Rocking rosette on the ellipse (X)"
PUMP_HEADING = "Pumping rosette (Z)"


def _linuxcnc_running():
    try:
        return subprocess.run(["pgrep", "-x", "linuxcncsvr"], capture_output=True).returncode == 0
    except OSError:
        return False


class RosetteControls:
    '''
    One rosette's controls - shape, lobes, amplitude, invert, and for
    the pumping rosette in Both its phase relative to the rocking one -
    in one column of the form's grid. prefix is "" for the first rosette
    (rocking, or pumping alone; no phase - the work is phased by
    indexing on the Rosetta panel; or the Ellipse), rr.WRAP for the
    rocking rosette on the Ellipse (phase along its outline) and
    rr.SECOND for the pumping rosette when both are used.
    '''

    def __init__(self, window, grid, column, first_row, prefix):
        self.window = window
        self.prefix = prefix
        self.widgets = []
        self.shown = True
        ranges = RANGES[window.units]
        row = first_row

        self.heading = Gtk.Label(xalign=0)
        self._place(grid, self.heading, column, row)
        row += 1

        self.shape = Gtk.ComboBoxText()
        # An Ellipse only rocks and is only the first rosette; None
        # (the plain ellipse) only for the rosette on it.
        left_out = {"": ("none",), rr.SECOND: ("none", "ellipse"), rr.WRAP: ("ellipse",)}[prefix]
        for shape_id in sorted(rr.SHAPE_IDS, key=lambda shape_id: shape_id != "none"):
            if shape_id not in left_out:
                self.shape.append(shape_id, rr.SHAPES[shape_id][0])
        self.shape.set_tooltip_text("The rosette's shape. The Holtzapffel letters are the patterns "
                                    "in Holtzapffel & Co.'s guide to their rose cutting frame.")
        self.shape.connect("changed", lambda w: window._changed())
        self._place(grid, self.shape, column, row)
        row += 1

        self.lobes = window._spin(1, 360, 1, 0)
        self.lobes.set_tooltip_text("How many lobes round the rosette, counted as the Holtzapffel "
                                    "guide numbers them (e.g. 24 for an A24). Shapes made of groups "
                                    "(J, M, N, O, P, Q) step by a whole group.")
        self._place(grid, self.lobes, column, row)
        row += 1

        self.amplitude = window._spin(*ranges["amplitude"])
        self.amplitude.set_tooltip_text("How far the cutter moves, peak to peak - at the work, "
                                        "not at the rosette.")
        self._place(grid, self.amplitude, column, row)
        row += 1

        # The Ellipse's A and B - the first rosette only, under the
        # Ellipse Parameters sub heading (row, DesignerWindow), shown only
        # when it is an Ellipse (DesignerWindow._changed). The other
        # columns leave these rows empty.
        self.ellipse_a = self.ellipse_b = None
        if not prefix:
            self.ellipse_a = window._spin(*ranges["ellipse"])
            self.ellipse_a.set_tooltip_text("Half the ellipse's length: from its centre to the end "
                                            "of its length. Start the cutter at this radius.")
            self._place(grid, self.ellipse_a, column, row + 1)
            self.ellipse_b = window._spin(*ranges["ellipse"])
            self.ellipse_b.set_tooltip_text("Half the ellipse's width: from its centre to its side.")
            self._place(grid, self.ellipse_b, column, row + 2)
        row += 3

        # Straight sides: the plain polygon amplitude that gives straight
        # sides at the Object Size radius.
        self.straight = Gtk.Button(label="Straight sides")
        self.straight.set_tooltip_text("Plain polygon: sets the amplitude that makes the sides "
                                       "straight at the Object Size radius. Rocking on the face.")
        self.straight.connect("clicked", self._on_straight_sides)
        self._place(grid, self.straight, column, row)
        row += 1

        self.has_phase = bool(prefix)
        if self.has_phase:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            self.phase = window._spin(0.0, 100.0, 5.0, 1)
            self.phase.set_width_chars(7)
            self.phase_unit = Gtk.ComboBoxText()
            self.phase_unit.append("lobe", "% of a lobe")
            self.phase_unit.append("deg", "degrees")
            self.phase_unit.connect("changed", self._on_phase_unit)
            box.pack_start(self.phase, True, True, 0)
            box.pack_start(self.phase_unit, False, False, 0)
            if prefix == rr.WRAP:
                box.set_tooltip_text("Slides the pattern along the ellipse's outline: a "
                                     "percentage of a lobe (50% = half a lobe, e.g. a cleft moved "
                                     "off the end; past 100% moves through a group for J, M, N, "
                                     "O, P, Q, S) - or degrees, 360 being the whole outline.")
            else:
                box.set_tooltip_text("Turns the pumping rosette relative to the rocking rosette: a "
                                     "percentage of a lobe (50% = half a lobe; past 100% moves "
                                     "through a group for J, M, N, O, P, Q, S) - or degrees of "
                                     "the spindle.")
            self._place(grid, box, column, row)
        row += 1

        self.invert = Gtk.CheckButton(label="Invert")
        self.invert.set_tooltip_text("Turns points into hollows - the same as running the rosette "
                                     "with the cutter on the opposite side of the spindle's axis "
                                     "(far side instead of near side).")
        self.invert.connect("toggled", lambda w: window._changed())
        self._place(grid, self.invert, column, row)
        self.last_row = row

    def _place(self, grid, widget, column, row):
        grid.attach(widget, column, row, 1, 1)
        self.widgets.append(widget)

    def set_shown(self, shown):
        self.shown = shown
        for widget in self.widgets:
            widget.set_no_show_all(not shown)
            if shown:
                widget.show_all()
            else:
                widget.hide()

    def key(self, name):
        return self.prefix + name

    def _repeats(self):
        return rr.repeats({"shape": self.shape.get_active_id() or "sine",
                           "lobes": int(self.lobes.get_value())})

    def _fit_lobes(self):
        # A shape made of groups only takes whole groups: step by one and
        # snap the count to the nearest.
        shape = self.shape.get_active_id() or "sine"
        lobes = int(self.lobes.get_value())
        per = rr.count_per_repeat(shape, lobes)
        step = 1 if shape == "holtz_s" else per
        self.lobes.set_increments(step, step * 2)
        fitted = rr.fit_lobes(shape, lobes)
        if fitted != lobes:
            loading, self.window.loading = self.window.loading, True
            self.lobes.set_value(fitted)
            self.window.loading = loading
        return fitted

    def _lobe_percent(self):
        # A whole repeat as a percentage of a lobe: 100, or more for a
        # shape made of groups (the phase is kept as a fraction of a repeat).
        shape = self.shape.get_active_id() or "sine"
        return 100.0 * rr.count_per_repeat(shape, int(self.lobes.get_value()))

    def _shown_phase(self, ros):
        return (ros["phase"] * self._lobe_percent() if ros["phase_unit"] == "lobe"
                else rr.phase_degrees(ros))

    def _set_phase_range(self):
        if self.phase_unit.get_active_id() == "deg":
            self.phase.set_range(0.0, 360.0 / self._repeats())
            self.phase.set_increments(0.5, 5.0)
            self.phase.set_digits(2)
        else:
            self.phase.set_range(0.0, self._lobe_percent())
            self.phase.set_increments(5.0, 25.0)
            self.phase.set_digits(1)

    def put(self, design):
        ros = rr.rosette(design, self.prefix)
        self.shape.set_active_id(ros["shape"])
        self.lobes.set_value(ros["lobes"])
        self.amplitude.set_value(ros["amplitude"])
        if self.ellipse_a is not None:
            self.ellipse_a.set_value(design["ellipse_a"])
            self.ellipse_b.set_value(design["ellipse_b"])
        if self.has_phase:
            self.phase_unit.set_active_id(ros["phase_unit"])
            self._set_phase_range()
            self.phase.set_value(self._shown_phase(ros))
        self.invert.set_active(ros["invert"])

    def read(self):
        lobes = self._fit_lobes()
        unit, phase = "lobe", 0.0
        if self.has_phase:
            unit = self.phase_unit.get_active_id() or "lobe"
            phase = self.phase.get_value()
            if unit == "deg":
                phase = phase * self._repeats() / 360.0
            else:
                phase = phase / self._lobe_percent()
            self._set_phase_range()     # the range follows the lobes
        values = {self.key("shape"): self.shape.get_active_id(), self.key("lobes"): lobes,
                  self.key("amplitude"): self.amplitude.get_value(), self.key("phase"): phase,
                  self.key("phase_unit"): unit, self.key("invert"): self.invert.get_active()}
        if self.ellipse_a is not None:
            values.update({"ellipse_a": self.ellipse_a.get_value(),
                           "ellipse_b": self.ellipse_b.get_value()})
        return values

    def _on_phase_unit(self, widget):
        # Keep the same phase, shown in the other unit.
        if self.window.loading:
            return
        ros = rr.rosette(self.window.design, self.prefix)
        self.window.loading = True
        self._set_phase_range()
        self.phase.set_value(self._shown_phase(dict(ros, phase_unit=widget.get_active_id())))
        self.window.loading = False
        self.window._changed()

    def _on_straight_sides(self, widget):
        d = self.window.design
        ros = rr.rosette(d, self.prefix)
        self.amplitude.set_value(rr.straight_sides_amplitude(ros, d["preview_radius"], d["radius_at"]))

    def update_sensitivity(self, axis, design):
        ros = rr.rosette(design, self.prefix)
        self.straight.set_sensitive(ros["shape"] == "polygon" and not ros["invert"]
                                    and self.prefix != rr.WRAP and axis == "X"
                                    and design["surface"] == "face")
        # The Ellipse column shows only A and B (DesignerWindow); a rosette
        # of None on it has nothing to set.
        show = self.shown and ros["shape"] != "ellipse"
        for widget in (self.lobes, self.amplitude, self.straight, self.invert):
            visible = show and not (widget is self.straight and self.prefix == rr.WRAP)
            widget.set_no_show_all(not visible)
            widget.set_visible(visible)
        waves = ros["shape"] != "none"
        for widget in (self.lobes, self.amplitude, self.invert) + ((self.phase,) if self.has_phase else ()):
            widget.set_sensitive(waves)


class DesignerWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Rosette Designer")
        self.set_default_size(1660, 920)
        self.connect("delete-event", self._on_close)

        settings = rosetta_settings_io.load_settings()
        self.settings = settings
        self.units = "mm" if settings.get("measurement_system") == "Metric" else "inch"
        self.loading = False
        self.design = self._load_last_design()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=10)
        self.add(outer)
        outer.pack_start(self._build_header(), False, False, 0)
        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.pack_start(columns, True, True, 0)

        columns.pack_start(self._build_form(), False, False, 0)
        columns.pack_start(self._build_previews(), True, True, 0)
        # The drawings and the notes share the spare width equally - the
        # cut drawing is limited by its height, so given all of it, it
        # only left white space either side (Rich, 15 November 2026).
        columns.pack_start(self._build_notes(), True, True, 0)

        self.info = Gtk.Label(xalign=0, wrap=True)
        self.info.set_use_markup(True)
        outer.pack_start(self.info, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, handler, tip in (
                ("New", self._on_new, "Start again from the standard design."),
                ("Open...", self._on_open, "Open a program saved by the Rosette Designer, to change it."),
                ("Save G-code...", self._on_save, "Save this rosette as a G-code program in the gcode folder."),
                ("Check Circle...", self._on_check_circle,
                 "Save a program that turns C once, so the cutter draws a circle round C's axis - "
                 "its diameter shows whether the cutter is at the start radius."),
                ("Save for 3D Printing...", self._on_print,
                 "Save the rosette itself as STL and STEP files, to 3D print it or have it made.")):
            button = Gtk.Button(label=label)
            button.set_tooltip_text(tip)
            button.connect("clicked", handler)
            buttons.pack_start(button, False, False, 0)
        close = Gtk.Button(label="Close")
        close.connect("clicked", lambda w: self.close())
        buttons.pack_end(close, False, False, 0)
        outer.pack_start(buttons, False, False, 0)

        self._put_design_in_form()
        self._changed()

    #################################################################
    # The design: last one, units
    #################################################################
    def _load_last_design(self):
        try:
            with open(LAST_DESIGN_PATH) as f:
                design = rr.clean_design(json.load(f))
        except (OSError, ValueError):
            design = rr.clean_design({})        # the standard design, in inches
        return self._convert(design, self.units)

    @staticmethod
    def _convert(design, units):
        '''The design in units (inch or mm), lengths and feeds converted.'''
        design = dict(design)
        if design["units"] != units:
            factor = 25.4 if units == "mm" else 1.0 / 25.4
            for key in LENGTH_KEYS + FEED_KEYS:
                design[key] = design[key] * factor
            design["units"] = units
        return rr.clean_design(design)

    def _save_last_design(self):
        try:
            os.makedirs(os.path.dirname(LAST_DESIGN_PATH), exist_ok=True)
            with open(LAST_DESIGN_PATH, "w") as f:
                json.dump(self.design, f, indent=1, sort_keys=True)
        except OSError as e:
            print("Could not save " + LAST_DESIGN_PATH + ": " + str(e))

    #################################################################
    # The form
    #################################################################
    def _section(self, grid, row, text):
        label = Gtk.Label(xalign=0)
        label.set_markup("<b>%s</b>" % text)
        label.set_margin_top(8 if row else 0)
        grid.attach(label, 0, row, 3, 1)
        return row + 1

    def _row(self, grid, row, text, widget, tip=None):
        label = Gtk.Label(label=text, xalign=0)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(widget, 1, row, 2, 1)
        if tip:
            label.set_tooltip_text(tip)
            widget.set_tooltip_text(tip)
        return row + 1

    def _spin(self, lower, upper, step, digits):
        spin = Gtk.SpinButton.new_with_range(lower, upper, step)
        spin.set_digits(digits)
        spin.set_numeric(True)
        spin.set_width_chars(8)
        # Only as wide as a number needs, not the whole column (Rich,
        # 16 November 2026: the boxes were needlessly wide).
        spin.set_halign(Gtk.Align.START)
        spin.set_hexpand(False)
        spin.connect("value-changed", lambda w: self._changed())
        return spin

    def _radios(self, choices, stacked=False):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL if stacked else Gtk.Orientation.HORIZONTAL,
                      spacing=2 if stacked else 8)
        buttons = {}
        group = None
        for value, text in choices:
            button = Gtk.RadioButton.new_with_label_from_widget(group, text)
            group = group or button
            button.connect("toggled", self._radio_toggled)
            box.pack_start(button, False, False, 0)
            buttons[value] = button
        return box, buttons

    def _radio_toggled(self, widget):
        if widget.get_active():
            self._changed()

    def _build_form(self):
        grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        unit = "in" if self.units == "inch" else "mm"
        ranges = RANGES[self.units]

        row = self._section(grid, 0, "Movement")
        motion_box, self.motion = self._radios((("rock", "Rocking (X)"), ("pump", "Pumping (Z)"),
                                                ("both", "Both")))
        row = self._row(grid, row, "Motion", motion_box,
                        "Rocking moves the cutter in X, pumping in Z; Both uses a rosette for each, "
                        "as with two rosettes engaged on a rose engine.")
        surface_box, self.surface = self._radios((("face", "Face"), ("side", "Side")))
        row = self._row(grid, row, "Cutting on", surface_box,
                        "Where the cut is: the face (end) of the work, or its side. Sets which axis "
                        "goes deeper (Z on the face, X on the side) and the drawing.")
        self.c_rpm = self._spin(0.1, 60.0, 0.1, 1)
        row = self._row(grid, row, "C speed (rev/min)", self.c_rpm,
                        "How fast C turns the work while cutting.")
        direction_box, self.c_direction = self._radios(((1, "+"), (-1, "-")))
        row = self._row(grid, row, "C direction", direction_box, "Which way C turns.")

        # The rosettes: one column each, sharing the row labels.
        row = self._section(grid, row, "Rosette")
        self.ellipse_labels = []
        # The ellipse's rows: a sub heading over A and B (Rich, 17 November 2026).
        ellipse_rows = ("Ellipse Parameters", "A (%s)" % unit, "B (%s)" % unit)
        for i, text in enumerate(("", "Shape", "Lobes", "Amplitude (%s)" % unit)
                                 + ellipse_rows + ("", "Phase", "")):
            label = Gtk.Label(label=text, xalign=0)
            if text == ellipse_rows[0]:
                label.set_markup("<i>%s</i>" % text)
                label.set_margin_top(4)
            grid.attach(label, 0, row + i, 1, 1)
            if text == "Phase":
                self.phase_label = label    # only the rosette on an Ellipse and the pumping one have one
            if text in ellipse_rows:
                self.ellipse_labels.append(label)   # only when an ellipse is in use
        # The first rosette (or the Ellipse), the rocking rosette on the
        # Ellipse (shown only with one), the pumping rosette (Both only).
        self.rosette_controls = [RosetteControls(self, grid, 1, row, ""),
                                 RosetteControls(self, grid, 2, row, rr.WRAP),
                                 RosetteControls(self, grid, 3, row, rr.SECOND)]
        row = self.rosette_controls[0].last_row + 1

        self.rubber = Gtk.ComboBoxText()
        self.rubber.append("point", "Point")
        self.rubber.connect("changed", lambda w: self._changed())
        self.rubber.set_halign(Gtk.Align.START)
        row = self._row(grid, row, "Rubber", self.rubber,
                        "The rubber that follows the rosette. Only a point for now - it follows the "
                        "shape exactly.")

        # Below the rosettes, two columns - Depth on the left, Advance and
        # Retract and Object Size on the right - so the form fits a
        # 1080-line screen without scrolling (Rich, 16 November 2026).
        top = grid
        lower = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=32)
        lower.set_margin_top(8)
        grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        lower.pack_start(grid, False, False, 0)
        row = self._section(grid, 0, "Depth")
        self.mode_passes = Gtk.RadioButton.new_with_label_from_widget(None, "Passes, deeper each time")
        self.mode_turns = Gtk.RadioButton.new_with_label_from_widget(self.mode_passes, "Turns at one depth")
        for button in (self.mode_passes, self.mode_turns):
            button.connect("toggled", self._radio_toggled)
        self.mode_passes.set_tooltip_text("The program cuts in passes, going deeper before each one, "
                                          "then backs the cutter out to where it started.")
        self.mode_turns.set_tooltip_text("The rosette repeats at the same depth; go deeper yourself "
                                         "between runs, as with a physical rosette.")
        grid.attach(self.mode_passes, 0, row, 3, 1)
        row += 1
        self.passes = self._spin(1, 100, 1, 0)
        row = self._row(grid, row, "    Passes", self.passes)
        self.depth_per_pass = self._spin(*ranges["depth_per_pass"])
        row = self._row(grid, row, "    Depth per pass (%s)" % unit, self.depth_per_pass,
                        "How much deeper each pass goes. Put the cutter just touching the work: the "
                        "first pass is one step deep.")
        self.plunge_feed = self._spin(*ranges["plunge_feed"])
        row = self._row(grid, row, "    Plunge feed (%s/min)" % unit, self.plunge_feed,
                        "How fast the cutter moves deeper between passes.")
        finish_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.finish_pass = Gtk.CheckButton()
        self.finish_pass.connect("toggled", lambda w: self._changed())
        self.finish_pct = self._spin(1, 100, 1, 0)
        self.finish_pct.set_width_chars(5)
        finish_box.pack_start(self.finish_pass, False, False, 0)
        finish_box.pack_start(self.finish_pct, False, False, 0)
        finish_box.pack_start(Gtk.Label(label="% of C speed"), False, False, 0)
        row = self._row(grid, row, "    Finishing pass", finish_box,
                        "Tick to run the last pass slower than the others, for a better finish: "
                        "C turns at this percentage of C speed.")
        self.spring_passes = self._spin(0, 5, 1, 0)
        row = self._row(grid, row, "    Spring passes", self.spring_passes,
                        "Extra turns at the final depth, to clean up the cut - at the finishing "
                        "speed when Finishing pass is ticked.")
        grid.attach(self.mode_turns, 0, row, 3, 1)
        row += 1
        self.turns = self._spin(1, 100, 1, 0)
        row = self._row(grid, row, "    Turns", self.turns)
        self.deeper_plus = Gtk.CheckButton(label="Deeper is + (normally -)")
        self.deeper_plus.set_tooltip_text("Tick if going deeper into the work means moving the depth "
                                          "axis in its + direction.")
        self.deeper_plus.connect("toggled", lambda w: self._changed())
        grid.attach(self.deeper_plus, 0, row, 3, 1)
        row += 1

        grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        lower.pack_start(grid, False, False, 0)
        row = self._section(grid, 0, "Advance and Retract Cutter")
        self.advance = {}
        self.advance_dir = {}
        for axis, choices in (("x", (("centre", "Towards centre"), ("away", "Away"))),
                              ("z", (("headstock", "Towards headstock"), ("away", "Away")))):
            # The direction under the distance (Rich, 16 November 2026).
            self.advance[axis] = self._spin(*ranges["advance"])
            radios_box, self.advance_dir[axis] = self._radios(choices)
            tip = ("How far the cutter moves in on %s before cutting, and back out at the end, "
                   "and which way. 0 = none." % axis.upper())
            row = self._row(grid, row, "%s advance (%s)" % (axis.upper(), unit), self.advance[axis], tip)
            radios_box.set_tooltip_text(tip)
            grid.attach(radios_box, 1, row, 2, 1)
            row += 1

        row = self._section(grid, row, "Object Size")
        self.preview_radius = self._spin(*ranges["preview_radius"])
        row = self._row(grid, row, "Radius (%s)" % unit, self.preview_radius,
                        "The radius of the object being made - for a rosette you'll use later, the "
                        "rosette's radius. For the drawing and Straight sides only: the program cuts "
                        "wherever the cutter is.")
        radius_box, self.radius_at = self._radios((("outside", "Outside (largest)"),
                                                   ("inside", "Inside (smallest)")), stacked=True)
        row = self._row(grid, row, "Radius is the", radius_box,
                        "Whether Radius is where the cut comes furthest out or closest in. The note "
                        "under the drawings says where to start the cutter for it.")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(560)
        # Ask for the whole form's height (scrolls only on a small screen).
        scroll.set_propagate_natural_height(True)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form.pack_start(top, False, False, 0)
        form.pack_start(lower, False, False, 0)
        scroll.add(form)
        return scroll

    def _build_header(self):
        '''The main panel's header, saying "Rosetta Rosette Designer": the O/S version (and the
        machine's S/N) under it, the logo on the right, then a line.'''
        grid = Gtk.Grid()
        title = Gtk.Label(xalign=0, hexpand=True)
        title.set_markup('<span font_desc="DejaVu Serif 20" weight="bold" foreground="%s">Rosetta Rosette Designer</span>'
                         % TITLE_COLOUR)
        grid.attach(title, 0, 0, 1, 1)
        version = Gtk.Label(xalign=0, valign=Gtk.Align.START)
        version.set_markup('<span font_desc="Serif Italic 9" foreground="%s">%s</span>'
                           % (VERSION_COLOUR, GLib.markup_escape_text(self._version_text())))
        grid.attach(version, 0, 1, 1, 1)
        if os.path.exists(LOGO_PATH):
            logo = Gtk.Image.new_from_file(LOGO_PATH)
            logo.set_valign(Gtk.Align.START)
            grid.attach(logo, 1, 0, 1, 2)
        separator = Gtk.Separator(margin_top=5, margin_bottom=5, hexpand=True)
        grid.attach(separator, 0, 2, 2, 1)
        return grid

    @staticmethod
    def _version_text():
        try:
            with open(PANEL_UI_PATH) as f:
                match = OS_VERSION_PATTERN.search(f.read())
        except OSError:
            match = None
        text = match.group(1).replace("REB ", "", 1) if match else ""
        try:
            with open(SERIAL_PATH) as f:
                serial = f.read().strip()
        except OSError:
            serial = ""
        if serial:
            text = (text + ", " if text else "") + "Machine S/N " + serial
        return text

    def _build_notes(self):
        '''The notes column, like Rosetta Settings': a heading, the text
        and a User Manual button for each section of the form.'''
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_end=6)
        for i, (heading, text, anchor) in enumerate(NOTES):
            title = Gtk.Label(xalign=0)
            title.set_markup('<span font_desc="DejaVu Serif 16" weight="bold" foreground="%s">%s</span>'
                             % (NOTES_HEADING_COLOUR, GLib.markup_escape_text(heading)))
            title.set_margin_top(12 if i else 0)
            box.pack_start(title, False, False, 0)
            body = Gtk.Label(xalign=0, wrap=True)
            body.set_max_width_chars(80)
            body.set_markup('<span font_desc="DejaVu Serif 10">%s</span>' % GLib.markup_escape_text(text))
            box.pack_start(body, False, False, 0)
            button = Gtk.Button(label="User Manual: " + heading)
            button.set_tooltip_text("Opens the User Manual's Rosette Designer page at %s." % heading)
            button.set_halign(Gtk.Align.START)
            button.connect("clicked", lambda w, a=anchor: webbrowser.open(MANUAL_PAGE + "#" + a))
            box.pack_start(button, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(380)
        scroll.set_hexpand(True)
        scroll.add(box)
        return scroll

    def _build_previews(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.profile_title = Gtk.Label(xalign=0)
        box.pack_start(self.profile_title, False, False, 0)
        self.profile_area = Gtk.DrawingArea()
        self.profile_area.set_size_request(400, 170)
        self.profile_area.connect("draw", self._draw_profile)
        box.pack_start(self.profile_area, False, True, 0)
        self.cut_title = Gtk.Label(xalign=0)
        box.pack_start(self.cut_title, False, False, 0)
        self.cut_area = Gtk.DrawingArea()
        self.cut_area.set_size_request(400, 380)
        self.cut_area.connect("draw", self._draw_cut)
        box.pack_start(self.cut_area, True, True, 0)
        return box

    #################################################################
    # Form <-> design
    #################################################################
    def _put_design_in_form(self):
        d = self.design
        self.loading = True
        for controls in self.rosette_controls:
            controls.put(d)
        self.rubber.set_active_id(d["rubber"])
        self.motion[d["motion"]].set_active(True)
        self.surface[d["surface"]].set_active(True)
        self.c_rpm.set_value(d["c_rpm"])
        self.c_direction[d["c_direction"]].set_active(True)
        (self.mode_passes if d["depth_mode"] == "passes" else self.mode_turns).set_active(True)
        self.passes.set_value(d["passes"])
        self.depth_per_pass.set_value(d["depth_per_pass"])
        self.plunge_feed.set_value(d["plunge_feed"])
        self.finish_pass.set_active(d["finish_pass"])
        self.finish_pct.set_value(d["finish_pct"])
        self.spring_passes.set_value(d["spring_passes"])
        self.turns.set_value(d["turns"])
        self.deeper_plus.set_active(d["deeper_plus"])
        self.preview_radius.set_value(d["preview_radius"])
        self.radius_at[d["radius_at"]].set_active(True)
        for axis in ("x", "z"):
            self.advance[axis].set_value(d["advance_" + axis])
            self.advance_dir[axis][d["advance_%s_dir" % axis]].set_active(True)
        self.loading = False

    @staticmethod
    def _chosen(radios):
        return next(value for value, button in radios.items() if button.get_active())

    def _read_form(self):
        values = {
            "rubber": self.rubber.get_active_id() or "point",
            "motion": self._chosen(self.motion),
            "surface": self._chosen(self.surface),
            "c_rpm": self.c_rpm.get_value(),
            "c_direction": self._chosen(self.c_direction),
            "depth_mode": "passes" if self.mode_passes.get_active() else "turns",
            "passes": int(self.passes.get_value()),
            "depth_per_pass": self.depth_per_pass.get_value(),
            "plunge_feed": self.plunge_feed.get_value(),
            "finish_pass": self.finish_pass.get_active(),
            "finish_pct": self.finish_pct.get_value(),
            "spring_passes": int(self.spring_passes.get_value()),
            "turns": int(self.turns.get_value()),
            "deeper_plus": self.deeper_plus.get_active(),
            "preview_radius": self.preview_radius.get_value(),
            "radius_at": self._chosen(self.radius_at),
            "units": self.units,
        }
        # The 3D printing settings are set in their own dialog (PrintDialog).
        values.update({key: value for key, value in self.design.items() if key.startswith("print_")})
        for axis in ("x", "z"):
            values["advance_" + axis] = self.advance[axis].get_value()
            values["advance_%s_dir" % axis] = self._chosen(self.advance_dir[axis])
        self.loading = True
        for controls in self.rosette_controls:
            values.update(controls.read())
        self.loading = False
        return rr.clean_design(values)

    def _changed(self):
        if self.loading:
            return
        self.design = self._read_form()
        d = self.design
        passes = d["depth_mode"] == "passes"
        for widget in (self.passes, self.depth_per_pass, self.plunge_feed, self.finish_pass,
                       self.spring_passes):
            widget.set_sensitive(passes)
        self.finish_pct.set_sensitive(passes and d["finish_pass"])
        self.turns.set_sensitive(not passes)
        both = d["motion"] == "both"
        ellipse = rr.ellipse_base(d) is not None
        first, wrap, pump = self.rosette_controls
        wrap.set_shown(ellipse)
        pump.set_shown(both)
        self.phase_label.set_no_show_all(not (both or ellipse))
        self.phase_label.set_visible(both or ellipse)
        first.heading.set_markup("<i>%s</i>" % (ELLIPSE_HEADING if d["shape"] == "ellipse"
                                                 else FIRST_HEADINGS[d["motion"]]))
        wrap.heading.set_markup("<i>%s</i>" % WRAP_HEADING)
        pump.heading.set_markup("<i>%s</i>" % PUMP_HEADING)
        first.update_sensitivity("Z" if d["motion"] == "pump" else "X", d)
        wrap.update_sensitivity("X", d)
        pump.update_sensitivity("Z", d)
        # The Ellipse's A and B rows only while it is one.
        for widget in [first.ellipse_a, first.ellipse_b] + self.ellipse_labels:
            widget.set_no_show_all(not ellipse)
            widget.set_visible(ellipse)
        # On an ellipse, a and b set the size on the face - Object Size
        # is not used there.
        sized = not (ellipse and d["surface"] == "face")
        for widget in [self.preview_radius] + list(self.radius_at.values()):
            widget.set_sensitive(sized)
        self._update_info()
        self.profile_area.queue_draw()
        self.cut_area.queue_draw()
        self._save_last_design()

    #################################################################
    # Information and warnings
    #################################################################
    def _assigned_roles(self):
        assignments = self.settings.get("channel_assignments") or {}
        active = rosetta_settings_io.active_channels(self.settings)
        return set(role for channel, role in assignments.items() if channel in active)

    def _axis_limit(self, letter):
        try:
            return float(self.settings["axes"][letter]["max_speed"])
        except (KeyError, TypeError, ValueError):
            return None

    def _update_info(self):
        d = self.design
        points = rr.turn_points(d)
        angles, offsets, capped = points
        moving = sorted(offsets)
        limits = {axis: self._axis_limit(axis) for axis in moving}
        c_limit = self._axis_limit("C")
        seconds, nominal = rr.turn_time(d, limits, c_limit, points)
        # Each turn at its own speed (a finishing pass is slower); C's
        # speed only changes the time of the turn, not its points.
        total = 0.0
        turn_seconds = {}
        for rpm in rr.pass_speeds(d):
            if rpm not in turn_seconds:
                turn_seconds[rpm] = rr.turn_time(dict(d, c_rpm=rpm), limits, c_limit, points)[0]
            total += turn_seconds[rpm]
        unit = "in" if self.units == "inch" else "mm"
        text = ("%d points per turn.  One turn takes about %s; the whole program about %s."
                % (len(angles) - 1, self._duration(seconds / 60.0), self._duration(total / 60.0)))
        if d["depth_mode"] == "passes" and d["finish_pass"]:
            finish_rpm = d["c_rpm"] * d["finish_pct"] / 100.0
            text += "  Finishing at %s rev/min (a turn about %s)." % (
                rr._num(round(finish_rpm, 3)), self._duration(turn_seconds[finish_rpm] / 60.0))
        if d["depth_mode"] == "passes":
            text += "  Final depth %s %s." % (self._number(d["passes"] * d["depth_per_pass"]), unit)
        base = rr.ellipse_base(d)
        if base:
            length, width, foci = rr.ellipse_axes(base)
            start = rr.start_radius(d)
            where = ("A = %s %s" % (self._number(base[0]), unit) if abs(start - base[0]) < 1e-9
                     else "%s %s (A less the waves' depth at the start)" % (self._number(start), unit))
            text += ("\nStart the cutter at radius %s from the centre, on the line the "
                     "ellipse's length is to lie along: it cuts an ellipse %s %s long and %s %s wide, "
                     "its foci %s %s apart%s."
                     % (where, self._number(length), unit,
                        self._number(width), unit, self._number(foci), unit,
                        ", with the waves cut in from it" if d["wrap_shape"] != "none" else ""))
            text += (" Started elsewhere, its length is still %s %s more than its width - "
                     "rounder further out, narrower further in." % (self._number(length - width), unit))
            if rr.advance(d, "X"):
                text += " Allow for the X advance: put it at radius %s %s." % (
                    self._number(rr.cutter_start_radius(d)), unit)
        elif d["surface"] == "face" and "X" in offsets:
            text += ("\nFor the cut's %s to be at radius %s %s, start the cutter at radius %s %s"
                     % (d["radius_at"], self._number(d["preview_radius"]), unit,
                        self._number(rr.cutter_start_radius(d)), unit))
            if rr.advance(d, "X"):
                text += " (it cuts from %s %s, after the X advance)." % (
                    self._number(rr.start_radius(d)), unit)
            else:
                text += "."
        advancing = rr.advance_order(d)
        if advancing:
            text += ("\nPut the cutter clear of the work: it moves in %s before cutting, and back "
                     "out at the end." % " then ".join(
                         "%s %s %s" % (axis, self._number(abs(rr.advance(d, axis))), unit)
                         for axis in advancing))

        warnings = []
        if d["motion"] == "pump" and d["shape"] == "ellipse":
            warnings.append("An Ellipse only rocks (X) - pumping alone, it doesn't move the cutter. "
                            "Choose Rocking or Both.")
        roles = self._assigned_roles()
        needed = sorted(set(["C", rr.depth_axis(d)] + moving))
        missing = [axis for axis in needed if axis not in roles]
        if missing:
            warnings.append("%s %s not assigned to a channel in Rosetta Settings - the program "
                            "won't run until %s." % (" and ".join(missing),
                                                     "is" if len(missing) == 1 else "are",
                                                     "it is" if len(missing) == 1 else "they are"))
        if c_limit and d["c_rpm"] * 6.0 > c_limit * 1.0001:
            warnings.append("C's Max Speed is %s rev/min (Rosetta Settings), so C will turn slower than set."
                            % self._number(c_limit / 6.0))
        c_only, _ = rr.turn_time(d, None, c_limit, points)
        if seconds > c_only * 1.02:
            slow = [axis for axis in moving
                    if rr.turn_time(d, {axis: limits[axis]}, c_limit, points)[0] > c_only * 1.02]
            warnings.append("%s can't always keep up with C at this speed (Max Speed %s), so C slows "
                            "down at the steepest places - one turn takes about %s instead of %s."
                            % (" and ".join(slow) or "An axis",
                               ", ".join("%s %s %s/sec" % (a, self._number(limits[a]), unit) for a in slow),
                               self._duration(seconds / 60.0), self._duration(nominal / 60.0)))
        if capped:
            warnings.append("This rosette needs more than %d points per turn, so the cut will be "
                            "slightly less exact." % rr.MAX_POINTS_PER_TURN)
        if warnings:
            text += "\n" + "\n".join('<span foreground="#c06000"><b>Note:</b> %s</span>'
                                     % GLib.markup_escape_text(w) for w in warnings)
        self.info.set_markup(text)

        if d["motion"] == "both":
            self.profile_title.set_markup("<b>The rosettes</b> - how far the cutter moves as the work "
                                          "turns: <span foreground='#1a1a5a'>X (rocking)</span>, "
                                          "<span foreground='#992619'>Z (pumping)</span>")
        else:
            self.profile_title.set_markup("<b>The rosette</b> - how far the cutter moves as the work turns")
        lateral, depth = self._lateral_axis(d), rr.depth_axis(d)
        across = lateral in offsets
        into = depth in offsets
        where = "on the face, seen from the end" if d["surface"] == "face" else "around the side, unrolled"
        if across and into:
            what = "the groove %s - darker is deeper" % where
        elif across:
            what = "the groove %s" % where
        else:
            what = "%s - darker is deeper" % ("the face, seen from the end" if d["surface"] == "face"
                                              else "the side, unrolled")
        self.cut_title.set_markup("<b>The cut</b> - " + what)

    def _number(self, value):
        return ("%.4f" if self.units == "inch" else "%.3f") % value

    @staticmethod
    def _duration(minutes):
        seconds = int(round(minutes * 60))
        if seconds < 60:
            return "%d sec" % seconds
        if seconds < 3600:
            return "%d min %02d sec" % (seconds // 60, seconds % 60)
        return "%d h %02d min" % (seconds // 3600, (seconds % 3600) // 60)

    #################################################################
    # Drawings
    #################################################################
    @staticmethod
    def _lateral_axis(d):
        '''The axis that moves the cutter across the surface (not into it).'''
        return "X" if d["surface"] == "face" else "Z"

    def _draw_profile(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        d = self.design
        theta = numpy.linspace(0.0, 360.0, 2000)
        curves = {axis: rr.offset(ros, theta) for axis, ros in rr.rosettes(d).items()}
        low = min(min(y.min() for y in curves.values()), 0.0)
        high = max(max(y.max() for y in curves.values()), 0.0)
        span = max(high - low, 1e-9)
        left, right, top, bottom = 40, width - 10, 14, height - 22

        def px(t, v):
            return (left + (right - left) * t / 360.0,
                    top + (bottom - top) * (high - v) / span)

        cr.set_line_width(1)
        cr.set_source_rgb(*GUIDE)
        for t in range(0, 361, 90):
            x, _ = px(t, 0)
            cr.move_to(x, top)
            cr.line_to(x, bottom)
            cr.move_to(x - 8, height - 6)
            cr.show_text("%d°" % t)
        x0, y0 = px(0, 0)
        cr.move_to(left, y0)
        cr.line_to(right, y0)
        cr.stroke()
        cr.move_to(2, y0 + 4)
        cr.show_text("start")
        for axis, y in curves.items():
            cr.set_source_rgb(*AXIS_INK[axis])
            cr.set_line_width(1.6)
            for i, (t, v) in enumerate(zip(theta, y)):
                (cr.move_to if i == 0 else cr.line_to)(*px(t, v))
            cr.stroke()

    def _draw_cut(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        d = self.design
        ros = rr.rosettes(d)
        most_lobes = max(r["lobes"] for r in ros.values())
        steps = int(min(max(2000, most_lobes * 60), 20000))
        theta = numpy.linspace(0.0, 360.0, steps)
        lateral_axis, depth_axis = self._lateral_axis(d), rr.depth_axis(d)
        lateral = rr.offset(ros[lateral_axis], theta) if lateral_axis in ros else None
        depth = self._depths(rr.offset(ros[depth_axis], theta), d) if depth_axis in ros else None
        if d["surface"] == "face":
            self._draw_face(cr, width, height, theta, lateral, depth, d)
        else:
            self._draw_side(cr, width, height, theta, lateral, depth, d)

    @staticmethod
    def _depths(y, d):
        '''0 (shallowest in the turn) to 1 (deepest) for each offset.'''
        deeper = y if d["deeper_plus"] else -y
        span = deeper.max() - deeper.min()
        return (deeper - deeper.min()) / span if span > 1e-12 else numpy.zeros_like(y)

    @staticmethod
    def _depth_shade(depth):
        return (0.85 - 0.75 * depth, 0.80 - 0.70 * depth, 0.75 - 0.45 * depth)

    def _stroke_path(self, cr, points, depth, width):
        '''A line through points; shaded by depth (0..1 each) if given.'''
        cr.set_line_width(width)
        if depth is None:
            cr.set_source_rgb(*INK)
            for i, p in enumerate(points):
                (cr.move_to if i == 0 else cr.line_to)(*p)
            cr.stroke()
            return
        cr.set_line_cap(1)      # round, so the short pieces join up
        for i in range(len(points) - 1):
            cr.set_source_rgb(*self._depth_shade(depth[i]))
            cr.move_to(*points[i])
            cr.line_to(*points[i + 1])
            cr.stroke()

    def _draw_face(self, cr, width, height, theta, lateral, depth, d):
        radius = rr.start_radius(d)         # where the cutter starts
        spread = numpy.max(numpy.abs(lateral)) if lateral is not None else 0.0
        sized = rr.ellipse_base(d) is None     # Object Size isn't used on an ellipse
        if sized:
            outer = max(radius, d["preview_radius"]) + spread * 1.1 + radius * 0.15
        else:
            # The ellipse's own furthest point (inverted waves can go out past a).
            furthest = radius + (numpy.max(lateral) if lateral is not None else 0.0)
            outer = max(radius, furthest) * 1.15
        scale = 0.46 * min(width, height) / outer
        cx, cy = width / 2.0, height / 2.0
        cr.set_source_rgb(*WOOD)
        cr.arc(cx, cy, outer * scale, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgb(*GUIDE)
        cr.set_line_width(1)
        if sized:
            cr.arc(cx, cy, d["preview_radius"] * scale, 0, 2 * math.pi)     # the Radius
            cr.stroke()
        angles = numpy.radians(theta)
        r = numpy.clip(radius + (lateral if lateral is not None else 0.0), 0.0, None)
        points = list(zip(cx + r * scale * numpy.cos(angles), cy - r * scale * numpy.sin(angles)))
        if lateral is None:
            # Pumping alone: a band of even width, shaded by depth.
            self._stroke_path(cr, points, depth, max(6.0, radius * scale * 0.08))
        else:
            self._stroke_path(cr, points, depth, 2.0 if depth is None else 4.0)
        cr.set_source_rgb(*INK)
        cr.arc(cx, cy, 2.5, 0, 2 * math.pi)
        cr.fill()

    def _draw_side(self, cr, width, height, theta, lateral, depth, d):
        left, right = 20, width - 20
        top, bottom = 30, height - 30
        cr.set_source_rgb(*WOOD)
        cr.rectangle(left, top, right - left, bottom - top)
        cr.fill()
        cr.set_source_rgb(0.4, 0.4, 0.45)
        cr.move_to(left, bottom + 16)
        cr.show_text("0°")
        cr.move_to(right - 26, bottom + 16)
        cr.show_text("360°")
        cr.move_to(left, top - 10)
        cr.show_text("around the work ->")
        mid = (top + bottom) / 2.0
        xs = left + (right - left) * theta / 360.0
        if lateral is None:
            # Rocking alone on the side: a band of even width, shaded by depth.
            band = (bottom - top) * 0.2
            for i in range(len(theta) - 1):
                cr.set_source_rgb(*self._depth_shade(depth[i]))
                cr.rectangle(xs[i], mid - band / 2, max(xs[i + 1] - xs[i], 0.6), band)
                cr.fill()
            return
        # The groove wanders along Z, drawn to scale (the band is the
        # work's circumference wide), unless that would overflow it.
        circumference = 2 * math.pi * d["preview_radius"]
        scale = (right - left) / circumference
        spread = max(numpy.ptp(lateral), 1e-9)
        scale = min(scale, (bottom - top) * 0.8 / spread)
        centre = (lateral.max() + lateral.min()) / 2.0
        points = list(zip(xs, mid - (lateral - centre) * scale))
        self._stroke_path(cr, points, depth, 2.0 if depth is None else 4.0)

    #################################################################
    # Buttons
    #################################################################
    def _commit_typing(self):
        focus = self.get_focus()
        if isinstance(focus, Gtk.SpinButton):
            focus.update()

    def _message(self, message_type, buttons, text, detail):
        dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=message_type,
                                   buttons=buttons, text=text)
        dialog.format_secondary_text(detail)
        response = dialog.run()
        dialog.destroy()
        return response

    def _on_new(self, widget):
        self.design = self._convert(rr.clean_design({}), self.units)
        self._put_design_in_form()
        self._changed()

    def _gcode_filter(self, dialog):
        file_filter = Gtk.FileFilter()
        file_filter.set_name("G-code programs (*.ngc)")
        file_filter.add_pattern("*.ngc")
        file_filter.add_pattern("*.NGC")
        dialog.add_filter(file_filter)

    def _on_open(self, widget):
        dialog = Gtk.FileChooserDialog(title="Open a Rosette Designer program", transient_for=self,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        self._gcode_filter(dialog)
        if os.path.isdir(GCODE_DIR):
            dialog.set_current_folder(GCODE_DIR)
        path = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not path:
            return
        design = rr.design_from_file(path)
        if design is None:
            self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Not a Rosette Designer program",
                          os.path.basename(path) + " wasn't saved by the Rosette Designer, so there's "
                          "no design in it to open.")
            return
        self.design = self._convert(design, self.units)
        self._put_design_in_form()
        self._changed()

    def _on_save(self, widget):
        self._commit_typing()
        self._changed()
        os.makedirs(GCODE_DIR, exist_ok=True)
        dialog = Gtk.FileChooserDialog(title="Save the rosette as a G-code program", transient_for=self,
                                       action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dialog.set_do_overwrite_confirmation(True)
        self._gcode_filter(dialog)
        dialog.set_current_folder(GCODE_DIR)
        dialog.set_current_name(rr.default_file_name(self.design))
        while True:
            if dialog.run() != Gtk.ResponseType.OK:
                dialog.destroy()
                return
            path = dialog.get_filename()
            if not path.lower().endswith(".ngc"):
                path += ".ngc"
            if rr.name_is_reserved(path):
                self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "That name is reserved",
                              "A G-code file's name must not start with \"Rosetta\" (any case) or be "
                              "M100 to M199 - LinuxCNC would run it in place of Rosetta's own. "
                              "Please choose another name.")
                continue
            break
        dialog.destroy()
        try:
            with open(path, "w") as f:
                f.write(rr.gcode(self.design))
        except OSError as e:
            self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Could not save the program", str(e))
            return
        print("Rosette Designer: saved " + path)
        if _linuxcnc_running():
            if self._message(Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, "Program saved",
                             "Open %s in Rosetta now?" % os.path.basename(path)) == Gtk.ResponseType.YES:
                try:
                    subprocess.run(["axis-remote", path], timeout=10, capture_output=True)
                except (OSError, subprocess.SubprocessError) as e:
                    print("axis-remote failed: " + str(e))
        else:
            self._message(Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Program saved",
                          "Saved as %s in the gcode folder. Open it in Rosetta, put the cutter where "
                          "the pattern should be cut, then run it." % os.path.basename(path))

    def _on_check_circle(self, widget):
        """Saves (and offers to open) a program that turns C once to draw
        a circle round C's axis, for setting the start radius - see
        rosetta_rosettes.check_circle_gcode (Rich, 17 November 2026)."""
        self._commit_typing()
        self._changed()
        radius, x_advance, deg_per_min = self._check_circle_values()
        if radius is None or radius <= 0:
            self._message(Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "No check circle for this design",
                          NO_CHECK_CIRCLE)
            return
        units = self.design["units"]
        name = rr.check_circle_file_name(radius, units)
        path = os.path.join(GCODE_DIR, name)
        try:
            os.makedirs(GCODE_DIR, exist_ok=True)
            with open(path, "w") as f:
                f.write(rr.check_circle_gcode(radius, units, deg_per_min, MADE_BY, x_advance,
                                              self.design["c_direction"]))
        except OSError as e:
            self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Could not save the check circle", str(e))
            return
        then = rr.check_circle_advance_text(x_advance, units)
        detail = ("Saved as %s in the gcode folder. Put the cutter just touching the work where the "
                  "cut will start and run it: C turns once and the cutter draws a circle round C's "
                  "axis. It should be %s across. If it's smaller, move X out by half the difference; "
                  "if bigger, move X in - then draw it again to check.%s"
                  % (name, rr.check_circle_size(radius, units), (" " + then) if then else ""))
        if _linuxcnc_running():
            if self._message(Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, "Check circle saved",
                             detail + "\n\nOpen it in Rosetta now?") == Gtk.ResponseType.YES:
                try:
                    subprocess.run(["axis-remote", path], timeout=10, capture_output=True)
                except (OSError, subprocess.SubprocessError) as e:
                    print("axis-remote failed: " + str(e))
        else:
            self._message(Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Check circle saved",
                          detail + " Open it in Rosetta with File > Open.")

    def _on_print(self, widget):
        """Save for 3D Printing: the rosette as STL and STEP files
        (rosetta_rosette_3d.py - Rich, 18 November 2026)."""
        self._commit_typing()
        self._changed()
        dialog = PrintDialog(self, self.design)
        dialog.run_dialog()
        self.design = dialog.design
        self._save_last_design()

    def _check_circle_values(self):
        """(start radius, X advance, C deg/min) - radius None unless X
        rocks on the face, where the start radius matters."""
        d = self.design
        if d["surface"] != "face" or "X" not in rr.rosettes(d):
            return None, 0.0, 0.0
        return rr.start_radius(d), rr.advance(d, "X"), d["c_rpm"] * 360.0

    def _on_close(self, widget, event):
        self._commit_typing()
        self._changed()
        Gtk.main_quit()
        return False


#######################################################################
# Only one copy at a time (15 November 2026, Rich): two copies would
# each remember their own last design, the last one closed winning,
# and a copy left behind Rosetta's full-screen window is easy to
# forget - so starting it again brings that one forward instead. The
# same scheme as Rosetta Settings: an exclusive lock on LOCK_PATH,
# released by the kernel however the copy ends, holding its process
# id for SIGUSR1.
#######################################################################
_single_instance_lock = None   # kept open (and so locked) until exit


class PrintDialog(Gtk.Dialog):
    """
    Save for 3D Printing (Rich, 18 November 2026): the rosette's size,
    machine ratio, thickness, bore and phasing holes, a drawing of it
    seen from the top as printed, the checks, and Save. The settings
    are the design's print_* keys, kept with the design.
    """

    def __init__(self, parent, design):
        Gtk.Dialog.__init__(self, title="Save for 3D Printing", transient_for=parent, modal=True)
        self.parent_window = parent
        self.design = dict(design)
        self.units = design["units"]
        self.loading = False
        self.geo = None
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        self.save_button = self.add_button("Save...", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        unit = "in" if self.units == "inch" else "mm"
        ranges = PRINT_RANGES[self.units]
        grid = Gtk.Grid(column_spacing=8, row_spacing=4, border_width=10)
        row = 0

        def add(text, widget, tip):
            nonlocal row
            label = Gtk.Label(label=text, xalign=0)
            label.set_tooltip_text(tip)
            widget.set_tooltip_text(tip)
            grid.attach(label, 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)
            row += 1
            return label

        def spin(key, lower, upper, step, digits):
            box = Gtk.SpinButton.new_with_range(lower, upper, step)
            box.set_digits(digits)
            box.set_numeric(True)
            box.set_width_chars(8)
            box.set_halign(Gtk.Align.START)
            box.connect("value-changed", lambda w: self._changed(key))
            return box

        axes = r3d.print_axes(self.design)
        self.axis = {}
        if len(axes) > 1:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            group = None
            for axis, text in (("X", "Rocking (X)"), ("Z", "Pumping (Z)")):
                button = Gtk.RadioButton.new_with_label_from_widget(group, text)
                group = group or button
                button.connect("toggled", lambda w: w.get_active() and self._changed("print_axis"))
                box.pack_start(button, False, False, 0)
                self.axis[axis] = button
            add("Rosette", box, "With Both, each rosette is saved on its own - choose which.")

        self.machine = Gtk.ComboBoxText()
        for key, (name, _) in r3d.MACHINES.items():
            self.machine.append(key, name)
        self.machine.set_halign(Gtk.Align.START)
        self.machine.connect("changed", lambda w: self._changed("print_machine"))
        add("Machine", self.machine, "Fills in this rose engine's usual rosette size and mounting. Other keeps "
                                      "whatever you enter.")
        self.spins = {}
        self.spins["print_diameter"] = spin("print_diameter", *ranges["print_diameter"])
        add("Diameter (%s)" % unit, self.spins["print_diameter"],
            "The rosette's diameter, measured where Measured at says.")
        at_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.at = {}
        group = None
        for value, text in (("largest", "Largest (across the points)"), ("smallest", "Smallest (across the hollows)")):
            button = Gtk.RadioButton.new_with_label_from_widget(group, text)
            group = group or button
            button.connect("toggled", lambda w: w.get_active() and self._changed("print_diameter_at"))
            at_box.pack_start(button, False, False, 0)
            self.at[value] = button
        self.at_label = add("Measured at", at_box, "Rose engines differ - some measure their rosettes "
                                                   "across the points, others across the hollows.")
        self.ratio = spin("print_ratio", 0.05, 20.0, 0.05, 2)
        add("Machine ratio", self.ratio, "The rosette's wave is the Amplitude times this: the rosette's "
                                         "movement against the cut's, set by the machine's levers.")
        for key, text, tip in (
                ("print_thickness", "Thickness (%s)" % unit, "How thick the disc is (a pumping rosette's "
                                                              "rim stands at least 1 mm above it)."),
                ("print_bore", "Centre bore (%s)" % unit, "The diameter of the hole in the middle."),
                ("print_rim_width", "Rim width (%s)" % unit, "How wide the pumping rosette's patterned "
                                                            "rim is, in from its edge.")):
            self.spins[key] = spin(key, *ranges[key])
            label = add(text, self.spins[key], tip)
            if key == "print_rim_width":
                self.rim_label = label
        def heading(text):
            nonlocal row
            label = Gtk.Label(xalign=0)
            label.set_markup("<i>%s</i>" % text)
            label.set_margin_top(4)
            grid.attach(label, 0, row, 2, 1)
            row += 1

        heading("Phasing holes")
        layout_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.layout = {}
        group = None
        for value, text in (("quarter", "A quarter lobe apart"), ("even", "Evenly round")):
            button = Gtk.RadioButton.new_with_label_from_widget(group, text)
            group = group or button
            button.connect("toggled", lambda w: w.get_active() and self._changed("print_hole_layout"))
            layout_box.pack_start(button, False, False, 0)
            self.layout[value] = button
        add("    Spacing", layout_box,
            "A quarter lobe apart (the MDF Rose Engine's way): each hole phases the pattern a quarter "
            "lobe on from the last - 0, 1/4, 1/2, 3/4, 1 lobe... - so the spacing depends on the "
            "rosette's lobes. When holes that close would touch, they go 1 1/4 lobes apart (or 2 1/4...), "
            "which phases the same. Evenly round: Number holes spaced equally.")
        self.holes = spin("print_holes", 0, 72, 1, 0)
        add("    Number", self.holes, "How many phasing holes (0 = none). Nine a quarter lobe apart "
                                      "phase the pattern from 0 to 2 lobes.")
        for key, text, tip in (
                ("print_hole_circle", "    On circle (%s across)" % unit,
                 "The diameter of the circle the holes' centres are on."),
                ("print_hole_diameter", "    Hole diameter (%s)" % unit,
                 "Each hole's true size (#30 drill = 0.1285\" on the MDF Rose Engine).")):
            self.spins[key] = spin(key, *ranges[key])
            add(text, self.spins[key], tip)
        self.spins["print_hole_centre"] = spin("print_hole_centre", 0.0, 359.0, 15.0, 1)
        add("    Centred at (degrees)", self.spins["print_hole_centre"],
            "Where round the rosette the holes are grouped: 0 is where the pattern starts (to the right "
            "on the drawing), 90 the top. The MDF Rose Engine's are at 0, midway between its slots. A "
            "quarter lobe apart, they're moved to the nearest whole lobe, to keep the phasing.")
        heading("Mounting slots")
        self.slots = spin("print_slots", 0, 12, 1, 0)
        add("    Number", self.slots, "Arced slots for the screws that hold the rosette to its drive "
                                      "gear, evenly round from the top (0 = none). The MDF Rose Engine "
                                      "has two, top and bottom.")
        for key, text, tip in (
                ("print_slot_circle", "    On circle (%s across)" % unit,
                 "The diameter of the circle along the slots' middles."),
                ("print_slot_span", "    Span (degrees)", "How far round each slot goes, from the "
                                                         "centre of one rounded end to the other."),
                ("print_slot_width", "    Width (%s)" % unit,
                 "How wide each slot is - 0.266\" lets a 1/4-20 screw through.")):
            if key == "print_slot_span":
                self.spins[key] = spin(key, 1.0, 330.0, 5.0, 1)
            else:
                self.spins[key] = spin(key, *ranges[key])
            add(text, self.spins[key], tip)
        self.spins["print_hole_allowance"] = spin("print_hole_allowance", *ranges["print_hole_allowance"])
        allowance_label = add("Printed hole allowance (%s)" % unit, self.spins["print_hole_allowance"],
                              "Printed holes come out smaller than drawn. This much is added to the "
                              "diameter of the bore, the phasing holes and the slots' width in the STL, "
                              "so they print the right size - adjust it to suit your printer. The STEP "
                              "file keeps their true sizes.")
        allowance_label.set_margin_top(6)
        files = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.stl = Gtk.CheckButton(label="STL (3D printing)")
        self.step = Gtk.CheckButton(label="STEP (CAD, machining)")
        for button in (self.stl, self.step):
            button.connect("toggled", lambda w: self._changed(None))
            files.pack_start(button, False, False, 0)
        files.set_margin_top(6)
        add("Save as", files, "Which files to save - both are in millimetres.")

        self.area = Gtk.DrawingArea()
        self.area.set_size_request(380, 380)
        self.area.connect("draw", self._draw)
        self.message = Gtk.Label(xalign=0, wrap=True, max_width_chars=70)
        self.message.set_use_markup(True)
        self.message.set_margin_start(10)
        self.message.set_margin_end(10)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top.pack_start(grid, False, False, 0)
        top.pack_start(self.area, True, True, 0)
        content = self.get_content_area()
        content.pack_start(top, True, True, 0)
        content.pack_start(self.message, False, False, 6)
        if self.design["print_machine"] != "other":
            # A machine's own values (editing one switches to Other), so
            # take them afresh - a design saved before they changed.
            self.design.update(r3d.machine_values(self.design, self.design["print_machine"]))
        self._put()
        self._changed(None)
        self.show_all()

    def _put(self):
        d = self.design
        self.loading = True
        if self.axis:
            self.axis[r3d.chosen_axis(d)].set_active(True)
        self.machine.set_active_id(d["print_machine"])
        for key, box in self.spins.items():
            box.set_value(d[key])
        self.at[d["print_diameter_at"]].set_active(True)
        self.ratio.set_value(d["print_ratio"])
        self.holes.set_value(d["print_holes"])
        self.slots.set_value(d["print_slots"])
        self.layout[d["print_hole_layout"]].set_active(True)
        self.stl.set_active(d["print_stl"])
        self.step.set_active(d["print_step"])
        self.loading = False

    def _changed(self, key):
        if self.loading:
            return
        d = self.design
        if key == "print_machine":
            d["print_machine"] = self.machine.get_active_id() or "other"
            d.update(r3d.machine_values(d, d["print_machine"]))
            self._put()
        if self.axis:
            d["print_axis"] = "X" if self.axis["X"].get_active() else "Z"
        for name, box in self.spins.items():
            d[name] = box.get_value()
        d["print_diameter_at"] = "largest" if self.at["largest"].get_active() else "smallest"
        d["print_hole_layout"] = "quarter" if self.layout["quarter"].get_active() else "even"
        d["print_ratio"] = self.ratio.get_value()
        d["print_holes"] = int(self.holes.get_value())
        d["print_slots"] = int(self.slots.get_value())
        if key not in (None, "print_machine", "print_axis"):
            # A value of one's own: no longer the machine's usual one.
            values = r3d.machine_values(d, d["print_machine"])
            if key in values and not self._same(values[key], d[key]):
                d["print_machine"] = "other"
                self.loading = True
                self.machine.set_active_id("other")
                self.loading = False
        d["print_stl"] = self.stl.get_active()
        d["print_step"] = self.step.get_active()
        self.design = rr.clean_design(d)
        try:
            self.geo = r3d.Rosette3D(self.design)
            # The checks are on the printed sizes (the larger holes).
            self.printed = r3d.Rosette3D(self.design, printed=True)
        except Exception as e:      # never leave the dialog unusable
            self.geo = self.printed = None
            print("Rosette Designer: 3D shape failed: %r" % (e,))
        pump = self.geo is not None and self.geo.kind == "pump"
        for widget in self.at.values():
            widget.set_sensitive(not pump)      # a pumping rosette's diameter is its outside
        if hasattr(self, "rim_label"):
            for widget in (self.rim_label, self.spins["print_rim_width"]):
                widget.set_no_show_all(not pump)    # only a pumping rosette has a rim
                widget.set_visible(pump)
        self._update_message()
        self.area.queue_draw()

    @staticmethod
    def _same(a, b):
        if isinstance(a, str) or isinstance(b, str):
            return a == b
        return abs(float(a) - float(b)) < 1e-6

    def _update_message(self):
        geo = self.printed
        lines = []
        ok = geo is not None and not geo.problems and (self.design["print_stl"] or self.design["print_step"])
        if geo is None:
            lines.append('<span foreground="#c01c28">This rosette can\'t be made into a solid.</span>')
        else:
            unit = "\"" if self.units == "inch" else " mm"
            to = lambda mm: ("%.3f" % r3d._from_mm(self.design, mm)).rstrip("0").rstrip(".") + unit
            if geo.kind == "rock":
                lines.append("Rocking rosette: %s across at its largest, %s at its smallest; the wave is "
                             "%s deep." % (to(2 * geo.largest), to(2 * geo.smallest), to(geo.wave_mm())))
            else:
                lines.append("Pumping rosette: %s across, the rim %s wide rising and falling %s." %
                             (to(2 * geo.outer_radius), to(geo.outer_radius - geo.inner_radius),
                              to(geo.wave_mm())))
            if self.design["print_stl"] and geo.allowance > 0:
                lines.append("In the STL the bore, phasing holes and slots are %s larger, to print the "
                             "right size; the STEP file has them at their true sizes." % to(geo.allowance))
            for text in geo.problems:
                lines.append('<span foreground="#c01c28">%s</span>' % GLib.markup_escape_text(text))
            for text in geo.warnings:
                lines.append('<span foreground="#b5560b">%s</span>' % GLib.markup_escape_text(text))
        if not (self.design["print_stl"] or self.design["print_step"]):
            lines.append('<span foreground="#c01c28">Tick STL, STEP or both.</span>')
        self.message.set_markup("\n".join(lines))
        self.save_button.set_sensitive(ok)

    def _draw(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        geo = self.geo
        if geo is None or (geo.kind == "rock" and geo.smallest <= 0) or (geo.kind == "pump" and geo.inner_radius <= 0):
            return
        theta = numpy.linspace(0.0, 360.0, 3601)
        rad = numpy.radians(theta)
        outer = geo.largest if geo.kind == "rock" else geo.outer_radius
        scale = 0.42 * min(width, height) / outer
        cx, cy = width / 2.0, height / 2.0
        cr.set_fill_rule(0)     # winding: the holes drawn the other way round
        if geo.kind == "rock":
            r = geo.radius(theta)
            cr.set_source_rgb(*WOOD)
            for i, (a, rr_) in enumerate(zip(rad, r)):
                (cr.move_to if i == 0 else cr.line_to)(cx + rr_ * scale * math.cos(a), cy - rr_ * scale * math.sin(a))
            cr.close_path()
            cr.fill()
        else:
            # The rim shaded by its height (darker = higher), the flat part plain.
            cr.set_source_rgb(*WOOD)
            cr.arc(cx, cy, geo.outer_radius * scale, 0, 2 * math.pi)
            cr.fill()
            # Pieces a quarter degree wide - thinner ones blur into a
            # moire pattern on screen.
            ring = numpy.linspace(0.0, 360.0, 1441)
            ring_rad = numpy.radians(ring)
            top = geo.top((ring[:-1] + ring[1:]) / 2.0)
            span = max(top.max() - top.min(), 1e-9)
            ri, ro = geo.inner_radius * scale, geo.outer_radius * scale
            for i in range(len(ring) - 1):
                shade = (top[i] - top.min()) / span
                cr.set_source_rgb(0.85 - 0.6 * shade, 0.70 - 0.5 * shade, 0.45 - 0.3 * shade)
                a, b = ring_rad[i], ring_rad[i + 1] + 0.0005     # a hair of overlap, so no seams show
                for k, (radius, angle) in enumerate(((ri, a), (ro, a), (ro, b), (ri, b))):
                    (cr.move_to if k == 0 else cr.line_to)(cx + radius * math.cos(angle),
                                                           cy - radius * math.sin(angle))
                cr.close_path()
                cr.fill()
        cr.set_source_rgb(*BACKGROUND)
        cr.arc(cx, cy, geo.bore_radius * scale, 0, 2 * math.pi)
        cr.fill()
        for hx, hy in (geo.hole_centres() if geo.holes else []):
            cr.arc(cx + hx * scale, cy - hy * scale, max(geo.hole_size * scale, 1.0), 0, 2 * math.pi)
            cr.fill()
        # The slots: a thick line along each, with round ends.
        if geo.slots and geo.slot_half_width > 0:
            cr.set_line_width(2.0 * geo.slot_half_width * scale)
            cr.set_line_cap(1)      # round
            for k in range(geo.slots):
                e0, e1 = r3d._slot_ends(geo, k)
                cr.new_path()
                cr.arc_negative(cx, cy, geo.slot_radius * scale, -math.radians(e0), -math.radians(e1))
                cr.stroke()
            cr.set_line_cap(0)
        # Where the pattern starts (0 degrees): a mark outside the edge.
        edge = (geo.radius(numpy.array([0.0]))[0] if geo.kind == "rock" else geo.outer_radius) * scale
        cr.set_source_rgb(*INK)
        cr.move_to(cx + edge + 4, cy)
        cr.line_to(cx + edge + 14, cy - 6)
        cr.line_to(cx + edge + 14, cy + 6)
        cr.close_path()
        cr.fill()
        cr.set_font_size(11)
        extents = cr.text_extents("Start")
        cr.move_to(min(cx + edge + 14 - extents.width, width - extents.width - 2), cy + 20)
        cr.show_text("Start")

    def run_dialog(self):
        while True:
            response = self.run()
            if response != Gtk.ResponseType.OK:
                break
            if self._save():
                break
        self.destroy()

    def _ask(self, message_type, buttons, text, detail):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=message_type,
                                   buttons=buttons, text=text)
        dialog.format_secondary_text(detail)
        response = dialog.run()
        dialog.destroy()
        return response

    def _save(self):
        """Asks for a name, writes the files; True when saved."""
        d, geo = self.design, self.geo
        if geo is None or geo.problems:
            return False
        os.makedirs(ROSETTES_DIR, exist_ok=True)
        chooser = Gtk.FileChooserDialog(title="Save the rosette for 3D printing", transient_for=self,
                                        action=Gtk.FileChooserAction.SAVE)
        chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        chooser.set_current_folder(ROSETTES_DIR)
        chooser.set_current_name(r3d.default_name(d, geo.axis))
        response = chooser.run()
        path = chooser.get_filename()
        chooser.destroy()
        if response != Gtk.ResponseType.OK or not path:
            return False
        base, extension = os.path.splitext(path)
        if extension.lower() not in (".stl", ".step", ".stp"):
            base = path
        folder, name = os.path.dirname(base), os.path.basename(base)
        wanted = [ext for ext, on in ((".stl", d["print_stl"]), (".step", d["print_step"])) if on]
        existing = [name + ext for ext in wanted if os.path.exists(os.path.join(folder, name + ext))]
        if existing and self._ask(Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, "Replace?",
                                  "%s already there. Replace %s?" % (
                                      " and ".join(existing) + (" are" if len(existing) > 1 else " is"),
                                      "them" if len(existing) > 1 else "it")) != Gtk.ResponseType.YES:
            return False
        window = self.get_window()
        if window:
            window.set_cursor(Gdk.Cursor.new_from_name(window.get_display(), "wait"))
        while Gtk.events_pending():
            Gtk.main_iteration()
        try:
            paths, geo = r3d.save(d, folder, name, geo.axis, d["print_stl"], d["print_step"])
        except (OSError, ValueError) as e:
            if window:
                window.set_cursor(None)
            self._ask(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Could not save the rosette", str(e))
            return False
        if window:
            window.set_cursor(None)
        print("Rosette Designer: saved " + ", ".join(paths))
        # Say what "in millimetres" means for this rosette, and what to
        # do about it (Rich, 18 November 2026: the bare note was unclear).
        across = 2.0 * (geo.largest if geo.kind == "rock" else geo.outer_radius)
        if self.units == "inch":
            size = "this rosette is %s\" (%.1f mm) across" % (
                ("%.3f" % (across / r3d.MM_PER_INCH)).rstrip("0").rstrip("."), across)
        else:
            size = "this rosette is %.1f mm across" % across
        detail = ("Saved %s in %s.\n\n%s in millimetres - %s." %
                  (" and ".join(os.path.basename(p) for p in paths), folder,
                   "Both files are" if len(paths) > 1 else "The file is", size))
        if any(p.endswith(".stl") for p in paths):
            detail += " If your slicer asks what units the STL is in, choose millimetres."
        if geo.kind == "pump":
            detail += ("\n\nPumping rosette: print it at the smallest layer height your printer can, and "
                       "use a rubber that rides over the ridges left (e.g. one with a roller bearing on "
                       "its nose).")
        self._ask(Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Rosette saved", detail)
        return True


def _take_single_instance_lock():
    '''
    True if this is the only copy running (the lock is now held), False
    if another copy holds it. If the lock file can't be made at all,
    carries on (True) rather than refusing to run.
    '''
    global _single_instance_lock
    try:
        os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
        lock = open(LOCK_PATH, "a")
    except OSError as e:
        print("Could not open " + LOCK_PATH + " (" + str(e) + ") - not checking for another copy")
        return True
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        _raise_running_copy()
        return False
    try:
        lock.truncate(0)
        lock.write(str(os.getpid()))
        lock.flush()
    except OSError:
        pass
    _single_instance_lock = lock
    # SIGUSR1 would end this copy while it's still loading - ignore it
    # until _raise_on_signal takes it over.
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)
    return True


def _raise_running_copy():
    '''Asks the copy holding the lock to bring its window to the front.'''
    try:
        with open(LOCK_PATH) as f:
            pid = int(f.read().strip())
        # Only if that process really is the Rosette Designer: the id
        # could be stale, and SIGUSR1 ends a program that doesn't handle it.
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            if b"Rosetta_Rosette_Designer.py" not in f.read():
                return
        os.kill(pid, signal.SIGUSR1)
    except (OSError, ValueError):
        pass


def _raise_on_signal(window):
    '''In the running copy: SIGUSR1 (from a second start) raises window.'''
    def raise_window():
        window.deiconify()
        window.present_with_time(Gdk.CURRENT_TIME)
        return True     # keep handling the signal
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, raise_window)


def main():
    if not _take_single_instance_lock():
        print("The Rosette Designer is already open - not starting a second copy.")
        dialog = Gtk.MessageDialog(transient_for=None, flags=0, message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK, text="The Rosette Designer is already open")
        dialog.format_secondary_text("Only one copy of the Rosette Designer can be open at a time, so "
                                     "the one already open has been brought to the front.")
        dialog.run()
        dialog.destroy()
        return
    window = DesignerWindow()
    _raise_on_signal(window)
    window.maximize()       # full screen, like Rosetta Settings and LinuxCNC
    window.show_all()       # the hidden rosette column stays hidden (set_no_show_all)
    Gtk.main()


if __name__ == "__main__":
    main()
