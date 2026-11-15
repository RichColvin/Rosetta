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
#   the operator defines a software rosette - shape, lobes, amplitude,
#   phase - sees the cut it would make, and saves it as a G-code
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
# Held (flock) by the copy that's open, with its process id - see
# _take_single_instance_lock.
LOCK_PATH = os.path.expanduser("~/.config/Rosetta/Rosette_Designer.lock")

# Settings measured in machine units: converted when the measurement
# system differs from the one a design was made in.
LENGTH_KEYS = ("amplitude", "pump_amplitude", "depth_per_pass", "preview_radius")
FEED_KEYS = ("plunge_feed",)

# Spin button ranges, per unit: (lower, upper, step, digits).
RANGES = {
    "inch": {"amplitude": (0.0001, 1.0, 0.001, 4), "depth_per_pass": (0.0001, 0.1, 0.001, 4),
             "plunge_feed": (0.1, 20.0, 0.1, 1), "preview_radius": (0.05, 10.0, 0.05, 3)},
    "mm": {"amplitude": (0.002, 25.0, 0.02, 3), "depth_per_pass": (0.002, 2.5, 0.02, 3),
           "plunge_feed": (2.0, 500.0, 1.0, 0), "preview_radius": (1.0, 250.0, 1.0, 1)},
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
     "Lobes is how many times the shape repeats in one turn of the work.\n\n"
     "Amplitude is how far the cutter moves, from the rosette's highest point to its lowest, measured "
     "at the object being cut.\n\n"
     "Phase turns the pattern around the work: as a fraction of a lobe (0.5 is half a lobe) or in "
     "degrees. Invert turns points into hollows.\n\n"
     "Straight sides (a plain polygon rocking on the face) sets the amplitude that makes the sides "
     "straight at the Object Size radius.\n\n"
     "Rubber: only a point for now, which follows the shape exactly.",
     "Rosette"),
    ("Depth",
     "Passes, deeper each time: put the cutter just touching the work. Each pass goes Depth per pass "
     "deeper, and at the end the cutter backs out to where it started.\n\n"
     "Turns at one depth: the cutter stays at one depth, as with a physical rosette. To go deeper, move "
     "the cutter in yourself and run the program again.",
     "Depth"),
    ("Object Size",
     "Radius is the radius on the object being made - the piece you are cutting.\n\n"
     "If you are making a rosette for later use on a rose engine, the object is that rosette: enter "
     "the radius of the rosette you want to make. Rose engines differ - some measure their rosettes "
     "across the points (Outside), others across the hollows (Inside).\n\n"
     "Radius is used for the drawing, Straight sides and the note on where to start the cutter. The "
     "program itself cuts wherever the cutter is.",
     "ObjectSize"),
    ("Running the Program",
     "Save G-code puts the program in the gcode folder. Don't name it starting with \"Rosetta\", or "
     "M100 to M199 - those names are reserved.\n\n"
     "Open it in Rosetta and put the cutter where the pattern should be cut before starting: the "
     "program works from wherever the cutter is, the same as setting up a cut with a physical "
     "rosette.\n\n"
     "C isn't turned back at the end - after three turns it reads 1080 degrees.",
     "Saving"),
)
NOTES_HEADING_COLOUR = "#1a5fb4"     # as Rosetta Settings' notes

# Drawing colours: X's rosette, Z's rosette, guides, background, the work.
AXIS_INK = {"X": (0.10, 0.10, 0.35), "Z": (0.60, 0.15, 0.10)}
INK = AXIS_INK["X"]
GUIDE = (0.70, 0.70, 0.75)
BACKGROUND = (1.0, 1.0, 1.0)
WOOD = (0.93, 0.85, 0.70)

# Column headings for the rosette controls: (motion, column) -> heading.
ROSETTE_HEADINGS = {("rock", 0): "Rocking rosette (X)", ("pump", 0): "Pumping rosette (Z)",
                    ("both", 0): "Rocking rosette (X)", ("both", 1): "Pumping rosette (Z)"}


def _linuxcnc_running():
    try:
        return subprocess.run(["pgrep", "-x", "linuxcncsvr"], capture_output=True).returncode == 0
    except OSError:
        return False


