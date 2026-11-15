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
#   rosetta_rosettes.py
#
# Purpose:
#   The maths of software-defined rosettes, for the Rosette Designer
#   (Rosetta_Rosette_Designer.py), which saves a rosette as a G-code
#   program: C turns the work and X follows the rosette (rocking) or Z
#   does (pumping), as the rubber follows a physical rosette on a rose
#   engine (https://otbok.info/index.php?n=Main.Rosette).
#
#   A shape is one lobe's deflection, f(u) for u = 0..1 across the
#   lobe: 0 = no deflection, 1 = the full amplitude. Deflection moves
#   the cutter in the minus direction of the motion axis (towards the
#   centre when rocking), so a lotus's rounded petals point outward and
#   its sharp points inward. Written from the shapes' geometry - none of
#   Bill Ooms' COrnLathe code (GPL-3) is used.
#
#   The cutter is where the operator put it: the program reads X, Z and
#   C as it starts and every move is relative to them, and the offset
#   is measured from the rosette's value at the starting angle, so the
#   first move has no jump.
#
#   Run on its own it writes sample programs (for testing without the
#   window):  python3 rosetta_rosettes.py <folder>
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
import re
import sys
import time

import numpy

#######################################################################
# Shapes
#######################################################################

# Tudor: each lobe is two small petals; the point between them reaches
# this fraction of the amplitude (the points between lobes reach all of
# it). To be confirmed with Rich, 15 November 2026.
TUDOR_INNER_POINT = 0.35


def _sine(u, lobes):
    # Holtzapffel A: a plain sine wave.
    return 0.5 - 0.5 * numpy.cos(2.0 * math.pi * u)


def _polygon(u, lobes):
    # Holtzapffel P: straight sides between points. The distance in from
    # the points' circle to a straight side, as a fraction of the most
    # (at the side's middle): 0 at the points, 1 mid-side.
    half = math.pi / max(lobes, 3)
    return (1.0 - math.cos(half) / numpy.cos(half * (2.0 * u - 1.0))) / (1.0 - math.cos(half))


def _petal(v):
    # A half circle, 0 at its top (v = 0.5), 1 at its ends - a sharp
    # point where two meet.
    return 1.0 - numpy.sqrt(numpy.clip(1.0 - (2.0 * v - 1.0) ** 2, 0.0, 1.0))


def _lotus(u, lobes):
    # Rounded petals meeting in sharp points.
    return _petal(u)


def _tudor(u, lobes):
    # Two petals per lobe; the point between them is shallower.
    first = u < 0.5
    v = numpy.where(first, 2.0 * u, 2.0 * u - 1.0)
    # 0 at the lobe's ends, 1 at its middle point.
    toward_middle = numpy.where(first, 2.0 * u, 2.0 * (1.0 - u))
    return _petal(v) * (1.0 - (1.0 - TUDOR_INNER_POINT) * toward_middle)


# id -> (name on screen, function)
SHAPES = {
    "sine": ("Sine (Holtzapffel A)", _sine),
    "polygon": ("Plain polygon (Holtzapffel P)", _polygon),
    "lotus": ("Lotus", _lotus),
    "tudor": ("Tudor", _tudor),
}
SHAPE_IDS = ("sine", "polygon", "lotus", "tudor")
SHAPE_SHORT = {"sine": "Sine", "polygon": "Polygon", "lotus": "Lotus", "tudor": "Tudor"}


#######################################################################
# The design
#######################################################################

DEFAULT_DESIGN = {
    "shape": "sine",
    "lobes": 12,
    "amplitude": 0.05,          # peak to peak, machine units
    "phase": 0.0,               # fraction of a lobe, 0..1
    "phase_unit": "lobe",       # how the window shows it: "lobe" or "deg"
    "invert": False,
    "motion": "rock",           # "rock" (X) or "pump" (Z)
    "surface": "face",          # "face" or "side"
    "rubber": "point",          # only a point so far (stage 3: round, flat)
    "c_rpm": 2.0,               # C's speed, rev/min
    "c_direction": 1,           # +1 or -1
    "depth_mode": "passes",     # "passes" (deeper each pass) or "turns" (same depth)
    "passes": 3,
    "depth_per_pass": 0.005,
    "turns": 1,
    "deeper_plus": False,       # depth goes minus (into the work) unless True
    "plunge_feed": 1.0,         # machine units/min
    "preview_radius": 1.0,      # machine units - the drawing only
    "units": "inch",            # "inch" or "mm"
}

