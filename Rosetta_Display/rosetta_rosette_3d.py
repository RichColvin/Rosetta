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
#   falls with it. Both have a centre bore and an optional ring of
#   phasing holes, the first at the pattern's start (0 degrees).
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

# Starting values for the rosette's size, by machine (Rich, 15 November
# 2026): (name, diameter in inches, measured at its "largest" or
# "smallest"). "other" keeps whatever is entered.
MACHINES = {
    "mdf": ("MDF Rose Engine", 7.0, "smallest"),
    "armbruster": ("Armbruster Mark II", 7.0, "largest"),
    "lindow": ("Lindow", 5.0, "largest"),
    "other": ("Other", None, None),
}

MESH_TOLERANCE_MM = 0.01        # STL: straight pieces within this of the true shape
CURVE_TOLERANCE_MM = 0.002      # STEP: its curves within this of the true shape
MAX_STEP_DEG = 1.0              # STL: no piece of an edge turns more than this
MIN_WALL_MM = 1.0               # least plastic between holes, the bore and the edge
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
    '''(diameter in the design's units, "largest"/"smallest") for a
    machine, or None for "other".'''
    name, diameter, at = MACHINES[machine]
    if diameter is None:
        return None
    return _from_mm(design, diameter * MM_PER_INCH), at


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
    outer_radius. problems block saving; warnings don't.
    '''

    def __init__(self, design, axis=None):
        d = rr.clean_design(design)
        self.design = d
        self.axis = axis or chosen_axis(d)
        self.kind = "rock" if self.axis == "X" else "pump"
        self.ros = rr.rosettes(d)[self.axis]
        self.ratio = d["print_ratio"]
        self.thickness = _to_mm(d, d["print_thickness"])
        self.bore_radius = _to_mm(d, d["print_bore"]) / 2.0
        self.holes = d["print_holes"]
        self.hole_radius = _to_mm(d, d["print_hole_radius"])
        self.hole_size = _to_mm(d, d["print_hole_diameter"]) / 2.0     # a hole's radius
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
        '''How far out the bore and holes may reach: the edge's smallest
        radius (rocking) or the rim's inside (pumping).'''
        return self.smallest if self.kind == "rock" else self.inner_radius

    def hole_centres(self):
        angles = numpy.radians(numpy.arange(self.holes) * 360.0 / max(self.holes, 1))
        return [(self.hole_radius * math.cos(a), self.hole_radius * math.sin(a)) for a in angles]

    def wave_mm(self):
        return self.high - self.low

    # -- checks -------------------------------------------------------

    def _check(self):
        problems, warnings = [], []
        mm = lambda v: _from_mm(self.design, v)
        unit = "\"" if self.design["units"] == "inch" else " mm"
        show = lambda v: ("%.3f" % mm(v)).rstrip("0").rstrip(".") + unit
        if self.thickness <= 0.0:
            problems.append("The thickness must be more than 0.")
        if self.bore_radius <= 0.0:
            problems.append("The rosette needs a centre bore.")
        if self.kind == "rock":
            if self.smallest <= 0.0:
                problems.append("The wave (amplitude x ratio) is bigger than the rosette - make the "
                                "diameter larger or the ratio smaller.")
                return problems, warnings
        else:
            if self.inner_radius <= 0.0:
                problems.append("The rim is wider than the rosette.")
                return problems, warnings
        inside = self.edge_inside()
        where = "the edge's smallest radius" if self.kind == "rock" else "the rim"
        if self.holes:
            if self.hole_size <= 0.0:
                problems.append("The phasing holes need a size.")
            inner = self.hole_radius - self.hole_size - MIN_WALL_MM
            outer = self.hole_radius + self.hole_size + MIN_WALL_MM
            if inner < self.bore_radius:
                problems.append("The phasing holes run into the bore - put them further out "
                                "(their radius at least %s)." % show(self.bore_radius + self.hole_size + MIN_WALL_MM))
            if outer > inside:
                problems.append("The phasing holes run into %s (%s) - put them further in or "
                                "make them smaller." % (where, show(inside)))
            if self.holes >= 2:
                gap = 2.0 * self.hole_radius * math.sin(math.pi / self.holes) - 2.0 * self.hole_size
                if gap < MIN_WALL_MM:
                    problems.append("The phasing holes overlap - use fewer, smaller ones, or a "
                                    "larger radius.")
        elif self.bore_radius + MIN_WALL_MM > inside:
            problems.append("The bore runs into %s (%s)." % (where, show(inside)))
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


