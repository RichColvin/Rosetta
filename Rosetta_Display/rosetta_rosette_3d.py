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
#   rosetta_rosette_3d.py
#
# Purpose:
#   The Rosette Designer's rosette as a solid, saved as STL (for 3D
#   printing) and STEP (for CAD, or to have it machined) - Rich, 18
#   November 2026 (the tracker's Planning, "Stage 4, making a physical
#   rosette").
#
#   A rocking rosette (X) is a disc whose edge follows the pattern; a
#   pumping rosette (Z) is a disc with a raised rim whose top rises and
#   falls with it. Both have a centre bore, phasing holes (a quarter
#   lobe apart, or evenly round) and arced slots for the screws that
#   hold it to its drive gear.
#
#   The rubber is a point (Rich, 18 November 2026): the edge is exactly
#   the designed motion, times the machine ratio (the rosette's wave
#   against the cut's). A real rubber's rounded nose cuts it a little
#   softer than designed; allowing for it is the Planning's stage 3.
#
#   Seen from the top as printed, a rocking rosette's outline is the
#   Rosette Designer's face drawing (angles counter-clockwise).
#
#   Clean room: plain geometry, and the STEP file is written from the
#   standard (ISO 10303-21, AP214 - automotive_design) - no CAD library.
#   Every file is in millimetres (slicers take STL as mm).
#
#   python3 rosetta_rosette_3d.py <folder>   writes sample files.
#
# Version:
#   1.0 - 18 November 2026
#   1.1 - 18 November 2026 - the MDF Rose Engine's mounting (Rich's
#         drawing A-08): phasing holes a quarter lobe apart, arced
#         slots for the drive gear's screws, a printed-hole allowance
#   1.2 - 19 November 2026 - Armbruster and Lindow: holes and slots
#         sized to the rosette (the MDF's were outside a 5" Lindow)
#
# Copyright (c) 2026 Colvin Tools / Brainwave Embedded - MIT License
#######################################################################

import math
import os
import struct
import sys
import time

import numpy

import rosetta_rosettes as rr

MM_PER_INCH = 25.4

# Starting values by machine: (name, {setting: value, lengths in
# inches}). Choosing one fills these in; "other" keeps what's entered.
# The MDF Rose Engine's from Rich's drawing A-08 v1 ("A-8 Rosette
# Construction", 12/10/08) and Rich, 18 November 2026: 7" at the
# hollows, 1/2" thick, a 1.002" bore, #30-drill (0.1285") phasing holes
# on a 6" circle a quarter lobe apart from 0 to 2 lobes, and two arced
# slots on a 5" circle spanning 90 degrees, top and bottom, for the
# 1/4-20 screws that hold the rosette to its drive gear (0.266" = a
# free fit). The holes centred at 0 degrees - the pattern's start, a
# quarter turn from the slots, midway between them (Rich, 18 November
# 2026: on the MDF Rose Engine they aren't over a slot). Others: only
# their usual size (Rich, 15 November 2026).
MACHINES = {
    "mdf": ("MDF Rose Engine", {
        "print_diameter": 7.0, "print_diameter_at": "smallest", "print_thickness": 0.5,
        "print_bore": 1.002, "print_hole_layout": "quarter", "print_holes": 9,
        "print_hole_circle": 6.0, "print_hole_diameter": 0.1285, "print_hole_centre": 0.0, "print_slots": 2,
        "print_slot_circle": 5.0, "print_slot_span": 90.0, "print_slot_width": 0.266}),
    "armbruster": ("Armbruster Mark II", {"print_diameter": 7.0, "print_diameter_at": "largest"}),
    "lindow": ("Lindow", {"print_diameter": 5.0, "print_diameter_at": "largest"}),
    "other": ("Other", {}),
}
# MACHINES' lengths (inches, converted for a mm design).
MACHINE_LENGTHS = ("print_diameter", "print_thickness", "print_bore", "print_hole_circle",
                   "print_hole_diameter", "print_slot_circle", "print_slot_width")

# Where the slots are centred (0 degrees, where the pattern starts, is
# to the right): top and bottom, as on the MDF drawing. The phasing
# holes' centre is a setting (print_hole_centre).
SLOT_CENTRE_DEG = 90.0

MESH_TOLERANCE_MM = 0.01        # STL: straight pieces within this of the true shape
CURVE_TOLERANCE_MM = 0.002      # STEP: its curves within this of the true shape
MAX_STEP_DEG = 1.0              # STL: no piece of an edge turns more than this
MIN_WALL_MM = 1.0               # least plastic between holes, slots, the bore and the edge
PRINTER_RESOLUTION_MM = 0.1     # about what a printer holds
PUMP_RIM_STEP_MM = 1.0          # a pumping rosette's rim stands at least this proud
MAX_CURVE_POINTS = 40000        # STEP: most control points in one curve


#######################################################################
# The rosette's shape
#######################################################################

def print_axes(design):
    '''The axes with a rosette to print: "X" (rocking) and/or "Z" (pumping).'''
    return [axis for axis in ("X", "Z") if axis in rr.rosettes(design)]


def chosen_axis(design):
    axes = print_axes(design)
    return design["print_axis"] if design["print_axis"] in axes else axes[0]


def _to_mm(design, value):
    return value * MM_PER_INCH if design["units"] == "inch" else value


def _from_mm(design, value):
    return value / MM_PER_INCH if design["units"] == "inch" else value


def machine_values(design, machine):
    '''{setting: value} a machine fills in, lengths in the design's units.'''
    values = dict(MACHINES[machine][1])
    for key in MACHINE_LENGTHS:
        if key in values:
            values[key] = _from_mm(design, values[key] * MM_PER_INCH)
    if machine != "other" and "print_hole_circle" not in values:
        # Mounting not known for this machine: the MDF's phasing-hole and
        # slot circles in proportion to this rosette's smallest diameter
        # (6" and 5" on the MDF's 7"), so they're always inside it - left
        # as they were, a 5" Lindow rosette had the MDF's 6" holes outside
        # it and couldn't be saved (Rich, 19 November 2026).
        mdf = MACHINES["mdf"][1]
        sized = dict(design, **values)
        sized["print_machine"] = "other"
        geo = Rosette3D(rr.clean_design(sized))
        smallest = 2.0 * (geo.smallest if geo.kind == "rock" else geo.inner_radius)
        for key in ("print_hole_circle", "print_slot_circle"):
            values[key] = _from_mm(design, smallest * mdf[key] / mdf["print_diameter"])
    return values


def sharp_angles(ros):
    '''Spindle angles (degrees, 0..360) where the rosette has a sharp point.'''
    n = rr.repeats(ros)
    found = []
    for u in rr.sharp_points(ros):
        turns = numpy.mod((numpy.arange(n) + u - ros["phase"]) / n, 1.0)
        found.append(numpy.mod(rr._angles(ros, turns), 360.0))
    if not found:
        return numpy.zeros(0)
    angles = numpy.unique(numpy.round(numpy.concatenate(found), 9))
    return angles[angles < 360.0 - 1e-9]


