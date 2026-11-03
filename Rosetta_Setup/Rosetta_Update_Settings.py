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
# Rosetta                                                             #
#######################################################################
#                                                                     #
# File:                                                               #
#   Rosetta_Update_Settings.py                                        #
#                                                                     #
# Purpose:                                                            #
#   Run by Rosetta_Update.sh after the latest files have been pulled  #
#   from GitHub. Adds to this machine's settings file                 #
#   (~/Documents/RosettaSet_v1.ini) any setting that the              #
#   shipped starting file (Rosetta_Setup/RosettaSet_v1.ini) has but   #
#   this machine's file doesn't - so a new feature's settings appear  #
#   in the file with sensible starting values. It never changes or    #
#   removes a value that is already there.                            #
#                                                                     #
#   This relies on Rosetta_Setup/RosettaSet_v1.ini always holding     #
#   every setting the programs use, with its starting value - keep it #
#   up to date whenever a new setting is added.                       #
#                                                                     #
#   Also gives each axis its own Max Speed / Max Acceleration / PID   #
#   Max Output (and each spindle its Indexing Max Output) the first   #
#   time, worked out from Rosetta.ini and the machine's own stepgen   #
#   values (see fill_speed_limits) - raising a stepgen Max Vel / Max  #
#   Accel only if it's now too low, the one case where an existing    #
#   value is changed.                                                 #
#                                                                     #
#   Then runs the one-time machine steps in ONE_TIME_STEPS (see       #
#   run_one_time_steps). They're here, not in Rosetta_Update.sh,      #
#   because this program is started fresh after the pull, while the   #
#   copy of Rosetta_Update.sh already running keeps its old steps     #
#   until the next update.                                            #
#                                                                     #
#   Finally calls Rosetta_Report_Version.report_version() - unlike    #
#   the one-time steps, this runs every update (see that file's       #
#   header).                                                          #
#                                                                     #
# Version                                                             #
#   1.0 - 03 October 2026                                             #
#   1.1 - 07 October 2026 - raise too-low stepgen Max Accel           #
#   1.2 - 08 October 2026 - fill in each axis's speed limits, which   #
#         moved from Rosetta.ini to Rosetta Settings (replaces 1.1's  #
#         rule)                                                       #
#   1.3 - 20 October 2026 - runs one-time machine steps (folder       #
#         shortcuts)                                                  #
#   1.4 - 23 October 2026 - runs the serial number one-time step, and #
#         reports this machine's version every update                 #
#   1.5 - 02 November 2026 - renamed from REB_Update_Settings.py;     #
#         ends with Rosetta_Renaming.finish (moves an older machine   #
#         over to the Rosetta names)                                  #
#                                                                     #
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.             #
#                                                                     #
# The MIT/X Consortium License applies - see LICENSE.                 #
#######################################################################

import json
import os
import shutil
import subprocess
import sys
import time

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSETTA_INI_PATH = os.path.join(REPO_DIR, "Rosetta.ini")
sys.path.insert(0, os.path.join(REPO_DIR, "Rosetta_Display"))
import rosetta_settings_io
import Rosetta_Report_Version
import Rosetta_Renaming

SEED_PATH = os.path.join(REPO_DIR, "Rosetta_Setup", "RosettaSet_v1.ini")
# One-time steps for machines built before a feature the installer now
# sets up. Each script decides for itself whether it has already run.
ONE_TIME_STEPS = (
    os.path.join(REPO_DIR, "Rosetta_Setup", "Rosetta_Add_Shortcuts.sh"),       # 20 October 2026
    os.path.join(REPO_DIR, "Rosetta_Setup", "Rosetta_Set_Serial_Number.sh"),   # 23 October 2026
)
SETTINGS_PATH = rosetta_settings_io.SETTINGS_PATH

# Settings whose value is one whole choice, not a set of independent
# entries - if this machine has the key at all, it's left exactly as it
# is. Filling in single entries could break it: e.g. adding a missing
# channel from the starting file to channel_assignments can put the
# same axis on two channels, which makes every program ignore the whole
# assignment and fall back to the defaults.
WHOLE_VALUE_KEYS = ("channel_assignments", "limit_switches", "device_names")


