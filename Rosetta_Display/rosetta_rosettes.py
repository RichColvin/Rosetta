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
#   program: C turns the work and X follows the rosette (rocking), Z
#   does (pumping), or each follows a rosette of its own (both), as the
#   rubbers follow physical rosettes on a rose engine
#   (https://otbok.info/index.php?n=Main.Rosette).
#
#   A shape is one repeat's deflection, profile(t) for t = 0..1 across
#   the repeat (a lobe, or a group of lobes for some Holtzapffel
#   letters): 0 = no deflection, 1 = the full amplitude. Deflection
#   moves the cutter in the minus direction of the motion axis (towards
#   the centre when rocking), so a polygon's points point outward.
#
#   Clean room (16 November 2026 - see docs/Rosetta_Tracker.md,
#   "Provenance"): the shapes and the deflection maths were rewritten
#   that day from plain geometry, the Holtzapffel & Co. guide's
#   drawings and the MDF Rose Engine's paper-chuck pictures
#   (https://www.colvintools.com/MDF-RE%20-%20Rosettes.html), each
#   source given with its shape. No other rosette software is used or
#   consulted.
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
#   1.1 - 15 November 2026 - rocking and pumping together (motion
#         "both": a rosette for X and one for Z)
#   1.2 - 15 November 2026 - the drawing's radius is the outside or
#         the inside of the cut (radius_at, start_radius)
#   1.3 - 15 November 2026 - no phase for the first rosette (always 0):
#         the operator phases the work by indexing on the Rosetta panel
#   1.4 - 15 November 2026 - finishing pass (chosen; at a percentage of
#         C's speed, 10% to start) and spring passes, in "passes" mode; the one-turn sub takes a
#         speed factor (#3); each pass is reported on M67 E0 for the
#         panel's progress bar ("pass 2 of 3", as Threading counts)
#   1.5 - 15 November 2026 - Lotus and Tudor redrawn from the MDF Rose
#         Engine's paper-chuck pictures (Rich); sharp_points;
#         suggested file names start "Rosette-"
#   1.6 - 16 November 2026 - shapes rewritten clean room; Holtzapffel
#         C, D, F, J, K, M, N, O, P, Q and S added from the guide's
#         drawings; lobes counted as the guide numbers them, so a
#         shape made of groups (J, M, N, O, P, Q) repeats lobes / its
#         group size times (count_per_repeat, fit_lobes, repeats);
#         phase is a fraction of a repeat; "Plain polygon" is no longer
#         called Holtzapffel P (the guide's P is groups of waves)
#   1.7 - 16 November 2026 - from the paper chuck: _scaled stretches
#         over the whole repeat, not the angles asked for (F, J, N, O,
#         P, Q and S jumped the whole amplitude on the first move);
#         Holtzapffel F turned over
#   1.8 - 16 November 2026 - advance and retract: the cutter can start
#         clear of the work, move in on X and/or Z (advance_x/_z and
#         their directions) before cutting and back out at the end
#   1.9 - 16 November 2026 - shorter shape names (no group sizes -
#         Lobes steps by a group), so the Shape lists are narrower
#   1.10 - 16 November 2026 - F with 1 lobe is the F-1 heart (_f1_heart,
#         from the MDF Rose Engine's F-1), not one Cupid's bow
#   1.11 - 16 November 2026 - F-1 traced from the MDF Rose Engine's
#         near-side cut (HOLTZ_F1_PROFILE) - the formula's point was
#         too blunt on the paper chuck
#   1.12 - 16 November 2026 - F-1's cleft deepened (HOLTZ_F1_CLEFT), so
#         the upper lobes stand out more (Rich)
#   1.13 - 16 November 2026 - Ellipse: a width / length ratio ("ratio",
#         "pump_ratio"), always 2 lobes; ellipse_amplitude makes the cut
#         an exact ellipse at a radius, ellipse_axes gives its size and
#         foci
#   1.14 - 17 November 2026 - Ellipse set by its half-length a and
#         half-width b (Rich, from his Desmos graph), always an exact
#         ellipse with the cutter started at radius a; any shape can
#         ride on an ellipse ("on_ellipse"), its lobes spaced evenly
#         along the ellipse's outline (Rich). "ratio"/"pump_ratio" and
#         ellipse_amplitude are gone; the Ellipse is for rocking only
#   1.15 - 17 November 2026 - the rosette on an ellipse is a second
#         rocking rosette of its own ("wrap_" keys, with a phase along
#         the outline; "none" = the plain ellipse), in place of
#         on_ellipse (Rich: two columns)
#   1.16 - 17 November 2026 - start_radius on an ellipse allows for
#         the waves' depth at the start, so they're cut in from the
#         ellipse (they went out past it - Rich's paper chuck)
#   1.17 - 17 November 2026 - check_circle_gcode: a program that turns
#         C once to draw a circle round the axis, for setting the start
#         radius (Rich - used by both Designers)
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
#
# Rewritten 16 November 2026 (clean room - see docs/Rosetta_Tracker.md,
# "Provenance"): every shape below is worked out here from plain
# geometry or measured off a cited picture, and the source is given
# with each one.
#
# How a shape is described. A rosette's pattern repeats round the turn;
# one repeat is described by profile(t) for t = 0..1 across it, giving
# how far in the rubber is pushed at that point as a fraction of the
# amplitude: 0 = not at all (the cutter at its outermost), 1 = the most.
# The rosette's "lobes" are counted the way the Holtzapffel guide numbers
# its rosettes (P18 = 18, the small waves you count round the edge), so
# a shape whose repeat carries several of them says so in COUNT_PER_REPEAT
# and the number of repeats in a turn is lobes / that. Most shapes have
# one per repeat.
#
# The Holtzapffel letters are from "Patterns of Rosettes for the
# Holtzapffel Rose Cutting Frame" (Holtzapffel & Co., about the 1880s),
# pages 5-14 of Rich's scan: each letter's pattern drawn at several
# counts, cut on a flat face, so the outer rings show the profile
# itself. They are first versions read off those drawings, to be checked
# on a paper chuck.


def _cosine(t):
    # One smooth wave: 0 at t = 0 and 1, the most (1) at t = 0.5.
    return 0.5 - 0.5 * numpy.cos(2.0 * math.pi * t)


def _chord(t, sides):
    # A straight side of a regular polygon, corners at t = 0 and 1 on a
    # circle of radius 1. The side lies cos(h) from the centre (h = half
    # the angle a side takes up); along a ray x from the side's middle it
    # is cos(h) / cos(x) out, so it is 1 - cos(h) / cos(x) in from the
    # circle - the most, 1 - cos(h), at the middle.
    h = math.pi / max(sides, 3)
    x = (2.0 * t - 1.0) * h
    return (1.0 - math.cos(h) / numpy.cos(x)) / (1.0 - math.cos(h))


def _arc(t, sag):
    # A round-topped lobe: a circular arc from one sharp inward cusp
    # (t = 0) to the next (t = 1). Measured across the chord between the
    # cusps (half length 1), the arc rises sag at its middle; a circle
    # through both cusps and that top has radius (1 + sag^2) / (2 sag).
    # 0 at the arc's top, 1 at the cusps. sag 1 = a half circle.
    x = 2.0 * t - 1.0
    radius = (1.0 + sag * sag) / (2.0 * sag)
    height = numpy.sqrt(numpy.maximum(radius * radius - x * x, 0.0)) - (radius - sag)
    return 1.0 - height / sag


def _notch(t, half_width):
    # A narrow V, 1 at t = 0 (and 1), falling straight to 0 half_width away.
    d = numpy.minimum(t, 1.0 - t)
    return numpy.clip(1.0 - d / half_width, 0.0, 1.0)


