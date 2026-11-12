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
#   Axis not available (11 November 2026): a program using an axis
#   this session doesn't have at all (not assigned, or on an Expansion
#   Box that isn't connected) gets Rosetta's explanation as it opens
#   instead of AXIS's "Bad character" error, and Run/Step are refused -
#   see "Axes a program uses that this session doesn't have" below.
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
#   1.2 - 11 November 2026 - programs using an axis this session
#         doesn't have get an explanation and can't be run
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


def _rosetta_read_settings():
    '''
    RosettaSet_v1.ini as a dict ({} if it can't be read). The file is
    JSON wrapped in "#" comment lines (see rosetta_settings_io.py, not
    importable from inside AXIS). Rosetta Settings can't run while
    LinuxCNC does, so reading it once as AXIS starts is enough.
    '''
    import json
    try:
        with open(os.path.expanduser("~/Documents/RosettaSet_v1.ini")) as f:
            text = "\n".join(l for l in f.read().splitlines() if not l.lstrip().startswith("#"))
        settings = json.loads(text)
        return settings if isinstance(settings, dict) else {}
    except Exception:
        return {}


ROSETTA_SETTINGS = _rosetta_read_settings()


def _rosetta_not_enabled_action():
    '''RosettaSet_v1.ini's "not_enabled_action" - "ask" (default) or "enable".'''
    choice = ROSETTA_SETTINGS.get("not_enabled_action", "ask")
    return choice if choice in ("ask", "enable") else "ask"


ROSETTA_NOT_ENABLED_ACTION = _rosetta_not_enabled_action()


# ---------------------------------------------------------------------
# Axes a program uses that this session doesn't have (11 November 2026)
#
# An axis letter not in this session's coordinates - not assigned to a
# channel, or on the Expansion Box while Rosetta Settings says it isn't
# connected - makes LinuxCNC's interpreter stop with "Bad character
# 'c' used". AXIS shows that as it loads the program, which doesn't say
# what's wrong, and still lets the program run, which then stops at the
# same line, possibly after other axes have moved. So the preview's
# result is checked here: an unavailable axis gets a message saying
# which axes, why, and what to change in Rosetta Settings (in place of
# AXIS's), and Run/Step are refused until a program without them is
# loaded. The interpreter stops at the first such letter, so the rest
# of the file is also scanned for others to name in the message.
# ---------------------------------------------------------------------

ROSETTA_EXPANSION_CHANNELS = ("06", "07", "08", "09")
ROSETTA_BAD_CHARACTER = re.compile(r"Bad character '([A-Za-z])' used")
ROSETTA_OWORD_KEYWORDS = re.compile(
    r"\b(ENDWHILE|WHILE|ENDIF|ELSEIF|ELSE|IF|ENDSUB|SUB|CALL|RETURN|DO|"
    r"BREAK|CONTINUE|ENDREPEAT|REPEAT)\b")
ROSETTA_AXIS_WORD = re.compile(r"([XYZABCUVW])\s*[-+.0-9\[#]")

rosetta_unavailable = None      # {"letters": [...], "line": n} for the loaded program


def rosetta_session_letters():
    '''The axis letters in this session's coordinates.'''
    s.poll()
    return set(letter for i, letter in enumerate(ROSETTA_AXIS_LETTERS)
               if s.axis_mask & (1 << i))


def rosetta_axis_words_in_file(path):
    '''
    Axis letters used as words anywhere in the file - a best-effort
    scan, used only to name every missing axis in the message, never to
    decide whether a program can run. Comments, named parameters,
    bracketed expressions (COS, ...) and o-word keywords (CALL, ...)
    are removed first so their letters aren't counted.
    '''
    found = set()
    try:
        with open(path, errors="replace") as f:
            lines = f.read().upper().splitlines()
    except Exception:
        return found
    for line in lines:
        line = re.sub(r"\([^)]*\)", " ", line).split(";", 1)[0]
        line = re.sub(r"#<[^>]*>", "#1", line)
        while True:             # innermost brackets first
            stripped = re.sub(r"\[[^\[\]]*\]", "[]", line)
            if stripped == line:
                break
            line = stripped
        line = re.sub(r"O\s*(<[^>]*>|\d+)", " ", line)
        line = ROSETTA_OWORD_KEYWORDS.sub(" ", line)
        found.update(ROSETTA_AXIS_WORD.findall(line))
    return found


