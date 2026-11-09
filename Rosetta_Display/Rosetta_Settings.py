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
#   Rosetta_Settings.py
#
# Purpose:  Standalone external configurator for Rosetta.
#   Replaces the Settings tab that used to be embedded inside
#   LinuxCNC's AXIS GUI via gladevcp - this is a plain, independently
#   launched GTK program (see Rosetta_Settings.sh) that loads
#   Rosetta_Settings_v1.ui directly, with no HAL component of its own.
#   Every live HAL read/write goes through `halcmd getp/setp/gets/sets`
#   subprocess calls, so this program works whether or not LinuxCNC
#   happens to be running at the time (the halcmd calls simply fail
#   harmlessly if it isn't).
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 04 September 2026
#   1.1 - 09 November 2026 - File menu: Back Up to USB, Restore from USB
#   1.2 - 09 November 2026 - Other page: Axis Not Enabled (Ask or
#         Enable it automatically); Measurement System moved last
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

import os
import time
import subprocess
import shutil
import re
import json
import contextlib
import webbrowser
import linuxcnc
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk

@contextlib.contextmanager
def _suppress_fd2():
    '''
    Silences writes to OS file descriptor 2 (stderr) for the duration
    of the `with` block - needed because gladevcp.hal_widgets (imported
    below) and linuxcnc.stat().poll() (see _linuxcnc_is_running further
    down) both print harmless diagnostic noise ("tool_mmap_user(): tool
    mmap not available" / "poll(): continuing without tool mmap data")
    straight to the raw fd from C code, which a plain Python-level
    contextlib.redirect_stderr can't catch (it only reassigns sys.
    stderr's object reference, not the underlying OS fd the C code
    writes to - confirmed by testing both approaches live 4 September
    2026). This also happens to swallow gladevcp's own "Logging to:
    ..." console line, since Python's logging.StreamHandler writes
    through sys.stderr, which is itself backed by this same fd absent
    a full reassignment.

    Scoped narrowly to each specific call site (the gladevcp import,
    and _linuxcnc_is_running's poll()) rather than left in place
    permanently, since it would just as easily hide a real error
    printed to stderr during whatever's wrapped in `with` - fine for a
    known-noisy, already-handled call, not something to reach for
    generally.
    '''
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    saved_fd = os.dup(2)
    os.dup2(devnull_fd, 2)
    try:
        yield
    finally:
        os.dup2(saved_fd, 2)
        os.close(saved_fd)
        os.close(devnull_fd)

# Registers the HAL_SpinButton GObject type (Rosetta_Settings_v1.ui's only
# custom widget class) so Gtk.Builder can resolve it - without this
# import, add_from_file() below fails immediately with "invalid object
# type 'HAL_SpinButton'". Confirmed this is sufficient on its own (no
# live HAL component/hal.component() needed at class-registration time)
# - gladevcp.hal_widgets' HAL_SpinButton only touches HAL when actually
# wired to a component, which this standalone program never does; every
# live HAL read/write here already goes through halcmd instead (see
# module docstring above).
with _suppress_fd2():
    import gladevcp.hal_widgets
import rosetta_settings_io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(SCRIPT_DIR, "Rosetta_Settings_v1.ui")

SETTINGS_PATH = os.path.expanduser("~/Documents/RosettaSet_v1.ini")

# The friendly serial number an owner can set (Rosetta_Set_Serial_Number.sh) -
# same path as Rosetta_Report_Version.py's own SERIAL_PATH and Rosetta_main.py's
# copy (duplicated, not imported - each runs standalone). Appended to
# each page's "O/S ..." label by _load_version_label below;
# absent/empty means no S/N has been set yet, so nothing is appended.
SERIAL_PATH = os.path.expanduser("~/.config/Rosetta/serial")

# The one "O/S ..." label's widget id on each of the 4 Settings
# pages (Axis Selection, Inputs/Outputs/and Sounds, Axis and Stepper
# Motor Tuning, Other) - Rosetta_Settings_v1.ui repeats the same static
# text on every page, each with its own widget id.
OS_VERSION_LABEL_IDS = (
    "OS_Version_Label_Axis_Selection",
    "OS_Version_Label_IO",
    "OS_Version_Label_Tuning",
    "OS_Version_Label_Other",
)

# Channel id ("00".."07", matching the hm2_7i92.0.stepgen.NN suffix) ->
# the role (one of the 8 axis letters or 2 spindles) Rosetta.ini/Rosetta.hal
# ship with by default. This is the seed value for a channel's
# <channel_assignments> entry in RosettaSet_v1.ini when the operator has
# never touched the Axis Selection tab - same "absent -> shipped
# default" convention as every other RosettaSet_v1.ini-backed setting (see
# _load_measurement_system).
#
# Widened 13 September 2026 (Rich): any of 10 roles (8 axis letters or
# 2 spindles) can now be assigned to any of these 8 channels - channels
# 06/07 used to be permanently, uneditably Sp0/Sp1. This retired the
# whole "internal id" concept this file used to need (a channel's own
# Settings widgets are named after LETTERS directly - X_Set_Scale is
# always about letter X - never after a fixed "internal id" tied to a
# channel slot), along with AXIS_STEPGEN/JOINT_NUMBER as fixed-forever
# per-role dicts and CURRENT_LETTER/CURRENT_LETTER_INTERNAL_ID/PID_AXES/
# EXTRA_SETTINGS_LETTERS - see _ROLE_CHANNEL_OF and JOINT_NUMBER below,
# both now computed fresh from the persisted assignment instead.
#
# Two-box hardware (14 October 2026): the 10 channels, their defaults
# and which card/stepgen each is on now come from rosetta_settings_io
# (CHANNEL_DEFAULT_ROLE, CHANNEL_IDS, BASE_CHANNELS, EXPANSION_CHANNELS,
# channel_hal) - shared, since completing an old 8-channel assignment
# must work the same in every program. Channels 06-09 are the optional
# expansion box's; their roles only count while "expansion_box" is set.
CHANNEL_DEFAULT_ROLE = rosetta_settings_io.CHANNEL_DEFAULT_ROLE
CHANNEL_IDS = rosetta_settings_io.CHANNEL_IDS
EXPANSION_CHANNELS = rosetta_settings_io.EXPANSION_CHANNELS


def _stepgen_pin(channel_id, suffix):
    '''A channel's stepgen HAL pin on whichever card it's on, e.g. ".position-scale".'''
    card, stepgen = rosetta_settings_io.channel_hal(channel_id)
    return card + ".stepgen." + stepgen + suffix

# The 8 letters selectable on the Axis Selection tab (Y removed - not
# used on this machine, LATHE=1) and the 2 spindles - the 10 possible
# roles a channel can be assigned.
AXIS_SELECTION_LETTERS = ("X", "Z", "U", "V", "W", "A", "B", "C")
SPINDLE_IDS = ("Sp0", "Sp1")
CHANNEL_ROLES = AXIS_SELECTION_LETTERS + SPINDLE_IDS

# Canonical joint-numbering order for active axis letters - mirrors
# Rosetta_Setup/Rosetta_Generate_Local_Ini.py's JOINT_NUMBER_CANONICAL_ORDER
# exactly (must match, since this program needs to resolve the SAME
# live joint number that script's Rosetta.local.ini generation assigned
# for this session, for the joint.N.backlash HAL parameter).
JOINT_NUMBER_CANONICAL_ORDER = ("X", "Z", "B", "U", "V", "W", "A", "C")

# Axis type (Linear/Angular) is always derived from the letter, forever
# - unlike the embedded Settings tab this replaces (which briefly had
# an independent per-channel Type combo, 3-4 September 2026), Rich
# asked for that reverted for this program: X/Z/U/V/W are always
# Linear, A/B/C are always Angular, with no separate Type choice for
# the operator to make. There is therefore no "channel_types"
# persistence in this file at all.
def _axis_type_for_letter(letter):
    return "ANGULAR" if letter.upper() in ("A", "B", "C") else "LINEAR"

def _save_channel_assignments(assignments):
    '''
    Persists the Axis Selection tab's channel -> role choices into
    RosettaSet_v1.ini's "channel_assignments" dict, for all 10 channels
    (a missing one falls back to CHANNEL_DEFAULT_ROLE).
    '''
    settings = rosetta_settings_io.load_settings()
    settings["channel_assignments"] = {
        channel_id: assignments.get(channel_id, CHANNEL_DEFAULT_ROLE[channel_id])
        for channel_id in CHANNEL_IDS
    }
    rosetta_settings_io.save_settings(settings)
    print("Saved channel assignments: " + str(settings["channel_assignments"]))

def _read_persisted_channel_assignments():
    '''
    The persisted channel -> role map, completed to all 10 channels with
    each role used once (rosetta_settings_io.complete_channel_assignments -
    an old 8-channel file keeps its 00-07 and 08/09 get the unused roles).
    '''
    return rosetta_settings_io.complete_channel_assignments(
        rosetta_settings_io.load_settings().get("channel_assignments"))

# The optional expansion box (two-box hardware, 14 October 2026): the
# Axis Selection page's Expansion_Box_Connected checkbox, persisted as
# RosettaSet_v1.ini's "expansion_box" (absent = not connected). Without it,
# channels 06-09 and limit jacks 4-6 are greyed out and ignored.
def _save_expansion_box(connected):
    settings = rosetta_settings_io.load_settings()
    settings["expansion_box"] = bool(connected)
    rosetta_settings_io.save_settings(settings)
    print("Saved expansion box: " + ("connected" if connected else "not connected"))

def _read_persisted_expansion_box():
    return rosetta_settings_io.load_settings().get("expansion_box") is True

# The 3 GX-12 limit jacks on the panel. Each takes one normally-closed
# limit switch (or both ends of an axis's travel wired in series) and
# may be left empty; the Axis Selection page's Limit_Jack_N_Axis combo
# picks what, if anything, it protects: both ends of an axis (switches in
# series), or just its min (negative) or max (positive) end - e.g. a
# curvilinear slide with a switch at each end uses two jacks, "B min" and
# "B max", so LinuxCNC knows which end tripped and allows jogging away
# from it. Persisted in RosettaSet_v1.ini's "limit_switches" dict (jack ->
# "B", "B min", "B max", or "" = not used)
# and wired into HAL at the next launch by Rosetta_Generate_Local_Ini.py,
# whose LIMIT_JACK_INPUT maps each jack to its 7i92 input.
LIMIT_JACKS = ("1", "2", "3", "4", "5", "6")
# Jacks 4-6 are on the expansion box - see _read_persisted_expansion_box.
EXPANSION_LIMIT_JACKS = ("4", "5", "6")
LIMIT_JACK_NOT_USED = "Not used"

# limit_switches value suffix -> which end(s) of travel it covers, and
# the text the combo shows for it (after the letter).
LIMIT_ENDS = {"": "both", " min": "min", " max": "max"}
LIMIT_END_LABELS = {"": " (both ends)", " min": " min", " max": " max"}

def _parse_limit_value(value):
    '''
    "X" -> ("X", "both"), "X min" -> ("X", "min"), "X max" -> ("X", "max");
    anything else (including "") -> None. Mirrors
    Rosetta_Generate_Local_Ini.py's _parse_limit_value.
    '''
    for suffix, end in LIMIT_ENDS.items():
        letter = value[:len(value) - len(suffix)] if suffix else value
        if value == letter + suffix and letter in AXIS_SELECTION_LETTERS:
            return letter, end
    return None

def _limit_ends_conflict(end_a, end_b):
    '''
    Two jacks on the same axis conflict unless one is min and the other
    max - "both" already covers either end.
    '''
    return not ({end_a, end_b} == {"min", "max"})

def _limit_value_label(value):
    '''The combo text for a limit_switches value ("" -> "Not used").'''
    parsed = _parse_limit_value(value)
    if parsed is None:
        return LIMIT_JACK_NOT_USED
    suffix = value[len(parsed[0]):]
    return parsed[0] + LIMIT_END_LABELS[suffix]

def _save_limit_jacks(jacks):
    '''
    Persists the Axis Selection page's limit jack choices into
    RosettaSet_v1.ini's "limit_switches" dict. jacks is a dict of jack
    ("1".."3") -> "<letter>", "<letter> min", "<letter> max", or "" for
    a jack that isn't used.
    '''
    settings = rosetta_settings_io.load_settings()
    settings["limit_switches"] = {jack: jacks.get(jack, "") for jack in LIMIT_JACKS}
    rosetta_settings_io.save_settings(settings)
    print("Saved limit jacks: " + str(settings["limit_switches"]))

def _read_persisted_limit_jacks():
    '''
    Reads the persisted limit jack map (jack -> limit_switches value). A
    missing or unrecognized entry means the jack isn't used - the safe
    default for a machine that has never set one up. A jack conflicting
    with a lower-numbered one on the same axis (anything but a min/max
    pair) is dropped, matching what Rosetta_Generate_Local_Ini.py's
    _read_limit_jacks will actually wire.
    '''
    jacks = {jack: "" for jack in LIMIT_JACKS}
    stored = rosetta_settings_io.load_settings().get("limit_switches", {})
    for jack in LIMIT_JACKS:
        value = stored.get(jack, "")
        parsed = _parse_limit_value(value)
        if parsed is None:
            continue
        clash = False
        for other in jacks.values():
            other_parsed = _parse_limit_value(other)
            if other_parsed and other_parsed[0] == parsed[0] and _limit_ends_conflict(other_parsed[1], parsed[1]):
                clash = True
        if not clash:
            jacks[jack] = value
    return jacks

# The optional E-stop button (GX-16/2 plug, normally-closed). The Axis
# Selection page's Estop_Button_Connected checkbox records whether one
# is plugged in, persisted as RosettaSet_v1.ini's "estop_button" (absent =
# not connected); Rosetta_Generate_Local_Ini.py wires it into HAL at the
# next launch only when true, since an empty plug would otherwise hold
# the machine in E-stop.
# Makes the Axis Selection page's E-Stop Button frame (named
# Estop_Frame in Rosetta_Settings_v1.ui) look like a safety control -
# safety-yellow background and a heavier dark border, with its title in
# red set in the .ui itself - so it stands apart from the Limit Jack
# frames beside it. Scoped to that one widget name, nothing else.
ESTOP_FRAME_CSS = b"""
#Estop_Frame > border {
    background-color: #FFE680;
    border: 2px solid #3d3d3d;
    border-radius: 3px;
}
"""

ESTOP_WARNING_MARKUP = ('<span foreground="#c01c28" weight="bold">Machine stays in E-stop '
                        'unless the button is plugged in</span>')

def _install_estop_frame_style():
    provider = Gtk.CssProvider()
    provider.load_from_data(ESTOP_FRAME_CSS)
    screen = Gdk.Screen.get_default()
    if screen is not None:
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def _save_estop_button(connected):
    settings = rosetta_settings_io.load_settings()
    settings["estop_button"] = bool(connected)
    rosetta_settings_io.save_settings(settings)
    print("Saved E-stop button: " + ("connected" if connected else "not connected"))

def _read_persisted_estop_button():
    return rosetta_settings_io.load_settings().get("estop_button") is True

# The optional signal tower (GX-12/4 plug; green/red lights and a
# sounder, each switched by a relay). The Axis Selection page's
# Signal_Tower_Connected checkbox records whether one is fitted,
# persisted as RosettaSet_v1.ini's "signal_tower" (absent = not connected);
# Rosetta_Generate_Local_Ini.py only sets up its three output pins at the
# next launch when true.
def _save_signal_tower(connected):
    settings = rosetta_settings_io.load_settings()
    settings["signal_tower"] = bool(connected)
    rosetta_settings_io.save_settings(settings)
    print("Saved signal tower: " + ("connected" if connected else "not connected"))

def _read_persisted_signal_tower():
    return rosetta_settings_io.load_settings().get("signal_tower") is True

# Whether the limit jacks take normally-closed or normally-open
# switches - the Limit_Switch_NC / Limit_Switch_NO radios, persisted as
# RosettaSet_v1.ini's "limit_switch_type" ("NC" or "NO"; absent = "NC").
# One choice for all jacks. Rosetta_Generate_Local_Ini.py reads the jacks'
# GPIO .in for NC and .in_not for NO. The E-stop button is always NC.
LIMIT_SWITCH_TYPES = ("NC", "NO")

# User Manual pages opened by the buttons beside the Axis Selection
# page's Limit Switches, E-Stop Button and Signal Tower and Sounds notes
# and the tuning page's three Scale notes (Open_Manual_Link), keyed by
# button id.
MANUAL_URL = "https://rosetta.colvintools.com/UserManual/index.php?n=Main."
MANUAL_LINKS = {
    "Limit_Switch_Cabling_Link": MANUAL_URL + "LimitSwitchCabling",
    "Limit_Switch_How_Link":     MANUAL_URL + "InputsOutputsSound#LimitSwitches",
    "Estop_Cabling_Link":        MANUAL_URL + "E-StopCabling",
    "Estop_How_Link":            MANUAL_URL + "InputsOutputsSound#EStopButton",
    "Tower_Cabling_Link":        MANUAL_URL + "SignalTowerCabling",
    "Tower_How_Link":            MANUAL_URL + "InputsOutputsSound#SignalTower",
    "Sounds_How_Link":           MANUAL_URL + "InputsOutputsSound#Sounds",
    "Expansion_Box_How_Link":    MANUAL_URL + "AxisSelection#ExpansionBox",
    "Linear_Scale_Link":         MANUAL_URL + "ScaleSettingsForADevice",
    "Rotary_Scale_Link":         MANUAL_URL + "ScaleSettingsForADevice",
    "Spindle_Scale_Link":        MANUAL_URL + "ScaleSettingsForADevice",
}

# Whether a reserved-name file in gcode/ (one starting with "rosetta",
# any case, or named M100-M199) stops LinuxCNC from starting or only
# warns - the Startup_Check_Abort / Startup_Check_Warn radios, persisted
# as RosettaSet_v1.ini's "startup_file_check" ("abort" or "warn"; absent =
# "abort"). The scan itself runs in Rosetta_Setup/Rosetta_Generate_Local_Ini.py,
# before LinuxCNC is launched - see "Reserved names" in CLAUDE.md for
# why gcode/ can never hold such a file.
STARTUP_FILE_CHECKS = ("abort", "warn")

def _save_startup_file_check(choice):
    settings = rosetta_settings_io.load_settings()
    settings["startup_file_check"] = choice
    rosetta_settings_io.save_settings(settings)
    print("Saved startup file check: " + choice)

