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
#   Rosetta_Change_Network.sh
#
# Purpose:
#   Moves a Rosetta onto its private wired network for the
#   two-box hardware: the base box's Mesa 7i92 at 10.10.10.10, the
#   expansion box's at 10.10.10.11 and the Raspberry Pi's wired
#   connection at 10.10.10.100, with no gateway or DNS on it (the Pi's
#   internet stays on Wi-Fi). These are the addresses
#   Rosetta_Setup/Rosetta_Generate_Local_Ini.py loads the cards at.
#
#   A new 7i92 always answers at its factory address, 192.168.1.121,
#   so a card is set up while the Pi is still on 192.168.1.120 and with
#   only that one card connected - two cards on the same address would
#   clash. The new address is stored on the card (its EEPROM); the card
#   only uses it once its W5/W6 jumpers are moved to the setting the
#   7i92 manual calls EEPROM, which is read at power-up.
#
#   Once the address is stored the Pi is moved to 10.10.10.100, then
#   shut down for the jumper change. Every Rosetta box powers the Pi and the
#   card from one 24V -> 5V module, and switching the card on while the
#   Pi runs restarts the Pi without a shutdown (found 14 October 2026 on
#   S/N REB003; S/N 1 and 2 are built the same way) - so the whole machine is
#   switched off, the jumpers moved, and switched on, and the Pi starts
#   up already on 10.10.10.x. Afterwards 'check' shows which cards
#   answer. If the Pi restarts at any point anyway, run this again with
#   'pi'.
#
#   Rosetta_Generate_Local_Ini.py picks the base card's address from the
#   Pi's wired address (192.168.1.121 while the Pi is on 192.168.1.x),
#   so an update can arrive before or after this script is run.
#
#   Choices (menu, or as the first argument):
#     base       set up the connected card as the base card (.10)
#     expansion  set up the connected card as the expansion card (.11)
#     pi         move the Pi's wired connection to 10.10.10.100
#     back       put the Pi's wired connection back on 192.168.1.120
#     check      show the Pi's wired address and which cards answer
#   Add --dry-run to show every command without running any of them.
#   --no-shutdown (used by the installer) stops after the address is
#   stored and the Pi moved; the installer gives the shutdown and
#   jumper steps at its end, so its remaining steps still run.
#
#   Nothing is changed without asking first. Recovery for a card: put
#   W5/W6 back to their factory setting and it answers at 192.168.1.121
#   again.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 14 October 2026
#   1.1 - 14 October 2026 - Moves the Pi before the card is power-cycled,
#         so a Pi restart at power-on no longer leaves it unable to
#         reach the card.
#   1.2 - 14 October 2026 - Offers to delete spare "Wired Ethernet"
#         connections.
#   1.3 - 16 October 2026 - Shuts the Pi down for the jumper change (the
#         Pi and card share one 5V supply); adds 'check' and
#         --no-shutdown.
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

TITLE='\033[0;34;1;47m'     # Blue on Lt Gray
KEYNOTE='\033[0;37;0;41m'   # Lt Gray on Red
CMNTTEXT='\033[0;34;1;40m'  # Blue on Black
NOCOLOR='\e[0m'

# The repo is the folder this script is in (not a fixed /home/<login>
# path - the login is changing from reuben to rosetta).
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
FIRMWARE="$REPO_DIR/Rosetta_Setup/MesaCard/7i92t_Rosetta.bin"
CONNECTION="Wired Ethernet"

# A Pi where the installer was run more than once has several
# connections called "Wired Ethernet" (found 14 October 2026), and nmcli
# then changes just one of them. Use the one on eth0 now (else the
# first), by its UUID, and give it a higher autoconnect priority so the
# Pi starts with that one.
CONNECTION_UUID=$(nmcli -t -f UUID,NAME,DEVICE con show --active 2>/dev/null \
    | awk -F: -v n="$CONNECTION" '$2 == n && $3 == "eth0" {print $1; exit}')