def rosetta_axis_reason(letter):
    '''Why letter isn't in this session, from RosettaSet_v1.ini.'''
    if letter == "Y":
        return "Rosetta doesn't use a Y axis (it is set up as a lathe)."
    assignments = ROSETTA_SETTINGS.get("channel_assignments") or {}
    channels = sorted(ch for ch, role in assignments.items() if role == letter)
    if channels and not ROSETTA_SETTINGS.get("expansion_box", False) \
            and all(ch in ROSETTA_EXPANSION_CHANNELS for ch in channels):
        return (letter + " is on channel " + channels[0] + ", on the Expansion Box, "
                "but Rosetta Settings says the Expansion Box isn't connected.")
    return letter + " isn't assigned to a channel."


def rosetta_unavailable_text(problem, running):
    letters = problem["letters"]
    names = _rosetta_names(letters)
    one = len(letters) == 1
    reasons = [rosetta_axis_reason(letter) for letter in letters]
    on_expansion = any("Expansion Box" in reason for reason in reasons)
    text = ("This program uses " + names + " (near line " + str(problem["line"]) + "), but "
            + ("it isn't" if one else "they aren't") + " available on this machine as it is set up now:\n\n")
    text += "\n".join("  " + reason for reason in reasons)
    text += ("\n\n" + ("The program can't be run.  " if running else "")
             + "To use " + names + ", close LinuxCNC and open Rosetta Settings.  ")
    if on_expansion:
        text += ("If the Expansion Box is plugged in, tick Expansion Box Connected on the "
                 "Axis Selection page.  If it isn't, move " + ("the axis" if one else "the axes")
                 + " to a Base Box channel on that page.")
    else:
        text += ("On the Axis Selection page, assign " + ("it" if one else "them")
                 + " to a channel.")
    text += "  Then start LinuxCNC again and open the program."
    return text


def rosetta_show_unavailable(problem, running):
    names = _rosetta_names(problem["letters"])
    root_window.tk.call("nf_dialog", ".error", names + " not available",
                        rosetta_unavailable_text(problem, running), "error", 0, "OK")


_rosetta_load_preview = o.load_preview


def rosetta_load_preview(f, canon, *args):
    '''
    AXIS's preview load, then the unavailable-axes check. If the
    interpreter stopped on an axis letter this session doesn't have,
    shows Rosetta's message and returns a no-error result so AXIS
    doesn't show its own "Bad character" one as well (the preview has
    already handled the real result by then).
    '''
    global rosetta_unavailable
    rosetta_unavailable = None
    result, seq = _rosetta_load_preview(f, canon, *args)
    if result <= gcode.MIN_ERROR:
        return result, seq
    try:
        match = ROSETTA_BAD_CHARACTER.search(gcode.strerror(result) or "")
        letter = match.group(1).upper() if match else None
        session = rosetta_session_letters()
        if letter not in ROSETTA_AXIS_LETTERS or letter in session:
            return result, seq
        others = rosetta_axis_words_in_file(f) - session
        letters = [l for l in ROSETTA_AXIS_LETTERS if l == letter or l in others]
        rosetta_unavailable = {"letters": letters, "line": seq}
        rosetta_show_unavailable(rosetta_unavailable, False)
        return gcode.MIN_ERROR, seq
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        return result, seq


o.load_preview = rosetta_load_preview


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
    if rosetta_unavailable:
        rosetta_show_unavailable(rosetta_unavailable, True)
        return 3
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