class Rosette3D(object):
    '''
    One rosette as a solid, in mm. kind "rock": edge radius(phi);
    kind "pump": rim top height top(phi), rim from inner_radius to
    outer_radius. printed=True adds the printed-hole allowance to the
    bore, phasing holes and slots (printed holes come out small) - for
    the STL; the STEP keeps their true sizes. problems block saving;
    warnings don't.
    '''

    def __init__(self, design, axis=None, printed=False):
        d = rr.clean_design(design)
        self.design = d
        self.axis = axis or chosen_axis(d)
        self.kind = "rock" if self.axis == "X" else "pump"
        self.ros = rr.rosettes(d)[self.axis]
        self.ratio = d["print_ratio"]
        self.allowance = _to_mm(d, d["print_hole_allowance"]) if printed else 0.0
        self.thickness = _to_mm(d, d["print_thickness"])
        self.bore_radius = (_to_mm(d, d["print_bore"]) + self.allowance) / 2.0
        self.holes = d["print_holes"]
        self.hole_radius = _to_mm(d, d["print_hole_circle"]) / 2.0
        self.hole_size = (_to_mm(d, d["print_hole_diameter"]) + self.allowance) / 2.0  # a hole's radius
        self.slots = d["print_slots"]
        self.slot_radius = _to_mm(d, d["print_slot_circle"]) / 2.0
        self.slot_span = d["print_slot_span"]
        self.slot_half_width = (_to_mm(d, d["print_slot_width"]) + self.allowance) / 2.0
        self.sharp = sharp_angles(self.ros)
        self.dense = numpy.unique(numpy.concatenate((rr._sample_angles(d), self.sharp, [0.0, 360.0])))
        off = self.offset(self.dense)
        self.low, self.high = float(off.min()), float(off.max())
        diameter = _to_mm(d, d["print_diameter"])
        if self.kind == "rock":
            half = diameter / 2.0
            self.reference = half - (self.high if d["print_diameter_at"] == "largest" else self.low)
            self.smallest = self.reference + self.low
            self.largest = self.reference + self.high
        else:
            self.outer_radius = diameter / 2.0
            self.inner_radius = self.outer_radius - _to_mm(d, d["print_rim_width"])
            self.base = self.thickness + PUMP_RIM_STEP_MM
        self.problems, self.warnings = self._check()

    # -- the shape ----------------------------------------------------

    def offset(self, phi):
        '''The rosette's wave at phi (degrees), mm: the cut's offset x the ratio.'''
        return _to_mm(self.design, self.ratio * rr.offset(self.ros, numpy.asarray(phi, dtype=float)))

    def radius(self, phi):
        '''A rocking rosette's edge radius at phi (degrees).'''
        return self.reference + self.offset(phi)

    def top(self, phi):
        '''A pumping rosette's rim height at phi (degrees).'''
        return self.base + self.offset(phi) - self.low

    def edge_inside(self):
        '''How far out the bore, holes and slots may reach: the edge's
        smallest radius (rocking) or the rim's inside (pumping).'''
        return self.smallest if self.kind == "rock" else self.inner_radius

    def hole_step_lobes(self):
        '''
        "quarter" layout: lobes between one phasing hole and the next -
        1/4, or when holes a quarter lobe apart would touch (many lobes),
        1 1/4, 2 1/4 ... - whole lobes don't change the phasing, so each
        hole still phases the pattern a quarter lobe more.
        '''
        lobes = max(self.ros["lobes"], 1)
        need = 2.0 * self.hole_size + MIN_WALL_MM
        for whole in range(lobes):
            step = whole + 0.25
            gap = math.radians(step * 360.0 / lobes)
            if 2.0 * self.hole_radius * math.sin(min(gap, math.pi) / 2.0) >= need:
                return step
        return 0.25

    def hole_angles(self):
        '''
        The phasing holes' angles (degrees, 0..360). "even": evenly
        round. "quarter" (the MDF drawing, Rich 18 November 2026): each
        a quarter lobe on from the last (hole_step_lobes) - the first at
        a whole lobe from the pattern's start, so the holes phase it by
        0, 1/4, 1/2 ... lobe - centred as near print_hole_centre as whole
        lobes allow. Holes that would come round onto others are left out.
        '''
        n = self.holes
        if n <= 0:
            return numpy.zeros(0)
        if self.design["print_hole_layout"] == "even":
            return numpy.arange(n) * 360.0 / n
        lobes = max(self.ros["lobes"], 1)
        lobe_deg = 360.0 / lobes
        step = self.hole_step_lobes()
        first = round((self.design["print_hole_centre"] - (n - 1) / 2.0 * step * lobe_deg) / lobe_deg)
        turns = (first + numpy.arange(n) * step) / lobes
        angles = numpy.mod(rr._angles(self.ros, numpy.mod(turns, 1.0)), 360.0)
        keep, seen = [], set()
        for a in angles:
            key = round(float(a), 6) % 360.0
            if key not in seen:
                seen.add(key)
                keep.append(float(a))
        return numpy.array(keep)

    def hole_centres(self):
        rad = numpy.radians(self.hole_angles())
        return [(self.hole_radius * math.cos(a), self.hole_radius * math.sin(a)) for a in rad]

    def slot_centres(self):
        '''Each slot's middle angle (degrees): evenly round from the top.'''
        return [(SLOT_CENTRE_DEG + k * 360.0 / self.slots) % 360.0 for k in range(self.slots)]

    def slot_tip_deg(self):
        '''How far a slot's rounded end reaches past its end's centre, in
        degrees round the rosette.'''
        return math.degrees(math.asin(min(self.slot_half_width / max(self.slot_radius, 1e-9), 1.0)))

    def wave_mm(self):
        return self.high - self.low

    # -- checks -------------------------------------------------------

    def _check(self):
        problems, warnings = [], []
        unit = "\"" if self.design["units"] == "inch" else " mm"
        show = lambda v: ("%.3f" % _from_mm(self.design, v)).rstrip("0").rstrip(".") + unit
        if self.thickness <= 0.0:
            problems.append("The thickness must be more than 0.")
        if self.bore_radius <= 0.0:
            problems.append("The rosette needs a centre bore.")
        if self.kind == "rock":
            if self.smallest <= 0.0:
                problems.append("The wave (amplitude x ratio) is bigger than the rosette - make the "
                                "diameter larger or the ratio smaller.")
                return problems, warnings
        elif self.inner_radius <= 0.0:
            problems.append("The rim is wider than the rosette.")
            return problems, warnings
        if self.holes and self.hole_size <= 0.0:
            problems.append("The phasing holes need a size.")
        if self.slots and (self.slot_half_width <= 0.0 or self.slot_span <= 0.0):
            problems.append("The slots need a width and a span.")
        if problems:
            return problems, warnings
        # Round the rosette, from the middle out: nothing may run into
        # the next thing, with MIN_WALL_MM between.
        rings = [("the bore", 0.0, self.bore_radius)]
        if self.slots:
            rings.append(("the slots", self.slot_radius - self.slot_half_width,
                          self.slot_radius + self.slot_half_width))
        if self.holes:
            rings.append(("the phasing holes", self.hole_radius - self.hole_size,
                          self.hole_radius + self.hole_size))
        rings.sort(key=lambda ring: ring[1])
        for (name_a, _, out_a), (name_b, in_b, _) in zip(rings[:-1], rings[1:]):
            if in_b - out_a < MIN_WALL_MM:
                problems.append("%s run into %s - move them apart." % (name_b.capitalize(), name_a))
        inside = self.edge_inside()
        name, _, out = rings[-1]
        if out + MIN_WALL_MM > inside:
            problems.append("%s run into %s (%s across)." % (
                name.capitalize(), "the edge at its smallest" if self.kind == "rock" else "the rim",
                show(2 * inside)))
        if self.holes >= 2:
            angles = numpy.sort(self.hole_angles())
            gaps = numpy.diff(numpy.concatenate((angles, [angles[0] + 360.0])))
            chord = 2.0 * self.hole_radius * math.sin(math.radians(float(gaps.min())) / 2.0)
            if chord - 2.0 * self.hole_size < MIN_WALL_MM:
                if self.design["print_hole_layout"] == "quarter":
                    problems.append("With %d lobes the phasing holes overlap - use fewer or smaller "
                                    "holes, a larger circle, or Evenly round." % self.ros["lobes"])
                else:
                    problems.append("The phasing holes overlap - use fewer, smaller ones, or a larger circle.")
        if self.slots >= 2:
            reach = self.slot_span + 2.0 * self.slot_tip_deg() + math.degrees(MIN_WALL_MM / self.slot_radius)
            if reach > 360.0 / self.slots:
                problems.append("The slots overlap - make them shorter, or use fewer.")
        elif self.slots == 1 and self.slot_span + 2.0 * self.slot_tip_deg() > 300.0:
            problems.append("The slot is too long.")
        if self.holes and self.design["print_hole_layout"] == "quarter" and self.hole_step_lobes() > 0.25:
            step = self.hole_step_lobes()
            warnings.append("Holes a quarter lobe apart would touch with %d lobes, so they are %d 1/4 "
                            "lobes apart - each still phases the pattern a quarter lobe on from the last."
                            % (self.ros["lobes"], int(step)))
        if (self.holes and self.design["print_hole_layout"] == "quarter"
                and len(self.hole_angles()) < self.holes):
            warnings.append("With %d lobe%s, only %d of the phasing holes fit - the rest would land on "
                            "the same places." % (self.ros["lobes"], "" if self.ros["lobes"] == 1 else "s",
                                                  len(self.hole_angles())))
        wave = self.wave_mm()
        if 0.0 < wave < PRINTER_RESOLUTION_MM:
            warnings.append("The wave is only %s deep - finer than most printers hold (about 0.1 mm)."
                            % show(wave))
        elif wave <= 0.0:
            warnings.append("This rosette has no wave - it's a plain %s." %
                            ("disc" if self.kind == "rock" else "ring"))
        if self.kind == "pump":
            warnings.append("Pumping rosette: print it at the smallest layer height your printer "
                            "can, and use a rubber that rides over the ridges left (e.g. one with a "
                            "roller bearing on its nose).")
        return problems, warnings