if [ -z "$CONNECTION_UUID" ]; then
    CONNECTION_UUID=$(nmcli -t -f UUID,NAME con show 2>/dev/null \
        | awk -F: -v n="$CONNECTION" '$2 == n {print $1; exit}')
fi
FACTORY_CARD_IP="192.168.1.121"
OLD_PI_IP="192.168.1.120/24"
BASE_CARD_IP="10.10.10.10"
EXPANSION_CARD_IP="10.10.10.11"
PI_IP="10.10.10.100/24"

DRY_RUN=false
NO_SHUTDOWN=false
CHOICE=""
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --no-shutdown) NO_SHUTDOWN=true ;;
        base|expansion|pi|back|check) CHOICE="$arg" ;;
        *) echo "Unknown option: $arg (use base, expansion, pi, back, check, --dry-run, --no-shutdown)"; exit 1 ;;
    esac
done

say()  { echo -e "${CMNTTEXT}$1${NOCOLOR}"; }
warn() { echo -e "${KEYNOTE}$1${NOCOLOR}"; }
title() {
    echo -e "${TITLE}#######################################################################${NOCOLOR}"
    echo -e "${TITLE}$1${NOCOLOR}"
}

# Runs a command, or only shows it with --dry-run.
run() {
    if $DRY_RUN; then
        printf '    [dry run]'; printf ' %q' "$@"; printf '\n'
        return 0
    fi
    "$@"
}

