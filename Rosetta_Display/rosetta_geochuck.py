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
#   rosetta_geochuck.py
#
# Purpose:
#   The maths of a geometric chuck, for the Geometric Chuck Designer
#   (Rosetta_GeoChuck_Designer.py), which saves a pattern as a G-code
#   program cut on the face: C turns the work and X moves the cutter
#   in and out, so the cutter traces the pattern the chuck would
#   (https://otbok.info/index.php?n=Main.GeometricChuck).
#
#   A geometric chuck stacks circular motions - "wheels on wheels".
#   The point cut, in the work's own frame, is the sum over its stages
#
#       z(t) = r1 e^(i(k1 t + p1)) + r2 e^(i(k2 t + p2)) + ...
#
#   r = a stage's offset (machine units), k = how fast it turns for
#   each turn of the work (a whole number, negative for the other way,
#   or a fraction such as 7/3), p = its phase (where it is set at the
#   start, degrees). Stage 1 is normally the cutter's own distance
#   from the centre, k = 1. A stage with r = 0 is unused.
#
#   Clean room (17 November 2026): written from Frank A. Farris,
#   "Wheels on Wheels on Wheels - Surprising Symmetry" (Mathematics
#   Magazine, 1996), T. S. Bazley, "Index to the Geometric Chuck"
#   (1875, public domain), and the Ornamental Turning Book of
#   Knowledge's Geometric Chuck page; first worked out in a Claude
#   session on Rich's Mac (16 November 2026, geochuck.py). See
#   docs/Rosetta_Tracker.md, "Provenance". No other software consulted.
#
#   C and X: each point is turned into an angle (C) and a radius (X).
#   C is kept continuous; where the pattern passes through or near the
#   centre the radius goes negative - the cutter crosses to the other
#   side of the centre - rather than C jumping half a turn (the line's
#   direction, unwrapped from twice the angle, so its sign is free).
#   Like the Rosette Designer, the program moves X and C from wherever
#   they are when it starts: started at the radius the Designer gives
#   (start_radius), it cuts the pattern exactly.
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
#   1.1 - 17 November 2026 - Bazley's figures: bazley_design fills in
#         the stages for a figure in Bazley_Index.csv (the pilot, table
#         page 71, figures 666-716)
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
import sys
import time
from fractions import Fraction
from functools import reduce

import numpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rosetta_rosettes as rr    # shared G-code pieces (numbers, pass codes, advance, names)


#######################################################################
# The design
#######################################################################

STAGES = 5          # enough for all of Bazley's figures, incl. his 3- and 4-part ones

DEFAULT_DESIGN = {
    # Stage n: rn (offset), kn (speed, text such as "6", "-4" or "7/3"),
    # phasen (degrees). Stage 1 is normally the cutter's distance from
    # the centre, k 1.
    "r1": 1.0, "k1": "1", "phase1": 0.0,
    "r2": 0.25, "k2": "6", "phase2": 0.0,
    "r3": 0.0, "k3": "0", "phase3": 0.0,
    "r4": 0.0, "k4": "0", "phase4": 0.0,
    "r5": 0.0, "k5": "0", "phase5": 0.0,
    "cutting_speed": 2.0,       # machine units/min along the pattern
    "c_direction": 1,           # +1 or -1 (-1 mirrors the pattern)
    "depth_mode": "passes",     # "passes" (deeper each pass) or "turns" (same depth)
    "passes": 3,
    "depth_per_pass": 0.005,
    "turns": 1,
    "deeper_plus": False,
    "plunge_feed": 1.0,
    "finish_pass": False,
    "finish_pct": 10.0,         # finishing (and spring) passes, % of cutting_speed
    "spring_passes": 0,
    "advance_x": 0.0,
    "advance_x_dir": "centre",
    "advance_z": 0.0,
    "advance_z_dir": "headstock",
    "surface": "face",          # always - for the shared advance helpers
    "units": "inch",
    "bazley_figure": 0,         # the Bazley figure the stages came from (0 = none)
}