#######################################################################
# Points along the edge
#######################################################################

def _pick(theta, points, tol, max_step, keep):
    '''
    Indices into theta (ascending) of the fewest points whose straight
    lines stay within tol of points (N x 2), no step over max_step
    degrees, always including the indices in keep.
    '''
    last = len(theta) - 1

    def fits(i, j):
        if j - i <= 1:
            return True
        a, b = points[i], points[j]
        ab = b - a
        length = math.hypot(ab[0], ab[1])
        rel = points[i + 1:j] - a
        if length < 1e-12:
            dist = numpy.hypot(rel[:, 0], rel[:, 1])
        else:
            dist = numpy.abs(rel[:, 0] * ab[1] - rel[:, 1] * ab[0]) / length
        return float(dist.max()) <= tol

    stops = sorted(set(int(k) for k in keep) | {0, last})
    chosen = [0]
    for start, end in zip(stops[:-1], stops[1:]):
        i = start
        while i < end:
            limit = int(numpy.searchsorted(theta, theta[i] + max_step, side="right")) - 1
            limit = max(min(limit, end), i + 1)
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
            chosen.append(i)
    return numpy.array(chosen)


def edge_angles(geo):
    '''The STL's angles round the edge (degrees, 0 .. 360 inclusive).'''
    theta = geo.dense
    keep = numpy.searchsorted(theta, geo.sharp)
    if geo.kind == "rock":
        r = geo.radius(theta)
        rad = numpy.radians(theta)
        points = numpy.column_stack((r * numpy.cos(rad), r * numpy.sin(rad)))
        sag_radius = geo.largest
    else:
        points = numpy.column_stack((geo.outer_radius * numpy.radians(theta), geo.top(theta)))
        sag_radius = geo.outer_radius
    step = min(MAX_STEP_DEG, math.degrees(2.0 * math.sqrt(2.0 * MESH_TOLERANCE_MM / max(sag_radius, 1e-6))))
    return theta[_pick(theta, points, MESH_TOLERANCE_MM, step, keep)]


#######################################################################
# STL
#######################################################################

def _circle_step(radius):
    '''Degrees between points on a circle so its straight pieces stay
    within MESH_TOLERANCE_MM.'''
    return min(MAX_STEP_DEG * 4, math.degrees(2.0 * math.sqrt(2.0 * MESH_TOLERANCE_MM / max(radius, 1e-6))))


def _fill(a, b, step):
    '''Angles from a up to (not including) b, at most step apart.'''
    count = max(int(math.ceil((b - a) / step - 1e-9)), 1)
    return a + (b - a) * numpy.arange(count) / count


def _cyclic_merge(inner, inner_ang, outer, outer_ang):
    '''
    Triangles joining two closed rings (lists of points, angles
    ascending over one turn from about the same start), both seen from
    one centre - each triangle has two points on one ring and one on
    the other.
    '''
    tris = []
    n, m = len(inner), len(outer)
    i = j = 0
    while i < n or j < m:
        if i == n:
            advance_inner = False
        elif j == m:
            advance_inner = True
        else:
            next_i = inner_ang[i + 1] if i + 1 < n else inner_ang[0] + 360.0
            next_j = outer_ang[j + 1] if j + 1 < m else outer_ang[0] + 360.0
            advance_inner = next_i <= next_j
        if advance_inner:
            tris.append((inner[i % n], outer[j % m], inner[(i + 1) % n]))
            i += 1
        else:
            tris.append((inner[i % n], outer[j % m], outer[(j + 1) % m]))
            j += 1
    return tris


def _ring(radius, angles, z, centre=(0.0, 0.0)):
    rad = numpy.radians(angles)
    return [(centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a), z) for a in rad]


def _polar(radii, angles, z):
    rad = numpy.radians(angles)
    return [(r * math.cos(a), r * math.sin(a), z) for r, a in zip(radii, rad)]


def _strip(lower, lower_ang, upper, upper_ang):
    '''Triangles between two open chains running the same way round
    (angles ascending, same first and last angle).'''
    tris = []
    i = j = 0
    n, m = len(lower), len(upper)
    while i < n - 1 or j < m - 1:
        if i == n - 1:
            advance_lower = False
        elif j == m - 1:
            advance_lower = True
        else:
            advance_lower = lower_ang[i + 1] <= upper_ang[j + 1]
        if advance_lower:
            tris.append((lower[i], upper[j], lower[i + 1]))
            i += 1
        else:
            tris.append((lower[i], upper[j], upper[j + 1]))
            j += 1
    return tris


def _hole_angles_about(geo):
    '''Angles (degrees, -180..180) of the points round each hole.'''
    return _fill(-180.0, 180.0, min(_circle_step(geo.hole_size), 10.0))


def _features(centres, halves):
    '''[(centre, half width, index)] sorted, each half width no more than
    half the way to its neighbours.'''
    order = numpy.argsort(numpy.mod(centres, 360.0))
    items = [(float(numpy.mod(centres[k], 360.0)), float(halves[k]), int(k)) for k in order]
    n = len(items)
    found = []
    for i, (c, h, k) in enumerate(items):
        if n > 1:
            before = (c - items[i - 1][0]) % 360.0
            after = (items[(i + 1) % n][0] - c) % 360.0
            h = min(h, before / 2.0, after / 2.0)
        found.append((c, h, k))
    return found


