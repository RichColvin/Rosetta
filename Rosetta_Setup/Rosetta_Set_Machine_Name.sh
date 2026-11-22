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
#   Rosetta_Set_Machine_Name.sh
#
# Purpose:
#   Names the computer after its serial number - "rosetta-003" for
#   S/N Rosetta003 - so an owner with more than one Rosetta can tell
#   them apart on the home network: two computers with the same name
#   both answer to <name>.local, one quietly becomes <name>-2, and
#   remote desktop or SSH can reach the wrong one. (The Mesa cards'
#   own wired network is separate for each machine and not affected.)
#
#   The name comes from ~/.config/Rosetta/serial (set by
#   Rosetta_Set_Serial_Number.sh, run just before this): lowercase,
#   letters, digits and hyphens only, a leading "S/N", "Rosetta" or
#   "REB" dropped and a plain number padded to 3 digits - "Rosetta003",
#   "REB003", "3" and "003" all give rosetta-003, "RichDev" gives
#   rosetta-richdev.
#
#   --install (the installer, Step 11): renames without asking; with
#     no serial number it uses the end of the Pi's hardware serial
#     (always unique) - rerun later once a number is set.
#   No option (Rosetta_Update_Settings.py's ONE_TIME_STEPS, every
#     update): asks once, in the terminal, whether to rename; the name
#     offered is kept in ~/.config/Rosetta/machine-name-offered, so a
#     "no" isn't asked again unless the serial number - and so the
#     name - changes. Nothing to do without a serial number or a
#     terminal.
#   --force: asks again even if declined before.
#   --dry-run: shows what would change, changes nothing.
#   --print-name: prints the name it would use and exits.
#
#   The new name is written to /etc/hostname and /etc/hosts and takes
#   effect at the next restart - changing it on the running desktop
#   can stop new windows opening until the next login. Until then
#   /etc/hosts keeps the old name too (sudo needs the running name to
#   resolve); the next run after the restart tidies it away. Raspberry
#   Pi OS's cloud-init can set the name at boot, so it is told not to
#   (/etc/cloud/cloud.cfg.d/99_rosetta_hostname.cfg).
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 22 November 2026
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

SERIAL_FILE="$HOME/.config/Rosetta/serial"
OFFERED_FILE="$HOME/.config/Rosetta/machine-name-offered"
CLOUD_CFG="/etc/cloud/cloud.cfg.d/99_rosetta_hostname.cfg"

install_mode=false
force=false
dry_run=false
print_name=false
for arg in "$@"; do
    case "$arg" in
        --install)    install_mode=true ;;
        --force)      force=true ;;
        --dry-run)    dry_run=true ;;
        --print-name) print_name=true ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# The name for a serial number ($1), or nothing if it gives none.
