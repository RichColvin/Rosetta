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
#   Rosetta_main.py
#
# Purpose:  This is used to handle buttons used in panels developed
#   for Rosetta's use on LinuxCNC.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 21 July 2026
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

import hal
import hal_glib
import glib
import time
import math
import os
import linuxcnc
import webbrowser
import subprocess
import shutil
import re
import json
import bisect
import decimal
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GLib
import rosetta_settings_io

SETTINGS_PATH = os.path.expanduser("~/Documents/RosettaSet_v1.ini")

# The friendly serial number an owner can set (Rosetta_Set_Serial_Number.sh) -
# same path as Rosetta_Report_Version.py's own SERIAL_PATH (duplicated, not
# imported - that script runs standalone from Rosetta_Update_Settings.py).
# Appended to the main panel's "O/S ..." label by _load_version_label
# below; absent/empty means no S/N has been set yet, so nothing is
# appended.
SERIAL_PATH = os.path.expanduser("~/.config/Rosetta/serial")

# Web pages opened by the panel's link buttons - kept together so a move
# to another address is a change here only. Since 04 November 2026 they're
# on rosetta.colvintools.com - except the forum, which must stay at
# colvintools.com/Rosetta/Forum: under rosetta.colvintools.com its users
# can't log in.
WEBSITE_URL = "https://rosetta.colvintools.com/"
USER_MANUAL_URL = "https://rosetta.colvintools.com/UserManual/"
USER_FORUM_URL = "https://colvintools.com/Rosetta/Forum/"
GCODE_LIBRARY_URL = "https://rosetta.colvintools.com/Gcode/"

# Channel id ("00".."07") -> the role (one of the 8 axis letters or 2
# spindles) Rosetta.ini/Rosetta.hal ship with by default. Seed value for a
# channel's <channel_assignments> entry in RosettaSet_v1.ini when the
# operator has never touched the Axis Selection tab (Rosetta_Settings.py, a
# standalone program - not this file, whose own embedded Settings tab
# was retired 4 September 2026) - same "absent -> shipped default"
# convention as every other RosettaSet_v1.ini-backed setting (see
# _load_measurement_system). Mirrors Rosetta_Settings.py's own
# CHANNEL_DEFAULT_ROLE exactly (duplicated, not imported - see that
# file's own comment on why small constants/logic like this stay
# duplicated across this codebase's independent scripts).
#
# Since Rosetta_Panel_v1.ui's 18 September 2026 rebuild, every one of the
# 10 roles below has its own permanent, dedicated main-panel row (no
# more "internal id" concept - a row's identity never changes at
# runtime, only whether it's currently assigned to a channel does, via
# PANEL_INTERNAL_IDS/_load_panel_axis_controls below) - this dict is
# now used only to seed/validate the persisted assignment, the same way
# Rosetta_Settings.py already uses its own copy.
# Two-box hardware (14 October 2026): the 10 channels, their defaults
# and the old-file completion come from rosetta_settings_io - shared, so the
# panel greys exactly the roles Rosetta_Generate_Local_Ini.py left out.
CHANNEL_DEFAULT_ROLE = rosetta_settings_io.CHANNEL_DEFAULT_ROLE

# The 8 letters selectable on the Axis Selection tab (Y removed - not
# used on this machine) and the 2 spindles - the 10 possible roles a
# channel can be assigned.
AXIS_SELECTION_LETTERS = ("X", "Z", "U", "V", "W", "A", "B", "C")
SPINDLE_IDS = ("Sp0", "Sp1")
CHANNEL_ROLES = AXIS_SELECTION_LETTERS + SPINDLE_IDS

# The axis letter -> Type rule: A/B/C are angular, everything else is
# linear. Was briefly an independent, per-channel operator choice via
# the Axis Selection tab's Type combo (RosettaSet_v1.ini's "channel_types"
# field) between 3 and 4 September 2026; that feature was retired the
# same week it shipped (nothing in the current UI can ever set an
# independent type again), so this is now simply the one and only
# source of truth. Mirrors Rosetta_Setup/Rosetta_Generate_Local_Ini.py's and
# Rosetta_Display/rosetta_settings_io.py's own copies of this same rule.
def _axis_type_for_letter(letter):
    # Case-fold so this stays correct regardless of caller casing.
    return "ANGULAR" if letter.upper() in ("A", "B", "C") else "LINEAR"

# Letter -> the same foreground color Rosetta_Panel_v1.ui's original per-axis
# DRO/jog labels already use for that letter (X/U share one color, Z/W
# share another, V/B share a third - grouped by mechanical relationship,
# e.g. "U is parallel to X" per the AXIS CONVENTIONS text), extended to
# cover A/C (not present elsewhere in the panel) by following the same
# X/Z/V groupings the Axis Selection tab already applies for TYPE
# (A angular like B, but grouped with X/U's color here; C angular like B,
# grouped with Z/W's color) - used by _load_panel_axis_display to color
# the main panel's read-only "Axis Assignments" letters the same way.
AXIS_LETTER_COLOR = {
    "X": "#e5e5a5a50a0a",
    "U": "#e5e5a5a50a0a",
    "A": "#e5e5a5a50a0a",
    "V": "#a5a51d1d2d2d",
    "B": "#a5a51d1d2d2d",
    "Z": "#1a1a5f5fb4b4",
    "W": "#1a1a5f5fb4b4",
    "C": "#1a1a5f5fb4b4",
}

# Type -> default Feed value for a role's initial self.<role>_Feed
# instance attribute (set once in __init__, see the "Generated
# per-channel handlers" block near the end of this file) - the working
# value the generated Set_Feed/Idx_Move handlers actually read/write via
# getattr/setattr, independent of whatever Rosetta_Panel_v1.ui's own
# GtkAdjustment happens to show before the operator (or this) first
# touches it. Angular default is 360 deg/min (Rich, 3 September 2026);
# linear stays 1 in-or-mm/min, matching every linear channel's original
# shipped value.
#
# Since Rosetta_Panel_v1.ui's 18 September 2026 rebuild gave every role a
# permanent row with its own static, type-correct GtkAdjustment
# lower/upper/step/digits already baked in (no more per-role
# reassignment to account for), this dict now exists only for the
# default-value seeding above - it no longer overwrites Rosetta_Panel_v1.ui's
# adjustment properties at runtime.
TYPE_ADJUSTMENT_PROFILE = {
    "LINEAR": 1,
    "ANGULAR": 360,
}

def _read_persisted_channel_assignments():
    '''
    The persisted channel -> role map, completed to all 10 channels
    (rosetta_settings_io.complete_channel_assignments).
    '''
    return rosetta_settings_io.complete_channel_assignments(
        rosetta_settings_io.load_settings().get("channel_assignments"))

# The 10 roles, in the order the operator sees them top-to-bottom on
# Rosetta_Panel_v1.ui (Sp0, Sp1, then the 8 axis letters) - since the 18
# September 2026 row rebuild, every one of these has its own permanent,
# independent main-panel row (Feed/Comment/Idx/jog widgets, an ENA
# button, an Ena_Override pin) - no more "internal id" concept: a row's
# identity never changes at runtime, only whether its role is currently
# assigned to a channel does (see _load_panel_axis_controls below).
PANEL_INTERNAL_IDS = ("Sp0", "Sp1") + AXIS_SELECTION_LETTERS

# This session's channel -> role assignment, as persisted at the
# time Rosetta_Generate_Local_Ini.py generated Rosetta.local.hal/Rosetta.local.ini for
# this LinuxCNC launch (see CLAUDE.md). Read once at module import: a
# running session's assignment can't change without a restart anyway (the
# Axis Selection tab shows the same "restart required" popup Measurement
# System/Max Jog Speed already use), so re-reading it later would only
# ever see the same value or a value that doesn't match what's actually
# wired into this session's HAL - re-reading live would be worse, not
# better.
_CHANNEL_ASSIGNMENTS_AT_STARTUP = _read_persisted_channel_assignments()

# Roles (letters or spindle ids) currently assigned to some channel, per
# this session's persisted assignment - the only thing that still
# varies per role at runtime now that every row is a permanent identity
# (see PANEL_INTERNAL_IDS above). Used by _load_panel_axis_controls
# below to grey out every widget belonging to a role that isn't active,
# and by _clear_ena_override/_axis_idx_move to decide whether an ENA
# press or jog move is meaningful at all.
# For User Manual screenshots only (Rich, 14 October 2026): started as
#     ROSETTA_SHOW_EXPANSION=1 ./Rosetta_Launch.sh
# the panel shows the expansion box as connected - its Axis Assignments
# tiles and its axes' rows - without changing RosettaSet_v1.ini or the HAL
# files, so LinuxCNC still starts with only the base box's card. Those
# rows aren't wired to anything; don't use them. A normal launch is back
# to normal.
SHOW_EXPANSION_FOR_SCREENSHOTS = os.environ.get("ROSETTA_SHOW_EXPANSION") == "1"

def _panel_settings():
    '''RosettaSet_v1.ini's settings, with the expansion box marked connected
    when SHOW_EXPANSION_FOR_SCREENSHOTS is set.'''
    settings = rosetta_settings_io.load_settings()
    if SHOW_EXPANSION_FOR_SCREENSHOTS:
        settings["expansion_box"] = True
    return settings

_ACTIVE_ROLES_AT_STARTUP = {
    role for channel_id, role in _CHANNEL_ASSIGNMENTS_AT_STARTUP.items()
    if channel_id in rosetta_settings_io.active_channels(_panel_settings())}

# <letter>_-prefixed widget-id suffixes every axis-letter row
# (X/Z/U/V/W/A/B/C) has, since Rosetta_Panel_v1.ui's 18 September 2026
# rebuild gave every letter the same complete, uniform set - used by
# _load_panel_axis_controls to grey out an inactive role's whole row.
# Idx_DegDiv_Box's two nested HAL_RadioButtons (<letter>_Idx_Deg/_Div)
# don't need their own entry - graying their container greys them too.
AXIS_ROW_FIELDS = (
    "_Letter", "_ENA", "_Feed", "_Feed_UOM", "_Comment",
    "_Idx_Dist", "_Idx_Count", "_IdxDist_UOM", "_Idx_DegDiv_Box",
    # Sync Move tab.
    "_Sync_Dist_Box", "_Sync_Dist_UOM", "_Sync_Rev", "_Sync_Fwd",
)

# gladevcp's HAL_LightButton.expose() (hal_lightbutton.py) only dims an
# insensitive button's existing light color to 30% alpha - it never
# desaturates it - so an unassigned role's ENA light would otherwise
# still render as a faded red rather than a neutral gray. Overriding
# the widget's own light-off-color to gray (below, in
# _load_panel_axis_controls) fixes this directly; light-on-color is
# left alone since an unassigned role's -light HAL pin is never wired
# to anything, so light_is_on can never go True.
_UNASSIGNED_ENA_LIGHT_COLOR = Gdk.Color.parse("gray")[1]

# Sp0/Sp1's own widget ids (not a per-letter suffix pattern - each
# spindle's row has its own, genuinely different, set of controls; see
# CLAUDE.md's "Specific Plans for Rosetta_Panel_v1.ui" history). Used the
# same way as AXIS_ROW_FIELDS above.
SPINDLE_ROW_FIELDS = {
    "Sp0": (
        "Sp0_ENA", "Sp0_Set_Feed", "Sp0_Move_Fwd", "Sp0_Move_Stop", "Sp0_Move_Rev",
        "Sp0_Idx_Dist", "Sp0_Idx_Count", "Sp0_Idx_Fwd", "Sp0_Idx_Rev",
        "Sp0_Set_Idx_bW_Deg", "Sp0_Set_Idx_bW_Div", "Sp0_Set_Idx_OnOff",
    ),
    "Sp1": (
        "Sp1_ENA", "Sp1_Set_Move_Pct", "Sp1_Set_Idx_OnOff",
    ),
}

# Sync Move tab (Rosetta_Panel_v1.ui's second Indexing/Sync Move tab):
# Direction button suffix -> the G-code sign it sends. <letter>_Sync_Rev
# sits in column 12 (headed "Rev"/"⊖") and <letter>_Sync_Fwd in column 13
# ("Fwd"/"⊕"), in the same cells as - and showing the same icons as -
# that letter's own Indexing tab buttons, which send "-" and "+"
# respectively (see the generated <letter>_Idx_Plus/_Idx_Minus loop near
# the end of this file) - so a given icon means the same physical
# direction on both tabs.
SYNC_DIR_SIGN = {"Rev": "-", "Fwd": "+"}

# Sync Move's A/B/C Distance (13 November 2026, Rich - users often ask
# for a large rotation): deg or rev, chosen per row with the
# <letter>_Sync_Unit_Deg/_Rev radios. Unit -> (decimals shown, spin
# step, largest value, degrees per unit). Rev has 3 decimals so eighths
# of a turn are exact. X/Z/U/V/W keep their .ui settings.
SYNC_ANGULAR_UNITS = {
    "deg": (2, 0.01, 99999999.0, 1.0),
    "rev": (3, 0.001, 999999.999, 360.0),
}

# Continue after a Sync Move was stopped part way (see _sync_continue):
# an axis further than this (machine units or degrees) from the move's
# straight line counts as moved while stopped, and Continue asks first.
SYNC_LINE_TOLERANCE = 0.001

# Pause asks LinuxCNC for a feed hold. If the move hasn't paused this
# long afterwards, it's stopped instead (and Continue sends the rest of
# it as a new move) - see _sync_check_paused.
SYNC_PAUSE_CHECK_MS = 500

# The external Pause button: a limit jack set to "Pause button" in
# Rosetta Settings (RosettaSet_v1.ini's limit_switches value "Pause") is
# wired by Rosetta_Generate_Local_Ini.py to this HAL signal, true while
# the button reads pressed (or, for an NC button, while its wire is
# broken or unplugged).
PAUSE_BUTTON_SIGNAL = "pause-button"
PAUSE_JACK_VALUE = "Pause"

# Axis letter -> its index in linuxcnc.stat().position (always the
# fixed X Y Z A B C U V W order, regardless of [TRAJ]COORDINATES).
STAT_POSITION_INDEX = {
    "X": 0, "Y": 1, "Z": 2, "A": 3, "B": 4, "C": 5, "U": 6, "V": 7, "W": 8,
}

# Rosetta_Panel_v1.ui's Indexing/Sync Move tabs: every MainGrid cell the two
# tabs swap between is a GtkStack whose id starts with this, holding an
# "idx" and a "sync" page - see Panel_Mode_Switch.
PANEL_MODE_STACK_PREFIX = "Mode_Stack_"

# Sync Move tab widgets with no Indexing counterpart - shown/hidden
# outright by Panel_Mode_Switch instead of living in a Mode_Stack.
SYNC_TAB_ONLY_WIDGETS = ("Sync_Spindle_Note", "Sync_Button_Box")

# Panel_Mode_Tabs page number -> the Mode_Stack page it shows. Threading
# (page 2) has none: its whole form (Thread_Form) overlays columns 10-13,
# and the stacks are unmapped instead - see Panel_Mode_Switch.
PANEL_MODE_STACK_PAGE = {0: "idx", 1: "sync"}
PANEL_MODE_THREAD_PAGE = 2

# Column 10-13 header labels outside any Mode_Stack (Indexing/Sync Move's
# Rev/Fwd and their ⊖/⊕), unmapped on the Threading tab since
# Thread_Form covers them.
MODE_HEADER_WIDGETS = ("Mode_Hdr_Rev", "Mode_Hdr_Fwd", "Title_Minus_Sign1", "Title_Plus_Sign1")

# Every button that starts a polled Sync Move/Threading motion - all
# disabled while any one of them is running (see _start_polled_mdi).
MOTION_BUTTONS = ("Sync_Run", "Sync_Return", "Thread_Run", "Thread_Return")
# Sync_Pause (Pause / Continue) isn't one of them: it's set by
# _sync_update_pause_button instead.

# The startup splash (the Turk's head over "ROSETTA", written each launch
# by Rosetta_Generate_Local_Ini.py) and the empty file swapped in for it
# before a Sync Move or Cut Thread, whose tool path AXIS would otherwise
# draw over the lettering - see _clear_splash.
SPLASH_FILE_NAME = "Rosetta_Splash.local.ngc"
EMPTY_PREVIEW_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rosetta_Splash.ngc")

# Axis letters the Threading tab drives: X feeds the cutter in, Z moves
# along the thread, C turns the work.
THREAD_AXES = ("X", "Z", "C")

# Threading tab defaults, per Measurement System - the Threading.xlsx
# example Rich designed the tab from (4 TPI, 0.25" long, 60 degrees,
# 0.1" first cut and clearance, 1 spring pass), converted to mm for
# Metric, but single-start. Final depth isn't here: it starts at the
# calculated max.
THREAD_DEFAULTS = {
    "Imperial": {"Thread_Starts": 1, "Thread_TPI": 4.0, "Thread_Length": 0.25,
                 "Thread_Angle": 60.0, "Thread_Clearance": 0.1,
                 "Thread_First_Depth": 0.1, "Thread_Spring": 1},
    "Metric":   {"Thread_Starts": 1, "Thread_TPI": 6.35, "Thread_Length": 6.35,
                 "Thread_Angle": 60.0, "Thread_Clearance": 2.54,
                 "Thread_First_Depth": 2.54, "Thread_Spring": 1},
}

# Main-panel values remembered between LinuxCNC sessions, in
# RosettaSet_v1.ini's "panel_state" (see _panel_state / _restore_panel_state).
# Threading fields in inches/mm (or TPI vs mm pitch) aren't restored if
# the Measurement System has changed since they were saved - see
# THREAD_UNIT_FIELDS.
THREAD_SAVED_SPINS = ("Thread_Starts", "Thread_TPI", "Thread_Length", "Thread_Angle",
                      "Thread_Clearance", "Thread_First_Depth", "Thread_Spring")
THREAD_SAVED_COMBOS = ("Thread_Hand", "Thread_Side", "Thread_Dir")
THREAD_UNIT_FIELDS = ("Thread_TPI", "Thread_Length", "Thread_Clearance",
                      "Thread_First_Depth", "Thread_Final_Depth")

# Refuse a threading run with more passes per start than this - almost
# certainly a mistyped First cut depth.
THREAD_MAX_PASSES_PER_START = 200

# rosetta_thread.ngc's progress code kinds (the thousands digit of
# gladevcp.thread-status - see that file's header).
THREAD_KIND_PASS = 1
THREAD_KIND_FINAL = 2
THREAD_KIND_SPRING = 3
THREAD_KIND_INDEX = 8
THREAD_KIND_DONE = 9

# How long a Cut Thread's "Done"/"Stopped" message stays up before the
# Threading tab's instructions come back.
THREAD_RESULT_SECONDS = 20

# Attention sounds (see _load_sounds). RosettaSet_v1.ini's "done_sound"
# picks where they play: "off", "tower" (the signal tower's buzzer, if
# one is connected), "speaker" (the Pi's own audio - HDMI or USB) or
# "both". Each pattern is that many short beeps, BEEP_SECONDS on then
# BEEP_SECONDS off - deliberately unlike the tower's steady 3 s fault
# siren. On the speaker, Rosetta_Display/Sounds/Rosetta_Done.wav is a "ta-da"
# (two organ-like chords) and Rosetta_Pause.wav two rising notes in the
# same voice (Rich's choices, 20 October 2026), each after 0.5 s of
# silence: an HDMI TV cuts off the start of a sound while it locks on
# (Rich's lost the first beep).
# The fault siren has its own setting, "fault_sound" (same choices):
# the tower sounds it straight from HAL, and Rosetta_Generate_Local_Ini.py
# nets the same 3 s pulse to the fault-siren pin for the speaker, which
# plays Rosetta_Fault.wav (a 3 s two-tone siren).
DONE_BEEPS = 3      # a program, Sync Move or Cut Thread finished
PAUSE_BEEPS = 2     # a program stopped at M0/M1/M60, waiting for the operator
FAULT_SIREN = "fault"
BEEP_SECONDS = 0.2
SOUND_FILES = {
    DONE_BEEPS: os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sounds", "Rosetta_Done.wav"),
    PAUSE_BEEPS: os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sounds", "Rosetta_Pause.wav"),
    FAULT_SIREN: os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sounds", "Rosetta_Fault.wav"),
}
# Tried in order for the speaker; the first one installed is used.
SOUND_PLAYERS = (["paplay"], ["pw-play"], ["aplay", "-q"])
# How often a running program is checked for finishing or pausing.
PROGRAM_POLL_MS = 250

# Program progress (see _load_program_progress). The estimate helper,
# run in the background as a program starts.
PROGRAM_ESTIMATE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "Rosetta_Program_Estimate.py")
# A run whose first move isn't among the program's first this many
# moves was started part way (Run From Line) - no progress shown.
PROGRESS_START_MOVES = 500

# Card contact (see _poll_card_contact). The cards' names on screen.
CARD_NAMES = {0: "Base box", 1: "Expansion box"}
CARD_CONTACT_POLL_MS = 500
# While in E-stop, a card hm2_eth has given up on is reconnected at
# most this often: each try on a card that's still unplugged fails
# again and prints "error finishing read" again.
CARD_RECONNECT_SECONDS = 5

# A Return to Start move smaller than this (machine units) on every
# axis counts as "already there".
SYNC_POSITION_TOLERANCE = 0.0001

# Max time (seconds) to wait for both Sp0 and Sp1 to report oriented in
# Sp0_Move_Idx_Fwd/Rev's simultaneous-index path (see
# _index_both_spindles_simultaneously) - matches the "Q20" timeout
# already used for the single-spindle M19 path elsewhere in this file.
SIMULTANEOUS_INDEX_TIMEOUT = 20.0

# Spindle index direction (08 November 2026): orient.N.mode for each
# index. Shortest path (mode 0) let an index of 180 degrees or more turn
# against the button pressed, losing the drive's backlash on every
# change of direction, and at exactly 180 (Div 2) the direction could
# flip from press to press. Found on Rich's Pi: mode 1 turns the way of
# the on-screen Fwd button (spindle position increasing, sign +1 - the
# Sp0_Move_Idx_Rev handler, since the ids don't match their columns),
# mode 2 the way of Rev.
SPINDLE_INDEX_MODE = {+1: 1, -1: 2}
# An index is worked out from the previous index's target, not from
# where the spindle stopped - it stops just inside ORIENT_TOLERANCE,
# always short on the side it came from (about 0.08 degrees), so working
# from the stopped position added that up (Div 24 all the way round
# ended nearly 2 degrees short). The stopped position is used instead
# when it's further than this from the last target (first index, or the
# spindle has been run since).
SPINDLE_INDEX_TRACK_DEGREES = 1.0

# Default directory Export/Import's file choosers start in.
ROSETTASET_DEFAULT_DIR = os.path.expanduser("~/Documents")

# Axes (not spindles) that have a free-text comment field on the main
# panel, persisted to REB_Settings_v1.ini as each <axis>'s <usercomment>.
COMMENT_AXES = ("X", "Z", "U", "V", "W", "A", "B", "C")

# Leading entry (index 0) in every device-name GtkComboBoxText - the main
# panel's per-axis Comment/Device combos and the Export Settings dialog's
# per-axis Device combos alike - standing in for "nothing chosen yet"
# instead of a blank-looking row. Never treated as a real device name -
# see _combo_selected_device.
DEVICE_COMBO_PLACEHOLDER = "(nothing selected yet)"

