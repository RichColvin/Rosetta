#######################################################################
#   RRRRRR    OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT    AA       #
#   RR   RR  OO    OO SS       EE          TT       TT      AAAA      #
#   RR   RR  OO    OO SS       EE          TT       TT     AA  AA     #
#   RRRRRR   OO    OO  SSSSSS  EEEEEE      TT       TT    AA    AA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AAAAAAAA    #
#   RR   RR  OO    OO       SS EE          TT       TT    AA    AA    #
#   RR    RR  OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA    #
#                                                                     #
#                              Rosetta                                #
#######################################################################
#                                                                     #
# File:                                                               #
#   Rosetta_Renaming.py                                               #
#                                                                     #
# Purpose:                                                            #
#   Moves a machine built before the Rosetta renaming (02 November    #
#   2026 - Rose Engine Butler's REB_* files became Rosetta_*) over to #
#   the new names: the things outside the repo that name its files.   #
#   Called by Rosetta_Update_Settings.py at the end of every update;  #
#   each step checks first, so on a machine already moved it does     #
#   nothing. A step that fails is reported and the rest still run.    #
#                                                                     #
#   The settings file and ~/.config/REB are moved by                  #
#   rosetta_settings_io.adopt_old_paths (whenever a Rosetta program   #
#   starts), not here.                                                #
#                                                                     #
#   Steps, in order:                                                  #
#     - the serial number's "REB" prefix becomes "Rosetta"            #
#       (REB003 -> Rosetta003)                                        #
#     - git's GitHub address: RoseEngineButler/RoseEngineButler ->    #
#       RichColvin/Rosetta (the old address forwards, but may not     #
#       forever)                                                      #
#     - the generated files left at their old names in the repo are   #
#       removed (they're made fresh at every launch)                  #
#     - ~/REB_Update.sh (the installer's copy) becomes a stand-in     #
#       that runs ~/Rosetta_Update.sh, a fresh copy                   #
#     - desktop, menu and bottom-bar launchers, Thunar's Places and   #
#       the wallpaper setting are pointed at the new names; a desktop #
#       launcher Xfce trusts is trusted again afterwards (Xfce keeps  #
#       a checksum of the file)                                       #
#     - last, the repo folder ~/linuxcnc/configs/RoseEngineButler is  #
#       renamed Rosetta, with a link at the old name so anything      #
#       still naming it keeps working                                 #
#                                                                     #
# End User Customisation:                                             #
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY THIS FILE.   #
#                                                                     #
#   Changes to this file are not supported by Colvin Tools nor        #
#   Brainwave Embedded.                                               #
#                                                                     #
# Version                                                             #
#   1.0 - 02 November 2026                                            #
#   1.1 - 04 November 2026 - an old idx_debug.log is joined onto a    #
#         new one Rosetta had already started, not left behind        #
#                                                                     #
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.             #
#                                                                     #
# The MIT/X Consortium License applies - see LICENSE.                 #
#######################################################################

import glob
import hashlib
import os
import re
import shutil
import subprocess
import tempfile

HOME = os.path.expanduser("~")
OLD_FOLDER = "RoseEngineButler"
NEW_FOLDER = "Rosetta"
SERIAL_PATH = os.path.join(HOME, ".config", "Rosetta", "serial")
OLD_GITHUB = "RoseEngineButler/RoseEngineButler"
NEW_GITHUB = "RichColvin/Rosetta"