# One repeat finely divided (7200 steps divides by every group size and
# count used here, so the cusps and notches fall on it exactly).
_SCALE_GRID = numpy.linspace(0.0, 1.0, 7201)


def _scaled(raw, t):
    # Stretch a profile to run exactly 0..1, from its lowest and highest
    # over the whole repeat - never from the t asked for, which may be a
    # single point (offset's start): stretched alone, that always gave 0,
    # so a shape starting at a cusp jumped the whole amplitude on its
    # first move (found on the paper chuck, 16 November 2026).
    grid = raw(_SCALE_GRID)
    low, high = numpy.min(grid), numpy.max(grid)
    return numpy.clip((raw(t) - low) / max(high - low, 1e-12), 0.0, 1.0)


# Lotus (MDF Rose Engine Lotus-8's paper chuck, colvintools.com,
# 15 November 2026): a polygon's straight sides from point to point,
# with a narrow V notch in the middle of each - where the rubber can't
# follow the lotus rosette's pointed trough. Notch depth (of the
# amplitude) and half width (of a lobe), measured off the picture.
LOTUS_NOTCH_DEPTH = 0.25
LOTUS_NOTCH_HALF_WIDTH = 0.08

# Tudor (Tudor-5 and Tudor-8's paper chucks, the same page): a rounded
# petal per lobe - a polygon turned over - and at each join between
# petals a small sharp barb pointing outward (the Tudor rose's sepals).
# Barb height (of the amplitude) and half width (of a lobe), measured
# off the pictures.
TUDOR_BARB_HEIGHT = 0.6
TUDOR_BARB_HALF_WIDTH = 0.04

# Holtzapffel D (guide pages 7-8, D6-D36): round petals meeting in sharp
# inward cusps. How full each petal is (the arc's sag, _arc), read off
# D6 and D8. C (pages 6-7) is D turned over: sharp points outward,
# hollow sides.
HOLTZ_D_SAG = 0.5

# Holtzapffel F (page 9, F3-F8): groups of three smooth waves, the
# middle one with a small V notch at its top - a Cupid's bow (F3's
# centre is a 9-point star, F4's 12). The guide numbers F by its
# groups (F3 = 3). The notch's depth (of the amplitude) and half width
# (of a group), read off F3 and F4.
HOLTZ_F_WAVES = 3
HOLTZ_F_NOTCH_DEPTH = 0.35
HOLTZ_F_NOTCH_HALF_WIDTH = 0.05

# F-1 (F with 1 lobe) is a single heart, not one Cupid's bow - the MDF
# Rose Engine's F-1 rosette (colvintools.com, MDF-RE-Rosette-F-1). The
# first version (16 November 2026) was a formula and Rich's paper chuck
# showed its point too blunt: a heart's point is sharp only because its
# sides fall away steeply right beside it. So the profile is traced
# from the near-side cut pictured on that page: the heart's edge, from
# the centre of its rings, every 2.5 degrees from the notch (0) round
# the right-hand side (the left shows the piece's side) to the point
# (180), as deflection 0..1 - the last 20 degrees each end straight
# lines fitted to the sides, so the notch and point are sharp (the photo
# rounds them a little). The cut there has amplitude about 0.47 of its
# outside radius; other ratios give fatter or thinner hearts, as a
# physical rosette does at different radii (Rich, 16 November 2026).
HOLTZ_F1_PROFILE = (
    1.0, 0.973, 0.942, 0.904, 0.862, 0.816, 0.761, 0.702, 0.64, 0.577,
    0.512, 0.447, 0.387, 0.332, 0.283, 0.238, 0.201, 0.173, 0.153, 0.14,
    0.132, 0.126, 0.121, 0.119, 0.117, 0.117, 0.118, 0.12, 0.124, 0.128,
    0.133, 0.14, 0.153, 0.173, 0.199, 0.228, 0.259, 0.291, 0.324, 0.355,
    0.385, 0.413, 0.439, 0.464, 0.486, 0.507, 0.526, 0.543, 0.557, 0.568,
    0.578, 0.584, 0.589, 0.591, 0.591, 0.589, 0.584, 0.577, 0.567, 0.555,
    0.541, 0.523, 0.502, 0.475, 0.445, 0.413, 0.374, 0.329, 0.278, 0.221,
    0.157, 0.083, 0.0)
# The cleft at the top deepened beyond the traced cut, to make more of
# the two upper lobes (Rich, 16 November 2026, from the Designer's
# drawing): an extra V, this much of the traced depth, fading out
# this many degrees each side of the cleft.
HOLTZ_F1_CLEFT = 0.5
HOLTZ_F1_CLEFT_HALF_DEG = 40.0

# Holtzapffel J (pages 11-12, J24-J36; Rich, 15 November 2026: "arcs of
# eccentric circles with each arch having on it a superimposed arc of
# sine waves"): shallow round arcs, 6 small waves on each - J24 has 4
# arcs, J30 5, J36 6.
HOLTZ_J_PER_ARC = 6
HOLTZ_J_ARC_SAG = 0.5
HOLTZ_J_WAVES = 0.2         # the small waves' share of the amplitude

# Holtzapffel K (page 11, K3 K4 K6): a polygon of that many sides with
# round waves along each side - an odd number, so the middle of each
# side is a dip, which K3 shows as a Cupid's-bow notch (about 5 a side).
HOLTZ_K_WAVES_PER_SIDE = 5
HOLTZ_K_WAVES = 0.35

# Holtzapffel M (page 12, M24): three long, deep round lobes, each
# carrying 8 small round scallops.
HOLTZ_M_PER_LOBE = 8
HOLTZ_M_LOBE_SAG = 0.7
HOLTZ_M_SCALLOP_SAG = 0.6
HOLTZ_M_SCALLOPS = 0.15

# Holtzapffel N (page 12, N15 N20): broad round lobes of 5 round
# scallops each - N15 has 3 lobes, N20 4.
HOLTZ_N_PER_LOBE = 5
HOLTZ_N_LOBE_SAG = 0.4
HOLTZ_N_SCALLOP_SAG = 0.6
HOLTZ_N_SCALLOPS = 0.35

# Holtzapffel O and P (page 13, O12-O24, P12-P36): broad round arcs
# of 6 waves each, the waves largest mid-arc - O12 and P12 show 2 arcs
# (their centres a bar), P18 3, P24 4. P's waves are smooth (sine),
# O's are round scallops with sharp cusps. HOLTZ_OP_SWELL is how much
# smaller the smallest wave of an arc is than the largest (a fraction).
HOLTZ_OP_PER_GROUP = 6
HOLTZ_OP_ARC_SAG = 0.5
HOLTZ_O_WAVES = 0.3         # the waves' share of the amplitude
HOLTZ_P_WAVES = 0.2
HOLTZ_OP_SWELL = 0.6
HOLTZ_O_SCALLOP_SAG = 0.6

# Holtzapffel Q (page 14, Q16-Q32): shallow round arcs, each carrying
# 4 round scallops - Q16 has 4 arcs.
HOLTZ_Q_PER_ARC = 4
HOLTZ_Q_ARC_SAG = 0.35
HOLTZ_Q_SCALLOP_SAG = 0.6
HOLTZ_Q_SCALLOPS = 0.2

# Holtzapffel S (page 14, S32): one heart round the turn - a V notch at
# its top, two round shoulders, a point at the bottom - carrying the
# count of small round scallops. Where the shoulders are (fraction of a
# turn from the notch), how far in the point is, and the scallops' share.
HOLTZ_S_SHOULDER = 0.17
HOLTZ_S_POINT = 0.4
HOLTZ_S_SCALLOP_SAG = 0.6
HOLTZ_S_SCALLOPS = 0.15


def _sine(t, repeats, count):
    # Holtzapffel A (page 5, A8-A36): one plain smooth wave per lobe.
    return _cosine(t)


