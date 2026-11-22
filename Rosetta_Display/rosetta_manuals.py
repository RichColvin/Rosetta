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
#   rosetta_manuals.py
#
# Purpose:
#   Opens a page of the User Manual or Gcode Library in the browser -
#   the copy on this machine (Rosetta_User_Manual/ and
#   Rosetta_Gcode_Library/ in the repo, which arrive with every git
#   pull), so no Internet connection is needed. If that page's file
#   isn't there, the same page on the website is opened instead.
#
#   Imported by Rosetta_main.py (the Help tab's User Manual, Gcode
#   Library and Ornamental Turner's Handy Book buttons), Rosetta_Settings.py (the User Manual buttons
#   beside its notes) and the Rosette and Geometric Chuck Designers
#   (the buttons beside their notes).
#
#   Pages are named as their files are, without ".html" (e.g.
#   "InputsOutputsSound"); "index" is a manual's contents page. The
#   anchor is a heading or [[#Name]] id inside the page.
#
#   A local page with an anchor (file:///...#LimitSwitches) is handed
#   straight to a browser: xdg-open/exo-open treat a file:// address as
#   a file and drop the part after "#". The default browser
#   (xdg-settings) is tried first, then Chromium and Firefox; with none
#   of those it falls back to Python's webbrowser module, as before.
#
# End User Customisation:
#   THE END USER OF THE ROSETTA SYSTEM SHOULD NOT MODIFY
#   THIS FILE.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 21 November 2026
#   1.1 - 21 November 2026 - document_url(): documents shipped with the
#         User Manual, such as the Ornamental Turner's Handy Book (PDF)
#   1.2 - 22 November 2026 - the website fallback is the website's copy
#         of the HTML folders, not the PmWiki pages
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

import os
import pathlib
import shutil
import subprocess
import webbrowser

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# section -> (folder in the repo, the website's copy of that folder).
# The website serves the same HTML folders (since 22 November 2026), so
# a page is <folder>/<page>.html there too.
SECTIONS = {
    "manual": ("Rosetta_User_Manual",
               "https://rosetta.colvintools.com/Rosetta_User_Manual/"),
    "gcode":  ("Rosetta_Gcode_Library",
               "https://rosetta.colvintools.com/Rosetta_Gcode_Library/"),
}

# Browsers that accept a file:// address with an anchor, by command.
BROWSERS = ("chromium", "chromium-browser", "firefox-esr", "firefox")


def page_url(page="index", anchor="", section="manual"):
    '''
    The address of a manual page: the local file if it's on this
    machine, otherwise the website's copy.
    '''
    folder, online = SECTIONS[section]
    fragment = "#" + anchor if anchor else ""
    path = os.path.join(REPO_DIR, folder, page + ".html")
    if os.path.isfile(path):
        return pathlib.Path(path).as_uri() + fragment
    return online + page + ".html" + fragment


def document_url(name, online):
    '''
    A document shipped with the User Manual (Rosetta_User_Manual/
    Documents/, e.g. "OTHB.pdf"): this machine's copy if it's there,
    otherwise the online address given.
    '''
    path = os.path.join(REPO_DIR, "Rosetta_User_Manual", "Documents", name)
    return pathlib.Path(path).as_uri() if os.path.isfile(path) else online


def _browser_commands():
    '''The default browser's command first, then the others found.'''
    found = []
    try:
        default = subprocess.run(["xdg-settings", "get", "default-web-browser"],
                                 capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        default = ""
    default = default[:-len(".desktop")] if default.endswith(".desktop") else default
    for name in ((default,) if default else ()) + BROWSERS:
        if name and name not in found and shutil.which(name):
            found.append(name)
    return found


def open_url(url):
    '''Opens url in the browser without waiting for it.'''
    if url.startswith("file://"):
        for command in _browser_commands():
            try:
                subprocess.Popen([command, url], start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except OSError:
                continue
    webbrowser.open(url)


def open_manual(page="index", anchor="", section="manual"):
    '''Opens a manual page (see page_url) and returns its address.'''
    url = page_url(page, anchor, section)
    open_url(url)
    return url
