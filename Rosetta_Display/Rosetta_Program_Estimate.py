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
#   Rosetta_Program_Estimate.py
#
# Purpose:  Works out, without moving anything, every move a G-code
#   program will make, in the order it makes them - for the main
#   panel's program progress bar (see "Program progress" in
#   Rosetta_main.py, which starts this in the background when a program
#   is loaded):
#
#       python3 Rosetta_Program_Estimate.py <program.ngc> <output.json>
#
#   It runs the program through LinuxCNC's own interpreter the way
#   AXIS draws its preview, so o-word loops, If blocks and subroutine
#   calls are followed for real (counting line numbers can't do that -
#   a loop runs the same lines over and over). For each move it notes
#   the path length LinuxCNC's motion planner will count for it - the
#   X/Y/Z distance, or U/V/W if only those move, or A/B/C if only
#   rotary axes move - in machine units, and a time estimate from the
#   feed rate and each axis's MAX_VELOCITY and MAX_ACCELERATION, each
#   move treated as starting and ending at rest. That overestimates
#   the total (LinuxCNC blends moves together - Rich's
#   Geo1216Case12-10-13-26b.ngc: 13.5 min estimated, 10 min real) but
#   keeps the proportions right, which is all the percentage needs:
#   without acceleration the bar ran up to 30% behind on that
#   program, with it within 6% (20 October 2026).
#
#   The output is JSON: "length" and "time" are running totals per
#   move, "line" each move's program line. Rosetta.hal integrates
#   motion.current-vel (program-path.out), which grows by the same
#   path length as the machine moves, so the panel can find how far
#   through the list the program is however its lines repeat.
#
#   Needs LinuxCNC running (INI_FILE_NAME in the environment, and its
#   status for the tool table) - the panel's own environment has both.
#   The first move is from where the machine is now, so the panel runs
#   this as a program starts, not when it's loaded (a jog in between
#   would change that move's length and shift every total after it).
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 20 October 2026
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
import shutil
import sys
import tempfile

import gcode
import linuxcnc
from rs274.interpret import Translated, ArcsToSegmentsMixin, StatMixin

AXES = "XYZABCUVW"
ANGULAR = (3, 4, 5)        # A, B, C positions in a 9-axis tuple
TINY = 1e-9


class EstimateCanon(Translated, ArcsToSegmentsMixin, StatMixin):
    '''
    Interpreter callbacks: records each move's planner length and time.
    The interpreter works in inches and degrees whatever the machine's
    units; `to_machine` converts linear distances for comparing with
    HAL (motion.current-vel is in machine units).
    '''
    def __init__(self, stat, max_vel, max_accel, to_machine):
        StatMixin.__init__(self, stat, 0)
        self.max_vel = max_vel          # 9 values, machine units/s (0 = unused)
        self.max_accel = max_accel      # 9 values, machine units/s^2
        self.to_machine = to_machine
        self.pos = None
        self.feed = 1.0                 # inches (or degrees) per second
        self.lineno = 0
        self.total_length = 0.0
        self.total_time = 0.0
        self.lines = []
        self.lengths = []
        self.times = []

    # Calls that need an answer or that matter here; everything else
    # the interpreter calls is accepted and ignored (__getattr__).
    def next_line(self, st):
        self.lineno = st.sequence_number

    def set_feed_rate(self, rate):
        self.feed = rate / 60.0

    def comment(self, text):
        pass

    def message(self, text):
        pass

    def check_abort(self):
        return False

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *args, **kwargs: None

    def straight_traverse(self, *args):
        self._move(self.rotate_and_translate(*args), rapid=True)

    def straight_feed(self, *args):
        self._move(self.rotate_and_translate(*args), rapid=False)

    straight_probe = straight_feed

    def straight_arcsegments(self, segments):
        for end in segments:
            self._move(tuple(end), rapid=False)

    def rigid_tap(self, x, y, z):
        if self.pos is None:
            return
        there = (x, y, z) + tuple(self.pos[3:])
        start = self.pos
        self._move(there, rapid=False)
        self._move(start, rapid=False)

    def dwell(self, seconds):
        self._record(0.0, seconds)

    def _move(self, end, rapid):
        if self.pos is None:            # the interpreter's start position
            self.pos = end
            return
        delta = [end[i] - self.pos[i] for i in range(9)]
        self.pos = end
        machine = [d if i in ANGULAR else d * self.to_machine for i, d in enumerate(delta)]
        xyz = math.sqrt(sum(d * d for d in delta[0:3]))
        uvw = math.sqrt(sum(d * d for d in delta[6:9]))
        abc = math.sqrt(sum(d * d for d in delta[3:6]))
        # LinuxCNC's planner measures a move by X/Y/Z, else U/V/W, else
        # A/B/C - the length its current-vel is a speed along.
        if xyz > TINY:
            length, scale = xyz, self.to_machine
        elif uvw > TINY:
            length, scale = uvw, self.to_machine
        elif abc > TINY:
            length, scale = abc, 1.0
        else:
            return
        # Cruising: slowest axis at its MAX_VELOCITY; a feed move also
        # at its feed. Then each axis at the speed that gives, speeding
        # up and slowing down at its MAX_ACCELERATION.
        cruise = 0.0
        for i, d in enumerate(machine):
            if abs(d) > TINY and self.max_vel[i] > 0:
                cruise = max(cruise, abs(d) / self.max_vel[i])
        if not rapid and self.feed > 0:
            cruise = max(cruise, length / self.feed)
        seconds = cruise
        if cruise > 0:
            for i, d in enumerate(machine):
                if abs(d) > TINY:
                    seconds = max(seconds, rest_to_rest(abs(d), abs(d) / cruise,
                                                        self.max_accel[i]))
        self._record(length * scale, seconds)

    def _record(self, length, seconds):
        self.total_length += length
        self.total_time += seconds
        self.lines.append(self.lineno)
        self.lengths.append(round(self.total_length, 6))
        self.times.append(round(self.total_time, 4))


