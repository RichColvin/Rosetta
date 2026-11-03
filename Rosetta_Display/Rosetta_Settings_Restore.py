#!/usr/bin/env python3
"""
Rosetta_Settings_Restore.py

At LinuxCNC startup, reads RosettaSet_v1.ini and pushes each Rosetta
axis's persisted stepgen position-scale, maxvel/maxaccel,
and P/I/D/FF0/FF1/FF2 pid.* gains onto the live HAL parameters those
values actually live on. (Not backlash - see the note at the end of
this docstring.) This is the load-side counterpart to Rosetta_Display/
Rosetta_Scale_Persist.py (which does the same job in reverse, at shutdown)
- together they're what makes a value retuned in Rosetta_Settings survive
to the next session.

Why this needs to exist as its own step: none of these are ordinary
HAL pins wired to Rosetta.ini through the usual [JOINT_n]/[AXIS_*]
INI-substitution mechanism - they're HAL PARAMETERS on the hm2_7i92
stepgen/pid/motion components, which reset to that component's own
hard default (position-scale/maxvel/maxaccel/PID gains all come up as
0 or 1, not this machine's real values) every time hm2_7i92/pid/motion
are freshly loaded. Before 4 September 2026, the embedded AXIS Settings
tab's own startup (Rosetta_main.py's _load_scale_settings/_load_pid_
settings/_load_backlash_settings/_load_max_vel_accel_settings) is what
pushed these values onto HAL every time LinuxCNC started - that ran
automatically because the tab was embedded in AXIS itself. Once the
Settings tab was replaced by the standalone Rosetta_Settings program (which
must run BEFORE LinuxCNC, and is blocked from running while LinuxCNC is
running - see Rosetta_Settings.py's _linuxcnc_is_running), nothing was left
to do this restore at a normal LinuxCNC startup at all - confirmed live
4 September 2026 (position-scale silently sitting at hm2's own default
of 1 after a restart, discovered only because a commanded move produced
far less physical travel than expected). This script is the fix.

Invoked from Rosetta.hal, after hm2_7i92/pid/motion are all loaded:
    loadusr -w python3 Rosetta_Display/Rosetta_Settings_Restore.py

------------------------------------------------------------------
Any-role/any-channel generalization (13 September 2026)
------------------------------------------------------------------
Any of 10 roles (8 axis letters or 2 spindles) can now be assigned to
any of the 8 physical channels - see CLAUDE.md and Rosetta_Setup/
Rosetta_Generate_Local_Ini.py, whose RoleLayout this script's
_compute_role_layout mirrors (duplicated rather than imported - this
script and the generator are independent processes, see AXIS_STEPGEN's
old comment for why small maps/logic like this stay duplicated across
scripts in this codebase).

Backlash restore is now axis-letter-only. Before this generalization,
spindles had a fixed (if largely theoretical) joint number - now that
[KINS]JOINTS dynamically ranges 6-8 depending how many letters are
active, joint numbers are reassigned fresh each launch and a spindle
has no joint number of its own at all ([TRAJ]SPINDLES is entirely
separate from [KINS]JOINTS in LinuxCNC's kinematics model - see
CLAUDE.md). Restoring backlash for a spindle against a stale/guessed
joint number risked writing to whatever REAL axis letter now actually
owns that joint number instead - silently corrupting a different
axis's backlash. Dropped rather than risk that.

Backlash restore removed entirely, 24 September 2026: it wrote
joint.N.backlash, which doesn't exist in LinuxCNC 2.9 (every launch
logged "parameter or pin 'joint.N.backlash' not found"), so no
persisted backlash ever reached LinuxCNC. Backlash is an INI value
there - Rosetta_Setup/Rosetta_Generate_Local_Ini.py's _overlay_backlash now
writes each active letter's persisted value into its [JOINT_n]BACKLASH
at launch, and Rosetta_Settings.py changes it live through inihal's
ini.N.backlash pin.
"""

import subprocess
import sys

import rosetta_settings_io

# The 8 axis letters (Y removed - not used on this machine, LATHE=1)
# and the 2 spindles - the 10 possible roles a channel can be assigned.
AXIS_SELECTION_LETTERS = ("X", "Z", "U", "V", "W", "A", "B", "C")
SPINDLE_IDS = ("Sp0", "Sp1")
CHANNEL_ROLES = AXIS_SELECTION_LETTERS + SPINDLE_IDS

