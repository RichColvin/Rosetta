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
#   Rosetta_Checkout.py                                               #
#                                                                     #
# Purpose:                                                            #
#   Bench checkout of a newly built system, run from                  #
#   Rosetta_Checkout.sh with a test motor on every channel (6 on the  #
#   base box, 4 more on the expansion box). Runs the same test twice, #
#   with LinuxCNC restarted in between:                               #
#     Pass A - the default roles (00 X, 01 Z, 02 B, 03 W, 04 Sp0,     #
#              05 Sp1, 06 U, 07 V, 08 A, 09 C);                       #
#     Pass B - every role moved 3 channels along (base box only:      #
#              within 00-05; with the expansion box: across all 10,   #
#              so roles change cards), putting spindles where axes    #
#              were and angular axes where linear ones were.          #
#   Each pass's G-code turns each channel's motor channel+1 times     #
#   forward and back, one channel at a time (the tester counts the    #
#   turns on the labelled motor), indexes each spindle in quarter     #
#   turns, then moves every axis together while the spindles run.     #
#   After each pass the tester records Pass / Fail / Skip for each    #
#   channel; everything goes into a dated log.                        #
#                                                                     #
#   For the test, every axis gets a scale of one motor turn per unit  #
#   (one inch or mm, or 360 degrees) and safe speeds, and the limit   #
#   jacks and E-stop button are switched off (a bench has no          #
#   switches plugged in). The machine's own settings file is backed   #
#   up first and ALWAYS put back at the end - also after Ctrl+C, a    #
#   failure, or (next time this runs) a power cut part way through.   #
#                                                                     #
#   Arguments:                                                        #
#     --steps-per-rev N   motor steps per turn as the drives are set  #
#                         (default 6400: 200 steps x 32 microsteps)   #
#     --pass A|B          run only that pass                          #
#     --dry-run           write the test files and the record sheet   #
#                         to the output folder only - no settings     #
#                         change, no LinuxCNC                         #
#     --settings PATH     settings file to read (dry run testing)     #
#     --out DIR           where the run folders go                    #
#                         (default ~/Documents/Checkout)              #
#                                                                     #
# Version                                                             #
#   1.0 - 18 October 2026                                             #
#                                                                     #
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.             #
#                                                                     #
# The MIT/X Consortium License applies - see LICENSE.                 #
#######################################################################

import argparse
import copy
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_DIR, "Rosetta_Display"))
import rosetta_settings_io

GENERATOR = os.path.join(REPO_DIR, "Rosetta_Setup", "Rosetta_Generate_Local_Ini.py")
LOCAL_INI_PATH = os.path.join(REPO_DIR, "Rosetta.local.ini")
SETTINGS_PATH = rosetta_settings_io.SETTINGS_PATH
DEFAULT_OUT_DIR = os.path.expanduser("~/Documents/Checkout")

# A file left next to the settings file while the test settings are in
# place, naming the backup - so a run cut short by a power cut is put
# right the next time this program starts.
RESTORE_MARKER = os.path.join(os.path.dirname(SETTINGS_PATH), "Rosetta_Checkout_restore.json")

DEFAULT_STEPS_PER_REV = 6400

# How far the roles move along the channels for pass B.
PASS_B_SHIFT = 3

# Test speeds, in motor turns per second, kept well inside what a bare
# DM542T and motor do without stalling.
AXIS_TURNS_PER_SEC = 0.8        # each channel on its own
GROUP_SECONDS = 2.0             # all axes together, one turn each way
SPINDLE_RPM = 60                # 1 turn per second
SPINDLE_SECONDS_PER_TURN = 60.0 / SPINDLE_RPM


def say(text=""):
    print(text, flush=True)


def ask(prompt, choices=None, default=None):
    '''Asks until the answer is one of choices (lower case), or any text when choices is None.'''
    while True:
        answer = input(prompt).strip()
        if not answer and default is not None:
            return default
        if choices is None:
            return answer
        if answer.lower() in choices:
            return answer.lower()
        say("    Please answer " + " / ".join(choices) + ".")