def _polygon(t, repeats, count):
    # A plain polygon: straight sides between points. (What a puffy-
    # sided rosette cuts on work much smaller than itself - de la
    # Condamine's point, guide pages 20-21 - so it is useful on its own.)
    return _chord(t, repeats)


def _lotus(t, repeats, count):
    notch = _notch((t + 0.5) % 1.0, LOTUS_NOTCH_HALF_WIDTH)     # mid-lobe
    return (1.0 - LOTUS_NOTCH_DEPTH) * _chord(t, repeats) + LOTUS_NOTCH_DEPTH * notch


def _tudor_barb(t):
    return TUDOR_BARB_HEIGHT * _notch(t, TUDOR_BARB_HALF_WIDTH)


def _tudor_barb_meets_petal(repeats):
    '''How far from the lobe's end (a fraction of a lobe) the barb's
    side meets the petal - a sharp notch.'''
    low, high = 0.0, TUDOR_BARB_HALF_WIDTH
    for _ in range(60):
        mid = 0.5 * (low + high)
        if _tudor_barb(numpy.array([mid]))[0] > _chord(numpy.array([mid]), repeats)[0]:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


# Ellipse (16 November 2026; set by a and b since 17 November 2026 -
# Rich, from his Desmos graph of x^2/a^2 + y^2/b^2 = 1): the geometry of
# an ellipse, r = a b / sqrt((b cos)^2 + (a sin)^2) at spindle angle
# theta, a = half its length (along the start, theta 0), b = half its
# width. Rocking only: X follows r exactly, so with the cutter started
# at radius a the cut is that ellipse, at any size. A second rocking
# rosette rides on it ("wrap_" keys - two rosettes both rocking, Rich,
# 17 November 2026; "none" leaves the plain ellipse): its waves added to
# r (towards the centre), its lobes spaced evenly along the ellipse's
# outline rather than by spindle angle (Rich) - on a long ellipse, even
# angles would crowd them along the sides - and its phase sliding the
# pattern along the outline (half a lobe moves a cleft off the end).
_OUTLINE_GRID = numpy.linspace(0.0, 360.0, 7201)


def ellipse_radius(base, theta_deg):
    '''The ellipse base = (a, b)'s distance from its centre at spindle
    angles theta_deg (degrees from the end of a).'''
    a, b = base
    theta = numpy.radians(numpy.asarray(theta_deg, dtype=float))
    return a * b / numpy.sqrt((b * numpy.cos(theta)) ** 2 + (a * numpy.sin(theta)) ** 2)


_outline_tables = {}


def _outline_table(base):
    # The fraction of the outline's length from theta 0 to each angle of
    # _OUTLINE_GRID (straight pieces 0.05 degrees long - far closer than
    # the chord tolerance).
    table = _outline_tables.get(base)
    if table is None:
        r = ellipse_radius(base, _OUTLINE_GRID)
        angles = numpy.radians(_OUTLINE_GRID)
        x, y = r * numpy.cos(angles), r * numpy.sin(angles)
        length = numpy.concatenate(([0.0], numpy.cumsum(numpy.hypot(numpy.diff(x), numpy.diff(y)))))
        table = length / length[-1]
        if len(_outline_tables) > 50:
            _outline_tables.clear()
        _outline_tables[base] = table
    return table


def outline_fraction(base, theta_deg):
    '''How far round the ellipse's outline (turns, 1 = the whole
    outline) the cutter is at spindle angles theta_deg.'''
    theta = numpy.asarray(theta_deg, dtype=float)
    turns = numpy.floor(theta / 360.0)
    return turns + numpy.interp(theta - 360.0 * turns, _OUTLINE_GRID, _outline_table(base))


def outline_angle(base, fraction):
    '''The spindle angle (degrees) that far round the outline - the
    reverse of outline_fraction.'''
    fraction = numpy.asarray(fraction, dtype=float)
    turns = numpy.floor(fraction)
    return 360.0 * turns + numpy.interp(fraction - turns, _outline_table(base), _OUTLINE_GRID)


def ellipse_axes(base):
    '''(length, width, distance between the foci) of the ellipse.'''
    a, b = base
    return 2.0 * a, 2.0 * b, 2.0 * math.sqrt(abs(a * a - b * b))


def _tudor(t, repeats, count):
    # A petal (highest mid-lobe) with the barb at the lobe's ends,
    # scaled so the notches beside the barb - its deepest points - are
    # the full amplitude.
    height = 1.0 - numpy.maximum(_chord(t, repeats), _tudor_barb(t))
    meet = numpy.array([_tudor_barb_meets_petal(repeats)])
    return height / (1.0 - _tudor_barb(meet)[0])


def _holtz_d(t, repeats, count):
    return _arc(t, HOLTZ_D_SAG)


def _holtz_c(t, repeats, count):
    return 1.0 - _arc(t, HOLTZ_D_SAG)


def _f1_heart(t):
    # The traced profile, the same both sides of the notch-point line,
    # with the cleft at the top deepened by a V (HOLTZ_F1_CLEFT of the
    # traced depth, HOLTZ_F1_CLEFT_HALF_DEG wide each side) - the rest
    # keeps its shape, scaled to make room.
    s = numpy.minimum(t, 1.0 - t) * 360.0
    table = numpy.asarray(HOLTZ_F1_PROFILE)
    traced = numpy.interp(s, numpy.linspace(0.0, 180.0, len(table)), table)
    # squared, so it fades out level into the lobes (no corner there)
    cleft = numpy.clip(1.0 - s / HOLTZ_F1_CLEFT_HALF_DEG, 0.0, 1.0) ** 2
    return (traced + HOLTZ_F1_CLEFT * cleft) / (1.0 + HOLTZ_F1_CLEFT)


def _holtz_f(t, repeats, count):
    if repeats == 1:
        return _f1_heart(t)
    # Wave tops at 1/6, 1/2 and 5/6 of the group; the notch at 1/2.
    # Turned over (1 - ...) since the paper chuck, 16 November 2026: Rich
    # had to tick Invert to get the guide's shape.
    def raw(t):
        waves = _cosine((t * HOLTZ_F_WAVES + 0.5) % 1.0)
        return ((1.0 - HOLTZ_F_NOTCH_DEPTH) * waves
                + HOLTZ_F_NOTCH_DEPTH * _notch((t + 0.5) % 1.0, HOLTZ_F_NOTCH_HALF_WIDTH))
    return 1.0 - _scaled(raw, t)


def _on_arcs(t, arc_sag, small, per_arc, share):
    # Small waves riding on round arcs: the arc's own profile plus the
    # small waves, each its share of the amplitude.
    return _scaled(lambda t: (1.0 - share) * _arc(t, arc_sag)
                   + share * small((t * per_arc) % 1.0), t)


def _holtz_j(t, repeats, count):
    return _on_arcs(t, HOLTZ_J_ARC_SAG, _cosine, HOLTZ_J_PER_ARC, HOLTZ_J_WAVES)


def _holtz_k(t, repeats, count):
    return _scaled(lambda t: (1.0 - HOLTZ_K_WAVES) * _chord(t, repeats)
                   + HOLTZ_K_WAVES * _cosine((t * HOLTZ_K_WAVES_PER_SIDE) % 1.0), t)


def _holtz_m(t, repeats, count):
    return _on_arcs(t, HOLTZ_M_LOBE_SAG, lambda s: _arc(s, HOLTZ_M_SCALLOP_SAG),
                    HOLTZ_M_PER_LOBE, HOLTZ_M_SCALLOPS)


def _holtz_n(t, repeats, count):
    return _on_arcs(t, HOLTZ_N_LOBE_SAG, lambda s: _arc(s, HOLTZ_N_SCALLOP_SAG),
                    HOLTZ_N_PER_LOBE, HOLTZ_N_SCALLOPS)


