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
#   Rosetta_GeoChuck_Designer.py
#
# Purpose:
#   The Geometric Chuck Designer (17 November 2026, Rich): a window in
#   which the operator sets up a geometric chuck's stages - each an
#   offset, a speed (k) and a phase - sees the pattern it cuts, and
#   saves it as a G-code program in the gcode folder. Running the
#   program cuts the pattern on the face with C and X, starting from
#   wherever the operator has put the cutter
#   (https://otbok.info/index.php?n=Main.GeometricChuck). The maths
#   and the G-code are in rosetta_geochuck.py.
#
#   Built like the Rosette Designer (Rosetta_Rosette_Designer.py),
#   whose window code this copies rather than shares. Standalone
#   (started by Rosetta_GeoChuck_Designer.sh); only writes files, so it
#   may be open while Rosetta runs - after saving it can open the
#   program in Rosetta (axis-remote). Reads RosettaSet_v1.ini for the
#   measurement system, which axes are assigned and their speed limits
#   (warnings only). The last design is remembered in
#   ~/.config/Rosetta/geochuck_designer.json. Only one copy runs at a
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
#   1.0 - 17 November 2026
#   1.1 - 17 November 2026 - Check Circle button: saves a program that
#         draws a circle round C's axis, to set the start radius (Rich)
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
import rosetta_geochuck as gc
import rosetta_rosettes as rr
import rosetta_settings_io

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GCODE_DIR = os.path.join(REPO_DIR, "gcode")       # Rosetta.ini's [DISPLAY]PROGRAM_PREFIX
# The header, as the main panel's (see the Rosette Designer).
LOGO_PATH = os.path.join(REPO_DIR, "Rosetta_Display", "Images", "RosettaLogo-Sm-rev.png")
PANEL_UI_PATH = os.path.join(REPO_DIR, "Rosetta_Display", "Rosetta_Panel_v1.ui")
OS_VERSION_PATTERN = re.compile(r">((?:REB )?O/S [^<]+)</property>")
SERIAL_PATH = os.path.expanduser("~/.config/Rosetta/serial")
TITLE_COLOUR = "#1a5fb4"
VERSION_COLOUR = "#c01c28"
LAST_DESIGN_PATH = os.path.expanduser("~/.config/Rosetta/geochuck_designer.json")
# The check circle (_on_check_circle).
MADE_BY = "Geometric Chuck Designer"
NO_CHECK_CIRCLE = "Every stage's r is 0 - there is no pattern, so no start radius to check."
# Held (flock) by the copy that's open, with its process id - see
# _take_single_instance_lock.
LOCK_PATH = os.path.expanduser("~/.config/Rosetta/GeoChuck_Designer.lock")

# Settings measured in machine units: converted when the measurement
# system differs from the one a design was made in.
LENGTH_KEYS = tuple("r%d" % n for n in range(1, gc.STAGES + 1)) + ("depth_per_pass", "advance_x",
                                                                    "advance_z")
FEED_KEYS = ("cutting_speed", "plunge_feed")

# Spin button ranges, per unit: (lower, upper, step, digits).
RANGES = {
    "inch": {"r": (0.0, 10.0, 0.05, 4), "cutting_speed": (0.1, 100.0, 0.5, 1),
             "depth_per_pass": (0.0001, 0.1, 0.001, 4), "plunge_feed": (0.1, 20.0, 0.1, 1),
             "advance": (0.0, 2.0, 0.01, 3)},
    "mm": {"r": (0.0, 250.0, 1.0, 3), "cutting_speed": (2.0, 2500.0, 10.0, 0),
           "depth_per_pass": (0.002, 2.5, 0.02, 3), "plunge_feed": (2.0, 500.0, 1.0, 0),
           "advance": (0.0, 50.0, 0.5, 2)},
}

MANUAL_PAGE = "https://rosetta.colvintools.com/UserManual/index.php?n=Main.GeometricChuckDesigner"