name_for_serial() {
    local s
    s=$(echo "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
    s=$(echo "$s" | sed -E 's#^s/n[-_.:\#]*##; s#^sn[-_.:\#]*([0-9]|rosetta|reb)#\1#; s/^(rosetta|reb)[-_.]*//; s/[^a-z0-9-]+/-/g; s/-+/-/g; s/^-//; s/-$//')
    if [[ "$s" =~ ^[0-9]+$ ]] && [ ${#s} -lt 3 ]; then
        s=$(printf "%03d" "$((10#$s))")
    fi
    [ -n "$s" ] && echo "rosetta-${s:0:55}" | sed 's/-$//'
}

# The end of the Pi's own hardware serial (unique), or nothing.
hardware_suffix() {
    local hw
    hw=$(sed -n 's/^Serial[[:space:]]*:[[:space:]]*//p' /proc/cpuinfo 2>/dev/null | head -1)
    if [ -z "$hw" ] && [ -r /sys/firmware/devicetree/base/serial-number ]; then
        hw=$(tr -d '\0' < /sys/firmware/devicetree/base/serial-number)
    fi
    hw=$(echo "$hw" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9')
    [ -n "$hw" ] && echo "${hw: -6}"
}

serial=""
[ -f "$SERIAL_FILE" ] && serial=$(tr -d '[:space:]' < "$SERIAL_FILE")
target=$(name_for_serial "$serial")
if [ -z "$target" ] && [ "$install_mode" = true ]; then
    suffix=$(hardware_suffix)
    [ -n "$suffix" ] && target="rosetta-$suffix"
fi
if [ "$print_name" = true ]; then
    echo "$target"
    exit 0
fi
if [ -z "$target" ]; then
    echo "Computer name: no serial number yet - left as \"$(hostname)\"."
    exit 0
fi

run() {
    if [ "$dry_run" = true ]; then
        echo "  (dry run) $*"
    else
        "$@"
    fi
}

# Writes $2 into root-owned file $1.
write_root_file() {
    if [ "$dry_run" = true ]; then
        echo "  (dry run) write $1: $2"
    else
        printf '%s\n' "$2" | sudo tee "$1" > /dev/null
    fi
}

remember_offer() {
    [ "$dry_run" = true ] && return
    mkdir -p "$(dirname "$OFFERED_FILE")"
    echo "$target" > "$OFFERED_FILE"
}

current=$(hostname)
saved=$(tr -d '[:space:]' < /etc/hostname 2>/dev/null)

if [ "$current" = "$target" ]; then
    # Renamed and restarted: take the old name off /etc/hosts' line.
    hosts_line=$(grep -m1 '^127\.0\.1\.1[[:space:]]' /etc/hosts)
    if [ -n "$hosts_line" ] && [ "$(echo "$hosts_line" | awk '{print $2, NF}')" != "$target 2" ]; then
        run sudo sed -i "s/^127\.0\.1\.1[[:space:]].*/127.0.1.1\t$target/" /etc/hosts
    fi
    remember_offer
    echo "Computer name: \"$target\"."
    exit 0
fi

if [ "$saved" = "$target" ]; then
    echo "Computer name: becomes \"$target\" at the next restart."
    exit 0
fi

if [ "$install_mode" != true ]; then
    if [ "$force" != true ] && [ "$(cat "$OFFERED_FILE" 2>/dev/null)" = "$target" ]; then
        echo "Computer name: \"$current\" (renaming to \"$target\" was declined)."
        exit 0
    fi
    if [ ! -t 0 ]; then
        echo "Computer name: not a terminal - will ask about \"$target\" next update."
        exit 0
    fi
    echo
    echo "This computer is called \"$current\". Naming it \"$target\", after"
    echo "its serial number, lets you tell your Rosetta machines apart on the"
    echo "network. Anything that connects to it by name (remote desktop, SSH)"
    echo "will need to use \"$target\" (or $target.local) afterwards."
    echo "The new name takes effect at the next restart."
    read -r -p "Rename this computer to \"$target\"? [y/N] " answer
    case "$answer" in
        [yY]*) ;;
        *)
            remember_offer
            echo "Computer name: left as \"$current\". To rename it later, run:"
            echo "  $0 --force"
            exit 0
            ;;
    esac
fi

write_root_file /etc/hostname "$target" || { echo "WARNING: could not write /etc/hostname."; exit 1; }
if grep -q '^127\.0\.1\.1[[:space:]]' /etc/hosts; then
    run sudo sed -i "s/^127\.0\.1\.1[[:space:]].*/127.0.1.1\t$target $current/" /etc/hosts
else
    if [ "$dry_run" = true ]; then
        echo "  (dry run) add to /etc/hosts: 127.0.1.1 $target $current"
    else
        printf '127.0.1.1\t%s %s\n' "$target" "$current" | sudo tee -a /etc/hosts > /dev/null
    fi
fi
if [ -d /etc/cloud/cloud.cfg.d ]; then
    write_root_file "$CLOUD_CFG" "# Rosetta names the computer itself (Rosetta_Set_Machine_Name.sh).
preserve_hostname: true"
fi
remember_offer
echo "Computer name: will be \"$target\" after the next restart."
exit 0