# Files in the repo that something outside it may name (launchers,
# icons, wallpaper), old path -> new path, relative to the repo.
MOVED_FILES = {
    "REB_Launch.sh": "Rosetta_Launch.sh",
    "REB_Settings.sh": "Rosetta_Settings.sh",
    "REB_Update.sh": "Rosetta_Update.sh",
    "REB_Backup.sh": "Rosetta_Backup.sh",
    "REB_Checkout.sh": "Rosetta_Checkout.sh",
    "REB_Change_Network.sh": "Rosetta_Change_Network.sh",
    "REB.ini": "Rosetta.ini",
    "REBStartupImage.gif": "RosettaStartupImage.gif",
    "REB_Setup/Images/REBStartupImage.gif": "Rosetta_Setup/Images/RosettaStartupImage.gif",
    "REB_Setup/Images/REBWallpaper.png": "Rosetta_Setup/Images/RosettaWallpaper.png",
    "REB_Setup/Images/REB_Backup.png": "Rosetta_Setup/Images/Rosetta_Backup.png",
    "REB_Setup/Images/REB_SettingsGear.png": "Rosetta_Setup/Images/Rosetta_SettingsGear.png",
    "REB_Setup/Images/REB_Update.png": "Rosetta_Setup/Images/Rosetta_Update.png",
    "REB_Setup/Images/ReubenHead.png": "Rosetta_Setup/Images/Rosetta_Folder.png",
    "REB_Setup/Images/ReubenHead-Gcode.png": "Rosetta_Setup/Images/Rosetta_Folder-Gcode.png",
    "REB_Setup/Images/Reuben.png": "Rosetta_Setup/Images/RosettaLogo.png",
    "REB_Display/Images/REBLogo-Sm-rev.png": "Rosetta_Display/Images/RosettaLogo-Sm-rev.png",
    "REB_Display/Images/REB_SettingsGear-Sm.png": "Rosetta_Display/Images/Rosetta_SettingsGear-Sm.png",
}
FOLDERS = {
    "REB_Display": "Rosetta_Display",
    "REB_Setup": "Rosetta_Setup",
    "REB_Custom": "Rosetta_Custom",
    "REB_Subroutines": "Rosetta_Subroutines",
}

# Generated at every launch under the old names - removed once the new
# code is in (Rosetta_Generate_Local_Ini.py writes the Rosetta ones).
OLD_GENERATED = (
    "REB.local.ini", "REB.local.hal", "REB.ini.expanded", "REB.local.ini.expanded",
    "REB_Display/REB_PostGUI_v1.local.hal", "REB_Display/REB_Splash.local.ngc",
    "REB_Display/REB_Panel_v1.ui~", "REB_Display/REB_Settings_v1.ui~",
    "REB_Display/REB_Tab_Help_v1.ui~", "REB_Display/REB_Tab_TsCs_v1.ui~",
)
OLD_CACHE_DIRS = ("REB_Display/__pycache__", "REB_Setup/__pycache__")
# Moved rather than removed.
OLD_KEPT = {"REB_Display/idx_debug.log": "Rosetta_Display/idx_debug.log"}

# The installer's copy of the update script in the home folder.
OLD_HOME_UPDATE = os.path.join(HOME, "REB_Update.sh")
NEW_HOME_UPDATE = os.path.join(HOME, "Rosetta_Update.sh")
HOME_UPDATE_STAND_IN = """#!/bin/bash
# Stand-in left by the Rosetta renaming (02 November 2026): this was the
# Rose Engine Butler update script. Runs the Rosetta one instead.
exec bash "$HOME/Rosetta_Update.sh" "$@"
"""

LAUNCHER_GLOBS = (
    os.path.join(HOME, "Desktop", "*.desktop"),
    os.path.join(HOME, ".local", "share", "applications", "*.desktop"),
    os.path.join(HOME, ".config", "xfce4", "panel", "launcher-*", "*.desktop"),
)
BOOKMARKS_PATH = os.path.join(HOME, ".config", "gtk-3.0", "bookmarks")
DESKTOP_XML = os.path.join(HOME, ".config", "xfce4", "xfconf", "xfce-perchannel-xml",
                           "xfce4-desktop.xml")
TRUST_ATTRIBUTE = "metadata::xfce-exe-checksum"