def _face(geo, z, edge_points, edge_ang):
    '''
    Triangles of a flat face at height z: from the bore out to the
    closed ring edge_points (at edge_ang), with the phasing holes.
    '''
    tris = []
    if not geo.holes:
        grid = _fill(0.0, 360.0, _circle_step(geo.bore_radius))
        bore = _ring(geo.bore_radius, grid, z)
        return _cyclic_merge(bore, grid, edge_points, edge_ang)
    gap = MIN_WALL_MM / 2.0
    r1 = geo.hole_radius - geo.hole_size - gap
    r2 = geo.hole_radius + geo.hole_size + gap
    pitch = 360.0 / geo.holes
    half = min(pitch / 2.0, 0.8 * math.degrees(math.acos(min(r1 / geo.hole_radius, 1.0))))
    # Each hole's sector, and the plain gaps between them.
    pieces = []
    for k in range(geo.holes):
        centre = k * pitch
        pieces.append(("hole", centre - half, centre + half, k))
        if pitch / 2.0 - half > 1e-9:
            pieces.append(("gap", centre + half, centre + pitch - half, None))
    step = min(_circle_step(r2), _circle_step(geo.bore_radius) * 4)
    grid = []           # angles on the bore and the band's two circles
    for kind, a, b, _ in pieces:
        grid.extend(_fill(a, b, step))
    grid = numpy.array(grid)
    # Start at 0 (the first hole's sector starts at -half).
    order = numpy.argsort(numpy.mod(grid, 360.0))
    grid_mod = numpy.mod(grid, 360.0)[order]
    bore = _ring(geo.bore_radius, grid_mod, z)
    inner = _ring(r1, grid_mod, z)
    outer = _ring(r2, grid_mod, z)
    tris += _cyclic_merge(bore, grid_mod, inner, grid_mod)
    tris += _cyclic_merge(outer, grid_mod, edge_points, edge_ang)
    # Look-up from an (unwrapped) angle to its index in grid_mod.
    index = {round(a, 9): i for i, a in enumerate(grid_mod)}

    def at(angle):
        return index[round(float(numpy.mod(angle, 360.0)), 9)]

    for kind, a, b, k in pieces:
        own = [at(x) for x in _fill(a, b, step)] + [at(b)]
        if kind == "gap":
            for p, q in zip(own[:-1], own[1:]):
                tris.append((inner[p], outer[p], outer[q]))
                tris.append((inner[p], outer[q], inner[q]))
            continue
        # The sector's outline, counter-clockwise, and the hole in it,
        # joined round the hole's centre.
        cx, cy = geo.hole_centres()[k]
        outline = [inner[own[0]]] + [outer[p] for p in own] + [inner[p] for p in reversed(own[1:])]
        ang = numpy.degrees(numpy.arctan2([p[1] - cy for p in outline], [p[0] - cx for p in outline]))
        start = int(numpy.argmin(ang))
        outline = outline[start:] + outline[:start]
        ang = numpy.concatenate((ang[start:], ang[:start]))
        ang = ang[0] + numpy.mod(ang - ang[0], 360.0)
        hole_ang = numpy.sort(numpy.mod(_fill(0.0, 360.0, _circle_step(geo.hole_size)) - 180.0 + 1e-6, 360.0) - 180.0)
        hole = _ring(geo.hole_size, hole_ang, z, (cx, cy))
        tris += _cyclic_merge(hole, hole_ang, outline, ang)
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
        ob, ot = _polar([ro] * len(ang), ang, 0.0), [(x, y, z) for (x, y, _), z in zip(_polar([ro] * len(ang), ang, 0.0), h)]
        ib, it = _polar([ri] * len(ang), ang, T), [(x, y, z) for (x, y, _), z in zip(_polar([ri] * len(ang), ang, T), h)]
        parts.append(_orient(_face(geo, 0.0, ob, ang), down))
        parts.append(_orient(_face(geo, T, ib, ang), up))
        parts.append(_orient(_wall(ob, ot), out))
        parts.append(_orient(_wall(ib, it), into))
        parts.append(_orient(_wall(it, ot), up))
    grid = _fill(0.0, 360.0, _circle_step(geo.bore_radius))
    if geo.holes:
        # The bore's points must be the ones _face put on it.
        grid = _bore_grid(geo)
    parts.append(_orient(_wall(_ring(geo.bore_radius, grid, 0.0), _ring(geo.bore_radius, grid, T)), into))
    for cx, cy in geo.hole_centres() if geo.holes else []:
        hole_ang = numpy.sort(numpy.mod(_fill(0.0, 360.0, _circle_step(geo.hole_size)) - 180.0 + 1e-6, 360.0) - 180.0)
        toward = lambda c, cx=cx, cy=cy: numpy.column_stack((cx - c[:, 0], cy - c[:, 1], numpy.zeros(len(c))))
        parts.append(_orient(_wall(_ring(geo.hole_size, hole_ang, 0.0, (cx, cy)),
                                   _ring(geo.hole_size, hole_ang, T, (cx, cy))), toward))
    return numpy.concatenate(parts)


