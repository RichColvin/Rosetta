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
#   Rosetta panel, says which ones and offers Enable and Run (the
#   default) or Cancel. It is added to AXIS's own run_warn (the
#   "Program exceeds machine limits" check), so it covers Run, Run From
#   Line and Step, and it runs before anything moves.
#
#   09 November 2026 (Rich): "Run Anyway" became "Enable <axes> and
#   Run", which turns the ENA on the way clicking the ENA button does
#   (pulses "<letter>-ena-flip.set") then runs. Rosetta Settings > Other
#   > Axis Not Enabled ("not_enabled_action" in RosettaSet_v1.ini, read
#   once as AXIS starts) can instead enable them automatically, with
#   only a note in AXIS's notification area. An axis Rosetta Settings'
#   override still blocks stays off, and the run is cancelled.
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
#   1.1 - 09 November 2026 - Enable and Run instead of Run Anyway;
#         optional automatic enable
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
ROSETTA_ENABLE_WAIT_SECONDS = 1.0


def _rosetta_not_enabled_action():
    '''
    RosettaSet_v1.ini's "not_enabled_action" - "ask" (default) or
    "enable". The file is JSON wrapped in "#" comment lines (see
    rosetta_settings_io.py, not importable from inside AXIS).
    '''
    import json
    try:
        with open(os.path.expanduser("~/Documents/RosettaSet_v1.ini")) as f:
            text = "\n".join(l for l in f.read().splitlines() if not l.lstrip().startswith("#"))
        choice = json.loads(text).get("not_enabled_action", "ask")
    except Exception:
        choice = "ask"
    return choice if choice in ("ask", "enable") else "ask"


ROSETTA_NOT_ENABLED_ACTION = _rosetta_not_enabled_action()


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


def rosetta_enable_axes(letters):
    '''
    Turns on each axis's ENA as its ENA button would (pulses
    "<letter>-ena-flip.set"), then waits up to
    ROSETTA_ENABLE_WAIT_SECONDS for it to come on. Returns the letters
    still off.
    '''
    import subprocess
    for letter in letters:
        pin = letter.lower() + "-ena-flip.set"
        try:
            subprocess.run(["halcmd", "setp", pin, "TRUE"], check=True, capture_output=True)
            subprocess.run(["halcmd", "setp", pin, "FALSE"], check=True, capture_output=True)
        except Exception:
            print("Rosetta: could not pulse " + pin, file=sys.stderr)
    deadline = time.monotonic() + ROSETTA_ENABLE_WAIT_SECONDS
    while True:
        still_off = rosetta_axes_not_enabled(letters)
        if not still_off or time.monotonic() > deadline:
            return still_off
        time.sleep(0.02)


def _rosetta_names(letters):
    return letters[0] if len(letters) == 1 else ", ".join(letters[:-1]) + " and " + letters[-1]


def rosetta_ask_enable(names, one):
    '''
    The "<names> not enabled" box: True for Enable and Run (the
    default - Return), False for Cancel (Escape, or closing it). A
    plain Tk dialog rather than AXIS's nf_dialog, whose buttons are a
    fixed 10 characters wide.
    '''
    import tkinter
    answer = {"enable": False}
    top = tkinter.Toplevel(root_window)
    top.title(names + " not enabled")
    top.transient(root_window)
    top.resizable(False, False)
    text = ("This program moves " + names + ", which " + ("is" if one else "are")
            + " not enabled.\n\n"
            "Enable and Run turns " + ("its ENA" if one else "their ENAs") + " on - the same as "
            "clicking the ENA " + ("button" if one else "buttons") + " on the Rosetta panel - "
            "then runs the program.  Cancel leaves " + ("it" if one else "them")
            + " off and doesn't run.")
    tkinter.Label(top, text=text, wraplength=420, justify="left").pack(padx=16, pady=(16, 8))
    row = tkinter.Frame(top)
    row.pack(padx=16, pady=(0, 16), anchor="e")

    def choose(enable):
        answer["enable"] = enable
        top.destroy()
    go = tkinter.Button(row, text="Enable " + names + " and Run", default="active",
                        command=lambda: choose(True))
    go.pack(side="left", padx=4)
    tkinter.Button(row, text="Cancel", command=lambda: choose(False)).pack(side="left", padx=4)
    top.bind("<Return>", lambda e: choose(True))
    top.bind("<Escape>", lambda e: choose(False))
    top.protocol("WM_DELETE_WINDOW", lambda: choose(False))
    top.update_idletasks()
    x = root_window.winfo_rootx() + (root_window.winfo_width() - top.winfo_reqwidth()) // 2
    y = root_window.winfo_rooty() + (root_window.winfo_height() - top.winfo_reqheight()) // 3
    top.geometry("+%d+%d" % (max(x, 0), max(y, 0)))
    go.focus_set()
    top.grab_set()
    top.wait_window()
    return answer["enable"]


_rosetta_axis_run_warn = run_warn


def run_warn():
    '''
    AXIS's own check first (machine limits: 0 run, 1 re-check, 2 run
    anyway, 3 cancel), then the axes-not-enabled check: enables them
    (asked, or automatically) and returns AXIS's own result, or
    returns 3 (cancel).
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
    names = _rosetta_names(off)
    if ROSETTA_NOT_ENABLED_ACTION != "enable" and not rosetta_ask_enable(names, len(off) == 1):
        return 3
    still_off = rosetta_enable_axes(off)
    if still_off:
        names = _rosetta_names(still_off)
        root_window.tk.call("nf_dialog", ".error", names + " not enabled",
                            names + " could not be enabled.  Click the ENA "
                            + ("button" if len(still_off) == 1 else "buttons") + " for "
                            + names + " on the Rosetta panel, then click Run again.",
                            "warning", 0, "OK")
        return 3
    if ROSETTA_NOT_ENABLED_ACTION == "enable":
        try:
            notifications.add("info", "Enabled " + names + " for this program.")
        except Exception:
            pass
    return result