def _swelling(t, small, share):
    # Waves on an arc, largest mid-arc, smallest at its ends.
    def raw(t):
        size = 1.0 - HOLTZ_OP_SWELL * _cosine((t + 0.5) % 1.0)
        return ((1.0 - share) * _arc(t, HOLTZ_OP_ARC_SAG)
                + share * size * small((t * HOLTZ_OP_PER_GROUP) % 1.0))
    return _scaled(raw, t)


def _holtz_o(t, repeats, count):
    return _swelling(t, lambda s: _arc(s, HOLTZ_O_SCALLOP_SAG), HOLTZ_O_WAVES)


def _holtz_p(t, repeats, count):
    return _swelling(t, _cosine, HOLTZ_P_WAVES)


def _holtz_q(t, repeats, count):
    return _on_arcs(t, HOLTZ_Q_ARC_SAG, lambda s: _arc(s, HOLTZ_Q_SCALLOP_SAG),
                    HOLTZ_Q_PER_ARC, HOLTZ_Q_SCALLOPS)


def _heart(t):
    # One heart round the turn, t = 0 at the notch: down the notch's
    # straight sides to round shoulders (a quarter sine, level at the
    # shoulder), then curving in to the point at t = 0.5, which is sharp
    # because both sides arrive at it sloping.
    s = numpy.minimum(t, 1.0 - t)
    k = HOLTZ_S_SHOULDER
    notch = 1.0 - numpy.sin(0.5 * math.pi * numpy.minimum(s, k) / k)
    lower = HOLTZ_S_POINT * ((numpy.maximum(s, k) - k) / (0.5 - k)) ** 2
    return numpy.where(s < k, notch, lower)


def _holtz_s(t, repeats, count):
    return _scaled(lambda t: (1.0 - HOLTZ_S_SCALLOPS) * _heart(t)
                   + HOLTZ_S_SCALLOPS * _arc((t * count) % 1.0, HOLTZ_S_SCALLOP_SAG), t)


# id -> (name on screen, short name for file names, function,
#        count per repeat (0 = the whole turn is one repeat))
SHAPES = {
    "sine": ("Holtzapffel A - sine", "HoltzA", _sine, 1),
    "holtz_c": ("Holtzapffel C - points, hollow sides", "HoltzC", _holtz_c, 1),
    "holtz_d": ("Holtzapffel D - round petals", "HoltzD", _holtz_d, 1),
    "holtz_f": ("Holtzapffel F - Cupid's bow", "HoltzF", _holtz_f, 1),
    "holtz_j": ("Holtzapffel J - waves on arcs", "HoltzJ", _holtz_j, HOLTZ_J_PER_ARC),
    "holtz_k": ("Holtzapffel K - waved polygon", "HoltzK", _holtz_k, 1),
    "holtz_m": ("Holtzapffel M - scallops on long lobes", "HoltzM", _holtz_m, HOLTZ_M_PER_LOBE),
    "holtz_n": ("Holtzapffel N - scallops on lobes", "HoltzN", _holtz_n, HOLTZ_N_PER_LOBE),
    "holtz_o": ("Holtzapffel O - swelling scallops", "HoltzO", _holtz_o, HOLTZ_OP_PER_GROUP),
    "holtz_p": ("Holtzapffel P - swelling waves", "HoltzP", _holtz_p, HOLTZ_OP_PER_GROUP),
    "holtz_q": ("Holtzapffel Q - scallops on arcs", "HoltzQ", _holtz_q, HOLTZ_Q_PER_ARC),
    # The rosette on an ellipse only: no waves - the plain ellipse.
    "none": ("None - the plain ellipse", "", None, 1),
    "holtz_s": ("Holtzapffel S - heart", "HoltzS", _holtz_s, 0),
    "polygon": ("Plain polygon", "Polygon", _polygon, 1),
    "lotus": ("Lotus", "Lotus", _lotus, 1),
    "tudor": ("Tudor", "Tudor", _tudor, 1),
    # The plain ellipse: no waves of its own (profile() gives 0) - the
    # ellipse itself is added in offset(). Always 2 lobes (fit_lobes).
    "ellipse": ("Ellipse", "Ellipse", None, 1),
}
SHAPE_IDS = tuple(SHAPES)
SHAPE_SHORT = {key: value[1] for key, value in SHAPES.items()}


def count_per_repeat(shape, lobes):
    '''How many of the rosette's counted lobes one repeat holds.'''
    per = SHAPES[shape][3]
    return lobes if per == 0 else per


def fit_lobes(shape, lobes):
    '''The nearest allowed lobe count: a whole number of repeats.'''
    if shape == "ellipse":
        return 2            # an ellipse is two lobes, its two ends
    per = count_per_repeat(shape, lobes)
    return max(per, int(round(lobes / float(per))) * per)


