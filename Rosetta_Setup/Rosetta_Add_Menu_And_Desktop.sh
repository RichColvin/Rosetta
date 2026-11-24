#!/bin/bash
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
#   Rosetta_Add_Menu_And_Desktop.sh
#
# Purpose:
#   Does what the Support Manual's Installation page used to have the
#   builder do by hand with MenuLibre and Create Launcher (its 3.6 and
#   3.8), once per machine:
#     - the Applications menu's Rosetta submenu, holding Rosetta,
#       Rosetta Settings, Back Up to USB and Update Rosetta (Update runs
#       in a terminal), placed above Terminal Emulator. It is named
#       menulibre-rose-engine-butler in
#       ~/.config/menus/xfce-applications.menu - the name MenuLibre gave
#       it on the machines built by hand before the Rosetta renaming -
#       so the scripts that add the Designers and the manuals to it
#       (Rosetta_Add_Rosette_Designer.sh and the rest) find it on every
#       machine. If there is no such file yet it is made the way
#       MenuLibre makes it: the system menu merged in, with the system
#       menu's own top-level order copied so the submenu can be placed;
#     - Rosetta and Rosetta Settings on the desktop, as trusted
#       launchers (the sha256 in the gio attribute
#       metadata::xfce-exe-checksum, as Rosetta_Add_Manuals.sh does), so
#       Xfce doesn't ask "Untrusted application launcher" on first use;
#     - hides Mail Reader, Games, Multimedia, Office and Science from
#       the menu (a copy of each in ~/.local/share with NoDisplay=true,
#       as MenuLibre's "Hide from menus" does).
#
#   A machine that already has a Rosetta submenu (made by hand, under
#   either menulibre-rose-engine-butler or menulibre-rosetta) was set up
#   already: nothing is changed on it, only the marker is written.
#
#   Run by the installer (before the steps that add to the submenu) and
#   by Rosetta_Setup/Rosetta_Update_Settings.py on every update
#   (ONE_TIME_STEPS). Writes ~/.config/Rosetta/menu-and-desktop-added
#   once done and from then on does nothing, so an owner who removes
#   something doesn't get it back. If the desktop session can't be
#   reached (e.g. run over ssh, so the icons can't be marked trusted)
#   it says so and tries again on the next update. --force runs it
#   again regardless of the marker. Rosetta_Install_Check.py checks
#   the result.
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
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MARKER="$HOME/.config/Rosetta/menu-and-desktop-added"
APPS_DIR="$HOME/.local/share/applications"
DIRS_DIR="$HOME/.local/share/desktop-directories"
MENU="$HOME/.config/menus/xfce-applications.menu"
IMAGES="$REPO_DIR/Rosetta_Setup/Images"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null)"
if [ -z "$DESKTOP_DIR" ] || [ "$DESKTOP_DIR" = "$HOME" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

if [ -f "$MARKER" ] && [ "$1" != "--force" ]; then
    echo "Menu and desktop: already set up on this machine."
    exit 0
fi
mkdir -p "$APPS_DIR" "$DIRS_DIR" "$DESKTOP_DIR" "$(dirname "$MARKER")" "$(dirname "$MENU")" || exit 1

# A submenu this script made (an earlier run that couldn't finish the
# desktop icons) is kept and only the icons are tried again; one made by
# hand means the machine was set up already.
make_menu=true
if [ -f "$MENU" ] && grep -qE '<Name>menulibre-(rose-engine-butler|rosetta)</Name>' "$MENU"; then
    if grep -q '<Filename>rosetta-launch.desktop</Filename>' "$MENU"; then
        make_menu=false
    else
        echo "Menu and desktop: this machine already has a Rosetta submenu - left as it is."
        date '+%Y-%m-%d %H:%M' > "$MARKER"
        exit 0
    fi
fi

# write_entry <file> <name> <comment> <script> <icon> <terminal>
write_entry() {
    cat > "$1" <<DESKTOP_ENTRY
[Desktop Entry]
Version=1.1
Type=Application
Name=$2
Comment=$3
Icon=$IMAGES/$5
Exec=bash $REPO_DIR/$4
Path=$REPO_DIR/
Terminal=$6
StartupNotify=false
Categories=X-XFCE;menulibre-rose-engine-butler;
DESKTOP_ENTRY
}

# file | name | comment | script | icon | terminal | on the desktop
ENTRIES=(
    "rosetta-launch.desktop|Rosetta|Start the Rosetta system|Rosetta_Launch.sh|Rosetta_Folder.png|false|yes"
    "rosetta-settings.desktop|Rosetta Settings|Run this to configure the way Rosetta works|Rosetta_Settings.sh|Rosetta_SettingsGear.png|false|yes"
    "rosetta-backup.desktop|Back Up to USB|Run this to back up the key Rosetta user files|Rosetta_Backup.sh|Rosetta_Backup.png|false|no"
    "rosetta-update.desktop|Update Rosetta|Run this when notified to do so|Rosetta_Update.sh|Rosetta_Update.png|true|no"
)

if [ "$make_menu" = true ]; then
# --- The menu entries and the submenu's folder -----------------------
for item in "${ENTRIES[@]}"; do
    IFS='|' read -r file name comment script icon terminal desktop <<< "$item"
    write_entry "$APPS_DIR/$file" "$name" "$comment" "$script" "$icon" "$terminal" || exit 1
done
cat > "$DIRS_DIR/menulibre-rose-engine-butler.directory" <<DIRECTORY || exit 1
[Desktop Entry]
Version=1.1
Type=Directory
Name=Rosetta
Comment=This is for the Rosetta programs.
Icon=$IMAGES/Rosetta_Folder.png
DIRECTORY

# --- The submenu, in ~/.config/menus/xfce-applications.menu ----------
python3 - "$MENU" "$DIRS_DIR" "${XDG_CONFIG_DIRS:-/etc/xdg}" <<'ADD_SUBMENU'
import os, re, shutil, sys
path, dirs_dir, config_dirs = sys.argv[1:4]
NAME = "menulibre-rose-engine-butler"
ENTRIES = ["rosetta-launch.desktop", "rosetta-settings.desktop",
           "rosetta-backup.desktop", "rosetta-update.desktop"]
T = "\t"                      # MenuLibre's indent, which the other scripts copy


def top_layout(text):
    '''(start, end) of the top-level <Menu>'s own <Layout>...</Layout>, or None.'''
    depth = 0
    for m in re.finditer(r"<(/?)(Menu|Layout)\b[^>]*?(/?)>", text):
        closing, tag, empty = m.group(1), m.group(2), m.group(3)
        if tag == "Menu" and not empty:
            depth += -1 if closing else 1
        elif tag == "Layout" and not closing and not empty and depth == 1:
            end = text.find("</Layout>", m.end())
            return (m.start(), end + len("</Layout>")) if end > 0 else None
    return None


def with_submenu_named(layout):
    '''The layout with the Rosetta submenu listed above Terminal Emulator.'''
    if NAME in layout:
        return layout
    item = re.search(r"\n([ \t]*)<", layout)
    indent = item.group(1) if item else T
    line = "<Menuname>%s</Menuname>\n%s" % (NAME, indent)
    for anchor in (r"<Filename>xfce4-terminal-emulator\.desktop</Filename>", r"<Merge\b"):
        m = re.search(anchor, layout)
        if m:
            return layout[:m.start()] + line + layout[m.start():]
    end = layout.rfind("</Layout>")
    return layout[:end] + T + "<Menuname>%s</Menuname>\n" % NAME + layout[end:]


submenu = "\n".join(
    [T + "<Menu>", T * 2 + "<Name>%s</Name>" % NAME,
     T * 2 + "<Directory>%s.directory</Directory>" % NAME,
     T * 2 + "<DirectoryDir>%s</DirectoryDir>" % dirs_dir]
    + ["%s<Include>\n%s<Filename>%s</Filename>\n%s</Include>" % (T * 2, T * 3, e, T * 2) for e in ENTRIES]
    + [T * 2 + "<Layout>"]
    + [T * 3 + "<Filename>%s</Filename>" % e for e in ENTRIES]
    + [T * 3 + '<Merge type="files"/>', T * 2 + "</Layout>", T + "</Menu>"])

if os.path.exists(path):
    # A menu file without a Rosetta submenu: add it, and list it in the
    # top-level order if the file has one.
    text = open(path).read()
    span = top_layout(text)
    if span:
        layout = with_submenu_named(text[span[0]:span[1]])
        text = text[:span[0]] + submenu.lstrip("\t") + "\n" + T + layout + text[span[1]:]
    else:
        end = text.rfind("</Menu>")
        text = text[:end] + submenu + "\n" + text[end:]
    shutil.copy2(path, path + ".before-rosetta-menu")
    open(path, "w").write(text)
    sys.exit(0)

# No menu file yet: merge in the system menu, as MenuLibre does.
system = None
for d in config_dirs.split(":"):
    candidate = os.path.join(d or "/etc/xdg", "menus", "xfce-applications.menu")
    if os.path.exists(candidate):
        system = candidate
        break
if not system:
    print("Menu and desktop: the system menu (xfce-applications.menu) wasn't found.")
    sys.exit(2)
system_text = open(system).read()
span = top_layout(system_text)
layout = ""
if span:
    # The system's own top-level order, re-indented, with Rosetta in it;
    # last in the file, where Rosetta_Add_Shut_Down.sh looks for it.
    items = [m.group(0) for m in re.finditer(r"<(Filename|Menuname)>.*?</\1>|<Separator\s*/>|<Merge\b[^>]*/>",
                                             system_text[span[0]:span[1]], re.S)]
    layout = with_submenu_named("\n".join([T + "<Layout>"] + [T * 2 + i for i in items] + [T + "</Layout>"]))
    layout = "\n" + layout
text = ("<?xml version=\"1.0\" ?>\n"
        "<!DOCTYPE Menu\n  PUBLIC '-//freedesktop//DTD Menu 1.0//EN'\n"
        "  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>\n"
        "<Menu>\n" + T + "<Name>Xfce</Name>\n"
        + T + '<MergeFile type="parent">%s</MergeFile>\n' % system
        + submenu + layout + "\n</Menu>\n")
open(path, "w").write(text)
ADD_SUBMENU
if [ $? != 0 ]; then
    echo "Menu and desktop: the Rosetta submenu couldn't be made - will try again next update."
    exit 0
fi
echo "Menu and desktop: Applications > Rosetta holds Rosetta, Rosetta Settings,"
echo "Back Up to USB and Update Rosetta."

# --- Hide the menus a Rosetta doesn't need ---------------------------
python3 - "$APPS_DIR" "$DIRS_DIR" "${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" <<'HIDE'
import os, re, sys
apps_dir, dirs_dir, data_dirs = sys.argv[1:4]
HIDE_APPS = ["xfce4-mail-reader.desktop"]
HIDE_DIRS = ["Games", "Multimedia", "Office", "Science"]    # by Name=


def hidden(text):
    if re.search(r"^NoDisplay=", text, re.M):
        return re.sub(r"^NoDisplay=.*$", "NoDisplay=true", text, flags=re.M)
    return re.sub(r"^(\[Desktop Entry\][^\n]*\n)", r"\1NoDisplay=true\n", text, count=1, flags=re.M)


def hide(src, dest_dir):
    dest = os.path.join(dest_dir, os.path.basename(src))
    text = open(dest if os.path.exists(dest) else src, errors="replace").read()
    open(dest, "w").write(hidden(text))
    print("Menu and desktop: hid " + os.path.basename(src) + ".")


roots = [d for d in data_dirs.split(":") if d]
for app in HIDE_APPS:
    for root in roots:
        src = os.path.join(root, "applications", app)
        if os.path.exists(src):
            hide(src, apps_dir)
            break
done = set()
for root in roots:
    folder = os.path.join(root, "desktop-directories")
    if not os.path.isdir(folder):
        continue
    for f in sorted(os.listdir(folder)):
        if not f.startswith("xfce-") or not f.endswith(".directory") or f in done:
            continue
        text = open(os.path.join(folder, f), errors="replace").read()
        m = re.search(r"^Name=(.*)$", text, re.M)
        if m and m.group(1).strip() in HIDE_DIRS:
            hide(os.path.join(folder, f), dirs_dir)
            done.add(f)
HIDE

fi

# --- Rosetta and Rosetta Settings on the desktop, trusted -----------
all_done=true
for item in "${ENTRIES[@]}"; do
    IFS='|' read -r file name comment script icon terminal desktop <<< "$item"
    [ "$desktop" = yes ] || continue
    # Already one running the same program (e.g. made by hand)?
    if grep -lqsE "^Exec=.*/$script\$" "$DESKTOP_DIR"/*.desktop; then
        echo "Menu and desktop: $name is already on the desktop."
        continue
    fi
    target="$DESKTOP_DIR/$file"
    write_entry "$target" "$name" "$comment" "$script" "$icon" "$terminal" || exit 1
    chmod +x "$target"
    digest="$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$target")"
    if gio set "$target" metadata::xfce-exe-checksum "$digest" 2>/dev/null; then
        echo "Menu and desktop: $name is on the desktop."
    else
        echo "Menu and desktop: $name is on the desktop, but it couldn't be marked trusted"
        echo "(no desktop session?) - will try again on the next update."
        rm -f "$target"
        all_done=false
    fi
done

if [ "$all_done" = true ]; then
    date '+%Y-%m-%d %H:%M' > "$MARKER"
fi
exit 0