# Asks a yes/no question; anything but y/yes means no.
confirm() {
    local answer
    read -r -p "$1 [y/N] " answer
    [[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}

pause() {
    read -r -p "$1 Press Enter when ready (Ctrl+C to stop)... " _
}

# True if a 7i92 answers at the given address.
card_answers() {
    if $DRY_RUN; then
        echo "    [dry run] mesaflash --device 7i92t --addr $1 --readhmid  (assumed to answer)"
        return 0
    fi
    mesaflash --device 7i92t --addr "$1" --readhmid > /dev/null 2>&1
}

stop_if_linuxcnc_running() {
    if pgrep -x linuxcncsvr > /dev/null || pgrep -x milltask > /dev/null; then
        warn "LinuxCNC is running. Close it, then run this again.              "
        exit 1
    fi
}

# --- set up one card --------------------------------------------------
set_up_card() {   # $1 = new address, $2 = "base" or "expansion"
    local new_ip="$1" which="$2"
    title "Set up the $which card ($new_ip)"
    stop_if_linuxcnc_running

    if ! ip -4 addr show | grep -q "inet 192\.168\.1\."; then
        warn "The Pi's wired connection isn't on 192.168.1.x, so it can't reach a"
        warn "card at its factory address. Choose 'back' first, then run this again."
        exit 1
    fi

    say "Connect ONLY the card being set up (unplug any other card), with its"
    say "W5/W6 jumpers at the factory setting, and power it on."
    pause ""

    say "Checking the card answers at $FACTORY_CARD_IP..."
    if ! card_answers "$FACTORY_CARD_IP"; then
        warn "No card answered at $FACTORY_CARD_IP - nothing was changed.        "
        warn "Check the cable, the card's power and its W5/W6 jumpers.          "
        exit 1
    fi
    say "Card found."

    if confirm "Write the Rosetta firmware to it (needed on a new card)?"; then
        run mesaflash --device 7i92t --addr "$FACTORY_CARD_IP" --write "$FIRMWARE" --reload
        if [ $? != 0 ]; then
            warn "Writing the firmware failed - the card's address was not changed."
            exit 1
        fi
    fi

    if ! confirm "Store $new_ip as this card's address?"; then
        say "Address not changed."
        exit 0
    fi
    run mesaflash --device 7i92t --addr "$FACTORY_CARD_IP" --set ip="$new_ip"
    if [ $? != 0 ]; then
        warn "Storing the address failed - the card still answers at $FACTORY_CARD_IP."
        exit 1
    fi

    # Move the Pi now, while nothing else is happening: the power-cycle
    # below can restart the Pi, and it must come back on 10.10.10.x.
    say "Address stored. The Pi's wired connection now moves to ${PI_IP%/*},"
    say "the network the card will be on after its jumpers are moved."
    if confirm "Move the Pi's wired connection to ${PI_IP%/*} now?"; then
        set_pi_address "$PI_IP"
    else
        say "Pi left on 192.168.1.x - run this again with 'pi' once every card"
        say "is set up. Until then the Pi can't reach this card or start LinuxCNC."
    fi

    if $NO_SHUTDOWN && ip -4 addr show | grep -q "inet ${PI_IP%/*}/"; then
        say "Address stored and the Pi moved. The card's W5/W6 jumpers are moved"
        say "after the installation finishes - it will say how."
        return 0
    fi
    if ip -4 addr show | grep -q "inet ${PI_IP%/*}/"; then
        say "The card's jumpers are only read when it's switched on, and the Pi and"
        say "the card run from the same 5V supply: switching the card on while the"
        say "Pi is running restarts the Pi without shutting it down. So:"
        say "  1. Shut the Pi down (next question) and wait for the screen to go dark."
        say "  2. Switch the machine off."
        say "  3. Move the card's W5/W6 jumpers to the setting the 7i92 manual calls"
        say "     EEPROM, and reconnect any card you unplugged for this."
        say "  4. Switch the machine on. Once the Pi has started, run"
        say "     $REPO_DIR/Rosetta_Change_Network.sh check"
        say "     - it should say the card at $new_ip answers."
        say "To undo: jumpers back to the factory setting = $FACTORY_CARD_IP again."
        if confirm "Shut the Pi down now?"; then
            run sudo poweroff
            exit 0
        fi
        say "Not shutting down - only for a card with its own power supply:"
    else
        say "Now:"
    fi
    say "  1. Power the card off."
    say "  2. Move its W5/W6 jumpers to the setting the 7i92 manual calls EEPROM."
    say "  3. Power it back on. It will answer at $new_ip."
    say "If the Pi restarts when the card powers on, log back in and run this"
    say "again with 'check'."
    say "To undo: jumpers back to the factory setting = $FACTORY_CARD_IP again."
    pause ""

    if ip -4 addr show | grep -q "inet ${PI_IP%/*}/"; then
        say "Checking the card answers at $new_ip..."
        if wait_for_card "$new_ip"; then
            say "Card at $new_ip answers."
        else
            warn "No card answered at $new_ip. Check its power, cable and that      "
            warn "W5/W6 are at the EEPROM setting, then run this again with 'pi'.   "
            exit 1
        fi
    fi
}

# A card takes a few seconds to answer after power-on; try for up to
# about 15 seconds.
wait_for_card() {
    local tries
    for tries in 1 2 3 4 5; do
        card_answers "$1" && return 0
        sleep 3
    done
    return 1
}

# --- move the Pi ------------------------------------------------------
# Gives the Pi's wired connection the address $1 (with /24). Stored in
# the connection, so a restart keeps it.
set_pi_address() {
    run nmcli con mod "$CONNECTION_UUID" ipv4.method manual ipv4.addresses "$1" ipv4.gateway "" ipv4.dns "" connection.autoconnect-priority 10
    if [ $? != 0 ]; then
        warn "Changing the '$CONNECTION' connection failed - nothing else was changed."
        exit 1
    fi
    run nmcli con up "$CONNECTION_UUID"
    sleep 2
    remove_spare_connections
}

# Offers to delete the other connections called "Wired Ethernet" (left
# by earlier installer runs - Rich's Pis had two or three). They do no
# harm while the one used here has the higher priority, but one is less
# confusing.
remove_spare_connections() {
    local spares uuid
    spares=$(nmcli -t -f UUID,NAME con show 2>/dev/null \
        | awk -F: -v n="$CONNECTION" -v keep="$CONNECTION_UUID" '$2 == n && $1 != keep {print $1}')
    [ -z "$spares" ] && return 0
    say "This Pi has $(echo "$spares" | wc -l) more connection(s) called '$CONNECTION', not in use:"
    for uuid in $spares; do
        say "    $uuid  $(nmcli -g ipv4.addresses con show "$uuid" 2>/dev/null)"
    done
    if confirm "Delete them (the one in use is kept)?"; then
        for uuid in $spares; do
            run nmcli con delete "$uuid"
        done
    fi
}

move_pi() {
    title "Move the Pi's wired connection to ${PI_IP%/*}"
    stop_if_linuxcnc_running
    set_pi_address "$PI_IP"
    for card_ip in "$BASE_CARD_IP" "$EXPANSION_CARD_IP"; do
        if card_answers "$card_ip"; then
            say "Card at $card_ip answers."
        else
            say "No card at $card_ip (fine if that card isn't set up or connected)."
        fi
    done
}

# --- check ------------------------------------------------------------
check_network() {
    title "Network check"
    stop_if_linuxcnc_running
    local addr card_ip
    addr=$(ip -4 -o addr show dev eth0 2>/dev/null | awk '{print $4}' | head -1)
    say "Pi's wired connection (eth0): ${addr:-no address - is the cable plugged in?}"
    case "$addr" in
        10.10.10.*)  for card_ip in "$BASE_CARD_IP" "$EXPANSION_CARD_IP"; do
                         if card_answers "$card_ip"; then
                             say "Card at $card_ip answers."
                         else
                             say "No card at $card_ip (fine for $EXPANSION_CARD_IP if there's no expansion box)."
                         fi
                     done ;;
        192.168.1.*) if card_answers "$FACTORY_CARD_IP"; then
                         say "Card at $FACTORY_CARD_IP answers (not yet moved to 10.10.10.x)."
                     else
                         say "No card at $FACTORY_CARD_IP."
                     fi ;;
    esac
}