def _read_persisted_startup_file_check():
    choice = rosetta_settings_io.load_settings().get("startup_file_check", "abort")
    return choice if choice in STARTUP_FILE_CHECKS else "abort"

# What happens when a program, index, Sync Move or thread would move an
# axis or spindle whose ENA is off (added 09 November 2026, Rich's
# idea) - the Not_Enabled_Ask / Not_Enabled_Enable radios on the Other
# page, persisted as RosettaSet_v1.ini's "not_enabled_action" ("ask" or
# "enable"; absent = "ask"). Read at startup by AXIS's
# Rosetta_Axis_Commands.py and by the panel (Rosetta_main.py).
NOT_ENABLED_ACTIONS = ("ask", "enable")

def _save_not_enabled_action(choice):
    settings = rosetta_settings_io.load_settings()
    settings["not_enabled_action"] = choice
    rosetta_settings_io.save_settings(settings)
    print("Saved not enabled action: " + choice)

def _read_persisted_not_enabled_action():
    choice = rosetta_settings_io.load_settings().get("not_enabled_action", "ask")
    return choice if choice in NOT_ENABLED_ACTIONS else "ask"

def _save_limit_switch_type(switch_type):
    settings = rosetta_settings_io.load_settings()
    settings["limit_switch_type"] = switch_type
    rosetta_settings_io.save_settings(settings)
    print("Saved limit switch type: " + switch_type)

def _read_persisted_limit_switch_type():
    switch_type = rosetta_settings_io.load_settings().get("limit_switch_type", "NC")
    return switch_type if switch_type in LIMIT_SWITCH_TYPES else "NC"

# Where the main panel's attention beeps play (3 when a program, Sync
# Move or Cut Thread finishes; 2 when a program stops at M0/M1) - see
# Rosetta_main.py's _load_sounds. The Done_Sound combo's ids are the
# persisted values, RosettaSet_v1.ini's "done_sound"; absent = "both".
DONE_SOUND_CHOICES = ("off", "tower", "speaker", "both")

def _save_done_sound(choice):
    settings = rosetta_settings_io.load_settings()
    settings["done_sound"] = choice
    rosetta_settings_io.save_settings(settings)
    print("Saved done sound: " + choice)

def _read_persisted_done_sound():
    choice = rosetta_settings_io.load_settings().get("done_sound", "both")
    return choice if choice in DONE_SOUND_CHOICES else "both"

# Where the fault siren sounds (3 s, when red comes on - a following
# error or a tripped limit switch): the tower's buzzer and/or the Pi's
# speaker (Rosetta_Generate_Local_Ini.py's _signal_tower_hal, Rosetta_main.py's
# _poll_fault_siren). Same ids as Done_Sound; RosettaSet_v1.ini's
# "fault_sound", absent = "both".
def _save_fault_sound(choice):
    settings = rosetta_settings_io.load_settings()
    settings["fault_sound"] = choice
    rosetta_settings_io.save_settings(settings)
    print("Saved fault sound: " + choice)

def _read_persisted_fault_sound():
    choice = rosetta_settings_io.load_settings().get("fault_sound", "both")
    return choice if choice in DONE_SOUND_CHOICES else "both"

# This session's channel -> role assignment, as persisted at the time
# Rosetta_Generate_Local_Ini.py generated Rosetta.local.hal/Rosetta.local.ini for
# this LinuxCNC launch (see CLAUDE.md). Read once at module import: a
# running LinuxCNC session's assignment can't change without a restart
# anyway - and this program refuses to run while LinuxCNC is up - so
# re-reading it later would only ever see the same value or one that
# doesn't match what's actually wired into HAL right now.
_CHANNEL_ASSIGNMENTS_AT_STARTUP = _read_persisted_channel_assignments()

# Role -> this session's actual channel id, for whichever of the 10
# roles are currently assigned to a channel (a role not currently
# assigned to any channel simply has no entry here - callers resolve
# that with .get(...) and treat None as "nothing live to push to").
# Reverse of _CHANNEL_ASSIGNMENTS_AT_STARTUP. Replaces the old fixed-
# forever AXIS_STEPGEN dict - unlike that dict, a role's channel is no
# longer fixed at all, so this has to be computed fresh from the
# persisted assignment instead of hardcoded.
_ROLE_CHANNEL_OF = {role: channel_id for channel_id, role in _CHANNEL_ASSIGNMENTS_AT_STARTUP.items()
                    if channel_id in rosetta_settings_io.active_channels(rosetta_settings_io.load_settings())}

# Letter -> this session's actual joint number, for whichever axis
# letters are currently assigned to a channel (JOINTS itself is dynamic
# now - 6 to 8, depending how many letters vs. spindles are active this
# session - see Rosetta_Setup/Rosetta_Generate_Local_Ini.py). Replaces the old
# fixed-forever JOINT_NUMBER dict, for the same reason as
# _ROLE_CHANNEL_OF above - a letter's joint number now depends on which
# OTHER letters are simultaneously active, so it must be computed fresh
# each session, not hardcoded.
_ACTIVE_LETTERS_AT_STARTUP = [l for l in JOINT_NUMBER_CANONICAL_ORDER if l in _ROLE_CHANNEL_OF]
JOINT_NUMBER = {letter: i for i, letter in enumerate(_ACTIVE_LETTERS_AT_STARTUP)}

# Spindle id -> {"Pos": its indexing (M19) position-loop component}. The
# suffix matches the Settings widget id suffix (e.g. Sp0_Set_P_Pos) and
# the RosettaSet_v1.ini block tag "pid_pos". (The velocity loops, pid.s0/
# pid.s1 and their "_Vel" widgets, were removed 08 October 2026 - their
# output never reached the stepgen.)
PID_SPINDLE_LOOPS = {
    "Sp0": {"Pos": "pid.p0"},
    "Sp1": {"Pos": "pid.p1"},
}

# The speed limits that moved out of Rosetta.ini on 08 October 2026: widget
# id suffix -> RosettaSet_v1.ini axes.<id> key. Max Speed / Max Acceleration
# are the motion planner's limits (written into Rosetta.local.ini by
# Rosetta_Generate_Local_Ini.py); PID/Indexing Max Output cap the position
# loop's output (set by Rosetta_Settings_Restore.py). Like Scale and the PID
# gains, they're saved by Save All Settings, and none has a live HAL
# write - this program never runs alongside LinuxCNC.
LIMIT_FIELDS = {
    "_Set_Max_Speed": "max_speed",
    "_Set_Max_Acceleration": "max_acceleration",
    "_Set_PID_Max_Output": "pid_max_output",
    "_Set_Index_Max_Output": "index_max_output",
}

# The three tuning groups' "Advanced settings" expanders, and the grid
# group each axis belongs to (its Limits_Warning label's prefix).
ADVANCED_EXPANDERS = ("LinearAxes_Advanced", "RotaryAxes_Advanced", "Spindle_Advanced")


def _limit_group(axis_id):
    if axis_id in SPINDLE_IDS:
        return "Spindle"
    return "RotaryAxes" if _axis_type_for_letter(axis_id) == "ANGULAR" else "LinearAxes"

# Settings widget field name -> HAL pid component pin name.
PID_PARAM_PIN = {
    "P":   "Pgain",
    "I":   "Igain",
    "D":   "Dgain",
    "FF0": "FF0",
    "FF1": "FF1",
    "FF2": "FF2",
}
PID_PARAMS = ("P", "I", "D", "FF0", "FF1", "FF2")

# Default directory Export/Import's file choosers start in.
ROSETTASET_DEFAULT_DIR = os.path.expanduser("~/Documents")

# Axes (not spindles) that have a free-text comment field on the main
# panel, persisted to RosettaSet_v1.ini as each <axis>'s <usercomment>.
# Rosetta_Settings has no comment field of its own (that widget lives on
# the main panel, a separate program) but still needs this list to
# default the Export dialog's Device combos and to apply an imported/
# loaded comment value to RosettaSet_v1.ini on the main panel's behalf.
COMMENT_AXES = ("X", "Z", "U", "V", "W", "B")

# Leading entry (index 0) in every device-name GtkComboBoxText - the
# Export Settings dialog's per-axis Device combos - standing in for
# "nothing chosen yet" instead of a blank-looking row. Never treated as
# a real device name - see _combo_selected_device.
DEVICE_COMBO_PLACEHOLDER = "(nothing selected yet)"

# Sp0/Sp1 have no main-panel comment field (see COMMENT_AXES) to default
# the Export Settings dialog's Device combo from, unlike X/Z/U/V/W/B -
# these are the ones Rich actually has, so use them as each spindle's
# default there instead of falling back to DEVICE_COMBO_PLACEHOLDER.
SPINDLE_DEFAULT_DEVICE_NAME = {
    "Sp0": "Spindle (Sp0)",
    "Sp1": "Rosette Phaser/Multiplier (Sp1)",
}

# Export_Settings/Import_Settings: a hand-picked subset of just what's
# literally on the Settings widgets (each axis's Scale/Backlash/Max
# Vel/Max Accel/PID, plus Measurement System), for quick, ad hoc
# sharing of a few values (e.g. "just my B-axis calibration") rather
# than a full profile. Plain JSON (matching RosettaSet_v1.ini's own shape).
EXPORT_EXTENSION = ".RosettaSet_v1.ini"
# Exports made before the Rosetta renaming (02 November 2026) end in
# this - Import still offers and reads them.
OLD_EXPORT_EXTENSION = ".REBset_v1.ini"

# Establish connection to command and status channels - needed for the
# M5-before-scale-change safety behavior in Sp0_Set_Scale/Sp1_Set_Scale/
# _axis_set_scale_letter below and the motion-abort in the latter. This
# is the one piece of LinuxCNC access that has no halcmd-subprocess
# equivalent - everything else in this file shells out to halcmd
# instead of importing hal/hal_glib, but the command/status channel can
# only be reached via `import linuxcnc`.
c = linuxcnc.command()
s = linuxcnc.stat()

def _linuxcnc_is_running():
    '''
    The intended workflow is: run Rosetta_Settings first, then start
    LinuxCNC - not the other way around, and not concurrently. Every
    _load_* method below pushes the values it reads from RosettaSet_v1.ini
    onto live HAL pins via halcmd, which only exist while LinuxCNC is
    running; running this program while LinuxCNC is up floods the
    console with harmless-but-alarming "parameter or pin not found"
    lines for every single pin (confirmed live 4 September 2026 with
    LinuxCNC not running). Rather than let that noise stand in for a
    real answer, check up front and tell the operator to close LinuxCNC
    first.

    s.poll() is documented to raise linuxcnc.error ("emcStatusBuffer
    invalid") when there's no running LinuxCNC session to connect to,
    and does exactly that in isolation - but confirmed live, once
    gladevcp.hal_widgets has been imported (needed above so Gtk.Builder
    can resolve HAL_SpinButton), the same failure instead surfaces as a
    bare SystemError ("returned NULL without setting an exception") -
    apparently some interaction between GTK/GLib's signal handling and
    NML's own alarm()-based timeout, not something to rely on staying
    exactly linuxcnc.error. There's no legitimate reason for poll() to
    raise anything at all when a session genuinely is running, so treat
    ANY exception here as "not running" rather than chase every exact
    exception type this interaction might produce.
    '''
    try:
        with _suppress_fd2():
            s.poll()
        return True
    except Exception:
        return False

def _show_settings_error(widget, message):
    dialog = Gtk.MessageDialog(
        transient_for=widget.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=message,
    )
    dialog.run()
    dialog.destroy()

def _save_measurement_system(system):
    '''
    Persists the Measurement System choice ("Metric"/"Imperial") into
    RosettaSet_v1.ini, the same silent, automatic settings file
    _load_scale_settings/_load_axis_comments already read/write.
    '''
    settings = rosetta_settings_io.load_settings()
    settings["measurement_system"] = system
    rosetta_settings_io.save_settings(settings)
    print("Saved measurement_system = " + system)

def _save_device_names(names):
    '''
    Persists the maintained device-name list (the Other page's Device
    Names box - one name per line) into RosettaSet_v1.ini's "device_names"
    list, replacing it wholesale each time rather than tracking
    adds/removes/reorders across saves.
    '''
    settings = rosetta_settings_io.load_settings()
    settings["device_names"] = list(names)
    rosetta_settings_io.save_settings(settings)
    print("Saved " + str(len(names)) + " device name(s)")

def _read_persisted_device_names():
    '''
    Reads the persisted device-name list straight from SETTINGS_PATH.
    Returns [] if the file can't be read or has no device_names list.
    '''
    return list(rosetta_settings_io.load_settings().get("device_names", []))

def _read_persisted_axis_comment(axis_id, settings):
    '''
    Extracts one axis's persisted usercomment value out of an
    already-loaded settings dict. Used by _run_export_selection_dialog
    to default each axis's Export dialog Device combo to whatever's
    currently set on the main panel - RosettaSet_v1.ini's usercomment is
    the only channel between this program and the main panel, which is
    a separate process with no live IPC. Returns "" if the axis or its
    usercomment isn't found.
    '''
    return settings.get("axes", {}).get(axis_id, {}).get("usercomment", "")

def _combo_selected_device(combo):
    '''
    Returns the real selected value of a device-name GtkComboBoxText
    (empty string if the leading DEVICE_COMBO_PLACEHOLDER entry - index
    0 - is what's active), rather than combo.get_active_text() directly,
    which would return the placeholder's own display text.
    '''
    return combo.get_active_text() if combo.get_active() > 0 else ""

def _save_max_jog_speed(value):
    '''
    Persists the Max Jog Speed choice into RosettaSet_v1.ini, the same
    silent, automatic settings file _save_measurement_system already
    writes measurement_system into.
    '''
    settings = rosetta_settings_io.load_settings()
    settings["max_jog_speed"] = round(value, 4)
    rosetta_settings_io.save_settings(settings)
    print("Saved max_jog_speed = " + str(settings["max_jog_speed"]))

# Settings widget id -> (RosettaSet_v1.ini tag, fallback default matching
# Rosetta.ini's own shipped value). Each of these patches ALL occurrences of
# its ini key, both [DISPLAY] (jog slider) and [TRAJ] (trajectory-planner
# ceiling), since Rosetta.ini ships the same value in both places for these
# keys - see Rosetta_Setup/Rosetta_Generate_Local_Ini.py for the overlay side.
VELOCITY_SETTINGS = {
    "Default_Linear_Velocity":  ("default_linear_velocity",  0.250000),
    "Min_Linear_Velocity":      ("min_linear_velocity",      0.016670),
    "Max_Angular_Velocity":     ("max_angular_velocity",     10.000000),
    "Default_Angular_Velocity": ("default_angular_velocity", 5.833333),
    "Min_Angular_Velocity":     ("min_angular_velocity",     1.666667),
}

def _save_velocity_setting(tag, value):
    '''
    Persists one of VELOCITY_SETTINGS' values into RosettaSet_v1.ini -
    generic version of _save_max_jog_speed above, parameterized by key
    name since these five all follow the exact same shape.
    '''
    settings = rosetta_settings_io.load_settings()
    settings[tag] = round(value, 6)
    rosetta_settings_io.save_settings(settings)
    print("Saved " + tag + " = " + str(settings[tag]))