def add_missing(user, seed, path=""):
    '''
    Copies into user every key seed has that user doesn't, recursing
    into dictionaries both have (e.g. each axis's settings), and returns
    the list of what was added. Existing values - including lists and
    WHOLE_VALUE_KEYS - are never changed.
    '''
    added = []
    for key, seed_value in seed.items():
        where = path + "/" + key if path else key
        if key not in user:
            user[key] = json.loads(json.dumps(seed_value))
            added.append(where)
        elif (isinstance(user[key], dict) and isinstance(seed_value, dict)
              and not (path == "" and key in WHOLE_VALUE_KEYS)):
            added += add_missing(user[key], seed_value, where)
    return added


# Each axis's stepgen ceiling (its saved "max_accel", which Rosetta.hal sets
# as the stepgen's maxaccel at startup, overriding Rosetta.ini's
# STEPGEN_MAXACCEL) must stay above the trajectory planner's limit
# (Rosetta.ini's MAX_ACCELERATION) or the stepgen can't keep up and the axis
# trips a following error on its first quick move. Rosetta.ini keeps a
# 1.5-2x margin; below 1.5x counts as too low.
AXIS_LETTERS = ("X", "Z", "B", "A", "C", "U", "V", "W")


def read_axis_planner(path=ROSETTA_INI_PATH):
    '''
    Returns {letter: (MAX_VELOCITY, MAX_ACCELERATION)} from each
    [AXIS_<letter>] section of Rosetta.ini - the starting point for an axis
    that has no Max Speed / Max Acceleration of its own yet.
    '''
    found = {}
    letter = None
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("["):
                letter = line[6:-1] if line.startswith("[AXIS_") and line[6:-1] in AXIS_LETTERS else None
                if letter:
                    found[letter] = {}
                continue
            if letter is None or "=" not in line or line.startswith("#"):
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in ("MAX_VELOCITY", "MAX_ACCELERATION") and key not in found[letter]:
                try:
                    found[letter][key] = float(value)
                except ValueError:
                    pass
    return {k: (v["MAX_VELOCITY"], v["MAX_ACCELERATION"])
            for k, v in found.items() if len(v) == 2}


def fill_speed_limits(user, planner):
    '''
    Gives every axis that doesn't have one yet its Max Speed, Max
    Acceleration and PID Max Output, and every spindle its Indexing Max
    Output (rosetta_settings_io.fill_missing_limits). Must run before
    add_missing, so these come from this machine's own values rather
    than the starting file's. Returns a list of what was set or raised.
    '''
    changed = []
    system = user.get("measurement_system", "Imperial")
    for axis_id, entry in sorted(user.get("axes", {}).items()):
        if not isinstance(entry, dict):
            continue
        if axis_id in rosetta_settings_io.SPINDLE_IDS:
            notes = rosetta_settings_io.fill_missing_limits(axis_id, entry)
        elif axis_id in planner:
            notes = rosetta_settings_io.fill_missing_limits(axis_id, entry, planner[axis_id], system)
        else:
            continue
        changed += [axis_id + " " + note for note in notes]
    return changed


def add_notes_to_other_files(main_path):
    '''
    Gives every other Rosetta settings or export file in the
    settings folder (~/Documents) the explanatory notes - "Save All
    Settings As..." copies and "Save Subset" exports saved before the
    notes existed. Only *.ini files that read as a settings/export file
    (a JSON object with "axes") are touched, and only if the notes are
    missing; the settings themselves are written back unchanged, checked
    before the file is replaced. Backups (*.ini.bak-...) don't end in
    .ini, so they're left alone. A RosettaSet file that can't be read is
    reported and left as it is.
    '''
    folder = os.path.dirname(main_path)
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return
    for name in names:
        path = os.path.join(folder, name)
        if not name.endswith(".ini") or os.path.abspath(path) == os.path.abspath(main_path):
            continue
        try:
            with open(path, "r") as f:
                raw = f.read()
            data = rosetta_settings_io.parse_settings_text(raw)
        except (OSError, ValueError, UnicodeDecodeError) as e:
            if "RosettaSet" in name:
                print("NOTE: " + name + " could not be read (" + str(e).split(":")[0]
                      + ") - left as it is.")
            continue
        if not isinstance(data, dict) or "axes" not in data:
            continue
        new = rosetta_settings_io.settings_text(data)
        if new == raw or rosetta_settings_io.SETTINGS_HEADER in raw or rosetta_settings_io.EXPORT_HEADER in raw:
            continue
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                f.write(new)
            with open(tmp_path, "r") as f:
                if rosetta_settings_io.parse_settings_text(f.read()) != data:
                    raise ValueError("settings changed on rewrite")
            os.replace(tmp_path, path)
            print("Added the explanatory notes to " + name)
        except (OSError, ValueError) as e:
            print("NOTE: could not add notes to " + name + " (" + str(e) + ") - left as it is.")
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def run_one_time_steps():
    '''
    Runs each ONE_TIME_STEPS script. A failure is reported but doesn't
    stop the update.
    '''
    for script in ONE_TIME_STEPS:
        sys.stdout.flush()      # keep this program's messages in order
        try:
            if subprocess.call([script]) != 0:
                print("WARNING: " + os.path.basename(script) + " reported a problem - see above.")
        except OSError as e:
            print("WARNING: could not run " + os.path.basename(script) + ": " + str(e))