# Presets: (name, {stage settings}) - each a classic figure.
PRESETS = (
    ("Ellipse (k -1)", {"r1": 1.0, "k1": "1", "r2": 0.5, "k2": "-1"}),
    ("5 lobes, small loops inside (k 6)", {"r1": 1.0, "k1": "1", "r2": 0.25, "k2": "6"}),
    ("5-point star (k -4)", {"r1": 1.0, "k1": "1", "r2": 0.3, "k2": "-4"}),
    ("4 loops through the centre (k 5)", {"r1": 1.0, "k1": "1", "r2": 1.0, "k2": "5"}),
    ("Loops that close after 3 turns (k 7/3)", {"r1": 1.0, "k1": "1", "r2": 0.5, "k2": "7/3"}),
    ("Three stages (k 6 and -4)", {"r1": 1.0, "k1": "1", "r2": 0.2, "k2": "6", "r3": 0.1, "k3": "-4"}),
    ("3 petals through the centre, ends opposite (k -2)", {"r1": 1.0, "k1": "1", "r2": 1.0, "k2": "-2"}),
)

# Straight-line error allowed between the program's points and the
# true pattern, per unit (as the Rosette Designer).
CHORD_TOLERANCE = rr.CHORD_TOLERANCE
MAX_SEGMENT_DEG = 2.0           # no move turns C more than this
MAX_POINTS = 60000              # per pattern
MAX_SAMPLES = 400000


def parse_k(text):
    '''A stage speed: "6", "-4", "2.5" or "7/3" -> Fraction (None if not a number).'''
    try:
        return Fraction(str(text).strip()).limit_denominator(1000)
    except (ValueError, ZeroDivisionError):
        return None


def clean_design(design):
    '''A complete design: DEFAULT_DESIGN's keys, each of the right kind.'''
    d = dict(DEFAULT_DESIGN)
    for key, default in DEFAULT_DESIGN.items():
        value = (design or {}).get(key, default)
        try:
            if isinstance(default, bool):
                value = bool(value)
            elif isinstance(default, int):
                value = int(value)
            elif isinstance(default, float):
                value = float(value)
            else:
                value = str(value)
        except (TypeError, ValueError):
            value = default
        d[key] = value
    for n in range(1, STAGES + 1):
        k = parse_k(d["k%d" % n])
        d["k%d" % n] = str(k) if k is not None else "0"
        d["r%d" % n] = max(d["r%d" % n], 0.0)
        d["phase%d" % n] = d["phase%d" % n] % 360.0
    for key, choices in (("depth_mode", ("passes", "turns")), ("units", ("inch", "mm")),
                         ("advance_x_dir", ("centre", "away")),
                         ("advance_z_dir", ("headstock", "away"))):
        if d[key] not in choices:
            d[key] = DEFAULT_DESIGN[key]
    d["surface"] = "face"
    d["c_direction"] = -1 if d["c_direction"] < 0 else 1
    d["cutting_speed"] = max(d["cutting_speed"], 1e-3)
    d["passes"] = min(max(d["passes"], 1), 100)
    d["turns"] = min(max(d["turns"], 1), 100)
    d["finish_pct"] = min(max(d["finish_pct"], 1.0), 100.0)
    d["spring_passes"] = min(max(d["spring_passes"], 0), 5)
    for axis in ("x", "z"):
        d["advance_" + axis] = max(d["advance_" + axis], 0.0)
    if d["bazley_figure"] and not bazley_matches(d):
        d["bazley_figure"] = 0      # the stages have been changed since
    return d


def stages(design):
    '''[(r, k as Fraction, phase in radians)] for the stages in use.'''
    found = []
    for n in range(1, STAGES + 1):
        r, k = design["r%d" % n], parse_k(design["k%d" % n])
        if r > 0 and k is not None:
            found.append((r, k, math.radians(design["phase%d" % n])))
    return found


#######################################################################
# The pattern
#######################################################################

def closing_turns(design):
    '''How many turns of the work before the pattern repeats.'''
    lcm = lambda a, b: a * b // math.gcd(a, b)
    return reduce(lcm, (k.denominator for _, k, _ in stages(design)), 1)


def symmetry(design):
    '''n-fold symmetry of the pattern (0 = a plain circle or a point).'''
    found = stages(design)
    turns = closing_turns(design)
    freqs = [int(k * turns) for _, k, _ in found]
    if len(freqs) < 2:
        return 0
    return reduce(math.gcd, (abs(f - freqs[0]) for f in freqs[1:]), 0)