def _pieces(features, step):
    '''The features' sectors and the gaps between, and the angles round
    the band (ascending from about 0).'''
    pieces = []
    n = len(features)
    for i, (c, h, k) in enumerate(features):
        pieces.append(("feature", c - h, c + h, k))
        nc, nh, _ = features[(i + 1) % n]
        after = nc - nh + (360.0 if i == n - 1 else 0.0)
        if after - (c + h) > 1e-9:
            pieces.append(("gap", c + h, after, None))
    grid = numpy.concatenate([_fill(a, b, step) for _, a, b, _ in pieces])
    return pieces, numpy.sort(numpy.mod(grid, 360.0))


def _indexer(grid):
    index = {round(float(a), 9): i for i, a in enumerate(grid)}
    return lambda angle: index[round(float(numpy.mod(angle, 360.0)), 9)]


def _hole_band(geo, z, r1, r2):
    '''A ring from r1 to r2 holding the phasing holes: (inner ring,
    outer ring, triangles); a ring is (points, angles).'''
    angles = geo.hole_angles()
    limit = 0.8 * math.degrees(math.acos(min(r1 / geo.hole_radius, 1.0)))
    features = _features(angles, [limit] * len(angles))
    # Close enough together that, seen from a hole's centre, the band's
    # points are no more than about 15 degrees apart - coarser, and the
    # triangles joining them to the hole cut across it. Rings across
    # the band do the same along the sides of each hole's piece (close
    # together when the holes are).
    near = min(r2 - geo.hole_radius, geo.hole_radius - r1,
               min(geo.hole_radius * math.sin(math.radians(h)) for _, h, _ in features))
    step = min(_circle_step(r2), math.degrees(0.25 * near / r2))
    count = max(int(math.ceil((r2 - r1) / (0.25 * near))), 1)
    pieces, grid = _pieces(features, step)
    at = _indexer(grid)
    rings = [_ring(r, grid, z) for r in numpy.linspace(r1, r2, count + 1)]
    inner, outer = rings[0], rings[-1]
    centres = geo.hole_centres()
    hole_ang = _hole_angles_about(geo)
    tris = []
    for kind, a, b, k in pieces:
        own = [at(x) for x in _fill(a, b, step)] + [at(b)]
        if kind == "gap":
            for lo, hi in zip(rings[:-1], rings[1:]):
                for p, q in zip(own[:-1], own[1:]):
                    tris.append((lo[p], hi[p], hi[q]))
                    tris.append((lo[p], hi[q], lo[q]))
            continue
        # The sector's outline, counter-clockwise, and the hole in it,
        # joined round the hole's centre.
        cx, cy = centres[k]
        outline = ([ring[own[0]] for ring in rings[:-1]] + [outer[p] for p in own]
                   + [ring[own[-1]] for ring in rings[-2:0:-1]] + [inner[p] for p in reversed(own[1:])])
        ang = numpy.degrees(numpy.arctan2([p[1] - cy for p in outline], [p[0] - cx for p in outline]))
        start = int(numpy.argmin(ang))
        outline = outline[start:] + outline[:start]
        ang = numpy.concatenate((ang[start:], ang[:start]))
        ang = ang[0] + numpy.mod(ang - ang[0], 360.0)
        hole = _ring(geo.hole_size, hole_ang, z, (cx, cy))
        tris += _cyclic_merge(hole, hole_ang, outline, ang)
    return (inner, grid), (outer, grid), tris


def _slot_ends(geo, k):
    '''(first end's centre angle, last end's) of slot k, degrees.'''
    centre = geo.slot_centres()[k]
    return centre - geo.slot_span / 2.0, centre + geo.slot_span / 2.0


def _slot_parts(geo, k, z):
    '''
    Slot k's outline in four parts at height z: its outer arc and inner
    arc (each from the first end to the last), and its rounded ends -
    the last end from the outer arc to the inner, the first from the
    inner arc to the outer - sharing their end points exactly.
    '''
    rs, c = geo.slot_radius, geo.slot_half_width
    e0, e1 = _slot_ends(geo, k)
    arc = numpy.concatenate((_fill(e0, e1, _circle_step(rs + c)), [e1]))
    outer, inner = _ring(rs + c, arc, z), _ring(rs - c, arc, z)
    steps = max(int(math.ceil(180.0 / min(_circle_step(c), 10.0))), 4)

    def cap(end_deg, psi):
        e = math.radians(end_deg)
        u, v = numpy.array([math.cos(e), math.sin(e)]), numpy.array([-math.sin(e), math.cos(e)])
        return [tuple(rs * u + c * (math.cos(p) * u + math.sin(p) * v)) + (z,) for p in psi]

    cap1 = [outer[-1]] + cap(e1, numpy.linspace(0.0, math.pi, steps + 1)[1:-1]) + [inner[-1]]
    cap0 = [inner[0]] + cap(e0, numpy.linspace(-math.pi, 0.0, steps + 1)[1:-1]) + [outer[0]]
    return arc, outer, inner, cap0, cap1


def _slot_outline(geo, k, z):
    '''Slot k's whole outline, a closed ring.'''
    arc, outer, inner, cap0, cap1 = _slot_parts(geo, k, z)
    return outer + cap1[1:-1] + inner[::-1] + cap0[1:-1]


def _ear_clip(points):
    '''Triangles (of the points) filling a simple polygon - one without
    holes; points in order round it.'''
    xy = numpy.array([(p[0], p[1]) for p in points])
    idx = list(range(len(points)))
    area = 0.5 * numpy.sum(xy[:, 0] * numpy.roll(xy[:, 1], -1) - numpy.roll(xy[:, 0], -1) * xy[:, 1])
    if area < 0:
        idx.reverse()
    tris = []

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    while len(idx) > 3:
        best = None
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = xy[i0], xy[i1], xy[i2]
            turn = cross(a, b, c)
            if turn <= 1e-12:
                continue        # reflex, or in a straight line
            others = numpy.array([q for q in idx if q not in (i0, i1, i2)])
            if len(others):
                o = xy[others]
                d1 = (b[0] - a[0]) * (o[:, 1] - a[1]) - (b[1] - a[1]) * (o[:, 0] - a[0])
                d2 = (c[0] - b[0]) * (o[:, 1] - b[1]) - (c[1] - b[1]) * (o[:, 0] - b[0])
                d3 = (a[0] - c[0]) * (o[:, 1] - c[1]) - (a[1] - c[1]) * (o[:, 0] - c[0])
                if numpy.any((d1 >= -1e-12) & (d2 >= -1e-12) & (d3 >= -1e-12)):
                    continue
            best = k
            break
        if best is None:
            raise ValueError("could not fill a slot's end")
        k = best
        tris.append((points[idx[k - 1]], points[idx[k]], points[idx[(k + 1) % len(idx)]]))
        del idx[k]
    tris.append(tuple(points[q] for q in idx))
    return tris