def main():
    result = update_settings()
    # Before the version report below, so it carries the new serial
    # prefix (REB003 -> Rosetta003); finish() at the end checks again.
    Rosetta_Renaming.serial_prefix()
    run_one_time_steps()
    # Runs every update (not a one-time step) - after the serial-number
    # step above, so a number set just now is included in this report.
    Rosetta_Report_Version.report_version()
    # Last: a machine built before the Rosetta renaming (02 November
    # 2026) is moved over to the new names - this renames the repo
    # folder itself, so nothing after it may use REPO_DIR.
    Rosetta_Renaming.finish(REPO_DIR)
    return result


def update_settings():
    print("Checking " + SETTINGS_PATH + " for new settings")

    try:
        with open(SEED_PATH, "r") as f:
            seed = rosetta_settings_io.parse_settings_text(f.read())
    except (OSError, ValueError) as e:
        print("ERROR: could not read " + SEED_PATH + ": " + str(e))
        return 1

    if not os.path.exists(SETTINGS_PATH):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        shutil.copyfile(SEED_PATH, SETTINGS_PATH)
        print("No settings file yet - copied the starting settings into place.")
        return 0

    with open(SETTINGS_PATH, "r") as f:
        raw = f.read()
    if raw.lstrip().startswith(("<?xml", "<settings")):
        # Old XML format: let the normal reader convert it (it backs up
        # the original first and writes the JSON version), then carry on.
        rosetta_settings_io.load_settings()
        with open(SETTINGS_PATH, "r") as f:
            raw = f.read()
    try:
        user = rosetta_settings_io.parse_settings_text(raw)
    except ValueError as e:
        # Never replace a file we can't read - it may hold the only copy
        # of this machine's calibration.
        print("ERROR: " + SETTINGS_PATH + " could not be read (" + str(e) + ") - left unchanged.")
        return 1
    if not isinstance(user, dict):
        print("ERROR: " + SETTINGS_PATH + " is not a settings file - left unchanged.")
        return 1

    try:
        raised = fill_speed_limits(user, read_axis_planner())
    except OSError as e:
        print("WARNING: could not read " + ROSETTA_INI_PATH + " (" + str(e) + ") - speed limits not filled in.")
        raised = []
    added = add_missing(user, seed)
    # A file from before the explanatory notes (08 October 2026 and
    # earlier) gets them now, rather than at the next program save.
    needs_notes = rosetta_settings_io.SETTINGS_HEADER not in raw
    add_notes_to_other_files(SETTINGS_PATH)
    if not added and not raised and not needs_notes:
        print("Settings file is up to date - nothing to add.")
        return 0

    backup = SETTINGS_PATH + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(SETTINGS_PATH, backup)
    rosetta_settings_io.save_settings(user, SETTINGS_PATH)
    if added:
        print("Added %d new setting(s), using the starting values:" % len(added))
        for where in added:
            print("    " + where)
    if raised:
        print("Set up %d speed limit value(s) (now in Rosetta Settings):" % len(raised))
        for what in raised:
            print("    " + what)
    if needs_notes:
        print("Added the notes explaining what the settings file is.")
    print("Previous settings file saved as " + backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