# Sp0/Sp1 have no main-panel comment field (see COMMENT_AXES) to default
# the Export Settings dialog's Device combo from, unlike X/Z/U/V/W/B -
# these are the ones Rich actually has, so use them as each spindle's
# default there instead of falling back to DEVICE_COMBO_PLACEHOLDER.
# Only applied if the name is still present in the maintained Device
# Names list at export time - see _run_export_selection_dialog.
SPINDLE_DEFAULT_DEVICE_NAME = {
    "Sp0": "Spindle (Sp0)",
    "Sp1": "Rosette Phaser/Multiplier (Sp1)",
}

# Export_Settings/Import_Settings (see docs/settings_file.md): a
# hand-picked subset of just what's literally on the Settings tab itself
# (each axis's Scale, plus Measurement System), for quick, ad hoc sharing
# of a few values (e.g. "just my B-axis calibration") rather than a full
# profile. Plain XML (matching REB_Settings_v1.ini's own shape). The
# filename itself defaults to "<comment>.RosettaSet_v1.ini", where <comment>
# is the single device name the operator picked in the export selection
# dialog - or, when the selected axes' Device combos name more than one
# distinct device, today's date instead (see Export_Settings) - not
# related to SETTINGS_PATH, which is always the fixed "RosettaSet_v1.ini"
# name with no comment prefix.
EXPORT_EXTENSION = ".RosettaSet_v1.ini"

# Establish connection to command and status channels
c = linuxcnc.command()
s = linuxcnc.stat()

# Temporary diagnostic log for the Sp0/Sp1 indexing checkbox investigation.
# The panel is normally launched with Terminal=false (see the desktop
# launcher), so print() output has nowhere visible to go - this mirrors the
# relevant prints to a file so they can be watched during live testing.
IDX_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "idx_debug.log")

def idx_log(msg):
    print(msg)
    try:
        with open(IDX_LOG_PATH, "a") as f:
            f.write(time.strftime("%H:%M:%S") + " " + msg + "\n")
            f.flush()
    except Exception:
        pass

def _clear_ena_override(axis_id):
    # The *_Set_Ena handlers fire from whichever component owns that
    # axis's ENA button (the main panel, "gladevcp") - but the real,
    # netted *_Ena_Override pin (see Rosetta_PostGUI_v1.hal) is written from
    # the standalone Rosetta_Settings program, a different process (before
    # 4 September 2026 this was the embedded Settings tab's own
    # component, "REBCnfg" - now retired). Cross the process boundary
    # via halcmd instead, the same way Rosetta_Settings's own Scale handlers
    # already do in the other direction for *_ENA-light.
    #
    # Once a pin is netted to a signal, halcmd can't "setp" the pin
    # directly ("pin is connected to a signal") - the signal itself has
    # to be set instead, via "halcmd sets". The signal name follows the
    # <letter>-ena-settings-allow convention in Rosetta_PostGUI_v1.hal. Since
    # Rosetta_Generate_Local_Ini.py names every net by ROLE, not by physical
    # channel (a role's own letter is a stable identity - see
    # CHANNEL_DEFAULT_ROLE's comment above), that net is always simply
    # axis_id's own letter, lowercased - no per-session lookup needed.
    current_letter = axis_id.lower()
    hal_signal = current_letter + "-ena-settings-allow"
    idx_log("_clear_ena_override(" + axis_id + ") -> " + hal_signal)

    # Was the override actually blocking anything? Only true right after
    # a scale change (Set_Scale) forced it False. If it's already True,
    # this ENA press is routine day-to-day toggling and must be left
    # alone below - forcing the panel bit in that case would turn
    # "click to disable" into a no-op.
    was_blocked = False
    try:
        result = subprocess.run(["halcmd", "gets", hal_signal], check=True, capture_output=True, text=True)
        was_blocked = result.stdout.strip().upper() not in ("TRUE", "1")
    except subprocess.CalledProcessError as e:
        idx_log("Error reading " + hal_signal + ": " + str(e.stderr))
    except FileNotFoundError:
        idx_log("halcmd not found - is the LinuxCNC environment sourced?")

    try:
        subprocess.run(["halcmd", "sets", hal_signal, "TRUE"], check=True, capture_output=True, text=True)
        idx_log("Set " + hal_signal + " = TRUE")
    except subprocess.CalledProcessError as e:
        idx_log("Error setting " + hal_signal + ": " + str(e.stderr))
    except FileNotFoundError:
        idx_log("halcmd not found - is the LinuxCNC environment sourced?")

    if was_blocked:
        # The same ENA press that got us here also clocks the flipflop's
        # own toggle bit (Rosetta_PostGUI_v1.hal) via the ordinary clk input -
        # since that bit never moved while the override was blocking
        # things, this click would otherwise flip a previously-on panel
        # state OFF, undoing the very re-enable just requested (this is
        # exactly the "press ENA and nothing happens, need a confusing
        # second press" behavior from live testing). Force the panel bit
        # on deterministically via the flipflop's own set/reset override
        # pins instead of leaving it to toggle-parity guesswork.
        flip_set_pin = current_letter + "-ena-flip.set"
        try:
            subprocess.run(["halcmd", "setp", flip_set_pin, "TRUE"], check=True, capture_output=True, text=True)
            subprocess.run(["halcmd", "setp", flip_set_pin, "FALSE"], check=True, capture_output=True, text=True)
            idx_log("Forced " + current_letter + "-ena-panel ON (override had been blocking)")
        except subprocess.CalledProcessError as e:
            idx_log("Error pulsing " + flip_set_pin + ": " + str(e.stderr))
        except FileNotFoundError:
            idx_log("halcmd not found - is the LinuxCNC environment sourced?")

def _show_no_spindle_enabled_popup(widget):
    dialog = Gtk.MessageDialog(
        transient_for=widget.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK,
        text="No spindle is enabled",
    )
    dialog.run()
    dialog.destroy()

def _roles_not_enabled(roles):
    '''
    Those of roles (axis letters, "Sp0", "Sp1") whose ENA is off - the
    "<role>-ena-and.out" pin in Rosetta_PostGUI_v1.hal (the panel's ENA
    toggle AND Rosetta Settings' override). A role with no such pin
    isn't counted.
    '''
    off = []
    for role in roles:
        try:
            if not hal.get_value(role.lower() + "-ena-and.out"):
                off.append(role)
        except Exception:
            pass
    return off


# What to do when a move needs an axis or spindle whose ENA is off -
# RosettaSet_v1.ini's "not_enabled_action" (Rosetta Settings > Other >
# Axis Not Enabled, added 09 November 2026): "ask" (the default) or
# "enable". Read once at startup, like the other settings.
try:
    NOT_ENABLED_ACTION = rosetta_settings_io.load_settings().get("not_enabled_action", "ask")
except Exception:
    NOT_ENABLED_ACTION = "ask"
if NOT_ENABLED_ACTION not in ("ask", "enable"):
    NOT_ENABLED_ACTION = "ask"
ENABLE_WAIT_SECONDS = 1.0


def _enable_roles(roles):
    '''
    Turns on each of roles' ENA the way clicking its ENA button does:
    pulses its "<role>-ena-flip.set" (Rosetta_PostGUI_v1.hal's ENA
    flipflop), so the panel's ENA light and the next click carry on
    from there. Doesn't touch Rosetta Settings' override
    ("<role>-ena-settings-allow") - a role it still blocks stays off.
    Returns the roles still not enabled after ENABLE_WAIT_SECONDS.
    '''
    for role in roles:
        pin = role.lower() + "-ena-flip.set"
        try:
            subprocess.run(["halcmd", "setp", pin, "TRUE"], check=True, capture_output=True, text=True)
            subprocess.run(["halcmd", "setp", pin, "FALSE"], check=True, capture_output=True, text=True)
            idx_log("Enabled " + role + " (" + pin + " pulsed)")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            idx_log("Could not pulse " + pin + ": " + str(e))
    deadline = time.monotonic() + ENABLE_WAIT_SECONDS
    while True:
        still_off = _roles_not_enabled(roles)
        if not still_off or time.monotonic() > deadline:
            break
        time.sleep(0.02)
    # Show the ENA lights now (found by Rich 09 November 2026: they only
    # turned green after the move). The move that follows holds up the
    # panel (wait_complete), and gladevcp only reads its -light pins
    # every 100 ms from the main loop - so read them now and draw.
    try:
        hal_glib.GPin.update_all()
    except Exception:
        pass
    while Gtk.events_pending():
        Gtk.main_iteration()
    return still_off


def _names(roles):
    return roles[0] if len(roles) == 1 else ", ".join(roles[:-1]) + " and " + roles[-1]


def _confirm_roles_enabled(widget, roles):
    '''
    Added 08 November 2026 - the panel's side of the check AXIS makes
    before a run (Rosetta_Axis_Commands.py): before an index, Sync Move
    or Threading button moves anything, looks for roles whose ENA is
    off. An axis with ENA off ends in a following error as soon as it
    has to move; a spindle with ENA off doesn't turn, so its index
    never finishes. Since 09 November 2026 (Rich): with
    NOT_ENABLED_ACTION "enable" they are switched on with no box;
    otherwise a box offers "Enable <names> and Move" (the default) or
    Cancel - "Move Anyway" was removed at Rich's request. True means
    go ahead.
    '''
    off = _roles_not_enabled(roles)
    if not off:
        return True
    names = _names(off)
    idx_log("Not enabled: " + names)
    if NOT_ENABLED_ACTION == "enable":
        off = _enable_roles(off)
        if not off:
            return True
        names = _names(off)
    else:
        one = len(off) == 1
        dialog = Gtk.MessageDialog(
            transient_for=widget.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=names + " not enabled",
        )
        dialog.format_secondary_text(
            "This moves " + names + ", which " + ("is" if one else "are") + " not enabled.\n\n"
            "Enable and Move turns " + ("its ENA" if one else "their ENAs") + " on - the same as "
            "clicking the ENA " + ("button" if one else "buttons") + " - then makes the move.  "
            "Cancel leaves " + ("it" if one else "them") + " off and moves nothing.")
        dialog.add_button("Enable " + names + " and Move", Gtk.ResponseType.ACCEPT)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        answer = dialog.run()
        dialog.destroy()
        if answer != Gtk.ResponseType.ACCEPT:
            return False
        off = _enable_roles(off)
        if not off:
            return True
        names = _names(off)
    # Still off: Rosetta Settings' override is blocking it, or HAL
    # couldn't be reached.
    _show_settings_error(widget, names + " could not be enabled.  Click the ENA "
                         + ("button" if len(off) == 1 else "buttons") + " for " + names
                         + ", then try again.")
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

def _round_half_up(value, digits):
    '''
    value rounded to `digits` decimals with halves going up, the way
    people round (40.125 -> 40.13) - Python's round() sends an exact half
    to the even digit (40.12).
    '''
    return float(decimal.Decimal(repr(value)).quantize(
        decimal.Decimal(1).scaleb(-digits), rounding=decimal.ROUND_HALF_UP))


def _gcode_number(value, significant=8):
    '''
    value as a G-code number - plain decimals (G-code has no "1e-09"),
    with enough places to keep `significant` significant digits however
    small it is. Added 13 November 2026 for Sync Move's inverse-time F
    (1 / minutes): with a fixed 8 decimals, a very long, slow move's F
    would round towards 0 (99,999,999 deg at 0.1 deg/min is F
    0.000000001).
    '''
    if value == 0:
        return "0"
    places = max(4, significant - 1 - int(math.floor(math.log10(abs(value)))))
    return "%.*f" % (places, value)

def _planner_length(deltas):
    '''
    The length LinuxCNC's motion planner counts for a move of deltas
    ({letter: distance}): its X/Y/Z length, else U/V/W, else A/B/C -
    what motion.current-vel (and so Rosetta.hal's program-path) measures.
    '''
    for group in ("XYZ", "UVW", "ABC"):
        length = math.sqrt(sum(d * d for axis, d in deltas.items() if axis in group))
        if length > 0:
            return length
    return 0.0


def _show_restart_required_popup(widget, detail=None):
    dialog = Gtk.MessageDialog(
        transient_for=widget.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text="Restart required",
    )
    dialog.format_secondary_text(
        detail if detail is not None else
        "The Measurement System change will not take effect until you exit "
        "and restart LinuxCNC."
    )
    dialog.run()
    dialog.destroy()



def _read_persisted_device_names():
    '''
    Reads the persisted device-name list straight from SETTINGS_PATH
    (RosettaSet_v1.ini's "device_names" list) - the on-disk counterpart to
    HandlerClass._read_device_names, which reads the live Settings tab's
    Device_Names GtkTextView instead. Used wherever a component needs
    this list but doesn't own that widget - e.g. the main panel
    populating each axis's Comment combo box at startup, since the main
    panel and Settings tab are separate gladevcp processes with no live
    IPC between them (see CLAUDE.md). Returns [] if the file can't be
    read or has no device_names list.
    '''
    return list(rosetta_settings_io.load_settings().get("device_names", []))

def _read_persisted_axis_comment(axis_id, settings):
    '''
    Extracts one axis's persisted usercomment value out of an
    already-loaded settings dict. Shared by _load_axis_comments (main
    panel, restoring its own Device combos at startup) and
    _run_export_selection_dialog (Settings tab, defaulting each axis's
    Export dialog Device combo to whatever's currently set on the main
    panel) - RosettaSet_v1.ini's usercomment is the only channel between
    those two separate gladevcp processes (see CLAUDE.md). Returns ""
    if the axis or its usercomment isn't found.
    '''
    return settings.get("axes", {}).get(axis_id, {}).get("usercomment", "")

def _combo_selected_device(combo):
    '''
    Returns the real selected value of a device-name GtkComboBoxText
    (empty string if the leading DEVICE_COMBO_PLACEHOLDER entry - index
    0 - is what's active), rather than combo.get_active_text() directly,
    which would return the placeholder's own display text. Index-based
    rather than a string comparison against DEVICE_COMBO_PLACEHOLDER so
    this keeps working even if that text is ever changed - index 0 is
    always the placeholder, in both places these combos get built
    (_load_axis_comments, _run_export_selection_dialog).
    '''
    return combo.get_active_text() if combo.get_active() > 0 else ""


# Settings tab jog-speed-grid widget id -> (REB_Settings_v1.ini tag,
# fallback default matching Rosetta.ini's own shipped value). Mirrors
# MAX_LINEAR_VELOCITY/<max_jog_speed> above, generalized to the other
# [DISPLAY]/[TRAJ] jog-speed values (see Rosetta_Setup/Rosetta_Generate_Local_Ini.py
# for the overlay side - like Max Jog Speed, each of these patches ALL
# occurrences of its ini key, both [DISPLAY] (jog slider) and [TRAJ]
# (trajectory-planner ceiling), since Rosetta.ini ships the same value in
# both places for these keys - unlike MAX_ANGULAR_VELOCITY historically,
# where [TRAJ] carried a much larger, effectively-unlimited value; this
# was a deliberate choice to unify them under one operator-facing
# control rather than leave two different meanings behind one label).


# The indexing Fwd/Rev handlers block on c.wait_complete() for as long as
# each M19 takes to converge (or time out), which otherwise leaves the UI
# looking unresponsive with no feedback that anything is happening.
def _set_busy_cursor(widget, busy):
    win = widget.get_toplevel().get_window()
    if win is None:
        return
    win.set_cursor(Gdk.Cursor.new_from_name(win.get_display(), "wait") if busy else None)
    # Force the cursor change to actually paint before the blocking MDI
    # calls take over the main loop.
    while Gtk.events_pending():
        Gtk.main_iteration()

# Used to show a plain HAL_Button as depressed/darkened while a move or
# an operation is active (X_Idx_Minus/Plus, Sp0_Move_Fwd/Rev).
# Deliberately NOT done via HAL_ToggleButton.set_active(): a real
# GtkToggleButton also flips its own active state on click or on the
# theme's native (and here, barely visible) "checked" rendering, and
# for the blocking X_Idx_Minus/Plus case specifically, the
# release-driven auto-flip happens right after our own code sets it
# back to False - undoing it and leaving the button stuck depressed
# (confirmed live). A custom CSS class on a plain, non-toggle button has
# no such built-in behavior to fight - only this code ever touches it,
# and the darkened background makes the state obvious regardless of
# theme.
# Used to be joined by three reb-axis-* label color classes
# _load_panel_axis_controls applied to recolor a channel row's letter
# label to match whichever letter that row's reassignable slot was
# currently showing. Since Rosetta_Panel_v1.ui's 18 September 2026 rebuild
# gave every role a permanent row with its own static, correct label
# color already baked in (Rosetta_Panel_v1.ui's own Pango <attributes>
# block - see AXIS_LETTER_COLOR above, still used by
# _load_panel_axis_display's read-only summary table), a row's letter
# label never needs recoloring at runtime any more - removed along with
# AXIS_LETTER_COLOR_CLASS/_AXIS_LETTER_COLOR_CLASSES.
# A button with a text label (Sync Move, Cut Thread) is also disabled
# while its move runs (MOTION_BUTTONS), and the theme draws disabled text
# grey - invisible on the darkened background (found 20 October 2026) -
# so the label is drawn white whether the button is disabled or not.
_DEPRESS_CSS = b"""
button.reb-depressed,
button.reb-depressed:hover,
button.reb-depressed:focus,
button.reb-depressed:active,
button.reb-depressed:disabled {
    background-color: shade(@theme_bg_color, 0.6);
    background-image: none;
    box-shadow: inset 2px 2px 4px rgba(0,0,0,0.6), inset -1px -1px 2px rgba(255,255,255,0.15);
}
button.reb-depressed label,
button.reb-depressed:disabled label {
    color: #ffffff;
}
"""

def _install_depress_css():
    try:
        provider = Gtk.CssProvider()
        provider.load_from_data(_DEPRESS_CSS)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        idx_log("_install_depress_css OK, screen=" + str(screen))
    except Exception as e:
        idx_log("_install_depress_css FAILED: " + str(e))

def _set_depressed(widget, depressed):
    ctx = widget.get_style_context()
    was_depressed = ctx.has_class("reb-depressed")
    if depressed:
        ctx.add_class("reb-depressed")
    else:
        ctx.remove_class("reb-depressed")
    # Only log actual transitions - the Run Operation poll calls this
    # every 100ms regardless of whether anything changed, which was
    # flooding idx_debug.log and triggering the monitor's own rate
    # limiting.
    if was_depressed != depressed:
        idx_log("_set_depressed(" + Gtk.Buildable.get_name(widget) + ", " + str(depressed)
                + ") classes=" + str(ctx.list_classes()))
    # Force the style change to actually paint now, the same reason
    # _set_busy_cursor does this - callers that bracket a blocking MDI
    # call (X_Idx_Minus/Plus) would otherwise freeze the main loop
    # before GTK gets a chance to repaint the new class, so the darkened
    # look barely shows (confirmed live: "hardly noticeable"). Periodic
    # callers (the Run Operation poll) don't strictly need this - they
    # get repainted on the next idle cycle regardless - but it's
    # harmless there too.
    while Gtk.events_pending():
        Gtk.main_iteration()