# Largest straight-line error allowed between the program's points and
# the true rosette, and the blending tolerance (G64 P), per unit.
CHORD_TOLERANCE = {"inch": 0.0002, "mm": 0.005}
MAX_POINTS_PER_TURN = 7200
# No segment turns C more than this, so C's speed stays even.
MAX_SEGMENT_DEG = 2.0


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
    if d["shape"] not in SHAPES:
        d["shape"] = DEFAULT_DESIGN["shape"]
    d["lobes"] = min(max(d["lobes"], 1), 360)
    d["phase"] = d["phase"] % 1.0
    for key, choices in (("phase_unit", ("lobe", "deg")), ("motion", ("rock", "pump")),
                         ("surface", ("face", "side")), ("rubber", ("point",)),
                         ("depth_mode", ("passes", "turns")), ("units", ("inch", "mm"))):
        if d[key] not in choices:
            d[key] = DEFAULT_DESIGN[key]
    d["c_direction"] = -1 if d["c_direction"] < 0 else 1
    d["passes"] = min(max(d["passes"], 1), 100)
    d["turns"] = min(max(d["turns"], 1), 100)
    return d


def deflection(design, theta_deg):
    '''
    The rosette's deflection (0..1) at spindle angles theta_deg
    (numpy array, degrees from the program's start).
    '''
    lobes = design["lobes"]
    u = numpy.mod(lobes * numpy.asarray(theta_deg, dtype=float) / 360.0 + design["phase"], 1.0)
    f = SHAPES[design["shape"]][1](u, lobes)
    if design["invert"]:
        f = 1.0 - f
    return f


def offset(design, theta_deg):
    '''
    How far the cutter moves along the motion axis at theta_deg, from
    where it was at the start: minus = deflection (towards the centre
    when rocking). 0 at theta 0, and again after each whole turn.
    '''
    start = deflection(design, numpy.array([0.0]))[0]
    return -design["amplitude"] * (deflection(design, theta_deg) - start)


def phase_degrees(design):
    '''The phase as spindle degrees (a whole lobe = 360 / lobes).'''
    return design["phase"] * 360.0 / design["lobes"]


def straight_sides_amplitude(design, radius):
    '''
    The plain polygon amplitude whose sides come out straight when the
    cut starts at this radius. The points are at radius + amplitude x
    the deflection where the cut starts (0 if it starts on a point), and
    a polygon's sides are straight when amplitude = points' radius x
    (1 - cos(180/lobes)).
    '''
    k = 1.0 - math.cos(math.pi / max(design["lobes"], 3))
    start = deflection(dict(design, shape="polygon", invert=False), numpy.array([0.0]))[0]
    return radius * k / (1.0 - k * start)


#######################################################################
# Points for one turn
#######################################################################

# Where each shape has sharp points, as fractions of a lobe - sampled
# exactly, with more samples close by (a lotus's sides are vertical at
# its points, so even sampling would cut the corner).
SHARP_POINTS = {"sine": (), "polygon": (0.0,), "lotus": (0.0,), "tudor": (0.0, 0.5)}


def _sample_angles(design):
    lobes = design["lobes"]
    samples = int(min(max(3600, lobes * 600), 200000))
    theta = [numpy.linspace(0.0, 360.0, samples + 1)]
    lobe_deg = 360.0 / lobes
    near = numpy.geomspace(1e-7, 0.05, 60) * lobe_deg
    for u in SHARP_POINTS[design["shape"]]:
        # The invert of a sharp point is still sharp.
        centres = (numpy.arange(lobes) + u - design["phase"]) * lobe_deg
        centres = numpy.mod(centres, 360.0)
        centres = numpy.concatenate([centres, centres + 360.0])   # a point at 0 is also at 360
        theta.append(centres)
        theta.append((centres[:, None] + near[None, :]).ravel())
        theta.append((centres[:, None] - near[None, :]).ravel())
    theta = numpy.concatenate(theta)
    theta = numpy.unique(numpy.clip(theta, 0.0, 360.0))
    return theta