# Channel id ("00".."07") -> the role Rosetta.ini/Rosetta.hal ship with by
# default. Mirrors rosetta_settings_io.py's own CHANNEL_DEFAULT_ROLE.
# Two-box hardware (14 October 2026): the 10 channels, their defaults
# and which card/stepgen each is on come from rosetta_settings_io, so this
# program numbers roles and joints exactly as Rosetta_Generate_Local_Ini.py
# did for this session.
CHANNEL_DEFAULT_ROLE = rosetta_settings_io.CHANNEL_DEFAULT_ROLE

# Canonical joint-numbering order for active axis letters - mirrors
# Rosetta_Setup/Rosetta_Generate_Local_Ini.py's JOINT_NUMBER_CANONICAL_ORDER
# exactly (must match, since this script needs to compute the SAME
# live joint number that script's Rosetta.local.ini generation already
# assigned for this session).
JOINT_NUMBER_CANONICAL_ORDER = ("X", "Z", "B", "U", "V", "W", "A", "C")


def _read_channel_assignments():
    '''
    The persisted channel -> role map, completed to all 10 channels
    (rosetta_settings_io.complete_channel_assignments) - the same map
    Rosetta_Generate_Local_Ini.py used for this session.
    '''
    return rosetta_settings_io.complete_channel_assignments(
        rosetta_settings_io.load_settings().get("channel_assignments"))


def _stepgen_pin(channel_id, suffix):
    '''A channel's stepgen HAL pin on whichever card it's on (rosetta_settings_io.channel_hal).'''
    card, stepgen = rosetta_settings_io.channel_hal(channel_id)
    return card + ".stepgen." + stepgen + suffix


class RoleLayout(object):
    '''
    Mirrors Rosetta_Setup/Rosetta_Generate_Local_Ini.py's own RoleLayout - which
    of the 10 roles are active (assigned to some channel) this session,
    which channel each one is on, and which joint number an active axis
    letter's [JOINT_n]/joint.N now is (see JOINT_NUMBER_CANONICAL_ORDER)
    - the same computation that script already used to generate this
    session's Rosetta.local.ini/Rosetta.local.hal, needed again here to know
    where to push each role's restored values.
    '''
    def __init__(self, assignments):
        # Only channels in use count - the expansion box's 06-09 only
        # while it's connected - exactly as Rosetta_Generate_Local_Ini.py's
        # RoleLayout, so joint numbers match this session's HAL.
        active = rosetta_settings_io.active_channels(rosetta_settings_io.load_settings())
        self.channel_of = {}
        for channel_id, role in assignments.items():
            if channel_id in active:
                self.channel_of[role] = channel_id

        active_letters = [l for l in JOINT_NUMBER_CANONICAL_ORDER if l in self.channel_of]
        self.joint_number = {letter: i for i, letter in enumerate(active_letters)}


_ROLE_LAYOUT = RoleLayout(_read_channel_assignments())

# Each spindle's indexing (M19) position loop. (Their velocity loops,
# pid.s0/pid.s1, were removed 08 October 2026 - their output never
# reached the stepgen.)
PID_SPINDLE_LOOPS = {
    "Sp0": {"Pos": "pid.p0"},
    "Sp1": {"Pos": "pid.p1"},
}
PID_PARAM_PIN = {
    "P":   "Pgain",
    "I":   "Igain",
    "D":   "Dgain",
    "FF0": "FF0",
    "FF1": "FF1",
    "FF2": "FF2",
}
PID_PARAMS = ("P", "I", "D", "FF0", "FF1", "FF2")


def _setp(hal_pin, value):
    subprocess.run(
        ["halcmd", "setp", hal_pin, str(value)],
        check=True,
        capture_output=True,
        text=True
    )


def set_scale(stepgen_ch, value):
    _setp(_stepgen_pin(stepgen_ch, ".position-scale"), value)


def set_stepgen_max(stepgen_ch, param, value):
    hal_suffix = ".maxvel" if param == "max_vel" else ".maxaccel"
    _setp(_stepgen_pin(stepgen_ch, hal_suffix), value)