def points(design, t):
    '''The cut's points (complex, work frame) at t (radians of the work's
    turn, numpy array); mirrored when C turns the other way.'''
    z = numpy.zeros(len(t), dtype=complex)
    for r, k, phase in stages(design):
        z += r * numpy.exp(1j * (float(k) * t + phase))
    return z if design["c_direction"] > 0 else numpy.conj(z)


def _samples(design):
    '''t and z sampled finely over the whole pattern - finely enough that
    the direction from the centre never jumps far between samples, even
    where the pattern passes close by it.'''
    total = 2.0 * math.pi * closing_turns(design)
    fastest = max([abs(float(k)) for _, k, _ in stages(design)] + [1.0])
    count = int(min(max(20000, 2000 * closing_turns(design) * fastest), MAX_SAMPLES))
    for _ in range(3):
        t = numpy.linspace(0.0, total, count + 1)
        z = points(design, t)
        step = numpy.abs(numpy.diff(z))
        near = numpy.maximum(numpy.minimum(numpy.abs(z[1:]), numpy.abs(z[:-1])), 1e-9)
        worst = numpy.max(step / near) if len(step) else 0.0
        # Passing exactly through the centre is fine (the line goes
        # straight through); close by, the angle swings fast.
        if worst < 0.2 or count >= MAX_SAMPLES:
            break
        count = int(min(count * min(worst / 0.2, 8.0) + 1, MAX_SAMPLES))
    return t, z


def polar(z):
    '''(angle in degrees, signed radius) for each point: the angle is
    the direction of the line through the centre, unwrapped from twice
    the angle, so passing through the centre flips the radius's sign
    instead of turning C half a turn. Starts with a plus radius.'''
    line = numpy.unwrap(2.0 * numpy.angle(z)) / 2.0
    r = numpy.real(z * numpy.exp(-1j * line))
    if r[0] < 0:
        line, r = line + math.pi, -r
    return numpy.degrees(line), r


def pattern_path(design):
    '''
    (angles, radii, xy, capped) - the program's points over one whole
    pattern: C angles (degrees, from the start), signed radii, the true
    points (complex) at each, and whether MAX_POINTS cut it short. The
    fewest points whose straight C/X moves stay within CHORD_TOLERANCE
    of the pattern; no move turns C more than MAX_SEGMENT_DEG.
    '''
    tol = CHORD_TOLERANCE[design["units"]]
    t, z = _samples(design)
    deg, r = polar(z)
    rad = numpy.radians(deg)
    last = len(t) - 1

    def fits(i, j):
        if j - i <= 1:
            return True
        f = (numpy.arange(i, j + 1) - i) / float(j - i)
        a = rad[i] + (rad[j] - rad[i]) * f
        rr_ = r[i] + (r[j] - r[i]) * f
        machine = rr_ * numpy.exp(1j * a)
        return numpy.max(numpy.abs(machine - z[i:j + 1])) <= tol

    keep = [0]
    i = 0
    while i < last:
        # C may run either way - limit by how far it turns, whichever way.
        turned = numpy.abs(deg[i:] - deg[i])
        beyond = numpy.nonzero(turned > MAX_SEGMENT_DEG)[0]
        limit = i + (int(beyond[0]) - 1 if len(beyond) else last - i)
        limit = max(min(limit, last), i + 1)
        step = 1
        while i + step * 2 <= limit and fits(i, i + step * 2):
            step *= 2
        low, high = step, min(step * 2, limit - i)
        while low < high:
            mid = (low + high + 1) // 2
            if fits(i, i + mid):
                low = mid
            else:
                high = mid - 1
        i += low
        keep.append(i)
    keep = numpy.array(keep)
    capped = len(keep) - 1 > MAX_POINTS
    if capped:
        keep = keep[numpy.unique(numpy.round(numpy.linspace(0, len(keep) - 1,
                                                            MAX_POINTS + 1)).astype(int))]
    return deg[keep] - deg[0], r[keep], z[keep], capped