def map_old_paths(text):
    '''
    Rewrites every path into the old repo folder (and the installer's
    ~/REB_Update.sh) in text to its new name. Paths to RoseEngineButlerLocal
    or anything else are left alone.
    '''
    old_root = "/linuxcnc/configs/" + OLD_FOLDER
    new_root = "/linuxcnc/configs/" + NEW_FOLDER
    for old, new in sorted(MOVED_FILES.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(old_root + "/" + old, new_root + "/" + new)
    for old, new in FOLDERS.items():
        text = text.replace(old_root + "/" + old + "/", new_root + "/" + new + "/")
    text = re.sub(re.escape(old_root) + r"(?=/|\"|'|\s|$)", new_root, text, flags=re.M)
    text = text.replace(OLD_HOME_UPDATE, NEW_HOME_UPDATE)
    return text


def map_launcher_text(text):
    text = map_old_paths(text)
    text = text.replace("Rose Engine Butler", "Rosetta")
    text = re.sub(r"(?m)^Name=RoseEngineButler$", "Name=Rosetta", text)
    text = text.replace("Open the RoseEngineButler folder", "Open the Rosetta folder")
    return text


def _write_replacing(path, text, mode=None):
    '''Writes text to path as a new file (a program already reading the
    old one - e.g. bash running ~/REB_Update.sh - keeps reading that).'''
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".rosetta-")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    st = os.stat(path) if os.path.exists(path) else None
    os.chmod(tmp, mode if mode is not None else (st.st_mode & 0o7777 if st else 0o644))
    os.replace(tmp, path)


def _run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None


def serial_prefix():
    try:
        with open(SERIAL_PATH, "r") as f:
            serial = f.read().strip()
    except OSError:
        return
    if re.match(r"(?i)^REB(?![a-z])", serial):
        new = "Rosetta" + serial[3:]
        _write_replacing(SERIAL_PATH, new + "\n")
        print("Rosetta renaming: serial number " + serial + " -> " + new)


def github_address(repo_dir):
    result = _run(["git", "-C", repo_dir, "remote", "-v"])
    if result is None or result.returncode != 0:
        return
    seen = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and OLD_GITHUB in parts[1] and parts[0] not in seen:
            seen.add(parts[0])
            new_url = parts[1].replace(OLD_GITHUB, NEW_GITHUB)
            if _run(["git", "-C", repo_dir, "remote", "set-url", parts[0], new_url]):
                print("Rosetta renaming: git remote " + parts[0] + " -> " + new_url)


def old_generated_files(repo_dir):
    for rel in OLD_GENERATED:
        path = os.path.join(repo_dir, rel)
        if os.path.isfile(path):
            os.remove(path)
    for rel in OLD_CACHE_DIRS:
        shutil.rmtree(os.path.join(repo_dir, rel), ignore_errors=True)
    for old, new in OLD_KEPT.items():
        src, dst = os.path.join(repo_dir, old), os.path.join(repo_dir, new)
        if not os.path.isfile(src) or not os.path.isdir(os.path.dirname(dst)):
            continue
        if not os.path.exists(dst):
            os.rename(src, dst)
        elif os.path.isfile(dst):
            # Rosetta started before this update and began a new log:
            # put the old entries in front of it, so it reads in order.
            tmp = dst + ".joining"
            with open(tmp, "wb") as out:
                for part in (src, dst):
                    with open(part, "rb") as f:
                        shutil.copyfileobj(f, out)
            os.replace(tmp, dst)
            os.remove(src)
    # An old folder left with nothing in it (REB_Setup keeps the
    # stand-in REB_Update_Settings.py, so it stays).
    for old in FOLDERS:
        path = os.path.join(repo_dir, old)
        if os.path.isdir(path) and not os.path.islink(path) and not os.listdir(path):
            os.rmdir(path)


def home_update_copy(repo_dir):
    if not os.path.isfile(OLD_HOME_UPDATE) or os.path.islink(OLD_HOME_UPDATE):
        return
    with open(OLD_HOME_UPDATE, "r") as f:
        if f.read() == HOME_UPDATE_STAND_IN:
            return
    shutil.copyfile(os.path.join(repo_dir, "Rosetta_Update.sh"), NEW_HOME_UPDATE)
    os.chmod(NEW_HOME_UPDATE, 0o755)
    _write_replacing(OLD_HOME_UPDATE, HOME_UPDATE_STAND_IN, 0o755)
    print("Rosetta renaming: ~/REB_Update.sh now runs ~/Rosetta_Update.sh")