def _stepgen_step_rate_ceiling(stepgen_ch):
    '''
    Returns the hardware step-rate ceiling (steps/sec) for the given
    stepgen channel, derived from its live steplen/stepspace HAL params
    (nanoseconds, set from [JOINT_n]STEPLEN/STEPSPACE in Rosetta.hal at
    startup and not editable from this UI) via
    1 / (STEPLEN + STEPSPACE) - the same formula worked by hand in
    Rosetta.ini's STEPGEN_MAXVEL comments. Returns None if steplen+stepspace
    sum to zero, or if either can't be read (e.g. LinuxCNC isn't
    running).

    Reads both params via `halcmd getp` rather than the Python hal
    module's hal.get_value() (what Rosetta_main.py's version of this
    function uses) - this program has no HAL component of its own and
    deliberately avoids `import hal` entirely, so every live HAL read
    goes through the same halcmd-subprocess pattern used everywhere
    else in this file.
    '''
    try:
        steplen_result = subprocess.run(
            ["halcmd", "getp", _stepgen_pin(stepgen_ch, ".steplen")],
            check=True, capture_output=True, text=True
        )
        stepspace_result = subprocess.run(
            ["halcmd", "getp", _stepgen_pin(stepgen_ch, ".stepspace")],
            check=True, capture_output=True, text=True
        )
        steplen = float(steplen_result.stdout.strip())
        stepspace = float(stepspace_result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None
    total_ns = steplen + stepspace
    if total_ns <= 0:
        return None
    return 1e9 / total_ns

def _warn_if_max_vel_exceeds_ceiling(self, widget, axis, stepgen_ch, scale, max_vel_widget):
    '''
    Warns and clamps when scale (steps/unit, just-committed) and the
    Max Vel spin button's current value together would ask the stepgen
    for more steps/sec than its steplen+stepspace timing can produce.
    LinuxCNC doesn't error in this case, it silently clips the
    stepgen's actual speed at the hardware ceiling - rather than leave
    the field showing a value the hardware can't actually honor, this
    pushes the calculated safe maximum back into max_vel_widget, which
    (via its own "value-changed" signal, already wired to
    _axis_set_max/_axis_set_max_letter) sends the corrected value to
    the live HAL maxvel pin the same way a manual edit would - no
    separate HAL write needed here. Only called for Max Vel, not Max
    Accel - there's no equivalent stepgen step-rate limit tied to
    acceleration.
    '''
    if scale == 0:
        return
    ceiling = _stepgen_step_rate_ceiling(stepgen_ch)
    if ceiling is None:
        return
    max_vel = max_vel_widget.get_value()
    if abs(scale) * max_vel <= ceiling:
        return

    # Round down (not to nearest) so the clamped value can't itself
    # still exceed the ceiling after rounding - the set_value() below
    # reenters this same check via max_vel_widget's own "value-changed"
    # signal, and a second popup there would be confusing.
    digits = max_vel_widget.get_digits()
    factor = 10 ** digits
    safe_max_vel = int((ceiling / abs(scale)) * factor) / factor

    # REB_Settings_v1.ini's Axis and Stepper Motor Tuning page shows one
    # representative Max Vel UOM label per table (LinearAxes_Max_Vel_UOM/
    # RotaryAxes_Max_Vel_UOM/Spindle_Max_Vel_UOM), not one per letter/
    # axis id the way the embedded Settings tab this replaces did (e.g.
    # "X_Max_Vel_UOM") - see _apply_measurement_system_labels' docstring
    # for the same consolidation. Map axis to the right table's label.
    if axis in ("Sp0", "Sp1"):
        uom_widget_id = "Spindle_Max_Vel_UOM"
    elif _axis_type_for_letter(axis) == "ANGULAR":
        uom_widget_id = "RotaryAxes_Max_Vel_UOM"
    else:
        uom_widget_id = "LinearAxes_Max_Vel_UOM"
    uom_widget = self.builder.get_object(uom_widget_id)
    uom = uom_widget.get_label().replace("\n", " ") if uom_widget is not None else "units/sec"
    dialog = Gtk.MessageDialog(
        transient_for=widget.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK,
        text=axis + ": Max Velocity was too high for this Scale",
    )
    dialog.format_secondary_text(
        "At a Scale of {:g}, the stepgen hardware can drive at most {:.4f} {} "
        "(step-rate ceiling {:.0f} steps/sec, from STEPLEN+STEPSPACE). "
        "Max Velocity has been reduced from {:g} {} to {:.4f} {} to match."
        .format(abs(scale), safe_max_vel, uom, ceiling, max_vel, uom, safe_max_vel, uom)
    )
    dialog.run()
    dialog.destroy()

    max_vel_widget.set_value(safe_max_vel)


class HandlerClass:
    '''
    Handler methods/state for the standalone Rosetta_Settings program.
    Not gladevcp-launched - a single instance is created directly by
    main() below against one Gtk.Builder that owns every widget in
    Rosetta_Settings_v1.ui, so (unlike Rosetta_main.py, which this was
    extracted from) the "does this component own this widget" guards
    inherited from several methods below are always trivially true
    here. They're kept anyway rather than stripped out, since they're
    harmless and keep this code close to its Rosetta_main.py original for
    anyone comparing the two later.
    '''

    def scroll_entries(self, widget, event):
        '''
        Lets the mouse scroll wheel scroll the viewport instead of the
        scroll being captured by a child widget such as a spin button
        under the cursor.
        '''
        adj = widget.get_property("vadjustment")
        if adj is None:
            return False

        increment = adj.get_step_increment()
        lower = adj.get_lower()
        upper = adj.get_upper() - adj.get_page_size()

        if event.direction == Gdk.ScrollDirection.UP:
            adj.set_value(max(lower, adj.get_value() - increment))
            return True
        elif event.direction == Gdk.ScrollDirection.DOWN:
            adj.set_value(min(upper, adj.get_value() + increment))
            return True
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            valid, dx, dy = event.get_scroll_deltas()
            if valid:
                new_value = adj.get_value() + (dy * increment)
                adj.set_value(max(lower, min(upper, new_value)))
            return True

        return False

    def _redirect_scroll_to_viewport(self, widget, event):
        '''
        scroll_entries above only fires for "windowless" widgets (Labels,
        empty grid cells) - anything with its own GdkWindow, like a
        GtkSpinButton or GtkComboBox, receives a scroll-event directly
        and never lets it reach the viewport at all. Wired onto every
        spin button/combo box individually (see
        _install_viewport_scroll_redirect) so scrolling still works
        when the cursor happens to be over one of the many spin
        buttons/combos this program is mostly made of.
        '''
        viewport = widget.get_ancestor(Gtk.Viewport)
        if viewport is None:
            return False
        return self.scroll_entries(viewport, event)

    def _install_viewport_scroll_redirect(self, container):
        '''
        Recursively wires _redirect_scroll_to_viewport onto every spin
        button/combo box under container. Called once from __init__ on
        the outer scrollable viewport.
        '''
        for child in container.get_children():
            if isinstance(child, (Gtk.SpinButton, Gtk.ComboBox)):
                child.connect("scroll-event", self._redirect_scroll_to_viewport)
            if isinstance(child, Gtk.Container):
                self._install_viewport_scroll_redirect(child)

    def _load_scale_settings(self):
        '''
        Reads persisted axis/spindle scale values from RosettaSet_v1.ini and
        applies them to the Settings spin buttons and the real stepgen
        position-scale HAL pins.

        All 10 CHANNEL_ROLES (8 letters + 2 spindles): always load the
        persisted value into the spin button, but only push it live if
        this role is currently assigned to a channel this session
        (_ROLE_CHANNEL_OF).
        '''
        if self.builder.get_object("X_Set_Scale") is None:
            return

        settings = rosetta_settings_io.load_settings()
        axes = settings.get("axes", {})

        for role in CHANNEL_ROLES:
            axis_entry = axes.get(role)
            if axis_entry is None or "scale" not in axis_entry:
                print("No stored scale found for axis " + role
                      + " in " + SETTINGS_PATH)
                continue

            value = float(axis_entry["scale"])

            widget = self.builder.get_object(role + "_Set_Scale")
            if widget is not None:
                widget.set_value(value)

            channel_id = _ROLE_CHANNEL_OF.get(role)
            if channel_id is None:
                # Not currently assigned to any channel - nothing live
                # to push to, the value just sits in the spin button/
                # file for whenever this role is assigned.
                continue

            hal_pin = _stepgen_pin(channel_id, ".position-scale")
            if self._linuxcnc_running:
                try:
                    subprocess.run(
                        ["halcmd", "setp", hal_pin, str(value)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Restored " + hal_pin + " = " + str(value) + " (" + role + ")")
                except subprocess.CalledProcessError as e:
                    print("Error restoring " + hal_pin + ": " + e.stderr)
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")

    def _load_max_vel_accel_settings(self):
        '''
        Reads persisted axis/spindle "max_vel"/"max_accel" values from
        RosettaSet_v1.ini and applies them to the Max Vel/Max Accel spin
        buttons and the real stepgen maxvel/maxaccel HAL params
        (hm2_7i92.0.stepgen.NN.maxvel/.maxaccel) - mirrors
        _load_scale_settings above exactly, just pushing two values per
        axis instead of one. These are the stepgen hardware limits, not
        [JOINT_n]MAX_VELOCITY/MAX_ACCELERATION - see rosetta_settings_io.py's
        _default_axis_entry for why.
        '''
        if self.builder.get_object("X_Set_Max_Vel") is None:
            return

        settings = rosetta_settings_io.load_settings()
        axes = settings.get("axes", {})

        def restore(axis_id, stepgen_ch, axis_entry, label_suffix=""):
            for key, widget_suffix, hal_suffix in (
                ("max_vel", "_Set_Max_Vel", ".maxvel"),
                ("max_accel", "_Set_Max_Accel", ".maxaccel"),
            ):
                if key not in axis_entry:
                    print("No stored " + key + " found for axis " + axis_id
                          + " in " + SETTINGS_PATH)
                    continue

                value = float(axis_entry[key])

                widget = self.builder.get_object(axis_id + widget_suffix)
                if widget is not None:
                    widget.set_value(value)

                if stepgen_ch is None or not self._linuxcnc_running:
                    continue

                hal_pin = _stepgen_pin(stepgen_ch, hal_suffix)
                try:
                    subprocess.run(
                        ["halcmd", "setp", hal_pin, str(value)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Restored " + hal_pin + " = " + str(value) + label_suffix)
                except subprocess.CalledProcessError as e:
                    print("Error restoring " + hal_pin + ": " + e.stderr)
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")

        for role in CHANNEL_ROLES:
            axis_entry = axes.get(role)
            if axis_entry is None:
                continue
            stepgen_ch = _ROLE_CHANNEL_OF.get(role)
            restore(role, stepgen_ch, axis_entry, " (" + role + ")")

    def _load_pid_settings(self):
        '''
        Reads persisted P/I/D/FF0/FF1/FF2 gains from RosettaSet_v1.ini
        (each axis's <pid> block, or <pid_pos>/<pid_vel> for the two
        spindle loops) and applies them to the PID spin buttons and the
        live pid.* HAL gain pins - mirrors _load_scale_settings above
        for the axis stepgen scales (same per-role resolution via
        _ROLE_CHANNEL_OF for all 10 CHANNEL_ROLES). Rosetta_Scale_Persist.py
        is what writes these back into RosettaSet_v1.ini at shutdown, the
        same as it already does for scale.
        '''
        if self.builder.get_object("X_Set_P") is None:
            return

        settings = rosetta_settings_io.load_settings()
        axes = settings.get("axes", {})

        def apply(axis_id, block_tag, hal_component, widget_id_for_param, push_live=True):
            '''
            widget_id_for_param(param) builds the Settings widget id for
            a given P/I/D/FF0/FF1/FF2 param - axes and spindle loops put
            their disambiguating suffix in different places (X_Set_P vs
            Sp0_Set_P_Pos), so the caller supplies this rather than
            apply() assuming one fixed naming shape.

            push_live=False (any role not currently assigned to a
            channel - see below) still sets the widget from file but
            skips the halcmd push: the pid.* HAL component technically
            still exists either way (all 10 roles' pid components are
            always loaded - see Rosetta.hal), but it isn't wired into any
            live control loop while unassigned, so there's nothing
            meaningful to restore it onto yet.
            '''
            axis_entry = axes.get(axis_id)
            if axis_entry is None:
                print("No axis \"" + axis_id + "\" entry found in " + SETTINGS_PATH)
                return

            pid_block = axis_entry.get(block_tag)
            if pid_block is None:
                print("No \"" + block_tag + "\" entry found for axis " + axis_id
                      + " in " + SETTINGS_PATH)
                return

            for param in PID_PARAMS:
                widget_id = widget_id_for_param(param)

                if param not in pid_block:
                    print("No stored " + param + " found for " + widget_id
                          + " in " + SETTINGS_PATH)
                    continue

                value = pid_block[param]
                widget = self.builder.get_object(widget_id)
                if widget is not None:
                    widget.set_value(float(value))

                if not push_live:
                    continue

                hal_pin = hal_component + "." + PID_PARAM_PIN[param]
                try:
                    subprocess.run(
                        ["halcmd", "setp", hal_pin, str(value)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Restored " + hal_pin + " = " + str(value))
                except subprocess.CalledProcessError as e:
                    print("Error restoring " + hal_pin + ": " + e.stderr)
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")

        for spindle_id, loops in PID_SPINDLE_LOOPS.items():
            for suffix, component in loops.items():
                block_tag = "pid_pos" if suffix == "Pos" else "pid_vel"
                apply(spindle_id, block_tag, component,
                      lambda param, spindle_id=spindle_id, suffix=suffix:
                          spindle_id + "_Set_" + param + "_" + suffix,
                      push_live=self._linuxcnc_running and spindle_id in _ROLE_CHANNEL_OF)

        # All 8 letters (X,Z,U,V,W,A,B,C): letter-keyed - pid.<letter> is
        # always loaded (see Rosetta.hal), but only wired into a live control
        # loop while this letter is currently assigned to a channel
        # (_ROLE_CHANNEL_OF).
        for letter in AXIS_SELECTION_LETTERS:
            apply(letter, "pid", "pid." + letter.lower(),
                  lambda param, letter=letter: letter + "_Set_" + param,
                  push_live=self._linuxcnc_running and letter in _ROLE_CHANNEL_OF)

    def _load_backlash_settings(self):
        '''
        Reads persisted axis backlash values from RosettaSet_v1.ini (each
        axis's "backlash") into the Backlash spin buttons. No live push:
        Rosetta_Setup/Rosetta_Generate_Local_Ini.py already wrote each active
        letter's value into its [JOINT_n]BACKLASH in Rosetta.local.ini, so
        LinuxCNC started with it. (LinuxCNC 2.9 has no joint.N.backlash
        HAL parameter - the old live push here never worked. The only
        live handle is inihal's ini.N.backlash pin, which
        _axis_set_backlash_letter uses for changes made on this page.)
        set_value below still fires each letter's handler, which finds
        the value unchanged and does nothing.

        Sp0/Sp1's Backlash spin buttons still load/save their persisted
        value (see _axis_set_backlash below), but spindles have no
        joint, so no backlash compensation, live or at startup.
        '''
        if self.builder.get_object("X_Set_Backlash") is None:
            return

        settings = rosetta_settings_io.load_settings()
        axes = settings.get("axes", {})

        for spindle_id in SPINDLE_IDS:
            axis_entry = axes.get(spindle_id)
            if axis_entry is None or "backlash" not in axis_entry:
                continue
            widget = self.builder.get_object(spindle_id + "_Set_Backlash")
            if widget is not None:
                widget.set_value(float(axis_entry["backlash"]))

        # All 8 letters (X,Z,U,V,W,A,B,C), assigned to a channel or not.
        for letter in AXIS_SELECTION_LETTERS:
            axis_entry = axes.get(letter)
            if axis_entry is None or "backlash" not in axis_entry:
                print("No stored backlash found for axis " + letter
                      + " in " + SETTINGS_PATH)
                continue

            value = float(axis_entry["backlash"])

            widget = self.builder.get_object(letter + "_Set_Backlash")
            if widget is not None:
                widget.set_value(value)

    def _load_limit_settings(self):
        '''
        Reads each axis's Max Speed / Max Acceleration / PID Max Output
        (and each spindle's Indexing Max Output) from RosettaSet_v1.ini into
        their spin buttons. No live push - see LIMIT_FIELDS.
        '''
        axes = rosetta_settings_io.load_settings().get("axes", {})
        self._applying_limits = True
        try:
            for axis_id in CHANNEL_ROLES:
                entry = axes.get(axis_id, {})
                for suffix, key in LIMIT_FIELDS.items():
                    widget = self.builder.get_object(axis_id + suffix)
                    if widget is None or key not in entry:
                        continue
                    try:
                        widget.set_value(float(entry[key]))
                    except (TypeError, ValueError):
                        print("Skipping " + axis_id + " " + key + " - not a number")
        finally:
            self._applying_limits = False
        self._remember_limit_values()
        self._update_limit_warnings()

    def _remember_limit_values(self):
        # Each axis's Max Speed / Max Acceleration as last seen, so a
        # change can tell whether the advanced values below it were
        # still at their worked-out value (see Tuning_Limit_Changed).
        self._last_limits = {}
        for axis_id in AXIS_SELECTION_LETTERS:
            for suffix in ("_Set_Max_Speed", "_Set_Max_Acceleration"):
                widget = self.builder.get_object(axis_id + suffix)
                if widget is not None:
                    self._last_limits[axis_id + suffix] = widget.get_value()

    def _spin_value(self, widget_id):
        widget = self.builder.get_object(widget_id)
        return widget.get_value() if widget is not None else None

    def Tuning_Limit_Changed(self, widget):
        '''
        value-changed handler for every Max Speed, Max Acceleration, PID
        Max Output and Indexing Max Output spin button. A Max Speed or
        Max Acceleration change carries through to the advanced values
        worked out from it (Stepgen Max Vel / PID Max Output, or Stepgen
        Max Accel) - but only those still at their worked-out value, so
        a value the operator set by hand is left alone (the warnings
        line then says if it no longer fits).
        '''
        if self._applying_limits:
            return
        name = Gtk.Buildable.get_name(widget)
        axis_id = name.split("_Set_")[0]
        old = self._last_limits.get(name)
        new = widget.get_value()
        if old is not None and name.endswith("_Set_Max_Speed"):
            follow = ((axis_id + "_Set_Max_Vel", rosetta_settings_io.STEPGEN_VEL_FACTOR),
                      (axis_id + "_Set_PID_Max_Output", rosetta_settings_io.PID_OUTPUT_FACTOR))
        elif old is not None and name.endswith("_Set_Max_Acceleration"):
            follow = ((axis_id + "_Set_Max_Accel", rosetta_settings_io.STEPGEN_ACCEL_FACTOR),)
        else:
            follow = ()
        for dependent_id, factor in follow:
            dependent = self.builder.get_object(dependent_id)
            if dependent is None:
                continue
            step = 10 ** -dependent.get_digits()
            if abs(dependent.get_value() - old * factor) <= step:
                dependent.set_value(new * factor)
        if name in self._last_limits:
            self._last_limits[name] = new
        self._update_limit_warnings()

    def _limit_problems(self, axis_id):
        '''One-line descriptions of whatever is wrong with this axis's limits.'''
        problems = []
        scale = self._spin_value(axis_id + "_Set_Scale")
        stepgen_vel = self._spin_value(axis_id + "_Set_Max_Vel")
        stepgen_accel = self._spin_value(axis_id + "_Set_Max_Accel")
        if axis_id in SPINDLE_IDS:
            top, index_out = stepgen_vel, self._spin_value(axis_id + "_Set_Index_Max_Output")
            if index_out is not None and stepgen_vel is not None and index_out > stepgen_vel:
                problems.append("Indexing Max Output is above Max Vel")
        else:
            top = self._spin_value(axis_id + "_Set_Max_Speed")
            accel = self._spin_value(axis_id + "_Set_Max_Acceleration")
            pid_out = self._spin_value(axis_id + "_Set_PID_Max_Output")
            if None in (top, accel, stepgen_vel, stepgen_accel, pid_out):
                return problems
            if stepgen_vel < top * rosetta_settings_io.STEPGEN_VEL_MIN:
                problems.append("Stepgen Max Vel is below Max Speed")
            if stepgen_accel < accel * rosetta_settings_io.STEPGEN_ACCEL_MIN:
                problems.append("Stepgen Max Accel is below 1.5 x Max Acceleration")
            if pid_out < top * rosetta_settings_io.PID_OUTPUT_MIN:
                problems.append("PID Max Output is below Max Speed")
        ceiling = rosetta_settings_io.step_rate_speed_ceiling(scale)
        if ceiling is not None and top is not None and top > ceiling:
            problems.append("%s is more than the step timing allows at this Scale (%.4g)"
                            % ("Max Vel" if axis_id in SPINDLE_IDS else "Max Speed", ceiling))
        return problems

    def _update_limit_warnings(self):
        '''
        Fills each tuning group's Limits_Warning line (just under
        Backlash, so it shows with Advanced settings closed) with every
        axis whose limits are out of order, e.g. "C: Stepgen Max Accel is
        below 1.5 x Max Acceleration". Empty when all is well. A warning
        only - nothing is changed or refused.
        '''
        lines = {"LinearAxes": [], "RotaryAxes": [], "Spindle": []}
        for axis_id in CHANNEL_ROLES:
            for problem in self._limit_problems(axis_id):
                lines[_limit_group(axis_id)].append(axis_id + ": " + problem)
        for group, problems in lines.items():
            label = self.builder.get_object(group + "_Limits_Warning")
            if label is None:
                continue
            if problems:
                label.set_markup('<span foreground="#c06000" weight="bold">'
                                 + GLib.markup_escape_text("\n".join(problems)) + '</span>')
            else:
                label.set_text("")

    def Advanced_Toggled(self, expander, param=None):
        '''
        Shows or hides the grid rows below an "Advanced settings"
        expander - every child of its GtkGrid placed below it. Hidden
        rows take no space, so the page closes up around them. Also
        switches its label's hint between "click to show" and "click to
        hide" (set_text keeps the .ui file's blue/bold attributes).
        '''
        grid = expander.get_parent()
        row = grid.child_get_property(expander, "top-attach")
        shown = expander.get_expanded()
        label = expander.get_label_widget()
        if label is not None:
            label.set_text("Advanced settings (click to " + ("hide" if shown else "show") + ")")
        for child in grid.get_children():
            if grid.child_get_property(child, "top-attach") > row:
                child.set_visible(shown)

    def _fit_notes_height(self, scroll, allocation):
        '''
        Makes the Axis Selection page's notes column as tall as its text
        needs at the width it actually got (14 October 2026). The window's
        own scrolled page measures wrapped text as if each paragraph were
        one long line, so the column came out too short and the end of
        the Expansion Box Notes was cut off; limiting the line length
        fixed that but left the text in a narrow strip.
        '''
        child = scroll.get_child()
        if child is None:
            return
        needed = child.get_preferred_height_for_width(allocation.width)[1]
        if needed != scroll.get_min_content_height():
            # Not from inside size-allocate - set it on the next idle.
            GLib.idle_add(scroll.set_min_content_height, needed)

    def apply_advanced_visibility(self):
        # Called after window.show_all(), which would otherwise show the
        # advanced rows of a closed expander.
        for expander_id in ADVANCED_EXPANDERS:
            expander = self.builder.get_object(expander_id)
            if expander is not None:
                self.Advanced_Toggled(expander)

    def Restore_Defaults(self, button):
        '''
        An axis's Restore Defaults button: puts its advanced values back -
        Stepgen Max Vel / Max Accel and PID Max Output worked out from its
        own Max Speed / Max Acceleration, and the standard PID gains (for
        a spindle, its indexing loop's gains and Indexing Max Output).
        Max Speed, Max Acceleration and Scale are left as they are.
        Saved with Save All Settings, like any other change here.
        '''
        axis_id = Gtk.Buildable.get_name(button).split("_Restore_Defaults")[0]
        values = {}
        if axis_id in SPINDLE_IDS:
            values["_Set_Index_Max_Output"] = rosetta_settings_io.default_limits(axis_id)["index_max_output"]
            pid_suffix = "_Pos"
        else:
            speed = self._spin_value(axis_id + "_Set_Max_Speed")
            accel = self._spin_value(axis_id + "_Set_Max_Acceleration")
            values["_Set_Max_Vel"] = speed * rosetta_settings_io.STEPGEN_VEL_FACTOR
            values["_Set_Max_Accel"] = accel * rosetta_settings_io.STEPGEN_ACCEL_FACTOR
            values["_Set_PID_Max_Output"] = speed * rosetta_settings_io.PID_OUTPUT_FACTOR
            pid_suffix = ""
        for param, value in rosetta_settings_io.default_pid(axis_id).items():
            values["_Set_" + param + pid_suffix] = value
        for suffix, value in values.items():
            widget = self.builder.get_object(axis_id + suffix)
            if widget is not None:
                widget.set_value(value)
        self._update_limit_warnings()
        print("Restored " + axis_id + " advanced settings to defaults")

    def _apply_measurement_system_labels(self, system):
        '''
        Sets the Scale/Max Vel/Max Accel unit-of-measure labels for the
        Linear Axes table (X/Z/U/V/W) to match the given system
        ("Metric" or "Imperial").

        Adapted from Rosetta_main.py's version of this method for
        Rosetta_Settings_v1.ui's consolidated UOM labels: the embedded
        Settings tab this replaces had one Scale/Max_Vel/Max_Accel_UOM
        label PER LETTER (needed because a channel's type used to be
        independently reassignable there); this program's Axis and
        Stepper Motor Tuning page instead shows one representative UOM
        label per table (LinearAxes_*_UOM/RotaryAxes_*_UOM/
        Spindle_*_UOM), since letter always determines type here (see
        _axis_type_for_letter) - a channel can no longer be reassigned
        away from its permanent type, so only the Linear table's three
        labels ever need to change; degrees (Rotary/Angular) and
        revolutions (Spindles) aren't metric or imperial, and those two
        tables' .ui-file-static text is already correct forever. The
        original method also set the main panel's Feed_UOM/IdxDist_UOM
        labels - this program has no main panel widgets, so that part
        is dropped entirely rather than ported as a permanent no-op.
        '''
        if system == "Metric":
            scale_uom, vel_uom, accel_uom = "pulses / mm", "mm / sec", "mm / sec²"
        else:
            scale_uom, vel_uom, accel_uom = "pulses / in", "in / sec", "in / sec²"

        scale_label = self.builder.get_object("LinearAxes_Scale_UOM")
        if scale_label is not None:
            scale_label.set_text(scale_uom)

        vel_label = self.builder.get_object("LinearAxes_Max_Vel_UOM")
        if vel_label is not None:
            vel_label.set_text(vel_uom)

        accel_label = self.builder.get_object("LinearAxes_Max_Accel_UOM")
        if accel_label is not None:
            accel_label.set_text(accel_uom)

        for label_id, uom in (("LinearAxes_Max_Speed_UOM", vel_uom),
                              ("LinearAxes_Max_Acceleration_UOM", accel_uom),
                              ("LinearAxes_PID_Max_Output_UOM", vel_uom)):
            label = self.builder.get_object(label_id)
            if label is not None:
                label.set_text(uom)

        # Linear axes are capped at 1 in/sec (25.4 mm/sec) - the Max
        # Speed boxes' own upper limit (PID Max Output's allows 2x that).
        cap = rosetta_settings_io.linear_speed_cap(system)
        for letter in AXIS_SELECTION_LETTERS:
            if _axis_type_for_letter(letter) != "LINEAR":
                continue
            for suffix, upper in (("_Set_Max_Speed", cap), ("_Set_PID_Max_Output", 2 * cap)):
                widget = self.builder.get_object(letter + suffix)
                if widget is not None:
                    widget.get_adjustment().set_upper(upper)

    def _load_measurement_system(self):
        '''
        Reads the persisted Measurement System ("Metric"/"Imperial", default
        "Imperial" if absent - matching Rosetta.ini's shipped inch/INCH default)
        from RosettaSet_v1.ini, applies it to the Measurement_System combo box
        and the Linear Axes table's unit-of-measure labels.
        '''
        settings = rosetta_settings_io.load_settings()
        system = settings.get("measurement_system", "Imperial")
        if system not in ("Metric", "Imperial"):
            system = "Imperial"

        combo = self.builder.get_object("Measurement_System")
        if combo is not None:
            self._applying_measurement_system = True
            combo.set_active(0 if system == "Metric" else 1)
            self._applying_measurement_system = False

        self._apply_measurement_system_labels(system)

    def _load_device_names(self):
        '''
        Reads the persisted device-name list (RosettaSet_v1.ini's
        <device_names> block) and applies it to the Other page's Device
        Names GtkTextView, one name per line - mirrors
        _load_measurement_system above.
        '''
        view = self.builder.get_object("Device_Names")
        if view is None:
            return

        names = _read_persisted_device_names()

        self._applying_device_names = True
        view.get_buffer().set_text("\n".join(names))
        self._applying_device_names = False

    def _read_device_names(self):
        '''
        Reads the maintained device-name list straight from the live
        Device Names widget (kept in sync with RosettaSet_v1.ini by
        Device_Names_Changed on every edit) rather than re-reading the
        file - used by _run_export_selection_dialog to populate each
        axis's comment dropdown. Blank/whitespace-only lines are
        dropped.
        '''
        view = self.builder.get_object("Device_Names")
        if view is None:
            return []
        buf = view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _rebuild_all_channel_combo_items(self):
        '''
        Populates every Channel_0N_Axis combo with the full role pool
        (CHANNEL_ROLES - all 8 axis letters plus Sp0/Sp1, since 13
        September 2026) and reselects that combo's own current role.
        Every role is always offered here - any channel is freely
        selectable to any role, with duplicates (and Sp1-without-Sp0)
        flagged live instead (see _update_validation_warnings) and only
        actually blocked from being persisted, not from being picked in
        the first place.

        Also refreshes each channel's Channel_0N_Type label -
        informational only (not itself selectable): Linear/Angular for
        an axis letter (_axis_type_for_letter), or "Spindle" for Sp0/
        Sp1, which have no Linear/Angular concept at all.

        Called both by _load_channel_assignments (startup) and by
        Channel_0N_Axis_Changed itself (every time one combo's choice
        changes).
        '''
        if self.builder.get_object("Channel_00_Axis") is None:
            return

        for channel_id in CHANNEL_IDS:
            combo = self.builder.get_object("Channel_" + channel_id + "_Axis")
            if combo is None:
                continue

            current = self._channel_assignments[channel_id]

            combo.remove_all()
            for role in CHANNEL_ROLES:
                combo.append_text(role)
            combo.set_active(CHANNEL_ROLES.index(current))

            type_label = self.builder.get_object("Channel_" + channel_id + "_Type")
            if type_label is not None:
                if current in SPINDLE_IDS:
                    type_label.set_text("Spindle")
                else:
                    type_label.set_text(_axis_type_for_letter(current).title())

    def _update_validation_warnings(self):
        '''
        Recomputes every channel's Channel_0N_Warning label from the
        current in-memory assignment (self._channel_assignments) and
        returns whether the whole assignment is safe to persist.

        Two independent rules, checked together so neither's warning
        can silently overwrite the other's on the same channel:
          - a role picked on more than one channel ("Duplicate!")
          - Sp1 assigned to a channel while Sp0 isn't assigned to any
            ("Sp1 needs Sp0!") - Sp1's speed is always computed as a
            percentage of Sp0's (see Rosetta_main.py's Sp1_Set_Move_Pct/
            _Sp1_Send_Pct), so running Sp1 without Sp0 assigned isn't
            just unsupported, it's meaningless - there's no speed for
            the percentage to apply to. Indexing is the one exception
            (Sp0/Sp1 can be indexed independently or together - see
            Sp0_Idx_Bool/Sp1_Idx_Bool in Rosetta_main.py), but that doesn't
            change this rule: both still need to be assigned to a
            channel to be usable at all.
        A channel can only ever trigger the first rule (duplicates are
        per-channel) or the second (Sp1-specific, and there's at most
        one channel holding Sp1), so the two never collide on the same
        label.

        Any role can still be picked freely at the dropdown - both
        rules are flagged immediately rather than rejected there.
        Channel_0N_Axis_Changed uses this method's return value to
        decide whether the assignment is safe to persist - actually
        saving/showing the restart notice is refused for as long as any
        violation remains, resuming automatically on whichever change
        clears it.

        Returns True if at least one violation exists (False, and every
        warning cleared, if the assignment is fully valid).
        '''
        if self.builder.get_object("Channel_00_Axis") is None:
            return False

        role_counts = {}
        for role in self._channel_assignments.values():
            role_counts[role] = role_counts.get(role, 0) + 1

        active = self._active_roles()
        sp0_assigned = "Sp0" in active

        any_violation = False
        for channel_id, role in self._channel_assignments.items():
            warning = self.builder.get_object("Channel_" + channel_id + "_Warning")
            if warning is None:
                continue
            if role_counts[role] > 1:
                warning.set_markup('<span foreground="red" weight="bold">Duplicate!</span>')
                any_violation = True
            elif role == "Sp1" and role in active and not sp0_assigned:
                warning.set_markup('<span foreground="red" weight="bold">Sp1 needs Sp0!</span>')
                any_violation = True
            else:
                warning.set_text("")

        return any_violation

    def _active_roles(self):
        '''
        The roles on channels in use right now: the base box's six, plus
        the expansion box's four while it's marked connected.
        '''
        return {role for channel_id, role in self._channel_assignments.items()
                if self._expansion_box or channel_id not in EXPANSION_CHANNELS}

    def _load_expansion_box(self):
        '''
        Reads the persisted "expansion_box" setting into the Axis
        Selection page's checkbox and greys the expansion side to match.
        Must run before _load_channel_assignments/_load_limit_jacks, which
        use self._expansion_box.
        '''
        self._expansion_box = _read_persisted_expansion_box()
        check = self.builder.get_object("Expansion_Box_Connected")
        if check is not None:
            self._applying_expansion_box = True
            check.set_active(self._expansion_box)
            self._applying_expansion_box = False
        self._apply_expansion_sensitivity()

    def _apply_expansion_sensitivity(self):
        '''Greys channels 06-09 and limit jacks 4-6 out unless the expansion box is connected.'''
        ids = (["Channel_" + c + "_Axis" for c in EXPANSION_CHANNELS]
               + ["Limit_Jack_" + j + "_Axis" for j in EXPANSION_LIMIT_JACKS])
        for wid in ids:
            w = self.builder.get_object(wid)
            while w is not None and not isinstance(w, Gtk.Frame):
                w = w.get_parent()
            if w is not None:
                w.set_sensitive(self._expansion_box)

    def Expansion_Box_Toggled(self, widget):
        '''
        Persists the expansion box checkbox, greys or ungreys its side of
        both pages, and re-checks the channels and limit jacks - roles on
        channels 06-09 count only while it's connected (e.g. Sp1 there
        needs Sp0 somewhere in use). Takes effect at the next launch.
        '''
        if self._applying_expansion_box:
            return
        self._expansion_box = widget.get_active()
        _save_expansion_box(self._expansion_box)
        self._apply_expansion_sensitivity()
        if self._update_validation_warnings():
            return
        if self._rebuild_limit_jack_combos():
            _save_limit_jacks(self._limit_jacks)
        self._update_limit_jack_warnings()

    def _load_channel_assignments(self):
        '''
        Reads the persisted channel -> axis letter assignment
        (RosettaSet_v1.ini's <channel_assignments> block) and populates the
        Axis Selection tab's 8 channel combos (widened from 6 channels/
        8 letters to 8 channels/10 roles - any of X,Z,U,V,W,A,B,C,Sp0,
        Sp1 assignable to any of the 8 physical channels - 13 September
        2026, see CLAUDE.md).

        Adapted from Rosetta_main.py's version of this method: the embedded
        Settings tab this replaces also read/populated a per-channel
        Type combo here (<channel_types>) - there is no such combo in
        this program's UI (type is always derived from the letter, see
        _axis_type_for_letter), so that half is dropped entirely rather
        than ported as a no-op. _rebuild_all_channel_combo_items does
        still populate a read-only Channel_0N_Type label from the
        current role, informational only.
        '''
        if self.builder.get_object("Channel_00_Axis") is None:
            return

        self._channel_assignments = _read_persisted_channel_assignments()

        self._applying_channel_assignments = True
        self._rebuild_all_channel_combo_items()
        self._applying_channel_assignments = False

        # _read_persisted_channel_assignments already falls back to the
        # shipped defaults rather than ever returning a duplicate or a
        # Sp1-without-Sp0 assignment, so this should always clear every
        # warning - called anyway so the tab's own state stays
        # consistent if that ever changes.
        self._update_validation_warnings()

    def _load_limit_jacks(self):
        '''
        Reads the persisted limit jack -> axis letter map (RosettaSet_v1.ini's
        "limit_switches") and populates the Axis Selection page's three
        Limit_Jack_N_Axis combos (see _rebuild_limit_jack_combos).
        '''
        if self.builder.get_object("Limit_Jack_1_Axis") is None:
            return

        self._limit_jacks = _read_persisted_limit_jacks()
        self._limit_jack_notices = {}
        if self._rebuild_limit_jack_combos():
            _save_limit_jacks(self._limit_jacks)
        self._update_limit_jack_warnings()

    def _rebuild_limit_jack_combos(self):
        '''
        Repopulates every Limit_Jack_N_Axis combo with "Not used" plus,
        for each axis letter currently assigned to a channel only, its
        "(both ends)", "min" and "max" choices - a jack can't be pointed
        at an axis that isn't configured for use. A jack
        whose axis is no longer assigned (a channel was changed, or the
        persisted file names one) is switched to "Not used", with a
        notice saying so (self._limit_jack_notices, shown by
        _update_limit_jack_warnings until that jack is next changed).
        Returns True if any jack was switched, so the caller can persist.
        '''
        if self.builder.get_object("Limit_Jack_1_Axis") is None:
            return False

        assigned = self._active_roles()
        values = ("",) + tuple(
            letter + suffix
            for letter in AXIS_SELECTION_LETTERS if letter in assigned
            for suffix in LIMIT_ENDS)

        cleared = False
        self._applying_limit_jacks = True
        for jack in LIMIT_JACKS:
            jack_values = values
            if jack in EXPANSION_LIMIT_JACKS and not self._expansion_box:
                # Greyed out with no expansion box: keep its choice as it
                # is (shown, not cleared) so connecting the box brings it back.
                if self._limit_jacks[jack] not in jack_values:
                    jack_values = jack_values + (self._limit_jacks[jack],)
            else:
                parsed = _parse_limit_value(self._limit_jacks[jack])
                if parsed and parsed[0] not in assigned:
                    self._limit_jacks[jack] = ""
                    self._limit_jack_notices[jack] = parsed[0] + " not assigned - cleared"
                    cleared = True
            combo = self.builder.get_object("Limit_Jack_" + jack + "_Axis")
            if combo is None:
                continue
            combo.remove_all()
            for value in jack_values:
                combo.append(value, _limit_value_label(value))
            combo.set_active(jack_values.index(self._limit_jacks[jack]))
        self._applying_limit_jacks = False
        return cleared

    def _load_estop_button(self):
        '''
        Reads the persisted E-stop button choice (RosettaSet_v1.ini's
        "estop_button") into the Axis Selection page's checkbox.
        '''
        check = self.builder.get_object("Estop_Button_Connected")
        if check is None:
            return
        _install_estop_frame_style()
        self._applying_estop_button = True
        check.set_active(_read_persisted_estop_button())
        self._applying_estop_button = False
        self._update_estop_warning(check.get_active())

    def _update_estop_warning(self, connected):
        '''
        Shows a warning under the E-Stop Button checkbox while it's
        checked: with the button marked connected, an empty plug holds
        the machine in E-stop.
        '''
        warning = self.builder.get_object("Estop_Button_Warning")
        if warning is None:
            return
        if connected:
            warning.set_markup(ESTOP_WARNING_MARKUP)
        else:
            warning.set_text("")

    def Estop_Button_Toggled(self, widget):
        '''
        Persists the E-stop button checkbox. Takes effect at the next
        LinuxCNC launch (Rosetta_Generate_Local_Ini.py).
        '''
        self._update_estop_warning(widget.get_active())
        if self._applying_estop_button:
            return
        _save_estop_button(widget.get_active())

    def _load_signal_tower(self):
        '''
        Reads the persisted signal tower choice (RosettaSet_v1.ini's
        "signal_tower") into the Axis Selection page's checkbox.
        '''
        check = self.builder.get_object("Signal_Tower_Connected")
        if check is None:
            return
        self._applying_signal_tower = True
        check.set_active(_read_persisted_signal_tower())
        self._applying_signal_tower = False

    def Signal_Tower_Toggled(self, widget):
        '''
        Persists the signal tower checkbox. Takes effect at the next
        LinuxCNC launch (Rosetta_Generate_Local_Ini.py).
        '''
        if self._applying_signal_tower:
            return
        _save_signal_tower(widget.get_active())

    def _load_startup_file_check(self):
        '''
        Reads the persisted startup file check choice (RosettaSet_v1.ini's
        "startup_file_check") into the Startup_Check_Abort / _Warn
        radios.
        '''
        radio = self.builder.get_object("Startup_Check_" + _read_persisted_startup_file_check().capitalize())
        if radio is None:
            return
        self._applying_startup_file_check = True
        radio.set_active(True)
        self._applying_startup_file_check = False

    def Startup_Check_Toggled(self, widget):
        '''
        Persists the startup file check choice. Each click fires
        "toggled" on both radios; only the one becoming active saves.
        '''
        if self._applying_startup_file_check or not widget.get_active():
            return
        _save_startup_file_check(Gtk.Buildable.get_name(widget).split("_")[-1].lower())

    def _load_not_enabled_action(self):
        '''
        Reads the persisted choice (RosettaSet_v1.ini's
        "not_enabled_action") into the Not_Enabled_Ask / _Enable radios.
        '''
        radio = self.builder.get_object("Not_Enabled_" + _read_persisted_not_enabled_action().capitalize())
        if radio is None:
            return
        self._applying_not_enabled_action = True
        radio.set_active(True)
        self._applying_not_enabled_action = False

    def Not_Enabled_Toggled(self, widget):
        '''
        Persists the not-enabled choice. Each click fires "toggled" on
        both radios; only the one becoming active saves.
        '''
        if self._applying_not_enabled_action or not widget.get_active():
            return
        _save_not_enabled_action(Gtk.Buildable.get_name(widget).split("_")[-1].lower())

    def _load_limit_switch_type(self):
        '''
        Reads the persisted limit switch type (RosettaSet_v1.ini's
        "limit_switch_type") into the Limit_Switch_NC / _NO radios.
        '''
        radio = self.builder.get_object("Limit_Switch_" + _read_persisted_limit_switch_type())
        if radio is None:
            return
        self._applying_limit_switch_type = True
        radio.set_active(True)
        self._applying_limit_switch_type = False

    def Limit_Switch_Type_Toggled(self, widget):
        '''
        Persists the limit switch type. Each click fires "toggled" on
        both radios; only the one becoming active saves. Takes effect at
        the next LinuxCNC launch.
        '''
        if self._applying_limit_switch_type or not widget.get_active():
            return
        _save_limit_switch_type(Gtk.Buildable.get_name(widget).split("_")[-1])

    def _load_done_sound(self):
        '''
        Reads the persisted attention-sound choice (RosettaSet_v1.ini's
        "done_sound") into the Axis Selection page's Done_Sound combo.
        '''
        combo = self.builder.get_object("Done_Sound")
        if combo is None:
            return
        self._applying_done_sound = True
        combo.set_active_id(_read_persisted_done_sound())
        self._applying_done_sound = False

    def Done_Sound_Changed(self, widget):
        '''
        Persists the attention-sound choice. Takes effect the next time
        LinuxCNC starts.
        '''
        if self._applying_done_sound or widget.get_active_id() is None:
            return
        _save_done_sound(widget.get_active_id())

    def _load_fault_sound(self):
        '''
        Reads the persisted fault-siren choice (RosettaSet_v1.ini's
        "fault_sound") into the Axis Selection page's Fault_Sound combo.
        '''
        combo = self.builder.get_object("Fault_Sound")
        if combo is None:
            return
        self._applying_fault_sound = True
        combo.set_active_id(_read_persisted_fault_sound())
        self._applying_fault_sound = False

    def Fault_Sound_Changed(self, widget):
        '''
        Persists the fault-siren choice. Takes effect the next time
        LinuxCNC starts.
        '''
        if self._applying_fault_sound or widget.get_active_id() is None:
            return
        _save_fault_sound(widget.get_active_id())

    def _load_version_label(self):
        '''
        Appends ", Machine S/N <n>" to each page's "O/S ..." label
        once an owner has set a friendly serial number (SERIAL_PATH) -
        same idea as Rosetta_main.py's main-panel version label. Left as
        shipped (no suffix) until a serial has been set.
        '''
        try:
            with open(SERIAL_PATH, "r") as f:
                serial = f.read().strip()
        except OSError:
            serial = ""
        if not serial:
            return
        suffix = ", Machine S/N " + serial
        for label_id in OS_VERSION_LABEL_IDS:
            label = self.builder.get_object(label_id)
            if label is not None:
                label.set_text(label.get_text() + suffix)

    def _update_limit_jack_warnings(self):
        '''
        Recomputes every Limit_Jack_N_Warning label and returns whether
        the jack choices are safe to persist:
          - two jacks covering the same end of the same axis blocks
            saving, same as a duplicate channel role: an identical choice
            shows "Duplicate!", an overlapping one (e.g. "B (both ends)"
            with "B min") shows "Conflict!". A min/max pair is fine.
          - otherwise, any notice left by _rebuild_limit_jack_combos
            for a jack it switched to "Not used" (informational only).
        Returns True if a blocking violation exists.
        '''
        if self.builder.get_object("Limit_Jack_1_Warning") is None:
            return False

        in_use = [j for j in LIMIT_JACKS if self._expansion_box or j not in EXPANSION_LIMIT_JACKS]
        parsed = {jack: (_parse_limit_value(self._limit_jacks[jack]) if jack in in_use else None)
                  for jack in LIMIT_JACKS}
        any_violation = False
        for jack in LIMIT_JACKS:
            warning = self.builder.get_object("Limit_Jack_" + jack + "_Warning")
            if warning is None:
                continue
            problem = None
            if parsed[jack]:
                for other in LIMIT_JACKS:
                    if other == jack or not parsed[other] or parsed[other][0] != parsed[jack][0]:
                        continue
                    if parsed[other] == parsed[jack]:
                        problem = "Duplicate!"
                    elif _limit_ends_conflict(parsed[other][1], parsed[jack][1]):
                        problem = problem or "Conflict!"
            if problem:
                warning.set_markup('<span foreground="red" weight="bold">' + problem + '</span>')
                any_violation = True
            elif jack in self._limit_jack_notices:
                warning.set_markup('<span foreground="#c06000" weight="bold">'
                                   + self._limit_jack_notices[jack] + '</span>')
            else:
                warning.set_text("")
        return any_violation

    def _load_max_jog_speed(self):
        '''
        Reads the persisted Max Jog Speed (default 1.0, matching Rosetta.ini's
        shipped [TRAJ]/[DISPLAY] MAX_LINEAR_VELOCITY) from RosettaSet_v1.ini
        and applies it to the Max Jog Speed spin button.
        '''
        settings = rosetta_settings_io.load_settings()
        value = float(settings.get("max_jog_speed", 1.0))

        spin = self.builder.get_object("Max_Jog_Speed")
        if spin is not None:
            self._applying_max_jog_speed = True
            spin.set_value(value)
            self._applying_max_jog_speed = False

    def _load_velocity_settings(self):
        '''
        Reads each of VELOCITY_SETTINGS' persisted values from
        RosettaSet_v1.ini (default to Rosetta.ini's own shipped value if never
        persisted) and applies them to their spin buttons - mirrors
        _load_max_jog_speed above, generalized to all five at once
        under one shared guard flag (they're only ever loaded together,
        so one flag covering the whole batch is enough).
        '''
        settings = rosetta_settings_io.load_settings()

        self._applying_velocity_settings = True
        try:
            for widget_id, (tag, default) in VELOCITY_SETTINGS.items():
                value = float(settings.get(tag, default))

                spin = self.builder.get_object(widget_id)
                if spin is not None:
                    spin.set_value(value)
        finally:
            self._applying_velocity_settings = False

    def _save_axis_comment(self, axis_id, text):
        '''
        Writes a single axis's comment back into RosettaSet_v1.ini's
        usercomment value for that axis. The main panel (a separate
        program) is what actually displays this field - Rosetta_Settings
        can only patch the file, not the live widget - so the main
        panel only picks up the new text at its own next startup.
        '''
        settings = rosetta_settings_io.load_settings()
        settings.setdefault("axes", {}).setdefault(axis_id, {})["usercomment"] = text
        rosetta_settings_io.save_settings(settings)
        print("Saved " + axis_id + " comment")

    def _read_pid_gains(self, widget_id_for_param):
        '''
        Reads P/I/D/FF0/FF1/FF2 from one axis's/spindle loop's own
        widgets into a plain {param: value} dict, for embedding
        directly in a settings-file JSON "pid"/"pid_pos"/"pid_vel"
        entry.
        '''
        values = {}
        for param in PID_PARAMS:
            widget = self.builder.get_object(widget_id_for_param(param))
            if widget is not None:
                values[param] = widget.get_value()
        return values

    def Settings_Notes_Changed(self, buffer):
        # Wired to the Notes GtkTextView's GtkTextBuffer "changed"
        # signal. The Notes field is free-text scratch space only -
        # nothing persists it.
        pass

    def Open_Manual_Link(self, widget):
        # One of the User Manual buttons beside the Axis Selection
        # page's notes - opens its MANUAL_LINKS page in the browser.
        url = MANUAL_LINKS.get(Gtk.Buildable.get_name(widget))
        if url:
            webbrowser.open(url)
            print("Opening website " + url)

    def Measurement_System_Changed(self, widget):
        if self._applying_measurement_system:
            return

        system = widget.get_active_text()
        if system not in ("Metric", "Imperial"):
            return

        self._apply_measurement_system_labels(system)
        _save_measurement_system(system)

    def Device_Names_Changed(self, buffer):
        # Wired to the Device Names GtkTextView's GtkTextBuffer
        # "changed" signal - mirrors Measurement_System_Changed's
        # save-immediately pattern. Suppressed while _load_device_names
        # is itself the one driving the buffer text at startup.
        if self._applying_device_names:
            return
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        names = [line.strip() for line in text.splitlines() if line.strip()]
        _save_device_names(names)

    def Max_Jog_Speed_Changed(self, widget):
        if self._applying_max_jog_speed:
            return

        if not self._jog_speeds_ok(widget, "linear"):
            return
        value = widget.get_value()
        _save_max_jog_speed(value)

    # Each jog speed group's (min, default, max) spin buttons, with the
    # RosettaSet_v1.ini key and fallback each is loaded from - used to check
    # min <= default <= max and to put a refused value back.
    JOG_SPEED_GROUPS = {
        "linear": (("Min_Linear_Velocity", "min_linear_velocity", VELOCITY_SETTINGS["Min_Linear_Velocity"][1]),
                   ("Default_Linear_Velocity", "default_linear_velocity", VELOCITY_SETTINGS["Default_Linear_Velocity"][1]),
                   ("Max_Jog_Speed", "max_jog_speed", 1.0)),
        "angular": (("Min_Angular_Velocity", "min_angular_velocity", VELOCITY_SETTINGS["Min_Angular_Velocity"][1]),
                    ("Default_Angular_Velocity", "default_angular_velocity", VELOCITY_SETTINGS["Default_Angular_Velocity"][1]),
                    ("Max_Angular_Velocity", "max_angular_velocity", VELOCITY_SETTINGS["Max_Angular_Velocity"][1])),
    }

    def _jog_speeds_ok(self, widget, group):
        '''
        True if the group's jog speeds are still in order (Minimum <=
        Default <= Maximum) after widget's change. Otherwise tells the
        operator, puts widget back to its saved value, and returns False
        so the caller doesn't save it.
        '''
        spins = [self.builder.get_object(wid) for wid, _, _ in self.JOG_SPEED_GROUPS[group]]
        if any(spin is None for spin in spins):
            return True
        low, default, high = (spin.get_value() for spin in spins)
        if low <= default <= high:
            return True

        name = "Linear Axes" if group == "linear" else "Rotary (Angular) Axis"
        _show_settings_error(
            widget,
            "%s Jog Speed must be Minimum \u2264 Default \u2264 Maximum.\n\n"
            "Minimum %.4f, Default %.4f, Maximum %.4f - the change was not saved.\n\n"
            "Change the other values first if you need to move this one further."
            % (name, low, default, high))

        settings = rosetta_settings_io.load_settings()
        for wid, key, fallback in self.JOG_SPEED_GROUPS[group]:
            if self.builder.get_object(wid) is widget:
                self._applying_velocity_settings = True
                self._applying_max_jog_speed = True
                try:
                    widget.set_value(float(settings.get(key, fallback)))
                finally:
                    self._applying_velocity_settings = False
                    self._applying_max_jog_speed = False
        return False

    def _tuning_values(self):
        '''
        The current Scale, Max Vel, Max Accel and PID values for every
        axis - the values Save All Settings writes that are NOT saved
        as soon as they change (Backlash is, so it's left out). Compared
        with self._saved_tuning to spot unsaved changes on close.
        '''
        values = {}
        for axis_id in CHANNEL_ROLES:
            for field in ("_Set_Scale", "_Set_Max_Vel", "_Set_Max_Accel") + tuple(LIMIT_FIELDS):
                widget = self.builder.get_object(axis_id + field)
                if widget is not None:
                    values[axis_id + field] = round(widget.get_value(), 6)
            suffixes = ("_Pos",) if axis_id in SPINDLE_IDS else ("",)
            for suffix in suffixes:
                for param in PID_PARAMS:
                    widget = self.builder.get_object(axis_id + "_Set_" + param + suffix)
                    if widget is not None:
                        values[axis_id + "_Set_" + param + suffix] = round(widget.get_value(), 6)
        return values

    def confirm_close(self, window, event=None):
        '''
        delete-event handler for the main window: if any Scale, Max Vel,
        Max Accel or PID value has changed since it was last saved, asks
        whether to save first. Returns True (keep the window open) if
        the operator cancels.
        '''
        # After Restore from USB the settings file on disk is the
        # restored one - nothing here may be saved over it.
        if getattr(self, "_closing_after_restore", False):
            return False
        if self._tuning_values() == self._saved_tuning:
            return False
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Save your changes before closing?",
        )
        dialog.format_secondary_text(
            "Some Scale, speed, acceleration or PID values have changed since they were "
            "last saved. If you close without saving, those changes will be lost.")
        dialog.add_button("Close Without Saving", Gtk.ResponseType.NO)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save and Close", Gtk.ResponseType.YES)
        dialog.set_default_response(Gtk.ResponseType.YES)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self._write_rebset_snapshot()
            return False
        return response != Gtk.ResponseType.NO

    def Settings_Save(self, widget):
        if self.builder.get_object("X_Set_Scale") is None:
            return

        print("=================================================")
        print("FUNCTION Settings_Save")
        self._write_rebset_snapshot()

    def _write_rebset_snapshot(self):
        '''
        Writes this program's live Scale/Backlash/Max Vel/Max Accel/PID
        widget values into RosettaSet_v1.ini's per-axis entries. Reads the
        whole file once, patches every axis's dict entry in memory,
        then writes it back once - unlike the shutdown path
        (Rosetta_Scale_Persist.py), which patches and writes incrementally
        since it goes through separate halcmd calls per value.
        '''
        settings = rosetta_settings_io.load_settings()
        axes = settings.setdefault("axes", {})

        for axis_id in CHANNEL_ROLES:
            axis_entry = axes.setdefault(axis_id, {})

            scale_widget = self.builder.get_object(axis_id + "_Set_Scale")
            if scale_widget is not None:
                axis_entry["scale"] = scale_widget.get_value()

            backlash_widget = self.builder.get_object(axis_id + "_Set_Backlash")
            if backlash_widget is not None:
                axis_entry["backlash"] = backlash_widget.get_value()

            max_vel_widget = self.builder.get_object(axis_id + "_Set_Max_Vel")
            if max_vel_widget is not None:
                axis_entry["max_vel"] = max_vel_widget.get_value()

            max_accel_widget = self.builder.get_object(axis_id + "_Set_Max_Accel")
            if max_accel_widget is not None:
                axis_entry["max_accel"] = max_accel_widget.get_value()

            for suffix, key in LIMIT_FIELDS.items():
                limit_widget = self.builder.get_object(axis_id + suffix)
                if limit_widget is not None:
                    axis_entry[key] = limit_widget.get_value()

            if axis_id in SPINDLE_IDS:
                for suffix, block_tag in (("Pos", "pid_pos"),):
                    values = self._read_pid_gains(
                        lambda param, axis_id=axis_id, suffix=suffix: axis_id + "_Set_" + param + "_" + suffix
                    )
                    if values:
                        axis_entry.setdefault(block_tag, {}).update(values)
            else:
                values = self._read_pid_gains(lambda param, axis_id=axis_id: axis_id + "_Set_" + param)
                if values:
                    axis_entry.setdefault("pid", {}).update(values)

        rosetta_settings_io.save_settings(settings)
        self._saved_tuning = self._tuning_values()
        print("Saved live scale/backlash/max vel/max accel/PID values to " + SETTINGS_PATH)

    def Settings_Save_As(self, widget):
        if self.builder.get_object("X_Set_Scale") is None:
            return

        print("=================================================")
        print("FUNCTION Settings_Save_As")

        self._write_rebset_snapshot()

        os.makedirs(ROSETTASET_DEFAULT_DIR, exist_ok=True)

        dialog = Gtk.FileChooserDialog(
            title="Save Settings As",
            transient_for=widget.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(ROSETTASET_DEFAULT_DIR)
        dialog.set_do_overwrite_confirmation(True)
        # Today's date, not SETTINGS_PATH's own fixed "RosettaSet_v1.ini"
        # name - this is a copy going somewhere else, so defaulting to
        # the exact name of the file it's copied from just invites
        # confusing the two.
        dialog.set_current_name(time.strftime("%Y-%m-%d") + ".RosettaSet_v1.ini")

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Rosetta Settings (*.ini)")
        file_filter.add_pattern("*.ini")
        dialog.add_filter(file_filter)

        response = dialog.run()
        path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        if not path:
            print("Settings_Save_As cancelled")
            return

        if not path.endswith(".ini"):
            path += ".ini"

        try:
            shutil.copyfile(SETTINGS_PATH, path)
        except OSError as e:
            _show_settings_error(widget, "Could not write " + path + ":\n" + str(e))
            return

        print("Saved a copy of " + SETTINGS_PATH + " to " + path)

    def Settings_Load(self, widget):
        if self.builder.get_object("X_Set_Scale") is None:
            return

        print("=================================================")
        print("FUNCTION Settings_Load")

        os.makedirs(ROSETTASET_DEFAULT_DIR, exist_ok=True)

        dialog = Gtk.FileChooserDialog(
            title="Load Settings",
            transient_for=widget.get_toplevel(),
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Load", Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(ROSETTASET_DEFAULT_DIR)

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Rosetta Settings (*.ini)")
        file_filter.add_pattern("*.ini")
        dialog.add_filter(file_filter)

        response = dialog.run()
        path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        if not path:
            print("Settings_Load cancelled")
            return

        try:
            with open(path, "r") as f:
                data = rosetta_settings_io.parse_settings_text(f.read())
        except (OSError, ValueError) as e:
            _show_settings_error(widget, "Could not read " + path + ":\n" + str(e))
            return

        if not isinstance(data, dict) or "axes" not in data:
            _show_settings_error(widget, path + " is not a Rosetta settings file.")
            return

        self._apply_settings_root(widget, data, path, "usercomment")

    def Export_Settings(self, widget):
        if self.builder.get_object("X_Set_Scale") is None:
            return

        print("=================================================")
        print("FUNCTION Export_Settings")

        selected = self._run_export_selection_dialog(widget)
        if not selected:
            print("Export_Settings cancelled")
            return

        comments = set(selected.get("comments", {}).values())
        if not comments:
            _show_settings_error(
                widget,
                "Pick a device name for at least one exported axis - it's "
                "used to name the exported file."
            )
            return
        if len(comments) == 1:
            file_name = re.sub(r'[\\/]', '-', comments.pop()) + EXPORT_EXTENSION
        else:
            # More than one different device name was selected - no
            # single name to build the file's default name from, so
            # fall back to today's date instead of refusing to export.
            file_name = time.strftime("%Y-%m-%d") + EXPORT_EXTENSION

        os.makedirs(ROSETTASET_DEFAULT_DIR, exist_ok=True)

        dialog = Gtk.FileChooserDialog(
            title="Export Settings",
            transient_for=widget.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Export", Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(ROSETTASET_DEFAULT_DIR)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(file_name)

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Rosetta Export (*" + EXPORT_EXTENSION + ")")
        file_filter.add_pattern("*" + EXPORT_EXTENSION)
        dialog.add_filter(file_filter)

        response = dialog.run()
        path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        if not path:
            print("Export_Settings cancelled")
            return

        if not path.endswith(EXPORT_EXTENSION):
            path += EXPORT_EXTENSION

        data = {"axes": {}}

        def get_axis_entry(axis_id):
            return data["axes"].setdefault(axis_id, {})

        # Each selected axis exports Scale, Backlash, Max Vel/Max Accel,
        # and PID together as one unit - see _run_export_selection_dialog
        # for why these no longer get independent checkboxes.
        exported = []
        for axis_id in selected.get("axes", ()):
            spin = self.builder.get_object(axis_id + "_Set_Scale")
            if spin is not None:
                get_axis_entry(axis_id)["scale"] = spin.get_value()
                exported.append(axis_id + " Scale")

            backlash_spin = self.builder.get_object(axis_id + "_Set_Backlash")
            if backlash_spin is not None:
                get_axis_entry(axis_id)["backlash"] = backlash_spin.get_value()
                exported.append(axis_id + " Backlash")

            max_vel_spin = self.builder.get_object(axis_id + "_Set_Max_Vel")
            if max_vel_spin is not None:
                get_axis_entry(axis_id)["max_vel"] = max_vel_spin.get_value()
                exported.append(axis_id + " Max Vel")

            max_accel_spin = self.builder.get_object(axis_id + "_Set_Max_Accel")
            if max_accel_spin is not None:
                get_axis_entry(axis_id)["max_accel"] = max_accel_spin.get_value()
                exported.append(axis_id + " Max Accel")

            for suffix, key in LIMIT_FIELDS.items():
                limit_spin = self.builder.get_object(axis_id + suffix)
                if limit_spin is not None:
                    get_axis_entry(axis_id)[key] = limit_spin.get_value()

            if axis_id in SPINDLE_IDS:
                for suffix in ("Pos",):
                    block_tag = "pid_pos"
                    self._export_pid_block(
                        get_axis_entry(axis_id), block_tag,
                        lambda param, axis_id=axis_id, suffix=suffix: axis_id + "_Set_" + param + "_" + suffix
                    )
                exported.append(axis_id + " PID")
            else:
                self._export_pid_block(get_axis_entry(axis_id), "pid",
                                        lambda param, axis_id=axis_id: axis_id + "_Set_" + param)
                exported.append(axis_id + " PID")

        for axis_id, comment in selected.get("comments", {}).items():
            get_axis_entry(axis_id)["comment"] = comment
            exported.append(axis_id + " Comment (" + comment + ")")

        if selected.get("measurement_system"):
            combo = self.builder.get_object("Measurement_System")
            system = combo.get_active_text() if combo is not None else None
            if system:
                data["measurement_system"] = system
                exported.append("Measurement System")

        try:
            rosetta_settings_io.save_settings(data, path)
        except OSError as e:
            _show_settings_error(widget, "Could not write " + path + ":\n" + str(e))
            return

        print("Exported " + ", ".join(exported) + " to " + path)

    def _export_pid_block(self, axis_entry, block_tag, widget_id_for_param):
        '''
        Reads P/I/D/FF0/FF1/FF2 from this axis's/spindle loop's own
        widgets into a "pid"/"pid_pos"/"pid_vel" dict on axis_entry -
        the same shape RosettaSet_v1.ini already uses, so a value
        round-trips through Import_Settings/_load_pid_settings
        identically either way.
        '''
        block = {}
        for param in PID_PARAMS:
            widget = self.builder.get_object(widget_id_for_param(param))
            if widget is None:
                continue
            block[param] = widget.get_value()
        if block:
            axis_entry[block_tag] = block

    def _run_export_selection_dialog(self, widget):
        '''
        Modal checklist: one row per axis, each with a single checkbox
        covering that axis's Scale, Backlash, Max Vel/Max Accel, and PID
        together, plus a Device dropdown (populated from the Other
        page's maintained Device Names list) to optionally label that
        axis's export with which physical device it belongs to.

        Each Device combo defaults to whatever's currently set on the
        main panel's own comment field for that axis (X/Z/U/V/W/B - see
        COMMENT_AXES), via _read_persisted_axis_comment against
        SETTINGS_PATH - the main panel is a separate program from this
        one, so its live widget isn't reachable directly. Sp0/Sp1 have
        no such field, so they default to SPINDLE_DEFAULT_DEVICE_NAME
        instead.

        Returns {"axes": [...ids...], "comments":
        {axis_id: name, ...}, "measurement_system": bool} on Export, or
        None if cancelled/nothing was selected.
        '''
        dialog = Gtk.Dialog(
            title="Export Settings - Choose What to Include",
            transient_for=widget.get_toplevel(),
            modal=True,
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Export", Gtk.ResponseType.OK,
        )

        content = dialog.get_content_area()
        content.set_border_width(8)
        content.set_spacing(6)

        select_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        select_all_btn = Gtk.Button(label="Select All")
        select_none_btn = Gtk.Button(label="Select None")
        select_row.pack_start(select_all_btn, False, False, 0)
        select_row.pack_start(select_none_btn, False, False, 0)
        content.pack_start(select_row, False, False, 0)

        content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        def section_label(text):
            label = Gtk.Label()
            label.set_markup("<b>" + text + "</b>")
            label.set_xalign(0)
            return label

        device_names = self._read_device_names()
        comments_settings = rosetta_settings_io.load_settings()

        axis_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        content.pack_start(axis_col, False, False, 0)

        # Sized so the "Device" header lines up with the combo boxes
        # below it, not just with wherever the widest axis checkbox
        # happens to end.
        axis_label_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        axis_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        axis_label = section_label("Axis")
        axis_label_group.add_widget(axis_label)
        axis_header.pack_start(axis_label, False, False, 0)
        axis_header.pack_start(section_label("Device"), False, False, 0)
        axis_col.pack_start(axis_header, False, False, 0)

        checks = {}
        comment_combos = {}
        for axis_id in CHANNEL_ROLES:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            check = Gtk.CheckButton(label=axis_id)
            check.set_active(True)
            check.set_tooltip_text(
                "Exports this axis's Scale, Backlash, and Stepper Motor "
                "Tuning together."
            )
            axis_label_group.add_widget(check)
            row.pack_start(check, False, False, 0)

            combo = Gtk.ComboBoxText()
            combo.append_text(DEVICE_COMBO_PLACEHOLDER)
            for name in device_names:
                combo.append_text(name)

            stored = (_read_persisted_axis_comment(axis_id, comments_settings)
                      or SPINDLE_DEFAULT_DEVICE_NAME.get(axis_id, ""))
            try:
                combo.set_active(device_names.index(stored) + 1 if stored else 0)
            except ValueError:
                combo.set_active(0)

            combo.set_tooltip_text(
                "Optional: label this axis's export with one of the "
                "device names maintained on the Other page."
            )
            row.pack_start(combo, False, False, 0)

            axis_col.pack_start(row, False, False, 0)
            checks[axis_id] = check
            comment_combos[axis_id] = combo

        content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        measurement_check = Gtk.CheckButton(label="Measurement System")
        measurement_check.set_active(True)
        content.pack_start(measurement_check, False, False, 0)

        device_note = Gtk.Label()
        device_note.set_markup(
            "<i>You must select a device for any axis data you wish to "
            "save. You can change that name on the file save screen "
            "which pops up next.</i>"
        )
        device_note.set_xalign(0)
        device_note.set_line_wrap(True)
        device_note.set_max_width_chars(60)
        content.pack_start(device_note, False, False, 0)

        all_checks = list(checks.values()) + [measurement_check]
        select_all_btn.connect("clicked", lambda b: [c.set_active(True) for c in all_checks])
        select_none_btn.connect("clicked", lambda b: [c.set_active(False) for c in all_checks])

        content.show_all()

        result = None
        while True:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                break

            axes = [axis_id for axis_id, c in checks.items() if c.get_active()]
            comments = {
                axis_id: text
                for axis_id, combo in comment_combos.items()
                for text in [_combo_selected_device(combo)]
                if text
            }
            measurement_system = measurement_check.get_active()
            if not axes and not comments and not measurement_system:
                _show_settings_error(widget, "Select at least one item to export.")
                continue

            result = {
                "axes": axes,
                "comments": comments,
                "measurement_system": measurement_system,
            }
            break

        dialog.destroy()
        return result

    def Import_Settings(self, widget):
        if self.builder.get_object("X_Set_Scale") is None:
            return

        print("=================================================")
        print("FUNCTION Import_Settings")

        os.makedirs(ROSETTASET_DEFAULT_DIR, exist_ok=True)

        dialog = Gtk.FileChooserDialog(
            title="Import Settings",
            transient_for=widget.get_toplevel(),
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Import", Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(ROSETTASET_DEFAULT_DIR)

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Rosetta Export (*" + EXPORT_EXTENSION + ", *"
                             + OLD_EXPORT_EXTENSION + ")")
        file_filter.add_pattern("*" + EXPORT_EXTENSION)
        file_filter.add_pattern("*" + OLD_EXPORT_EXTENSION)
        dialog.add_filter(file_filter)

        response = dialog.run()
        path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        if not path:
            print("Import_Settings cancelled")
            return

        try:
            with open(path, "r") as f:
                data = rosetta_settings_io.parse_settings_text(f.read())
        except (OSError, ValueError) as e:
            _show_settings_error(widget, "Could not read " + path + ":\n" + str(e))
            return

        if not isinstance(data, dict) or "axes" not in data:
            _show_settings_error(widget, path + " is not a Rosetta export file.")
            return

        self._apply_settings_root(widget, data, path, "comment")

    def _apply_settings_root(self, widget, data, path, comment_key):
        '''
        Applies whatever subset of axis Scale/Backlash/Max Vel/Max
        Accel/PID/comment/Measurement System values a parsed settings
        dict contains to the live widgets, then reports what changed.
        Shared by Import_Settings (small "comment"-keyed
        Export_Settings subset files) and Settings_Load (full
        "usercomment"-keyed RosettaSet_v1.ini-shaped snapshots) -
        comment_key is the only thing that differs between those two
        file shapes. Each value is applied through its own widget
        handler (<Axis>_Set_Scale/<Axis>_Set_Backlash/
        Measurement_System_Changed) rather than written to disk
        directly - it keeps the usual per-axis safety checks (motion
        abort, disable-if-enabled) in the loop exactly as if the
        operator had typed/selected each value themselves.
        '''
        imported = []
        comment_imported = False
        # Apply the file's own stepgen/PID values as they are, rather
        # than recalculating them as its Max Speed/Acceleration go in.
        self._applying_limits = True
        for axis_id, axis_entry in data.get("axes", {}).items():
            if axis_id not in CHANNEL_ROLES:
                continue
            if not isinstance(axis_entry, dict):
                continue

            # Scale and PID are independent - a file may carry either,
            # both, or neither for a given axis, so check each on its own
            # rather than skipping the whole axis entry when one is
            # absent.
            if "scale" in axis_entry:
                spin = self.builder.get_object(axis_id + "_Set_Scale")
                if spin is not None:
                    try:
                        scale = float(axis_entry["scale"])
                    except (TypeError, ValueError):
                        print("Skipping " + axis_id + " scale - not a number: " + str(axis_entry["scale"]))
                        scale = None
                    if scale is not None:
                        spin.set_value(scale)  # fires <Axis>_Set_Scale: abort/disable-if-enabled/halcmd setp
                        imported.append(axis_id + " Scale")

            if "backlash" in axis_entry:
                spin = self.builder.get_object(axis_id + "_Set_Backlash")
                if spin is not None:
                    try:
                        backlash = float(axis_entry["backlash"])
                    except (TypeError, ValueError):
                        print("Skipping " + axis_id + " backlash - not a number: " + str(axis_entry["backlash"]))
                        backlash = None
                    if backlash is not None:
                        spin.set_value(backlash)  # fires <Axis>_Set_Backlash: halcmd setp
                        imported.append(axis_id + " Backlash")

            if "max_vel" in axis_entry:
                spin = self.builder.get_object(axis_id + "_Set_Max_Vel")
                if spin is not None:
                    try:
                        max_vel = float(axis_entry["max_vel"])
                    except (TypeError, ValueError):
                        print("Skipping " + axis_id + " max_vel - not a number: " + str(axis_entry["max_vel"]))
                        max_vel = None
                    if max_vel is not None:
                        spin.set_value(max_vel)  # fires <Axis>_Set_Max_Vel: halcmd setp
                        imported.append(axis_id + " Max Vel")

            if "max_accel" in axis_entry:
                spin = self.builder.get_object(axis_id + "_Set_Max_Accel")
                if spin is not None:
                    try:
                        max_accel = float(axis_entry["max_accel"])
                    except (TypeError, ValueError):
                        print("Skipping " + axis_id + " max_accel - not a number: " + str(axis_entry["max_accel"]))
                        max_accel = None
                    if max_accel is not None:
                        spin.set_value(max_accel)  # fires <Axis>_Set_Max_Accel: halcmd setp
                        imported.append(axis_id + " Max Accel")

            for suffix, key in LIMIT_FIELDS.items():
                spin = self.builder.get_object(axis_id + suffix)
                if key not in axis_entry or spin is None:
                    continue
                try:
                    spin.set_value(float(axis_entry[key]))
                    imported.append(axis_id + " " + key.replace("_", " ").title())
                except (TypeError, ValueError):
                    print("Skipping " + axis_id + " " + key + " - not a number: " + str(axis_entry[key]))

            # Comment (device name): only COMMENT_AXES have a live
            # comment field to apply it to (Sp0/Sp1 don't - the main
            # panel has no spindle comment entries), so a file's comment
            # for a spindle is informational-only and doesn't round-trip
            # back into anything here. _save_axis_comment only patches
            # RosettaSet_v1.ini on disk - it can't reach into the main
            # panel's own Comment widget, a separate program with no
            # live IPC to this one. The panel only picks up the new text
            # at its own next startup - hence comment_imported below.
            comment_value = axis_entry.get(comment_key)
            if comment_value is not None and axis_id in COMMENT_AXES:
                self._save_axis_comment(axis_id, comment_value)
                imported.append(axis_id + " Comment")
                comment_imported = True

            pid_applied = False
            if axis_id in SPINDLE_IDS:
                for suffix in ("Pos",):
                    block_tag = "pid_pos"
                    if self._import_pid_block(
                        axis_entry, block_tag,
                        lambda param, axis_id=axis_id, suffix=suffix: axis_id + "_Set_" + param + "_" + suffix
                    ):
                        pid_applied = True
            else:
                pid_applied = self._import_pid_block(
                    axis_entry, "pid", lambda param, axis_id=axis_id: axis_id + "_Set_" + param
                )
            if pid_applied:
                imported.append(axis_id + " PID")

        self._applying_limits = False
        self._remember_limit_values()
        self._update_limit_warnings()

        measurement_system = data.get("measurement_system")
        if measurement_system in ("Metric", "Imperial"):
            combo = self.builder.get_object("Measurement_System")
            if combo is not None:
                combo.set_active(0 if measurement_system == "Metric" else 1)  # fires Measurement_System_Changed
                imported.append("Measurement System")

        if imported:
            print("Imported " + ", ".join(imported) + " from " + path)
            dialog = Gtk.MessageDialog(
                transient_for=widget.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Imported: " + ", ".join(imported),
            )
            if comment_imported:
                dialog.format_secondary_text(
                    "The imported comment(s) are saved, but the main "
                    "panel's Comment field runs as a separate program and "
                    "won't show the new text until you restart LinuxCNC."
                )
            dialog.run()
            dialog.destroy()
        else:
            _show_settings_error(widget, "Nothing recognizable to import in " + path)

    def _import_pid_block(self, axis_entry, block_tag, widget_id_for_param):
        '''
        Mirror of _export_pid_block: reads a "pid"/"pid_pos"/"pid_vel"
        dict (if present) and applies each P/I/D/FF0/FF1/FF2 value it
        contains to that param's own widget via set_value() - fires the
        same _pid_set handler a live edit would (pushes straight to the
        live pid.* HAL gain pin). Returns True if anything was actually
        applied.
        '''
        block = axis_entry.get(block_tag)
        if not isinstance(block, dict):
            return False

        applied = False
        for param in PID_PARAMS:
            if param not in block:
                continue

            widget = self.builder.get_object(widget_id_for_param(param))
            if widget is None:
                continue

            try:
                value = float(block[param])
            except (TypeError, ValueError):
                print("Skipping " + widget_id_for_param(param) + " - not a number: " + str(block[param]))
                continue

            widget.set_value(value)
            applied = True

        return applied

    def Sp0_Set_Scale(self, widget):
        '''
        Value-changed handler for Sp0's Scale spin button. Sp0's
        ENA-light/override signal name ("sp0") is a fixed constant -
        that identity never changes - but since 13 September 2026 its
        stepgen channel is no longer fixed either (any of 10 roles can
        be assigned to any of 8 channels - see CLAUDE.md), so it's
        resolved through _ROLE_CHANNEL_OF at call time, same as the 8
        letter-labeled Scale handlers (_axis_set_scale_letter).
        '''
        print("=================================================")
        print("FUNCTION Sp0_Set_Scale")

        channel_id = _ROLE_CHANNEL_OF.get("Sp0")
        if channel_id is None:
            print("Sp0 is not currently assigned to a channel - value kept, no live HAL write")
            return

        # Stop any Run Operation spindle rotation (M3/M4) before this
        # scale change lands - a large change to position-scale while
        # the spindle is actively spinning under S-word/M3/M4 control
        # could otherwise cause a runaway once the new scale takes
        # effect.
        #
        # Only if the machine is actually ON: this handler also fires
        # from _load_scale_settings's programmatic spin.set_value() (the
        # startup auto-restore from RosettaSet_v1.ini), which runs before
        # the operator has powered on/reset E-stop, when there's no
        # spinning spindle to stop anyway.
        s.poll()
        if s.task_state == linuxcnc.STATE_ON:
            if s.task_state != linuxcnc.MODE_MDI:
                    c.mode(linuxcnc.MODE_MDI)
                    c.wait_complete()
            c.mdi("M5")
            c.wait_complete()
        else:
            print("Sp0_Set_Scale: machine not ON - skipping M5 (nothing to stop)")

        Sp0_Scale = round(widget.get_value(), 1)

        # Sp0_ENA-light belongs to the main panel's HAL component
        # ("gladevcp"); read it cross-component via halcmd. To disable
        # the axis, set the sp0-ena-settings-allow signal FALSE (see
        # _axis_set_scale_letter's docstring for why "sets" on the
        # signal, not "setp" on the pin - Rosetta_PostGUI_v1.hal nets that
        # signal from gladevcp.Sp0_Ena_Override).
        status_pin = "gladevcp.Sp0_ENA-light"

        try:
            result = subprocess.run(
                ["halcmd", "getp", status_pin],
                check=True,
                capture_output=True,
                text=True
            )
            is_enabled = result.stdout.strip().upper() in ("TRUE", "1")
            print(status_pin + " = " + result.stdout.strip())

            if is_enabled:
                print("Sp0 axis is enabled - disabling")
                try:
                    subprocess.run(
                        ["halcmd", "sets", "sp0-ena-settings-allow", "FALSE"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Set sp0-ena-settings-allow = FALSE")
                except subprocess.CalledProcessError as e:
                    print("Error setting sp0-ena-settings-allow: " + e.stderr)
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")
            else:
                print("Sp0 axis is already disabled")
        except subprocess.CalledProcessError as e:
            print("Error checking " + status_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

        hal_pin = _stepgen_pin(channel_id, ".position-scale")
        cmd = ["halcmd", "setp", hal_pin, str(Sp0_Scale)]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(Sp0_Scale))
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

    def Sp1_Set_Scale(self, widget):
        '''
        Value-changed handler for Sp1's Scale spin button - mirrors
        Sp0_Set_Scale above exactly (dynamic stepgen channel via
        _ROLE_CHANNEL_OF), for the sp1-ena-settings-allow signal.
        '''
        print("=================================================")
        print("FUNCTION Sp1_Set_Scale")

        channel_id = _ROLE_CHANNEL_OF.get("Sp1")
        if channel_id is None:
            print("Sp1 is not currently assigned to a channel - value kept, no live HAL write")
            return

        s.poll()
        if s.task_state == linuxcnc.STATE_ON:
            if s.task_state != linuxcnc.MODE_MDI:
                    c.mode(linuxcnc.MODE_MDI)
                    c.wait_complete()
            c.mdi("M5")
            c.wait_complete()
        else:
            print("Sp1_Set_Scale: machine not ON - skipping M5 (nothing to stop)")

        Sp1_Scale = round(widget.get_value(), 1)

        status_pin = "gladevcp.Sp1_ENA-light"

        try:
            result = subprocess.run(
                ["halcmd", "getp", status_pin],
                check=True,
                capture_output=True,
                text=True
            )
            is_enabled = result.stdout.strip().upper() in ("TRUE", "1")
            print(status_pin + " = " + result.stdout.strip())

            if is_enabled:
                print("Sp1 axis is enabled - disabling")
                try:
                    subprocess.run(
                        ["halcmd", "sets", "sp1-ena-settings-allow", "FALSE"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Set sp1-ena-settings-allow = FALSE")
                except subprocess.CalledProcessError as e:
                    print("Error setting sp1-ena-settings-allow: " + e.stderr)
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")
            else:
                print("Sp1 axis is already disabled")
        except subprocess.CalledProcessError as e:
            print("Error checking " + status_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

        hal_pin = _stepgen_pin(channel_id, ".position-scale")
        cmd = ["halcmd", "setp", hal_pin, str(Sp1_Scale)]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(Sp1_Scale))
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

    def __init__(self, builder):
        self.builder = builder

        # main() only ever constructs HandlerClass after confirming
        # LinuxCNC is NOT running (see _linuxcnc_is_running/main's
        # blocking dialog) - so this is always False in practice, but
        # every _load_* method below still checks it explicitly rather
        # than assuming, so they degrade the same way if HandlerClass
        # is ever constructed some other way (as this session's own
        # verification scripts already do). Without this gate, each
        # _load_* method below would attempt a `halcmd setp` for every
        # single axis/spindle/PID-gain pin and print an individual
        # "parameter or pin not found" error for each one when nothing
        # is running to own those pins (confirmed live 4 September
        # 2026, ~90 such lines from one normal startup) - computing
        # this once and skipping the doomed attempts entirely, with one
        # informational line instead, is far less alarming for what is
        # in fact the expected, intended way to run this program.
        self._linuxcnc_running = _linuxcnc_is_running()
        if not self._linuxcnc_running:
            print("LinuxCNC is not running - settings loaded from RosettaSet_v1.ini only; live HAL pins were not touched.")

        # Suppresses Measurement_System_Changed's save/patch/popup while
        # _load_measurement_system is itself the one driving the combo box
        # at startup (see combo.set_active there) - a startup load should
        # not re-save RosettaSet_v1.ini or pop up the restart notice.
        self._applying_measurement_system = False

        # Same suppression as _applying_measurement_system above, for
        # _load_device_names driving the Device Names text buffer at
        # startup.
        self._applying_device_names = False

        # Same suppression as _applying_measurement_system above, for
        # _load_max_jog_speed driving the Max Jog Speed spin button at
        # startup.
        self._applying_max_jog_speed = False

        # Same suppression as above, for _load_velocity_settings driving
        # the five VELOCITY_SETTINGS spin buttons at startup.
        self._applying_velocity_settings = False

        # Same suppression as above, for _load_channel_assignments (and
        # Channel_0N_Axis_Changed's own re-filtering rebuild - see
        # _rebuild_all_channel_combo_items) driving the six Axis Selection
        # combos.
        self._applying_channel_assignments = False
        self._applying_expansion_box = False

        # Same suppression as above, for _load_limit_jacks driving the
        # three Limit_Jack_N_Axis combos.
        self._applying_limit_jacks = False

        # Same suppression as above, for _load_estop_button driving the
        # Estop_Button_Connected checkbox.
        self._applying_estop_button = False

        # Same suppression as above, for _load_signal_tower driving the
        # Signal_Tower_Connected checkbox.
        self._applying_signal_tower = False

        # Same suppression as above, for _load_startup_file_check driving
        # the Startup_Check_Abort / _Warn radios.
        self._applying_startup_file_check = False

        # Same suppression as above, for _load_not_enabled_action driving
        # the Not_Enabled_Ask / _Enable radios.
        self._applying_not_enabled_action = False

        # Same suppression as above, for _load_limit_switch_type driving
        # the Limit_Switch_NC / _NO radios.
        self._applying_limit_switch_type = False

        # Same suppression as above, for _load_done_sound driving the
        # Done_Sound combo.
        self._applying_done_sound = False

        # Same suppression as above, for _load_fault_sound driving the
        # Fault_Sound combo.
        self._applying_fault_sound = False

        # Restore persisted axis scale values (RosettaSet_v1.ini) into the
        # spin buttons and the real stepgen scale pins.
        self._load_scale_settings()

        # Restore persisted P/I/D/FF0/FF1/FF2 gains (RosettaSet_v1.ini) into
        # the PID spin buttons and the live pid.* HAL gain pins.
        self._load_pid_settings()

        # Restore persisted backlash values (RosettaSet_v1.ini) into the
        # Backlash spin buttons and the live joint.N.backlash HAL
        # parameters.
        self._load_backlash_settings()

        # Restore persisted Max Vel/Max Accel values (RosettaSet_v1.ini)
        # into the spin buttons and the live stepgen maxvel/maxaccel
        # HAL params.
        self._load_max_vel_accel_settings()

        # Restore the persisted Measurement System (RosettaSet_v1.ini) into
        # the Measurement_System combo box and the Linear Axes table's
        # unit-of-measure labels.
        self._load_measurement_system()

        # Restore each axis's Max Speed / Max Acceleration / PID Max
        # Output and each spindle's Indexing Max Output (RosettaSet_v1.ini).
        # After _load_measurement_system, which sets the linear Max Speed
        # boxes' upper limit for the units in use.
        self._applying_limits = False
        self._last_limits = {}
        self._load_limit_settings()
        # Any value the warnings line checks - keep it current.
        for axis_id in CHANNEL_ROLES:
            for suffix in ("_Set_Scale", "_Set_Max_Vel", "_Set_Max_Accel"):
                widget = self.builder.get_object(axis_id + suffix)
                if widget is not None:
                    widget.connect("value-changed", lambda _w: self._update_limit_warnings())

        # Restore the persisted device-name list (RosettaSet_v1.ini) into
        # the Other page's Device Names text box.
        self._load_device_names()

        # Axis Selection's notes column: see _fit_notes_height.
        notes = self.builder.get_object("Axis_Selection_Notes_Scroll")
        if notes is not None:
            notes.connect("size-allocate", self._fit_notes_height)

        # Restore the persisted channel -> axis letter assignment
        # (RosettaSet_v1.ini) into the Axis Selection tab's six combos.
        self._load_expansion_box()
        self._load_channel_assignments()

        # Restore the persisted limit jack -> axis letter choices
        # (RosettaSet_v1.ini) into the Axis Selection tab's three Limit Jack
        # combos. Must follow _load_channel_assignments - its "Axis not
        # assigned" notice checks the channel assignment.
        self._load_limit_jacks()

        # Restore the persisted E-stop button choice (RosettaSet_v1.ini) into
        # the Axis Selection tab's E-Stop Button checkbox.
        self._load_estop_button()

        # Restore the persisted signal tower choice (RosettaSet_v1.ini) into
        # the Axis Selection tab's Signal Tower checkbox.
        self._load_signal_tower()
        self._load_limit_switch_type()
        self._load_startup_file_check()
        self._load_not_enabled_action()
        self._load_done_sound()
        self._load_fault_sound()

        # Append ", Machine S/N <n>" to each page's "O/S ..." label
        # if this owner has set a friendly serial number.
        self._load_version_label()

        # Restore the persisted Max Jog Speed (RosettaSet_v1.ini) into the
        # Max Jog Speed spin button.
        self._load_max_jog_speed()

        # Restore the five persisted VELOCITY_SETTINGS values
        # (RosettaSet_v1.ini) into the jog-speed spin buttons.
        self._load_velocity_settings()

        # Let the mouse wheel scroll the page even when the cursor is
        # over one of its many spin buttons/combo boxes, rather than only
        # working over the shrinking gaps between them - see
        # _redirect_scroll_to_viewport.
        viewport = self.builder.get_object("viewport1")
        if viewport is not None:
            self._install_viewport_scroll_redirect(viewport)

        # Baseline for confirm_close's unsaved-changes check - everything
        # above has just loaded the saved values into the widgets.
        self._saved_tuning = self._tuning_values()


# ------------------------------------------------------------------
# Generated per-channel handlers, for all 8 selectable letters
# (AXIS_SELECTION_LETTERS) and the two fixed spindles (Sp0/Sp1).
#
# Widgets are bound per LETTER, not per internal id, for Scale/Backlash/
# Max Vel/Max Accel/PID: the widget labeled e.g. "B" must always mean
# "whichever channel currently wears letter B," not "channel 05,
# forever" - see _axis_set_scale_letter's docstring for the live bug
# this fixes (found live 3 September 2026, in Rosetta_main.py, before this
# program existed).
#
# This has to produce real, named methods rather than a __getattr__
# dispatcher: GtkBuilder discovers handlers via dir(instance) fed into
# builder.connect_signals(), and dir() does not enumerate names that
# only exist through __getattr__.

def _axis_set_scale_letter(letter):
    '''
    Value-changed handler for one of the 8 letter-labeled Scale spin
    buttons (<letter>_Set_Scale, letter in AXIS_SELECTION_LETTERS). The
    live stepgen pin is resolved through _ROLE_CHANNEL_OF at call time,
    rather than a closure-captured constant. If this letter isn't
    currently assigned to any channel, the value is simply kept (and
    persisted at shutdown by Rosetta_Scale_Persist.py) with no live HAL
    write to make.

    scale is rounded to 3 decimal places, matching this widget's own
    "digits" property in the .ui file.

    The axis-disable step uses `halcmd sets <letter>-ena-settings-allow
    FALSE` rather than a direct pin write - this program has no HAL
    component of its own, so it can't do the embedded Settings tab's
    old `self.halcomp[...] = False` trick (that only worked because the
    writer WAS the netted component, REBCnfg). Since 4 September 2026,
    Rosetta_PostGUI_v1.hal nets that "allow" signal from the main panel's
    own always-running HAL component ("gladevcp.<Axis>_Ena_Override")
    instead - a real component this program can influence, cross-
    process, the same way the main panel's own _clear_ena_override
    already does in the other direction (`halcmd sets ... TRUE`). Once
    a pin is netted to a signal, halcmd can't "setp" the pin directly
    ("pin is connected to a signal") - the signal itself has to be set
    instead, via "halcmd sets".

    Since 13 September 2026, "<letter>_ENA-light"/"<letter>-ena-
    settings-allow" are simply the LETTER's own permanent names, not a
    channel-slot's fixed internal id showing a possibly-different
    current letter - Rosetta_PostGUI_v1.hal's ena-toggle chains are letter-
    keyed forever now, never renamed by channel reassignment (see
    Rosetta_Setup/Rosetta_Generate_Local_Ini.py's module docstring). A/C have
    no such chain (no main-panel ENA button exists for them yet -
    "engine only" scope) - the getp below simply fails harmlessly for
    them (caught, printed, and skipped) and the scale write still
    proceeds.
    '''
    def handler(self, widget):
        print("=================================================")
        print("FUNCTION " + letter + "_Set_Scale")

        channel_id = _ROLE_CHANNEL_OF.get(letter)
        if channel_id is None:
            print(letter + " is not currently assigned to a channel - value kept, no live HAL write")
            return

        c.abort()
        c.wait_complete()

        scale = round(widget.get_value(), 3)
        hal_pin = _stepgen_pin(channel_id, ".position-scale")
        status_pin = "gladevcp." + letter + "_ENA-light"
        ena_signal = letter.lower() + "-ena-settings-allow"

        try:
            result = subprocess.run(
                ["halcmd", "getp", status_pin],
                check=True,
                capture_output=True,
                text=True
            )
            is_enabled = result.stdout.strip().upper() in ("TRUE", "1")
            print(status_pin + " = " + result.stdout.strip())

            if is_enabled:
                print(letter + " axis is enabled - disabling")
                try:
                    subprocess.run(
                        ["halcmd", "sets", ena_signal, "FALSE"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Set " + ena_signal + " = FALSE")
                except subprocess.CalledProcessError as e:
                    print("Error setting " + ena_signal + ": " + e.stderr)
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")
            else:
                print(letter + " axis is already disabled")
        except subprocess.CalledProcessError as e:
            print("Error checking " + status_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

        cmd = ["halcmd", "setp", hal_pin, str(scale)]
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(scale) + " (" + letter + ")")
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

        max_vel_widget = self.builder.get_object(letter + "_Set_Max_Vel")
        if max_vel_widget is not None:
            _warn_if_max_vel_exceeds_ceiling(
                self, widget, letter, channel_id, scale, max_vel_widget)
    handler.__name__ = letter + "_Set_Scale"
    return handler

for _letter in AXIS_SELECTION_LETTERS:
    setattr(HandlerClass, _letter + "_Set_Scale", _axis_set_scale_letter(_letter))
del _letter

def _axis_set_backlash(axis):
    '''
    Value-changed handler for Sp0_Set_Backlash/Sp1_Set_Backlash only.

    Since 13 September 2026, spindles have no joint.N.backlash pin to
    push to at all - see _load_backlash_settings's docstring for why
    (joint numbers are now dynamic and belong entirely to whichever
    axis letters are active; a spindle guessing at one risked
    corrupting a real letter's backlash). Rosetta_Scale_Persist.py no
    longer reads a live pin for spindle backlash either (there isn't
    one), so unlike every other Settings widget, this one persists
    directly to RosettaSet_v1.ini on every change instead of relying on
    that shutdown round-trip - otherwise the value would just be lost.
    '''
    def handler(self, widget):
        value = widget.get_value()
        settings = rosetta_settings_io.load_settings()
        settings.setdefault("axes", {}).setdefault(axis, {})["backlash"] = value
        rosetta_settings_io.save_settings(settings)
        print("Saved " + axis + " backlash = " + str(value) + " (no live HAL pin to push to)")
    handler.__name__ = axis + "_Set_Backlash"
    return handler

for _axis_id in ("Sp0", "Sp1"):
    setattr(HandlerClass, _axis_id + "_Set_Backlash", _axis_set_backlash(_axis_id))
del _axis_id

def _axis_set_backlash_letter(letter):
    '''
    Value-changed handler for one of the 8 letter-labeled Backlash spin
    buttons (<letter>_Set_Backlash, letter in AXIS_SELECTION_LETTERS).

    Saves the value to RosettaSet_v1.ini straight away (the next launch
    writes it into [JOINT_n]BACKLASH - see Rosetta_Setup/
    Rosetta_Generate_Local_Ini.py's _overlay_backlash) and, if LinuxCNC is
    running and letter is assigned to a channel, applies it live
    through inihal's ini.N.backlash pin, N being letter's joint number
    this session (JOINT_NUMBER). milltask picks up a change to that pin
    on its next cycle. Saved here rather than at shutdown because
    Rosetta_Scale_Persist.py runs after milltask - and with it the ini.N.*
    pins - may already be gone. Does nothing if the value matches
    what's already saved (as when _load_backlash_settings fills the
    field in).
    '''
    def handler(self, widget):
        value = widget.get_value()
        settings = rosetta_settings_io.load_settings()
        axis_entry = settings.setdefault("axes", {}).setdefault(letter, {})
        if axis_entry.get("backlash") == value:
            return
        axis_entry["backlash"] = value
        rosetta_settings_io.save_settings(settings)
        print("Saved " + letter + " backlash = " + str(value))

        if letter not in JOINT_NUMBER or not self._linuxcnc_running:
            print(letter + " backlash takes effect the next time LinuxCNC starts")
            return
        hal_pin = "ini." + str(JOINT_NUMBER[letter]) + ".backlash"
        try:
            subprocess.run(
                ["halcmd", "setp", hal_pin, str(value)],
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(value) + " (" + letter + ")")
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
    handler.__name__ = letter + "_Set_Backlash"
    return handler

for _letter in AXIS_SELECTION_LETTERS:
    setattr(HandlerClass, _letter + "_Set_Backlash", _axis_set_backlash_letter(_letter))
del _letter

def _axis_set_max(axis, param):
    '''
    Value-changed handler for Sp0/Sp1's Max Vel/Max Accel spin buttons.
    Since 13 September 2026, a spindle's channel is no longer fixed
    either - resolved through _ROLE_CHANNEL_OF at call time, same
    pattern as _axis_set_max_letter below. The 8 letters are bound to
    that separate function.

    Pushes the new value straight to the live
    hm2_7i92.0.stepgen.NN.maxvel/.maxaccel HAL param. param is "Vel" or
    "Accel". Like backlash (and unlike scale), no need to disable the
    axis first.
    '''
    hal_suffix = ".maxvel" if param == "Vel" else ".maxaccel"
    def handler(self, widget):
        channel_id = _ROLE_CHANNEL_OF.get(axis)
        if channel_id is None:
            print(axis + " is not currently assigned to a channel - value kept, no live HAL write")
            return

        hal_pin = _stepgen_pin(channel_id, hal_suffix)
        value = widget.get_value()
        try:
            subprocess.run(
                ["halcmd", "setp", hal_pin, str(value)],
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(value))
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

        if param == "Vel":
            scale_widget = self.builder.get_object(axis + "_Set_Scale")
            if scale_widget is not None:
                _warn_if_max_vel_exceeds_ceiling(
                    self, widget, axis, channel_id, scale_widget.get_value(), widget)
    handler.__name__ = axis + "_Set_Max_" + param
    return handler

for _axis in ("Sp0", "Sp1"):
    setattr(HandlerClass, _axis + "_Set_Max_Vel", _axis_set_max(_axis, "Vel"))
    setattr(HandlerClass, _axis + "_Set_Max_Accel", _axis_set_max(_axis, "Accel"))
del _axis

def _axis_set_max_letter(letter, param):
    '''
    Value-changed handler for one of the 8 letter-labeled Max Vel/Max
    Accel spin buttons (<letter>_Set_Max_Vel/_Accel, letter in
    AXIS_SELECTION_LETTERS). letter has no fixed channel of its own, so
    the live stepgen pin is resolved through _ROLE_CHANNEL_OF at call
    time, same as _axis_set_scale_letter/_axis_set_backlash_letter.
    '''
    hal_suffix = ".maxvel" if param == "Vel" else ".maxaccel"
    def handler(self, widget):
        channel_id = _ROLE_CHANNEL_OF.get(letter)
        if channel_id is None:
            print(letter + " is not currently assigned to a channel - value kept, no live HAL write")
            return

        hal_pin = _stepgen_pin(channel_id, hal_suffix)
        value = widget.get_value()
        try:
            subprocess.run(
                ["halcmd", "setp", hal_pin, str(value)],
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(value) + " (" + letter + ")")
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")

        if param == "Vel":
            scale_widget = self.builder.get_object(letter + "_Set_Scale")
            if scale_widget is not None:
                _warn_if_max_vel_exceeds_ceiling(
                    self, widget, letter, channel_id, scale_widget.get_value(), widget)
    handler.__name__ = letter + "_Set_Max_" + param
    return handler

for _letter in AXIS_SELECTION_LETTERS:
    setattr(HandlerClass, _letter + "_Set_Max_Vel", _axis_set_max_letter(_letter, "Vel"))
    setattr(HandlerClass, _letter + "_Set_Max_Accel", _axis_set_max_letter(_letter, "Accel"))
del _letter

def _channel_axis_changed(channel_id):
    '''
    Generic "changed" handler for one Axis Selection role combo.
    Records the new choice and refreshes every combo
    (_rebuild_all_channel_combo_items) - every role (any of the 8 axis
    letters or 2 spindles, since 13 September 2026) is always
    selectable, duplicates and an unassigned Sp0 with Sp1 assigned are
    no longer prevented at the dropdown. Instead,
    _update_validation_warnings flags every channel with either
    problem; as long as any violation remains, this handler
    deliberately does NOT persist the assignment - that only happens
    once the whole assignment is valid, at which point it fires on
    that clearing change. No "restart required" notice is
    shown here (unlike Measurement System/Max Jog Speed/velocity
    settings, which can be changed while LinuxCNC is running): this
    program refuses to run at all while LinuxCNC is up (see
    _linuxcnc_is_running), so every axis assignment change already
    happens before the next launch, not during a live session.
    '''
    def handler(self, widget):
        if self._applying_channel_assignments:
            return

        role = widget.get_active_text()
        if role not in CHANNEL_ROLES:
            return

        # A role held by a greyed-out expansion channel (no expansion box)
        # can't be taken back there, so it would stay "Duplicate!" for
        # good (found by Rich 14 October 2026). Swap instead: that channel
        # takes the role this one gives up, so every role is still on
        # exactly one channel when the expansion box is connected later.
        previous = self._channel_assignments[channel_id]
        if not self._expansion_box:
            for other_id in EXPANSION_CHANNELS:
                if other_id != channel_id and self._channel_assignments[other_id] == role:
                    self._channel_assignments[other_id] = previous
                    print("Channel " + other_id + " (expansion box) takes " + previous
                          + " so " + role + " can go on channel " + channel_id)

        self._channel_assignments[channel_id] = role

        self._applying_channel_assignments = True
        self._rebuild_all_channel_combo_items()
        self._applying_channel_assignments = False

        if self._update_validation_warnings():
            return

        # Only once the channel assignment is valid (and being saved):
        # the limit jack combos only offer assigned axes, so refresh them
        # - a jack whose axis just lost its channel switches to "Not
        # used". Not done while a duplicate is showing, so a transient
        # duplicate mid-rearrangement can't wipe a jack's axis.
        if self._rebuild_limit_jack_combos():
            _save_limit_jacks(self._limit_jacks)
        self._update_limit_jack_warnings()

        _save_channel_assignments(self._channel_assignments)
    handler.__name__ = "Channel_" + channel_id + "_Axis_Changed"
    return handler

for _channel_id in CHANNEL_IDS:
    setattr(HandlerClass, "Channel_" + _channel_id + "_Axis_Changed", _channel_axis_changed(_channel_id))
del _channel_id

def _limit_jack_axis_changed(jack):
    '''
    Generic "changed" handler for one Limit_Jack_N_Axis combo. Records
    the choice and persists all three jacks unless the choices now
    contain a duplicate axis (flagged by _update_limit_jack_warnings,
    saved automatically once cleared - same pattern as
    _channel_axis_changed). Takes effect at the next LinuxCNC launch.
    '''
    def handler(self, widget):
        if self._applying_limit_jacks:
            return

        value = widget.get_active_id()
        if value is None or (value and _parse_limit_value(value) is None):
            return
        self._limit_jack_notices.pop(jack, None)
        self._limit_jacks[jack] = value

        if self._update_limit_jack_warnings():
            return

        _save_limit_jacks(self._limit_jacks)
    handler.__name__ = "Limit_Jack_" + jack + "_Axis_Changed"
    return handler

for _jack in LIMIT_JACKS:
    setattr(HandlerClass, "Limit_Jack_" + _jack + "_Axis_Changed", _limit_jack_axis_changed(_jack))
del _jack

def _pid_set(hal_pin):
    '''
    Generic value-changed handler for a single P/I/D/FF0/FF1/FF2 spin
    button: pushes the new value straight to the live pid.* HAL gain
    pin. Unlike _axis_set_scale_letter, there's no need to disable the
    axis first - a PID gain is safe to retune on the fly, it doesn't
    invalidate an in-progress move the way a scale change can. Used
    only for Sp0/Sp1's fixed pid components (pid.p0/pid.s0/pid.p1/
    pid.s1) - the six reassignable channels are instead bound via
    _pid_set_letter below.
    '''
    def handler(self, widget):
        value = widget.get_value()
        try:
            subprocess.run(
                ["halcmd", "setp", hal_pin, str(value)],
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(value))
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
    return handler

def _pid_set_letter(letter, param):
    '''
    Value-changed handler for one of the 8 letter-labeled PID spin
    buttons (<letter>_Set_<param>, letter in AXIS_SELECTION_LETTERS).
    The live pid.* component here is named after the LETTER ITSELF and
    always loaded (see Rosetta.hal), so no channel indirection is needed to
    build the pin name, only a check that this letter is actually
    assigned to a channel right now (_ROLE_CHANNEL_OF), since the
    component isn't wired into any live control loop otherwise - same
    gating _axis_set_scale_letter/_axis_set_backlash_letter use.
    '''
    hal_pin = "pid." + letter.lower() + "." + PID_PARAM_PIN[param]
    def handler(self, widget):
        if letter not in _ROLE_CHANNEL_OF:
            print(letter + " is not currently assigned to a channel - value kept, no live HAL write")
            return
        value = widget.get_value()
        try:
            subprocess.run(
                ["halcmd", "setp", hal_pin, str(value)],
                check=True,
                capture_output=True,
                text=True
            )
            print("Set " + hal_pin + " = " + str(value))
        except subprocess.CalledProcessError as e:
            print("Error setting " + hal_pin + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
    handler.__name__ = letter + "_Set_" + param
    return handler

for _letter in AXIS_SELECTION_LETTERS:
    for _param in PID_PARAMS:
        setattr(HandlerClass, _letter + "_Set_" + _param, _pid_set_letter(_letter, _param))
del _letter, _param

for _spindle_id, _loops in PID_SPINDLE_LOOPS.items():
    for _suffix, _component in _loops.items():
        for _param in PID_PARAMS:
            _widget_id = _spindle_id + "_Set_" + _param + "_" + _suffix
            _handler = _pid_set(_component + "." + PID_PARAM_PIN[_param])
            _handler.__name__ = _widget_id
            setattr(HandlerClass, _widget_id, _handler)
del _spindle_id, _loops, _suffix, _component, _param, _widget_id, _handler

def _velocity_setting_changed(tag):
    '''
    Generic value-changed handler for one of VELOCITY_SETTINGS' spin
    buttons: persists to RosettaSet_v1.ini, same as Max_Jog_Speed_Changed -
    these are read once by LinuxCNC at startup, and this program only
    runs while LinuxCNC isn't running, so the next launch picks them up.
    Refused (and put back) if it would break min <= default <= max.
    '''
    def handler(self, widget):
        if self._applying_velocity_settings:
            return
        group = "angular" if "angular" in tag else "linear"
        if not self._jog_speeds_ok(widget, group):
            return
        value = widget.get_value()
        _save_velocity_setting(tag, value)
    return handler

for _widget_id, (_tag, _default) in VELOCITY_SETTINGS.items():
    _handler = _velocity_setting_changed(_tag)
    _handler.__name__ = _widget_id + "_Changed"
    setattr(HandlerClass, _widget_id + "_Changed", _handler)
del _widget_id, _tag, _default, _handler


def main():
    if _linuxcnc_is_running():
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="LinuxCNC is currently running",
        )
        dialog.format_secondary_text(
            "Rosetta Settings must be run before starting LinuxCNC, not "
            "while it's running. Please exit LinuxCNC first, then run "
            "Rosetta Settings again."
        )
        dialog.run()
        dialog.destroy()
        return

    builder = Gtk.Builder()
    builder.add_from_file(UI_FILE)
    handler = HandlerClass(builder)
    builder.connect_signals(handler)
    window = builder.get_object("window1")
    window.connect("delete-event", handler.confirm_close)
    window.connect("destroy", Gtk.main_quit)
    window.set_title("Rosetta Settings")
    _add_file_menu(builder, handler, window)
    # window1/scrolledwindow1 no longer propagate their content's
    # natural size upward (see scrolledwindow1's propagate-natural-
    # width/height in Rosetta_Settings_v1.ui - needed so content actually
    # fills a maximized window instead of clamping to a cramped natural
    # size, the old embedded-tab-era behavior). The tradeoff: nothing
    # now gives this window a sensible size on its own at startup - it
    # opens tiny (confirmed live 4 September 2026) unless explicitly
    # told to maximize, so do that here rather than relying on content
    # size to imply a window size.
    window.maximize()
    window.show_all()
    handler.apply_advanced_visibility()
    Gtk.main()

def _add_file_menu(builder, handler, window):
    '''
    Puts a File menu across the top of the window (asked for by Chuck,
    07 October 2026) with the same four actions as the four buttons on
    the Axis Selection page, which stay as they are, plus the
    usual keyboard shortcuts. Each item runs that button's own handler with
    the button as its widget, so dialogs open over the main window
    rather than over the menu's popup.
    '''
    accel_group = Gtk.AccelGroup()
    window.add_accel_group(accel_group)
    file_menu = Gtk.Menu()
    file_menu.set_accel_group(accel_group)
    for label, button_id, method, accel in (
        ("_Save All Settings", "Settings_Save", handler.Settings_Save, "<Control>s"),
        ("Save All Settings _As...", "Settings_Save_As", handler.Settings_Save_As, "<Shift><Control>s"),
        ("Save Subset of Settings As...", "Export_Settings", handler.Export_Settings, None),
        ("_Load Settings from File...", "Settings_Load", handler.Settings_Load, "<Control>o"),
        (None, None, None, None),
        ("Back _Up to USB...", None, lambda widget: _open_backup(window), None),
        ("_Restore from USB...", None, lambda widget: _open_restore(handler, window), None),
        (None, None, None, None),
        ("_Quit", None, lambda widget: window.close(), "<Control>q"),
    ):
        if label is None:
            file_menu.append(Gtk.SeparatorMenuItem())
            continue
        item = Gtk.MenuItem.new_with_mnemonic(label)
        button = builder.get_object(button_id) if button_id else None
        item.connect("activate", lambda _item, m=method, b=button: _run_menu_action(window, m, b))
        if accel:
            key, mods = Gtk.accelerator_parse(accel)
            item.add_accelerator("activate", accel_group, key, mods, Gtk.AccelFlags.VISIBLE)
        file_menu.append(item)
    file_item = Gtk.MenuItem.new_with_mnemonic("_File")
    file_item.set_submenu(file_menu)
    menu_bar = Gtk.MenuBar()
    menu_bar.append(file_item)
    outer_box = builder.get_object("Settings_Outer_Box")
    outer_box.pack_start(menu_bar, False, False, 0)
    outer_box.reorder_child(menu_bar, 0)

def _open_backup(window):
    '''
    File > Back Up to USB (added 09 November 2026): the same window as
    the Back Up launcher (Rosetta_Backup.py), over this one.
    '''
    import Rosetta_Backup
    Rosetta_Backup.BackupWindow(parent=window).show_all()

def _open_restore(handler, window):
    '''
    File > Restore from USB (added 09 November 2026; see
    Rosetta_Backup.py's header). The restore replaces RosettaSet_v1.ini
    underneath this program, whose widgets still hold the old values -
    and some of them save as soon as they change - so once anything has
    been restored this program closes without saving; reopening it
    reads the restored file. Unsaved tuning changes are asked about
    first, since closing would otherwise lose them silently.
    '''
    if handler._tuning_values() != handler._saved_tuning:
        dialog = Gtk.MessageDialog(
            transient_for=window, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Unsaved changes",
        )
        dialog.format_secondary_text(
            "Some Scale, speed, acceleration or PID values have changed since "
            "they were last saved. A restore replaces the settings and then "
            "closes Rosetta Settings, so those changes would be lost.\n\n"
            "Save them first if you want them in this machine's settings "
            "(they'll be set aside with the other replaced files).")
        dialog.add_button("Continue Without Saving", Gtk.ResponseType.NO)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save and Continue", Gtk.ResponseType.YES)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            handler._write_rebset_snapshot()
        elif response != Gtk.ResponseType.NO:
            return
    import Rosetta_Backup

    def restored():
        handler._closing_after_restore = True
        window.close()
    Rosetta_Backup.RestoreWindow(window, restored).show_all()

def _run_menu_action(window, method, button):
    # A shortcut key leaves focus in a spin button that's still being
    # typed in, whose new value isn't committed until focus leaves it
    # (clicking a button does that); commit it first so it's saved.
    focus = window.get_focus()
    if isinstance(focus, Gtk.SpinButton):
        focus.update()
    method(button)

if __name__ == "__main__":
    main()