def rest_to_rest(distance, speed, accel):
    '''Seconds to move `distance` from rest to rest, at most `speed`.'''
    if accel <= 0:
        return distance / speed
    if distance >= speed * speed / accel:
        return distance / speed + speed / accel     # speeds up, cruises, slows
    return 2 * math.sqrt(distance / accel)          # never reaches `speed`


def main():
    program, output = sys.argv[1], sys.argv[2]
    ini_path = os.environ["INI_FILE_NAME"]
    ini = linuxcnc.ini(ini_path)
    stat = linuxcnc.stat()
    stat.poll()

    inch = (ini.find("TRAJ", "LINEAR_UNITS") or "inch").strip().lower() in ("inch", "in", "imperial")
    to_machine = 1.0 if inch else 25.4
    max_vel = [float(ini.find("AXIS_" + a, "MAX_VELOCITY") or 0) for a in AXES]
    max_accel = [float(ini.find("AXIS_" + a, "MAX_ACCELERATION") or 0) for a in AXES]

    canon = EstimateCanon(stat, max_vel, max_accel, to_machine)
    # The interpreter saves its parameters at the end, so give it a
    # copy - like AXIS's preview - never the machine's own file.
    parameter = os.path.join(os.path.dirname(ini_path),
                             ini.find("RS274NGC", "PARAMETER_FILE") or "sim.var")
    workdir = tempfile.mkdtemp(prefix="Rosetta_estimate_")
    canon.parameter_file = os.path.join(workdir, os.path.basename(parameter))
    if os.path.exists(parameter):
        shutil.copy(parameter, canon.parameter_file)

    initcodes = []
    startup = ini.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""
    if startup:
        initcodes.append(startup)
    initcodes.append("G90")
    # Start from where the machine is now, as the run will.
    position = "G53 G0"
    for i, a in enumerate(AXES):
        if stat.axis_mask & (1 << i):
            p = stat.position[i]
            position += " %s%.6f" % (a, p if i in ANGULAR else p / to_machine)
    initcodes.append("G20")
    initcodes.append(position)
    if not inch:
        initcodes.append("G21")

    result = {"file": program, "mtime": os.path.getmtime(program)}
    try:
        code, seq = gcode.parse(program, canon, initcodes)
        if code > gcode.MIN_ERROR:
            result["error"] = "line %d: %s" % (seq, gcode.strerror(code))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    result.update({"line": canon.lines, "length": canon.lengths, "time": canon.times})

    with open(output + ".part", "w") as f:
        json.dump(result, f, separators=(",", ":"))
    os.replace(output + ".part", output)


if __name__ == "__main__":
    main()