def repeats(ros):
    '''How many times the shape's repeat goes round in one turn.'''
    return max(ros["lobes"] // count_per_repeat(ros["shape"], ros["lobes"]), 1)


def profile(ros, t):
    '''The shape over one repeat, t = 0..1 (numpy array), 0..1.'''
    if ros["shape"] in ("ellipse", "none"):
        return numpy.zeros_like(numpy.asarray(t, dtype=float))
    return SHAPES[ros["shape"]][2](numpy.asarray(t, dtype=float), repeats(ros), ros["lobes"])


def sharp_points(ros):
    '''Where a shape has sharp points, as fractions of a repeat.'''
    shape, n = ros["shape"], repeats(ros)
    if shape == "polygon":
        return (0.0,)
    if shape == "lotus":
        return (0.0, 0.5 - LOTUS_NOTCH_HALF_WIDTH, 0.5, 0.5 + LOTUS_NOTCH_HALF_WIDTH)
    if shape == "tudor":
        meet = _tudor_barb_meets_petal(n)
        return (0.0, meet, 1.0 - meet)
    if shape in ("holtz_c", "holtz_d"):
        return (0.0,)
    if shape == "holtz_f":
        if n == 1:
            return (0.0, 0.5)       # F-1: the heart's notch and point
        return (0.5 - HOLTZ_F_NOTCH_HALF_WIDTH, 0.5, 0.5 + HOLTZ_F_NOTCH_HALF_WIDTH)
    if shape == "holtz_j":
        return (0.0,)
    if shape == "holtz_k":
        return (0.0,)
    per = {"holtz_m": HOLTZ_M_PER_LOBE, "holtz_n": HOLTZ_N_PER_LOBE, "holtz_o": HOLTZ_OP_PER_GROUP,
           "holtz_q": HOLTZ_Q_PER_ARC, "holtz_s": ros["lobes"]}.get(shape)
    if per:
        points = list(numpy.arange(per) / float(per))
        if shape == "holtz_s":
            points += [0.5]
        return tuple(points)
    return ()


#######################################################################
# The design
#######################################################################

# A design has one rosette (rocking or pumping) or two (both - a
# rocking rosette for X and a pumping rosette for Z, each with its own
# shape, lobes, amplitude and phase, as with two rosettes and rubbers
# engaged on a rose engine). The first rosette's settings are the plain
# keys (shape, lobes, ...); the second's start "pump_" and are used only
# when motion is "both".
#
# The first rosette has no phase (always 0 - Rich, 15 November 2026):
# a physical rosette's phasing holes let it turn relative to the work,
# but with Rosetta the operator phases the work by indexing on the
# Rosetta panel before running the program. The pumping rosette's phase,
# used with "both", is how far it's turned relative to the rocking
# rosette - something indexing can't do, since it turns both together.
ROSETTE_KEYS = ("shape", "lobes", "amplitude", "phase", "phase_unit", "invert")
SECOND = "pump_"
WRAP = "wrap_"      # the rocking rosette on the Ellipse (see the Ellipse above)

DEFAULT_DESIGN = {
    "shape": "sine",
    "lobes": 12,
    "amplitude": 0.05,          # peak to peak, machine units
    "phase": 0.0,               # fraction of a repeat - always 0 (see above)
    "phase_unit": "lobe",       # how the window shows it: "lobe" or "deg"
    "invert": False,
    "ellipse_a": 1.0,           # the Ellipse: half its length (machine units)
    "ellipse_b": 0.75,          # half its width
    "wrap_shape": "sine",       # the rocking rosette on the Ellipse ("none" = plain)
    "wrap_lobes": 12,
    "wrap_amplitude": 0.02,
    "wrap_phase": 0.0,          # fraction of a repeat, along the ellipse's outline
    "wrap_phase_unit": "lobe",
    "wrap_invert": False,
    "pump_shape": "sine",       # the pumping rosette, when motion is "both"
    "pump_lobes": 12,
    "pump_amplitude": 0.02,
    "pump_phase": 0.0,
    "pump_phase_unit": "lobe",
    "pump_invert": False,
    "motion": "rock",           # "rock" (X), "pump" (Z) or "both"
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
    "finish_pass": False,       # passes mode: the last pass slower, at finish_pct
    "finish_pct": 10.0,         # finishing (and spring) passes' speed, % of c_rpm
    "spring_passes": 0,         # passes mode: extra turns at the final depth
    "preview_radius": 1.0,      # machine units - the drawing and Straight sides only
    "radius_at": "outside",     # preview_radius is the cut's "outside" (largest) or "inside"
    "units": "inch",            # "inch" or "mm"
    # Advance and retract (Rich, 16 November 2026): the cutter starts
    # clear of the work, moves in this far before cutting and back out
    # at the end - once for the whole program. 0 = none. X towards the
    # centre is minus, Z towards the headstock is minus.
    "advance_x": 0.0,
    "advance_x_dir": "centre",  # "centre" or "away"
    "advance_z": 0.0,
    "advance_z_dir": "headstock",   # "headstock" or "away"
    # Saving the rosette itself for 3D printing (rosetta_rosette_3d.py,
    # Rich 18 November 2026). Lengths in machine units, as above.
    "print_axis": "X",          # which rosette, when motion is "both"
    "print_machine": "mdf",     # starting values: rosetta_rosette_3d.MACHINES
    "print_diameter": 7.0,      # the rosette's diameter ...
    "print_diameter_at": "smallest",    # ... at its "largest" or "smallest"
    "print_ratio": 1.0,         # rosette amplitude = amplitude x this
    # The mounting starts as the MDF Rose Engine's (its drawing A-08 -
    # rosetta_rosette_3d.MACHINES).
    "print_thickness": 0.5,
    "print_bore": 1.002,        # centre bore diameter
    "print_hole_layout": "quarter",     # phasing holes "quarter" lobe apart, or "even"
    "print_holes": 9,           # phasing holes (0 = none) ...
    "print_hole_circle": 6.0,   # ... on a circle this diameter ...
    "print_hole_diameter": 0.1285,  # ... this size (#30 drill)
    "print_slots": 2,           # arced slots for the drive gear's screws (0 = none) ...
    "print_slot_circle": 5.0,   # ... on a circle this diameter ...
    "print_slot_span": 90.0,    # ... degrees between their ends' centres ...
    "print_slot_width": 0.266,  # ... this wide (1/4-20, free fit)
    "print_hole_allowance": 0.008,  # added to holes, slots and bore in the STL (printed holes come out small)
    "print_rim_width": 0.375,   # a pumping rosette's patterned rim
    "print_stl": True,
    "print_step": True,
}

# Largest straight-line error allowed between the program's points and
# the true rosette, and the blending tolerance (G64 P), per unit.
CHORD_TOLERANCE = {"inch": 0.0002, "mm": 0.005}
MAX_POINTS_PER_TURN = 7200
# No segment turns C more than this, so C's speed stays even.
MAX_SEGMENT_DEG = 2.0


def clean_design(design):
    '''A complete design: DEFAULT_DESIGN's keys, each of the right kind.'''
    design = dict(design or {})
    if "ratio" in design and "ellipse_a" not in design:
        # Saved 16 November 2026, before a and b: the exact ellipse at
        # the Object Size radius (as its outside).
        try:
            a = float(design.get("preview_radius", DEFAULT_DESIGN["preview_radius"]))
            design["ellipse_a"], design["ellipse_b"] = a, a * float(design["ratio"])
        except (TypeError, ValueError):
            pass
    if design.get("on_ellipse") and design.get("shape") != "ellipse":
        # Saved 17 November 2026 with On an ellipse ticked: that shape
        # becomes the rosette on the Ellipse.
        for key in ROSETTE_KEYS:
            if key in design:
                design[WRAP + key] = design[key]
        design["shape"] = "ellipse"
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
    for prefix in ("", SECOND, WRAP):
        # An Ellipse only rocks, and only it carries a rosette ("none" is
        # only for that one).
        allowed = set(SHAPES) - set({"": ["none"], SECOND: ["none", "ellipse"],
                                     WRAP: ["ellipse"]}[prefix])
        if d[prefix + "shape"] not in allowed:
            d[prefix + "shape"] = DEFAULT_DESIGN[prefix + "shape"]
        d[prefix + "lobes"] = fit_lobes(d[prefix + "shape"], min(max(d[prefix + "lobes"], 1), 360))
        d[prefix + "phase"] = d[prefix + "phase"] % 1.0
        if d[prefix + "phase_unit"] not in ("lobe", "deg"):
            d[prefix + "phase_unit"] = "lobe"
    d["phase"] = 0.0      # no phase for the first rosette (see ROSETTE_KEYS)
    for key, choices in (("motion", ("rock", "pump", "both")),
                         ("surface", ("face", "side")), ("rubber", ("point",)),
                         ("depth_mode", ("passes", "turns")), ("units", ("inch", "mm")),
                         ("radius_at", ("outside", "inside")),
                         ("advance_x_dir", ("centre", "away")),
                         ("advance_z_dir", ("headstock", "away")),
                         ("print_axis", ("X", "Z")),
                         ("print_machine", ("mdf", "armbruster", "lindow", "other")),
                         ("print_hole_layout", ("quarter", "even")),
                         ("print_diameter_at", ("largest", "smallest"))):
        if d[key] not in choices:
            d[key] = DEFAULT_DESIGN[key]
    d["c_direction"] = -1 if d["c_direction"] < 0 else 1
    d["passes"] = min(max(d["passes"], 1), 100)
    d["turns"] = min(max(d["turns"], 1), 100)
    d["finish_pct"] = min(max(d["finish_pct"], 1.0), 100.0)
    for key in ("ellipse_a", "ellipse_b"):
        d[key] = max(d[key], 1e-4)
    d["spring_passes"] = min(max(d["spring_passes"], 0), 5)
    for axis in ("x", "z"):
        d["advance_" + axis] = max(d["advance_" + axis], 0.0)
    for key in ("print_diameter", "print_ratio", "print_thickness", "print_bore", "print_hole_circle",
                "print_hole_diameter", "print_slot_circle", "print_slot_width", "print_hole_allowance",
                "print_rim_width"):
        d[key] = max(d[key], 0.0)
    d["print_holes"] = min(max(d["print_holes"], 0), 360)
    d["print_slots"] = min(max(d["print_slots"], 0), 12)
    d["print_slot_span"] = min(max(d["print_slot_span"], 0.0), 330.0)
    return d


def advance(design, axis):
    '''
    How far the cutter moves on axis ("X" or "Z") before cutting, signed
    as a machine move (towards the centre / headstock is minus); 0 if none.
    '''
    key = "advance_" + axis.lower()
    away = design[key + "_dir"] == "away"
    return design[key] * (1.0 if away else -1.0)


def advance_order(design):
    '''The axes that advance, in the order they move in: the depth axis
    last, so the cutter enters the work along the depth direction (and
    retracts in the reverse order).'''
    depth = depth_axis(design)
    axes = [axis for axis in ("X", "Z") if axis != depth] + [depth]
    return [axis for axis in axes if abs(advance(design, axis)) > 1e-12]


def pass_speeds(design):
    '''
    C's speed (rev/min) for each turn the program makes, in order. In
    "passes" mode: the passes, then any spring passes at the final
    depth; with a finishing pass the last pass and the spring passes
    run at finish_pct percent of c_rpm (roughing fast, finishing slow -
    Rich, 15 November 2026; 10% to start). In "turns" mode every turn is at c_rpm.
    '''
    d = design
    if d["depth_mode"] != "passes":
        return [d["c_rpm"]] * d["turns"]
    finish = d["c_rpm"] * d["finish_pct"] / 100.0 if d["finish_pass"] else d["c_rpm"]
    return [d["c_rpm"]] * (d["passes"] - 1) + [finish] * (1 + d["spring_passes"])


def rosette(design, prefix=""):
    '''One rosette's settings (shape, lobes, ...) from a design.'''
    return {key: design[prefix + key] for key in ROSETTE_KEYS}


def ellipse_base(design):
    '''(a, b) when the first rosette is an Ellipse, rocking, or None.'''
    if design["motion"] == "pump" or design["shape"] != "ellipse":
        return None
    return (design["ellipse_a"], design["ellipse_b"])


def rosettes(design):
    '''
    {axis: rosette} - the rosette each moving axis follows. With an
    Ellipse, X follows the rosette on it, carrying the ellipse
    ("ellipse"), and every rosette is spaced along its outline
    ("outline"), so a pumping rosette's waves stay in step.
    '''
    base = ellipse_base(design)
    if base:
        found = {"X": rosette(design, WRAP)}
        if design["motion"] == "both":
            found["Z"] = rosette(design, SECOND)
        found["X"]["ellipse"] = base
        for ros in found.values():
            ros["outline"] = base
        return found
    if design["motion"] == "rock":
        found = {"X": rosette(design)}
    elif design["motion"] == "pump":
        found = {"Z": rosette(design)}
    else:
        found = {"X": rosette(design), "Z": rosette(design, SECOND)}
    return found


def _turns(ros, theta_deg):
    '''Spindle angles as turns of the rosette: by angle, or on an
    ellipse by how far round its outline.'''
    if ros.get("outline"):
        return outline_fraction(ros["outline"], theta_deg)
    return numpy.asarray(theta_deg, dtype=float) / 360.0


def _angles(ros, turns):
    '''The reverse of _turns: spindle angles (degrees).'''
    if ros.get("outline"):
        return outline_angle(ros["outline"], turns)
    return numpy.asarray(turns, dtype=float) * 360.0


def deflection(ros, theta_deg):
    '''
    A rosette's deflection (0..1) at spindle angles theta_deg (numpy
    array, degrees from the program's start).
    '''
    t = numpy.mod(repeats(ros) * _turns(ros, theta_deg) + ros["phase"], 1.0)
    f = profile(ros, t)
    if ros["invert"]:
        f = 1.0 - f
    return f


def offset(ros, theta_deg):
    '''
    How far a rosette moves the cutter along its axis at theta_deg,
    from where it was at the start: minus = deflection (towards the
    centre when rocking). 0 at theta 0, and again after each whole turn.
    On an ellipse, X also follows it: r - a, so a cutter started at
    radius a cuts the ellipse exactly, with the waves on it.
    '''
    start = deflection(ros, numpy.array([0.0]))[0]
    y = -ros["amplitude"] * (deflection(ros, theta_deg) - start)
    if ros.get("ellipse"):
        y = y + ellipse_radius(ros["ellipse"], theta_deg) - ros["ellipse"][0]
    return y


def phase_degrees(ros):
    '''A rosette's phase as spindle degrees (phase is a fraction of one
    repeat - a lobe for most shapes; a whole repeat = 360 / repeats).'''
    return ros["phase"] * 360.0 / repeats(ros)


def straight_sides_amplitude(ros, radius, radius_at="outside"):
    '''
    The plain polygon amplitude whose sides come out straight when the
    cut's outside (its points) or inside (the middle of its sides) is at
    this radius: a polygon's sides are straight when amplitude = the
    points' radius x (1 - cos(180/lobes)), and the inside is the points'
    radius - amplitude.
    '''
    k = 1.0 - math.cos(math.pi / max(ros["lobes"], 3))
    return radius * k if radius_at == "outside" else radius * k / (1.0 - k)


def start_radius(design):
    '''
    The radius the cutter starts at, so that the cut's outside (largest
    radius) or inside (smallest) is at preview_radius - X's offsets move
    the cutter away from it as C turns. Without an X rosette the radius
    never changes. For the drawing and the notes only: the program cuts
    wherever the cutter is.
    '''
    radius = design["preview_radius"]
    ros = rosettes(design).get("X")
    if ros is None:
        return radius
    if ros.get("ellipse"):
        # Radius a (the end of its length), less how deep the waves on it
        # are at the start: the cut moves from where the cutter is put,
        # so a start on a wave's deepest point (D's cusp at phase 0) put
        # at a pushed the petals out past the ellipse - Rich's paper
        # chuck, 17 November 2026 (2.25 x 1.25 for A 1, B 0.5,
        # amplitude 0.125). Started here, the ellipse is the outside
        # of the waves.
        return ros["ellipse"][0] - ros["amplitude"] * deflection(ros, numpy.array([0.0]))[0]
    # Every shape's highest and lowest points are at a quarter, half or
    # whole lobe or at one of its sharp points - sampled exactly (a
    # sharp point is too narrow to find by even sampling alone).
    n = repeats(ros)
    where = numpy.concatenate((numpy.arange(4) / 4.0, sharp_points(ros)))
    marks = ((numpy.arange(n)[:, None] + where[None, :] - ros["phase"]) % n).ravel() * 360.0 / n
    y = offset(ros, numpy.concatenate((numpy.linspace(0.0, 360.0, 4000), marks)))
    return radius - (y.max() if design["radius_at"] == "outside" else y.min())


def cutter_start_radius(design):
    '''Where to put the cutter before running: start_radius, less the
    X advance (an advance towards the centre starts it further out).'''
    return start_radius(design) - advance(design, "X")


#######################################################################
# Points for one turn
#######################################################################

def _sample_angles(design):
    ros_list = list(rosettes(design).values())
    most_lobes = max(r["lobes"] for r in ros_list)
    samples = int(min(max(3600, most_lobes * 600), 200000))
    theta = [numpy.linspace(0.0, 360.0, samples + 1)]
    for ros in ros_list:
        n = repeats(ros)
        near = numpy.geomspace(1e-7, 0.05, 60) / ros["lobes"]
        for u in sharp_points(ros):
            # The invert of a sharp point is still sharp. Worked out in
            # turns of the rosette, then as spindle angles (the same,
            # except on an ellipse).
            centres = numpy.mod((numpy.arange(n) + u - ros["phase"]) / n, 1.0)
            centres = numpy.concatenate([centres, centres + 1.0])   # a point at 0 is also at 360
            for turns in (centres, (centres[:, None] + near[None, :]).ravel(),
                          (centres[:, None] - near[None, :]).ravel()):
                theta.append(_angles(ros, turns))
    theta = numpy.concatenate(theta)
    return numpy.unique(numpy.clip(theta, 0.0, 360.0))


def turn_points(design):
    '''
    (angles, {axis: offsets}, capped) for one turn, 0..360 degrees: the
    fewest points whose straight lines stay within CHORD_TOLERANCE of
    every rosette (no step over MAX_SEGMENT_DEG). capped is True when
    that needed more than MAX_POINTS_PER_TURN, so fewer were kept and
    the cut is less exact (very many sharp lobes).
    '''
    tol = CHORD_TOLERANCE[design["units"]]
    theta = _sample_angles(design)
    ys = {axis: offset(ros, theta) for axis, ros in rosettes(design).items()}
    last = len(theta) - 1

    def fits(i, j):
        if j - i <= 1:
            return True
        fraction = (theta[i:j + 1] - theta[i]) / (theta[j] - theta[i])
        for y in ys.values():
            line = y[i] + (y[j] - y[i]) * fraction
            if numpy.max(numpy.abs(y[i:j + 1] - line)) > tol:
                return False
        return True

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
    keep = numpy.array(keep)
    capped = len(keep) - 1 > MAX_POINTS_PER_TURN
    if capped:
        keep = keep[numpy.unique(numpy.round(numpy.linspace(0, len(keep) - 1,
                                                            MAX_POINTS_PER_TURN + 1)).astype(int))]
    angles = theta[keep]
    offsets = {}
    for axis, y in ys.items():
        offsets[axis] = y[keep]
        offsets[axis][-1] = 0.0     # exactly back where it started
    return angles, offsets, capped


def turn_seconds(design):
    return 60.0 / max(design["c_rpm"], 1e-9)


def turn_time(design, max_speeds=None, c_max_speed=None, points=None):
    '''
    (seconds, nominal seconds) for one turn: nominal at C's set speed;
    seconds allowing for each moving axis's Max Speed (max_speeds,
    {axis: units/sec}) and C's (deg/sec) - where a rosette is steeper
    than its axis can follow, LinuxCNC slows that move, and C with it (a
    sharp point always does this). Acceleration isn't counted, so it's
    a little short where a rosette changes direction sharply.
    '''
    angles, offsets, _ = points or turn_points(design)
    nominal = numpy.diff(angles) / 360.0 * turn_seconds(design)
    needed = nominal.copy()
    for axis, y in offsets.items():
        speed = (max_speeds or {}).get(axis)
        if speed:
            needed = numpy.maximum(needed, numpy.abs(numpy.diff(y)) / speed)
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


def _short(ros):
    ellipse = ros.get("ellipse")
    plain = ros["shape"] in ("ellipse", "none")
    name = "" if plain else "%s%d" % (SHAPE_SHORT[ros["shape"]], ros["lobes"])
    if ellipse:
        # e.g. Ellipse50 (b half of a), or HoltzD12-Ellipse50 on one
        name += ("-" if name else "") + "Ellipse%02d" % int(round(100.0 * ellipse[1] / ellipse[0]))
    return name or "Ellipse"        # an Ellipse that isn't rocking


# Every suggested name starts with this, so the Designer's programs sort
# together in the gcode folder (Rich, 15 November 2026). Not reserved:
# only names starting "rosetta" are (RESERVED_NAME).
FILE_NAME_PREFIX = "Rosette-"


def default_file_name(design):
    if design["motion"] == "both":
        found = rosettes(design)
        name = "%s_rock_%s_pump_%s.ngc" % (_short(found["X"]), _short(found["Z"]), design["surface"])
    else:
        name = "%s_%s_%s.ngc" % (_short(list(rosettes(design).values())[0]), design["motion"],
                                 design["surface"])
    return FILE_NAME_PREFIX + name


def describe(design):
    d = design
    found = rosettes(d)
    if d["motion"] == "both":
        what = "%s rocking, %s pumping" % (_short(found["X"]), _short(found["Z"]))
    else:
        what = "%s %s" % (_short(list(found.values())[0]), "rocking" if d["motion"] == "rock" else "pumping")
    return "%s, %s" % (what, "face" if d["surface"] == "face" else "side")


def depth_axis(design):
    return "Z" if design["surface"] == "face" else "X"


def _num(value):
    '''A plain decimal for G-code, at most 6 places, no "-0".'''
    text = ("%.6f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _signed(value):
    '''"+0.0123" or "-0.0123", to add to a parameter: never a bare
    number, which would be read as part of the parameter.'''
    text = _num(abs(value))
    return ("-" if value < 0 and text != "0" else "+") + text


# Each pass or turn is reported on motion.analog-out-00 (M67 E0, net
# thread-status -> the main panel's gladevcp.thread-status, shared with
# rosetta_thread.ngc), so the panel's progress bar can say "pass 2 of 3"
# (15 November 2026, Rich - as Threading counts its passes). Code =
# kind x PASS_STATUS_BASE + how many x 1000 + which; Threading's codes
# all stay below PASS_STATUS_BASE. M67 changes it as that pass's first
# move starts, not when the interpreter reads ahead to it. The program
# sets it to 0 first (M68, at once), clearing the last run's code. The
# panel shows codes only for a program whose first line starts
# "(Rosette Designer - " (gcode's first line - keep it). Duplicated in
# Rosetta_main.py (ROSETTE_PASS_*, ROSETTE_PROGRAM_MARK).
PASS_STATUS_BASE = 1000000
PASS_KIND = {"pass": 1, "finish": 2, "spring": 3, "turn": 4}


def _pass_status(kind, number, of):
    return "M67 E0 Q%d" % (PASS_KIND[kind] * PASS_STATUS_BASE + of * 1000 + number)


def gcode(design):
    '''The whole program, as text.'''
    d = clean_design(design)
    angles, offsets, _ = turn_points(d)
    tol = CHORD_TOLERANCE[d["units"]]
    depth = depth_axis(d)
    deeper = 1.0 if d["deeper_plus"] else -1.0
    turn_minutes = 1.0 / d["c_rpm"]
    speeds = pass_speeds(d)
    count = len(speeds)

    advancing = advance_order(d)
    if advancing:
        where = ["(Runs from where the cutter is: put it clear of the work - it moves in)",
                 "(%s first, cuts, then moves back out to where it started. Then run.)"
                 % " and ".join("%s %s" % (axis, _num(advance(d, axis))) for axis in advancing)]
    else:
        where = ["(Runs from where the cutter is: put it where the pattern should be cut,)",
                 "(then run.)"]
    lines = [
        "(Rosette Designer - %s - %s)" % (describe(d), time.strftime("%d %B %Y")),
    ] + where + [
        "(C turns %d time%s. Made by Rosetta's Rosette Designer -)"
        % (count, "" if count == 1 else "s"),
        "(open it there to change it.)",
    ] + [DESIGN_PREFIX + "%s %s)" % (key, json.dumps(d[key])) for key in sorted(d)] + [
        "",
        "#<_rd_diameter> = #<_lathe_diameter_mode>",
        "%s G8 G90 G64 P%s" % ("G20" if d["units"] == "inch" else "G21", _num(tol)),
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
            lines.append("%s = [%s%s]" % (var, var, _signed(advance(d, axis))))
            lines.append("G94 G1 %s[%s] F%s" % (axis, var, _num(d["plunge_feed"])))
        lines.append("")
    lines += [
        "(One turn of the rosette. #1 = depth from the start, #2 = C at the start,)",
        "(#3 = speed factor: 1 at the set C speed, less for a slower finishing pass)",
        "o100 sub",
    ]
    for i in range(1, len(angles)):
        words = []
        for axis in ("X", "Z"):
            if axis not in offsets and axis != depth:
                continue
            expr = "#<_rd_%s0>" % axis.lower()
            if axis == depth:
                expr += "+#1"
            if axis in offsets:
                expr += _signed(offsets[axis][i])
            words.append("%s[%s]" % (axis, expr))
        c = d["c_direction"] * angles[i]
        words.append("C[#2%s]" % _signed(c))
        minutes = (angles[i] - angles[i - 1]) / 360.0 * turn_minutes
        words.append("F[%s*#3]" % _num(1.0 / minutes))
        lines.append("  G93 G1 " + " ".join(words))
    lines += ["  G94", "o100 endsub", ""]

    depth_var = "#<_rd_%s0>" % depth.lower()
    if d["depth_mode"] == "passes":
        for k in range(1, count + 1):
            factor = speeds[k - 1] / d["c_rpm"]
            c_start = "[#<_rd_c0>%s]" % _signed(d["c_direction"] * 360.0 * (k - 1))
            if k > d["passes"]:
                depth_now = deeper * d["depth_per_pass"] * d["passes"]
                lines.append("(Spring pass %d of %d - %s rev/min)"
                             % (k - d["passes"], d["spring_passes"], _num(speeds[k - 1])))
                lines.append(_pass_status("spring", k - d["passes"], d["spring_passes"]))
            else:
                depth_now = deeper * d["depth_per_pass"] * k
                finishing = k == d["passes"] and d["finish_pass"]
                lines.append("(%s %d of %d - %s deep - %s rev/min)"
                             % ("Finishing pass" if finishing else "Pass", k, d["passes"],
                                _num(abs(depth_now)), _num(speeds[k - 1])))
                lines.append(_pass_status("finish" if finishing else "pass", k, d["passes"]))
                lines.append("G94 G1 %s[%s%s] F%s" % (depth, depth_var, _signed(depth_now),
                                                     _num(d["plunge_feed"])))
            lines.append("o100 call [%s] %s [%s]" % (_num(depth_now), c_start, _num(factor)))
        lines += ["(Back out of the cut)" if advancing else "(Back out to where the cutter started)",
                  "G0 %s[%s]" % (depth, depth_var)]
    else:
        for k in range(1, d["turns"] + 1):
            lines.append("(Turn %d of %d)" % (k, d["turns"]))
            lines.append(_pass_status("turn", k, d["turns"]))
            lines.append("o100 call [0] [#<_rd_c0>%s] [1]" % _signed(d["c_direction"] * 360.0 * (k - 1)))
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


#######################################################################
# Check circle (17 November 2026, Rich): the programs move the cutter
# from wherever it is put, so the start radius - measured from C's
# axis - sets the pattern's size and shape. That's hard to measure on
# a machine whose headstock moves, so this program turns C once with X
# and Z still: the cutter draws a circle round the true axis, whose
# diameter is twice the cutter's radius. Shared by the Rosette
# Designer and the Geometric Chuck Designer.
#######################################################################
CHECK_CIRCLE_PREFIX = "Check-Circle_"


def check_circle_file_name(radius, units):
    """e.g. Check-Circle_3.000in.ngc - named by the diameter it should be."""
    if units == "inch":
        return "%s%.3fin.ngc" % (CHECK_CIRCLE_PREFIX, 2.0 * radius)
    return "%s%.1fmm.ngc" % (CHECK_CIRCLE_PREFIX, 2.0 * radius)


def check_circle_size(radius, units):
    """The circle's diameter as text, e.g. "3.000 in"."""
    return ("%.3f in" if units == "inch" else "%.2f mm") % (2.0 * radius)


def check_circle_advance_text(x_advance, units):
    """What to do after the circle when there's an X advance, or ""."""
    if abs(x_advance) < 1e-12:
        return ""
    return ("Then move X %s by %s - the X advance - before running the pattern."
            % ("out" if x_advance < 0 else "in",
               ("%.3f in" if units == "inch" else "%.2f mm") % abs(x_advance)))


def check_circle_gcode(radius, units, c_deg_per_min, made_by, x_advance=0.0, c_direction=1):
    """
    The check circle program for a start radius (machine units): turns
    C once from where it is, at c_deg_per_min, nothing else moving.
    x_advance (signed, as advance()): the cutter is put clear by that
    much after the circle is right, so the program says so.
    """
    size = check_circle_size(radius, units)
    then = check_circle_advance_text(x_advance, units)
    message = ("Check circle: it should be %s across. Smaller - move X out by half the "
               "difference; bigger - move X in. Draw it again to check." % size)
    lines = [
        "(Check circle - %s - %s)" % (made_by, time.strftime("%d %B %Y")),
        "(Turns C once with X and Z still, so the cutter draws a circle round C's axis.)",
        "(Put the cutter just touching the work where the pattern's cut will start.)",
        "(The circle should be %s across - twice the start radius, %s.)"
        % (size, ("%.4f in" if units == "inch" else "%.3f mm") % radius),
        "(Smaller - move X out by half the difference; bigger - move X in. Draw it again.)",
    ]
    if then:
        lines.append("(%s)" % then)
    lines += [
        "",
        "(MSG,%s)" % (message + (" " + then if then else "")),
        "G90 G94",
        "G1 C[#5425%s] F%s" % (_signed(360.0 * (1 if c_direction >= 0 else -1)),
                               _num(max(min(c_deg_per_min, 7200.0), 36.0))),
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

# The sample programs' lobes: the guide's own counts for the letters.
SAMPLE_LOBES = {"sine": 12, "holtz_j": 24, "holtz_k": 4, "holtz_m": 24, "holtz_n": 15,
                "holtz_o": 12, "holtz_p": 18, "holtz_q": 16, "holtz_s": 32}


def write_samples(folder):
    os.makedirs(folder, exist_ok=True)
    written = []
    for units in ("inch", "mm"):
        scale = 1.0 if units == "inch" else 25.4
        for shape in SHAPE_IDS:
            if shape == "none":
                continue        # only the rosette on an Ellipse (below)
            for motion in ("rock", "pump", "both"):
                for surface in ("face", "side"):
                    for mode in ("passes", "turns"):
                        d = clean_design({
                            "shape": shape, "lobes": SAMPLE_LOBES.get(shape, 8),
                            "amplitude": 0.05 * scale, "depth_per_pass": 0.005 * scale,
                            "plunge_feed": 1.0 * scale, "preview_radius": 1.0 * scale,
                            "motion": motion, "surface": surface, "depth_mode": mode,
                            "turns": 2, "units": units, "finish_pass": mode == "passes",
                            "finish_pct": 10.0, "spring_passes": 1,
                            "pump_shape": "lotus" if shape == "sine" else "sine",
                            "pump_lobes": 5, "pump_amplitude": 0.02 * scale, "pump_phase": 0.1,
                        })
                        name = "%s_%s_%s_%s_%s.ngc" % (shape, motion, surface, mode, units)
                        with open(os.path.join(folder, name), "w") as f:
                            f.write(gcode(d))
                        written.append(name)
        # Waves on an ellipse (a 2:1 ellipse), rocking and both.
        for shape in ("sine", "holtz_d", "lotus"):
            for motion in ("rock", "both"):
                for surface in ("face", "side"):
                    d = clean_design({
                        "shape": "ellipse", "wrap_shape": shape,
                        "wrap_lobes": SAMPLE_LOBES.get(shape, 8), "wrap_phase": 0.5,
                        "ellipse_a": 1.0 * scale, "ellipse_b": 0.5 * scale,
                        "wrap_amplitude": 0.05 * scale, "depth_per_pass": 0.005 * scale,
                        "plunge_feed": 1.0 * scale, "motion": motion, "surface": surface,
                        "units": units, "pump_shape": "sine", "pump_lobes": 6,
                        "pump_amplitude": 0.02 * scale, "pump_phase": 0.1,
                    })
                    name = "%s_on_ellipse_%s_%s_%s.ngc" % (shape, motion, surface, units)
                    with open(os.path.join(folder, name), "w") as f:
                        f.write(gcode(d))
                    written.append(name)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 rosetta_rosettes.py <folder for sample programs>")
        sys.exit(1)
    print("\n".join(write_samples(sys.argv[1])))