def turn_points(design):
    '''
    (angles, offsets, capped) for one turn, 0..360 degrees: the fewest
    points whose straight lines stay within CHORD_TOLERANCE of the
    rosette (no step over MAX_SEGMENT_DEG). capped is True when that
    needed more than MAX_POINTS_PER_TURN, so fewer were kept and the cut
    is less exact (very many sharp lobes).
    '''
    tol = CHORD_TOLERANCE[design["units"]]
    theta = _sample_angles(design)
    y = offset(design, theta)
    last = len(theta) - 1

    def fits(i, j):
        if j - i <= 1:
            return True
        line = y[i] + (y[j] - y[i]) * (theta[i:j + 1] - theta[i]) / (theta[j] - theta[i])
        return numpy.max(numpy.abs(y[i:j + 1] - line)) <= tol

    keep = [0]
    i = 0
    while i < last:
        # The furthest sample within MAX_SEGMENT_DEG, then the furthest
        # of those whose line fits: grow the step while it fits, then
        # narrow it down.
        limit = int(numpy.searchsorted(theta, theta[i] + MAX_SEGMENT_DEG, side="right")) - 1
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
    angles, offsets = theta[keep], y[keep]
    capped = len(angles) - 1 > MAX_POINTS_PER_TURN
    if capped:
        pick = numpy.unique(numpy.round(numpy.linspace(0, len(angles) - 1,
                                                       MAX_POINTS_PER_TURN + 1)).astype(int))
        angles, offsets = angles[pick], offsets[pick]
    offsets[-1] = 0.0       # exactly back where it started
    return angles, offsets, capped


def turn_seconds(design):
    return 60.0 / max(design["c_rpm"], 1e-9)


def turn_time(design, motion_max_speed=None, c_max_speed=None, points=None):
    '''
    (seconds, nominal seconds) for one turn: nominal at C's set speed;
    seconds allowing for the motion axis's and C's Max Speed (units/sec,
    deg/sec) - where the rosette is steeper than the motion axis can
    follow, LinuxCNC slows that move, and C with it (a sharp point
    always does this). Acceleration isn't counted, so it's a little
    short where the rosette changes direction sharply.
    '''
    angles, offsets, _ = points or turn_points(design)
    nominal = numpy.diff(angles) / 360.0 * turn_seconds(design)
    needed = nominal.copy()
    if motion_max_speed:
        needed = numpy.maximum(needed, numpy.abs(numpy.diff(offsets)) / motion_max_speed)
    if c_max_speed:
        needed = numpy.maximum(needed, numpy.diff(angles) / c_max_speed)
    return float(needed.sum()), float(nominal.sum())


#######################################################################
# G-code
#######################################################################

# The design is kept in the program, one setting per comment line -
# (DESIGN shape "lotus") - so the Rosette Designer can open it again.
# One line per setting: LinuxCNC refuses a line over 255 characters.
DESIGN_PREFIX = "(DESIGN "

# The gcode folder can't hold a file starting with "rosetta" (any case)
# or named M100-M199 - LinuxCNC would run it in place of Rosetta's own
# (see CLAUDE.md, "Reserved names"; the same rule as
# Rosetta_Generate_Local_Ini.py's reserved-name check).
RESERVED_NAME = re.compile(r"^(rosetta|m1\d\d(\.|$))", re.IGNORECASE)


def name_is_reserved(file_name):
    return bool(RESERVED_NAME.match(os.path.basename(file_name)))


def default_file_name(design):
    return "%s%d_%s_%s.ngc" % (SHAPE_SHORT[design["shape"]], design["lobes"],
                               design["motion"], design["surface"])


def describe(design):
    d = design
    return "%s %d, %s, %s" % (SHAPE_SHORT[d["shape"]], d["lobes"],
                              "rocking" if d["motion"] == "rock" else "pumping",
                              "face" if d["surface"] == "face" else "side")


def depth_axis(design):
    return "Z" if design["surface"] == "face" else "X"


def motion_axis(design):
    return "X" if design["motion"] == "rock" else "Z"