def linuxcnc_running():
    for name in ("linuxcncsvr", "milltask"):
        if subprocess.run(["pgrep", "-x", name], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0:
            return True
    return False


def software_version():
    try:
        out = subprocess.run(["git", "-C", REPO_DIR, "log", "-1", "--oneline"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        branch = subprocess.run(["git", "-C", REPO_DIR, "branch", "--show-current"],
                                capture_output=True, text=True, timeout=10).stdout.strip()
        return (branch + " " + out).strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


# ----------------------------------------------------------------------
# Layouts

def layout_for(pass_name, expansion_box):
    '''channel id -> role for this pass: all 10 channels, as the settings file needs.'''
    default = rosetta_settings_io.CHANNEL_DEFAULT_ROLE
    if pass_name == "A":
        return dict(default)
    channels = list(rosetta_settings_io.CHANNEL_IDS if expansion_box else rosetta_settings_io.BASE_CHANNELS)
    layout = dict(default)
    for i, channel in enumerate(channels):
        layout[channel] = default[channels[(i + PASS_B_SHIFT) % len(channels)]]
    return layout


def tested_channels(expansion_box):
    return list(rosetta_settings_io.CHANNEL_IDS if expansion_box else rosetta_settings_io.BASE_CHANNELS)


def is_spindle(role):
    return role in rosetta_settings_io.SPINDLE_IDS


def is_angular(role):
    return role in ("A", "B", "C")


def turns_for(channel):
    return int(channel) + 1


def turns_text(n):
    return "%d turn%s" % (n, "" if n == 1 else "s")


def spindle_numbers(layout, channels):
    '''role -> LinuxCNC spindle number, as Rosetta_Generate_Local_Ini.py numbers them.'''
    active = [layout[c] for c in channels]
    return {role: n for n, role in enumerate(s for s in ("Sp0", "Sp1") if s in active)}


# ----------------------------------------------------------------------
# Test settings

def test_axis_values(role, steps_per_rev):
    '''The scale, limits and PID a role gets for the test.'''
    if is_spindle(role):
        return {"scale": steps_per_rev, "backlash": 0.0,
                "max_vel": 2.0, "max_accel": 2.0, "index_max_output": 1.0,
                "pid_pos": rosetta_settings_io.default_pid(role)}
    if is_angular(role):
        unit = 360.0                 # degrees per turn
    else:
        unit = 1.0                   # inch or mm per turn
    speed = 1.0 * unit               # 1 turn/sec
    accel = 2.0 * unit               # 2 turns/sec^2
    return {"scale": round(steps_per_rev / unit, 6), "backlash": 0.0,
            "max_speed": speed, "max_acceleration": accel,
            "max_vel": round(speed * rosetta_settings_io.STEPGEN_VEL_FACTOR, 6),
            "max_accel": round(accel * rosetta_settings_io.STEPGEN_ACCEL_FACTOR, 6),
            "pid_max_output": round(speed * rosetta_settings_io.PID_OUTPUT_FACTOR, 6),
            "pid": rosetta_settings_io.default_pid(role)}


def test_settings(original, layout, expansion_box, steps_per_rev):
    settings = copy.deepcopy(original)
    settings["channel_assignments"] = dict(layout)
    settings["expansion_box"] = bool(expansion_box)
    # Nothing is plugged into the jacks on the bench: an unplugged
    # normally-closed switch or E-stop reads as tripped.
    settings["limit_switches"] = {}
    settings["estop_button"] = False
    axes = settings.setdefault("axes", {})
    for role in rosetta_settings_io.CHANNEL_ROLES:
        entry = axes.setdefault(role, {})
        entry.update(test_axis_values(role, steps_per_rev))
    return settings


# ----------------------------------------------------------------------
# Test program

def fmt(value):
    return ("%.4f" % value).rstrip("0").rstrip(".")


def axis_feed(role):
    '''Feed (units/min) for AXIS_TURNS_PER_SEC on this role.'''
    unit = 360.0 if is_angular(role) else 1.0
    return AXIS_TURNS_PER_SEC * unit * 60.0


def test_program(serial, pass_name, layout, channels):
    spindle_no = spindle_numbers(layout, channels)
    lines = [
        "(Rosetta checkout - S/N %s - pass %s)" % (serial, pass_name),
        "(Written by Rosetta_Checkout.py - one motor turn = 1 unit / 360 degrees)",
        # G8: X in radius, so X1 is one turn (lathe diameter mode, G7,
        # would halve it).
        "G94 G90 G8",
        "(MSG,Pass %s: each channel in turn, then everything together. Before each step the program pauses - read the message, watch that motor, press Resume.)" % pass_name,
        "M0",
    ]
    for channel in channels:
        role = layout[channel]
        turns = turns_for(channel)
        if is_spindle(role):
            n = spindle_no[role]
            dwell = fmt(turns * SPINDLE_SECONDS_PER_TURN)
            lines += [
                "",
                "(MSG,Channel %s - %s: about %s forward, about %d in reverse, then 4 quarter turns. Press Resume.)" % (channel, role, turns_text(turns), turns),
                "M0",
                "M3 S%d $%d" % (SPINDLE_RPM, n),
                "G4 P%s" % dwell,
                "M5 $%d" % n,
                "G4 P1",
                "M4 S%d $%d" % (SPINDLE_RPM, n),
                "G4 P%s" % dwell,
                "M5 $%d" % n,
                "G4 P1",
            ]
            for angle in (90, 180, 270, 0):
                lines += ["M19 R%d $%d" % (angle, n), "G4 P1"]
            lines.append("M5 $%d" % n)
        else:
            distance = turns * (360 if is_angular(role) else 1)
            lines += [
                "",
                "(MSG,Channel %s - %s: %s forward, then %d back. Press Resume.)" % (channel, role, turns_text(turns), turns),
                "M0",
                "G91 G1 %s%s F%s" % (role, fmt(distance), fmt(axis_feed(role))),
                "G4 P0.5",
                "G1 %s-%s" % (role, fmt(distance)),
                "G90",
            ]

    axes = [layout[c] for c in channels if not is_spindle(layout[c])]
    spindles = sorted(spindle_no.items(), key=lambda kv: kv[1])
    if axes:
        forward = " ".join("%s%s" % (r, 360 if is_angular(r) else 1) for r in axes)
        back = " ".join("%s-%s" % (r, 360 if is_angular(r) else 1) for r in axes)
        lines += [
            "",
            "(MSG,All together: every axis turns once forward and once back, all finishing together, while the spindles run. Press Resume.)",
            "M0",
        ]
        for role, n in spindles:
            lines.append("M3 S%d $%d" % (SPINDLE_RPM if n == 0 else SPINDLE_RPM // 2, n))
        lines += [
            "G4 P1",
            # Inverse time: F = 1 / minutes for the move, so every axis
            # starts and finishes together.
            "G91 G93 G1 %s F%s" % (forward, fmt(60.0 / GROUP_SECONDS)),
            "G1 %s F%s" % (back, fmt(60.0 / GROUP_SECONDS)),
            "G94 G90",
        ]
        for role, n in spindles:
            lines.append("M5 $%d" % n)
    lines += [
        "",
        "(MSG,Pass %s finished. Close LinuxCNC and record the results in the terminal.)" % pass_name,
        "M2",
        "",
    ]
    return "\n".join(lines)


def record_sheet(pass_name, layout, channels):
    rows = ["Pass %s - what each motor should do:" % pass_name,
            "",
            "  Channel  Role  Box        Should"]
    for channel in channels:
        role = layout[channel]
        box = "base" if channel in rosetta_settings_io.BASE_CHANNELS else "expansion"
        turns = turns_for(channel)
        if is_spindle(role):
            should = "about %s forward, %d in reverse, then 4 quarter turns" % (turns_text(turns), turns)
        else:
            should = "%s forward, %d back" % (turns_text(turns), turns)
        rows.append("  %-7s  %-4s  %-9s  %s" % (channel, role, box, should))
    rows += ["", "  Then all together: each axis 1 turn forward and back,",
             "  finishing together, with the spindles running (Sp1 at half speed)."]
    return "\n".join(rows)


# ----------------------------------------------------------------------
# Running a pass

def generate_local_files():
    '''Runs the startup generator; True when it wrote the .local files.'''
    result = subprocess.run([sys.executable, GENERATOR])
    return result.returncode == 0


def point_local_ini_at(program_path):
    with open(LOCAL_INI_PATH, "r") as f:
        text = f.read()
    text, n = re.subn(r'(?m)^(OPEN_FILE\s*=\s*).*$', lambda m: m.group(1) + program_path, text, count=1)
    if n != 1:
        raise RuntimeError("No OPEN_FILE line found in " + LOCAL_INI_PATH)
    with open(LOCAL_INI_PATH, "w") as f:
        f.write(text)


def run_linuxcnc():
    proc = subprocess.Popen(["linuxcnc", LOCAL_INI_PATH])
    try:
        return proc.wait()
    except KeyboardInterrupt:
        say("\nWaiting for LinuxCNC to close...")
        proc.wait()
        raise


def collect_results(pass_name, layout, channels):
    say("")
    say("Record pass %s.  p = pass, f = fail, s = skipped (no motor on that channel)." % pass_name)
    results = []
    for channel in channels:
        role = layout[channel]
        answer = ask("  Channel %s (%s): p / f / s? " % (channel, role), ("p", "f", "s"))
        note = ask("    Note (Enter for none): ") if answer == "f" else ""
        results.append((channel, role, answer, note))
    group = ask("  All together - every axis moved and finished together: p / f? ", ("p", "f"))
    group_note = ask("    Note (Enter for none): ") if group == "f" else ""
    results.append(("all", "together", group, group_note))
    return results


WORD = {"p": "PASS", "f": "FAIL", "s": "skipped"}


def log_results(log, pass_name, results, attempt):
    log.write("\nPass %s (attempt %d) - %s\n" % (pass_name, attempt, time.strftime("%d %B %Y %H:%M")))
    for channel, role, answer, note in results:
        label = "Channel %s (%s)" % (channel, role) if channel != "all" else "All together"
        log.write("  %-22s %s%s\n" % (label, WORD[answer], ("  - " + note) if note else ""))
    log.flush()


# ----------------------------------------------------------------------
# Settings backup and restore

def restore_settings(backup_path):
    shutil.copy2(backup_path, SETTINGS_PATH)
    try:
        os.remove(RESTORE_MARKER)
    except OSError:
        pass
    say("Settings restored from " + backup_path)
    # Put the .local files back to this machine's own settings too (the
    # next launch would do it anyway).
    generate_local_files()


def recover_from_earlier_run():
    if not os.path.exists(RESTORE_MARKER):
        return
    try:
        with open(RESTORE_MARKER) as f:
            backup = json.load(f).get("backup", "")
    except (OSError, ValueError):
        backup = ""
    say("An earlier checkout didn't finish, so the test settings may still be in place.")
    if backup and os.path.exists(backup):
        if ask("Put back this machine's settings from %s? [Y/n] " % backup, ("y", "n"), "y") == "y":
            restore_settings(backup)
            say("Run Rosetta_Checkout.sh again to start a new checkout.")
            sys.exit(0)
    else:
        say("Its backup (%s) can't be found. Check %s by hand, then delete %s."
            % (backup or "unknown", SETTINGS_PATH, RESTORE_MARKER))
    sys.exit(1)


def _exit_on_signal(signum, frame):
    raise SystemExit(128 + signum)


# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Rosetta bench checkout")
    parser.add_argument("--steps-per-rev", type=int, default=DEFAULT_STEPS_PER_REV)
    parser.add_argument("--pass", dest="only_pass", choices=("A", "B"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--settings", default=SETTINGS_PATH)
    parser.add_argument("--out", default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    say("Rosetta - bench checkout")
    say("")
    if not args.dry_run:
        if linuxcnc_running():
            say("LinuxCNC is running. Close it, then run this again.")
            return 1
        recover_from_earlier_run()

    serial = ask("Serial number: ")
    serial_file = re.sub(r"[^A-Za-z0-9_-]+", "_", serial) or "unknown"
    expansion_box = ask("Is the expansion box connected and being tested? [y/n] ", ("y", "n")) == "y"
    say("Each test motor must be labelled with its channel number. Steps per turn: %d."
        % args.steps_per_rev)

    original = rosetta_settings_io.load_settings(args.settings)
    run_dir = os.path.join(args.out, "%s_%s" % (serial_file, time.strftime("%Y%m%d-%H%M%S")))
    os.makedirs(run_dir, exist_ok=True)
    channels = tested_channels(expansion_box)
    passes = [args.only_pass] if args.only_pass else ["A", "B"]

    log_path = os.path.join(run_dir, "checkout_log.txt")
    log = open(log_path, "a")
    log.write("Rosetta bench checkout\n")
    log.write("Serial number: %s\n" % serial)
    log.write("Date: %s\n" % time.strftime("%d %B %Y %H:%M"))
    log.write("Software: %s\n" % software_version())
    log.write("Boxes: base%s\n" % (" + expansion" if expansion_box else " only"))
    log.write("Steps per turn: %d\n" % args.steps_per_rev)
    log.flush()

    if args.dry_run:
        for pass_name in passes:
            layout = layout_for(pass_name, expansion_box)
            settings = test_settings(original, layout, expansion_box, args.steps_per_rev)
            with open(os.path.join(run_dir, "pass_%s_settings.json" % pass_name), "w") as f:
                json.dump(settings, f, indent=2)
            with open(os.path.join(run_dir, "pass_%s.ngc" % pass_name), "w") as f:
                f.write(test_program(serial, pass_name, layout, channels))
            say("")
            say(record_sheet(pass_name, layout, channels))
        log.write("Dry run - nothing was changed or run.\n")
        log.close()
        say("")
        say("Dry run: files written to " + run_dir)
        return 0

    backup_path = os.path.join(run_dir, "RosettaSet_v1.ini.before-checkout")
    shutil.copy2(SETTINGS_PATH, backup_path)
    with open(RESTORE_MARKER, "w") as f:
        json.dump({"backup": backup_path}, f)
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _exit_on_signal)

    failed = False
    try:
        for pass_name in passes:
            layout = layout_for(pass_name, expansion_box)
            program_path = os.path.join(run_dir, "pass_%s.ngc" % pass_name)
            with open(program_path, "w") as f:
                f.write(test_program(serial, pass_name, layout, channels))
            rosetta_settings_io.save_settings(
                test_settings(original, layout, expansion_box, args.steps_per_rev), SETTINGS_PATH)
            attempt = 0
            while True:
                attempt += 1
                say("")
                say("=" * 71)
                say(record_sheet(pass_name, layout, channels))
                say("")
                say("Starting LinuxCNC for pass %s. In AXIS:" % pass_name)
                say("  1. F1, then F2 (machine on).")
                say("  2. Click ENA on every row in use until it is green (they start off).")
                say("  3. Run the program (R). It pauses before each step - press Resume.")
                say("  4. Close LinuxCNC when it says the pass is finished.")
                if not generate_local_files():
                    say("The startup generator refused (see above) - pass %s not run." % pass_name)
                    log.write("\nPass %s: not run - the startup generator refused.\n" % pass_name)
                    failed = True
                    break
                point_local_ini_at(program_path)
                run_linuxcnc()
                results = collect_results(pass_name, layout, channels)
                log_results(log, pass_name, results, attempt)
                if any(r[2] == "f" for r in results):
                    if ask("Something failed. Fix it and run pass %s again? [y/n] " % pass_name,
                           ("y", "n")) == "y":
                        continue
                    failed = True
                break
    finally:
        restore_settings(backup_path)

    log.write("\nResult: %s\n" % ("FAILED - see above" if failed else "all recorded checks passed"))
    log.close()
    say("")
    say("Checkout %s. Log: %s" % ("FAILED" if failed else "finished", log_path))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
