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
#                         Rosetta                                     #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   rosetta_phone_alerts.py
#
# Purpose:
#   Phone alerts (15 November 2026, Rich): sends a message to the
#   operator's phone through the free ntfy app (https://ntfy.sh) when
#   a program, Sync Move or Cut Thread finishes, a program pauses at
#   M0/M1/M60, the fault siren goes off, the Raspberry Pi reaches its
#   Alarm temperature, or a box loses contact with the Pi. The
#   operator subscribes to a "topic" (a private name, like a
#   password - anyone who knows it can read the alerts) in the app;
#   the Pi posts each alert to that topic.
#
#   Shared by Rosetta_main.py (sends the alerts), Rosetta_Settings.py
#   (the settings and its Send Test Message button) and
#   Rosetta_Setup/Rosetta_Generate_Local_Ini.py (wires the fault
#   siren's pulse to the panel when the fault alert is on), like
#   rosetta_settings_io.py.
#
#   RosettaSet_v1.ini keys (all in the seed file):
#     phone_alerts         true/false (default false)
#     phone_alerts_topic   the ntfy topic ("" until one is made)
#     phone_alerts_events  list of EVENT ids to send (default all)
#
#   A convenience only: it needs the internet, and a message that
#   can't be sent is lost (printed to the console, never retried).
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 15 November 2026
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

import json
import os
import re
import secrets
import threading
import urllib.error
import urllib.request

# ntfy's public server. Messages are posted as JSON to its root, which
# (unlike the plain "Title:" header form) carries any UTF-8 text - °C.
NTFY_SERVER = "https://ntfy.sh"
SEND_TIMEOUT_SECONDS = 10

# Event id -> what Rosetta Settings calls it. The ids are what
# RosettaSet_v1.ini's phone_alerts_events lists.
EVENTS = (
    ("done", "Finished"),
    ("pause", "Paused (M0/M1)"),
    ("fault", "Fault siren"),
    ("pi_temp", "Pi too hot"),
    ("card", "Box lost contact"),
)
EVENT_IDS = tuple(e for e, _ in EVENTS)

# ntfy priorities: 3 = default, 4 = high, 5 = urgent (the app makes
# more noise and can break through Do Not Disturb if allowed).
PRIORITY_NORMAL = 3
PRIORITY_HIGH = 4
PRIORITY_URGENT = 5

# Topics ntfy accepts: letters, digits, _ and -, at most 64.
TOPIC_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TOPIC_PREFIX = "rosetta-"
TOPIC_RANDOM_CHARS = 12
TOPIC_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"   # no l/o/0/1 - easy to retype

SERIAL_PATH = os.path.expanduser("~/.config/Rosetta/serial")


def new_topic():
    '''A new, hard-to-guess topic, e.g. "rosetta-k7m2q9xh4c3w".'''
    return TOPIC_PREFIX + "".join(secrets.choice(TOPIC_ALPHABET) for _ in range(TOPIC_RANDOM_CHARS))


def topic_ok(topic):
    return bool(TOPIC_PATTERN.match(topic or ""))


def settings_from(settings):
    '''
    (enabled, topic, set of event ids) from RosettaSet_v1.ini's
    settings. Not enabled when the topic isn't a valid ntfy topic.
    '''
    topic = settings.get("phone_alerts_topic", "")
    topic = topic.strip() if isinstance(topic, str) else ""
    events = settings.get("phone_alerts_events", list(EVENT_IDS))
    if not isinstance(events, list):
        events = list(EVENT_IDS)
    enabled = settings.get("phone_alerts") is True and topic_ok(topic)
    return enabled, topic, set(e for e in events if e in EVENT_IDS)


def title():
    '''"Rosetta", plus ", S/N n" once the owner has set a serial number.'''
    try:
        with open(SERIAL_PATH) as f:
            serial = f.read().strip()
    except OSError:
        serial = ""
    return "Rosetta, S/N " + serial if serial else "Rosetta"


def send_now(topic, message, priority=PRIORITY_NORMAL, tags=None):
    '''
    Posts one message and waits for ntfy's answer. Returns None when
    sent, else a short description of what went wrong.
    '''
    body = {"topic": topic, "title": title(), "message": message, "priority": priority}
    if tags:
        body["tags"] = list(tags)
    request = urllib.request.Request(
        NTFY_SERVER, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=SEND_TIMEOUT_SECONDS) as response:
            response.read()
        return None
    except urllib.error.HTTPError as e:
        return "the ntfy server answered %d %s" % (e.code, e.reason)
    except urllib.error.URLError as e:
        return "couldn't reach the ntfy server (%s) - is the Pi on the internet?" % e.reason
    except OSError as e:
        return "couldn't reach the ntfy server (%s)" % e


def send(topic, message, priority=PRIORITY_NORMAL, tags=None):
    '''
    send_now in a background thread, so LinuxCNC's panel never waits
    on the network. The outcome is only printed.
    '''
    def worker():
        problem = send_now(topic, message, priority, tags)
        if problem:
            print("Phone alert not sent (" + message + "): " + problem, flush=True)
        else:
            print("Phone alert sent: " + message, flush=True)
    threading.Thread(target=worker, daemon=True).start()
