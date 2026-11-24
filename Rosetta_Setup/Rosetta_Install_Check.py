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
#
# File:
#   Rosetta_Install_Check.py
#
# Purpose:
#   Checks that the software install worked: every file, program,
#   setting, menu entry, desktop icon and shortcut the installer
#   (Rosetta_Install_Debian_13_Trixie.sh) puts in place is there and
#   points at something that exists, the network is set up, the cards
#   answer, and this machine's LinuxCNC configuration can be made.
#
#       python3 ~/linuxcnc/configs/Rosetta/Rosetta_Setup/Rosetta_Install_Check.py
#
#   The installer runs it as its last step with --before-jumpers: the
#   base card only answers at 10.10.10.10 once its W6 jumper is moved,
#   after the shutdown that ends the install, so until then a card
#   that doesn't answer is only noted. Run it again (without the
#   option) once the machine is back on - that is the full check.
#
#   Each line is OK, WARN (works, but worth a look - e.g. no serial
#   number, or something an update will finish) or FAIL (something the
#   install should have done and didn't - the Support Manual's
#   Installation page, 3.3, says how to do each by hand). The same
#   report is saved to ~/Documents/Rosetta_Install_Check.txt, for
#   sending to support. Exits 1 if anything failed, else 0. Changes
#   nothing except that report and the files LinuxCNC's start makes
#   every time (Rosetta.local.ini and the .local.hal files).
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 24 November 2026
#   1.1 - 24 November 2026 - checks the weekly virus scan is
#         scheduled and the signatures update themselves
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

import datetime
import glob
import hashlib
import os
import re
import shutil
import socket
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
sys.path.insert(0, os.path.join(REPO, "Rosetta_Display"))

REPORT_PATH = os.path.join(HOME, "Documents", "Rosetta_Install_Check.txt")
CONFIG_DIR = os.path.join(HOME, ".config", "Rosetta")
APPS_DIR = os.path.join(HOME, ".local", "share", "applications")
DIRS_DIR = os.path.join(HOME, ".local", "share", "desktop-directories")
MENU = os.path.join(HOME, ".config", "menus", "xfce-applications.menu")
PANEL_DIR = os.path.join(HOME, ".config", "xfce4", "panel")
FIRMWARE_DIR = "/usr/lib/firmware/hm2/hostmot2"
FIRMWARE_FILES = ("7i92t_Rosetta.bin", "7i92t_Rosetta.pin", "PIN_Rosetta_34.vhd")
SUBMENU_NAMES = ("menulibre-rose-engine-butler", "menulibre-rosetta")
PI_WIRED = "10.10.10.100/24"
PI_WIRED_BEFORE = "192.168.1.120/24"
BASE_CARD, EXPANSION_CARD = "10.10.10.10", "10.10.10.11"

# Programs the installer installs: (what, command names - any one will do)
PROGRAMS = (
    ("LinuxCNC", ("linuxcnc",)),
    ("halcmd", ("halcmd",)),
    ("mesaflash", ("mesaflash",)),
    ("ClamAV", ("clamscan",)),
    ("MenuLibre", ("menulibre",)),
    ("galculator", ("galculator",)),
    ("xfce4-screenshooter", ("xfce4-screenshooter",)),
    ("Chromium", ("chromium", "chromium-browser")),
    ("Claude Code", ("claude", os.path.join(HOME, ".npm-global", "bin", "claude"))),
)

# What the Rosetta submenu should hold: (what, program it runs)
SUBMENU_PROGRAMS = (
    ("Rosetta", "Rosetta_Launch.sh"),
    ("Rosetta Settings", "Rosetta_Settings.sh"),
    ("Back Up to USB", "Rosetta_Backup.sh"),
    ("Update Rosetta", "Rosetta_Update.sh"),
    ("Rosette Designer", "Rosetta_Rosette_Designer.sh"),
    ("Geometric Chuck Designer", "Rosetta_GeoChuck_Designer.sh"),
    ("User Manual", "Rosetta_User_Manual/index.html"),
    ("Gcode Library", "Rosetta_Gcode_Library/index.html"),
)

# What should be on the desktop: (what, program it runs)
DESKTOP_PROGRAMS = (
    ("Rosetta", "Rosetta_Launch.sh"),
    ("Rosetta Settings", "Rosetta_Settings.sh"),
    ("User Manual", "Rosetta_User_Manual/index.html"),
    ("Gcode Library", "Rosetta_Gcode_Library/index.html"),
)