def pattern_info(design, path=None):
    '''What the note under the drawings says about the pattern.'''
    angles, radii, z, capped = path or pattern_path(design)
    length = float(numpy.sum(numpy.abs(numpy.diff(z))))
    flipped = radii[-1] < 0
    return {
        "turns": closing_turns(design),
        "symmetry": symmetry(design),
        "largest": float(numpy.max(numpy.abs(z))),
        "smallest": float(numpy.min(numpy.abs(z))),
        "start_radius": float(radii[0]),
        "past_centre": float(max(-numpy.min(radii), 0.0)),     # how far X goes past the centre
        "length": length,
        "c_turned": float(angles[-1]),          # C's net turn over one pattern (degrees)
        "flipped": bool(flipped),               # ends on the other side of the centre
        "points": len(angles) - 1,
        "capped": capped,
    }


def pass_speeds(design):
    '''The cutting speed for each time through the pattern, in order.'''
    d = design
    if d["depth_mode"] != "passes":
        return [d["cutting_speed"]] * d["turns"]
    finish = d["cutting_speed"] * d["finish_pct"] / 100.0 if d["finish_pass"] else d["cutting_speed"]
    return [d["cutting_speed"]] * (d["passes"] - 1) + [finish] * (1 + d["spring_passes"])


def pattern_time(design, speed=None, x_max=None, c_max=None, path=None):
    '''
    (seconds, nominal seconds) for one pattern at speed (machine units
    a minute, the design's cutting speed if None): nominal at that
    speed; seconds allowing for X's Max Speed (units/sec) and C's
    (deg/sec) - near the centre C turns fast, and slows the cut there.
    '''
    angles, radii, z, _ = path or pattern_path(design)
    speed = speed or design["cutting_speed"]
    nominal = numpy.abs(numpy.diff(z)) / speed * 60.0
    needed = nominal.copy()
    if x_max:
        needed = numpy.maximum(needed, numpy.abs(numpy.diff(radii)) / x_max)
    if c_max:
        needed = numpy.maximum(needed, numpy.abs(numpy.diff(angles)) / c_max)
    return float(needed.sum()), float(nominal.sum())


#######################################################################
# G-code
#######################################################################

DESIGN_PREFIX = rr.DESIGN_PREFIX
FILE_NAME_PREFIX = "GeoChuck-"
# The main panel's pass counter shows only for programs whose first
# line starts like this (Rosetta_main.py, GEOCHUCK_PROGRAM_MARK).
PROGRAM_MARK = "(Geometric Chuck Designer - "
name_is_reserved = rr.name_is_reserved


#######################################################################
# Bazley's figures (17 November 2026, Rich): T. S. Bazley, "Index to the
# Geometric Chuck" (1875, public domain) gives, for over 3,000 numbered
# figures, the settings of a two-part geometric chuck that cut them.
# Bazley_Index.csv holds those transcribed so far (see its header); this
# turns a figure's settings into the Designer's stages.
#
# The chuck, in Bazley's terms (worked out from his Chapters I-III in
# the Mac session of 16 November 2026): Part I's train value V1 (a gear
# ratio), "in" (an odd number of arbors, s = +1) or "out" (even, s = -1),
# makes its front wheel turn w1 = 1 + s1/V1 times per turn of the mandrel;
# Part II on top of it turns w2 = w1 + s1 s2 / (V1 V2). In the work's
# frame the point cut is
#     SR e^(-i w2 t) - Ex1 e^(i(1 - w2) t) - Ex2 e^(i(w1 - w2) t)
# with SR the tool's distance from the axis and Ex1, Ex2 the two
# eccentric slides, all in hundredths of an inch - three stages. A pair
# of companion figures differs by Part I set half a turn apart (Ex1's
# phase 180 or 0); which is which is in the file, matched to the plates.
# Checked against his plates for figures 666-716.
#######################################################################
BAZLEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Bazley_Index.csv")
_bazley = None


def bazley_index():
    """{figure: row} from Bazley_Index.csv (empty if it can't be read)."""
    global _bazley
    if _bazley is None:
        _bazley = {}
        try:
            with open(BAZLEY_PATH) as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            header = lines[0].split(",")
            for line in lines[1:]:
                row = dict(zip(header, line.split(",")))
                _bazley[int(row["figure"])] = row
        except (OSError, IndexError, KeyError, ValueError) as e:
            print("Could not read %s: %s" % (BAZLEY_PATH, e))
    return _bazley