# The notes column on the right: (heading, text, User Manual anchor),
# one per section of the form.
NOTES = (
    ("Stages",
     "A geometric chuck stacks circular motions - wheels on wheels. Each stage turns a circle of "
     "radius r, k times for each turn of the work, set at its phase to start. The pattern is "
     "where they all add up.\n\n"
     "Stage 1 is normally the cutter's own distance from the centre, with k 1. Each stage after "
     "it adds a circle: k 6 gives 5 broad lobes with small loops, k -4 a 5-point star - a pattern "
     "with two stages has |k - 1|-fold symmetry. k -1 gives an exact ellipse.\n\n"
     "k can be a fraction, such as 7/3: the pattern then takes 3 turns of the work to close.\n\n"
     "Leave r at 0 for a stage you don't use. Presets fill in some classic patterns to start "
     "from.",
     "Stages"),
    ("Movement",
     "Cutting speed is how fast the cutter moves along the pattern. C slows down where it, or X, "
     "can't keep up - most where the pattern passes close to the centre, where C has to turn "
     "fast. The note under the drawings gives the time.\n\n"
     "C direction - turns the pattern into its mirror image.",
     "Movement"),
    ("Depth",
     "Passes, deeper each time: put the cutter just touching the work. Each pass goes Depth per pass "
     "deeper, and at the end the cutter backs out to where it started.\n\n"
     "Finishing pass: tick it to run the last pass slower - a percentage of the cutting speed (10% to "
     "start) - for a better finish. Spring passes repeat the final depth to clean up the cut.\n\n"
     "Times at one depth: the pattern is cut again at the same depth. To go deeper, move the cutter "
     "in yourself and run the program again.",
     "Depth"),
    ("Advance and Retract Cutter",
     "To start the cutter clear of the work: set how far it moves in on X, Z or both before cutting, "
     "and which way. It moves in at the Plunge feed - Z last, so it enters the work straight in - "
     "then cuts, then moves back out to exactly where it was put, Z first. 0 = no advance.\n\n"
     "If the program is stopped part way, the cutter is left where it stopped - it backs out only at "
     "the normal end.",
     "Advance"),
    ("Running the Program",
     "Put the cutter at the radius the note under the drawings gives, from the centre of C. The "
     "program moves the cutter from wherever it is put, so started elsewhere the pattern changes "
     "shape. To turn the pattern on the work, index C first - the dot on the drawing is where the "
     "cut starts.\n\n"
     "A pattern that passes through the centre moves X past it, to the other side of C's axis - "
     "the note says how far. Make sure X can travel that far before running.\n\n"
     "Save G-code puts the program in the gcode folder. Don't name it starting with \"Rosetta\", or "
     "M100 to M199 - those names are reserved.\n\n"
     "While it runs, the progress bar on the Rosetta panel shows which pass it's on.",
     "Saving"),
)
NOTES_HEADING_COLOUR = "#1a5fb4"

# Drawing colours: the pattern, X and C curves, guides, background, the work.
INK = (0.10, 0.10, 0.35)
C_INK = (0.60, 0.15, 0.10)
START_INK = (0.75, 0.08, 0.06)
GUIDE = (0.70, 0.70, 0.75)
BACKGROUND = (1.0, 1.0, 1.0)
WOOD = (0.93, 0.85, 0.70)


def _linuxcnc_running():
    try:
        return subprocess.run(["pgrep", "-x", "linuxcncsvr"], capture_output=True).returncode == 0
    except OSError:
        return False


class DesignerWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Geometric Chuck Designer")
        self.set_default_size(1660, 920)
        self.connect("delete-event", self._on_close)

        settings = rosetta_settings_io.load_settings()
        self.settings = settings
        self.units = "mm" if settings.get("measurement_system") == "Metric" else "inch"
        self.loading = False
        self.design = self._load_last_design()
        self._path_cache = (None, None)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=10)
        self.add(outer)
        outer.pack_start(self._build_header(), False, False, 0)
        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.pack_start(columns, True, True, 0)
        columns.pack_start(self._build_form(), False, False, 0)
        columns.pack_start(self._build_previews(), True, True, 0)
        columns.pack_start(self._build_notes(), True, True, 0)

        self.info = Gtk.Label(xalign=0, wrap=True)
        self.info.set_use_markup(True)
        outer.pack_start(self.info, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, handler, tip in (
                ("New", self._on_new, "Start again from the standard design."),
                ("Open...", self._on_open, "Open a program saved by the Geometric Chuck Designer, to change it."),
                ("Save G-code...", self._on_save, "Save this pattern as a G-code program in the gcode folder."),
                ("Check Circle...", self._on_check_circle,
                 "Save a program that turns C once, so the cutter draws a circle round C's axis - "
                 "its diameter shows whether the cutter is at the start radius.")):
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
                design = gc.clean_design(json.load(f))
        except (OSError, ValueError):
            design = gc.clean_design({})        # the standard design, in inches
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
        return gc.clean_design(design)

    def _save_last_design(self):
        try:
            os.makedirs(os.path.dirname(LAST_DESIGN_PATH), exist_ok=True)
            with open(LAST_DESIGN_PATH, "w") as f:
                json.dump(self.design, f, indent=1, sort_keys=True)
        except OSError as e:
            print("Could not save " + LAST_DESIGN_PATH + ": " + str(e))

    def _path(self):
        '''pattern_path for the current design - worked out again only
        when something it depends on changes.'''
        d = self.design
        key = tuple(d[k] for k in sorted(d) if k[:1] in "rkp" and k[-1:].isdigit()) + (
            d["c_direction"], d["units"])
        if self._path_cache[0] != key:
            self._path_cache = (key, gc.pattern_path(d))
        return self._path_cache[1]

    #################################################################
    # The form
    #################################################################
    def _section(self, grid, row, text):
        label = Gtk.Label(xalign=0)
        label.set_markup("<b>%s</b>" % text)
        label.set_margin_top(8 if row else 0)
        grid.attach(label, 0, row, 4, 1)
        return row + 1

    def _row(self, grid, row, text, widget, tip=None):
        label = Gtk.Label(label=text, xalign=0)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(widget, 1, row, 3, 1)
        if tip:
            label.set_tooltip_text(tip)
            widget.set_tooltip_text(tip)
        return row + 1

    def _spin(self, lower, upper, step, digits):
        spin = Gtk.SpinButton.new_with_range(lower, upper, step)
        spin.set_digits(digits)
        spin.set_numeric(True)
        spin.set_width_chars(8)
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

        row = self._section(grid, 0, "Stages")
        for column, text, tip in ((0, "", None),
                                  (1, "r (%s)" % unit, "The stage's offset - the radius of its circle."),
                                  (2, "k", "How many times the stage turns for each turn of the work: "
                                           "a whole number, negative for the other way, or a "
                                           "fraction such as 7/3."),
                                  (3, "Phase (deg)", "Where the stage is set at the start.")):
            label = Gtk.Label(xalign=0)
            label.set_markup("<i>%s</i>" % text)
            if tip:
                label.set_tooltip_text(tip)
            grid.attach(label, column, row, 1, 1)
        row += 1
        self.stage_r, self.stage_k, self.stage_phase = {}, {}, {}
        for n in range(1, gc.STAGES + 1):
            grid.attach(Gtk.Label(label="Stage %d" % n, xalign=0), 0, row, 1, 1)
            self.stage_r[n] = self._spin(*ranges["r"])
            self.stage_r[n].set_tooltip_text("Stage %d's offset - the radius of its circle. "
                                             "0 = not used." % n)
            grid.attach(self.stage_r[n], 1, row, 1, 1)
            entry = Gtk.Entry()
            entry.set_width_chars(6)
            entry.set_tooltip_text("Stage %d's speed: turns for each turn of the work - e.g. 6, -4 "
                                   "or 7/3." % n)
            entry.connect("changed", lambda w: self._changed())
            self.stage_k[n] = entry
            grid.attach(entry, 2, row, 1, 1)
            self.stage_phase[n] = self._spin(0.0, 359.9, 5.0, 1)
            self.stage_phase[n].set_width_chars(6)
            self.stage_phase[n].set_tooltip_text("Where stage %d is set at the start, in degrees." % n)
            grid.attach(self.stage_phase[n], 3, row, 1, 1)
            row += 1
        self.preset = Gtk.ComboBoxText()
        self.preset.append("", "Choose a preset...")
        for i, (name, _) in enumerate(gc.PRESETS):
            self.preset.append(str(i), name)
        self.preset.set_active_id("")
        self.preset.connect("changed", self._on_preset)
        self.preset.set_halign(Gtk.Align.START)
        row = self._row(grid, row, "Presets", self.preset,
                        "Fills in the stages for a classic pattern (in inches: scaled for mm).")

        row = self._section(grid, row, "Movement")
        self.cutting_speed = self._spin(*ranges["cutting_speed"])
        row = self._row(grid, row, "Cutting speed (%s/min)" % unit, self.cutting_speed,
                        "How fast the cutter moves along the pattern. C slows down where it or X "
                        "can't keep up.")
        direction_box, self.c_direction = self._radios(((1, "+"), (-1, "-")))
        row = self._row(grid, row, "C direction", direction_box,
                        "Which way C turns - the other way cuts the pattern's mirror image.")
        top = grid

        # Below: Depth on the left, Advance and Retract Cutter on the right.
        lower = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=32)
        lower.set_margin_top(8)
        grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        lower.pack_start(grid, False, False, 0)
        row = self._section(grid, 0, "Depth")
        self.mode_passes = Gtk.RadioButton.new_with_label_from_widget(None, "Passes, deeper each time")
        self.mode_turns = Gtk.RadioButton.new_with_label_from_widget(self.mode_passes, "Times at one depth")
        for button in (self.mode_passes, self.mode_turns):
            button.connect("toggled", self._radio_toggled)
        self.mode_passes.set_tooltip_text("The pattern is cut in passes, going deeper before each one, "
                                          "then the cutter backs out to where it started.")
        self.mode_turns.set_tooltip_text("The pattern is cut again at the same depth; go deeper "
                                         "yourself between runs.")
        grid.attach(self.mode_passes, 0, row, 4, 1)
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
        finish_box.pack_start(Gtk.Label(label="% of cutting speed"), False, False, 0)
        row = self._row(grid, row, "    Finishing pass", finish_box,
                        "Tick to run the last pass slower than the others, for a better finish.")
        self.spring_passes = self._spin(0, 5, 1, 0)
        row = self._row(grid, row, "    Spring passes", self.spring_passes,
                        "Extra times round at the final depth, to clean up the cut - at the finishing "
                        "speed when Finishing pass is ticked.")
        grid.attach(self.mode_turns, 0, row, 4, 1)
        row += 1
        self.turns = self._spin(1, 100, 1, 0)
        row = self._row(grid, row, "    Times", self.turns)
        self.deeper_plus = Gtk.CheckButton(label="Deeper is + (normally -)")
        self.deeper_plus.set_tooltip_text("Tick if going deeper into the work means moving Z in its "
                                          "+ direction.")
        self.deeper_plus.connect("toggled", lambda w: self._changed())
        grid.attach(self.deeper_plus, 0, row, 4, 1)

        grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        lower.pack_start(grid, False, False, 0)
        row = self._section(grid, 0, "Advance and Retract Cutter")
        self.advance = {}
        self.advance_dir = {}
        for axis, choices in (("x", (("centre", "Towards centre"), ("away", "Away"))),
                              ("z", (("headstock", "Towards headstock"), ("away", "Away")))):
            self.advance[axis] = self._spin(*ranges["advance"])
            radios_box, self.advance_dir[axis] = self._radios(choices)
            tip = ("How far the cutter moves in on %s before cutting, and back out at the end, "
                   "and which way. 0 = none." % axis.upper())
            row = self._row(grid, row, "%s advance (%s)" % (axis.upper(), unit), self.advance[axis], tip)
            radios_box.set_tooltip_text(tip)
            grid.attach(radios_box, 1, row, 3, 1)
            row += 1

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(560)
        scroll.set_propagate_natural_height(True)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form.pack_start(top, False, False, 0)
        form.pack_start(lower, False, False, 0)
        scroll.add(form)
        return scroll

    def _build_header(self):
        '''The main panel's header, saying "Rosetta Geometric Chuck Designer".'''
        grid = Gtk.Grid()
        title = Gtk.Label(xalign=0, hexpand=True)
        title.set_markup('<span font_desc="DejaVu Serif 20" weight="bold" foreground="%s">'
                         'Rosetta Geometric Chuck Designer</span>' % TITLE_COLOUR)
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
            button.set_tooltip_text("Opens the User Manual's Geometric Chuck Designer page at %s." % heading)
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
        title = Gtk.Label(xalign=0)
        title.set_markup("<b>The pattern</b> - on the face, seen from the end; "
                         "<span foreground='#bf140f'>the dot</span> is where the cut starts")
        box.pack_start(title, False, False, 0)
        self.pattern_area = Gtk.DrawingArea()
        self.pattern_area.set_size_request(400, 380)
        self.pattern_area.connect("draw", self._draw_pattern)
        box.pack_start(self.pattern_area, True, True, 0)
        title = Gtk.Label(xalign=0)
        title.set_markup("<b>X and C</b> along the pattern: <span foreground='#1a1a5a'>X (radius)</span>, "
                         "<span foreground='#992619'>C (angle)</span>")
        box.pack_start(title, False, False, 0)
        self.axes_area = Gtk.DrawingArea()
        self.axes_area.set_size_request(400, 170)
        self.axes_area.connect("draw", self._draw_axes)
        box.pack_start(self.axes_area, False, True, 0)
        return box

    #################################################################
    # Form <-> design
    #################################################################
    def _put_design_in_form(self):
        d = self.design
        self.loading = True
        for n in range(1, gc.STAGES + 1):
            self.stage_r[n].set_value(d["r%d" % n])
            self.stage_k[n].set_text(d["k%d" % n])
            self.stage_phase[n].set_value(d["phase%d" % n])
        self.cutting_speed.set_value(d["cutting_speed"])
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
        for axis in ("x", "z"):
            self.advance[axis].set_value(d["advance_" + axis])
            self.advance_dir[axis][d["advance_%s_dir" % axis]].set_active(True)
        self.loading = False

    @staticmethod
    def _chosen(radios):
        return next(value for value, button in radios.items() if button.get_active())

    def _read_form(self):
        values = {
            "cutting_speed": self.cutting_speed.get_value(),
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
            "units": self.units,
        }
        self.bad_k = []
        for n in range(1, gc.STAGES + 1):
            text = self.stage_k[n].get_text().strip()
            k = gc.parse_k(text)
            if k is None:
                # Keep the last good value while this one is being typed.
                self.bad_k.append(n)
                text = self.design["k%d" % n]
            style = self.stage_k[n].get_style_context()
            if k is None:
                style.add_class("error")
            else:
                style.remove_class("error")
            values["r%d" % n] = self.stage_r[n].get_value()
            values["k%d" % n] = text
            values["phase%d" % n] = self.stage_phase[n].get_value()
        for axis in ("x", "z"):
            values["advance_" + axis] = self.advance[axis].get_value()
            values["advance_%s_dir" % axis] = self._chosen(self.advance_dir[axis])
        return gc.clean_design(values)

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
        self._update_info()
        self.pattern_area.queue_draw()
        self.axes_area.queue_draw()
        self._save_last_design()

    def _on_preset(self, widget):
        chosen = widget.get_active_id()
        if not chosen:
            return
        _, preset = gc.PRESETS[int(chosen)]
        scale = 1.0 if self.units == "inch" else 25.4
        design = dict(self.design)
        for n in range(1, gc.STAGES + 1):
            design["r%d" % n], design["k%d" % n], design["phase%d" % n] = 0.0, "0", 0.0
        for key, value in preset.items():
            design[key] = value * scale if key[0] == "r" else value
        self.design = gc.clean_design(design)
        self._put_design_in_form()
        self.loading = True
        widget.set_active_id("")        # back to "Choose a preset..."
        self.loading = False
        self._changed()

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
        unit = "in" if self.units == "inch" else "mm"
        warnings = []
        if len(gc.stages(d)) == 0:
            self.info.set_markup('<span foreground="#c06000"><b>Note:</b> every stage\'s r is 0 - '
                                 'there is no pattern.</span>')
            return
        path = self._path()
        info = gc.pattern_info(d, path)
        x_limit, c_limit = self._axis_limit("X"), self._axis_limit("C")
        total = 0.0
        for speed in gc.pass_speeds(d):
            total += gc.pattern_time(d, speed, x_limit, c_limit, path)[0]
        seconds, nominal = gc.pattern_time(d, None, x_limit, c_limit, path)
        sym = info["symmetry"]
        text = ("%s symmetry; closes after %d turn%s of the work.  Largest radius %s %s, smallest %s %s.  "
                "%d points.  One pattern takes about %s; the whole program about %s."
                % ("%d-fold" % sym if sym > 1 else "No rotational", info["turns"],
                   "" if info["turns"] == 1 else "s",
                   self._number(info["largest"]), unit, self._number(info["smallest"]), unit,
                   info["points"], self._duration(seconds / 60.0), self._duration(total / 60.0)))
        if d["depth_mode"] == "passes":
            text += "  Final depth %s %s." % (self._number(d["passes"] * d["depth_per_pass"]), unit)
        text += ("\nStart the cutter at radius %s %s from the centre of C - the dot on the drawing; "
                 "index C first to turn the pattern on the work." % (self._number(info["start_radius"]), unit))
        x_advance = gc.rr.advance(d, "X")
        if x_advance:
            text += " Allow for the X advance: put it at radius %s %s." % (
                self._number(info["start_radius"] - x_advance), unit)
        advancing = gc.rr.advance_order(d)
        if advancing:
            text += ("\nPut the cutter clear of the work: it moves in %s before cutting, and back "
                     "out at the end." % " then ".join(
                         "%s %s %s" % (axis, self._number(abs(gc.rr.advance(d, axis))), unit)
                         for axis in advancing))

        if self.bad_k:
            warnings.append("Stage %s's k isn't a number (e.g. 6, -4 or 7/3) - the last good value is used."
                            % " and ".join(str(n) for n in self.bad_k))
        if info["past_centre"] > 1e-9:
            warnings.append("This pattern passes through the centre: X moves %s %s past C's axis, to "
                            "the other side. Make sure X can travel that far."
                            % (self._number(info["past_centre"]), unit))
        roles = self._assigned_roles()
        missing = [axis for axis in ("C", "X", "Z") if axis not in roles]
        if missing:
            warnings.append("%s %s not assigned to a channel in Rosetta Settings - the program "
                            "won't run until %s." % (" and ".join(missing),
                                                     "is" if len(missing) == 1 else "are",
                                                     "it is" if len(missing) == 1 else "they are"))
        if seconds > nominal * 1.02:
            slow = []
            if gc.pattern_time(d, None, None, c_limit, path)[0] > nominal * 1.02:
                slow.append("C (Max Speed %s deg/sec)" % self._number(c_limit))
            if gc.pattern_time(d, None, x_limit, None, path)[0] > nominal * 1.02:
                slow.append("X (Max Speed %s %s/sec)" % (self._number(x_limit), unit))
            warnings.append("%s can't always keep up at this cutting speed, so the cut slows down "
                            "where it must - one pattern takes about %s instead of %s."
                            % (" and ".join(slow) or "An axis", self._duration(seconds / 60.0),
                               self._duration(nominal / 60.0)))
        if info["capped"]:
            warnings.append("This pattern needs more than %d points, so the cut will be slightly "
                            "less exact." % gc.MAX_POINTS)
        if warnings:
            text += "\n" + "\n".join('<span foreground="#c06000"><b>Note:</b> %s</span>'
                                     % GLib.markup_escape_text(w) for w in warnings)
        self.info.set_markup(text)

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
    def _draw_pattern(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        if not gc.stages(self.design):
            return
        d = self.design
        t = numpy.linspace(0.0, 2.0 * math.pi * gc.closing_turns(d), 20000)
        z = gc.points(d, t)
        outer = max(float(numpy.max(numpy.abs(z))), 1e-9) * 1.15
        scale = 0.46 * min(width, height) / outer
        cx, cy = width / 2.0, height / 2.0
        cr.set_source_rgb(*WOOD)
        cr.arc(cx, cy, outer * scale, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgb(*GUIDE)
        cr.set_line_width(1)
        for dx, dy in ((8, 0), (0, 8)):
            cr.move_to(cx - dx, cy - dy)
            cr.line_to(cx + dx, cy + dy)
        cr.stroke()
        cr.set_source_rgb(*INK)
        cr.set_line_width(1.4)
        for i, p in enumerate(z):
            (cr.move_to if i == 0 else cr.line_to)(cx + p.real * scale, cy - p.imag * scale)
        cr.stroke()
        cr.set_source_rgb(*START_INK)
        cr.arc(cx + z[0].real * scale, cy - z[0].imag * scale, 4.0, 0, 2 * math.pi)
        cr.fill()

    def _draw_axes(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        if not gc.stages(self.design):
            return
        angles, radii, z, _ = self._path()
        along = numpy.concatenate(([0.0], numpy.cumsum(numpy.abs(numpy.diff(z)))))
        along = along / max(along[-1], 1e-12)
        left, right = 40, width - 10
        half = (height - 16) / 2.0
        for values, ink, top, label in ((radii, INK, 4, "X"), (angles, C_INK, 8 + half, "C")):
            low, high = float(numpy.min(values)), float(numpy.max(values))
            span = max(high - low, 1e-9)
            cr.set_source_rgb(*GUIDE)
            cr.set_line_width(1)
            cr.rectangle(left, top, right - left, half - 4)
            cr.stroke()
            if label == "X" and low < 0 < high:
                y0 = top + (half - 4) * (high - 0.0) / span
                cr.move_to(left, y0)
                cr.line_to(right, y0)
                cr.stroke()
                cr.move_to(left + 3, y0 - 2)
                cr.show_text("centre")
            cr.set_source_rgb(*ink)
            cr.move_to(4, top + half / 2.0)
            cr.show_text(label)
            cr.set_line_width(1.4)
            for i, (a, v) in enumerate(zip(along, values)):
                x = left + (right - left) * a
                y = top + (half - 4) * (high - v) / span
                (cr.move_to if i == 0 else cr.line_to)(x, y)
            cr.stroke()

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
        self.design = self._convert(gc.clean_design({}), self.units)
        self._put_design_in_form()
        self._changed()

    def _gcode_filter(self, dialog):
        file_filter = Gtk.FileFilter()
        file_filter.set_name("G-code programs (*.ngc)")
        file_filter.add_pattern("*.ngc")
        file_filter.add_pattern("*.NGC")
        dialog.add_filter(file_filter)

    def _on_open(self, widget):
        dialog = Gtk.FileChooserDialog(title="Open a Geometric Chuck Designer program", transient_for=self,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        self._gcode_filter(dialog)
        if os.path.isdir(GCODE_DIR):
            dialog.set_current_folder(GCODE_DIR)
        path = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not path:
            return
        design = gc.design_from_file(path)
        if design is None:
            self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                          "Not a Geometric Chuck Designer program",
                          os.path.basename(path) + " wasn't saved by the Geometric Chuck Designer, so "
                          "there's no design in it to open.")
            return
        self.design = self._convert(design, self.units)
        self._put_design_in_form()
        self._changed()

    def _on_save(self, widget):
        self._commit_typing()
        self._changed()
        if not gc.stages(self.design):
            self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "There is no pattern",
                          "Every stage's r is 0. Set at least one stage first.")
            return
        os.makedirs(GCODE_DIR, exist_ok=True)
        dialog = Gtk.FileChooserDialog(title="Save the pattern as a G-code program", transient_for=self,
                                       action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dialog.set_do_overwrite_confirmation(True)
        self._gcode_filter(dialog)
        dialog.set_current_folder(GCODE_DIR)
        dialog.set_current_name(gc.default_file_name(self.design))
        while True:
            if dialog.run() != Gtk.ResponseType.OK:
                dialog.destroy()
                return
            path = dialog.get_filename()
            if not path.lower().endswith(".ngc"):
                path += ".ngc"
            if gc.name_is_reserved(path):
                self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "That name is reserved",
                              "A G-code file's name must not start with \"Rosetta\" (any case) or be "
                              "M100 to M199 - LinuxCNC would run it in place of Rosetta's own. "
                              "Please choose another name.")
                continue
            break
        dialog.destroy()
        try:
            with open(path, "w") as f:
                f.write(gc.gcode(self.design))
        except OSError as e:
            self._message(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Could not save the program", str(e))
            return
        print("Geometric Chuck Designer: saved " + path)
        if _linuxcnc_running():
            if self._message(Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, "Program saved",
                             "Open %s in Rosetta now?" % os.path.basename(path)) == Gtk.ResponseType.YES:
                try:
                    subprocess.run(["axis-remote", path], timeout=10, capture_output=True)
                except (OSError, subprocess.SubprocessError) as e:
                    print("axis-remote failed: " + str(e))
        else:
            self._message(Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Program saved",
                          "Saved as %s in the gcode folder. Open it in Rosetta, put the cutter at the "
                          "radius the note gives, then run it." % os.path.basename(path))

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

    def _check_circle_values(self):
        """(start radius, X advance, C deg/min at the cutting speed)."""
        d = self.design
        if not gc.stages(d):
            return None, 0.0, 0.0
        radius = gc.pattern_info(d, self._path())["start_radius"]
        deg_per_min = d["cutting_speed"] / (2.0 * math.pi * max(radius, 1e-6)) * 360.0
        return radius, gc.rr.advance(d, "X"), deg_per_min

    def _on_close(self, widget, event):
        self._commit_typing()
        self._changed()
        Gtk.main_quit()
        return False


#######################################################################
# Only one copy at a time - as the Rosette Designer (see there): an
# exclusive lock on LOCK_PATH holding the open copy's process id, which
# a second start sends SIGUSR1 to bring its window forward.
#######################################################################
_single_instance_lock = None   # kept open (and so locked) until exit


def _take_single_instance_lock():
    '''True if this is the only copy running (the lock is now held),
    False if another copy holds it; True if the lock can't be made.'''
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
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)
    return True


def _raise_running_copy():
    '''Asks the copy holding the lock to bring its window to the front.'''
    try:
        with open(LOCK_PATH) as f:
            pid = int(f.read().strip())
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            if b"Rosetta_GeoChuck_Designer.py" not in f.read():
                return
        os.kill(pid, signal.SIGUSR1)
    except (OSError, ValueError):
        pass


def _raise_on_signal(window):
    '''In the running copy: SIGUSR1 (from a second start) raises window.'''
    def raise_window():
        window.deiconify()
        window.present_with_time(Gdk.CURRENT_TIME)
        return True
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, raise_window)


def main():
    if not _take_single_instance_lock():
        print("The Geometric Chuck Designer is already open - not starting a second copy.")
        dialog = Gtk.MessageDialog(transient_for=None, flags=0, message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text="The Geometric Chuck Designer is already open")
        dialog.format_secondary_text("Only one copy can be open at a time, so the one already open "
                                     "has been brought to the front.")
        dialog.run()
        dialog.destroy()
        return
    window = DesignerWindow()
    _raise_on_signal(window)
    window.maximize()
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
