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
#   follows the rosette (rocking) or Z does (pumping), starting from
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
#   ~/.config/Rosetta/rosette_designer.json.
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

import json
import math
import os
import subprocess
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

import numpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosetta_rosettes as rr
import rosetta_settings_io

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GCODE_DIR = os.path.join(REPO_DIR, "gcode")       # Rosetta.ini's [DISPLAY]PROGRAM_PREFIX
LAST_DESIGN_PATH = os.path.expanduser("~/.config/Rosetta/rosette_designer.json")

# Settings measured in machine units: converted when the measurement
# system differs from the one a design was made in.
LENGTH_KEYS = ("amplitude", "depth_per_pass", "preview_radius")
FEED_KEYS = ("plunge_feed",)

# Spin button ranges, per unit: (lower, upper, step, digits).
RANGES = {
    "inch": {"amplitude": (0.0001, 1.0, 0.001, 4), "depth_per_pass": (0.0001, 0.1, 0.001, 4),
             "plunge_feed": (0.1, 20.0, 0.1, 1), "preview_radius": (0.05, 10.0, 0.05, 3)},
    "mm": {"amplitude": (0.002, 25.0, 0.02, 3), "depth_per_pass": (0.002, 2.5, 0.02, 3),
           "plunge_feed": (2.0, 500.0, 1.0, 0), "preview_radius": (1.0, 250.0, 1.0, 1)},
}