def _bore_grid(geo):
    '''The angles _face uses on the bore when there are holes.'''
    gap = MIN_WALL_MM / 2.0
    r1 = geo.hole_radius - geo.hole_size - gap
    r2 = geo.hole_radius + geo.hole_size + gap
    pitch = 360.0 / geo.holes
    half = min(pitch / 2.0, 0.8 * math.degrees(math.acos(min(r1 / geo.hole_radius, 1.0))))
    step = min(_circle_step(r2), _circle_step(geo.bore_radius) * 4)
    grid = []
    for k in range(geo.holes):
        centre = k * pitch
        grid.extend(_fill(centre - half, centre + half, step))
        if pitch / 2.0 - half > 1e-9:
            grid.extend(_fill(centre + half, centre + pitch - half, step))
    return numpy.sort(numpy.mod(numpy.array(grid), 360.0))


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
    '''Writes name.stl / name.step to folder; returns (paths, geo).'''
    geo = Rosette3D(design, axis)
    if geo.problems:
        raise ValueError(" ".join(geo.problems))
    name = name or default_name(design, geo.axis)
    os.makedirs(folder, exist_ok=True)
    paths = []
    if stl:
        path = os.path.join(folder, name + ".stl")
        with open(path, "wb") as f:
            f.write(stl_bytes(geo, name))
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
    an ellipse with waves, inch and mm.'''
    found = []
    for shape in rr.SHAPE_IDS:
        if shape in ("none", "ellipse"):
            continue
        found.append(("%s_rock" % shape, {"shape": shape, "lobes": rr.SAMPLE_LOBES.get(shape, 8),
                                          "amplitude": 0.1, "motion": "rock"}))
    for shape in ("sine", "holtz_d", "lotus", "tudor"):
        found.append(("%s_pump" % shape, {"shape": shape, "lobes": 12, "amplitude": 0.1, "motion": "pump",
                                          "print_axis": "Z"}))
    found.append(("ellipse_holtz_d_rock", {"shape": "ellipse", "wrap_shape": "holtz_d", "wrap_lobes": 12,
                                           "wrap_amplitude": 0.05, "ellipse_a": 1.0, "ellipse_b": 0.6,
                                           "motion": "rock", "print_diameter": 7.0,
                                           "print_diameter_at": "largest"}))
    found.append(("sine_rock_noholes", {"shape": "sine", "lobes": 12, "amplitude": 0.1, "print_holes": 0}))
    found.append(("holtz_f1_rock_mm", {"shape": "holtz_f", "lobes": 1, "amplitude": 6.0, "units": "mm",
                                       "print_diameter": 150.0, "print_thickness": 8.0, "print_bore": 25.0,
                                       "print_holes": 6, "print_hole_radius": 40.0,
                                       "print_hole_diameter": 6.0, "print_rim_width": 10.0}))
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