class HandlerClass:
    '''
    class with gladevcp callback handlers
    '''

    def on_button_press(self,widget,data=None):
        '''
        a callback method
        parameters are:
            the generating object instance, likte a GtkButton instance
            user data passed if any - this is currently unused but
            the convention should be retained just in case
        '''
        print ("on_button_press called")
        self.nhits += 1
        self.builder.get_object('hits').set_label("Hits: %d" % (self.nhits))

    def scroll_entries(self,widget,event):
        '''
        Lets the mouse scroll wheel scroll the viewport (e.g. on the
        Usage tab) instead of the scroll being captured by a child
        widget such as a spin button under the cursor.
        '''
        adj = widget.get_vadjustment()
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
        and never lets it reach the viewport at all, since GTK delivers
        the event straight to the most specific window under the
        pointer rather than bubbling it up through the container
        hierarchy. That widget's own built-in class handler then runs
        its default scroll behavior (increment/decrement a spin button,
        change a combo box's selection) instead.

        With the Settings tab's grid now almost entirely full of spin
        buttons (Scale + PID gains), that left almost no surface left to
        actually scroll the page from - hence wiring this onto every
        spin button/combo box individually (see
        _install_viewport_scroll_redirect) rather than relying on
        scroll_entries alone. A broader attempt at wiring *every* widget
        in the subtree (labels, grids, boxes) was tried and made things
        worse - it broke scrolling over spin buttons too, for reasons
        not fully understood - so this deliberately stays scoped to just
        the input widgets. Settled behavior: scrolling works over spin
        buttons/combo boxes; it does not work over the surrounding
        labels/empty grid space.
        '''
        viewport = widget.get_ancestor(Gtk.Viewport)
        if viewport is None:
            return False
        return self.scroll_entries(viewport, event)

    def _install_viewport_scroll_redirect(self, container):
        '''
        Recursively wires _redirect_scroll_to_viewport onto every spin
        button/combo box under container (see that method's docstring
        for why). Called once from __init__ on the Settings tab's own
        scrollable viewport - harmless/no-op everywhere else, since
        every other tab/panel's viewport (if it has one at all) has far
        fewer, more sparsely-packed input widgets and get_children()
        simply returns less to walk.
        '''
        for child in container.get_children():
            if isinstance(child, (Gtk.SpinButton, Gtk.ComboBox)):
                child.connect("scroll-event", self._redirect_scroll_to_viewport)
            if isinstance(child, Gtk.Container):
                self._install_viewport_scroll_redirect(child)

    def _set_checkbox_active(self, widget_id, active):
        '''
        Forces a checkbox to the given state. Only the main panel
        component has these widgets - every other tab/panel finds
        the widget missing and no-ops.

        Deferred via GLib.idle_add (see __init__) rather than set
        directly during __init__: the checkbox doesn't reliably end up
        checked from the .ui file's active="True" alone once the panel
        is actually interactive (confirmed live), so this runs after
        gladevcp's own startup sequence has settled instead of risking
        being overwritten by whatever resets it otherwise.
        '''
        widget = self.builder.get_object(widget_id)
        if widget is not None:
            widget.set_active(active)
        return False

    def _sync_run_operation_buttons(self):
        '''
        Keeps the Run Operation tab's Fwd/Rev buttons visually depressed/
        darkened for as long as the spindle is actually running in that
        direction, reading the real HAL state (spindle.0.forward /
        spindle.0.reverse) rather than just whatever the last click did -
        so the button reflects reality even if a move ends some other
        way (e.g. M5 from elsewhere, a fault, etc). Runs on a timer
        rather than once, since gladevcp has no built-in live binding
        for an arbitrary read-only HAL pin like this (unlike HAL_LED,
        which is built for exactly this but doesn't give a "look
        pressed" visual).

        Fwd is tied to spindle.0.reverse and Rev to spindle.0.forward -
        backwards-looking, but intentional: Sp0_Move_Fwd/Sp0_Move_Rev
        send M4/M3 respectively (see those functions' docstrings for why
        - an empirically-verified swap fixing an unexplained direction
        flip), so spindle.0.reverse is what actually goes TRUE while Fwd
        is spinning. This mirrors that same swap so the highlighted
        button still matches the one physically pressed.

        Uses _set_depressed (a plain HAL_Button plus a CSS class), not
        HAL_ToggleButton.set_active() - the theme's native "checked"
        look for a toggle button wasn't visibly different enough to
        read as "pressed" (confirmed live: hover-highlight only, no
        visible change on click).

        Only the main panel component has these widgets; every other
        tab/panel finds them missing and this becomes a no-op (but the
        timer itself, once started, keeps calling it - see __init__).
        '''
        fwd = self.builder.get_object('Sp0_Move_Fwd')
        rev = self.builder.get_object('Sp0_Move_Rev')
        if fwd is None or rev is None:
            return False

        _set_depressed(fwd, bool(hal.get_value('spindle.0.reverse')))
        _set_depressed(rev, bool(hal.get_value('spindle.0.forward')))
        return True





    def _load_axis_comments(self):
        '''
        Populates each axis's comment combo box (X_Comment etc., on the
        main Rosetta_Panel) with the persisted device-name list
        (_read_persisted_device_names - the on-disk counterpart to the
        General tab's live Device Names widget, which this component
        doesn't have access to, being a separate gladevcp process - see
        CLAUDE.md) plus a leading DEVICE_COMBO_PLACEHOLDER entry for
        "nothing chosen yet", then selects whichever entry matches that
        axis's persisted
        comment from REB_Settings_v1.ini. This is what constrains a
        comment to one of the maintained device names rather than free
        text - GtkComboBoxText (no entry) only ever offers what's been
        appended to it.

        Guarded by _applying_axis_comments so combo.set_active() below
        doesn't trigger X_Comment/etc.'s own "changed" handler and
        immediately re-save the value being loaded (same pattern as
        _load_measurement_system's _applying_measurement_system).

        Only runs in the component that actually owns these widgets -
        every other tab/panel also using Rosetta_main.py will find them
        missing and return immediately.
        '''
        if self.builder.get_object("X_Comment") is None:
            return

        settings = rosetta_settings_io.load_settings()
        device_names = _read_persisted_device_names()

        self._applying_axis_comments = True
        try:
            for axis_id in COMMENT_AXES:
                widget = self.builder.get_object(axis_id + "_Comment")
                if widget is None:
                    continue

                widget.remove_all()
                widget.append_text(DEVICE_COMBO_PLACEHOLDER)
                for name in device_names:
                    widget.append_text(name)

                stored = _read_persisted_axis_comment(axis_id, settings)
                if not stored:
                    print("No stored comment found for axis " + axis_id
                          + " in " + SETTINGS_PATH)

                try:
                    widget.set_active(device_names.index(stored) + 1 if stored else 0)
                except ValueError:
                    # Stored comment doesn't match any current device
                    # name (e.g. free text from before this became a
                    # constrained dropdown, or the device-name list
                    # changed since it was picked) - fall back to the
                    # placeholder entry rather than silently keeping an
                    # invalid value selected.
                    print(axis_id + " comment \"" + stored
                          + "\" doesn't match any device name - leaving blank")
                    widget.set_active(0)
        finally:
            self._applying_axis_comments = False

    def _autosave_axis_comments(self):
        '''
        Polling backstop for the comment combo boxes - see the
        GLib.timeout_add call in __init__ for why this exists alongside
        (not instead of) X_Comment/Z_Comment/etc.'s "changed" signal.

        Only the main panel component has these widgets; every other
        tab/panel finds them missing and returning False here cancels
        the timer entirely (same pattern as _sync_run_operation_buttons).
        '''
        if self.builder.get_object("X_Comment") is None:
            return False

        for axis_id in COMMENT_AXES:
            widget = self.builder.get_object(axis_id + "_Comment")
            if widget is None:
                continue

            text = _combo_selected_device(widget)
            if text != self._last_saved_axis_comment.get(axis_id):
                self._save_axis_comment(axis_id, text)
                self._last_saved_axis_comment[axis_id] = text

        return True









    def _load_panel_axis_display(self):
        '''
        Reads the persisted channel -> axis letter assignment and
        populates the main panel's own read-only "Axis Assignments"
        display (Panel_Channel_0N_Axis/_Type - Rosetta_Panel_v1.ui; each
        tile's "Channel 0N" frame label, _Name, is fixed text), if
        this component owns those widgets. Unlike the Axis Selection
        tab's combos, these are plain labels with no signal handlers -
        purely informational; the Settings tab is the only place the
        assignment can actually be changed. Populated once at this
        component's own startup, same as everything else keyed off
        RosettaSet_v1.ini - a change made on the Settings tab only takes
        effect (here and everywhere else) after a restart anyway, at
        which point this process reloads fresh too. No-ops outside the
        main panel component.
        '''
        if self.builder.get_object("Panel_Channel_00_Axis") is None:
            return

        assignments = _read_persisted_channel_assignments()
        # Spindles aren't axes, so _axis_type_for_letter (angular or
        # linear) doesn't apply to them - label them for what they are,
        # whichever channel they're on.
        types = {channel_id: "SPINDLE" if letter in SPINDLE_ROW_FIELDS else _axis_type_for_letter(letter)
                 for channel_id, letter in assignments.items()}
        for channel_id, letter in assignments.items():
            axis_label = self.builder.get_object("Panel_Channel_" + channel_id + "_Axis")
            if axis_label is not None:
                color = AXIS_LETTER_COLOR.get(letter)
                if color is not None:
                    # set_markup takes over the label's whole attribute
                    # list, so the big/bold styling Rosetta_Panel_v1.ui gives
                    # this label has to be restated here too, not just
                    # the color - otherwise it would revert to plain text
                    # the moment this runs.
                    axis_label.set_markup(
                        '<span foreground="' + color + '" font_desc="DejaVu Serif 24" weight="bold">'
                        + letter + '</span>'
                    )
                else:
                    axis_label.set_text(letter)

            type_label = self.builder.get_object("Panel_Channel_" + channel_id + "_Type")
            if type_label is not None:
                type_label.set_text(types[channel_id].capitalize())

        # Two-box hardware: the expansion box's four tiles (channels
        # 06-09, to the right of the base box's 3 x 2) only show while
        # it's connected (Rich's choice, 14 October 2026). no_show_all
        # keeps a later show_all() from bringing them back.
        expansion = _panel_settings().get("expansion_box") is True
        for channel_id in rosetta_settings_io.EXPANSION_CHANNELS:
            tile = self.builder.get_object("Panel_Channel_" + channel_id + "_Axis")
            while tile is not None and not isinstance(tile, Gtk.Frame):
                tile = tile.get_parent()
            if tile is not None:
                tile.set_no_show_all(not expansion)
                tile.set_visible(expansion)

    def _load_panel_axis_controls(self):
        '''
        Greys out (set_sensitive(False)) every widget belonging to a
        role (one of the 8 axis letters or 2 spindles - PANEL_INTERNAL_IDS)
        not currently assigned to any channel, if this component owns
        the main panel's widgets.

        Before Rosetta_Panel_v1.ui's 18 September 2026 rebuild, this method
        also had to swap each row's letter/color/jog images and
        rewrite its Feed/Idx adjustment ranges at runtime, because a
        row was a reassignable channel *slot* that could end up
        showing any letter. Every role now has its own permanent row
        with that content already correct and baked in statically (see
        Rosetta_Panel_v1.ui) - a role's identity never changes, only
        whether it's currently assigned to a channel does, which is the
        only thing left for this method to reflect.

        Populated once at this component's own startup, same as
        _load_panel_axis_display - a reassignment made on the Settings
        tab only takes effect after a restart anyway, at which point
        this process reloads fresh too. No-ops outside the main panel
        component.
        '''
        if self.builder.get_object("X_ENA") is None:
            return

        for axis in AXIS_SELECTION_LETTERS:
            role_active = axis in _ACTIVE_ROLES_AT_STARTUP
            for suffix in AXIS_ROW_FIELDS:
                widget = self.builder.get_object(axis + suffix)
                if widget is not None:
                    widget.set_sensitive(role_active)
                    if suffix == "_ENA" and not role_active:
                        widget.set_property("light-off-color", _UNASSIGNED_ENA_LIGHT_COLOR)

        for spindle_id, widget_ids in SPINDLE_ROW_FIELDS.items():
            role_active = spindle_id in _ACTIVE_ROLES_AT_STARTUP
            for widget_id in widget_ids:
                widget = self.builder.get_object(widget_id)
                if widget is not None:
                    widget.set_sensitive(role_active)
                    if widget_id == spindle_id + "_ENA" and not role_active:
                        widget.set_property("light-off-color", _UNASSIGNED_ENA_LIGHT_COLOR)

    def _save_axis_comment(self, axis_id, text):
        '''
        Writes a single axis's comment back into REB_Settings_v1.ini's
        usercomment value for that axis. Called from each comment
        Entry's focus-out-event handler below.
        '''
        settings = rosetta_settings_io.load_settings()
        settings.setdefault("axes", {}).setdefault(axis_id, {})["usercomment"] = text
        rosetta_settings_io.save_settings(settings)
        print("Saved " + axis_id + " comment")



    def _on_machine_is_on_changed(self, hal_pin, data=None):
        '''
        Grays out the main panel's whole grid of axis/spindle controls
        whenever the machine is not powered on, so nothing on it can be
        operated until the operator powers the machine on. GTK
        propagates insensitivity to every child of a container, so
        toggling this one grid is enough for the whole panel.

        No-op in every component other than the main panel (MainGrid),
        which is the only one with this widget.
        '''
        grid = self.builder.get_object("MainGrid")
        if grid is None:
            return
        grid.set_sensitive(bool(hal_pin.get()))

    # Each of these is wired to its GtkComboBoxText's "changed" signal
    # (see Rosetta_Panel_v1.ui) - fired the instant the operator picks a
    # different entry, and also by combo.set_active() in
    # _load_axis_comments itself, which is why each checks
    # _applying_axis_comments first: without that guard, loading the
    # persisted comment at startup would immediately re-save the exact
    # value just read (same pattern as Measurement_System_Changed).
    # _combo_selected_device() (not get_active_text() directly) reads
    # back "" when the leading DEVICE_COMBO_PLACEHOLDER entry is active,
    # rather than saving that placeholder text itself as the comment.
    def X_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("X", _combo_selected_device(widget))

    def Z_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("Z", _combo_selected_device(widget))

    def U_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("U", _combo_selected_device(widget))

    def V_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("V", _combo_selected_device(widget))

    def W_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("W", _combo_selected_device(widget))

    def B_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("B", _combo_selected_device(widget))

    def A_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("A", _combo_selected_device(widget))

    def C_Comment(self, widget):
        if self._applying_axis_comments:
            return
        self._save_axis_comment("C", _combo_selected_device(widget))

# B's jog/feed/index/scale/ena handlers used to be hand-written here
# (B_Move_Idx_Fwd/Rev, B_Set_Idx_Feed, B_Set_Idx_Dist, B_Set_Idx_DegDiv,
# B_Set_Move_Dist, B_Set_Scale, B_Set_Ena) - they're now generated by the
# same factories as every other letter (see "Generated per-letter
# handlers" below) - B's widget ids were renamed to match the rest
# rather than the factories needing to carry a B-specific exception.

# ********************************************************************
#    AA     LL       LL              AA    XX    XX EEEEEEEE  SSSSSS 
#   AAAA    LL       L              AAAA    XX  XX  EE       SSS   SS
#  AA  AA   LL       LL            AA  AA    XXXX   EE        SSS 
# AAAAAAAA  LL       LL           AAAAAAAA   XXXX   EEEEE        SSS 
# AA    AA  LL       LL           AA    AA  XX  XX  EE       SS    SS
# AA    AA  LLLLLLLL LLLLLLLL     AA    AA XX    XX EEEEEEEE  SSSSSS  
# ********************************************************************

#######################################################################
# OpenRosettaWebsite
# Purpose:              This is used to open the Rosetta
#                       website.
# Updated:              ver 1.0, 06 August 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel_v1
#   Button:             Open Library  (HAL_Button)
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenRosettaWebsite(self,widget):

        print("=================================================")
        print("FUNCTION OpenRosettaWebsite")

        url = WEBSITE_URL
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

#######################################################################
# OpenGcodeLibrary
# Purpose:              This is used to open the Rosetta
#                       Gcode library web page.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Tab_Help
#   Button:             Gcode_Library
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenGcodeLibrary(self,widget):

        print("=================================================")
        print("FUNCTION OpenGcodeLibrary")

        url = GCODE_LIBRARY_URL
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

#######################################################################
# OpenGcodeQuickReference
# Purpose:              This is used to open the LinuxCNC Gcode Quick
#                       Reference.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Tab_Help
#   Button:             Gcode_QuickRef
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenGcodeQuickReference(self,widget):

        print("=================================================")
        print("FUNCTION OpenGcodeQuickReference")

        url = "https://linuxcnc.org/docs/html/gcode.html"
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

#######################################################################
# OpenLibrary
# Purpose:              This is used to open the Rosetta
#                       web page.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#                       Rosetta_Tab_Help
#   Button:             Library
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenLibrary(self,widget):

        print("=================================================")
        print("FUNCTION OpenLibrary")

        url = WEBSITE_URL
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

#######################################################################
# OpenOTHandyBook
# Purpose:              This is used to open the Ornamental Turner's
#                       Handy Book
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Tab_Help
#   Button:             OT_HandyBook
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       Rosetta_Help
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenOTHandyBook(self,widget):

        print("=================================================")
        print("FUNCTION OpenOTHandyBook")

        url = "https://mdfre2.colvintools.com/Documents/OTHB.pdf"
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

#######################################################################
# OpenUserForum
# Purpose:              This is used to open the Rosetta
#                       forum web page.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Tab_Help
#   Button:             User_Forum
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       Rosetta_Help
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenUserForum(self,widget):

        print("=================================================")
        print("FUNCTION OpenUserForum")

        url = USER_FORUM_URL
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

#######################################################################
# OpenUserManual
# Purpose:              This is used to open the Rosetta
#                       user manual web page.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Tab_Help
#   Button:             User_Manual
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def OpenUserManual(self,widget):

        print("=================================================")
        print("FUNCTION OpenUserManual")

        url = USER_MANUAL_URL
        webbrowser.open(url)

        Prt1 = "Opening website " + url
        print(Prt1)

# ********************************************************************
#  SSSSSS  PPPPPPP  IIIIIIII N     NN DDDDDDD  LL       EEEEEEEE   0000
# SS    SS PP    PP    II    NN    NN DD    DD LL       EE        00  00
#  SSS     PP    PP    II    NNN   NN DD    DD LL       EEEEE    00    00
#     SSS  PPPPPPP     II    NN NN NN DD    DD LL       EE       00    00
# SS    SS PP          II    NN  NNNN DD    DD LL       EE        00  00
#  SSSSSS  PP       IIIIIIII NN    NN DDDDDDD  LLLLLLLL EEEEEEEE   0000
# ********************************************************************

#######################################################################
# Sp0_Move_Fwd
# Purpose:              This is used to start the spindles rotating
#                           forward.
#                       Note:  this starts both Sp0 and Sp1.
#                       Note:  sends M4, not M3 - see the Gcode0/Gcode1
#                           comment below. This is an intentional,
#                           empirically-verified swap, not a typo.
# Updated:              ver 1.2, 08 August 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Move_Fwd  (Hal_Button)
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     self.Sp0_Feed
#                       self.Sp1_Pct
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        M4 (S combined on the same line - see below)
#######################################################################
    def Sp0_Move_Fwd(self,widget):

        print("=================================================")
        print("FUNCTION Sp0_Move_Fwd")

        # Ensure the system is in MDI mode - only switch if not already
        # there (matches _axis_idx_move/B_Move_Idx_Fwd/Sp0_Move_Idx_Fwd
        # etc.). This used to call c.mode(MODE_MDI) unconditionally on
        # every press, even when already in MDI mode from the previous
        # one - a redundant mode-switch no other handler in this file
        # does, and one a human typing directly into the AXIS MDI box
        # never triggers either. Re-entering MDI mode while already in
        # it is exactly the kind of thing that can carry an internal
        # abort/reset side effect in LinuxCNC's task controller, and was
        # removed as a suspect once the wait_complete()-between-mdi-calls
        # fix (see Gcode0/Gcode1 below) alone didn't resolve the spindle
        # 0 direction flip found via live halcmd pin tracing.
        s.poll()
        if s.task_state != linuxcnc.MODE_MDI:
                c.mode(linuxcnc.MODE_MDI)
                c.wait_complete() # Wait for mode change to complete

        # Set the feed rates
        Sp1_Feed = self.Sp1_Pct * self.Sp0_Feed / 100

        # Sends M4, not M3, despite this being the Fwd handler - an
        # empirical workaround, not a mistake. Live halcmd pin tracing
        # (spindle.0.forward/reverse/speed-out, which are motion-controller
        # output pins Rosetta.hal/this file cannot influence) proved that
        # M3 $0 S<speed>, sent via this component's c.mdi(), reliably
        # commands spindle.0.reverse=TRUE / speed-out negative - i.e.
        # actual reverse rotation - while the byte-identical line typed
        # into the AXIS MDI box by hand, in the same live session,
        # reliably commands forward. Ruled out along the way: the S
        # value's sign (always positive), the "$-1"/all-spindles form
        # (replaced with per-spindle $0/$1 addressing), missing
        # wait_complete() between the two spindles' mdi() calls (fixed -
        # each now waits before the next is sent), and a redundant
        # unconditional c.mode(MODE_MDI) call this used to make on every
        # press (removed - now matches every other MDI-issuing handler's
        # conditional-only mode switch). None of those changed the
        # outcome, and manually replaying this exact two-line sequence
        # by hand did not reproduce the flip either - so whatever
        # actually causes it remains unexplained. Sending M4 here (and
        # M3 in Sp0_Move_Rev) is the pragmatic fix: it makes the physical
        # rotation match the button pressed, at the cost of the M-code
        # sent no longer matching the function name/button label.
        Gcode0 = "M4 $0 S" + str(self.Sp0_Feed)
        Gcode1 = "M4 $1 S" + str(Sp1_Feed)

        print(Gcode0)
        c.mdi(Gcode0)
        c.wait_complete()

        print(Gcode1)
        c.mdi(Gcode1)
        c.wait_complete()

    def _spindle_index_target(self, n, sign):
        '''
        Target angle (0-360) for spindle n's next index, sign +1 or -1
        times Sp0_Idx_Deg from the previous index's target - see
        SPINDLE_INDEX_TRACK_DEGREES - and remembered for the next one.
        '''
        current = (hal.get_value('spindle.%d-position-fb' % n) % 1.0) * 360.0
        if not hasattr(self, "_spindle_last_target"):
            self._spindle_last_target = {}
        start = current
        last = self._spindle_last_target.get(n)
        if last is not None:
            off = (current - last + 180.0) % 360.0 - 180.0
            if abs(off) <= SPINDLE_INDEX_TRACK_DEGREES:
                start = last
        target = (start + sign * self.Sp0_Idx_Deg) % 360.0
        self._spindle_last_target[n] = target
        idx_log("Sp%d index: at %.4f, from %.4f, target %.4f" % (n, current, start, target))
        return target

    @staticmethod
    def _set_spindle_index_direction(sign):
        '''
        Makes the next index turn one way only (SPINDLE_INDEX_MODE) on
        both spindles - orient.N.mode isn't connected to anything, so
        it's set directly.
        '''
        for n in (0, 1):
            try:
                subprocess.run(["halcmd", "setp", "orient.%d.mode" % n,
                                str(SPINDLE_INDEX_MODE[sign])], check=True, timeout=5)
            except (OSError, subprocess.SubprocessError) as e:
                idx_log("could not set orient.%d.mode: %s" % (n, e))

    def _index_both_spindles_simultaneously(self, sign):
        '''
        Indexes Sp0 and Sp1 together, in the same servo-thread cycle,
        by driving orient.0/orient.1's target angle and trigger bit
        directly through the Sp0-idx-angle/Sp1-idx-angle and
        Sp0-idx-active/Sp1-idx-active HAL pins (see Rosetta.hal's Sp0/Sp1
        blocks: mux2.2/mux2.3 select this angle over the M19-driven
        one, or2.0/or2.1 OR this active bit into the same enable chain
        M19 already used) - entirely bypassing M19/MDI, unlike the
        single-spindle path in Sp0_Move_Idx_Fwd/Rev.

        This exists because that M19 path is fundamentally sequential -
        LinuxCNC's M19 blocks the (single-threaded) interpreter until
        that spindle reports oriented, so a second M19 for the other
        spindle cannot even begin until the first returns. Queuing both
        back-to-back with only one final wait_complete() was tried and
        dropped Sp1's move entirely (see Sp0_Move_Idx_Fwd's git history).
        orient.0 and orient.1 are fully independent realtime components
        with their own PID loop each (pid.p0/pid.p1), so once both
        Active bits are set - each individual halcmd-style pin write
        only microseconds apart - both land well within the same or
        adjacent servo-thread cycle and both spindles move at once.

        sign is +1 for Sp0_Move_Idx_Rev (the Fwd/Rev handlers pass a
        swapped sign - see their docstrings), -1 for Sp0_Move_Idx_Fwd.
        Only called when both Sp0_Idx_Bool and Sp1_Idx_Bool are true
        (see callers).
        '''
        self._set_spindle_index_direction(sign)
        target_angle_0 = self._spindle_index_target(0, sign)
        target_angle_1 = self._spindle_index_target(1, sign)

        idx_log("Simultaneous index: Sp0 target=" + str(target_angle_0)
                + "  Sp1 target=" + str(target_angle_1))

        # Set both target angles first - orient.N samples position/angle
        # on Active's rising edge (see Rosetta.hal comments) - then trigger
        # both together.
        self.halcomp['Sp0-idx-angle'] = target_angle_0
        self.halcomp['Sp1-idx-angle'] = target_angle_1
        self.halcomp['Sp0-idx-active'] = True
        self.halcomp['Sp1-idx-active'] = True

        try:
            deadline = time.time() + SIMULTANEOUS_INDEX_TIMEOUT
            sp0_done = False
            sp1_done = False
            while time.time() < deadline:
                if not sp0_done and hal.get_value('orient.0.is-oriented'):
                    sp0_done = True
                    idx_log("Sp0 oriented")
                if not sp1_done and hal.get_value('orient.1.is-oriented'):
                    sp1_done = True
                    idx_log("Sp1 oriented")
                if sp0_done and sp1_done:
                    break
                # Keep the GUI responsive while polling - same reason
                # _set_busy_cursor/_set_depressed force a repaint before
                # a blocking call takes over the main loop.
                while Gtk.events_pending():
                    Gtk.main_iteration()
                time.sleep(0.02)
            else:
                idx_log("Simultaneous index TIMED OUT - Sp0 oriented=" + str(sp0_done)
                        + " Sp1 oriented=" + str(sp1_done))
        finally:
            # Clear the trigger bits regardless of outcome - orient.N
            # only reacts to the next rising edge, so leaving Active
            # stuck True would just be a no-op until cleared and
            # re-raised anyway, but clearing it now keeps HAL state
            # consistent with "idle" for the next press.
            self.halcomp['Sp0-idx-active'] = False
            self.halcomp['Sp1-idx-active'] = False

#######################################################################
# Sp0_Move_Idx_Fwd
# Purpose:              This is used to index the Sp0 spindle in a
#                           forward direction.
#                       Note:  indexes toward a lower angle (sign -1),
#                           not higher, despite being the Fwd handler -
#                           see Sp0_Move_Fwd's docstring for the same
#                           empirically-verified swap applied here.
# Updated:              ver 1.1, 08 August 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Idx_Fwd
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     self.Sp0_Idx_Deg
#                       self.Sp1_Pct
#       Set:            (none)
#   Written to UI:      B_Idx_Qty - the quantity of indexes so far.
#                           Forward increases this value.
# ---------------------------------------------------------------------
# Gcodes Called:        M19
#######################################################################
    def Sp0_Move_Idx_Fwd(self,widget):

        idx_log("=================================================")
        idx_log("FUNCTION Sp0_Move_Idx_Fwd")
        idx_log("Sp0_Idx_Bool = " + str(self.Sp0_Idx_Bool) + "  Sp1_Idx_Bool = " + str(self.Sp1_Idx_Bool))

        if not self.Sp0_Idx_Bool and not self.Sp1_Idx_Bool:
            idx_log("No spindle enabled - aborting move")
            _show_no_spindle_enabled_popup(widget)
            return
        if not _confirm_roles_enabled(widget, [sp for sp, on in (("Sp0", self.Sp0_Idx_Bool),
                                                                 ("Sp1", self.Sp1_Idx_Bool)) if on]):
            return

        _set_busy_cursor(widget, True)
        try:
            # Ensure the system is in MDI mode
            s.poll()
            if s.task_state != linuxcnc.MODE_MDI:
                    c.mode(linuxcnc.MODE_MDI)
                    c.wait_complete() # Wait for mode change to complete

            # Set spindle rotational speeds
            GcodeStr1 = "S0 " + str(self.Sp0_Feed)
            idx_log(GcodeStr1)

            Sp1_Feed = self.Sp0_Feed * self.Sp1_Pct / 100
            GcodeStr2 = "S1 " + str(Sp1_Feed)
            idx_log(GcodeStr2)

            c.mdi(GcodeStr1)
            c.mdi(GcodeStr2)

            if self.Sp0_Idx_Bool and self.Sp1_Idx_Bool:
                # Both selected - drive both spindles' orient chains
                # directly and simultaneously (see
                # _index_both_spindles_simultaneously) instead of two
                # sequential M19s. sign is -1, not +1 - see this
                # function's docstring.
                self._index_both_spindles_simultaneously(-1)
                self._bump_idx_count("Sp0", -1)
                return

            # M19 orients to an absolute angle, not a relative step, so compute
            # the next target from each spindle's own actual current angle
            # rather than sending Sp0_Idx_Deg itself as R each time (which
            # would just re-target the same fixed angle on every press). Only
            # one of Sp0_Idx_Bool/Sp1_Idx_Bool can be true here (the both-true
            # case already returned above), so exactly one of the two blocks
            # below runs - a spindle the operator hasn't enabled is simply
            # skipped rather than sent a command that can only time out.
            if self.Sp0_Idx_Bool:
                # One direction only (SPINDLE_INDEX_MODE, set directly on
                # orient.N.mode - M19's P word isn't connected to it).
                # Forcing a direction with M19 P1/P2 was tried before and
                # took the long ~270 degree way: the modes were the other
                # way round from the buttons, whose ids don't match their
                # columns.
                self._set_spindle_index_direction(-1)
                target_angle = self._spindle_index_target(0, -1)
                GcodeStr3 = "M19 R" + str(target_angle) + " Q20 P0 $0"
                idx_log(GcodeStr3)
                c.mdi(GcodeStr3)
                c.wait_complete()
            else:
                idx_log("Sp0 M19 skipped (Sp0_Idx_Bool is False)")

            if self.Sp1_Idx_Bool:
                self._set_spindle_index_direction(-1)
                target_angle_1 = self._spindle_index_target(1, -1)

                GcodeStr4 = "M19 R" + str(target_angle_1) + " Q20 P0 $1"
                idx_log(GcodeStr4)
                c.mdi(GcodeStr4)
                c.wait_complete()
            else:
                idx_log("Sp1 M19 skipped (Sp1_Idx_Bool is False)")
            self._bump_idx_count("Sp0", -1)
        finally:
            _set_busy_cursor(widget, False)

#######################################################################
# Sp0_Move_Idx_Rev
# Purpose:              This is used to index the Sp0 spindle in a
#                           reverse direction.
#                       Note:  indexes toward a higher angle (sign +1),
#                           not lower, despite being the Rev handler -
#                           see Sp0_Move_Idx_Fwd/Sp0_Move_Fwd's
#                           docstrings for the same empirically-verified
#                           swap applied here.
# Updated:              ver 1.1, 08 August 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Idx_Rev
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     self.Sp0_Idx_Deg
#                       self.Sp1_Pct
#       Set:            (none)
#   Written to UI:      B_Idx_Qty - the quantity of indexes so far.
#                           Forward increases this value.
# ---------------------------------------------------------------------
# Gcodes Called:        M19
#######################################################################
    def Sp0_Move_Idx_Rev(self,widget):

        idx_log("=================================================")
        idx_log("FUNCTION Sp0_Move_Idx_Rev")
        idx_log("Sp0_Idx_Bool = " + str(self.Sp0_Idx_Bool) + "  Sp1_Idx_Bool = " + str(self.Sp1_Idx_Bool))

        if not self.Sp0_Idx_Bool and not self.Sp1_Idx_Bool:
            idx_log("No spindle enabled - aborting move")
            _show_no_spindle_enabled_popup(widget)
            return
        if not _confirm_roles_enabled(widget, [sp for sp, on in (("Sp0", self.Sp0_Idx_Bool),
                                                                 ("Sp1", self.Sp1_Idx_Bool)) if on]):
            return

        _set_busy_cursor(widget, True)
        try:
            # Ensure the system is in MDI mode
            s.poll()
            if s.task_state != linuxcnc.MODE_MDI:
                    c.mode(linuxcnc.MODE_MDI)
                    c.wait_complete() # Wait for mode change to complete

            # Set spindle rotational speeds
            GcodeStr1 = "S0 " + str(self.Sp0_Feed)
            idx_log(GcodeStr1)

            Sp1_Feed = self.Sp0_Feed * self.Sp1_Pct / 100
            GcodeStr2 = "S1 " + str(Sp1_Feed)
            idx_log(GcodeStr2)

            c.mdi(GcodeStr1)
            c.mdi(GcodeStr2)

            if self.Sp0_Idx_Bool and self.Sp1_Idx_Bool:
                # Both selected - see matching branch in Sp0_Move_Idx_Fwd.
                # sign is +1, not -1 - see this function's docstring.
                self._index_both_spindles_simultaneously(+1)
                self._bump_idx_count("Sp0", +1)
                return

            # See Sp0_Move_Idx_Fwd for how the target is computed per-spindle
            # (_spindle_index_target), and why the checkboxes gate each M19 (only
            # one of Sp0_Idx_Bool/Sp1_Idx_Bool can be true past this point).
            if self.Sp0_Idx_Bool:
                # One direction only - see Sp0_Move_Idx_Fwd.
                self._set_spindle_index_direction(+1)
                target_angle = self._spindle_index_target(0, +1)
                GcodeStr3 = "M19 R" + str(target_angle) + " Q20 P0 $0"
                idx_log(GcodeStr3)
                c.mdi(GcodeStr3)
                c.wait_complete()
            else:
                idx_log("Sp0 M19 skipped (Sp0_Idx_Bool is False)")

            if self.Sp1_Idx_Bool:
                self._set_spindle_index_direction(+1)
                target_angle_1 = self._spindle_index_target(1, +1)

                GcodeStr4 = "M19 R" + str(target_angle_1) + " Q20 P0 $1"
                idx_log(GcodeStr4)
                c.mdi(GcodeStr4)
                c.wait_complete()
            else:
                idx_log("Sp1 M19 skipped (Sp1_Idx_Bool is False)")
            self._bump_idx_count("Sp0", +1)
        finally:
            _set_busy_cursor(widget, False)

#######################################################################
# Sp0_Move_Rev
# Purpose:              This is used to start the spindles rotating in
#                           reverse.
#                       Note:  this starts both Sp0 and Sp1.
#                       Note:  sends M3, not M4 - see the Gcode0/Gcode1
#                           comment below (and Sp0_Move_Fwd's). This is
#                           an intentional, empirically-verified swap,
#                           not a typo.
# Updated:              ver 1.2, 08 August 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Move_Rev  (Hal_Button)
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     self.Sp0_Feed
#                       self.Sp1_Pct
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        M3 (S combined on the same line - see below)
#######################################################################
    def Sp0_Move_Rev(self,widget):

        print("=================================================")
        print("FUNCTION Sp0_Move_Rev")

        # Ensure the system is in MDI mode - only switch if not already
        # there. See Sp0_Move_Fwd for why the previous unconditional
        # c.mode(MODE_MDI) call was removed.
        s.poll()
        if s.task_state != linuxcnc.MODE_MDI:
                c.mode(linuxcnc.MODE_MDI)
                c.wait_complete() # Wait for mode change to complete

        # In case the values had not already been written to the
        # Gcode S values, write them.
        Sp1_Feed = self.Sp1_Pct * self.Sp0_Feed / 100

        # Sends M3, not M4, despite this being the Rev handler - see the
        # Gcode0/Gcode1 comment in Sp0_Move_Fwd for the full explanation
        # (live pin tracing showed M4 here reliably commanding forward
        # rotation instead of reverse, with no root cause found after
        # ruling out S sign, "$-1" addressing, missing wait_complete()
        # between the two spindles' mdi() calls, and a redundant
        # unconditional mode switch). This is the matching pragmatic swap.
        Gcode0 = "M3 $0 S" + str(self.Sp0_Feed)
        Gcode1 = "M3 $1 S" + str(Sp1_Feed)

        print(Gcode0)
        c.mdi(Gcode0)
        c.wait_complete()

        print(Gcode1)
        c.mdi(Gcode1)
        c.wait_complete()

#######################################################################
# Move_Stop
# Purpose:              This is used to stop any movement.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Buttons:            Sp0_Move_Stop  (Hal_Button)
#   Signal:             GtkButton/pressed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       Rosetta_Panel
#   Program Variables
#       Referenced:     (none)
#       Set:            (none)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        M5
#######################################################################
    def Move_Stop(self,widget):

        print("=================================================")
        print("FUNCTION Move_Stop")

        # Ensure the system is in MDI mode
        s.poll()
        if s.task_state != linuxcnc.MODE_MDI:
                c.mode(linuxcnc.MODE_MDI)
                c.wait_complete() # Wait for mode change to complete

        # Send an MDI command to stop the spindles from rotating.
        Gcode = "M5"

        print(Gcode)
        c.mdi(Gcode)

        c.mdi("M5")

        # Wait for the command to complete
        c.wait_complete()

#######################################################################
# Sp0_Set_Feed
# Purpose:              This is used to set the base feed rate for the
#                           spindle (Sp0) & the rosette phaser
#                           multiplier (Sp1).  (Sp1 gets multiplied
#                           by the value of Sp1Pct
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Set_Feed  (Hal_SpinButton)
#   Signal:             GtkSpinButton/value-changed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       Sp0_Feed from Sp0_Spd on the UI
#   Program Variables
#       Referenced:     (none)
#       Set:            self.Sp0_Feed - the speed for the spindle
#                           (Sp0)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        S
#######################################################################
    def Sp0_Set_Feed(self,widget):

        print("=================================================")
        print("FUNCTION Sp0_Set_Feed")

        self.Sp0_Feed = round(widget.get_value(), 1)
        print("self.Sp0_Feed = " + str(self.Sp0_Feed))
        # Restoring the saved panel at startup - don't send an S word.
        if getattr(self, "_restoring_panel", False):
            return

        # The spinbutton's arrows auto-repeat while held, firing
        # value-changed on every tick. c.mdi()/c.wait_complete() below
        # block the GTK main loop (same issue noted in _set_busy_cursor
        # and _axis_set_scale above), so sending them on every tick was
        # freezing the whole panel - including the spinbutton's own
        # on-screen digits - for as long as the button stayed held.
        # Debounce: only actually dispatch once the value has settled for
        # 150ms, so GTK is free to repaint between ticks.
        if self.Sp0_Feed_debounce_id is not None:
            GLib.source_remove(self.Sp0_Feed_debounce_id)
        self.Sp0_Feed_debounce_id = GLib.timeout_add(150, self._Sp0_Send_Feed)

    def _Sp0_Send_Feed(self):

        self.Sp0_Feed_debounce_id = None

        Sp1_Feed = round(self.Sp0_Feed * self.Sp1_Pct / 100, 2)

        Gcode0 = "S" + str(self.Sp0_Feed) + " $0"
        Gcode1 = "S" + str(Sp1_Feed) + " $1"

        # Ensure the system is in MDI mode
        s.poll()
        if s.task_state != linuxcnc.MODE_MDI:
                c.mode(linuxcnc.MODE_MDI)
                c.wait_complete() # Wait for mode change to complete

        # Send an MDI commands to set the spindle speeds.
        print(Gcode0)
        c.mdi(Gcode0)

        print(Gcode1)
        c.mdi(Gcode1)

        # Wait for the command to complete
        c.wait_complete()

        return False  # one-shot timeout, not a repeating GLib source

#######################################################################
# Sp0_Set_Idx_bW_DegDiv
# Purpose:              This is used to set the rotational distance
#                       measurement for the Sp0 & Sp1 spindles.
#                       If degrees, set to divisions; 
#                       if divisions, set to degrees.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Set_Idx_Deg  (HAL_RadioButton)
#                       Sp0_Set_Idx_Div  (HAL_RadioButton)
#   Signal:             GtkToggledButton/toggled
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     self.Sp0_Idx_Dist - distance field data
#       Set:            self.Sp0_Idx_Deg - degrees to index
#                       self.Sp0_Idx_DegDiv - type of distance
#                           measurement (Deg or Div)
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
# Index counters
# Purpose:              The small number left of each Indexing row's
#                       Distance (<key>_Idx_Count, a flat button holding
#                       <key>_Idx_Count_Label; key = an axis letter, or
#                       Sp0 for the shared spindle row): +1 for each
#                       press of the row's Fwd (plus-sign column) index
#                       button, -1 for each Rev (minus-sign column) - it
#                       follows the column, not the button's id, since
#                       the ids don't match their columns (X_Idx_Plus /
#                       Sp0_Idx_Fwd sit under Rev). Counted once the move
#                       has been sent, so a move stopped part way still
#                       counts. Kept in self.<key>_Idx_Qty, reset to 0 at
#                       startup, when the row's distance or deg/div
#                       changes, and on a double-click of the number
#                       (Idx_Count_Clicked).
#                       Never saved.
# Updated:              ver 1.0, 11 October 2026
#######################################################################
    def _set_idx_count(self, key, value):
        setattr(self, key + "_Idx_Qty", value)
        label = self.builder.get_object(key + "_Idx_Count_Label")
        if label is not None:
            label.set_text(str(value))

    def _bump_idx_count(self, key, delta):
        self._set_idx_count(key, getattr(self, key + "_Idx_Qty", 0) + delta)
        print(key + "_Idx_Qty = " + str(getattr(self, key + "_Idx_Qty")))

    def Idx_Count_Clicked(self, widget):
        # Double-click resets; a single click does nothing. Built on the
        # button's own "clicked" signal (two within the desktop's
        # double-click time) rather than button-press-event's
        # _2BUTTON_PRESS - a GtkButton's own click handling can take the
        # real mouse presses before a button-press-event handler sees
        # them (on 11 October 2026 clicking the number didn't reset it).
        key = Gtk.Buildable.get_name(widget)[:-len("_Idx_Count")]
        clicks = self.__dict__.setdefault("_idx_count_last_click", {})
        now = time.monotonic()
        limit = Gtk.Settings.get_default().get_property("gtk-double-click-time") / 1000.0
        if now - clicks.get(key, -1e9) <= limit:
            self._set_idx_count(key, 0)
            clicks[key] = -1e9
        else:
            clicks[key] = now

#######################################################################
    def Sp0_Set_Idx_DegDiv(self,widget):

        idx_log("=================================================")
        idx_log("FUNCTION Sp0_Set_Idx_DegDiv")

        # Sp0_Set_Idx_bW_Deg and Sp0_Set_Idx_bW_Div are a GTK radio pair
        # sharing this one "toggled" handler - clicking either one fires
        # this handler TWICE (once for the button going active, once for
        # its paired sibling going inactive). Blindly flipping our own
        # mode flag on every call meant one click flipped it there and
        # back, net no-op - Div mode could never actually engage. Reading
        # the widget directly and ignoring the "going inactive" call fixes
        # it the same way the Sp0/Sp1 index checkboxes were fixed earlier.
        if not widget.get_active():
            idx_log("Sp0_Set_Idx_DegDiv ignored (widget going inactive)")
            return

        self.Sp0_Idx_DegDiv = "Div" if Gtk.Buildable.get_name(widget) == "Sp0_Set_Idx_bW_Div" else "Deg"

        if self.Sp0_Idx_DegDiv == "Div":
            self.Sp0_Idx_Deg = round(360 / self.Sp0_Idx_Dist, 1)
        else:
            self.Sp0_Idx_Deg = round(self.Sp0_Idx_Dist, 1)

        idx_log("Sp0_Idx_DegDiv = " + self.Sp0_Idx_DegDiv)
        idx_log("Sp0_Idx_Deg = " + str(self.Sp0_Idx_Deg))
        self._set_idx_count("Sp0", 0)

#######################################################################
# Sp0_Set_Idx_Dist
# Purpose:              This is used to set the distance that and index
#                           operation moves the spindles(s).  This is
#                           used with self.Sp0_Idx_DegDiv to set the
#                           actual movement distance.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Set_Idx_Dist  (Hal_SpinButton)
#   Signal:             GtkSpinButton/value-changed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            self.Sp0_Idx_Dist
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def Sp0_Set_Idx_Dist(self,widget):

        idx_log("=================================================")
        idx_log("FUNCTION Sp0_Set_Idx_Dist")

        self.Sp0_Idx_Dist = round(widget.get_value(), 1)
        idx_log("self.Sp0_Idx_Dist = " + str(self.Sp0_Idx_Dist))

        # Sp0_Idx_Deg is what every M19 move actually uses, and it must
        # track the current Deg/Div mode here too - previously it was only
        # recalculated inside Sp0_Set_Idx_DegDiv (the mode toggle), so
        # changing the distance value while already in Div mode had no
        # effect on the actual move size until the mode was toggled again.
        if self.Sp0_Idx_DegDiv == "Div":
            self.Sp0_Idx_Deg = round(360 / self.Sp0_Idx_Dist, 1)
        else:
            self.Sp0_Idx_Deg = round(self.Sp0_Idx_Dist, 1)
        idx_log("self.Sp0_Idx_Deg = " + str(self.Sp0_Idx_Deg))
        self._set_idx_count("Sp0", 0)

#######################################################################
# Sp0_Set_Idx_OnOff
# Purpose:              This is used to set the use of Sp1 indexing
#                           on or off.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp0_Set_Idx_OnOff
#   Signal:             GtkToggleButton/toggled
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            self.Sp0_Idx_Bool
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def Sp0_Set_Idx_OnOff(self,widget):

        idx_log("=================================================")
        idx_log("FUNCTION Sp0_Set_Idx_OnOff")

        # Read the checkbox's actual state rather than blindly flipping our
        # own flag - the "toggled" signal isn't guaranteed to fire exactly
        # once per user click, so blindly flipping let this drift out of
        # sync with what the checkbox visually shows.
        self.Sp0_Idx_Bool = widget.get_active()
        idx_log("Sp0_Idx_Bool = " + str(self.Sp0_Idx_Bool))

#######################################################################
# Sp0_Set_Ena
# Purpose:              See B_Set_Ena - same pattern, for Sp0.
#######################################################################
    def Sp0_Set_Ena(self,widget,*args):
        _clear_ena_override('Sp0')

# ********************************************************************
#  SSSSSS  PPPPPPP  IIIIIIII N     NN DDDDDDD  LL       EEEEEEEE  1111
# SS    SS PP    PP    II    NN    NN DD    DD LL       EE       11 11
#  SSS     PP    PP    II    NNN   NN DD    DD LL       EEEEE       11
#     SSS  PPPPPPP     II    NN NN NN DD    DD LL       EE          11
# SS    SS PP          II    NN  NNNN DD    DD LL       EE          11
#  SSSSSS  PP       IIIIIIII NN    NN DDDDDDD  LLLLLLLL EEEEEEEE 11111111
# ********************************************************************

#######################################################################
# Sp1_Set_Idx_Dist
# Purpose:              This is used to set the rotational distance
#                           (degrees) for the Sp1 spindle (the
#                           rosette phaser/multiplier).
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp1_Idx (on setting the value)
#   Signal:             GtkSpinButton/value-changed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       Sp1_Idx
#   Program Variables
#       Referenced:     (none)
#       Set:            self.Sp1_Idx_Dist
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def Sp1_Set_Idx_Dist(self,widget):

        print("=================================================")
        print("FUNCTION Sp1_Set_Idx_Dist")

        self.Sp1_Idx_Dist = widget.get_value()

#######################################################################
# Sp1_Set_Idx_OnOff
# Purpose:              This is used to set the use of Sp1 indexing
#                           on or off.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp1_Set_Idx_OnOff
#   Signal:             GtkToggleButton/toggled
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            self.Sp1_Idx_Bool
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        (none)
#######################################################################
    def Sp1_Set_Idx_OnOff(self,widget):

        idx_log("=================================================")
        idx_log("FUNCTION Sp1_Set_Idx_OnOff")

        # See Sp0_Set_Idx_OnOff for why this reads the widget directly
        # instead of flipping a separately-tracked flag.
        self.Sp1_Idx_Bool = widget.get_active()
        idx_log("Sp1_Idx_Bool = " + str(self.Sp1_Idx_Bool))

#######################################################################
# Sp1_Set_Move_Pct
# Purpose:              This is used to set the speed for the rosette
#                           phaser / multiplier (Sp0) as a percentage
#                           of the spindle speed.
# Updated:              ver 1.0, 21 July 2026
# ---------------------------------------------------------------------
# Called from:
#   UI:                 Rosetta_Panel
#   Button:             Sp1_Set_Move_Pct  (Hal_SpinButton)
#   Signal:             GtkSpinButton/value-changed
# ---------------------------------------------------------------------
# Data
#   Read from UI:       (none)
#   Program Variables
#       Referenced:     (none)
#       Set:            self.Sp1_Pct
#   Written to UI:      (none)
# ---------------------------------------------------------------------
# Gcodes Called:        S
#######################################################################
    def Sp1_Set_Move_Pct(self,widget):

        print("=================================================")
        print("FUNCTION Sp1_Set_Move_Pct")

        self.Sp1_Pct = round(widget.get_value(), 2)
        print("self.Sp1_Pct = " + str(self.Sp1_Pct))
        # Restoring the saved panel at startup - don't send an S word.
        if getattr(self, "_restoring_panel", False):
            return

        # Same freeze as Sp0_Set_Feed (see that handler's comment): the
        # spinbutton arrows auto-repeat while held, and dispatching the
        # blocking c.mdi()/c.wait_complete() pair on every tick stalls the
        # GTK main loop long enough that the on-screen value looks stuck.
        # Debounce the actual dispatch instead.
        if self.Sp1_Pct_debounce_id is not None:
            GLib.source_remove(self.Sp1_Pct_debounce_id)
        self.Sp1_Pct_debounce_id = GLib.timeout_add(150, self._Sp1_Send_Pct)

    def _Sp1_Send_Pct(self):

        self.Sp1_Pct_debounce_id = None

        Sp1_Feed = round(self.Sp0_Feed * self.Sp1_Pct / 100, 2)
        Gcode1 = "S" + str(Sp1_Feed) + " $1"

        print("self.Sp0_Feed = " + str(self.Sp0_Feed))
        print("self.Sp1_Pct = " + str(self.Sp1_Pct))
        print("Sp1_Feed = " + str(Sp1_Feed))

        # Ensure the system is in MDI mode
        s.poll()
        if s.task_state != linuxcnc.MODE_MDI:
                c.mode(linuxcnc.MODE_MDI)
                c.wait_complete() # Wait for mode change to complete

        # Send an MDI command to set the spindle speed.
        print(Gcode1)
        c.mdi(Gcode1)

        # Wait for the command to complete
        c.wait_complete()

        return False  # one-shot timeout, not a repeating GLib source

#######################################################################
# Sp1_Set_Ena
# Purpose:              See B_Set_Ena - same pattern, for Sp1.
#######################################################################
    def Sp1_Set_Ena(self,widget,*args):
        _clear_ena_override('Sp1')


#######################################################################
# Sync Move tab (Rosetta_Panel_v1.ui, second of the Indexing/Sync Move tabs)
# Purpose:              Moves every checked axis letter by its own
#                       distance, in its own direction, at its own row's
#                       Feed Rate, as ONE G1 move so they all start and
#                       finish together, then lets the operator put them
#                       all back where they started. Only the main panel
#                       component has these widgets; every other
#                       component no-ops.
#                       13 November 2026 (Rich): A/B/C distances up to
#                       99,999,999.00 deg or 999,999.999 rev, shown with
#                       thousands commas; a Pause / Continue button; an
#                       optional external Pause button on a limit jack.
# Updated:              ver 1.1, 13 November 2026
#######################################################################
    def _load_sync_move_tab(self):
        '''
        One-time setup of the Sync Move tab: per-row state, and
        unit-of-measure labels for the persisted Measurement System
        (startup-only, like _load_panel_axis_controls - a Measurement
        System change needs a restart to take effect anyway). The linear
        rows' own Feed Rate/Indexing UOM labels are set here too: Sync
        Move uses each row's existing Feed Rate, so its label has to be
        right for Sync Move to be, and Rosetta_Settings.py (see its
        _apply_measurement_system_labels) no longer can - it's a
        separate program. Unassigned letters are greyed out by
        _load_panel_axis_controls (AXIS_ROW_FIELDS includes the Sync
        widgets). Also starts watching the external Pause button, if a
        limit jack is set to one.
        '''
        if self.builder.get_object("Sync_Run") is None:
            return

        self._sync_dir = {axis: None for axis in AXIS_SELECTION_LETTERS}
        self._sync_start = None      # stat().position when Run Operation last started
        self._sync_feeds = {}        # letter -> feed rate used by that Run Operation
        self._sync_target = {}       # letter -> where the current move should end
        self._sync_poll_id = None
        # A/B/C rows' Distance unit, "deg" or "rev" (Sync_Set_Unit).
        self._sync_unit = {axis: "deg" for axis in AXIS_SELECTION_LETTERS
                           if _axis_type_for_letter(axis) == "ANGULAR"}
        # Which Sync Move button's move is running: "run" (Sync Move or
        # Continue), "return", or None (nothing, or a Cut Thread, which
        # shares _start_polled_mdi but can't be paused from here).
        self._sync_kind = None
        # A Sync Move stopped before it got to its end point, which
        # Continue can finish: {"start": stat position, "target":
        # {letter: end position}, "feeds": {letter: feed}}. None once it
        # finishes or Return to Start is used.
        self._sync_resume = None
        # Something to do once the move being stopped has wound down -
        # Return to Start pressed while paused (see Sync_Return).
        self._sync_after_stop = None

        system = rosetta_settings_io.load_settings().get("measurement_system", "Imperial")
        self._sync_metric = system == "Metric"

        for axis in AXIS_SELECTION_LETTERS:
            if _axis_type_for_letter(axis) == "ANGULAR":
                continue
            dist_uom = "mm" if self._sync_metric else "in"
            self.builder.get_object(axis + "_Sync_Dist_UOM").set_text(dist_uom)
            self.builder.get_object(axis + "_IdxDist_UOM").set_text(dist_uom)
            self.builder.get_object(axis + "_Feed_UOM").set_text(dist_uom + " / min")
        for axis in self._sync_unit:
            self._sync_apply_unit(axis, "deg")

        self._pause_jack = self._read_pause_jack()
        self._pause_button_was_pressed = False
        if self._pause_jack is not None:
            print("External Pause button on limit jack " + self._pause_jack)
            GLib.timeout_add(PROGRAM_POLL_MS, self._poll_pause_button)
        self._sync_update_pause_button()

    def Panel_Mode_Switch(self, notebook, page, page_num):
        '''
        Indexing (page 0) / Sync Move (page 1) / Threading (page 2) tab
        switch. The tabs' own pages are empty: Indexing's and Sync
        Move's widgets live directly in MainGrid's columns 10-13, one
        GtkStack per cell, so every row stays aligned with its
        letter/ENA/Feed Rate/Device - and since a GtkStack always sizes
        to its larger page, nothing moves or resizes when switching.
        Only SYNC_TAB_ONLY_WIDGETS (no Indexing counterpart) are
        shown/hidden outright.

        Threading isn't per-row, so it's one form (Thread_Form) laid over
        the same columns. Under it, the stacks and MODE_HEADER_WIDGETS
        are unmapped with set_child_visible(False) rather than hidden:
        that keeps their size request, so MainGrid's columns - and the
        whole panel - stay exactly the same size on all three tabs
        (hiding them, or switching the stacks to an empty page, lets
        GtkGrid redistribute the spanning tab strip's width differently
        and the panel shifts a few pixels).
        '''
        print("=================================================")
        print("FUNCTION Panel_Mode_Switch, page " + str(page_num))
        grid = self.builder.get_object("MainGrid")
        if grid is None or self.builder.get_object("Sync_Run") is None:
            return
        threading = page_num == PANEL_MODE_THREAD_PAGE
        for child in grid.get_children():
            if (Gtk.Buildable.get_name(child) or "").startswith(PANEL_MODE_STACK_PREFIX):
                if not threading:
                    child.set_visible_child_name(PANEL_MODE_STACK_PAGE[page_num])
                child.set_child_visible(not threading)
        for wid in MODE_HEADER_WIDGETS:
            self.builder.get_object(wid).set_child_visible(not threading)
        for wid in SYNC_TAB_ONLY_WIDGETS:
            self.builder.get_object(wid).set_visible(page_num == 1)
        self.builder.get_object("Thread_Form").set_visible(threading)

    def Sync_Set_Dir(self, widget):
        '''
        Rev/Fwd pick for one row - radio-style: selecting one deselects
        the other. Shown with _set_depressed rather than a
        GtkToggleButton's own "checked" look, for the same visibility
        reason given at _DEPRESS_CSS.
        '''
        axis, _, direction = Gtk.Buildable.get_name(widget).split("_")
        self._sync_dir[axis] = direction
        for d in SYNC_DIR_SIGN:
            _set_depressed(self.builder.get_object(axis + "_Sync_" + d), d == direction)

    # -----------------------------------------------------------------
    # A/B/C Distance: thousands commas, deg / rev (13 November 2026)
    #
    # GTK's spin button has no thousands separator, so the A/B/C
    # Distance boxes draw their own ("output", Sync_Dist_Output) and
    # have numeric off so a comma can be typed. GTK reads the typed text
    # with its own parser, which stops at a comma ("1,000" would be 1),
    # and PyGObject can't hand a value back from the "input" signal
    # (tried 13 November 2026: TypeError, or a GLib warning), so instead
    # the commas are taken out just before GTK reads the box - on Enter,
    # on a click of its +/- arrows, on leaving it (when that event comes -
    # it doesn't always arrive inside AXIS's embedded panels),
    # and before Sync Move reads it (_sync_read_spin).
    # -----------------------------------------------------------------
    @staticmethod
    def _strip_commas(spin):
        text = spin.get_text()
        if "," in text:
            spin.set_text(text.replace(",", ""))

    def Sync_Dist_Strip_Commas(self, spin, *args):
        self._strip_commas(spin)
        return False     # let GTK go on to read the box as usual

    def Sync_Dist_Output(self, spin):
        spin.set_text("{:,.{d}f}".format(spin.get_adjustment().get_value(), d=spin.get_digits()))
        return True

    def _sync_read_spin(self, spin):
        '''
        A Sync Distance (or Feed Rate) box's value, after committing
        anything typed but not yet Enter'd, rounded to the decimals the
        box shows - so the number sent is the number on screen.
        '''
        self._strip_commas(spin)
        spin.update()
        return _round_half_up(spin.get_value(), spin.get_digits())

    def _sync_apply_unit(self, axis, unit):
        '''
        Sets an A/B/C row's Distance box for deg or rev: decimals, step
        and largest value. The number stays as it is (Rich: 40 then rev
        means 40 rev), except that it's rounded to the new decimals and
        lowered to the new largest value if it's over it.
        '''
        digits, step, upper, _ = SYNC_ANGULAR_UNITS[unit]
        spin = self.builder.get_object(axis + "_Sync_Dist")
        self._strip_commas(spin)
        spin.update()
        value = spin.get_value()
        adj = spin.get_adjustment()
        adj.set_upper(upper)
        adj.set_step_increment(step)
        adj.set_page_increment(step * 10)
        spin.set_digits(digits)
        spin.set_value(_round_half_up(min(value, upper), digits))
        self._sync_unit[axis] = unit
        # set_value doesn't redraw an unchanged value in the new decimals.
        self.Sync_Dist_Output(spin)

    def Sync_Set_Unit(self, widget):
        '''deg / rev radios on an A/B/C row (<letter>_Sync_Unit_Deg/_Rev).'''
        if not widget.get_active():
            return      # the radio being switched off - its partner does the work
        axis = Gtk.Buildable.get_name(widget)[0]
        unit = "rev" if Gtk.Buildable.get_name(widget).endswith("_Rev") else "deg"
        if self._sync_unit.get(axis) != unit:
            self._sync_apply_unit(axis, unit)

    # -----------------------------------------------------------------
    # External Pause button (13 November 2026)
    # -----------------------------------------------------------------
    @staticmethod
    def _read_pause_jack():
        '''
        The limit jack set to "Pause button" in Rosetta Settings, or None.
        Jacks 4-6 count only with the expansion box connected - the
        same rule Rosetta_Generate_Local_Ini.py wires them by.
        '''
        settings = rosetta_settings_io.load_settings()
        expansion = settings.get("expansion_box") is True
        for jack, value in sorted(settings.get("limit_switches", {}).items()):
            if value == PAUSE_JACK_VALUE and (expansion or jack not in ("4", "5", "6")):
                return jack
        return None

    def _pause_button_pressed(self):
        '''
        True while the external Pause button reads pressed - which an NC
        button also does when its wire is broken or unplugged, or a
        button doesn't match Rosetta Settings' Limit Switch Type.
        '''
        if self._pause_jack is None:
            return False
        try:
            return bool(hal.get_value(PAUSE_BUTTON_SIGNAL))
        except Exception:
            return False

    def _refuse_if_pause_pressed(self, widget):
        if not self._pause_button_pressed():
            return False
        _show_settings_error(widget, "The Pause button is pressed or disconnected.  Release it, "
                             "or check its plug and wiring, then try again.")
        return True

    def _poll_pause_button(self):
        '''
        Watches the external Pause button. Pressing it pauses a Sync
        Move or a G-code program (AXIS's Resume, or the panel's
        Continue, carries on); it never resumes anything - the jacks
        have no debounce filter (num_inms=0), so a bounce mustn't undo
        the pause, and continuing should be done at the screen. Cut
        Thread and indexing aren't paused (Rich, 13 November 2026).
        '''
        pressed = self._pause_button_pressed()
        if pressed and not self._pause_button_was_pressed:
            s.poll()
            if self._sync_poll_id is not None and self._sync_kind is not None:
                if s.interp_state != linuxcnc.INTERP_PAUSED:
                    print("External Pause button: pausing the Sync Move")
                    self._sync_pause()
            elif s.task_mode == linuxcnc.MODE_AUTO and s.interp_state in (
                    linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING):
                print("External Pause button: pausing the program")
                c.auto(linuxcnc.AUTO_PAUSE)
        self._pause_button_was_pressed = pressed
        return True

    # -----------------------------------------------------------------
    # Pause / Continue (13 November 2026)
    #
    # One button (Sync_Pause) between Sync Move and Return to Start:
    #   - while a Sync Move or Return to Start runs: "Pause" - a feed
    #     hold, so the axes slow down and stop where they are;
    #   - while paused: "Continue" - resumes the move; Return to Start
    #     works too (it ends the paused move, then goes back);
    #   - after a Sync Move that was stopped part way (E-stop, machine
    #     off, AXIS's Stop - e.g. to fix a broken belt): "Continue" -
    #     sends the rest of the move from where the axes are, at the
    #     same speed, along the same line (asking first if an axis was
    #     moved off that line meanwhile);
    #   - while a G-code program is paused (AXIS's Pause, M0/M1, the
    #     external Pause button): "Continue" - resumes it, like AXIS's
    #     Resume (Rich, 13 November 2026).
    # Silent, and doesn't touch the spindles (the cutter isn't
    # Rosetta-controlled). Cut Thread can't be paused from here.
    # -----------------------------------------------------------------
    def _sync_update_pause_button(self):
        button = self.builder.get_object("Sync_Pause")
        if button is None:
            return
        busy = self._sync_poll_id is not None
        ours = busy and self._sync_kind is not None
        paused = ours and s.interp_state == linuxcnc.INTERP_PAUSED
        if paused or self._program_paused() or (not busy and self._sync_resume is not None):
            label, sensitive = "Continue", True
        else:
            label, sensitive = "Pause", ours
        if button.get_label() != label:
            button.set_label(label)
        if button.get_sensitive() != sensitive:
            button.set_sensitive(sensitive)
        # Return to Start is one of MOTION_BUTTONS (off while anything
        # moves) but works while a Sync Move is paused.
        if busy:
            ret = self.builder.get_object("Sync_Return")
            if ret.get_sensitive() != paused:
                ret.set_sensitive(paused)

    def _program_paused(self):
        '''
        A G-code program (AXIS's Run) is paused - by AXIS's Pause, an M0/M1,
        or the external Pause button. Continue resumes it too (Rich, 13
        November 2026), the same as AXIS's Resume. Kept up to date by
        _poll_program.
        '''
        return (self._sync_poll_id is None and s.task_mode == linuxcnc.MODE_AUTO
                and s.interp_state == linuxcnc.INTERP_PAUSED)

    def Sync_Pause(self, widget):
        print("=================================================")
        print("FUNCTION Sync_Pause (" + widget.get_label() + ")")
        s.poll()
        if self._program_paused():
            if not self._refuse_if_pause_pressed(widget):
                print("Continue: resuming the paused program")
                c.auto(linuxcnc.AUTO_RESUME)
            self._sync_update_pause_button()
            return
        if self._sync_poll_id is not None:
            if self._sync_kind is None:
                return
            if s.interp_state == linuxcnc.INTERP_PAUSED:
                if self._refuse_if_pause_pressed(widget):
                    return
                c.auto(linuxcnc.AUTO_RESUME)
            else:
                self._sync_pause()
        elif self._sync_resume is not None:
            self._sync_continue(widget)
        self._sync_update_pause_button()

    def _sync_pause(self):
        c.auto(linuxcnc.AUTO_PAUSE)
        GLib.timeout_add(SYNC_PAUSE_CHECK_MS, self._sync_check_paused)

    def _sync_check_paused(self):
        '''
        If LinuxCNC didn't pause the move (still moving, not paused),
        stops it instead - it slows to a stop the same way - and
        Continue then sends the rest as a new move.
        '''
        s.poll()
        if self._sync_poll_id is not None and self._sync_kind is not None \
                and s.interp_state not in (linuxcnc.INTERP_PAUSED, linuxcnc.INTERP_IDLE):
            print("Sync Move didn't pause - stopping it instead")
            c.abort()
        return False

    def _sync_line_problem(self, resume):
        '''
        For Continue: (fraction of the move done, axes no longer on the
        move's straight line). The fraction comes from the axis with the
        longest move (the most exact); any other axis further than
        SYNC_LINE_TOLERANCE from where that fraction puts it - or the
        lead axis being outside the move - was moved while stopped.
        '''
        start, target = resume["start"], resume["target"]
        total = {axis: end - start[STAT_POSITION_INDEX[axis]] for axis, end in target.items()}
        lead = max(total, key=lambda axis: abs(total[axis]))
        done = (s.position[STAT_POSITION_INDEX[lead]] - start[STAT_POSITION_INDEX[lead]]) / total[lead]
        moved = []
        for axis, length in total.items():
            i = STAT_POSITION_INDEX[axis]
            if abs(start[i] + done * length - s.position[i]) > SYNC_LINE_TOLERANCE:
                moved.append(axis)
        if (done < -1e-9 or done > 1 + 1e-9) and lead not in moved:
            moved.append(lead)
        return max(0.0, min(done, 1.0)), moved

    def _sync_continue(self, widget):
        '''
        Finishes a Sync Move that was stopped part way: one move from
        where the axes are now to the original end point, at the same
        feed rates - so, from a point on the original line, the same
        path at the same speed.
        '''
        resume = self._sync_resume
        if not self._sync_ready_to_move(widget) or self._refuse_if_pause_pressed(widget):
            return
        deltas = {}
        for axis, end in resume["target"].items():
            delta = end - s.position[STAT_POSITION_INDEX[axis]]
            if abs(delta) >= SYNC_POSITION_TOLERANCE:
                deltas[axis] = delta
        if not deltas:
            self._sync_resume = None
            _show_settings_error(widget, "Already at the Sync Move's end point.")
            return
        done, moved = self._sync_line_problem(resume)
        if moved and not self._sync_confirm_off_line(widget, moved):
            return
        if not _confirm_roles_enabled(widget, list(deltas)):
            return
        total = {axis: end - resume["start"][STAT_POSITION_INDEX[axis]]
                 for axis, end in resume["target"].items()}
        length = _planner_length(total)
        progress = self._mdi_progress_start("Sync Move", length=length)
        if progress is not None and not moved:
            # Count what was done before the stop, so the bar picks up
            # where it left off.
            progress["start"] -= done * length
        self._sync_kind = "run"
        self._sync_start_move(self.builder.get_object("Sync_Run"), deltas,
                              resume["feeds"], self._sync_run_finished, progress)

    @staticmethod
    def _sync_confirm_off_line(widget, moved):
        names = _names(moved)
        one = len(moved) == 1
        dialog = Gtk.MessageDialog(
            transient_for=widget.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=names + (" was" if one else " were") + " moved while the Sync Move was stopped",
        )
        dialog.format_secondary_text(
            "Continue Anyway goes straight from where the axes are now to the Sync Move's "
            "end point - not the path it was on.  Return to Start goes back to where the "
            "Sync Move started.  Cancel moves nothing.")
        dialog.add_button("Continue Anyway", Gtk.ResponseType.ACCEPT)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        answer = dialog.run()
        dialog.destroy()
        return answer == Gtk.ResponseType.ACCEPT

    def _sync_ready_to_move(self, widget):
        '''
        Common Run Operation/Return to Start precondition: machine on
        and nothing else (a program, an MDI command, a previous Sync
        move) currently running.
        '''
        s.poll()
        if s.task_state != linuxcnc.STATE_ON:
            _show_settings_error(widget, "The machine must be turned on first.")
            return False
        if self._sync_poll_id is not None or s.interp_state != linuxcnc.INTERP_IDLE:
            _show_settings_error(widget, "Wait for the current motion to finish first.")
            return False
        return True

    def _sync_start_move(self, widget, deltas, feeds, on_done=None, progress=None):
        '''
        Sends deltas ({letter: signed incremental distance, in machine
        units}) as a single G1. Each letter's own time is
        |distance| / feed; the move is timed to the slowest of those via
        inverse-time feed (G93, F = 1/minutes), so every axis starts and
        stops together and none goes faster than the feed rate it was
        given. Units (G20/G21), distance mode, feed mode and radius mode are forced
        for this one move and the operator's previous modal state is put
        back afterwards, along with its modal F (see _sync_poll_move).
        '''
        minutes = max(abs(d) / feeds[axis] for axis, d in deltas.items())
        words = " ".join("%s%.4f" % (axis, d) for axis, d in deltas.items())
        # G8 too (08 November 2026, found with GitHub issue #24): a
        # program that leaves diameter mode (G7) on would otherwise halve
        # every X move, and Return's deltas come from radius positions.
        gcode = (("G21" if self._sync_metric else "G20") + " G91 G93 G8 G1 " + words
                 + " F" + _gcode_number(1.0 / minutes))
        # Where each axis should end up - see _sync_run_finished.
        self._sync_target = {axis: s.position[STAT_POSITION_INDEX[axis]] + d
                             for axis, d in deltas.items()}
        self._start_polled_mdi(widget, gcode, on_done, progress)

    def _start_polled_mdi(self, widget, gcode, on_done=None, progress=None):
        '''
        Sends one MDI command (a single move, or a whole subroutine
        call) and polls until it finishes, with every MOTION_BUTTONS
        button disabled meanwhile, then puts back the operator's own
        units, distance mode, feed mode, lathe radius/diameter mode and
        modal F - whichever of those the command changed - and calls
        on_done(), if given. Shared by the Sync Move and Threading tabs.
        progress, if given, puts the command on the progress bar - see
        _mdi_progress_start.
        '''
        self._mdi_progress = progress
        self._clear_splash()
        modal = set(s.gcodes)
        restore = []
        restore.append("G21" if 210 in modal else "G20")
        restore.append("G91" if 910 in modal else "G90")
        restore.append("G93" if 930 in modal else "G95" if 950 in modal else "G94")
        restore.append("G7" if 70 in modal else "G8")
        # The move's own inverse-time F would otherwise stay behind as
        # the modal feed rate once G94 is back in effect.
        restore.append("F%.4f" % s.settings[1])

        if s.task_mode != linuxcnc.MODE_MDI:
            c.mode(linuxcnc.MODE_MDI)
            c.wait_complete()
        print(gcode)
        c.mdi(gcode)

        for wid in MOTION_BUTTONS:
            self.builder.get_object(wid).set_sensitive(False)
        _set_depressed(widget, True)
        # Polled rather than c.wait_complete()'d, so the tab (and AXIS's
        # own Stop/ESC) stays responsive for however long the move takes.
        self._sync_poll_id = GLib.timeout_add(
            100, self._sync_poll_move, widget, " ".join(restore), time.time(), on_done)
        self._sync_update_pause_button()

    @staticmethod
    def _clear_splash():
        '''
        If AXIS still shows the startup splash, has it open the empty
        Rosetta_Splash.ngc instead (axis-remote - AXIS is a separate process),
        so a Sync Move's or Cut Thread's tool path isn't drawn over the
        lettering (Rich, 20 October 2026). A G-code program needs nothing:
        opening it replaces the splash. Done before switching to MDI,
        since AXIS refuses remote commands while anything runs.
        '''
        if os.path.basename(s.file or "") != SPLASH_FILE_NAME:
            return
        try:
            subprocess.run(["axis-remote", EMPTY_PREVIEW_FILE], timeout=5,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as e:
            print("Could not clear the splash: " + str(e))
        s.poll()

    def _sync_poll_move(self, widget, restore_gcode, started, on_done=None):
        s.poll()
        # interp_state can still read idle for a moment right after
        # c.mdi() - don't mistake that for "already finished".
        if s.interp_state != linuxcnc.INTERP_IDLE or time.time() - started < 0.5:
            self._mdi_progress_update()
            self._sync_update_pause_button()
            return True
        # Finished, or aborted from AXIS - either way, put the
        # operator's own modal state back.
        if s.task_state == linuxcnc.STATE_ON:
            c.mdi(restore_gcode)
            c.wait_complete()
        print("Sync/Threading move done, restored: " + restore_gcode)
        _set_depressed(widget, False)
        for wid in MOTION_BUTTONS:
            self.builder.get_object(wid).set_sensitive(True)
        self._sync_poll_id = None
        if on_done is not None:
            on_done()
        self._sync_kind = None
        self._sync_update_pause_button()
        after, self._sync_after_stop = self._sync_after_stop, None
        if after is not None:
            GLib.idle_add(after)
        return False

    def Sync_Run(self, widget):
        print("=================================================")
        print("FUNCTION Sync_Run")
        deltas = {}
        feeds = {}
        for axis in AXIS_SELECTION_LETTERS:
            if axis not in _ACTIVE_ROLES_AT_STARTUP:
                continue
            if not self.builder.get_object(axis + "_Sync_Use").get_active():
                continue
            # The row's own (Indexing tab's) Feed Rate.
            feed_spin = self.builder.get_object(axis + "_Feed")
            # Commits anything typed but not yet Enter'd/tabbed out of.
            distance = self._sync_read_spin(self.builder.get_object(axis + "_Sync_Dist"))
            feed_spin.update()
            feed = feed_spin.get_value()
            if self._sync_dir[axis] is None:
                _show_settings_error(widget, "Select a direction for " + axis + ".")
                return
            if distance <= 0:
                _show_settings_error(widget, "Enter a distance for " + axis + ".")
                return
            if feed <= 0:
                _show_settings_error(widget, "Enter a feed rate for " + axis + ".")
                return
            if axis in self._sync_unit:
                # rev -> degrees.
                distance *= SYNC_ANGULAR_UNITS[self._sync_unit[axis]][3]
            deltas[axis] = -distance if SYNC_DIR_SIGN[self._sync_dir[axis]] == "-" else distance
            feeds[axis] = feed

        if not deltas:
            _show_settings_error(widget, "Check \"Use\" for at least one axis.")
            return
        if not self._sync_ready_to_move(widget) or self._refuse_if_pause_pressed(widget):
            return
        if not _confirm_roles_enabled(widget, list(deltas)):
            return

        self._sync_start = tuple(s.position)
        self._sync_feeds = feeds
        self._sync_kind = "run"
        self._sync_start_move(widget, deltas, feeds, self._sync_run_finished,
                              self._mdi_progress_start("Sync Move", length=_planner_length(deltas)))
        # Continue's record of this move (its end points were just
        # worked out by _sync_start_move).
        self._sync_resume = {"start": self._sync_start, "target": dict(self._sync_target),
                             "feeds": dict(feeds)}
        self._sync_update_pause_button()

    def _sync_run_finished(self):
        '''
        A Sync Move's move (or Continue's) is over. Beeps only if every
        axis actually got where it was going - a move stopped from AXIS
        part way (or by E-stop) stays silent and can be continued.
        '''
        s.poll()
        finished = (s.task_state == linuxcnc.STATE_ON
                    and all(abs(s.position[STAT_POSITION_INDEX[axis]] - end) < SYNC_POSITION_TOLERANCE
                            for axis, end in self._sync_target.items()))
        self._mdi_progress_end(finished)
        if finished:
            self._sync_resume = None
            self._play_sound(DONE_BEEPS)

    def Sync_Return(self, widget):
        '''
        Moves every axis the last Run Operation used back to where it
        was when that Run Operation started, at the same feed rates -
        computed from where each axis actually is now, so this is still
        correct after a Run Operation that was stopped part way. Pressed
        while a Sync Move is paused, it first ends that move (AXIS's
        Stop does the same), then returns once it has wound down.
        '''
        print("=================================================")
        print("FUNCTION Sync_Return")
        if self._sync_start is None:
            _show_settings_error(widget, "Nothing to return from - use Sync Move first.")
            return
        s.poll()
        if self._sync_poll_id is not None and self._sync_kind is not None \
                and s.interp_state == linuxcnc.INTERP_PAUSED:
            if self._refuse_if_pause_pressed(widget):
                return
            print("Return to Start while paused: stopping the paused move first")
            self._sync_after_stop = lambda: self.Sync_Return(widget) and False
            c.abort()
            return
        if not self._sync_ready_to_move(widget) or self._refuse_if_pause_pressed(widget):
            return

        deltas = {}
        for axis in self._sync_feeds:
            i = STAT_POSITION_INDEX[axis]
            delta = self._sync_start[i] - s.position[i]
            if abs(delta) >= SYNC_POSITION_TOLERANCE:
                deltas[axis] = delta
        if not deltas:
            self._sync_resume = None
            self._sync_update_pause_button()
            _show_settings_error(widget, "Already at the starting point.")
            return
        if not _confirm_roles_enabled(widget, list(deltas)):
            return

        # Going back abandons the stopped Sync Move - nothing to continue.
        self._sync_resume = None
        self._sync_kind = "return"
        self._sync_start_move(widget, deltas, self._sync_feeds)


#######################################################################
# Threading tab (Rosetta_Panel_v1.ui, third of the Indexing/Sync Move/
# Threading tabs)
# Purpose:              Cuts a single- or multi-start thread with a
#                       cutter held in the drilling spindle: X feeds the
#                       cutter in, Z and C move together along the thread
#                       (a helix), each start is cut to full depth, then
#                       C indexes 360 / starts degrees to the next. Based
#                       on Rich's Threading.xlsx, which planned this as a
#                       G76 - Rosetta_Subroutines/rosetta_thread.ngc cuts the same
#                       passes G76 would (J, then J deeper each pass, K,
#                       then H spring passes, from I clearance), but as
#                       coordinated Z+C moves, since G76 syncs Z to
#                       spindle.0 (which isn't what turns the work here)
#                       and waits on an index pulse this machine has no
#                       source for. Only the main panel component has
#                       these widgets; every other component no-ops.
# Updated:              ver 1.0, 24 September 2026
#######################################################################
    def _load_threading_tab(self):
        '''
        One-time setup of the Threading tab: Measurement System labels
        (Threads / inch for Imperial, Pitch in mm for Metric - startup-
        only, like _load_sync_move_tab), default values, and the
        calculated fields.
        '''
        if self.builder.get_object("Thread_Run") is None:
            return

        self._thread_start = None     # stat().position when Cut Thread last started
        self._thread_metric = self._sync_metric
        self._thread_running = False  # a Cut Thread is in progress - show its progress
        self._thread_last_code = 0    # last progress code seen from rosetta_thread.ngc
        self._thread_result_id = None # pending GLib timeout putting the instructions back
        instructions = self.builder.get_object("Thread_Instructions")
        self._thread_instructions = instructions.get_text()

        # rosetta_thread.ngc's progress, via motion.analog-out-00 (net
        # thread-status in Rosetta_PostGUI_v1.hal) - see _on_thread_status.
        self._thread_status_pin = hal_glib.GPin(
            self.halcomp.newpin("thread-status", hal.HAL_FLOAT, hal.HAL_IN)
        )
        self._thread_status_pin.connect('value-changed', self._on_thread_status)

        uom = "mm" if self._thread_metric else "in"
        for wid in ("Thread_Length_UOM", "Thread_Clearance_UOM", "Thread_First_Depth_UOM",
                    "Thread_Final_Depth_UOM", "Thread_Max_Depth_UOM"):
            self.builder.get_object(wid).set_text(uom)
        self.builder.get_object("Thread_Lead_UOM").set_text(uom + " / rev")
        if self._thread_metric:
            self.builder.get_object("Thread_TPI_Label").set_text("Pitch")
            self.builder.get_object("Thread_TPI_UOM").set_text("mm")

        defaults = THREAD_DEFAULTS["Metric" if self._thread_metric else "Imperial"]
        for wid, value in defaults.items():
            self.builder.get_object(wid).set_value(value)
        # set_value above fires Thread_Pitch_Changed, but only for values
        # that actually changed - make sure Final depth and the
        # calculated fields are filled in regardless.
        self.Thread_Pitch_Changed(None)

    def _panel_state(self):
        '''
        Snapshot of the main panel's operator-entered values - Indexing
        (Feed Rate, Index Distance, Deg/Div per axis; spindle speed, Sp1 %,
        Sp0/Sp1 index checkboxes), Sync Move (selected, distance,
        direction per axis, and deg / rev for A/B/C) and Threading (every field) - saved to
        RosettaSet_v1.ini's "panel_state" and put back at the next start
        (_restore_panel_state). ENA states are deliberately not saved:
        every axis starts disabled.
        '''
        b = self.builder.get_object
        state = {"measurement_system": "Metric" if self._sync_metric else "Imperial", "axes": {}}
        for axis in AXIS_SELECTION_LETTERS:
            state["axes"][axis] = {
                "feed": b(axis + "_Feed").get_value(),
                "idx_dist": b(axis + "_Idx_Dist").get_value(),
                "idx_degdiv": getattr(self, axis + "_Idx_DegDiv"),
                "sync_use": b(axis + "_Sync_Use").get_active(),
                "sync_dist": b(axis + "_Sync_Dist").get_value(),
                "sync_dir": self._sync_dir.get(axis),
            }
            if axis in self._sync_unit:
                # deg / rev (13 November 2026).
                state["axes"][axis]["sync_unit"] = self._sync_unit[axis]
        state["Sp0"] = {"feed": b("Sp0_Set_Feed").get_value(),
                        "idx_dist": b("Sp0_Idx_Dist").get_value(),
                        "idx_degdiv": self.Sp0_Idx_DegDiv,
                        "idx_on": b("Sp0_Set_Idx_OnOff").get_active()}
        state["Sp1"] = {"pct": b("Sp1_Set_Move_Pct").get_value(),
                        "idx_on": b("Sp1_Set_Idx_OnOff").get_active()}
        thread = {wid: b(wid).get_value() for wid in THREAD_SAVED_SPINS + ("Thread_Final_Depth",)}
        thread.update({wid: b(wid).get_active_text() for wid in THREAD_SAVED_COMBOS})
        state["threading"] = thread
        return state

    def _restore_panel_state(self):
        '''
        Puts back the values _panel_state saved last session. Run once
        from GLib.idle_add, after the panel is up and its signals are
        connected, so every widget is set the same way an operator would
        set it - with _restoring_panel stopping Sp0_Set_Feed/
        Sp1_Set_Move_Pct from sending S words, and the handler-held
        copies (<axis>_Feed, Sp0_Idx_Deg, _sync_dir, ...) set explicitly
        afterwards so they always match what's on screen. Inch/mm
        values are skipped if the Measurement System has changed since
        they were saved. Then starts the once-a-second autosave.
        '''
        saved = rosetta_settings_io.load_settings().get("panel_state", {})
        same_units = saved.get("measurement_system") == ("Metric" if self._sync_metric else "Imperial")
        b = self.builder.get_object
        self._restoring_panel = True
        try:
            for axis, row in saved.get("axes", {}).items():
                if axis not in AXIS_SELECTION_LETTERS:
                    continue
                linear = _axis_type_for_letter(axis) == "LINEAR"
                # deg / rev before the distance, so the box has the
                # right decimals and largest value when it's set.
                if row.get("sync_unit") in SYNC_ANGULAR_UNITS and axis in self._sync_unit:
                    b(axis + ("_Sync_Unit_Rev" if row["sync_unit"] == "rev" else "_Sync_Unit_Deg")).set_active(True)
                if same_units or not linear:
                    for wid, key in (("_Feed", "feed"), ("_Idx_Dist", "idx_dist"), ("_Sync_Dist", "sync_dist")):
                        if key in row:
                            b(axis + wid).set_value(row[key])
                if "sync_use" in row:
                    b(axis + "_Sync_Use").set_active(bool(row["sync_use"]))
                degdiv = row.get("idx_degdiv", "Deg")
                if not linear and degdiv in ("Deg", "Div"):
                    b(axis + ("_Idx_Div" if degdiv == "Div" else "_Idx_Deg")).set_active(True)
                    setattr(self, axis + "_Idx_DegDiv", degdiv)
                direction = row.get("sync_dir")
                if direction in SYNC_DIR_SIGN:
                    self._sync_dir[axis] = direction
                    for d in SYNC_DIR_SIGN:
                        _set_depressed(b(axis + "_Sync_" + d), d == direction)
                # What the Set_Feed/Set_Idx_Dist/Set_Idx_DegDiv handlers
                # would hold for these on-screen values.
                setattr(self, axis + "_Feed", round(b(axis + "_Feed").get_value(), 1))
                dist = b(axis + "_Idx_Dist").get_value()
                setattr(self, axis + "_Idx_Dist", dist)
                if not linear:
                    deg = 360 / dist if getattr(self, axis + "_Idx_DegDiv") == "Div" and dist else dist
                    setattr(self, axis + "_Idx_Deg", round(deg, 1))

            sp0 = saved.get("Sp0", {})
            if "feed" in sp0:
                b("Sp0_Set_Feed").set_value(sp0["feed"])
            if "idx_dist" in sp0:
                b("Sp0_Idx_Dist").set_value(sp0["idx_dist"])
            if sp0.get("idx_degdiv") in ("Deg", "Div"):
                b("Sp0_Set_Idx_bW_" + sp0["idx_degdiv"]).set_active(True)
                self.Sp0_Idx_DegDiv = sp0["idx_degdiv"]
            if "idx_on" in sp0:
                self._set_checkbox_active("Sp0_Set_Idx_OnOff", bool(sp0["idx_on"]))
                self.Sp0_Idx_Bool = bool(sp0["idx_on"])
            sp1 = saved.get("Sp1", {})
            if "pct" in sp1:
                b("Sp1_Set_Move_Pct").set_value(sp1["pct"])
            if "idx_on" in sp1:
                self._set_checkbox_active("Sp1_Set_Idx_OnOff", bool(sp1["idx_on"]))
                self.Sp1_Idx_Bool = bool(sp1["idx_on"])
            self.Sp0_Feed = round(b("Sp0_Set_Feed").get_value(), 1)
            self.Sp1_Pct = b("Sp1_Set_Move_Pct").get_value()
            self.Sp0_Idx_Dist = round(b("Sp0_Idx_Dist").get_value(), 1)
            self.Sp0_Idx_Deg = round(360 / self.Sp0_Idx_Dist, 1) \
                if self.Sp0_Idx_DegDiv == "Div" and self.Sp0_Idx_Dist else self.Sp0_Idx_Dist

            thread = saved.get("threading", {})
            for wid in THREAD_SAVED_SPINS:
                if wid in thread and (same_units or wid not in THREAD_UNIT_FIELDS):
                    b(wid).set_value(thread[wid])
            for wid in THREAD_SAVED_COMBOS:
                combo = b(wid)
                texts = [row[0] for row in combo.get_model()]
                if thread.get(wid) in texts:
                    combo.set_active(texts.index(thread[wid]))
            # Final depth last: changing Starts/TPI/angle above resets it
            # to the new maximum (Thread_Pitch_Changed).
            if same_units and "Thread_Final_Depth" in thread:
                b("Thread_Final_Depth").set_value(thread["Thread_Final_Depth"])
            self.Thread_Recalc(None)
        finally:
            self._restoring_panel = False

        self._last_saved_panel_state = self._panel_state()
        GLib.timeout_add(1000, self._autosave_panel_state)
        return False

    def _autosave_panel_state(self):
        '''
        Once a second: saves _panel_state to RosettaSet_v1.ini whenever it
        differs from what was last saved (same approach as
        _autosave_axis_comments).
        '''
        state = self._panel_state()
        if state != self._last_saved_panel_state:
            settings = rosetta_settings_io.load_settings()
            settings["panel_state"] = state
            rosetta_settings_io.save_settings(settings)
            self._last_saved_panel_state = state
        return True

    def _thread_value(self, wid):
        spin = self.builder.get_object(wid)
        # Commit anything typed but not yet Enter'd/tabbed out of.
        spin.update()
        return spin.get_value()

    def _thread_geometry(self):
        '''
        (pitch, lead, max depth) from the current Starts, Threads / inch
        (or Pitch) and Thread angle, or None while any is unusable.
        Pitch is the distance between neighbouring threads (1 / TPI);
        lead is how far one thread advances per turn of the work, pitch
        x starts - what G76 calls P. Max depth is the sharp-V depth for
        this pitch and angle, from the pitch, not the lead: a multi-start
        thread's grooves are only one pitch apart.
        '''
        starts = int(self._thread_value("Thread_Starts"))
        tpi = self._thread_value("Thread_TPI")
        angle = self._thread_value("Thread_Angle")
        if starts < 1 or tpi <= 0 or not 0 < angle < 180:
            return None
        pitch = tpi if self._thread_metric else 1.0 / tpi
        return pitch, pitch * starts, (pitch / 2.0) / math.tan(math.radians(angle / 2.0))

    def _thread_passes_per_start(self):
        '''
        How many passes rosetta_thread.ngc makes per start, including spring
        passes, or None while First cut / Final depth are unusable.
        '''
        first = self._thread_value("Thread_First_Depth")
        final = self._thread_value("Thread_Final_Depth")
        if first <= 0 or final <= 0:
            return None
        # Passes at first, 2 x first, ... while short of final, then one
        # at final - the small allowance keeps a final depth that's an
        # exact multiple of first from counting one pass too many.
        return max(1, int(math.ceil(final / first - 1e-9))) + int(self._thread_value("Thread_Spring"))

    def Thread_Pitch_Changed(self, widget):
        '''
        Starts, Threads / inch (Pitch) or Thread angle changed: resets
        Final depth to the new max (as Threading.xlsx does - it can be
        changed afterwards) and updates the calculated fields.
        '''
        if self.builder.get_object("Thread_Run") is None:
            return
        geometry = self._thread_geometry()
        if geometry is not None:
            self.builder.get_object("Thread_Final_Depth").set_value(round(geometry[2], 4))
        self.Thread_Recalc(None)

    def Thread_Recalc(self, widget):
        if self.builder.get_object("Thread_Run") is None:
            return
        geometry = self._thread_geometry()
        passes = self._thread_passes_per_start()
        lead_label = self.builder.get_object("Thread_Lead")
        max_label = self.builder.get_object("Thread_Max_Depth")
        passes_label = self.builder.get_object("Thread_Passes")
        if geometry is None:
            lead_label.set_text("-")
            max_label.set_text("-")
        else:
            lead_label.set_text("%.4f" % geometry[1])
            max_label.set_text("%.4f" % geometry[2])
        if passes is None:
            passes_label.set_text("-")
        else:
            starts = int(self._thread_value("Thread_Starts"))
            passes_label.set_text("%d x %d starts" % (passes, starts) if starts > 1 else str(passes))

    def Thread_Run(self, widget):
        print("=================================================")
        print("FUNCTION Thread_Run")
        missing = [axis for axis in THREAD_AXES if axis not in _ACTIVE_ROLES_AT_STARTUP]
        if missing:
            _show_settings_error(widget, "Threading uses X, Z and C - assign "
                                 + " and ".join(missing) + " on the Axis Selection tab first.")
            return
        feeds = {}
        for axis in THREAD_AXES:
            feed_spin = self.builder.get_object(axis + "_Feed")
            feed_spin.update()
            feeds[axis] = feed_spin.get_value()
            if feeds[axis] <= 0:
                _show_settings_error(widget, "Enter a feed rate for " + axis + ".")
                return

        geometry = self._thread_geometry()
        if geometry is None:
            _show_settings_error(widget, "Enter the starts, "
                                 + ("pitch" if self._thread_metric else "threads / inch")
                                 + " and thread angle.")
            return
        pitch, lead, max_depth = geometry
        starts = int(self._thread_value("Thread_Starts"))
        length = self._thread_value("Thread_Length")
        clearance = self._thread_value("Thread_Clearance")
        first = self._thread_value("Thread_First_Depth")
        final = self._thread_value("Thread_Final_Depth")
        spring = int(self._thread_value("Thread_Spring"))
        passes = self._thread_passes_per_start()
        if length <= 0:
            _show_settings_error(widget, "Enter the thread length.")
            return
        if passes is None:
            _show_settings_error(widget, "Enter the first cut depth and final depth.")
            return
        # Final depth is shown to 4 places - allow for that rounding.
        if final > max_depth + 0.00005:
            _show_settings_error(widget, "Final depth can't be more than the max depth (%.4f)." % max_depth)
            return
        if passes - spring > THREAD_MAX_PASSES_PER_START:
            _show_settings_error(widget, "That's %d passes per start - check the first cut depth." % (passes - spring))
            return
        if not self._sync_ready_to_move(widget):
            return
        if not _confirm_roles_enabled(widget, list(THREAD_AXES)):
            return

        # Outside threads feed in toward the work's centre (-X), inside
        # threads out toward the bore wall (+X) - the same convention as
        # G76's I sign.
        infeed = 1 if self.builder.get_object("Thread_Side").get_active_id() == "inside" else -1
        z_sign = 1 if self.builder.get_object("Thread_Dir").get_active_id() == "l2r" else -1
        # With the work turned by C (right-hand rule about +Z) under a
        # fixed cutter, a right-hand thread needs C to turn opposite to
        # Z's travel, a left-hand thread the same way.
        c_sign = -z_sign if self.builder.get_object("Thread_Hand").get_active_id() == "right" else z_sign
        c_travel = c_sign * length / lead * 360.0
        # Smallest move back to the same C phase as the start of the pass.
        c_return = math.remainder(-c_travel, 360.0)
        # Time the helix to whichever of Z and C is slower at its own
        # row's Feed Rate, the same way Sync Move does (G93 inverse time).
        minutes = max(length / feeds["Z"], abs(c_travel) / feeds["C"])

        args = (infeed, clearance, z_sign * length, c_travel, c_return,
                first, final, spring, starts, 360.0 / starts,
                feeds["X"], 1.0 / minutes, 21 if self._thread_metric else 20)
        gcode = "o<rosetta_thread> call " + " ".join("[%.6f]" % a for a in args)

        self._thread_start = tuple(s.position)
        self._thread_running = True
        self._thread_last_code = 0
        self._thread_show_status("Starting...")
        self._start_polled_mdi(widget, gcode, self._thread_finished,
                               self._mdi_progress_start("Threading", passes=passes,
                                                        starts=starts, spring=spring))

    @staticmethod
    def _thread_ordinal(n):
        suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return str(n) + suffix

    def _thread_describe(self, code, stopped=False):
        '''
        Operator-facing sentence for one of rosetta_thread.ngc's progress
        codes (start x 10000 + kind x 1000 + pass number) - what it's
        doing now, or with stopped=True, what it was doing when stopped
        - or None for 0 / anything unrecognised. The "- start N of M"
        suffix only appears for a multi-start thread.
        '''
        start, rest = divmod(int(round(code)), 10000)
        kind, number = divmod(rest, 1000)
        if start < 1:
            return None
        starts = int(self._thread_value("Thread_Starts"))
        of_starts = " - start %d of %d" % (start, starts) if starts > 1 else ""
        if kind == THREAD_KIND_PASS:
            phrase = self._thread_ordinal(number) + " pass" + of_starts
        elif kind == THREAD_KIND_FINAL:
            phrase = self._thread_ordinal(number) + " pass (final depth)" + of_starts
        elif kind == THREAD_KIND_SPRING:
            phrase = "spring pass %d%s" % (number, of_starts)
        elif kind == THREAD_KIND_INDEX:
            action = "indexing C to start %d of %d" % (start, starts)
            return ("Stopped while " + action if stopped else action[0].upper() + action[1:]) + "."
        elif kind == THREAD_KIND_DONE:
            return "Done." if stopped else "Returning C to where it began."
        else:
            return None
        return ("Stopped during the " if stopped else "Running ") + phrase + "."

    def _thread_show_status(self, text):
        '''
        Shows a Cut Thread's progress in place of the Threading tab's
        instructions (same spot, so nothing moves), in bold.
        '''
        if self._thread_result_id is not None:
            GLib.source_remove(self._thread_result_id)
            self._thread_result_id = None
        self.builder.get_object("Thread_Instructions").set_markup(
            "<b>" + GLib.markup_escape_text(text) + "</b>")

    def _thread_restore_instructions(self):
        self._thread_result_id = None
        self.builder.get_object("Thread_Instructions").set_text(self._thread_instructions)
        return False

    def _on_thread_status(self, pin, data=None):
        code = pin.get()
        if not self._thread_running or code == 0:
            return
        text = self._thread_describe(code)
        if text is None:
            return
        self._thread_last_code = code
        self._thread_show_status(text)

    def _thread_finished(self):
        '''
        Cut Thread's MDI call is over - finished, or stopped from AXIS.
        rosetta_thread.ngc only reports THREAD_KIND_DONE once every pass is
        cut, so any other last code means it was stopped part way.
        '''
        self._thread_running = False
        # A stop during the final "returning C" move still counts as
        # done - every pass was already cut.
        text = self._thread_describe(self._thread_last_code, stopped=True) or "Stopped before the first pass."
        self._thread_show_status(text)
        self._thread_result_id = GLib.timeout_add_seconds(
            THREAD_RESULT_SECONDS, self._thread_restore_instructions)
        finished = (int(round(self._thread_last_code)) % 10000) // 1000 == THREAD_KIND_DONE
        self._mdi_progress_end(finished)
        if finished:
            self._play_sound(DONE_BEEPS)

    def Thread_Return(self, widget):
        '''
        Puts X, Z and C back where they were when Cut Thread last
        started - X first, straight out, so the cutter clears the thread
        even after a Cut Thread stopped part way, then Z and C together.
        C only turns as far as it takes to get back in phase with where
        it started, not back through every turn it made.
        '''
        print("=================================================")
        print("FUNCTION Thread_Return")
        if self._thread_start is None:
            _show_settings_error(widget, "Nothing to return from - use Cut Thread first.")
            return
        if not self._sync_ready_to_move(widget):
            return

        deltas = {}
        for axis in THREAD_AXES:
            i = STAT_POSITION_INDEX[axis]
            deltas[axis] = self._thread_start[i] - s.position[i]
        deltas["C"] = math.remainder(deltas["C"], 360.0)
        if all(abs(d) < SYNC_POSITION_TOLERANCE for d in deltas.values()):
            _show_settings_error(widget, "Already at the starting point.")
            return
        if not _confirm_roles_enabled(widget, [a for a, d in deltas.items()
                                               if abs(d) >= SYNC_POSITION_TOLERANCE]):
            return

        args = (deltas["X"], deltas["Z"], deltas["C"], 21 if self._thread_metric else 20)
        gcode = "o<rosetta_thread_return> call " + " ".join("[%.6f]" % a for a in args)
        self._start_polled_mdi(widget, gcode)


#######################################################################
# Attention sounds
# Purpose:              3 short beeps when a G-code program, a Sync Move
#                       Run Operation or a Cut Thread finishes normally;
#                       2 when a program stops at M0/M1/M60 to wait for
#                       the operator. Played on the signal tower's
#                       buzzer and/or the Pi's speaker, per RosettaSet_v1.ini's
#                       "done_sound" (Rosetta Settings, Axis Selection page;
#                       read once at startup, like the tower itself).
#                       Also plays the fault siren on the speaker, per
#                       "fault_sound" (the tower's own siren is all HAL).
#                       Only the main panel component plays them; every
#                       other component no-ops.
# Updated:              ver 1.1, 20 October 2026 - program finish
#                       detection (_poll_program)
#######################################################################
    def _load_sounds(self):
        if self.builder.get_object("Sync_Run") is None:
            return
        settings = rosetta_settings_io.load_settings()
        choice = settings.get("done_sound", "both")
        self._sound_tower = choice in ("tower", "both") and settings.get("signal_tower") is True
        self._sound_speaker = choice in ("speaker", "both")
        fault_speaker = settings.get("fault_sound", "both") in ("speaker", "both")
        self._sound_player = None
        if self._sound_speaker or fault_speaker:
            for player in SOUND_PLAYERS:
                if shutil.which(player[0]):
                    self._sound_player = player
                    break
            if self._sound_player is None:
                print("Attention sounds: no audio player found (" +
                      ", ".join(p[0] for p in SOUND_PLAYERS) + ") - speaker sounds off")
        print("Attention sounds: tower " + ("on" if self._sound_tower else "off") +
              ", speaker " + ("on" if self._sound_player and self._sound_speaker else "off") +
              "; fault siren on speaker " + ("on" if self._sound_player and fault_speaker else "off"))

        # Fault siren for the speaker: netted (in Rosetta_PostGUI_v1.local.hal)
        # to the tower-siren pulse only when fault_sound includes the
        # speaker. The pulse lasts 3 s, so polling can't miss it.
        self.halcomp.newpin("fault-siren", hal.HAL_BIT, hal.HAL_IN)
        self._fault_siren_was_on = False
        if fault_speaker and self._sound_player is not None:
            GLib.timeout_add(PROGRAM_POLL_MS, self._poll_fault_siren)

        # Pulsed in the beep pattern; Rosetta_Generate_Local_Ini.py nets it
        # (in Rosetta_PostGUI_v1.local.hal) into the buzzer's OR gate
        # alongside the fault siren, only when a tower is connected.
        self.halcomp.newpin("tower-beep", hal.HAL_BIT, hal.HAL_OUT)
        self._beep_steps_left = 0

        # Program state seen at the last check - see _poll_program.
        self._program_was_running = False
        self._program_was_paused = False
        self._program_end_line = None
        self._program_read_end = False
        GLib.timeout_add(PROGRAM_POLL_MS, self._poll_program)

    def _play_sound(self, beeps):
        if self.builder.get_object("Sync_Run") is None:
            return
        print("Attention sound: %d beeps" % beeps)
        if self._sound_speaker:
            self._play_on_speaker(SOUND_FILES[beeps])
        if self._sound_tower and self._beep_steps_left == 0:
            # Each step flips the pin: on, off, on, off, ...
            self._beep_steps_left = beeps * 2
            self._tower_beep_step()
            GLib.timeout_add(int(BEEP_SECONDS * 1000), self._tower_beep_step)

    def _play_on_speaker(self, path):
        if self._sound_player is None:
            return
        try:
            subprocess.Popen(self._sound_player + [path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as e:
            print("Could not play " + path + ": " + str(e))

    def _poll_fault_siren(self):
        on = self.halcomp["fault-siren"]
        if on and not self._fault_siren_was_on:
            print("Fault siren")
            self._play_on_speaker(SOUND_FILES[FAULT_SIREN])
        self._fault_siren_was_on = on
        return True

    def _tower_beep_step(self):
        if self._beep_steps_left <= 0:
            self.halcomp["tower-beep"] = False
            return False
        self.halcomp["tower-beep"] = self._beep_steps_left % 2 == 0
        self._beep_steps_left -= 1
        return True

    @staticmethod
    def _gcode_words(line):
        '''A G-code line with its (comments) and ;comment removed, upper case.'''
        return re.sub(r"\([^)]*\)", " ", line.split(";")[0]).upper()

    def _find_program_end_line(self, path):
        '''
        Line number (1-based) of the loaded program's last M2/M30, or
        its last line if it has neither. A run counts as finished only
        if the interpreter read that far - see _poll_program. None if
        the file can't be read.
        '''
        try:
            with open(path, "r", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            return None
        last = len(lines)
        for number, line in enumerate(lines, 1):
            if re.search(r"\bM0*(2|30)\b", self._gcode_words(line)):
                last = number
        return last

    def _line_is_operator_stop(self, path, number):
        '''True when line `number` of the program is an M0/M1/M60.'''
        try:
            with open(path, "r", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if i == number:
                        return bool(re.search(r"\bM0*(0|1|60)\b", self._gcode_words(line)))
        except OSError:
            pass
        return False

    def _poll_program(self):
        '''
        Watches a program run from a file (AUTO mode). LinuxCNC has no
        "finished normally" flag - pressing Stop, E-stop, turning the
        machine off and an error all end a run the same way as M2/M30 -
        so a run counts as finished only if the machine is still on,
        the interpreter read as far as the program's M2/M30
        (_find_program_end_line) and LinuxCNC already reports the run
        done (RCS_DONE) as it goes idle. Checked on the machine 20
        October 2026: at M30 read_line was past the M30 and the state
        was DONE at once; after Stop read_line was part way and the
        state stayed EXEC for a moment as the motion queue emptied.
        The first version compared motion_line with the file's last
        axis move, which a program whose last move is in an o-word If
        it skipped (or that ends in loops) never reaches - no beeps.
        MDI commands (Sync Move, Threading, indexing) are left to their
        own handlers.
        '''
        s.poll()
        auto = s.task_mode == linuxcnc.MODE_AUTO
        running = auto and s.interp_state != linuxcnc.INTERP_IDLE
        paused = running and s.interp_state == linuxcnc.INTERP_PAUSED

        if running and not self._program_was_running:
            self._program_end_line = self._find_program_end_line(s.file)
            self._program_read_end = False
            self._progress_start()
        # read_line drops to 0 once the run ends, so note it while running.
        if running and self._program_end_line is not None \
                and s.read_line >= self._program_end_line:
            self._program_read_end = True

        if paused and not self._program_was_paused:
            if self._line_is_operator_stop(s.file, s.current_line) or \
                    self._line_is_operator_stop(s.file, s.motion_line):
                self._play_sound(PAUSE_BEEPS)

        if self._program_was_running and not running:
            finished = (s.task_state == linuxcnc.STATE_ON
                        and self._program_read_end
                        and s.state == linuxcnc.RCS_DONE)
            print("Program run ended: M2/M30 line=%s read=%s state=%d machine %s -> %s"
                  % (self._program_end_line, self._program_read_end, s.state,
                     "on" if s.task_state == linuxcnc.STATE_ON else "off",
                     "finished" if finished else "stopped/aborted"), flush=True)
            if finished:
                self._play_sound(DONE_BEEPS)
            self._progress_end(finished)

        self._progress_update(running, paused)
        # Continue also resumes a paused program - see _program_paused.
        self._sync_update_pause_button()
        self._program_was_running = running
        self._program_was_paused = paused
        return True


#######################################################################
# Program progress
# Purpose:              A bar left of Sync Move showing how far a G-code
#                       program, a Sync Move or a Cut Thread has got, as
#                       a percentage (not Run Operation, indexing or the
#                       Return moves - Rich's choice, 20 October 2026). A
#                       Sync Move is one move of known length, measured
#                       with program-path below; a Cut Thread counts
#                       passes finished from rosetta_thread.ngc's progress
#                       codes (_mdi_progress_*). For a program:
#                       Line numbers can't say how far a program is -
#                       o-word loops run the same lines over and over -
#                       so as a program starts Rosetta_Program_Estimate.py
#                       works out every move it will make from where the
#                       machine is, in order, with the path length the
#                       motion planner counts for each (in the background,
#                       a few seconds - not at load, since a jog in
#                       between would change the first move). Rosetta.hal's
#                       program-path.out adds up that same length as the
#                       machine moves, so how far it has grown since the
#                       run started finds the place in the move list,
#                       and the estimated time up to there over the
#                       total is the percentage (time-weighted, so a long
#                       slow cut counts for more than a quick rapid; the
#                       estimate includes acceleration, without which the
#                       bar lagged up to 30% on Rich's first test). No
#                       time left: it was shown at first (worked out from
#                       the real rate) but kept changing as the program
#                       went - Rich's call, 20 October 2026, the
#                       percentage is enough. Driven by _poll_program.
#                       The bar always keeps its space (set_child_visible)
#                       so the panel doesn't change size when it appears -
#                       the Sync Move row is otherwise empty on the other
#                       tabs. Main panel only.
# Updated:              ver 1.0, 20 October 2026
#######################################################################
    def _load_program_progress(self):
        self._progress_bar = None
        if self.builder.get_object("Sync_Run") is None:
            return
        self._progress_bar = self.builder.get_object("Program_Progress")
        self._progress_bar.set_child_visible(False)
        self._progress_estimate = None      # this run's moves (dict)
        self._progress_proc = None          # the helper while it runs
        self._progress_output = "/tmp/Rosetta_progress_%d.json" % os.getpid()
        self._progress_run = None           # the run being shown
        self._mdi_progress = None           # a Sync Move or Cut Thread being shown

    def _progress_collect(self):
        '''Picks up the estimate helper's result once it has finished.'''
        if self._progress_proc is None or self._progress_proc.poll() is None:
            return
        ok = self._progress_proc.returncode == 0
        self._progress_proc = None
        try:
            if ok:
                with open(self._progress_output) as f:
                    data = json.load(f)
                if data.get("error"):
                    print("Program progress: " + data["error"])
                if data["time"] and data["time"][-1] > 0:
                    self._progress_estimate = data
                    print("Program progress: %d moves, estimated %s"
                          % (len(data["time"]), self._progress_duration(data["time"][-1])))
        except (OSError, ValueError, KeyError) as e:
            print("Program progress: no estimate - " + str(e))
        try:
            os.remove(self._progress_output)
        except OSError:
            pass

    def _progress_path(self):
        try:
            return hal.get_value("program-path.out")
        except Exception:
            return None

    def _progress_start(self):
        '''
        A program has started: works out its moves from where the
        machine is now (a few seconds, in the background), and notes
        program-path, which grows from here as it moves.
        '''
        if self._progress_bar is None:
            return
        if self._progress_proc is not None:
            self._progress_proc.kill()
            self._progress_proc.wait()
            self._progress_proc = None
        self._progress_estimate = None
        start = self._progress_path()
        if start is None or not s.file:
            self._progress_run = None
            self._progress_bar.set_child_visible(False)
            return
        try:
            self._progress_proc = subprocess.Popen(
                ["nice", "-n", "10", "python3", PROGRAM_ESTIMATE_SCRIPT, s.file,
                 self._progress_output], stdout=subprocess.DEVNULL)
        except OSError as e:
            print("Program progress: could not start the estimate - " + str(e))
        self._progress_run = {"start": start, "elapsed": 0.0, "last": time.monotonic(),
                              "first_line": 0, "part_way": None, "fraction": 0.0}
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_text("Program 0% - working it out")
        self._progress_bar.set_child_visible(True)

    def _progress_update(self, running, paused):
        run = self._progress_run
        if self._progress_bar is None or not running or run is None or run.get("ended"):
            return
        now = time.monotonic()
        if not paused:
            run["elapsed"] += now - run["last"]
        run["last"] = now
        if not run["first_line"]:
            run["first_line"] = s.motion_line
        self._progress_collect()
        data = self._progress_estimate
        if data is None:
            return
        if run["part_way"] is None and run["first_line"]:
            run["part_way"] = run["first_line"] not in data["line"][:PROGRESS_START_MOVES]
        if run["part_way"]:
            self._progress_bar.set_text("Started part way - no progress shown")
            return
        path = self._progress_path()
        if path is None:
            return
        done = self._progress_time_at(data, path - run["start"])
        total = data["time"][-1]
        fraction = min(done / total, 0.999)
        run["fraction"] = fraction
        self._progress_bar.set_fraction(fraction)
        text = "Program %d%%" % int(fraction * 100)
        if paused:
            text += " (paused)"
        self._progress_bar.set_text(text)

    @staticmethod
    def _progress_time_at(data, distance):
        '''Estimated time to the point `distance` along the move list.'''
        lengths, times = data["length"], data["time"]
        i = bisect.bisect_left(lengths, distance)
        if i >= len(lengths):
            return times[-1]
        before_len = lengths[i - 1] if i > 0 else 0.0
        before_time = times[i - 1] if i > 0 else 0.0
        span = lengths[i] - before_len
        part = (distance - before_len) / span if span > 0 else 1.0
        return before_time + part * (times[i] - before_time)

    def _progress_end(self, finished):
        run = self._progress_run
        if self._progress_bar is None or run is None:
            return
        run["ended"] = True
        self._progress_collect()
        if run["part_way"] or self._progress_estimate is None:
            self._progress_bar.set_child_visible(False)
        elif finished:
            self._progress_bar.set_fraction(1.0)
            self._progress_bar.set_text("Program done in " + self._progress_duration(run["elapsed"]))
        else:
            self._progress_bar.set_text("Program stopped at %d%%" % int(run["fraction"] * 100))
        print("Program progress: run took %s (not counting pauses), estimate %s"
              % (self._progress_duration(run["elapsed"]),
                 self._progress_duration(self._progress_estimate["time"][-1])
                 if self._progress_estimate else "none"), flush=True)

    def _mdi_progress_start(self, name, length=None, passes=None, starts=None, spring=None):
        '''
        Puts a Sync Move (length = its planner length, measured with
        program-path like a program) or a Cut Thread (counted in passes,
        from rosetta_thread.ngc's progress codes) on the bar. Returns the
        description for _start_polled_mdi, or None. Run Operation,
        indexing and the Return moves aren't shown.
        '''
        if self._progress_bar is None:
            return None
        progress = {"name": name, "fraction": 0.0}
        if length is not None:
            start = self._progress_path()
            if start is None or length <= 0:
                return None
            progress.update(start=start, length=length)
        else:
            progress.update(passes=passes, starts=starts, spring=spring)
        self._progress_run = None
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_text(name + " 0%")
        self._progress_bar.set_child_visible(True)
        return progress

    def _mdi_progress_update(self):
        progress = self._mdi_progress
        if self._progress_bar is None or progress is None:
            return
        if "length" in progress:
            path = self._progress_path()
            if path is None:
                return
            fraction = (path - progress["start"]) / progress["length"]
        else:
            # Passes finished so far: rosetta_thread.ngc reports each pass as
            # it starts (start x 10000 + kind x 1000 + pass number).
            start, rest = divmod(int(round(self._thread_last_code)), 10000)
            kind, number = divmod(rest, 1000)
            passes = progress["passes"]
            if start < 1:
                done = 0
            elif kind == THREAD_KIND_SPRING:
                done = (start - 1) * passes + passes - progress["spring"] + number - 1
            elif kind in (THREAD_KIND_PASS, THREAD_KIND_FINAL):
                done = (start - 1) * passes + number - 1
            elif kind == THREAD_KIND_DONE:
                done = progress["starts"] * passes
            else:                               # indexing to the next start
                done = (start - 1) * passes
            fraction = done / float(progress["starts"] * passes)
        fraction = max(0.0, min(fraction, 0.999))
        progress["fraction"] = fraction
        self._progress_bar.set_fraction(fraction)
        text = "%s %d%%" % (progress["name"], int(fraction * 100))
        if s.interp_state == linuxcnc.INTERP_PAUSED:
            text += " (paused)"
        self._progress_bar.set_text(text)

    def _mdi_progress_end(self, finished):
        progress = self._mdi_progress
        self._mdi_progress = None
        if self._progress_bar is None or progress is None:
            return
        if finished:
            self._progress_bar.set_fraction(1.0)
            self._progress_bar.set_text(progress["name"] + " done")
        else:
            self._progress_bar.set_text("%s stopped at %d%%" % (progress["name"],
                                                               int(progress["fraction"] * 100)))

    @staticmethod
    def _progress_duration(seconds):
        minutes = int(round(seconds / 60.0))
        if minutes < 1:
            return "under a minute"
        if minutes < 60:
            return "%d min" % minutes
        return "%d h %02d min" % (minutes // 60, minutes % 60)


#######################################################################
# Version label (machine S/N)
# Purpose:              Appends ", Machine S/N <n>" to the main panel's
#                       "O/S ..." label once an owner has set a
#                       friendly serial number (Rosetta_Set_Serial_Number.sh,
#                       ~/.config/Rosetta/serial - SERIAL_PATH above), so the
#                       panel shows which machine this is at a glance
#                       (Rich's idea). Left as shipped (no suffix) until
#                       a serial has been set. Main panel only -
#                       Rosetta_Panel_v1.ui's own static text is untouched,
#                       which is what Rosetta_Report_Version.py reads by
#                       regex.
# Updated:              ver 1.0, 26 October 2026
#######################################################################
    def _load_version_label(self):
        label = self.builder.get_object("OS_Version_Label")
        if label is None:
            return
        try:
            with open(SERIAL_PATH, "r") as f:
                serial = f.read().strip()
        except OSError:
            serial = ""
        if not serial:
            return
        label.set_text(label.get_text() + ", Machine S/N " + serial)


#######################################################################
# Card contact
# Purpose:              A Mesa card that loses contact with the Pi -
#                       network cable, switch or the box's power - stops
#                       its axes but, on its own, leaves the machine on
#                       and the other box's axes running, and stays cut
#                       off even once the cable is back (found 16 October
#                       2026). Rosetta_Generate_Local_Ini.py's _estop_fault_hal
#                       latches E-stop on the card's packet-error-exceeded
#                       or watchdog.has_bit; this says which box it was
#                       and, while the machine is in E-stop, brings the
#                       card back: clears its io_error (hm2_eth then
#                       talks to it again and reads has_bit, TRUE if the
#                       card's watchdog bit), then has_bit (its outputs
#                       come back). Both are done only in E-stop, so
#                       nothing can move as the card returns. A card
#                       still unplugged fails again at once, keeping the
#                       latch set, so F1 can't reset until it's fixed.
#                       Main panel only.
# Updated:              ver 1.0, 16 October 2026
#######################################################################
    def _load_card_contact(self):
        if self.builder.get_object("Sync_Run") is None:
            return
        # The cards this session loaded (not the expansion_box setting,
        # which ROSETTA_SHOW_EXPANSION can override for screenshots).
        self._cards = []
        for n in CARD_NAMES:
            try:
                hal.get_value("hm2_7i92.%d.io_error" % n)
            except RuntimeError:
                continue
            self._cards.append(n)
        self._card_lost = {n: False for n in self._cards}
        self._card_retry_at = {n: 0.0 for n in self._cards}
        GLib.timeout_add(CARD_CONTACT_POLL_MS, self._poll_card_contact)

    def _poll_card_contact(self):
        s.poll()
        in_estop = s.task_state == linuxcnc.STATE_ESTOP
        now = time.monotonic()
        for n in self._cards:
            card = "hm2_7i92.%d" % n
            io_error = bool(hal.get_value(card + ".io_error"))
            bitten = bool(hal.get_value(card + ".watchdog.has_bit"))
            lost = io_error or bitten or bool(hal.get_value(card + ".packet-error-exceeded"))
            if lost and not self._card_lost[n]:
                message = (CARD_NAMES[n] + " lost contact - E-stop. Check its network cable, "
                           "the switch and its power, then press F1.")
                print(message)
                c.error_msg(message)
            elif self._card_lost[n] and not lost:
                print(CARD_NAMES[n] + " back in contact.")
            self._card_lost[n] = lost
            if not (lost and in_estop):
                continue
            if io_error:
                if now >= self._card_retry_at[n]:
                    self._card_retry_at[n] = now + CARD_RECONNECT_SECONDS
                    self._halcmd("setp", card + ".io_error", "FALSE")
            elif bitten:
                # has_bit is netted (to card-fault-or), so its signal is set.
                self._halcmd("sets", "card-%d-watchdog" % n, "FALSE")
        return True

    @staticmethod
    def _halcmd(*args):
        try:
            subprocess.run(["halcmd"] + list(args), check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as e:
            print("halcmd " + " ".join(args) + " failed: " + str(e))


#######################################################################
# __init__
# Purpose:              This is used to initialize everything.
# Updated:              ver 1.0, 21 July 2026
#######################################################################
    def __init__(self, halcomp,builder,useropts):
        '''
        Handler classes are instantiated in the following state:
        - the widget tree is created, but not yet realized (no toplevel window.show() executed yet)
        - the halcomp HAL component is set up and the widhget tree's HAL pins have already been added to it
        - it is safe to add more hal pins because halcomp.ready() has not yet been called at this point.

        after all handlers are instantiated in command line and get_handlers() order, callbacks will be
        connected with connect_signals()/signal_autoconnect()

        The builder may be either of libglade or GtkBuilder type depending on the glade file format.
        '''

        self.halcomp        = halcomp
        self.builder        = builder
        self.nhits          = 0





        # Same suppression as above, for _load_axis_comments driving each
        # axis's comment combo box at startup.
        self._applying_axis_comments = False



        _install_depress_css()

        # Independent pins this component owns, used to force each
        # axis disabled from this tab regardless of what the main
        # panel's own enable button is doing. Each defaults to "allow
        # enabled". ANDed with the panel button per-axis in
        # Rosetta_PostGUI_v1.hal - only this component's own copy
        # ("gladevcp.<Axis>_Ena_Override") is actually netted; every
        # other component (Help, License) creates the same pin
        # harmlessly unused.
        #
        # HAL_IO, not HAL_OUT: this component's own Set_Scale handlers
        # clear an axis to False, but re-arming it happens from the main
        # panel's ENA button - a different process - via
        # the external Rosetta_Settings program clears an axis to False
        # before a scale change (a different process, via
        # `halcmd sets <letter>-ena-settings-allow FALSE` - the signal,
        # not this pin directly, once netted) - re-arming happens back
        # in THIS component's own _clear_ena_override, below, when the
        # panel's ENA button is pressed again. See
        # _clear_ena_override). An OUT pin can only ever be driven by
        # its owning component; halcmd setp on one fails outright
        # ("pin is not writable"). IO allows the legitimate external
        # write while this component's own self.halcomp[...] = value
        # writes still work exactly the same as before.
        #
        # Per the GladeVCP docs, an output pin must be created via
        # hal_glib.GPin(halcomp.newpin(...)) - not a bare newpin() -
        # for writes through halcomp[name] = value to actually take
        # effect. The GPin objects are kept on self so they aren't
        # garbage-collected.
        self._ena_override_pins = {}
        for axis_id in PANEL_INTERNAL_IDS:
            pin_name = axis_id + "_Ena_Override"
            self._ena_override_pins[axis_id] = hal_glib.GPin(
                self.halcomp.newpin(pin_name, hal.HAL_BIT, hal.HAL_IO)
            )
            self.halcomp[pin_name] = True

        # Sp0-idx-angle/Sp1-idx-angle (float) and Sp0-idx-active/
        # Sp1-idx-active (bit) - drive orient.0/orient.1 directly,
        # bypassing M19/MDI, so Sp0_Move_Idx_Fwd/Rev can trigger both
        # spindles in the same servo cycle when both are selected for
        # indexing (see Rosetta.hal's Sp0/Sp1 blocks: mux2.2/mux2.3 pick
        # this angle over the M19-driven one, or2.0/or2.1 OR this
        # active bit into the same enable chain M19 already used).
        # HAL_OUT (not IO): only this component (the main panel,
        # "gladevcp" - the only one with the Idx Fwd/Rev buttons) ever
        # drives these, so plain GPin output pins are enough - see
        # _ena_override_pins above for why GPin specifically (required
        # for halcomp[name] = value writes to take effect).
        self._sp_idx_pins = {}
        if self.builder.get_object("Sp0_Idx_Fwd") is not None:
            for spindle_id in ("Sp0", "Sp1"):
                angle_pin = spindle_id + "-idx-angle"
                active_pin = spindle_id + "-idx-active"
                self._sp_idx_pins[spindle_id + "_Angle"] = hal_glib.GPin(
                    self.halcomp.newpin(angle_pin, hal.HAL_FLOAT, hal.HAL_OUT)
                )
                self._sp_idx_pins[spindle_id + "_Active"] = hal_glib.GPin(
                    self.halcomp.newpin(active_pin, hal.HAL_BIT, hal.HAL_OUT)
                )
                self.halcomp[active_pin] = False





        # Restore persisted per-axis user comments (REB_Settings_v1.ini)
        # into the main panel's comment fields. No-ops in every
        # component other than the main panel (gladevcp), which is the
        # only one with these widgets.
        self._load_axis_comments()

        # Baseline for _autosave_axis_comments below - what's on screen
        # right after the load above already matches REB_Settings_v1.ini,
        # so there's nothing to flush until an operator actually changes
        # a field.
        self._last_saved_axis_comment = {
            axis_id: _combo_selected_device(widget)
            for axis_id in COMMENT_AXES
            for widget in [self.builder.get_object(axis_id + "_Comment")]
            if widget is not None
        }

        # Backstop for X_Comment/Z_Comment/etc.'s "changed" signal -
        # cheap insurance alongside it, on the same reasoning as the old
        # Entry-based "activate"/"focus-out-event" backstop this
        # replaced (a GtkComboBoxText's "changed" signal is a plain
        # same-process GTK signal with none of that focus-out-event's
        # cross-process reliability concerns, but polling every second
        # and only writing a field that actually changed since the last
        # flush costs nothing while idle). See _autosave_axis_comments.
        GLib.timeout_add(1000, self._autosave_axis_comments)




        # Restore the persisted channel -> axis letter assignment
        # (RosettaSet_v1.ini) into the main panel's own read-only display
        # (if owned by this component).
        self._load_panel_axis_display()

        # Reconfigure the main panel's 6 channel rows (letter label,
        # jog icons, adjustment ranges, column-11 widget visibility) to
        # match each channel's current type/letter (if owned by this
        # component).
        self._load_panel_axis_controls()

        # Append ", Machine S/N <n>" to the "O/S ..." label if this
        # owner has set a friendly serial number (if owned by this
        # component) - see _load_version_label.
        self._load_version_label()

        # Sync Move tab setup (if owned by this component).
        self._load_sync_move_tab()

        # Threading tab setup (if owned by this component).
        self._load_threading_tab()

        # Program progress bar (main panel only) - see
        # _load_program_progress. Before _load_sounds, whose program poll
        # drives it.
        self._load_program_progress()

        # Program-done / pause beeps (main panel only) - see _load_sounds.
        self._load_sounds()

        # E-stop on a card losing contact, and bringing it back (main
        # panel only) - see _load_card_contact.
        self._load_card_contact()



        # Let the mouse wheel scroll the page even when the cursor is
        # over one of its many spin buttons/combo boxes, rather than only
        # working over the shrinking gaps between them - see
        # _redirect_scroll_to_viewport. No-op wherever there's no
        # "viewport1" (every tab/panel other than the ones that embed a
        # GtkScrolledWindow).
        viewport = self.builder.get_object("viewport1")
        if viewport is not None:
            self._install_viewport_scroll_redirect(viewport)

        # Input pin fed from the existing "machine-is-on" HAL signal
        # (net machine-is-on => gladevcp.machine-is-on in
        # Rosetta_PostGUI_v1.hal). Grays out the whole main panel grid
        # whenever the machine is not powered on. GPin.update() treats
        # any pin's first read after creation as a change (self._prev
        # starts as None), so this fires once automatically shortly
        # after startup even if the machine is already on - no need to
        # sync it manually here.
        self._machine_is_on_pin = hal_glib.GPin(
            self.halcomp.newpin("machine-is-on", hal.HAL_BIT, hal.HAL_IN)
        )
        self._machine_is_on_pin.connect('value-changed', self._on_machine_is_on_changed)

        ###############################################################
        # Global Program Variables - declare and set initial value.
        ###############################################################

        self.Sp0_Feed       = 1.0       # Sp0 Speed
        self.Sp0_Idx_Bool   = True      # Index this spindle? Default enabled at startup. The checkbox itself doesn't reliably render checked from the .ui file's active="True" alone (confirmed live) - _set_checkbox_active below forces it to match once the panel is up.
        self.Sp0_Idx_DegDiv = "Deg"     # Sp0 & Sp1 spindles: index by degrees or divisions
        self.Sp0_Idx_Deg    = 90.0      # Sp0 index degrees
        self.Sp0_Idx_Dist   = 90.0      # B axis index distance
        self.Sp0_Idx_Qty    = 0         # Sp0 axis index counter
        self.Sp0_Feed_debounce_id = None  # pending GLib timeout for Sp0_Set_Feed, see that handler

        self.Sp1_Idx_Bool   = False     # Index this spindle? See Sp0_Idx_Bool - the checkbox renders unchecked at launch regardless of the .ui default.
        self.Sp1_Idx_Dist   = 90.0      # Sp1 index degrees
        self.Sp1_Idx_Qty    = 0         # Sp1 axis index counter
        self.Sp1_Pct        = 100.0     # Sp1 speed percentage of Sp0 speed
        self.Sp1_Pct_debounce_id = None  # pending GLib timeout for Sp1_Set_Move_Pct, see that handler

        # Match the on-screen checkboxes to the defaults above (see
        # _set_checkbox_active for why this is deferred rather than done
        # here directly).
        GLib.idle_add(self._set_checkbox_active, 'Sp0_Set_Idx_OnOff', self.Sp0_Idx_Bool)
        GLib.idle_add(self._set_checkbox_active, 'Sp1_Set_Idx_OnOff', self.Sp1_Idx_Bool)

        # Keep the Run Operation tab's Fwd/Rev buttons showing pressed
        # for as long as the spindle is actually running that direction
        # (see _sync_run_operation_buttons). No-ops itself out after one
        # call in every component other than the main panel.
        GLib.timeout_add(100, self._sync_run_operation_buttons)

        # Per-letter state for all 8 axis letters, read/written by the
        # generated Idx_Fwd/Idx_Rev/Set_Feed/etc. methods below via
        # getattr/setattr. Defaults are picked from the letter's own
        # fixed type (_axis_type_for_letter - A/B/C angular, the rest
        # linear; type has been purely letter-derived since the brief
        # independent-Type experiment was retired 4 September 2026).
        # Idx_Deg/Idx_DegDiv are harmless to set on a linear letter -
        # they simply go unused. Sp0/Sp1 keep their own hand-written
        # state above - genuinely different shape (Idx_Bool checkboxes,
        # no Move_Dist).
        for axis in AXIS_SELECTION_LETTERS:
            if _axis_type_for_letter(axis) == "ANGULAR":
                setattr(self, axis + "_Feed", TYPE_ADJUSTMENT_PROFILE["ANGULAR"])
                setattr(self, axis + "_Idx_Dist", 90.0)
                setattr(self, axis + "_Idx_Deg", 90.0)
            else:
                setattr(self, axis + "_Feed", TYPE_ADJUSTMENT_PROFILE["LINEAR"])
                setattr(self, axis + "_Idx_Dist", 0.0)
                setattr(self, axis + "_Idx_Deg", 0.0)
            setattr(self, axis + "_Idx_DegDiv", "Deg")
            setattr(self, axis + "_Idx_Qty", 0)
            setattr(self, axis + "_Move_Dist", 0.0)

        # Put back the main panel's values from last session (Indexing,
        # Sync Move, Threading) once the panel is up, then keep them
        # saved - see _restore_panel_state. Main panel only; queued after
        # the Sp0/Sp1 checkbox idle callbacks above, so it runs after them.
        self._restoring_panel = False
        if self.builder.get_object("Sync_Run") is not None and self.builder.get_object("Thread_Run") is not None:
            GLib.idle_add(self._restore_panel_state)

# ------------------------------------------------------------------
# Generated per-letter handlers, for all 8 axis letters
# (AXIS_SELECTION_LETTERS).
#
# Collapses the near-identical Idx_Plus/Idx_Minus/Set_Feed/Set_Idx_Dist/
# Set_Idx_DegDiv/Set_Move_Dist/Set_Scale methods - which used to be
# hand-written once per axis (see docs/hitcounter-review.md, Issue 1),
# then generated for the 5 linear axes only, with B kept separately
# hand-written (different shape: Idx_Deg/Idx_DegDiv derivation, no
# equivalent in the linear factories) - into one factory function per
# pattern, looped over all 8 letters and bound onto HandlerClass via
# setattr. This has to produce real, named methods rather than a
# __getattr__ dispatcher: GladeVCP discovers handlers via dir(instance)
# fed into builder.connect_signals(), and dir() does not enumerate names
# that only exist through __getattr__ - such a button would silently
# stop working with no error anywhere.
#
# A letter is no longer permanently linear or angular in the sense that
# used to matter here either - which shape a given letter's controls
# behave as is decided at CALL TIME by _axis_type_for_letter(axis), the
# one and only source of truth for TYPE. Since Rosetta_Panel_v1.ui's 18
# September 2026 rebuild, every letter follows the exact same
# "<letter>_Idx_Plus"/"<letter>_Idx_Minus"/"<letter>_Set_Feed" widget-id
# pattern - B's old exception (B_Idx_Fwd/B_Idx_Rev/B_Set_Idx_Feed) was
# renamed to match, so the handler name for any letter can just be
# computed directly instead of looked up (JOG_NEG_HANDLER/
# JOG_POS_HANDLER/FEED_HANDLER, which used to carry that exception,
# are gone).
#
# Set_Ena IS generated here (revised 2026-07-28): initially thought dead
# (no .ui file wires a <signal> to any <Axis>_Set_Ena), but that's because
# the ENA buttons were redesigned from HAL_Button (which used a "pressed"
# signal) to HAL_LightButton, which only emits "clicked" - the signal
# wiring was never carried over, silently orphaning
# _clear_ena_override()'s fix for the "press ENA and nothing happens,
# need a confusing second press" bug (see that function's own comments).
# The real fix is reconnecting Rosetta_Panel_v1.ui's <Axis>_ENA widgets'
# "clicked" signal to <Axis>_Set_Ena, not deleting the method.

# Column-12/column-13 jog button handler names actually wired in
# Rosetta_Panel_v1.ui, per channel. These are fixed forever (widgets are
# never renamed) - only B differs from the "<letter>_Idx_Minus"/
# "<letter>_Idx_Plus" pattern the rest use (B_Move_Idx_Fwd/Rev, a
# leftover from before this handler was generated generically). Despite
# the different naming, column 12 always sends G-code sign "-" and
# column 13 always sends "+" for every channel, linear or angular alike
# (empirically verified independently for both X's Idx_Minus/Idx_Plus
# and B's Move_Idx_Fwd/Rev - see the loop below) - that's what lets one
# factory serve both naming patterns.
def _axis_idx_move(axis, handler_name, gcode_sign):
    '''
    handler_name is the exact method name GladeVCP dispatches to
    ("<axis>_Idx_Plus"/"<axis>_Idx_Minus" - every letter follows this
    pattern since Rosetta_Panel_v1.ui's 18 September 2026 rebuild); gcode_sign
    ("+"/"-") is the actual sign sent in the G-code, and also which way
    the row's index counter moves: "+" (the Fwd column) counts up, "-"
    (Rev) down - see "Index counters". Whether this move
    uses Idx_Dist (linear) or the derived Idx_Deg (angular) is decided
    at call time from the letter's own fixed type - see the module
    comment above.
    '''
    def handler(self, widget):
        print("=================================================")
        print("FUNCTION " + handler_name)
        if not _confirm_roles_enabled(widget, [axis]):
            return

        # Depress the button for the duration of the move (see
        # _set_depressed for why this isn't a HAL_ToggleButton).
        _set_depressed(widget, True)
        try:
            s.poll()
            if s.task_state != linuxcnc.MODE_MDI:
                c.mode(linuxcnc.MODE_MDI)
                c.wait_complete()

            angular = _axis_type_for_letter(axis) == "ANGULAR"
            amount = getattr(self, axis + "_Idx_Deg") if angular else getattr(self, axis + "_Idx_Dist")
            feed = getattr(self, axis + "_Feed")
            # The G-code axis word is simply this row's own letter - a
            # letter is a stable role identity now (see
            # CHANNEL_DEFAULT_ROLE's comment above), so whichever
            # physical channel currently backs it, LinuxCNC recognizes
            # this exact letter in [TRAJ]COORDINATES as long as the role
            # is assigned to some channel (which is the only thing that
            # gates whether this handler is even reachable - see
            # _load_panel_axis_controls).
            gcode_axis = axis
            # The move states its own modes rather than relying on
            # Rosetta.ini's startup code (G20/G21 per the Measurement
            # System, G91, G94, G8). Added 08 November 2026 - GitHub
            # issue #24: after a G-code program (which leaves G90 in
            # effect) the buttons made absolute moves, so X went to +5
            # and a second press didn't move it, and C took the long way
            # round to an absolute angle. The operator's own modes and
            # modal F are put back afterwards, as Sync Move does.
            modal = set(s.gcodes)
            restore = " ".join([
                "G21" if 210 in modal else "G20",
                "G91" if 910 in modal else "G90",
                "G93" if 930 in modal else "G95" if 950 in modal else "G94",
                "G7" if 70 in modal else "G8",
                "F%.4f" % s.settings[1]])
            units = "G21" if getattr(self, "_sync_metric", False) else "G20"
            Gcode = (units + " G91 G94 G8 G1 " + gcode_axis + gcode_sign + str(amount)
                     + " F" + str(feed))

            print(Gcode)
            c.mdi(Gcode)
            c.wait_complete()
            c.mdi(restore)
            c.wait_complete()

            # Fwd (plus-sign column, sends "+") counts up, Rev counts down -
            # see "Index counters".
            self._bump_idx_count(axis, 1 if gcode_sign == "+" else -1)
        finally:
            _set_depressed(widget, False)
    handler.__name__ = handler_name
    return handler

def _axis_set_feed(axis, handler_name):
    def handler(self, widget):
        print("=================================================")
        print("FUNCTION " + handler_name)
        setattr(self, axis + "_Feed", round(widget.get_value(), 1))
        print(axis + "_Feed = " + str(getattr(self, axis + "_Feed")))
    handler.__name__ = handler_name
    return handler

def _axis_set_idx_dist(axis):
    '''
    Linear channels: Idx_Dist is used directly. Angular channels: Idx_Dist
    is the raw user entry, which - depending on the channel's Idx_DegDiv
    mode ("Deg" vs "Div", toggled by _axis_set_idx_degdiv below) - gets
    derived into Idx_Deg, the value _axis_idx_move actually sends in
    G-code (matches B's old hand-written derivation, now available to
    any channel currently angular).
    '''
    def handler(self, widget):
        print("=================================================")
        print("FUNCTION " + axis + "_Set_Idx_Dist")
        value = widget.get_value()
        setattr(self, axis + "_Idx_Dist", value)
        if _axis_type_for_letter(axis) == "ANGULAR":
            if getattr(self, axis + "_Idx_DegDiv") == "Deg":
                setattr(self, axis + "_Idx_Deg", round(value, 1))
            else:
                setattr(self, axis + "_Idx_Deg", round(360 / value, 1))
            print(axis + "_Idx_DegDiv = " + getattr(self, axis + "_Idx_DegDiv"))
            print(axis + "_Idx_Deg = " + str(getattr(self, axis + "_Idx_Deg")) + " deg")
        else:
            print(axis + "_Idx_Dist = " + str(value))
        self._set_idx_count(axis, 0)
    handler.__name__ = axis + "_Set_Idx_Dist"
    return handler

def _axis_set_idx_degdiv(axis):
    '''
    Toggles a currently-angular channel's jog-increment entry between
    meaning degrees directly ("Deg") and meaning "N divisions of a full
    circle" ("Div", i.e. 360/N degrees) - wired to the deg/div
    HAL_RadioButton pair every channel's row now has (previously only
    B's row did). Matches B's old hand-written B_Set_Idx_DegDiv exactly;
    only reachable in practice on a currently-angular channel, since
    that's the only case _load_panel_axis_controls makes this pair
    visible - harmless to register for every channel regardless.
    '''
    def handler(self, widget):
        print("=================================================")
        print("FUNCTION " + axis + "_Set_Idx_DegDiv")
        # <axis>_Idx_Deg / <axis>_Idx_Div are a GTK radio pair sharing
        # this "toggled" handler, so one click fires it twice (the button
        # going active, then its sibling going inactive). It used to flip
        # the mode on every call - two flips, net no change - so Div mode
        # could never engage. Same fix as Sp0_Set_Idx_DegDiv: ignore the
        # "going inactive" call and take the mode from the active button.
        if not widget.get_active():
            return
        mode = "Div" if Gtk.Buildable.get_name(widget).endswith("_Idx_Div") else "Deg"
        setattr(self, axis + "_Idx_DegDiv", mode)
        dist = getattr(self, axis + "_Idx_Dist")
        if mode == "Div":
            setattr(self, axis + "_Idx_Deg", round(360 / dist, 1) if dist else 0.0)
        else:
            setattr(self, axis + "_Idx_Deg", round(dist, 1))
        print(axis + "_Idx_Deg = " + str(getattr(self, axis + "_Idx_Deg")))
        print(axis + "_Idx_DegDiv = " + getattr(self, axis + "_Idx_DegDiv"))
        self._set_idx_count(axis, 0)
    handler.__name__ = axis + "_Set_Idx_DegDiv"
    return handler

def _axis_set_move_dist(axis):
    def handler(self, widget):
        print("=================================================")
        print("FUNCTION " + axis + "_Set_Move_Dist")
        setattr(self, axis + "_Move_Dist", widget.get_value())
        print(axis + "_Move_Dist = " + str(getattr(self, axis + "_Move_Dist")))
    handler.__name__ = axis + "_Set_Move_Dist"
    return handler



def _axis_set_ena(axis):
    def handler(self, widget, *args):
        _clear_ena_override(axis)
    handler.__name__ = axis + "_Set_Ena"
    return handler

for _axis in AXIS_SELECTION_LETTERS:
    # Column 12 sends gcode sign "-", column 13 sends "+" - empirically
    # verified independently for X/U/V/Z/W's Idx_Minus/Idx_Plus (live
    # testing showed all five linear axes moving the physically wrong
    # way relative to their correct icons - the same class of bug
    # already found and fixed for the spindles' Fwd/Rev and Idx_Fwd/
    # Idx_Rev via live halcmd pin tracing, see Sp0_Move_Fwd's docstring)
    # and for B's old Move_Idx_Fwd/Rev - every letter now uses the same
    # "<letter>_Idx_Plus"/"<letter>_Idx_Minus" naming, so the handler
    # name is computed directly rather than looked up.
    setattr(HandlerClass, _axis + "_Idx_Plus", _axis_idx_move(_axis, _axis + "_Idx_Plus", "-"))
    setattr(HandlerClass, _axis + "_Idx_Minus", _axis_idx_move(_axis, _axis + "_Idx_Minus", "+"))
    setattr(HandlerClass, _axis + "_Set_Feed", _axis_set_feed(_axis, _axis + "_Set_Feed"))
    setattr(HandlerClass, _axis + "_Set_Ena", _axis_set_ena(_axis))
    setattr(HandlerClass, _axis + "_Set_Idx_Dist", _axis_set_idx_dist(_axis))
    setattr(HandlerClass, _axis + "_Set_Idx_DegDiv", _axis_set_idx_degdiv(_axis))
    setattr(HandlerClass, _axis + "_Set_Move_Dist", _axis_set_move_dist(_axis))
del _axis
















# Scale/PID/Backlash editing lives entirely in Rosetta_Settings.py now (see
# that file and CLAUDE.md) - this file's main panel never reads or
# writes those live HAL pins.






def get_handlers(halcomp,builder,useropts):
    '''
    this function is called by gladevcp at import time (when this module is passed with '-u <modname>.py')

    return a list of object instances whose methods should be connected as callback handlers
    any method whose name does not begin with an underscore ('_') is a  callback candidate

    the 'get_handlers' name is reserved - gladevcp expects it, so do not change
    '''
    return [HandlerClass(halcomp,builder,useropts)]

#
