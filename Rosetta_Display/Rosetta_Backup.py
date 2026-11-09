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
#   Rosetta_Backup.py
#
# Purpose:  "Back Up to USB" and "Restore from USB" for Rosetta.
#   Back Up is a plain GTK window - launched on its own (see
#   Rosetta_Backup.sh) or from Rosetta Settings' File menu - that
#   copies the operator's own files onto a USB memory stick inserted
#   into the Raspberry Pi:
#
#     ~/Documents/*.ini                    -> Documents/
#         (RosettaSet_v1.ini plus any Export_Settings .RosettaSet_v1.ini files)
#     RoseEngineButler/gcode/   (all files) -> gcode/
#     RoseEngineButler/Rosetta_Custom/Rosetta_Custom.hal, Rosetta_Tool.tbl
#                                           -> Rosetta_Custom/
#     ~/linuxcnc/nc_files/      (all files) -> nc_files/
#
#   Each run writes a NEW dated folder on the stick,
#   Rosetta_Backup/YYYY-MM-DD_HHMM/, so an earlier backup is never
#   overwritten, plus a backup_log.txt listing every file copied and
#   anything that failed. Once copying finishes the stick is synced
#   and unmounted (udisksctl), and only then is the operator told it
#   is safe to remove.
#
#   The stick is found by scanning /proc/mounts for the desktop's
#   automount points (/media/<user>/<label>), re-checked every couple
#   of seconds so a stick inserted after the window opens just
#   appears. No HAL access and no linuxcnc module import - this
#   program works the same whether or not LinuxCNC is running. If it
#   IS running the operator is warned (not blocked): heavy USB I/O on
#   the Pi can add latency to the realtime motion thread, so a backup
#   is best done with no program cutting.
#
#   Restore from USB (added 09 November 2026; only from Rosetta
#   Settings' File menu - RestoreWindow) copies a chosen dated backup
#   back to the same places. Agreed with Rich: the operator picks which
#   backup on the stick; every file it would replace is first copied to
#   ~/Documents/Before_Restore/YYYY-MM-DD_HHMM/ (laid out like a
#   backup, so it could itself be copied back); it refuses while
#   LinuxCNC is running (LinuxCNC saves RosettaSet_v1.ini as it closes,
#   which would undo the restore); and it warns, without blocking, when
#   the backup's channel assignments or expansion box differ from this
#   machine's. Files on the Pi that aren't in the backup are left
#   alone. Older backups (REB_Backup/ on the stick, with REBset_v1.ini
#   and REB_Custom/) are found too, and their old file names mapped to
#   the new ones. Once anything has been copied, Rosetta Settings
#   closes without saving (its on_restored), so it can't write the
#   values it had loaded over the restored settings.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 06 October 2026
#   1.1 - 09 November 2026 - Restore from USB; both windows can open
#         from Rosetta Settings' File menu; the repo is found from this
#         file's own folder
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
import fnmatch
import shutil
import socket
import subprocess
import threading
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gtk