def _num(value):
    '''A plain decimal for G-code, at most 6 places, no "-0".'''
    text = ("%.6f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _signed(value):
    '''"+0.0123" or "-0.0123", to add to a parameter: never a bare
    number, which would be read as part of the parameter.'''
    text = _num(abs(value))
    return ("-" if value < 0 and text != "0" else "+") + text


def gcode(design):
    '''The whole program, as text.'''
    d = clean_design(design)
    angles, offsets, _ = turn_points(d)
    tol = CHORD_TOLERANCE[d["units"]]
    motion, depth = motion_axis(d), depth_axis(d)
    deeper = 1.0 if d["deeper_plus"] else -1.0
    turn_minutes = 1.0 / d["c_rpm"]

    lines = [
        "(Rosette Designer - %s - %s)" % (describe(d), time.strftime("%d %B %Y")),
        "(Runs from where the cutter is: put it where the pattern should be cut,)",
        "(then run. C turns %d time%s. Made by Rosetta's Rosette Designer -)"
        % (d["passes"] if d["depth_mode"] == "passes" else d["turns"],
           "" if (d["passes"] if d["depth_mode"] == "passes" else d["turns"]) == 1 else "s"),
        "(open it there to change it.)",
    ] + [DESIGN_PREFIX + "%s %s)" % (key, json.dumps(d[key])) for key in sorted(d)] + [
        "",
        "#<_rd_diameter> = #<_lathe_diameter_mode>",
        "%s G8 G90 G64 P%s" % ("G20" if d["units"] == "inch" else "G21", _num(tol)),
        "#<_rd_x0> = #5420",
        "#<_rd_z0> = #5422",
        "#<_rd_c0> = #5425",
        "",
        "(One turn of the rosette. #1 = depth from the start, #2 = C at the start)",
        "o100 sub",
    ]
    for i in range(1, len(angles)):
        words = []
        for axis in ("X", "Z"):
            if axis not in (motion, depth):
                continue
            expr = "#<_rd_%s0>" % axis.lower()
            if axis == depth:
                expr += "+#1"
            if axis == motion:
                expr += _signed(offsets[i])
            words.append("%s[%s]" % (axis, expr))
        c = d["c_direction"] * angles[i]
        words.append("C[#2%s]" % _signed(c))
        minutes = (angles[i] - angles[i - 1]) / 360.0 * turn_minutes
        words.append("F%s" % _num(1.0 / minutes))
        lines.append("  G93 G1 " + " ".join(words))
    lines += ["  G94", "o100 endsub", ""]

    depth_var = "#<_rd_%s0>" % depth.lower()
    if d["depth_mode"] == "passes":
        for k in range(1, d["passes"] + 1):
            depth_now = deeper * d["depth_per_pass"] * k
            lines.append("(Pass %d of %d - %s deep)" % (k, d["passes"], _num(abs(depth_now))))
            lines.append("G94 G1 %s[%s%s] F%s" % (depth, depth_var, _signed(depth_now),
                                                 _num(d["plunge_feed"])))
            lines.append("o100 call [%s] [#<_rd_c0>%s]" % (_num(depth_now),
                                                          _signed(d["c_direction"] * 360.0 * (k - 1))))
        lines += ["(Back out to where the cutter started)",
                  "G0 %s[%s]" % (depth, depth_var)]
    else:
        for k in range(1, d["turns"] + 1):
            lines.append("(Turn %d of %d)" % (k, d["turns"]))
            lines.append("o100 call [0] [#<_rd_c0>%s]" % _signed(d["c_direction"] * 360.0 * (k - 1)))
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
    '''The design saved in a Rosette Designer program, or None.'''
    found = {}
    try:
        with open(path, errors="replace") as f:
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
# Samples (python3 rosetta_rosettes.py <folder>)
#######################################################################

def write_samples(folder):
    os.makedirs(folder, exist_ok=True)
    written = []
    for units in ("inch", "mm"):
        scale = 1.0 if units == "inch" else 25.4
        for shape in SHAPE_IDS:
            for motion in ("rock", "pump"):
                for surface in ("face", "side"):
                    for mode in ("passes", "turns"):
                        d = clean_design({
                            "shape": shape, "lobes": 8 if shape != "sine" else 12,
                            "amplitude": 0.05 * scale, "depth_per_pass": 0.005 * scale,
                            "plunge_feed": 1.0 * scale, "preview_radius": 1.0 * scale,
                            "motion": motion, "surface": surface, "depth_mode": mode,
                            "turns": 2, "units": units, "phase": 0.25,
                        })
                        name = "%s_%s_%s_%s_%s.ngc" % (shape, motion, surface, mode, units)
                        with open(os.path.join(folder, name), "w") as f:
                            f.write(gcode(d))
                        written.append(name)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 rosetta_rosettes.py <folder for sample programs>")
        sys.exit(1)
    print("\n".join(write_samples(sys.argv[1])))