# Menus the install hides: (what, file in ~/.local/share)
HIDDEN = (
    ("Mail Reader", os.path.join(APPS_DIR, "xfce4-mail-reader.desktop")),
    ("Games", os.path.join(DIRS_DIR, "xfce-games.directory")),
    ("Multimedia", os.path.join(DIRS_DIR, "xfce-multimedia.directory")),
    ("Office", os.path.join(DIRS_DIR, "xfce-office.directory")),
    ("Science", os.path.join(DIRS_DIR, "xfce-science.directory")),
)

# The one-time steps' markers: (what, marker file in ~/.config/Rosetta)
MARKERS = (
    ("Folder shortcuts", "shortcuts-added"),
    ("Rosetta menu and desktop icons", "menu-and-desktop-added"),
    ("Rosette Designer menu entry", "rosette-designer-added"),
    ("Shut Down menu entry and launcher", "shut-down-added-2"),
    ("Geometric Chuck Designer menu entry", "geochuck-designer-added"),
    ("User Manual and Gcode Library icons", "manuals-added"),
    ("Weekly virus scan", "virus-scan-added"),
)
SCAN_CRON = "/etc/cron.d/rosetta-virus-scan"

results = []           # (status, section, text)
section = ""


def report(status, text):
    results.append((status, section, text))
    print("  %-4s  %s" % (status, text))


def ok(text):
    report("OK", text)


def warn(text):
    report("WARN", text)


def fail(text):
    report("FAIL", text)


def heading(name):
    global section
    section = name
    print("\n" + name)


def run(cmd, timeout=20):
    '''(exit code, output) of a command, or (None, why) if it can't run.'''
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=timeout)
        return p.returncode, p.stdout
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)


def read(path):
    try:
        with open(path, errors="replace") as f:
            return f.read()
    except OSError:
        return None


def desktop_fields(path):
    '''The [Desktop Entry] keys of a .desktop/.directory file.'''
    fields, in_entry = {}, False
    for line in (read(path) or "").splitlines():
        if line.startswith("["):
            in_entry = line.strip() == "[Desktop Entry]"
        elif in_entry and "=" in line:
            key, value = line.split("=", 1)
            fields.setdefault(key.strip(), value.strip())
    return fields


def runs(fields, program):
    '''True if a launcher's Exec runs this repo's program.'''
    return re.search(r"(^|[\s/])" + re.escape(program) + r"(\s|$)", fields.get("Exec", "")) is not None


def launcher_problems(fields):
    '''What's wrong with a launcher: its program or icon missing.'''
    problems = []
    words = fields.get("Exec", "").split()
    target = next((w for w in words if w.startswith("/")), None)
    if not target or not os.path.exists(target):
        problems.append("runs %s, which doesn't exist" % (target or "nothing"))
    icon = fields.get("Icon", "")
    if icon.startswith("/") and not os.path.exists(icon):
        problems.append("its icon %s is missing" % icon)
    return problems


# --- Files -----------------------------------------------------------
def check_files():
    heading("Files")
    missing = [f for f in FIRMWARE_FILES if not os.path.exists(os.path.join(FIRMWARE_DIR, f))]
    if missing:
        fail("Mesa card files missing from %s: %s" % (FIRMWARE_DIR, ", ".join(missing)))
    else:
        ok("Mesa card files are in " + FIRMWARE_DIR)
    for what, path in (("AXIS settings", os.path.join(HOME, ".axisrc")),
                       ("Update script copy", os.path.join(HOME, "Rosetta_Update.sh"))):
        (ok if os.path.isfile(path) else fail)("%s: %s" % (what, path))
    for what, path in (("Gcode folder", os.path.join(REPO, "gcode")),
                       ("ClamAV quarantine folder", os.path.join(HOME, "ClamAv", "SuspiciousFiles"))):
        (ok if os.path.isdir(path) else fail)("%s: %s" % (what, path))
    settings = os.path.join(HOME, "Documents", "RosettaSet_v1.ini")
    text = read(settings)
    if text is None:
        fail("Settings file missing: " + settings)
    else:
        try:
            import rosetta_settings_io
            data = rosetta_settings_io.parse_settings_text(text)
            ok("Settings file reads: %s (%d settings)" % (settings, len(data)))
        except Exception as e:
            fail("Settings file %s can't be read: %s" % (settings, e))