def set_pid_gain(hal_component, param, value):
    _setp(hal_component + "." + PID_PARAM_PIN[param], value)


def set_pid_max_output(hal_component, value):
    _setp(hal_component + ".maxoutput", value)


def main():
    '''
    Restores exactly what Rosetta_Scale_Persist.py's main() persists, in
    the same order, keyed the same way: all 10 CHANNEL_ROLES, resolved
    through _ROLE_LAYOUT.channel_of, skipping any role not currently
    assigned to a channel this session (nothing live to push it onto).
    Backlash isn't restored here - see this file's own header.
    '''
    settings = rosetta_settings_io.load_settings()
    axes = settings.get("axes", {})

    def restore_scale(axis_id, stepgen_ch):
        axis_entry = axes.get(axis_id)
        if axis_entry is None or "scale" not in axis_entry:
            print("No stored scale found for axis " + axis_id)
            return
        value = float(axis_entry["scale"])
        try:
            set_scale(stepgen_ch, value)
            print("Restored " + axis_id + " scale = " + str(value))
        except subprocess.CalledProcessError as e:
            print("Error restoring scale for axis " + axis_id + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
            sys.exit(1)

    def restore_stepgen_max(axis_id, stepgen_ch):
        axis_entry = axes.get(axis_id)
        if axis_entry is None:
            return
        for param in ("max_vel", "max_accel"):
            if param not in axis_entry:
                print("No stored " + param + " found for axis " + axis_id)
                continue
            value = float(axis_entry[param])
            try:
                set_stepgen_max(stepgen_ch, param, value)
                print("Restored " + axis_id + " " + param + " = " + str(value))
            except subprocess.CalledProcessError as e:
                print("Error restoring " + param + " for axis " + axis_id + ": " + e.stderr)
            except FileNotFoundError:
                print("halcmd not found - is the LinuxCNC environment sourced?")
                sys.exit(1)

    def restore_pid(axis_id, block_tag, hal_component):
        axis_entry = axes.get(axis_id)
        if axis_entry is None:
            return
        pid_block = axis_entry.get(block_tag)
        if pid_block is None:
            print("No \"" + block_tag + "\" entry found for axis " + axis_id)
            return
        for param in PID_PARAMS:
            if param not in pid_block:
                print("No stored " + param + " found for " + axis_id + " " + block_tag)
                continue
            value = float(pid_block[param])
            try:
                set_pid_gain(hal_component, param, value)
            except subprocess.CalledProcessError as e:
                print("Error restoring " + param + " for " + axis_id + " " + block_tag + ": " + e.stderr)
            except FileNotFoundError:
                print("halcmd not found - is the LinuxCNC environment sourced?")
                sys.exit(1)
        print("Restored " + axis_id + " " + block_tag + " PID gains = " + str(pid_block))

    def restore_max_output(axis_id, key, hal_component):
        # An axis's PID Max Output / a spindle's Indexing Max Output
        # (Rosetta Settings' advanced rows). Rosetta.hal sets each from Rosetta.ini
        # first; this replaces it with the machine's own value.
        axis_entry = axes.get(axis_id)
        if axis_entry is None or key not in axis_entry:
            print("No stored " + key + " found for axis " + axis_id)
            return
        value = float(axis_entry[key])
        try:
            set_pid_max_output(hal_component, value)
            print("Restored " + axis_id + " " + key + " = " + str(value))
        except subprocess.CalledProcessError as e:
            print("Error restoring " + key + " for axis " + axis_id + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
            sys.exit(1)

    for role in CHANNEL_ROLES:
        channel_id = _ROLE_LAYOUT.channel_of.get(role)
        if channel_id is None:
            # Not currently assigned to any channel this session -
            # nothing live to push it onto.
            print(role + " is not currently assigned to a channel - skipping")
            continue

        restore_scale(role, channel_id)
        restore_stepgen_max(role, channel_id)

        if role in AXIS_SELECTION_LETTERS:
            restore_pid(role, "pid", "pid." + role.lower())
            restore_max_output(role, "pid_max_output", "pid." + role.lower())
        else:
            hal_component = PID_SPINDLE_LOOPS[role]["Pos"]
            restore_pid(role, "pid_pos", hal_component)
            restore_max_output(role, "index_max_output", hal_component)


if __name__ == "__main__":
    main()