# Drawing colours.
INK = (0.10, 0.10, 0.35)
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
        Gtk.Window.__init__(self, title="Rosette Designer")
        self.set_default_size(1250, 920)
        self.connect("delete-event", self._on_close)

        settings = rosetta_settings_io.load_settings()
        self.settings = settings
        self.units = "mm" if settings.get("measurement_system") == "Metric" else "inch"
        self.loading = False
        self.design = self._load_last_design()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=10)
        self.add(outer)
        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.pack_start(columns, True, True, 0)

        columns.pack_start(self._build_form(), False, False, 0)
        columns.pack_start(self._build_previews(), True, True, 0)

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

    def _row(self, grid, row, text, widget, tip=None, extra=None):
        label = Gtk.Label(label=text, xalign=0)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(widget, 1, row, 1, 1)
        if extra is not None:
            grid.attach(extra, 2, row, 1, 1)
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
        row = self._section(grid, 0, "Rosette")

        self.shape = Gtk.ComboBoxText()
        for shape_id in rr.SHAPE_IDS:
            self.shape.append(shape_id, rr.SHAPES[shape_id][0])
        self.shape.connect("changed", lambda w: self._changed())
        row = self._row(grid, row, "Shape", self.shape, "The shape of each lobe.")

        self.lobes = self._spin(1, 360, 1, 0)
        row = self._row(grid, row, "Lobes", self.lobes,
                        "How many times the shape repeats around the rosette (e.g. 24 for a Sine 24).")

        self.amplitude = self._spin(*ranges["amplitude"])
        self.straight = Gtk.Button(label="Straight sides")
        self.straight.set_tooltip_text("Sets the amplitude that makes a plain polygon's sides straight "
                                       "at the preview radius.")
        self.straight.connect("clicked", self._on_straight_sides)
        row = self._row(grid, row, "Amplitude (%s)" % unit, self.amplitude,
                        "How far the cutter moves, peak to peak, as at the rubber of a rose engine.",
                        self.straight)

        self.phase = self._spin(0.0, 1.0, 0.05, 3)
        phase_box, self.phase_unit = self._radios((("lobe", "of a lobe"), ("deg", "degrees")))
        for button in self.phase_unit.values():
            button.connect("toggled", self._on_phase_unit)
        row = self._row(grid, row, "Phase", self.phase,
                        "Turns the rosette relative to the work: a fraction of one lobe (0.5 = half a "
                        "lobe), or degrees of the spindle.", phase_box)

        self.invert = Gtk.CheckButton(label="Invert")
        self.invert.set_tooltip_text("Turns the shape inside out (points become hollows).")
        self.invert.connect("toggled", lambda w: self._changed())
        grid.attach(self.invert, 1, row, 2, 1)
        row += 1

        self.rubber = Gtk.ComboBoxText()
        self.rubber.append("point", "Point")
        self.rubber.set_tooltip_text("The rubber that follows the rosette. Only a point for now - "
                                     "it follows the shape exactly.")
        self.rubber.connect("changed", lambda w: self._changed())
        row = self._row(grid, row, "Rubber", self.rubber)

        row = self._section(grid, row, "Movement")
        motion_box, self.motion = self._radios((("rock", "Rocking (X)"), ("pump", "Pumping (Z)")))
        row = self._row(grid, row, "Motion", motion_box,
                        "Rocking moves the cutter in X, pumping in Z.")
        surface_box, self.surface = self._radios((("face", "Face"), ("side", "Side")))
        row = self._row(grid, row, "Cutting on", surface_box,
                        "Where the cut is: the face (end) of the work, or its side. Sets which axis "
                        "goes deeper (Z on the face, X on the side) and the drawing.")
        self.c_rpm = self._spin(0.1, 60.0, 0.1, 1)
        row = self._row(grid, row, "C speed (rev/min)", self.c_rpm,
                        "How fast C turns the work while cutting.")
        direction_box, self.c_direction = self._radios(((1, "+"), (-1, "-")))
        row = self._row(grid, row, "C direction", direction_box, "Which way C turns.")

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

        row = self._section(grid, row, "Drawing")
        self.preview_radius = self._spin(*ranges["preview_radius"])
        row = self._row(grid, row, "Radius (%s)" % unit, self.preview_radius,
                        "The radius where you'll cut - for the drawing only. The program cuts wherever "
                        "the cutter is.")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(470)
        # Ask for the whole form's height (scrolls only on a small screen).
        scroll.set_propagate_natural_height(True)
        scroll.add(grid)
        return scroll

    def _build_previews(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.profile_title = Gtk.Label(xalign=0)
        self.profile_title.set_markup("<b>The rosette</b> - how far the cutter moves as the work turns")
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
        self.shape.set_active_id(d["shape"])
        self.lobes.set_value(d["lobes"])
        self.amplitude.set_value(d["amplitude"])
        self.phase_unit[d["phase_unit"]].set_active(True)
        self._set_phase_range()
        self.phase.set_value(d["phase"] if d["phase_unit"] == "lobe" else rr.phase_degrees(d))
        self.invert.set_active(d["invert"])
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
        self.loading = False

    def _chosen(self, radios):
        return next(value for value, button in radios.items() if button.get_active())

    def _set_phase_range(self):
        if self._chosen(self.phase_unit) == "lobe":
            self.phase.set_range(0.0, 1.0)
            self.phase.set_increments(0.05, 0.25)
            self.phase.set_digits(3)
        else:
            lobe_deg = 360.0 / max(int(self.lobes.get_value()), 1)
            self.phase.set_range(0.0, lobe_deg)
            self.phase.set_increments(0.5, 5.0)
            self.phase.set_digits(2)

    def _on_phase_unit(self, widget):
        # Keep the same phase, shown in the other unit.
        if self.loading or not widget.get_active():
            return
        fraction = self.design["phase"]
        self.loading = True
        self._set_phase_range()
        self.phase.set_value(fraction if self._chosen(self.phase_unit) == "lobe"
                             else fraction * 360.0 / self.design["lobes"])
        self.loading = False
        self._changed()

    def _read_form(self):
        lobes = int(self.lobes.get_value())
        unit = self._chosen(self.phase_unit)
        phase = self.phase.get_value()
        if unit == "deg":
            phase = phase * lobes / 360.0
            # The degrees range follows the lobes.
            self.loading = True
            self._set_phase_range()
            self.loading = False
        return rr.clean_design({
            "shape": self.shape.get_active_id(),
            "lobes": lobes,
            "amplitude": self.amplitude.get_value(),
            "phase": phase,
            "phase_unit": unit,
            "invert": self.invert.get_active(),
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
            "units": self.units,
        })

    def _changed(self):
        if self.loading:
            return
        self.design = self._read_form()
        passes = self.design["depth_mode"] == "passes"
        for widget in (self.passes, self.depth_per_pass, self.plunge_feed):
            widget.set_sensitive(passes)
        self.turns.set_sensitive(not passes)
        self.straight.set_sensitive(self.design["shape"] == "polygon" and not self.design["invert"])
        self._update_info()
        self.profile_area.queue_draw()
        self.cut_area.queue_draw()
        self._save_last_design()

    def _on_straight_sides(self, widget):
        d = self.design
        self.amplitude.set_value(rr.straight_sides_amplitude(d, d["preview_radius"]))

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
        letter = rr.motion_axis(d)
        limit = self._axis_limit(letter)
        c_limit = self._axis_limit("C")
        seconds, nominal = rr.turn_time(d, limit, c_limit, points)
        count = d["passes"] if d["depth_mode"] == "passes" else d["turns"]
        unit = "in" if self.units == "inch" else "mm"
        text = ("%d points per turn.  One turn takes about %s; the whole program about %s."
                % (len(angles) - 1, self._duration(seconds / 60.0), self._duration(count * seconds / 60.0)))
        if d["depth_mode"] == "passes":
            text += "  Final depth %s %s." % (self._number(d["passes"] * d["depth_per_pass"]), unit)

        warnings = []
        roles = self._assigned_roles()
        needed = sorted(set(["C", rr.motion_axis(d), rr.depth_axis(d)]))
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
            warnings.append("%s can't always keep up with C at this speed (its Max Speed is %s %s/sec), "
                            "so C slows down at the steepest places - one turn takes about %s instead "
                            "of %s." % (letter, self._number(limit), unit,
                                        self._duration(seconds / 60.0), self._duration(nominal / 60.0)))
        if capped:
            warnings.append("This rosette needs more than %d points per turn, so the cut will be "
                            "slightly less exact." % rr.MAX_POINTS_PER_TURN)
        if warnings:
            text += "\n" + "\n".join('<span foreground="#c06000"><b>Note:</b> %s</span>'
                                     % GLib.markup_escape_text(w) for w in warnings)
        self.info.set_markup(text)

        surface, motion = d["surface"], d["motion"]
        titles = {
            ("face", "rock"): "the groove on the face, seen from the end",
            ("side", "pump"): "the groove around the side, unrolled",
            ("face", "pump"): "the face, seen from the end - darker is deeper",
            ("side", "rock"): "the side, unrolled - darker is deeper",
        }
        self.cut_title.set_markup("<b>The cut</b> - " + titles[(surface, motion)])

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
    def _draw_profile(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        d = self.design
        theta = numpy.linspace(0.0, 360.0, 2000)
        y = rr.offset(d, theta)
        low, high = min(y.min(), -d["amplitude"]), max(y.max(), 0.0)
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
        cr.set_source_rgb(*INK)
        cr.set_line_width(1.6)
        for i, (t, v) in enumerate(zip(theta, y)):
            (cr.move_to if i == 0 else cr.line_to)(*px(t, v))
        cr.stroke()

    def _draw_cut(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        d = self.design
        steps = int(min(max(2000, d["lobes"] * 60), 20000))
        theta = numpy.linspace(0.0, 360.0, steps)
        y = rr.offset(d, theta)
        if d["surface"] == "face":
            self._draw_face(cr, width, height, theta, y, d)
        else:
            self._draw_side(cr, width, height, theta, y, d)

    def _draw_face(self, cr, width, height, theta, y, d):
        radius = d["preview_radius"]
        outer = radius + (d["amplitude"] if d["motion"] == "rock" else 0) * 1.1 + radius * 0.15
        scale = 0.46 * min(width, height) / outer
        cx, cy = width / 2.0, height / 2.0
        cr.set_source_rgb(*WOOD)
        cr.arc(cx, cy, outer * scale, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgb(*GUIDE)
        cr.set_line_width(1)
        cr.arc(cx, cy, radius * scale, 0, 2 * math.pi)
        cr.stroke()
        angles = numpy.radians(theta)
        if d["motion"] == "rock":
            r = numpy.clip(radius + y, 0.0, None)
            cr.set_source_rgb(*INK)
            cr.set_line_width(2.0)
            for i in range(len(theta)):
                point = (cx + r[i] * scale * math.cos(angles[i]), cy - r[i] * scale * math.sin(angles[i]))
                (cr.move_to if i == 0 else cr.line_to)(*point)
            cr.close_path()
            cr.stroke()
        else:
            self._depth_ring(cr, cx, cy, radius * scale, max(6.0, radius * scale * 0.08), angles, y, d)
        cr.set_source_rgb(*INK)
        cr.arc(cx, cy, 2.5, 0, 2 * math.pi)
        cr.fill()

    @staticmethod
    def _depths(y, d):
        '''0 (shallowest in the turn) to 1 (deepest) for each offset.'''
        deeper = y if d["deeper_plus"] else -y
        span = deeper.max() - deeper.min()
        return (deeper - deeper.min()) / span if span > 1e-12 else numpy.zeros_like(y)

    @staticmethod
    def _depth_shade(depth):
        return (0.85 - 0.75 * depth, 0.80 - 0.70 * depth, 0.75 - 0.45 * depth)

    def _depth_ring(self, cr, cx, cy, r, band, angles, y, d):
        cr.set_line_width(band)
        depths = self._depths(y, d)
        for i in range(len(angles) - 1):
            cr.set_source_rgb(*self._depth_shade(depths[i]))
            cr.arc_negative(cx, cy, r, -angles[i], -angles[i + 1] - 0.002)
            cr.stroke()

    def _draw_side(self, cr, width, height, theta, y, d):
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
        if d["motion"] == "pump":
            # The groove wanders along Z: scale so the full amplitude
            # fills half the band, but never exaggerate more than the
            # band's own size in circumference terms.
            circumference = 2 * math.pi * d["preview_radius"]
            scale = (right - left) / circumference
            scale = min(scale, (bottom - top) * 0.4 / max(d["amplitude"], 1e-9))
            cr.set_source_rgb(*INK)
            cr.set_line_width(2.0)
            for i, (t, v) in enumerate(zip(theta, y)):
                point = (left + (right - left) * t / 360.0, mid - v * scale - d["amplitude"] * scale / 2)
                (cr.move_to if i == 0 else cr.line_to)(*point)
            cr.stroke()
        else:
            band = (bottom - top) * 0.2
            cr.set_line_width(1.0)
            depths = self._depths(y, d)
            for i in range(len(theta) - 1):
                x0 = left + (right - left) * theta[i] / 360.0
                x1 = left + (right - left) * theta[i + 1] / 360.0
                cr.set_source_rgb(*self._depth_shade(depths[i]))
                cr.rectangle(x0, mid - band / 2, max(x1 - x0, 0.6), band)
                cr.fill()

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


def main():
    window = DesignerWindow()
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
