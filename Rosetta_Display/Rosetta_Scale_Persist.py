#!/usr/bin/env python3
"""
Rosetta_Scale_Persist.py

At LinuxCNC shutdown, reads the current stepgen position-scale value
for each Rosetta axis directly from HAL and writes it back
into REB_Settings_v1.ini, updating only that axis's "scale" value. The
rest of the file is left untouched.

Also persists each axis's/spindle loop's live P/I/D/FF0/FF1/FF2 pid.*
gains the same way, into that axis's "pid" entry (or "pid_pos"/
"pid_vel" for the two spindle loops) - see PID_SPINDLE_LOOPS below.
These gains are set live from REB_Settings_v1.ini by Rosetta_main.py's
_load_pid_settings() at Settings-tab load and by each PID spin
button's value-changed handler while running (see Rosetta.hal for why
they're no longer set from Rosetta.ini directly), so this is the only place
that carries a retuned gain forward into the next session - exactly
mirroring how scale already worked before PID gains were added to this
file.

Doesn't persist backlash: Rosetta_Settings.py saves it to RosettaSet_v1.ini the
moment it's changed. (Until 24 September 2026 this read a
joint.N.backlash HAL parameter here, which LinuxCNC 2.9 doesn't have -
every shutdown logged "pin or parameter 'joint.N.backlash' not found"
and nothing was saved. Its live replacement, inihal's ini.N.backlash,
belongs to milltask, which may already be gone by the time this runs.)

Invoked from Rosetta_Shutdown.hal:
    loadusr -w python3 Rosetta_Display/Rosetta_Scale_Persist.py

------------------------------------------------------------------
Any-role/any-channel generalization (13 September 2026)
------------------------------------------------------------------
Any of 10 roles (8 axis letters or 2 spindles) can now be assigned to
any of the 8 physical channels - see CLAUDE.md and Rosetta_Setup/
Rosetta_Generate_Local_Ini.py, whose RoleLayout this script's own
RoleLayout mirrors (duplicated rather than imported, per this
codebase's usual convention for small maps/logic shared only at the
value level across independent scripts). Sp0/Sp1 and the 8 axis
letters are now restored/persisted through the exact same single loop
over CHANNEL_ROLES, resolved via RoleLayout.channel_of - no more
separate "spindles are always present" special case, matching how
Rosetta_Settings_Restore.py's load-side counterpart was fixed at the same
time.
"""

import os
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
# exactly (must match, since this script needs to read back the joint
# number that script's Rosetta.local.ini generation already assigned for
# this session).
JOINT_NUMBER_CANONICAL_ORDER = ("X", "Z", "B", "U", "V", "W", "A", "C")

SETTINGS_PATH = rosetta_settings_io.SETTINGS_PATH


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
    letter's joint.N now is (see JOINT_NUMBER_CANONICAL_ORDER).
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

# Each spindle's indexing (M19) position loop - see
# Rosetta_Settings_Restore.py.
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


def get_scale(stepgen_ch):
    hal_pin = _stepgen_pin(stepgen_ch, ".position-scale")
    result = subprocess.run(
        ["halcmd", "getp", hal_pin],
        check=True,
        capture_output=True,
        text=True
    )
    return float(result.stdout.strip())


def get_stepgen_max(stepgen_ch, param):
    hal_suffix = ".maxvel" if param == "max_vel" else ".maxaccel"
    hal_pin = _stepgen_pin(stepgen_ch, hal_suffix)
    result = subprocess.run(
        ["halcmd", "getp", hal_pin],
        check=True,
        capture_output=True,
        text=True
    )
    return float(result.stdout.strip())


def get_pid_gain(hal_component, param):
    hal_pin = hal_component + "." + PID_PARAM_PIN[param]
    result = subprocess.run(
        ["halcmd", "getp", hal_pin],
        check=True,
        capture_output=True,
        text=True
    )
    return float(result.stdout.strip())


def get_pid_max_output(hal_component):
    result = subprocess.run(
        ["halcmd", "getp", hal_component + ".maxoutput"],
        check=True,
        capture_output=True,
        text=True
    )
    return float(result.stdout.strip())


def main():
    settings = rosetta_settings_io.load_settings()
    axes = settings.setdefault("axes", {})

    for role in CHANNEL_ROLES:
        channel_id = _ROLE_LAYOUT.channel_of.get(role)
        if channel_id is None:
            # Not currently assigned to any channel this session -
            # nothing live to read, leave its persisted value untouched.
            continue

        try:
            value = get_scale(channel_id)
        except subprocess.CalledProcessError as e:
            print("Error reading scale for axis " + role + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
            sys.exit(1)
        else:
            axes.setdefault(role, {})["scale"] = value
            print("Saved " + role + " scale = " + str(value))

        for param in ("max_vel", "max_accel"):
            try:
                value = get_stepgen_max(channel_id, param)
            except subprocess.CalledProcessError as e:
                print("Error reading " + param + " for axis " + role + ": " + e.stderr)
                continue
            except FileNotFoundError:
                print("halcmd not found - is the LinuxCNC environment sourced?")
                sys.exit(1)
            axes.setdefault(role, {})[param] = value
            print("Saved " + role + " " + param + " = " + str(value))

        if role in AXIS_SELECTION_LETTERS:
            values = {}
            try:
                for param in PID_PARAMS:
                    values[param] = get_pid_gain("pid." + role.lower(), param)
            except subprocess.CalledProcessError as e:
                print("Error reading PID gains for axis " + role + ": " + e.stderr)
            except FileNotFoundError:
                print("halcmd not found - is the LinuxCNC environment sourced?")
                sys.exit(1)
            else:
                axes.setdefault(role, {}).setdefault("pid", {}).update(values)
                print("Saved " + role + " PID gains = " + str(values))
        else:
            for suffix, hal_component in PID_SPINDLE_LOOPS[role].items():
                block_tag = "pid_pos"
                values = {}
                try:
                    for param in PID_PARAMS:
                        values[param] = get_pid_gain(hal_component, param)
                except subprocess.CalledProcessError as e:
                    print("Error reading " + suffix + " PID gains for " + role
                          + ": " + e.stderr)
                    continue
                except FileNotFoundError:
                    print("halcmd not found - is the LinuxCNC environment sourced?")
                    sys.exit(1)
                axes.setdefault(role, {}).setdefault(block_tag, {}).update(values)
                print("Saved " + role + " " + suffix + " PID gains = " + str(values))

        if role in AXIS_SELECTION_LETTERS:
            key, hal_component = "pid_max_output", "pid." + role.lower()
        else:
            key, hal_component = "index_max_output", PID_SPINDLE_LOOPS[role]["Pos"]
        try:
            value = get_pid_max_output(hal_component)
        except subprocess.CalledProcessError as e:
            print("Error reading " + key + " for axis " + role + ": " + e.stderr)
        except FileNotFoundError:
            print("halcmd not found - is the LinuxCNC environment sourced?")
            sys.exit(1)
        else:
            axes.setdefault(role, {})[key] = value
            print("Saved " + role + " " + key + " = " + str(value))

    try:
        rosetta_settings_io.save_settings(settings)
    except OSError as e:
        print("Could not write " + SETTINGS_PATH + ": " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