def _train(text):
    """"2in" -> (2, +1), "9out" -> (9, -1)."""
    text = text.strip().lower()
    if text.endswith("in"):
        return Fraction(text[:-2]), 1
    return Fraction(text[:-3]), -1


def bazley_stage_values(row):
    """[(r in hundredths of an inch, k, phase in degrees)] for a figure's row."""
    v1, s1 = _train(row["v1"])
    v2, s2 = _train(row["v2"])
    w1 = 1 + Fraction(s1) / v1
    w2 = w1 + Fraction(s1 * s2) / (v1 * v2)
    found = [(float(row["sr"]), -w2, 0.0), (float(row["ex1"]), 1 - w2, float(row["ex1_phase"])),
             (float(row["ex2"]), w1 - w2, 180.0)]
    return [stage for stage in found if stage[0] > 0]


def bazley_design(figure, units):
    """The stage settings (r1..r5, k1..k5, phase1..phase5, bazley_figure)
    for Bazley's figure, in units ("inch" or "mm"); None if not in the index."""
    row = bazley_index().get(int(figure))
    if row is None:
        return None
    scale = 0.01 if units == "inch" else 0.254       # hundredths of an inch
    values = {"bazley_figure": int(figure)}
    for n in range(1, STAGES + 1):
        values.update({"r%d" % n: 0.0, "k%d" % n: "0", "phase%d" % n: 0.0})
    for n, (r, k, phase) in enumerate(bazley_stage_values(row), 1):
        values.update({"r%d" % n: r * scale, "k%d" % n: str(k), "phase%d" % n: phase})
    return values


def bazley_matches(design):
    """True if the design's stages are still those of its Bazley figure."""
    wanted = bazley_design(design["bazley_figure"], design["units"])
    if wanted is None:
        return False
    for n in range(1, STAGES + 1):
        if abs(design["r%d" % n] - wanted["r%d" % n]) > 1e-6 or \
                abs((design["phase%d" % n] - wanted["phase%d" % n] + 180.0) % 360.0 - 180.0) > 1e-6 or \
                (design["r%d" % n] > 0 and parse_k(design["k%d" % n]) != parse_k(wanted["k%d" % n])):
            return False
    return True


def bazley_settings_text(figure):
    """Bazley's own settings for a figure, for the note under the drawings."""
    row = bazley_index().get(int(figure))
    if row is None:
        return ""
    def train(text):
        v, s = _train(text)
        return "%s %s" % (v, "in" if s > 0 else "out")
    # Its companion: a neighbouring figure with the same trains and slides.
    same = ("v1", "v2", "ex1", "ex2")
    companion = [n for n in (int(figure) - 1, int(figure) + 1)
                 if n in bazley_index() and all(bazley_index()[n][key] == row[key] for key in same)]
    return ("V1 %s, V2 %s, Ex1 %s, Ex2 %s, S.R. %s (hundredths of an inch)%s - settings on page %s "
            "of his book"
            % (train(row["v1"]), train(row["v2"]), row["ex1"], row["ex2"], row["sr"],
               "; companion of figure %d" % companion[0] if companion else "", row["table_page"]))


def describe(design):
    if design.get("bazley_figure"):
        return "Bazley figure %d" % design["bazley_figure"]
    found = stages(design)
    if len(found) < 2:
        return "a circle"
    sym = symmetry(design)
    speeds = ", ".join("k %s" % k for _, k, _ in found[1:])
    # No brackets: LinuxCNC refuses a comment inside a comment.
    return "%d stages - %s - %s" % (len(found), speeds,
                                   "%d-fold" % sym if sym > 1 else "no rotational symmetry")


def default_file_name(design):
    if design.get("bazley_figure"):
        return FILE_NAME_PREFIX + "Bazley%d_face.ngc" % design["bazley_figure"]
    found = stages(design)
    sym = symmetry(design)
    parts = ["%dfold" % sym if sym > 1 else ("Circle" if len(found) < 2 else "Pattern")]
    parts += ["k%s" % str(k).replace("/", "-") for _, k, _ in found[1:]]
    return FILE_NAME_PREFIX + "_".join(parts) + "_face.ngc"