# --- Programs --------------------------------------------------------
def check_programs():
    heading("Programs")
    for what, names in PROGRAMS:
        found = None
        for n in names:
            found = n if os.path.isabs(n) and os.access(n, os.X_OK) else shutil.which(n)
            if found:
                break
        (ok if found else fail)("%s%s" % (what, ": " + found if found else " is not installed"))
    code, out = run(["git", "-C", REPO, "rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0:
        ok("Rosetta files: %s (branch %s)" % (REPO, out.strip()))
    else:
        fail("Rosetta files at %s aren't a git copy - updates won't work" % REPO)


# --- Network and Mesa cards ------------------------------------------
def check_network(before_jumpers, expansion_box):
    heading("Network and Mesa cards")
    if not shutil.which("nmcli"):
        fail("nmcli (NetworkManager) is not available")
        return
    code, out = run(["nmcli", "-t", "-f", "NAME,UUID", "con", "show"])
    wired = [line for line in out.splitlines() if line.split(":")[0] == "Wired Ethernet"]
    if len(wired) != 1:
        fail("There should be one connection called Wired Ethernet; there are %d" % len(wired))
        return
    code, out = run(["nmcli", "-g", "ipv4.addresses,ipv4.gateway,ipv4.dns", "con", "show", "Wired Ethernet"])
    lines = (out.splitlines() + ["", "", ""])[:3]
    address, gateway, dns = (l.strip() for l in lines)
    if address == PI_WIRED:
        ok("Wired Ethernet is set to " + PI_WIRED)
    elif address == PI_WIRED_BEFORE:
        fail("Wired Ethernet is still on %s - the base card wasn't set up "
             "(Rosetta_Change_Network.sh base)" % PI_WIRED_BEFORE)
    else:
        fail("Wired Ethernet is set to %r, not %s" % (address, PI_WIRED))
    if gateway or dns:
        warn("Wired Ethernet has a gateway or DNS (%s %s) - it shouldn't" % (gateway, dns))
    code, out = run(["ip", "-4", "-o", "addr", "show", "dev", "eth0"])
    live = re.search(r"inet (\S+)", out or "")
    live = live.group(1) if live else ""
    if live == PI_WIRED:
        ok("eth0 is on " + live)
    else:
        (warn if before_jumpers else fail)("eth0 is on %s, not %s" % (live or "no address", PI_WIRED))
    cards = [("Base card", BASE_CARD)] + ([("Expansion card", EXPANSION_CARD)] if expansion_box else [])
    for what, ip in cards:
        code, _ = run(["ping", "-c", "1", "-W", "1", ip], timeout=5)
        if code == 0:
            ok("%s answers at %s" % (what, ip))
        elif before_jumpers:
            warn("%s doesn't answer at %s yet - expected until its W6 jumper is moved; "
                 "run this check again after that" % (what, ip))
        else:
            fail("%s doesn't answer at %s - check its cable, power and W5/W6 jumpers" % (what, ip))
    code, out = run(["iwgetid", "-r"])
    if code == 0 and out.strip():
        ok("WiFi is connected (%s)" % out.strip())
    else:
        warn("WiFi isn't connected - updates need it")


# --- Virus scanning --------------------------------------------------
def check_virus_scan():
    heading("Virus scanning")
    text = read(SCAN_CRON)
    scan_dir = os.path.join(HOME, "ClamAv")
    if text is not None:
        lines = [l for l in text.splitlines() if "clamscan" in l and not l.lstrip().startswith("#")]
        st = os.stat(SCAN_CRON)
        if not lines:
            fail("%s has no clamscan line" % SCAN_CRON)
        elif "--move=%s/SuspiciousFiles" % scan_dir not in lines[0] or " %s " % HOME not in lines[0]:
            fail("%s scans another home folder, not %s (run Rosetta_Add_Virus_Scan.sh --force)" % (SCAN_CRON, HOME))
        elif st.st_uid != 0 or st.st_mode & 0o022:
            fail("%s must belong to root and not be writable by others, or cron ignores it" % SCAN_CRON)
        else:
            ok("Weekly scan scheduled (%s): Mondays at 03:00" % SCAN_CRON)
    else:
        code, out = run(["sudo", "-n", "crontab", "-l"])
        if code == 0 and any("clamscan" in l and not l.lstrip().startswith("#") for l in out.splitlines()):
            ok("Weekly scan scheduled in root's schedule (added by hand)")
        elif code == 0:
            fail("The weekly virus scan isn't scheduled (Rosetta_Add_Virus_Scan.sh)")
        else:
            warn("No %s; root's own schedule can't be read without the password - "
                 "check with: sudo crontab -l" % SCAN_CRON)
    code, out = run(["systemctl", "is-active", "clamav-freshclam"])
    if out.strip() == "active":
        ok("Virus signatures update themselves (clamav-freshclam is running)")
    else:
        fail("clamav-freshclam isn't running (%s) - virus signatures won't update" % (out.strip() or "not found"))


# --- This machine ----------------------------------------------------
def check_machine():
    heading("This machine")
    serial = (read(os.path.join(CONFIG_DIR, "serial")) or "").strip()
    if serial:
        ok("Serial number: " + serial)
    else:
        warn("No serial number recorded - it is asked again at each update")
    name = (read("/etc/hostname") or "").strip()
    if name.startswith("rosetta"):
        ok("Computer name: %s%s" % (name, "" if name == socket.gethostname()
                                    else " (takes effect at the next restart)"))
    else:
        warn("Computer name is %r, not rosetta-... (Rosetta_Set_Machine_Name.sh)" % name)


# --- Menu ------------------------------------------------------------
def submenu_entries():
    '''(submenu name, its Filenames) from the menu file, or (None, why).'''
    text = read(MENU)
    if text is None:
        return None, "no menu file " + MENU
    try:
        root = ET.fromstring(re.sub(r"<!DOCTYPE[^>]*>", "", text, flags=re.S))
    except ET.ParseError as e:
        return None, "the menu file %s can't be read: %s" % (MENU, e)
    for menu in root.iter("Menu"):
        name = (menu.findtext("Name") or "").strip()
        if name in SUBMENU_NAMES:
            files = [f.text.strip() for inc in menu.findall("Include") for f in inc.iter("Filename") if f.text]
            return name, files
    return None, "the menu has no Rosetta submenu"


def check_menu():
    heading("Applications menu")
    name, files = submenu_entries()
    if name is None:
        fail(files)
        return
    ok("Rosetta submenu found (%s)" % name)
    directory = os.path.join(DIRS_DIR, name + ".directory")
    if name == SUBMENU_NAMES[0] and not os.path.exists(directory):
        warn("The submenu's folder file %s is missing - it may show without its name or icon" % directory)
    launchers = {f: desktop_fields(os.path.join(APPS_DIR, f)) for f in files
                 if os.path.exists(os.path.join(APPS_DIR, f))}
    for what, program in SUBMENU_PROGRAMS:
        found = [f for f, fields in launchers.items() if runs(fields, program)]
        if not found:
            fail("%s is not in the Rosetta submenu" % what)
            continue
        problems = launcher_problems(launchers[found[0]])
        (fail if problems else ok)("%s is in the Rosetta submenu%s" % (what, "" if not problems else
                                    " but " + " and ".join(problems)))
    update = [fields for fields in launchers.values() if runs(fields, "Rosetta_Update.sh")]
    if update and update[0].get("Terminal", "").lower() != "true":
        fail("Update Rosetta doesn't run in a terminal - its questions won't show")
    shut_down = desktop_fields(os.path.join(APPS_DIR, "rosetta-shut-down.desktop"))
    if not shut_down:
        fail("Shut Down is not in the Applications menu")
    else:
        problems = launcher_problems(shut_down)
        (fail if problems else ok)("Shut Down is in the Applications menu%s" %
                                   ("" if not problems else " but " + " and ".join(problems)))
    for what, path in HIDDEN:
        hidden = desktop_fields(path).get("NoDisplay", "").lower() == "true"
        (ok if hidden else warn)("%s is %shidden from the menu" % (what, "" if hidden else "not "))


# --- Desktop, file manager and bottom bar ----------------------------
def desktop_dir():
    code, out = run(["xdg-user-dir", "DESKTOP"])
    path = out.strip() if code == 0 else ""
    return path if path and path != HOME else os.path.join(HOME, "Desktop")


def trusted(path):
    '''True/False, or None if it can't be told (no desktop session).'''
    code, out = run(["gio", "info", "-a", "metadata::xfce-exe-checksum", path])
    if code != 0:
        return None
    m = re.search(r"metadata::xfce-exe-checksum:\s*(\S+)", out)
    with open(path, "rb") as f:
        return bool(m) and m.group(1) == hashlib.sha256(f.read()).hexdigest()


def check_desktop():
    heading("Desktop, file manager and bottom bar")
    folder = desktop_dir()
    icons = {p: desktop_fields(p) for p in glob.glob(os.path.join(folder, "*.desktop"))}
    for what, program in DESKTOP_PROGRAMS:
        found = [p for p, fields in icons.items() if runs(fields, program)]
        if not found:
            fail("%s is not on the desktop" % what)
            continue
        path = found[0]
        problems = launcher_problems(icons[path])
        if not os.access(path, os.X_OK):
            problems.append("it isn't marked executable")
        is_trusted = trusted(path)
        if is_trusted is False:
            problems.append("it isn't trusted (Xfce will ask before running it)")
        if problems:
            fail("%s is on the desktop but %s" % (what, " and ".join(problems)))
        elif is_trusted is None:
            warn("%s is on the desktop (can't tell whether it's trusted without a desktop session)" % what)
        else:
            ok("%s is on the desktop" % what)
    bookmarks = read(os.path.join(HOME, ".config", "gtk-3.0", "bookmarks")) or ""
    for what, path in (("Rosetta", REPO), ("Gcode", os.path.join(REPO, "gcode"))):
        has = re.search(r"^file://%s(\s|$)" % re.escape(path), bookmarks, re.M)
        (ok if has else fail)("File manager Places has %s" % what if has else
                              "File manager Places doesn't have %s" % what)
    panel = [desktop_fields(p) for p in glob.glob(os.path.join(PANEL_DIR, "launcher-*", "*.desktop"))]
    for what, pattern in (("Rosetta folder", 'thunar "%s"' % REPO),
                          ("Gcode folder", 'thunar "%s/gcode"' % REPO),
                          ("Shut Down", "Rosetta_Shut_Down.sh")):
        has = any(pattern in fields.get("Exec", "") for fields in panel)
        (ok if has else fail)("Bottom bar has the %s launcher" % what if has else
                              "Bottom bar doesn't have the %s launcher" % what)
    for what, marker in MARKERS:
        if not os.path.exists(os.path.join(CONFIG_DIR, marker)):
            warn("%s: not finished (no %s marker) - the next update tries again" % (what, marker))


# --- LinuxCNC configuration ------------------------------------------
def check_configuration():
    heading("LinuxCNC configuration")
    code, out = run([sys.executable, os.path.join(REPO, "Rosetta_Setup", "Rosetta_Generate_Local_Ini.py")], 60)
    if code == 0 and os.path.exists(os.path.join(REPO, "Rosetta.local.ini")):
        ok("This machine's configuration (Rosetta.local.ini) can be made")
    else:
        last = [l for l in (out or "").splitlines() if l.strip()][-3:]
        fail("Making Rosetta.local.ini failed: " + " / ".join(last))


def main():
    before_jumpers = "--before-jumpers" in sys.argv[1:]
    expansion_box = False
    try:
        import rosetta_settings_io
        expansion_box = bool(rosetta_settings_io.load_settings().get("expansion_box"))
    except Exception:
        pass
    print("Rosetta install check - " + datetime.datetime.now().strftime("%d %B %Y %H:%M"))
    check_files()
    check_programs()
    check_network(before_jumpers, expansion_box)
    check_virus_scan()
    check_machine()
    check_menu()
    check_desktop()
    check_configuration()

    failed = [r for r in results if r[0] == "FAIL"]
    warned = [r for r in results if r[0] == "WARN"]
    summary = "%d checks: %d OK, %d to look at (WARN), %d failed (FAIL)" % (
        len(results), len(results) - len(failed) - len(warned), len(warned), len(failed))
    print("\n" + summary)
    if failed:
        print("Failed:")
        for _, where, text in failed:
            print("  %s - %s" % (where, text))
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w") as f:
            f.write("Rosetta install check - %s%s\n" % (
                datetime.datetime.now().strftime("%d %B %Y %H:%M"),
                " (before the card's jumpers were moved)" if before_jumpers else ""))
            last = None
            for status, where, text in results:
                if where != last:
                    f.write("\n%s\n" % where)
                    last = where
                f.write("  %-4s  %s\n" % (status, text))
            f.write("\n%s\n" % summary)
        print("Saved to " + REPORT_PATH)
    except OSError as e:
        print("Couldn't save the report: %s" % e)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
