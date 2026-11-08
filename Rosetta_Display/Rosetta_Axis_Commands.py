#######################################################################
#   RRRRRR    OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT    AA       #
#   RR   RR  OO    OO SS       EE          TT       TT      AAAA      #
#   RR   RR  OO    OO SS       EE          TT       TT     AA  AA     #
#   RRRRRR   OO    OO  SSSSSS  EEEEEE      TT       TT    AA    AA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AAAAAAAA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AA    AA    #
#   RR    RR  OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA    #
#                                                                     #
# Rosetta                                                             #
#######################################################################
#
# File:
#   Rosetta_Axis_Commands.py
#
# Purpose:
#   Extra commands for AXIS, named by Rosetta.ini's
#   [DISPLAY]USER_COMMAND_FILE. AXIS runs this file inside its own
#   program as it starts (the same way it would run ~/.axisrc), so
#   everything here can use AXIS's own names - root_window, s (its
#   linuxcnc.stat), o (the preview) and run_warn.
#
#   AXIS reads USER_COMMAND_FILE *instead of* ~/.axisrc, so this file
#   first runs ~/.axisrc itself, keeping the window size and other
#   settings the installer put there (and anything the owner added).
#
#   Warn before running with an axis not enabled (08 November 2026):
#   a program that moves an axis whose ENA button is off ends in a
#   "following error" as soon as that axis has to move - the stepgen
#   doesn't step, so the axis falls behind. Before a run starts, the
#   check below looks through AXIS's preview of the loaded program for
#   every axis it moves, and if any of them isn't enabled on the
#   Rosetta panel, says which ones and offers Cancel (the default) or
#   Run Anyway. It is added to AXIS's own run_warn (the "Program
#   exceeds machine limits" check), so it covers Run, Run From Line
#   and Step, and it runs before anything moves.
#
#   How a move is seen: the preview (rs274.glcanon) lists every
#   traverse, feed and arc segment with its start and end in all nine
#   axes (X Y Z A B C U V W). An axis counts as moved if any segment
#   changes it. Limits: rapids before the program's first feed move
#   aren't in the preview's lists (glcanon skips them), a program cut
#   short by [DISPLAY]PREVIEW_TIMEOUT is only checked as far as the
#   preview got, and spindles (M3/M4/M19) aren't checked.
#
#   An axis's ENA state is the "<letter>-ena-and.out" pin in
#   Rosetta_PostGUI_v1.hal - the panel's ENA toggle AND Rosetta
#   Settings' override - read with hal.get_value. Only axes in this
#   session's coordinates (s.axis_mask) are checked.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.  Put your own AXIS settings in ~/.axisrc instead -
#   this file runs it first.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 08 November 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

# Keep the owner's ~/.axisrc working - AXIS no longer reads it itself
# once USER_COMMAND_FILE is set.
_rosetta_axisrc = os.path.expanduser("~/.axisrc")
if os.path.exists(_rosetta_axisrc):
    try:
        exec(compile(open(_rosetta_axisrc, "rb").read(), _rosetta_axisrc, "exec"))
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        root_window.tk.call("nf_dialog", ".error", "Error in ~/.axisrc",
                            traceback.format_exc(), "error", 0, "OK")

ROSETTA_AXIS_LETTERS = "XYZABCUVW"      # the preview's order
ROSETTA_MOVE_TOLERANCE = 1e-6


def rosetta_axes_moved():
    '''
    Set of axis letters the previewed program moves, or None if there
    is no preview to look at.
    '''
    canon = getattr(o, "canon", None)
    if canon is None:
        return None
    moved = set()
    for segments in (canon.traverse, canon.feed, canon.arcfeed):
        for segment in segments:
            start, end = segment[1], segment[2]
            for i, letter in enumerate(ROSETTA_AXIS_LETTERS):
                if letter not in moved and i < len(start) and i < len(end) \
                        and abs(end[i] - start[i]) > ROSETTA_MOVE_TOLERANCE:
                    moved.add(letter)
        if len(moved) == len(ROSETTA_AXIS_LETTERS):
            break
    return moved


def rosetta_axes_not_enabled(letters):
    '''Those of letters in this session whose ENA is off on the panel.'''
    s.poll()
    off = []
    for i, letter in enumerate(ROSETTA_AXIS_LETTERS):
        if letter not in letters or not (s.axis_mask & (1 << i)):
            continue
        try:
            if not hal.get_value(letter.lower() + "-ena-and.out"):
                off.append(letter)
        except Exception:
            pass        # no such pin - nothing to check
    return off


_rosetta_axis_run_warn = run_warn


def run_warn():
    '''
    AXIS's own check first (machine limits: 0 run, 1 re-check, 2 run
    anyway, 3 cancel), then the axes-not-enabled check - returning 2
    (Run Anyway) or 3 (Cancel) the same way.
    '''
    result = _rosetta_axis_run_warn()
    if result in (1, 3):
        return result
    try:
        moved = rosetta_axes_moved()
        off = rosetta_axes_not_enabled(moved) if moved else []
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        return result
    if not off:
        return result
    names = off[0] if len(off) == 1 else ", ".join(off[:-1]) + " and " + off[-1]
    verb = "is" if len(off) == 1 else "are"
    text = ("This program moves " + names + ", which " + verb + " not enabled.\n\n"
            "Click the ENA " + ("button" if len(off) == 1 else "buttons") + " for "
            + names + " on the Rosetta panel, "
            "then click Run again.\n\n"
            "If you run it anyway, it will stop with a following error "
            "as soon as " + names + " " + ("has" if len(off) == 1 else "have")
            + " to move.")
    answer = int(root_window.tk.call("nf_dialog", ".error",
                                     names + " not enabled", text, "warning",
                                     1, "Run Anyway", "Cancel"))
    return 2 if answer == 0 else 3