def gcode(design):
    '''The whole program, as text.'''
    d = clean_design(design)
    path = pattern_path(d)
    angles, radii, z, _ = path
    info = pattern_info(d, path)
    tol = CHORD_TOLERANCE[d["units"]]
    deeper = 1.0 if d["deeper_plus"] else -1.0
    speeds = pass_speeds(d)
    count = len(speeds)
    r0 = radii[0]

    advancing = rr.advance_order(d)
    if advancing:
        where = ["(Runs from where the cutter is: put it clear of the work - it moves in)",
                 "(%s first, cuts, then moves back out to where it started. Then run.)"
                 % " and ".join("%s %s" % (axis, rr._num(rr.advance(d, axis))) for axis in advancing)]
    else:
        where = ["(Runs from where the cutter is: put it at radius %s from the centre,)" % rr._num(r0),
                 "(then run.)"]
    lines = [
        PROGRAM_MARK + "%s - %s)" % (describe(d), time.strftime("%d %B %Y")),
    ] + where + [
        "(The pattern is cut %d time%s. Made by Rosetta's Geometric Chuck Designer -)"
        % (count, "" if count == 1 else "s"),
        "(open it there to change it.)",
    ] + [DESIGN_PREFIX + "%s %s)" % (key, json.dumps(d[key])) for key in sorted(d)] + [
        "",
        "#<_rd_diameter> = #<_lathe_diameter_mode>",
        "%s G8 G90 G64 P%s" % ("G20" if d["units"] == "inch" else "G21", rr._num(tol)),
        "#<_rd_x0> = #5420",
        "#<_rd_z0> = #5422",
        "#<_rd_c0> = #5425",
        "M68 E0 Q0  (pass counter for Rosetta's progress bar: this run's start)",
        "",
    ]
    if advancing:
        lines.append("(Advance: move in from where the cutter was put; the pattern is cut from here)")
        for axis in ("X", "Z"):
            lines.append("#<_rd_%s_back> = #<_rd_%s0>" % (axis.lower(), axis.lower()))
        for axis in advancing:
            var = "#<_rd_%s0>" % axis.lower()
            lines.append("%s = [%s%s]" % (var, var, rr._signed(rr.advance(d, axis))))
            lines.append("G94 G1 %s[%s] F%s" % (axis, var, rr._num(d["plunge_feed"])))
        lines.append("")
    lines += [
        "(One whole pattern. #1 = depth from the start, #2 = C at the start,)",
        "(#3 = speed factor: 1 at the set cutting speed, less for a slower finishing pass,)",
        "(#4 = 1, or -1 when the last pattern ended on the other side of the centre)",
        "o100 sub",
    ]
    nominal_minutes = numpy.abs(numpy.diff(z)) / d["cutting_speed"]
    for i in range(1, len(angles)):
        x = "X[#<_rd_x0>+#4*%s%s]" % (rr._num(radii[i]), rr._signed(-r0))
        zw = "Z[#<_rd_z0>+#1]"
        c = "C[#2%s]" % rr._signed(angles[i])
        f = "F[%s*#3]" % rr._num(1.0 / max(nominal_minutes[i - 1], 1e-7))
        lines.append("  G93 G1 %s %s %s %s" % (x, zw, c, f))
    lines += ["  G94", "o100 endsub", ""]

    # Each pattern starts where the last ended: C on by its net turn;
    # if it ended on the other side of the centre, the next runs with
    # the radii's signs flipped (the same points on the work).
    sign = -1 if info["flipped"] else 1

    def call(k, depth_now, factor):
        c_start = "[#<_rd_c0>%s]" % rr._signed(info["c_turned"] * (k - 1))
        flip = sign ** (k - 1)
        return "o100 call [%s] %s [%s] [%d]" % (rr._num(depth_now), c_start, rr._num(factor), flip)

    if d["depth_mode"] == "passes":
        for k in range(1, count + 1):
            factor = speeds[k - 1] / d["cutting_speed"]
            if k > d["passes"]:
                depth_now = deeper * d["depth_per_pass"] * d["passes"]
                lines.append("(Spring pass %d of %d)" % (k - d["passes"], d["spring_passes"]))
                lines.append(rr._pass_status("spring", k - d["passes"], d["spring_passes"]))
            else:
                depth_now = deeper * d["depth_per_pass"] * k
                finishing = k == d["passes"] and d["finish_pass"]
                lines.append("(%s %d of %d - %s deep)"
                             % ("Finishing pass" if finishing else "Pass", k, d["passes"],
                                rr._num(abs(depth_now))))
                lines.append(rr._pass_status("finish" if finishing else "pass", k, d["passes"]))
                lines.append("G94 G1 Z[#<_rd_z0>%s] F%s" % (rr._signed(depth_now),
                                                            rr._num(d["plunge_feed"])))
            lines.append(call(k, depth_now, factor))
        lines += ["(Back out of the cut)" if advancing else "(Back out to where the cutter started)",
                  "G0 Z[#<_rd_z0>]"]
    else:
        for k in range(1, d["turns"] + 1):
            lines.append("(Time %d of %d)" % (k, d["turns"]))
            lines.append(rr._pass_status("turn", k, d["turns"]))
            lines.append(call(k, 0.0, 1.0))
    if advancing:
        lines.append("(Retract: back out to where the cutter was put)")
        for axis in reversed(advancing):
            lines.append("G0 %s[#<_rd_%s_back>]" % (axis, axis.lower()))
    lines += [
        "",
        "G94",
        "o200 if [#<_rd_diameter> EQ 1]",
        "  G7",
        "o200 endif",
        "M2",
        "",
    ]
    return "\n".join(lines)