def _trusted_checksum(path):
    result = _run(["gio", "info", "-a", TRUST_ATTRIBUTE, path])
    if result is None or result.returncode != 0:
        return None
    m = re.search(re.escape(TRUST_ATTRIBUTE) + r":\s*([0-9a-f]{64})", result.stdout)
    return m.group(1) if m else None


def launchers():
    changed_panel = False
    for pattern in LAUNCHER_GLOBS:
        for path in glob.glob(pattern):
            try:
                with open(path, "r") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            new = map_launcher_text(text)
            if new == text:
                continue
            with open(path, "rb") as f:
                was_trusted = _trusted_checksum(path) == hashlib.sha256(f.read()).hexdigest()
            _write_replacing(path, new)
            if was_trusted:
                digest = hashlib.sha256(new.encode()).hexdigest()
                _run(["gio", "set", path, TRUST_ATTRIBUTE, digest])
            if "/xfce4/panel/" in path:
                changed_panel = True
            print("Rosetta renaming: launcher " + path.replace(HOME, "~"))
    if changed_panel:
        running = _run(["pgrep", "-x", "xfce4-panel"])
        if running is not None and running.returncode == 0:
            _run(["xfce4-panel", "-r"])      # show the new icons now


def bookmarks():
    try:
        with open(BOOKMARKS_PATH, "r") as f:
            text = f.read()
    except OSError:
        return
    new = map_old_paths(text)
    new = re.sub(r"(?m)^(file://\S*/linuxcnc/configs/" + NEW_FOLDER + r") RoseEngineButler$",
                 r"\1 Rosetta", new)
    if new != text:
        _write_replacing(BOOKMARKS_PATH, new)
        print("Rosetta renaming: Thunar's Places shortcuts")


def wallpaper():
    result = _run(["xfconf-query", "-c", "xfce4-desktop", "-l", "-v"])
    if result is not None and result.returncode == 0:
        for line in result.stdout.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2 and "/linuxcnc/configs/" + OLD_FOLDER in parts[1]:
                _run(["xfconf-query", "-c", "xfce4-desktop", "-p", parts[0],
                      "-s", map_old_paths(parts[1])])
                print("Rosetta renaming: desktop setting " + parts[0])
        return
    # No desktop session (e.g. over ssh): the settings daemon isn't
    # running, so its file can be edited directly.
    try:
        with open(DESKTOP_XML, "r") as f:
            text = f.read()
    except OSError:
        return
    new = map_old_paths(text)
    if new != text:
        _write_replacing(DESKTOP_XML, new)
        print("Rosetta renaming: wallpaper setting (" + DESKTOP_XML.replace(HOME, "~") + ")")


def repo_folder(repo_dir):
    real = os.path.realpath(repo_dir)
    parent, name = os.path.split(real)
    new = os.path.join(parent, NEW_FOLDER)
    if name != OLD_FOLDER or os.path.lexists(new):
        return real
    os.rename(real, new)
    os.symlink(NEW_FOLDER, real)
    print("Rosetta renaming: folder " + real.replace(HOME, "~") + " -> "
          + new.replace(HOME, "~") + " (the old name now links to it)")
    return new


def finish(repo_dir):
    '''Runs every step above; returns the repo folder's (new) path.'''
    steps = (
        ("serial number", serial_prefix, ()),
        ("GitHub address", github_address, (repo_dir,)),
        ("old generated files", old_generated_files, (repo_dir,)),
        ("~/REB_Update.sh", home_update_copy, (repo_dir,)),
        ("launchers", launchers, ()),
        ("Places shortcuts", bookmarks, ()),
        ("wallpaper", wallpaper, ()),
    )
    for what, step, args in steps:
        try:
            step(*args)
        except OSError as e:
            print("WARNING: Rosetta renaming (" + what + ") failed: " + str(e))
    try:
        return repo_folder(repo_dir)
    except OSError as e:
        print("WARNING: Rosetta renaming (repo folder) failed: " + str(e))
        return repo_dir