def _slot_band(geo, z, r1, r2):
    '''
    A ring from r1 to r2 holding the slots, with a middle circle at the
    slots' radius: (inner ring, outer ring, triangles). Along a slot,
    strips join its arcs to the ring's circles; each end is a small
    outline filled by ear clipping (its rounded end turns too steeply
    to join by angle).
    '''
    rm = geo.slot_radius
    reach = geo.slot_span / 2.0 + geo.slot_tip_deg() + max(0.5, math.degrees(MIN_WALL_MM / 2.0 / rm))
    features = _features(numpy.array(geo.slot_centres()), [reach] * geo.slots)
    pieces = []
    n = len(features)
    for i, (c, h, k) in enumerate(features):
        e0, e1 = _slot_ends(geo, k)
        e0 = c + ((e0 - c + 180.0) % 360.0 - 180.0)
        e1 = e0 + geo.slot_span
        pieces += [("end0", c - h, e0, k), ("body", e0, e1, k), ("end1", e1, c + h, k)]
        nc, nh, _ = features[(i + 1) % n]
        after = nc - nh + (360.0 if i == n - 1 else 0.0)
        if after - (c + h) > 1e-9:
            pieces.append(("gap", c + h, after, None))
    step = _circle_step(r2)
    grid = numpy.sort(numpy.mod(numpy.concatenate([_fill(a, b, step) for _, a, b, _ in pieces]), 360.0))
    at = _indexer(grid)
    inner, middle, outer = _ring(r1, grid, z), _ring(rm, grid, z), _ring(r2, grid, z)
    tris = []
    for kind, a, b, k in pieces:
        own_ang = numpy.concatenate((_fill(a, b, step), [b]))
        own = [at(x) for x in own_ang]
        if kind == "gap":
            for p, q in zip(own[:-1], own[1:]):
                for lo, hi in ((inner, middle), (middle, outer)):
                    tris.append((lo[p], hi[p], hi[q]))
                    tris.append((lo[p], hi[q], lo[q]))
            continue
        arc, s_outer, s_inner, cap0, cap1 = _slot_parts(geo, k, z)
        if kind == "body":
            arc_ang = a + numpy.mod(arc - a, 360.0)
            arc_ang[-1] = b
            tris += _strip([inner[p] for p in own], own_ang, s_inner, arc_ang)
            tris += _strip(s_outer, arc_ang, [outer[p] for p in own], own_ang)
        elif kind == "end0":
            tris += _ear_clip([inner[p] for p in own] + cap0 + [outer[p] for p in reversed(own)]
                              + [middle[own[0]]])
        else:
            tris += _ear_clip([inner[p] for p in own] + [middle[own[-1]]] + [outer[p] for p in reversed(own)]
                              + cap1)
    return (inner, grid), (outer, grid), tris


def _bands(geo):
    '''The rings holding the slots and the holes, inside out:
    (kind, inner radius, outer radius).'''
    gap = MIN_WALL_MM / 2.0
    bands = []
    if geo.slots:
        bands.append(("slots", geo.slot_radius - geo.slot_half_width - gap,
                      geo.slot_radius + geo.slot_half_width + gap))
    if geo.holes:
        bands.append(("holes", geo.hole_radius - geo.hole_size - gap, geo.hole_radius + geo.hole_size + gap))
    return sorted(bands, key=lambda band: band[1])


def _bore_angles(geo):
    return _fill(0.0, 360.0, _circle_step(geo.bore_radius))


def _face(geo, z, edge_points, edge_ang):
    '''
    Triangles of a flat face at height z: from the bore out to the
    closed ring edge_points (at edge_ang), with the slots and phasing
    holes - rings joined one to the next.
    '''
    grid = _bore_angles(geo)
    last = (_ring(geo.bore_radius, grid, z), grid)
    tris = []
    for kind, r1, r2 in _bands(geo):
        inner, outer, inside = (_hole_band if kind == "holes" else _slot_band)(geo, z, r1, r2)
        tris += _cyclic_merge(last[0], last[1], inner[0], inner[1])
        tris += inside
        last = outer
    tris += _cyclic_merge(last[0], last[1], edge_points, edge_ang)
    return tris


def _wall(lower, upper):
    '''Quads between two closed rings of the same length.'''
    tris = []
    n = len(lower)
    for i in range(n):
        j = (i + 1) % n
        tris.append((lower[i], lower[j], upper[j]))
        tris.append((lower[i], upper[j], upper[i]))
    return tris


def _orient(tris, want):
    '''numpy (N, 3, 3) of the triangles, each turned so its normal
    points along want(centroids) (N x 3).'''
    t = numpy.array(tris, dtype=float)
    normal = numpy.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    flip = numpy.einsum("ij,ij->i", normal, want(t.mean(axis=1))) < 0.0
    t[flip] = t[flip][:, ::-1]
    return t


def triangles(geo):
    '''Every triangle of the solid, numpy (N, 3, 3), normals outward.'''
    up = lambda c: numpy.tile([0.0, 0.0, 1.0], (len(c), 1))
    down = lambda c: numpy.tile([0.0, 0.0, -1.0], (len(c), 1))
    out = lambda c: numpy.column_stack((c[:, 0], c[:, 1], numpy.zeros(len(c))))
    into = lambda c: -out(c)
    ang = edge_angles(geo)[:-1]
    T = geo.thickness
    parts = []
    if geo.kind == "rock":
        r = geo.radius(ang)
        bottom, top = _polar(r, ang, 0.0), _polar(r, ang, T)
        parts.append(_orient(_face(geo, 0.0, bottom, ang), down))
        parts.append(_orient(_face(geo, T, top, ang), up))
        parts.append(_orient(_wall(bottom, top), out))
    else:
        ro, ri = geo.outer_radius, geo.inner_radius
        h = geo.top(ang)
        ob = _polar([ro] * len(ang), ang, 0.0)
        ot = [(x, y, z) for (x, y, _), z in zip(ob, h)]
        ib = _polar([ri] * len(ang), ang, T)
        it = [(x, y, z) for (x, y, _), z in zip(ib, h)]
        parts.append(_orient(_face(geo, 0.0, ob, ang), down))
        parts.append(_orient(_face(geo, T, ib, ang), up))
        parts.append(_orient(_wall(ob, ot), out))
        parts.append(_orient(_wall(ib, it), into))
        parts.append(_orient(_wall(it, ot), up))
    grid = _bore_angles(geo)
    parts.append(_orient(_wall(_ring(geo.bore_radius, grid, 0.0), _ring(geo.bore_radius, grid, T)), into))
    hole_ang = _hole_angles_about(geo)
    for cx, cy in (geo.hole_centres() if geo.holes else []):
        toward = lambda c, cx=cx, cy=cy: numpy.column_stack((cx - c[:, 0], cy - c[:, 1], numpy.zeros(len(c))))
        parts.append(_orient(_wall(_ring(geo.hole_size, hole_ang, 0.0, (cx, cy)),
                                   _ring(geo.hole_size, hole_ang, T, (cx, cy))), toward))
    for k in range(geo.slots):
        e0, e1 = _slot_ends(geo, k)
        rings = [_slot_outline(geo, k, z) for z in (0.0, T)]

        def toward(c, e0=e0, e1=e1):
            # towards the slot's middle line (its arc, or an end's centre)
            ang = numpy.degrees(numpy.arctan2(c[:, 1], c[:, 0]))
            mid = (e0 + e1) / 2.0
            ang = mid + numpy.clip(numpy.mod(ang - mid + 180.0, 360.0) - 180.0, e0 - mid, e1 - mid)
            rad = numpy.radians(ang)
            return numpy.column_stack((geo.slot_radius * numpy.cos(rad) - c[:, 0],
                                       geo.slot_radius * numpy.sin(rad) - c[:, 1], numpy.zeros(len(c))))
        parts.append(_orient(_wall(rings[0], rings[1]), toward))
    return numpy.concatenate(parts)


def stl_bytes(geo, name="Rosette"):
    '''A binary STL of the rosette (mm).'''
    t = triangles(geo)
    normal = numpy.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    length = numpy.linalg.norm(normal, axis=1)
    normal = normal / numpy.where(length > 0, length, 1.0)[:, None]
    record = numpy.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    record["n"] = normal
    record["v"] = t
    header = ("Rosetta %s (mm)" % name).encode("ascii", "replace")[:80].ljust(80, b" ")
    return header + struct.pack("<I", len(t)) + record.tobytes()