def design_from_file(path):
    '''The design saved in a Geometric Chuck Designer program, or None.'''
    found = {}
    try:
        with open(path, errors="replace") as f:
            first = f.readline()
            if not first.startswith(PROGRAM_MARK):
                return None
            for line in f:
                line = line.strip()
                if line.startswith(DESIGN_PREFIX) and line.endswith(")"):
                    key, _, value = line[len(DESIGN_PREFIX):-1].partition(" ")
                    try:
                        found[key] = json.loads(value)
                    except ValueError:
                        pass
    except OSError:
        return None
    return clean_design(found) if found else None


#######################################################################
# Samples (python3 rosetta_geochuck.py <folder>)
#######################################################################

def write_samples(folder):
    os.makedirs(folder, exist_ok=True)
    written = []
    for units in ("inch", "mm"):
        scale = 1.0 if units == "inch" else 25.4
        for n, (name, preset) in enumerate(PRESETS, 1):
            for mode in ("passes", "turns"):
                for direction in (1, -1):
                    d = dict(DEFAULT_DESIGN, **{"r2": 0.0, "k2": "0"})
                    d.update(preset)
                    for key in list(d):
                        if key[0] == "r" and key[1:].isdigit():
                            d[key] = d[key] * scale
                    d.update({"units": units, "depth_mode": mode, "c_direction": direction,
                              "cutting_speed": 2.0 * scale, "depth_per_pass": 0.005 * scale,
                              "plunge_feed": 1.0 * scale, "finish_pass": True, "spring_passes": 1,
                              "turns": 2, "advance_x": 0.1 * scale if n == 2 else 0.0,
                              "advance_z": 0.05 * scale if n == 2 else 0.0})
                    file_name = "preset%d_%s_%s_%s.ngc" % (n, mode, "plus" if direction > 0 else "minus", units)
                    with open(os.path.join(folder, file_name), "w") as f:
                        f.write(gcode(d))
                    written.append(file_name)
        # Some of Bazley's figures (8, 12 and 18 turns to close).
        for figure in (666, 694, 714, 716):
            d = dict(DEFAULT_DESIGN, units=units, cutting_speed=2.0 * scale,
                     depth_per_pass=0.005 * scale, plunge_feed=1.0 * scale)
            d.update(bazley_design(figure, units))
            file_name = "bazley%d_%s.ngc" % (figure, units)
            with open(os.path.join(folder, file_name), "w") as f:
                f.write(gcode(d))
            written.append(file_name)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 rosetta_geochuck.py <folder for sample programs>")
        sys.exit(1)
    print("\n".join(write_samples(sys.argv[1])))