# --- put the Pi back --------------------------------------------------
move_pi_back() {
    title "Put the Pi's wired connection back on ${OLD_PI_IP%/*}"
    stop_if_linuxcnc_running
    say "Use this to reach a card at its factory address, or to run software"
    say "from before the two-box change. A card already moved to 10.10.10.x"
    say "also needs its W5/W6 jumpers back at the factory setting."
    confirm "Continue?" || exit 0
    set_pi_address "$OLD_PI_IP"
    if card_answers "$FACTORY_CARD_IP"; then
        say "Card at $FACTORY_CARD_IP answers."
    else
        say "No card at $FACTORY_CARD_IP yet."
    fi
}

# --- main -------------------------------------------------------------
$DRY_RUN && warn "DRY RUN - commands are shown, not run.                              "
if [ -z "$CHOICE" ]; then
    title "Rosetta - network setup"
    echo "  1) Set up a card as the base card       ($BASE_CARD_IP)"
    echo "  2) Set up a card as the expansion card  ($EXPANSION_CARD_IP)"
    echo "  3) Move the Pi's wired connection to    ${PI_IP%/*}"
    echo "  4) Put the Pi back on                   ${OLD_PI_IP%/*}"
    echo "  5) Check the network"
    read -r -p "Choose 1-5: " pick
    case "$pick" in
        1) CHOICE=base ;; 2) CHOICE=expansion ;; 3) CHOICE=pi ;; 4) CHOICE=back ;; 5) CHOICE=check ;;
        *) echo "Nothing chosen."; exit 0 ;;
    esac
fi
case "$CHOICE" in
    base)      set_up_card "$BASE_CARD_IP" base ;;
    expansion) set_up_card "$EXPANSION_CARD_IP" expansion ;;
    pi)        move_pi ;;
    back)      move_pi_back ;;
    check)     check_network ;;
esac
title "Done"