#######################################################################
# STEP (ISO 10303-21, AP214)
#######################################################################

def _real(value):
    text = "%.12G" % float(value)
    if text in ("-0", "-0."):
        text = "0"
    if "E" in text:
        mantissa, exponent = text.split("E")
        if "." not in mantissa:
            mantissa += "."
        return mantissa + "E" + exponent
    return text if "." in text else text + "."


class _Step(object):
    def __init__(self):
        self.lines = []

    def add(self, text):
        self.lines.append(text)
        return "#%d" % len(self.lines)

    def point(self, p):
        return self.add("CARTESIAN_POINT('',(%s))" % ",".join(_real(v) for v in p))

    def direction(self, d):
        return self.add("DIRECTION('',(%s))" % ",".join(_real(v) for v in d))

    def axis(self, origin, z=(0.0, 0.0, 1.0), x=(1.0, 0.0, 0.0)):
        return self.add("AXIS2_PLACEMENT_3D('',%s,%s,%s)" % (self.point(origin), self.direction(z),
                                                             self.direction(x)))

    def vertex(self, p):
        return self.add("VERTEX_POINT('',%s)" % self.point(p))

    def line_edge(self, v0, p0, v1, p1):
        delta = numpy.subtract(p1, p0)
        length = float(numpy.linalg.norm(delta))
        line = self.add("LINE('',%s,%s)" % (self.point(p0), self.add(
            "VECTOR('',%s,%s)" % (self.direction(delta / length), _real(length)))))
        return self.add("EDGE_CURVE('',%s,%s,%s,.T.)" % (v0, v1, line))

    def bspline_edge(self, v0, v1, ctrl, mults, knots):
        # closed_curve .F. even when the ends meet: the curve is clamped
        # (not periodic), with a vertex where its ends join.
        curve = self.add("B_SPLINE_CURVE_WITH_KNOTS('',3,(%s),.UNSPECIFIED.,.F.,.F.,(%s),(%s),.UNSPECIFIED.)"
                         % (",".join(self.point(p) for p in ctrl),
                            ",".join(str(m) for m in mults), ",".join(_real(k) for k in knots)))
        return self.add("EDGE_CURVE('',%s,%s,%s,.T.)" % (v0, v1, curve))

    def circle_edge(self, vertex, centre, radius, z):
        circle = self.add("CIRCLE('',%s,%s)" % (self.axis((centre[0], centre[1], z)), _real(radius)))
        return self.add("EDGE_CURVE('',%s,%s,%s,.T.)" % (vertex, vertex, circle))

    def arc_edge(self, v0, v1, centre, radius, z):
        '''Part of a circle (centre, radius, at height z), counter-clockwise from v0 to v1.'''
        circle = self.add("CIRCLE('',%s,%s)" % (self.axis((centre[0], centre[1], z)), _real(radius)))
        return self.add("EDGE_CURVE('',%s,%s,%s,.T.)" % (v0, v1, circle))

    def ruled_surface(self, lower, upper, mults, knots):
        rows = ",".join("(%s,%s)" % (self.point(a), self.point(b)) for a, b in zip(lower, upper))
        return self.add("B_SPLINE_SURFACE_WITH_KNOTS('',3,1,(%s),.UNSPECIFIED.,.F.,.F.,.F.,(%s),(2,2),(%s),"
                        "(0.,1.),.UNSPECIFIED.)" % (rows, ",".join(str(m) for m in mults),
                                                    ",".join(_real(k) for k in knots)))

    def loop(self, edges):
        '''edges: [(edge, forward)].'''
        oriented = [self.add("ORIENTED_EDGE('',*,*,%s,%s)" % (e, ".T." if f else ".F."))
                    for e, f in edges]
        return self.add("EDGE_LOOP('',(%s))" % ",".join(oriented))

    def face(self, surface, outer, inner=(), same_sense=True):
        bounds = [self.add("FACE_OUTER_BOUND('',%s,.T.)" % self.loop(outer))]
        bounds += [self.add("FACE_BOUND('',%s,.T.)" % self.loop(edges)) for edges in inner]
        return self.add("ADVANCED_FACE('',(%s),%s,%s)" % (",".join(bounds), surface,
                                                          ".T." if same_sense else ".F."))

    def text(self, solid, name):
        s = self.add
        ctx_app = s("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
        s("APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,%s)" % ctx_app)
        ctx_prod = s("PRODUCT_CONTEXT('',%s,'mechanical')" % ctx_app)
        product = s("PRODUCT('%s','%s','',(%s))" % (name, name, ctx_prod))
        s("PRODUCT_RELATED_PRODUCT_CATEGORY('part',$,(%s))" % product)
        formation = s("PRODUCT_DEFINITION_FORMATION('','',%s)" % product)
        ctx_def = s("PRODUCT_DEFINITION_CONTEXT('part definition',%s,'design')" % ctx_app)
        definition = s("PRODUCT_DEFINITION('design','',%s,%s)" % (formation, ctx_def))
        shape = s("PRODUCT_DEFINITION_SHAPE('','',%s)" % definition)
        length = s("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
        angle = s("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
        solid_angle = s("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
        accuracy = s("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-05),%s,'distance_accuracy_value',"
                     "'confusion accuracy')" % length)
        ctx = s("(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((%s))"
                "GLOBAL_UNIT_ASSIGNED_CONTEXT((%s,%s,%s))REPRESENTATION_CONTEXT('Context #1',"
                "'3D Context with UNIT and UNCERTAINTY'))" % (accuracy, length, angle, solid_angle))
        rep = s("ADVANCED_BREP_SHAPE_REPRESENTATION('%s',(%s,%s),%s)" % (name, self.axis((0, 0, 0)), solid, ctx))
        s("SHAPE_DEFINITION_REPRESENTATION(%s,%s)" % (shape, rep))
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        head = ("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Rosetta rosette - %s'),'2;1');\n"
                "FILE_NAME('%s','%s',(''),(''),'Rosetta Rosette Designer','Rosetta','');\n"
                "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n"
                % (name, name, stamp))
        body = "".join("#%d=%s;\n" % (i + 1, line) for i, line in enumerate(self.lines))
        return head + body + "ENDSEC;\nEND-ISO-10303-21;\n"


def _bspline_eval(ctrl, t, u):
    '''Points of a cubic B-spline (ctrl N x dim, full knot vector t) at u.'''
    p = 3
    n = len(ctrl)
    k = numpy.clip(numpy.searchsorted(t, u, side="right") - 1, p, n - 1)
    d = numpy.stack([ctrl[k - p + j] for j in range(p + 1)], axis=1)
    for r in range(1, p + 1):
        for j in range(p, r - 1, -1):
            i = k - p + j
            denom = t[i + p - r + 1] - t[i]
            alpha = numpy.where(denom > 0, (u - t[i]) / numpy.where(denom > 0, denom, 1.0), 0.0)
            d[:, j] = (1.0 - alpha)[:, None] * d[:, j - 1] + alpha[:, None] * d[:, j]
    return d[:, p]


def _fit(fn, error, a, b):
    '''
    A clamped cubic B-spline through fn(phi) (phi degrees, a..b, -> N x 3)
    within CURVE_TOLERANCE_MM by error(points, phi) -> N errors:
    (ctrl, mults, knots, worst error).
    '''
    count = max(8, int(math.ceil((b - a) / 2.0)))
    while True:
        m = count + 3
        inner = numpy.linspace(0.0, 1.0, m - 2)
        t = numpy.concatenate(([0.0] * 3, inner, [1.0] * 3))
        greville = (t[1:m + 1] + t[2:m + 2] + t[3:m + 3]) / 3.0
        samples = fn(a + (b - a) * greville)
        ctrl = samples.copy()
        # Pull the control points out by the curve's smoothing (uniform
        # cubic: (P[i-1] + 4 P[i] + P[i+1]) / 6), where spacing is even.
        ctrl[3:-3] = samples[3:-3] - (samples[2:-4] - 2.0 * samples[3:-3] + samples[4:-2]) / 6.0
        u = numpy.linspace(0.0, 1.0, 8 * m + 1)
        worst = float(numpy.max(error(_bspline_eval(ctrl, t, u), a, b)))
        if worst <= CURVE_TOLERANCE_MM or m >= MAX_CURVE_POINTS:
            mults = [4] + [1] * (m - 4) + [4]
            return ctrl, mults, inner, worst
        count *= 2


def _angle_of(points, a):
    '''Polar angles (degrees) of points, unwrapped to a .. a + 360.'''
    return a + numpy.mod(numpy.degrees(numpy.arctan2(points[:, 1], points[:, 0])) - a, 360.0)


def _segments(geo):
    '''(start, end) angles of the edge's smooth pieces (split at sharp points).'''
    cuts = list(geo.sharp) if len(geo.sharp) else [0.0]
    return [(a, b if b > a else b + 360.0) for a, b in zip(cuts, cuts[1:] + [cuts[0] + 360.0])]


def step_text(geo, name="Rosette"):
    '''The rosette as a STEP AP214 file (mm). Also sets geo.step_error,
    the curves' worst distance from the true shape (mm).'''
    st = _Step()
    T = geo.thickness
    faces = []
    worst = 0.0
    segs = _segments(geo)
    pieces = []
    for a, b in segs:
        if geo.kind == "rock":
            def fn(phi):
                r, rad = geo.radius(phi), numpy.radians(phi)
                return numpy.column_stack((r * numpy.cos(rad), r * numpy.sin(rad), numpy.zeros(len(phi))))

            def error(p, a, b):
                return numpy.abs(numpy.hypot(p[:, 0], p[:, 1]) - geo.radius(_angle_of(p, a)))
        else:
            ro, ri = geo.outer_radius, geo.inner_radius

            def fn(phi):
                rad = numpy.radians(phi)
                return numpy.column_stack((ro * numpy.cos(rad), ro * numpy.sin(rad), geo.top(phi)))

            def error(p, a, b):
                phi = _angle_of(p, a)
                radial = numpy.abs(numpy.hypot(p[:, 0], p[:, 1]) - ro)
                return numpy.maximum(radial, numpy.abs(p[:, 2] - geo.top(phi)))
        ctrl, mults, knots, err = _fit(fn, error, a, b)
        worst = max(worst, err)
        pieces.append((ctrl, mults, knots))
    geo.step_error = worst
    n = len(segs)
    if geo.kind == "rock":
        vb = [st.vertex((c[0][0], c[0][1], 0.0)) for c, _, _ in pieces]
        vt = [st.vertex((c[0][0], c[0][1], T)) for c, _, _ in pieces]
        eb, et, lv = [], [], []
        for s, (ctrl, mults, knots) in enumerate(pieces):
            lower = ctrl * [1, 1, 0]
            upper = lower + [0, 0, T]
            eb.append(st.bspline_edge(vb[s], vb[(s + 1) % n], lower, mults, knots))
            et.append(st.bspline_edge(vt[s], vt[(s + 1) % n], upper, mults, knots))
        for s, (ctrl, _, _) in enumerate(pieces):
            p = (ctrl[0][0], ctrl[0][1])
            lv.append(st.line_edge(vb[s], (p[0], p[1], 0.0), vt[s], (p[0], p[1], T)))
        for s, (ctrl, mults, knots) in enumerate(pieces):
            lower = ctrl * [1, 1, 0]
            surface = st.ruled_surface(lower, lower + [0, 0, T], mults, knots)
            faces.append(st.face(surface, [(eb[s], True), (lv[(s + 1) % n], True), (et[s], False),
                                           (lv[s], False)]))
        top_outer = [(e, True) for e in et]
        bottom_outer = [(e, False) for e in reversed(eb)]
    else:
        ro, ri = geo.outer_radius, geo.inner_radius
        scale_in = [ri / ro, ri / ro, 1.0]
        verts = {}
        for key, z_of in (("ob", lambda c: 0.0), ("ot", lambda c: c[2]), ("ib", lambda c: T),
                          ("it", lambda c: c[2])):
            s_xy = 1.0 if key[0] == "o" else ri / ro
            verts[key] = [st.vertex((c[0][0] * s_xy, c[0][1] * s_xy, z_of(c[0]))) for c, _, _ in pieces]
        nets = []
        e = {k: [] for k in ("ob", "ot", "ib", "it")}
        for s, (ctrl, mults, knots) in enumerate(pieces):
            ot = ctrl
            ob = ctrl * [1, 1, 0]
            it = ctrl * scale_in
            ib = it * [1, 1, 0] + [0, 0, T]
            nets.append((ob, ot, ib, it, mults, knots))
            for key, c in (("ob", ob), ("ot", ot), ("ib", ib), ("it", it)):
                e[key].append(st.bspline_edge(verts[key][s], verts[key][(s + 1) % n], c, mults, knots))
        lo, li, lr = [], [], []
        for s, (ob, ot, ib, it, _, _) in enumerate(nets):
            lo.append(st.line_edge(verts["ob"][s], ob[0], verts["ot"][s], ot[0]))
            li.append(st.line_edge(verts["ib"][s], ib[0], verts["it"][s], it[0]))
            lr.append(st.line_edge(verts["it"][s], it[0], verts["ot"][s], ot[0]))
        for s, (ob, ot, ib, it, mults, knots) in enumerate(nets):
            nxt = (s + 1) % n
            faces.append(st.face(st.ruled_surface(ob, ot, mults, knots),
                                 [(e["ob"][s], True), (lo[nxt], True), (e["ot"][s], False), (lo[s], False)]))
            faces.append(st.face(st.ruled_surface(ib, it, mults, knots),
                                 [(li[s], True), (e["it"][s], True), (li[nxt], False), (e["ib"][s], False)],
                                 same_sense=False))
            faces.append(st.face(st.ruled_surface(it, ot, mults, knots),
                                 [(lr[s], True), (e["ot"][s], True), (lr[nxt], False), (e["it"][s], False)],
                                 same_sense=False))
        top_outer = [(x, True) for x in e["ib"]]
        bottom_outer = [(x, False) for x in reversed(e["ob"])]
    # The bore and the phasing holes: cylinders, with circles on the flat faces.
    top_inner, bottom_inner = [], []
    circles = [((0.0, 0.0), geo.bore_radius)]
    if geo.holes:
        circles += [(c, geo.hole_size) for c in geo.hole_centres()]
    for centre, radius in circles:
        start_b = (centre[0] + radius, centre[1], 0.0)
        start_t = (centre[0] + radius, centre[1], T)
        vb_, vt_ = st.vertex(start_b), st.vertex(start_t)
        cb = st.circle_edge(vb_, centre, radius, 0.0)
        ct = st.circle_edge(vt_, centre, radius, T)
        seam = st.line_edge(vb_, start_b, vt_, start_t)
        cylinder = st.add("CYLINDRICAL_SURFACE('',%s,%s)" % (st.axis((centre[0], centre[1], 0.0)), _real(radius)))
        faces.append(st.face(cylinder, [(seam, True), (ct, True), (seam, False), (cb, False)], same_sense=False))
        top_inner.append([(ct, False)])
        bottom_inner.append([(cb, True)])
    # The slots: two arcs round the rosette's centre and a half circle
    # at each end - four walls, and a loop of four edges on each face.
    rs, c = geo.slot_radius, geo.slot_half_width
    for k in range(geo.slots):
        e0, e1 = (math.radians(a) for a in _slot_ends(geo, k))
        corner = lambda r, e, z: (r * math.cos(e), r * math.sin(e), z)
        ends = {}
        for z in (0.0, T):
            v = {key: st.vertex(corner(r, e, z)) for key, r, e in
                 (("o0", rs + c, e0), ("o1", rs + c, e1), ("i0", rs - c, e0), ("i1", rs - c, e1))}
            ends[z] = {
                "outer": st.arc_edge(v["o0"], v["o1"], (0.0, 0.0), rs + c, z),
                "inner": st.arc_edge(v["i0"], v["i1"], (0.0, 0.0), rs - c, z),
                "cap1": st.arc_edge(v["o1"], v["i1"], (rs * math.cos(e1), rs * math.sin(e1)), c, z),
                "cap0": st.arc_edge(v["i0"], v["o0"], (rs * math.cos(e0), rs * math.sin(e0)), c, z),
                "v": v}
        b, t = ends[0.0], ends[T]
        line = {key: st.line_edge(b["v"][key], corner(r, e, 0.0), t["v"][key], corner(r, e, T))
                for key, r, e in (("o0", rs + c, e0), ("o1", rs + c, e1), ("i0", rs - c, e0), ("i1", rs - c, e1))}
        cyl = lambda centre, radius: st.add("CYLINDRICAL_SURFACE('',%s,%s)" % (
            st.axis((centre[0], centre[1], 0.0)), _real(radius)))
        faces.append(st.face(cyl((0.0, 0.0), rs + c), [(line["o0"], True), (t["outer"], True),
                                                       (line["o1"], False), (b["outer"], False)], same_sense=False))
        faces.append(st.face(cyl((0.0, 0.0), rs - c), [(b["inner"], True), (line["i1"], True),
                                                       (t["inner"], False), (line["i0"], False)]))
        faces.append(st.face(cyl((rs * math.cos(e1), rs * math.sin(e1)), c),
                             [(line["o1"], True), (t["cap1"], True), (line["i1"], False), (b["cap1"], False)],
                             same_sense=False))
        faces.append(st.face(cyl((rs * math.cos(e0), rs * math.sin(e0)), c),
                             [(line["i0"], True), (t["cap0"], True), (line["o0"], False), (b["cap0"], False)],
                             same_sense=False))
        top_inner.append([(t["cap0"], False), (t["inner"], True), (t["cap1"], False), (t["outer"], False)])
        bottom_inner.append([(b["outer"], True), (b["cap1"], True), (b["inner"], False), (b["cap0"], True)])
    top_z = T
    faces.append(st.face(st.add("PLANE('',%s)" % st.axis((0.0, 0.0, top_z))), top_outer, top_inner))
    faces.append(st.face(st.add("PLANE('',%s)" % st.axis((0.0, 0.0, 0.0))), bottom_outer, bottom_inner,
                         same_sense=False))
    shell = st.add("CLOSED_SHELL('',(%s))" % ",".join(faces))
    solid = st.add("MANIFOLD_SOLID_BREP('%s',%s)" % (name, shell))
    return st.text(solid, name)


#######################################################################
# Names and saving
#######################################################################

def default_name(design, axis=None):
    '''e.g. Rosette-HoltzD12_rock (no extension).'''
    axis = axis or chosen_axis(design)
    ros = rr.rosettes(design)[axis]
    return "%s%s_%s" % (rr.FILE_NAME_PREFIX, rr._short(ros), "rock" if axis == "X" else "pump")


def save(design, folder, name=None, axis=None, stl=True, step=True):
    '''
    Writes name.stl / name.step to folder; returns (paths, geo). The STL
    has the printed-hole allowance added to its holes, slots and bore;
    the STEP has them at their true sizes.
    '''
    printed = Rosette3D(design, axis, printed=True)
    if printed.problems:
        raise ValueError(" ".join(printed.problems))
    geo = Rosette3D(design, printed.axis)
    name = name or default_name(design, geo.axis)
    os.makedirs(folder, exist_ok=True)
    paths = []
    if stl:
        path = os.path.join(folder, name + ".stl")
        with open(path, "wb") as f:
            f.write(stl_bytes(printed, name))
        paths.append(path)
    if step:
        path = os.path.join(folder, name + ".step")
        with open(path, "w") as f:
            f.write(step_text(geo, name))
        paths.append(path)
    return paths, geo


#######################################################################
# Samples (python3 rosetta_rosette_3d.py <folder>)
#######################################################################

def sample_designs():
    '''(name, design) for the samples: every shape rocking, some pumping,
    an ellipse with waves, the MDF A-8, other mountings, inch and mm.'''
    found = []
    for shape in rr.SHAPE_IDS:
        if shape in ("none", "ellipse"):
            continue
        found.append(("%s_rock" % shape, {"shape": shape, "lobes": rr.SAMPLE_LOBES.get(shape, 8),
                                          "amplitude": 0.1, "motion": "rock"}))
    for shape in ("sine", "holtz_d", "lotus", "tudor"):
        found.append(("%s_pump" % shape, {"shape": shape, "lobes": 12, "amplitude": 0.1, "motion": "pump",
                                          "print_axis": "Z"}))
    found.append(("mdf_a8_rock", {"shape": "sine", "lobes": 8, "amplitude": 0.1}))
    found.append(("ellipse_holtz_d_rock", {"shape": "ellipse", "wrap_shape": "holtz_d", "wrap_lobes": 12,
                                           "wrap_amplitude": 0.05, "ellipse_a": 1.0, "ellipse_b": 0.6,
                                           "motion": "rock", "print_diameter": 7.0,
                                           "print_diameter_at": "largest", "print_hole_circle": 5.6}))
    found.append(("sine_rock_plain", {"shape": "sine", "lobes": 12, "amplitude": 0.1, "print_holes": 0,
                                      "print_slots": 0}))
    found.append(("sine_rock_even_noslots", {"shape": "sine", "lobes": 12, "amplitude": 0.1, "print_slots": 0,
                                             "print_hole_layout": "even", "print_holes": 12}))
    found.append(("holtz_d_rock_3slots", {"shape": "holtz_d", "lobes": 6, "amplitude": 0.1, "print_slots": 3,
                                          "print_slot_span": 60.0}))
    found.append(("holtz_f1_rock_mm", {"shape": "holtz_f", "lobes": 1, "amplitude": 6.0, "units": "mm",
                                       "print_diameter": 150.0, "print_thickness": 8.0, "print_bore": 25.0,
                                       "print_holes": 9, "print_hole_circle": 120.0,
                                       "print_hole_diameter": 3.3, "print_slots": 2,
                                       "print_slot_circle": 90.0, "print_slot_width": 6.8,
                                       "print_hole_allowance": 0.2, "print_rim_width": 10.0}))
    return [(name, rr.clean_design(d)) for name, d in found]


def write_samples(folder):
    written = []
    for name, design in sample_designs():
        paths, geo = save(design, folder, name)
        written.append("%s  (STEP within %.4f mm)" % (", ".join(os.path.basename(p) for p in paths),
                                                       geo.step_error))
    return written


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 rosetta_rosette_3d.py <folder for sample files>")
        sys.exit(1)
    print("\n".join(write_samples(sys.argv[1])))