HOME_DIR = os.path.expanduser("~")
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (destination folder on the stick, source folder, filename patterns,
#  recurse into subfolders?). A source folder that doesn't exist on
# this machine is simply skipped and noted in the log.
BACKUP_SOURCES = [
    ("Documents", os.path.join(HOME_DIR, "Documents"), ["*.ini"], False),
    ("gcode", os.path.join(REPO_DIR, "gcode"), ["*"], True),
    ("Rosetta_Custom", os.path.join(REPO_DIR, "Rosetta_Custom"),
     ["Rosetta_Custom.hal", "Rosetta_Tool.tbl"], False),
    ("nc_files", os.path.join(HOME_DIR, "linuxcnc/nc_files"), ["*"], True),
]

BACKUP_ROOT_NAME = "Rosetta_Backup"
LOG_FILE_NAME = "backup_log.txt"

# Restore: backup folders on the stick to look in (REB_Backup is what
# the program wrote before the Rosetta renaming), and old file/folder
# names in a backup mapped to today's (relative to the backup folder).
RESTORE_ROOT_NAMES = (BACKUP_ROOT_NAME, "REB_Backup")
RESTORE_RENAMES = {
    "Documents/REBset_v1.ini": "Documents/RosettaSet_v1.ini",
    "REB_Custom/REB_Custom.hal": "Rosetta_Custom/Rosetta_Custom.hal",
    "REB_Custom/REB_Tool.tbl": "Rosetta_Custom/Rosetta_Tool.tbl",
}
SETTINGS_RELATIVE = "Documents/RosettaSet_v1.ini"
BEFORE_RESTORE_DIR = os.path.join(HOME_DIR, "Documents", "Before_Restore")

# Where the desktop's automounter (udisks2) mounts removable media.
MEDIA_PREFIXES = ("/media/", "/run/media/")

STICK_POLL_MS = 2000


def _decode_mount_field(field):
    '''/proc/mounts escapes space, tab, newline and backslash as octal
    (e.g. a stick labelled "MY STICK" shows as MY\\040STICK).'''
    for code, char in (("\\040", " "), ("\\011", "\t"),
                       ("\\012", "\n"), ("\\134", "\\")):
        field = field.replace(code, char)
    return field


def find_usb_mounts():
    '''
    Returns [(label, mount_point, device), ...] for every writable,
    automounted removable drive. Only mounts under /media or
    /run/media backed by a real /dev block device count, so the Pi's
    own SD card/NVMe partitions (mounted at / and /boot/firmware) are
    never offered as a backup target.
    '''
    mounts = []
    try:
        with open("/proc/mounts") as f:
            lines = f.readlines()
    except OSError:
        return mounts
    for line in lines:
        fields = line.split()
        if len(fields) < 3:
            continue
        device = _decode_mount_field(fields[0])
        mount_point = _decode_mount_field(fields[1])
        if not device.startswith("/dev/"):
            continue
        if not mount_point.startswith(MEDIA_PREFIXES):
            continue
        if not os.access(mount_point, os.W_OK):
            continue
        mounts.append((os.path.basename(mount_point), mount_point, device))
    return mounts


def linuxcnc_is_running():
    '''linuxcncsvr is the server process every LinuxCNC session starts
    and stops with - checked by process name rather than via
    linuxcnc.stat() so this program needs no LinuxCNC imports at all.'''
    try:
        result = subprocess.run(["pgrep", "-x", "linuxcncsvr"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except OSError:
        return False


def collect_files():
    '''
    Returns (files, notes): files is [(source_path, relative_dest,
    size_bytes), ...]; notes lists any source folder that was missing.
    Symlinks are skipped, not followed - LinuxCNC's own nc_files
    folder is seeded with symlinks to its large stock example trees,
    which aren't the operator's files and would bloat every backup.
    '''
    files = []
    notes = []
    for dest_name, source_dir, patterns, recurse in BACKUP_SOURCES:
        if not os.path.isdir(source_dir):
            notes.append("Not found, skipped: %s" % source_dir)
            continue
        if recurse:
            walker = os.walk(source_dir, followlinks=False)
        else:
            walker = [(source_dir, [], os.listdir(source_dir))]
        for dir_path, dir_names, file_names in walker:
            dir_names[:] = sorted(d for d in dir_names
                                  if not d.startswith(".")
                                  and not os.path.islink(
                                      os.path.join(dir_path, d)))
            for name in sorted(file_names):
                if name.startswith("."):
                    continue
                if not any(fnmatch.fnmatch(name.lower(), p.lower())
                           for p in patterns):
                    continue
                source_path = os.path.join(dir_path, name)
                if os.path.islink(source_path) or \
                        not os.path.isfile(source_path):
                    continue
                relative = os.path.relpath(source_path, source_dir)
                files.append((source_path,
                              os.path.join(dest_name, relative),
                              os.path.getsize(source_path)))
    return files, notes


def make_backup_dir(mount_point):
    '''Rosetta_Backup/YYYY-MM-DD_HHMM on the stick - no colons, since most
    sticks are FAT32, which forbids them. A second backup inside the
    same minute gets a _2, _3, ... suffix rather than overwriting.'''
    root = os.path.join(mount_point, BACKUP_ROOT_NAME)
    stamp = time.strftime("%Y-%m-%d_%H%M")
    backup_dir = os.path.join(root, stamp)
    suffix = 2
    while os.path.exists(backup_dir):
        backup_dir = os.path.join(root, "%s_%d" % (stamp, suffix))
        suffix += 1
    os.makedirs(backup_dir)
    return backup_dir


def copy_one(source_path, dest_path):
    '''copyfile, not copy2 - FAT32 rejects chmod, so copying
    permissions would fail. The file's modified time is still kept
    where the filesystem allows. Raises on a failed or short copy.'''
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copyfile(source_path, dest_path)
    try:
        stat = os.stat(source_path)
        os.utime(dest_path, (stat.st_atime, stat.st_mtime))
    except OSError:
        pass
    if os.path.getsize(dest_path) != os.path.getsize(source_path):
        raise OSError("size mismatch after copy")


def run_backup(mount_point, progress=None):
    '''
    Copies everything collect_files() finds into a new dated folder on
    the stick, writes backup_log.txt, and syncs. One file failing (an
    illegal-on-FAT32 character in its name, say) is logged and the
    rest still copied. Returns (backup_dir, copied_count, errors,
    notes). progress, if given, is called as progress(done, total,
    relative_dest) after each file.
    '''
    files, notes = collect_files()
    total_bytes = sum(size for _, _, size in files)
    free_bytes = shutil.disk_usage(mount_point).free
    if total_bytes > free_bytes:
        raise OSError("Not enough room on the USB stick: need %s, "
                      "only %s free." % (_format_size(total_bytes),
                                         _format_size(free_bytes)))

    backup_dir = make_backup_dir(mount_point)
    log_lines = [
        "Rosetta backup",
        "Date:    %s" % time.strftime("%d %B %Y %H:%M"),
        "Machine: %s" % socket.gethostname(),
        "",
    ]
    errors = []
    copied = 0
    for index, (source_path, relative, size) in enumerate(files, 1):
        try:
            copy_one(source_path, os.path.join(backup_dir, relative))
            copied += 1
            log_lines.append("OK      %10d  %s" % (size, relative))
        except OSError as e:
            errors.append("%s: %s" % (relative, e))
            log_lines.append("FAILED  %10d  %s  (%s)" % (size, relative, e))
        if progress:
            progress(index, len(files), relative)

    log_lines.append("")
    log_lines.append("%d of %d files copied (%s)."
                     % (copied, len(files), _format_size(total_bytes)))
    log_lines.extend(notes)
    with open(os.path.join(backup_dir, LOG_FILE_NAME), "w") as f:
        f.write("\n".join(log_lines) + "\n")

    os.sync()
    return backup_dir, copied, errors, notes


def eject(device):
    '''Unmounts the stick, then powers it off (the same as the file
    manager's Eject). Returns True once it's safe to pull out - power
    off can fail harmlessly on some card readers, so only the unmount
    has to succeed.'''
    try:
        result = subprocess.run(["udisksctl", "unmount", "-b", device],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    except OSError:
        return False
    if result.returncode != 0:
        return False
    try:
        subprocess.run(["udisksctl", "power-off", "-b", device],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass
    return True


def _format_size(n):
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "bytes" \
                else ("%.1f %s" % (n, unit))
        n /= 1024.0


class BackupWindow(Gtk.Window):

    def __init__(self, parent=None):
        '''parent: the window it was opened from (Rosetta Settings), or
        None when run on its own - then closing it ends the program.'''
        Gtk.Window.__init__(self, title="Rosetta - Back Up to USB")
        self.set_border_width(16)
        self.set_default_size(520, -1)
        if parent is None:
            self.set_position(Gtk.WindowPosition.CENTER)
            self.connect("destroy", Gtk.main_quit)
        else:
            self.set_transient_for(parent)
            self.set_modal(True)
            self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self._poll_id = None
        self.connect("destroy", self._stop_polling)

        self.mounts = []
        self.busy = False

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(box)

        heading = Gtk.Label()
        heading.set_markup("<big><b>Back Up to USB Memory Stick</b></big>")
        heading.set_xalign(0)
        box.pack_start(heading, False, False, 0)

        files, _ = collect_files()
        summary = Gtk.Label(
            label="Copies your settings (.ini) files, G-code, custom HAL "
                  "and tool table, and nc_files: %d files, %s.\n"
                  "Each backup goes into its own dated folder, so earlier "
                  "backups are kept."
                  % (len(files), _format_size(sum(s for _, _, s in files))))
        summary.set_line_wrap(True)
        summary.set_xalign(0)
        box.pack_start(summary, False, False, 0)

        self.warning = Gtk.Label()
        self.warning.set_markup(
            "<span foreground='#b00000'><b>LinuxCNC is running.</b> "
            "A backup is best done while no program is cutting.</span>")
        self.warning.set_line_wrap(True)
        self.warning.set_xalign(0)
        self.warning.set_no_show_all(True)
        box.pack_start(self.warning, False, False, 0)

        stick_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        stick_row.pack_start(Gtk.Label(label="USB stick:"), False, False, 0)
        self.stick_combo = Gtk.ComboBoxText()
        stick_row.pack_start(self.stick_combo, True, True, 0)
        box.pack_start(stick_row, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        box.pack_start(self.progress, False, False, 0)

        self.status = Gtk.Label()
        self.status.set_line_wrap(True)
        self.status.set_xalign(0)
        box.pack_start(self.status, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.backup_button = Gtk.Button(label="Back Up")
        self.backup_button.connect("clicked", self.on_backup_clicked)
        self.close_button = Gtk.Button(label="Close")
        self.close_button.connect("clicked", lambda w: self.destroy())
        buttons.pack_end(self.close_button, False, False, 0)
        buttons.pack_end(self.backup_button, False, False, 0)
        box.pack_start(buttons, False, False, 0)

        self.refresh()
        self._poll_id = GLib.timeout_add(STICK_POLL_MS, self.refresh)

    def _stop_polling(self, widget):
        if self._poll_id is not None:
            GLib.source_remove(self._poll_id)
            self._poll_id = None

    def refresh(self):
        '''Re-scans for sticks and LinuxCNC; runs every STICK_POLL_MS.'''
        if self.busy:
            return True
        self.warning.set_visible(linuxcnc_is_running())

        mounts = find_usb_mounts()
        if mounts != self.mounts:
            previous = self.mounts or []
            selected = self.stick_combo.get_active()
            selected_mount = previous[selected][1] \
                if 0 <= selected < len(previous) else None
            self.mounts = mounts
            self.stick_combo.remove_all()
            for label, mount_point, _ in mounts:
                self.stick_combo.append_text(label)
            active = 0
            for i, (_, mount_point, _) in enumerate(mounts):
                if mount_point == selected_mount:
                    active = i
            if mounts:
                self.stick_combo.set_active(active)

        if self.mounts:
            self.backup_button.set_sensitive(True)
            if not self.status.get_text() or \
                    self.status.get_text().startswith("Insert"):
                self.status.set_text("Ready. Press Back Up to start.")
        else:
            self.backup_button.set_sensitive(False)
            self.status.set_text("Insert a USB memory stick...")
        return True

    def on_backup_clicked(self, widget):
        index = self.stick_combo.get_active()
        if not 0 <= index < len(self.mounts):
            return
        _, mount_point, device = self.mounts[index]
        self.busy = True
        self.backup_button.set_sensitive(False)
        self.close_button.set_sensitive(False)
        self.stick_combo.set_sensitive(False)
        self.progress.set_fraction(0)
        self.status.set_text("Copying... do not remove the USB stick.")
        threading.Thread(target=self._backup_thread,
                         args=(mount_point, device), daemon=True).start()

    def _backup_thread(self, mount_point, device):
        def progress(done, total, name):
            GLib.idle_add(self._show_progress, done, total, name)
        try:
            result = run_backup(mount_point, progress)
        except OSError as e:
            GLib.idle_add(self._finish, None, str(e), False)
            return
        GLib.idle_add(self.status.set_text,
                      "Finishing writes to the USB stick...")
        ejected = eject(device)
        GLib.idle_add(self._finish, result, None, ejected)

    def _show_progress(self, done, total, name):
        self.progress.set_fraction(done / total if total else 1.0)
        self.progress.set_text("%d of %d" % (done, total))
        self.status.set_text("Copying %s" % name)
        return False

    def _finish(self, result, failure, ejected):
        self.busy = False
        self.close_button.set_sensitive(True)
        self.stick_combo.set_sensitive(True)
        self.mounts = None   # force the stick list to rebuild

        if failure:
            message_type = Gtk.MessageType.ERROR
            text = "Backup failed"
            detail = failure
            self.status.set_text("Backup failed.")
        else:
            backup_dir, copied, errors, notes = result
            folder = os.path.join(BACKUP_ROOT_NAME,
                                  os.path.basename(backup_dir))
            detail = "%d files copied to %s on the USB stick." % (copied,
                                                                   folder)
            if errors:
                message_type = Gtk.MessageType.WARNING
                text = "Backup finished with problems"
                detail += "\n\n%d files could not be copied (see %s):\n%s" % (
                    len(errors), LOG_FILE_NAME, "\n".join(errors[:10]))
                if len(errors) > 10:
                    detail += "\n..."
            else:
                message_type = Gtk.MessageType.INFO
                text = "Backup complete"
            if ejected:
                detail += "\n\nIt is now safe to remove the USB stick."
                self.status.set_text("Done. Safe to remove the USB stick.")
            else:
                detail += ("\n\nThe stick could not be ejected "
                           "automatically. Use Eject in the file manager "
                           "before removing it.")
                self.status.set_text("Done. Eject the stick before "
                                     "removing it.")

        dialog = Gtk.MessageDialog(transient_for=self, flags=0,
                                   message_type=message_type,
                                   buttons=Gtk.ButtonsType.OK, text=text)
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()
        self.refresh()
        return False


#######################################################################
# Restore from USB (added 09 November 2026) - see the header.
#######################################################################

def find_backups(mount_point):
    '''
    Every backup folder on the stick, newest first, as
    [(name, path), ...]. Names are the folders' own YYYY-MM-DD_HHMM
    (plus _2, _3, ... for a second backup in the same minute), so
    sorting them sorts by date.
    '''
    backups = []
    for root_name in RESTORE_ROOT_NAMES:
        root = os.path.join(mount_point, root_name)
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for name in names:
            path = os.path.join(root, name)
            if os.path.isdir(path) and not name.startswith("."):
                backups.append((name, path))
    backups.sort(key=lambda b: b[0], reverse=True)
    return backups


def describe_backup(name):
    '''"09 November 2026 14:30" from 2026-11-09_1430 (the name
    itself if it doesn't fit that pattern).'''
    stamp = name.split("_")[0] + "_" + name.split("_")[1] if name.count("_") else name
    try:
        when = time.strptime(stamp, "%Y-%m-%d_%H%M")
    except ValueError:
        return name
    text = time.strftime("%d %B %Y %H:%M", when)
    if name != stamp:
        text += " (" + name[len(stamp) + 1:] + ")"
    return text


def _restore_destination(relative):
    '''
    Where a file in a backup (its path relative to the backup folder)
    goes on this Pi, or None if it isn't one Back Up would have written
    (the log, or a folder or name Back Up doesn't use).
    '''
    relative = RESTORE_RENAMES.get(relative, relative)
    folder, _, rest = relative.partition("/")
    for dest_name, source_dir, patterns, recurse in BACKUP_SOURCES:
        if folder != dest_name or not rest:
            continue
        if not recurse and "/" in rest:
            return None
        name = os.path.basename(rest)
        if name.startswith(".") or not any(
                fnmatch.fnmatch(name.lower(), p.lower()) for p in patterns):
            return None
        return relative, os.path.join(source_dir, rest)
    return None


def collect_restore(backup_dir):
    '''
    Returns [(backup_path, new_relative, destination, size), ...] for
    every file in the backup that restores somewhere. A backup holding
    both REBset_v1.ini and RosettaSet_v1.ini keeps RosettaSet_v1.ini.
    '''
    found = {}
    for dir_path, dir_names, file_names in os.walk(backup_dir):
        dir_names[:] = sorted(d for d in dir_names if not d.startswith("."))
        for name in sorted(file_names):
            path = os.path.join(dir_path, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            relative = os.path.relpath(path, backup_dir).replace(os.sep, "/")
            target = _restore_destination(relative)
            if target is None:
                continue
            new_relative, destination = target
            renamed = new_relative != relative
            if new_relative in found and renamed:
                continue    # today's name wins over the old one
            found[new_relative] = (path, new_relative, destination,
                                   os.path.getsize(path))
    return [found[k] for k in sorted(found)]


def restore_summary(files):
    '''"3 settings files, 40 G-code files, ..." for the confirm box.'''
    labels = (("Documents", "settings file"), ("gcode", "G-code file"),
              ("Rosetta_Custom", "custom HAL / tool table file"),
              ("nc_files", "nc_files file"))
    counts = {}
    for _, relative, _, _ in files:
        folder = relative.split("/")[0]
        counts[folder] = counts.get(folder, 0) + 1
    parts = []
    for folder, label in labels:
        n = counts.get(folder, 0)
        if n:
            parts.append("%d %s%s" % (n, label, "" if n == 1 else "s"))
    return ", ".join(parts)


def _read_settings(path):
    try:
        import rosetta_settings_io
        with open(path) as f:
            data = rosetta_settings_io.parse_settings_text(f.read())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def setup_differences(files):
    '''
    Lines saying how the backup's machine setup (channel assignments,
    expansion box) differs from this machine's, from the two
    RosettaSet_v1.ini files - empty if they match or either can't be
    read (an old XML-format file, say). A warning only.
    '''
    backup_path = next((p for p, rel, _, _ in files if rel == SETTINGS_RELATIVE), None)
    if backup_path is None:
        return ["The backup has no RosettaSet_v1.ini, so this machine's "
                "settings stay as they are."]
    import rosetta_settings_io
    here = _read_settings(rosetta_settings_io.SETTINGS_PATH)
    there = _read_settings(backup_path)
    if here is None or there is None:
        return []
    lines = []
    if bool(here.get("expansion_box")) != bool(there.get("expansion_box")):
        lines.append("Expansion box: %s here, %s in the backup." % (
            "connected" if here.get("expansion_box") else "not connected",
            "connected" if there.get("expansion_box") else "not connected"))
    mine = rosetta_settings_io.complete_channel_assignments(here.get("channel_assignments"))
    theirs = rosetta_settings_io.complete_channel_assignments(there.get("channel_assignments"))
    for channel in rosetta_settings_io.CHANNEL_IDS:
        if mine.get(channel) != theirs.get(channel):
            lines.append("Channel %s: %s here, %s in the backup." % (
                channel, mine.get(channel) or "nothing", theirs.get(channel) or "nothing"))
    return lines


def run_restore(files, progress=None):
    '''
    Copies the backup's files into place. Every file that would be
    replaced is first copied to a new Before_Restore/YYYY-MM-DD_HHMM
    folder (if that fails for a file, the file isn't replaced). Returns
    (saved_dir or None, copied, errors). progress, if given, is called
    as progress(done, total, relative) after each file.
    '''
    stamp = time.strftime("%Y-%m-%d_%H%M")
    saved_dir = os.path.join(BEFORE_RESTORE_DIR, stamp)
    suffix = 2
    while os.path.exists(saved_dir):
        saved_dir = os.path.join(BEFORE_RESTORE_DIR, "%s_%d" % (stamp, suffix))
        suffix += 1
    saved_any = False
    copied = 0
    errors = []
    for index, (source, relative, destination, size) in enumerate(files, 1):
        try:
            if os.path.isfile(destination):
                keep = os.path.join(saved_dir, relative)
                os.makedirs(os.path.dirname(keep), exist_ok=True)
                shutil.copy2(destination, keep)
                saved_any = True
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            # Write beside the file then rename over it, so a failed
            # copy never leaves a half-written file in its place.
            temporary = destination + ".restoring"
            shutil.copyfile(source, temporary)
            if os.path.getsize(temporary) != size:
                os.remove(temporary)
                raise OSError("size mismatch after copy")
            try:
                st = os.stat(source)
                os.utime(temporary, (st.st_atime, st.st_mtime))
            except OSError:
                pass
            os.replace(temporary, destination)
            copied += 1
        except OSError as e:
            errors.append("%s: %s" % (relative, e))
        if progress:
            progress(index, len(files), relative)
    os.sync()
    return (saved_dir if saved_any else None), copied, errors


class RestoreWindow(Gtk.Window):
    '''
    Restore from USB, opened from Rosetta Settings (parent). on_restored
    is called once the restore has copied anything, after the operator
    closes the result box - Rosetta Settings then closes without saving.
    '''

    def __init__(self, parent, on_restored):
        Gtk.Window.__init__(self, title="Rosetta - Restore from USB")
        self.set_border_width(16)
        self.set_default_size(560, -1)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.on_restored = on_restored
        self.mounts = None      # so the first refresh fills the lists
        self.backups = []
        self.files = []
        self.differences = []
        self.busy = False

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(box)

        heading = Gtk.Label()
        heading.set_markup("<big><b>Restore from USB Memory Stick</b></big>")
        heading.set_xalign(0)
        box.pack_start(heading, False, False, 0)

        summary = Gtk.Label(
            label="Copies a backup made with Back Up to USB back onto this "
                  "Raspberry Pi: settings (.ini) files, G-code, custom HAL "
                  "and tool table, and nc_files.\n"
                  "Each file it replaces is first copied to "
                  "Documents/Before_Restore. Files that aren't in the "
                  "backup are left as they are.")
        summary.set_line_wrap(True)
        summary.set_xalign(0)
        box.pack_start(summary, False, False, 0)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.attach(Gtk.Label(label="USB stick:", xalign=0), 0, 0, 1, 1)
        self.stick_combo = Gtk.ComboBoxText(hexpand=True)
        self.stick_combo.connect("changed", self.on_stick_changed)
        grid.attach(self.stick_combo, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label="Backup:", xalign=0), 0, 1, 1, 1)
        self.backup_combo = Gtk.ComboBoxText(hexpand=True)
        self.backup_combo.connect("changed", self.on_backup_changed)
        grid.attach(self.backup_combo, 1, 1, 1, 1)
        box.pack_start(grid, False, False, 0)

        self.details = Gtk.Label()
        self.details.set_line_wrap(True)
        self.details.set_xalign(0)
        box.pack_start(self.details, False, False, 0)

        self.warning = Gtk.Label()
        self.warning.set_line_wrap(True)
        self.warning.set_xalign(0)
        box.pack_start(self.warning, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        box.pack_start(self.progress, False, False, 0)

        self.status = Gtk.Label()
        self.status.set_line_wrap(True)
        self.status.set_xalign(0)
        box.pack_start(self.status, False, False, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.restore_button = Gtk.Button(label="Restore")
        self.restore_button.connect("clicked", self.on_restore_clicked)
        self.close_button = Gtk.Button(label="Close")
        self.close_button.connect("clicked", lambda w: self.destroy())
        buttons.pack_end(self.close_button, False, False, 0)
        buttons.pack_end(self.restore_button, False, False, 0)
        box.pack_start(buttons, False, False, 0)

        self.connect("delete-event", lambda w, e: self.busy)
        self.refresh()
        self._poll_id = GLib.timeout_add(STICK_POLL_MS, self.refresh)
        self.connect("destroy", self._stop_polling)

    def _stop_polling(self, widget):
        if self._poll_id is not None:
            GLib.source_remove(self._poll_id)
            self._poll_id = None

    def refresh(self):
        '''Re-scans for sticks; runs every STICK_POLL_MS.'''
        if self.busy:
            return True
        mounts = find_usb_mounts()
        if mounts != self.mounts:
            selected = self.stick_combo.get_active()
            selected_mount = self.mounts[selected][1] \
                if self.mounts and 0 <= selected < len(self.mounts) else None
            self.mounts = mounts
            self.stick_combo.remove_all()
            active = 0
            for i, (label, mount_point, _) in enumerate(mounts):
                self.stick_combo.append_text(label)
                if mount_point == selected_mount:
                    active = i
            if mounts:
                self.stick_combo.set_active(active)
            else:
                self.on_stick_changed(self.stick_combo)
        return True

    def _selected_mount(self):
        index = self.stick_combo.get_active()
        return self.mounts[index] if self.mounts and 0 <= index < len(self.mounts) else None

    def on_stick_changed(self, combo):
        mount = self._selected_mount()
        self.backups = find_backups(mount[1]) if mount else []
        self.backup_combo.remove_all()
        for name, _ in self.backups:
            self.backup_combo.append_text(describe_backup(name))
        if self.backups:
            self.backup_combo.set_active(0)
        else:
            self.on_backup_changed(self.backup_combo)

    def _selected_backup(self):
        index = self.backup_combo.get_active()
        return self.backups[index] if 0 <= index < len(self.backups) else None

    def on_backup_changed(self, combo):
        backup = self._selected_backup()
        self.files = collect_restore(backup[1]) if backup else []
        self.differences = setup_differences(self.files) if self.files else []
        self.progress.set_fraction(0)
        self.progress.set_text("")
        if not self.mounts:
            self.details.set_text("")
            self.status.set_text("Insert the USB memory stick that holds the backup...")
        elif not self.backups:
            self.details.set_text("")
            self.status.set_text("No backups on this USB stick (Back Up to USB "
                                 "puts them in a Rosetta_Backup folder).")
        elif not self.files:
            self.details.set_text("")
            self.status.set_text("This backup has no files to restore.")
        else:
            self.details.set_text("This backup has %s (%s)." % (
                restore_summary(self.files),
                _format_size(sum(f[3] for f in self.files))))
            self.status.set_text("Ready. Press Restore to start.")
        if self.differences:
            self.warning.set_markup(
                "<span foreground='#b00000'><b>This backup's machine setup is "
                "different:</b>\n" + GLib.markup_escape_text("\n".join(self.differences))
                + "</span>")
            self.warning.show()
        else:
            self.warning.set_text("")
            self.warning.hide()
        self.restore_button.set_sensitive(bool(self.files))

    def _message(self, message_type, text, detail, buttons=Gtk.ButtonsType.OK):
        dialog = Gtk.MessageDialog(transient_for=self, flags=0,
                                   message_type=message_type,
                                   buttons=buttons, text=text)
        dialog.format_secondary_text(detail)
        return dialog

    def on_restore_clicked(self, widget):
        mount = self._selected_mount()
        backup = self._selected_backup()
        if not (mount and backup and self.files):
            return
        if linuxcnc_is_running():
            dialog = self._message(
                Gtk.MessageType.ERROR, "LinuxCNC is running",
                "Close LinuxCNC first, then restore. LinuxCNC saves its "
                "settings as it closes, which would undo the restore.")
            dialog.run()
            dialog.destroy()
            return
        detail = ("This replaces files on this Raspberry Pi with the copies "
                  "in the backup from %s: %s.\n\n"
                  "Each file it replaces is first copied to Documents/"
                  "Before_Restore. Rosetta Settings closes when it's done."
                  % (describe_backup(backup[0]), restore_summary(self.files)))
        if self.differences:
            detail += ("\n\nThe backup's machine setup is different from "
                       "this machine's:\n" + "\n".join(self.differences))
        dialog = self._message(Gtk.MessageType.WARNING if self.differences
                               else Gtk.MessageType.QUESTION,
                               "Restore this backup?", detail, Gtk.ButtonsType.NONE)
        dialog.add_button("Restore", Gtk.ResponseType.ACCEPT)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        answer = dialog.run()
        dialog.destroy()
        if answer != Gtk.ResponseType.ACCEPT:
            return

        self.busy = True
        for w in (self.restore_button, self.close_button,
                  self.stick_combo, self.backup_combo):
            w.set_sensitive(False)
        self.progress.set_fraction(0)
        self.status.set_text("Restoring... do not remove the USB stick.")
        threading.Thread(target=self._restore_thread,
                         args=(list(self.files), mount[2]), daemon=True).start()

    def _restore_thread(self, files, device):
        def progress(done, total, name):
            GLib.idle_add(self._show_progress, done, total, name)
        result = run_restore(files, progress)
        GLib.idle_add(self.status.set_text, "Finishing with the USB stick...")
        ejected = eject(device)
        GLib.idle_add(self._finish, result, ejected)

    def _show_progress(self, done, total, name):
        self.progress.set_fraction(done / total if total else 1.0)
        self.progress.set_text("%d of %d" % (done, total))
        self.status.set_text("Restoring %s" % name)
        return False

    def _finish(self, result, ejected):
        saved_dir, copied, errors = result
        self.busy = False
        detail = "%d files restored." % copied
        if saved_dir:
            detail += ("\n\nThe files they replaced are in %s."
                       % os.path.relpath(saved_dir, HOME_DIR))
        if errors:
            message_type = Gtk.MessageType.WARNING
            text = "Restore finished with problems"
            detail += "\n\n%d files could not be restored:\n%s" % (
                len(errors), "\n".join(errors[:10]))
            if len(errors) > 10:
                detail += "\n..."
        else:
            message_type = Gtk.MessageType.INFO
            text = "Restore complete"
        detail += ("\n\nIt is now safe to remove the USB stick." if ejected else
                   "\n\nThe stick could not be ejected automatically. Use "
                   "Eject in the file manager before removing it.")
        if copied:
            detail += ("\n\nRosetta Settings will now close. Open it again "
                       "to see the restored settings.")
        self.status.set_text("Done.")
        dialog = self._message(message_type, text, detail)
        dialog.run()
        dialog.destroy()
        self.destroy()
        if copied and self.on_restored:
            self.on_restored()
        return False


if __name__ == "__main__":
    window = BackupWindow()
    window.show_all()
    Gtk.main()
