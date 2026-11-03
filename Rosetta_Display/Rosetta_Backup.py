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
# Purpose:  Standalone "Back Up to USB" program for Rosetta.
#   A plain, independently launched GTK window (see Rosetta_Backup.sh) that
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
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 06 October 2026
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
REPO_DIR = os.path.join(HOME_DIR, "linuxcnc/configs/Rosetta")

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

    def __init__(self):
        Gtk.Window.__init__(self, title="Rosetta - Back Up to USB")
        self.set_border_width(16)
        self.set_default_size(520, -1)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

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
        GLib.timeout_add(STICK_POLL_MS, self.refresh)

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


if __name__ == "__main__":
    window = BackupWindow()
    window.show_all()
    Gtk.main()