class RosetteControls:
    '''
    One rosette's controls - shape, lobes, amplitude, phase, invert -
    in one column of the form's grid. prefix is "" for the first rosette
    (rocking, or pumping alone) and rr.SECOND for the pumping rosette
    when both are used.
    '''

    def __init__(self, window, grid, column, first_row, prefix):
        self.window = window
        self.prefix = prefix
        self.widgets = []
        ranges = RANGES[window.units]
        row = first_row

        self.heading = Gtk.Label(xalign=0)
        self._place(grid, self.heading, column, row)
        row += 1

        self.shape = Gtk.ComboBoxText()
        for shape_id in rr.SHAPE_IDS:
            self.shape.append(shape_id, rr.SHAPES[shape_id][0])
        self.shape.set_tooltip_text("The shape of each lobe.")
        self.shape.connect("changed", lambda w: window._changed())
        self._place(grid, self.shape, column, row)
        row += 1

        self.lobes = window._spin(1, 360, 1, 0)
        self.lobes.set_tooltip_text("How many times the shape repeats around the rosette "
                                    "(e.g. 24 for a Sine 24).")
        self._place(grid, self.lobes, column, row)
        row += 1

        self.amplitude = window._spin(*ranges["amplitude"])
        self.amplitude.set_tooltip_text("How far the cutter moves, peak to peak - at the work, "
                                        "not at the rosette.")
        self._place(grid, self.amplitude, column, row)
        row += 1

        self.straight = Gtk.Button(label="Straight sides")
        self.straight.set_tooltip_text("Sets the amplitude that makes a plain polygon's sides "
                                       "straight at the Object Size radius (rocking on the face).")
        self.straight.connect("clicked", self._on_straight_sides)
        self._place(grid, self.straight, column, row)
        row += 1

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.phase = window._spin(0.0, 1.0, 0.05, 3)
        self.phase.set_width_chars(7)
        self.phase_unit = Gtk.ComboBoxText()
        self.phase_unit.append("lobe", "of a lobe")
        self.phase_unit.append("deg", "degrees")
        self.phase_unit.connect("changed", self._on_phase_unit)
        box.pack_start(self.phase, True, True, 0)
        box.pack_start(self.phase_unit, False, False, 0)
        box.set_tooltip_text("Turns the rosette relative to the work: a fraction of one lobe "
                             "(0.5 = half a lobe), or degrees of the spindle.")
        self._place(grid, box, column, row)
        row += 1

        self.invert = Gtk.CheckButton(label="Invert")
        self.invert.set_tooltip_text("Turns the shape inside out (points become hollows).")
        self.invert.connect("toggled", lambda w: window._changed())
        self._place(grid, self.invert, column, row)
        self.last_row = row

    def _place(self, grid, widget, column, row):
        grid.attach(widget, column, row, 1, 1)
        self.widgets.append(widget)

    def set_shown(self, shown):
        for widget in self.widgets:
            widget.set_no_show_all(not shown)
            if shown:
                widget.show_all()
            else:
                widget.hide()

    def key(self, name):
        return self.prefix + name

    def _set_phase_range(self):
        if self.phase_unit.get_active_id() == "deg":
            lobe_deg = 360.0 / max(int(self.lobes.get_value()), 1)
            self.phase.set_range(0.0, lobe_deg)
            self.phase.set_increments(0.5, 5.0)
            self.phase.set_digits(2)
        else:
            self.phase.set_range(0.0, 1.0)
            self.phase.set_increments(0.05, 0.25)
            self.phase.set_digits(3)

    def put(self, design):
        ros = rr.rosette(design, self.prefix)
        self.shape.set_active_id(ros["shape"])
        self.lobes.set_value(ros["lobes"])
        self.amplitude.set_value(ros["amplitude"])
        self.phase_unit.set_active_id(ros["phase_unit"])
        self._set_phase_range()
        self.phase.set_value(ros["phase"] if ros["phase_unit"] == "lobe" else rr.phase_degrees(ros))
        self.invert.set_active(ros["invert"])

    def read(self):
        lobes = int(self.lobes.get_value())
        unit = self.phase_unit.get_active_id() or "lobe"
        phase = self.phase.get_value()
        if unit == "deg":
            phase = phase * lobes / 360.0
            self._set_phase_range()     # the degrees range follows the lobes
        return {self.key("shape"): self.shape.get_active_id(), self.key("lobes"): lobes,
                self.key("amplitude"): self.amplitude.get_value(), self.key("phase"): phase,
                self.key("phase_unit"): unit, self.key("invert"): self.invert.get_active()}

    def _on_phase_unit(self, widget):
        # Keep the same phase, shown in the other unit.
        if self.window.loading:
            return
        ros = rr.rosette(self.window.design, self.prefix)
        self.window.loading = True
        self._set_phase_range()
        self.phase.set_value(ros["phase"] if widget.get_active_id() == "lobe" else rr.phase_degrees(ros))
        self.window.loading = False
        self.window._changed()

    def _on_straight_sides(self, widget):
        d = self.window.design
        self.amplitude.set_value(rr.straight_sides_amplitude(rr.rosette(d, self.prefix),
                                                             d["preview_radius"], d["radius_at"]))

    def update_sensitivity(self, axis, design):
        ros = rr.rosette(design, self.prefix)
        self.straight.set_sensitive(ros["shape"] == "polygon" and not ros["invert"]
                                    and axis == "X" and design["surface"] == "face")


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
                ("Save G-code...", self._on_save, "Save this rosette as a G-code program in the gcode folder.")):
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
        spin.set_width_chars(9)
        spin.connect("value-changed", lambda w: self._changed())
        return spin

    def _radios(self, choices):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
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
        for i, text in enumerate(("", "Shape", "Lobes", "Amplitude (%s)" % unit, "", "Phase", "")):
            grid.attach(Gtk.Label(label=text, xalign=0), 0, row + i, 1, 1)
        self.rosette_controls = [RosetteControls(self, grid, 1, row, ""),
                                 RosetteControls(self, grid, 2, row, rr.SECOND)]
        row = self.rosette_controls[0].last_row + 1

        self.rubber = Gtk.ComboBoxText()
        self.rubber.append("point", "Point")
        self.rubber.connect("changed", lambda w: self._changed())
        row = self._row(grid, row, "Rubber", self.rubber,
                        "The rubber that follows the rosette. Only a point for now - it follows the "
                        "shape exactly.")

        row = self._section(grid, row, "Depth")
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

        row = self._section(grid, row, "Object Size")
        self.preview_radius = self._spin(*ranges["preview_radius"])
        row = self._row(grid, row, "Radius (%s)" % unit, self.preview_radius,
                        "The radius of the object being made - for a rosette you'll use later, the "
                        "rosette's radius. For the drawing and Straight sides only: the program cuts "
                        "wherever the cutter is.")
        radius_box, self.radius_at = self._radios((("outside", "Outside (largest)"),
                                                   ("inside", "Inside (smallest)")))
        row = self._row(grid, row, "Radius is the", radius_box,
                        "Whether Radius is where the cut comes furthest out or closest in. The note "
                        "under the drawings says where to start the cutter for it.")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(560)
        # Ask for the whole form's height (scrolls only on a small screen).
        scroll.set_propagate_natural_height(True)
        scroll.add(grid)
        return scroll

    def _build_header(self):
        '''The main panel's header: "Rosetta", the O/S version (and the
        machine's S/N) under it, the logo on the right, then a line.'''
        grid = Gtk.Grid()
        title = Gtk.Label(xalign=0, hexpand=True)
        title.set_markup('<span font_desc="DejaVu Serif 20" weight="bold" foreground="%s">Rosetta</span>'
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
        self.turns.set_value(d["turns"])
        self.deeper_plus.set_active(d["deeper_plus"])
        self.preview_radius.set_value(d["preview_radius"])
        self.radius_at[d["radius_at"]].set_active(True)
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
            "turns": int(self.turns.get_value()),
            "deeper_plus": self.deeper_plus.get_active(),
            "preview_radius": self.preview_radius.get_value(),
            "radius_at": self._chosen(self.radius_at),
            "units": self.units,
        }
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
        for widget in (self.passes, self.depth_per_pass, self.plunge_feed):
            widget.set_sensitive(passes)
        self.turns.set_sensitive(not passes)
        both = d["motion"] == "both"
        self.rosette_controls[1].set_shown(both)
        for column, controls in enumerate(self.rosette_controls):
            heading = ROSETTE_HEADINGS.get((d["motion"], column), "")
            controls.heading.set_markup("<i>%s</i>" % heading)
            axis = "Z" if (d["motion"] == "pump" or column == 1) else "X"
            controls.update_sensitivity(axis, d)
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
        count = d["passes"] if d["depth_mode"] == "passes" else d["turns"]
        unit = "in" if self.units == "inch" else "mm"
        text = ("%d points per turn.  One turn takes about %s; the whole program about %s."
                % (len(angles) - 1, self._duration(seconds / 60.0), self._duration(count * seconds / 60.0)))
        if d["depth_mode"] == "passes":
            text += "  Final depth %s %s." % (self._number(d["passes"] * d["depth_per_pass"]), unit)
        if d["surface"] == "face" and "X" in offsets:
            text += ("\nFor the cut's %s to be at radius %s %s, start the cutter at radius %s %s."
                     % (d["radius_at"], self._number(d["preview_radius"]), unit,
                        self._number(rr.start_radius(d)), unit))

        warnings = []
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
        outer = max(radius, d["preview_radius"]) + spread * 1.1 + radius * 0.15
        scale = 0.46 * min(width, height) / outer
        cx, cy = width / 2.0, height / 2.0
        cr.set_source_rgb(*WOOD)
        cr.arc(cx, cy, outer * scale, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgb(*GUIDE)
        cr.set_line_width(1)
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
