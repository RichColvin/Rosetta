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
# File:
#   docs/build_manuals.py
#
# Purpose:
#   Refreshes the parts of the offline manuals (Rosetta_User_Manual/,
#   Rosetta_Gcode_Library/) that are made from the pages themselves.
#   Run it after editing, adding or renaming a manual page, and at every
#   release (after the version label in Rosetta_Panel_v1.ui changes):
#
#       python3 docs/build_manuals.py
#
#   It writes, in both folders:
#     - search-index.js: every page's title, headings and text, for the
#       search box in the header (rosetta-docs.js). A script file, not
#       JSON, so it loads from file:// with no web server.
#     - each page's Previous / Next links (between <!--pager--> and
#       <!--/pager-->), in the order of that manual's contents page
#       (index.html). Pages the contents page doesn't link get none.
#     - each page's version line under the title in the header (between
#       <!--version--> and <!--/version-->), the same text as the
#       programs show: OS_Version_Label in
#       Rosetta_Display/Rosetta_Panel_v1.ui.
#   Running it twice changes nothing the second time. Standard library
#   only, so it runs on the Pi or a Mac.
#
# Version
#   1.0 - 21 November 2026
#   1.1 - 21 November 2026 - the version line moved to the header
#
# Copyright (c) 2026 Colvin Tools and Brainwave Embedded.
#
# The MIT/X Consortium License applies - see LICENSE.
#######################################################################

import html
import json
import os
import re
from html.parser import HTMLParser

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUALS = (("Rosetta_User_Manual", "User Manual"),
           ("Rosetta_Gcode_Library", "Gcode Library"))
PANEL_UI = os.path.join(REPO, "Rosetta_Display", "Rosetta_Panel_v1.ui")


class Page(HTMLParser):
    '''Title, headings (id, text) and plain text of a manual page's
    <div class="content"> (plus its <h1>), and its local links in order.'''

    SKIP = {"script", "style", "nav", "math"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.heads, self.text, self.links = "", [], [], []
        self._in_h1 = self._depth = 0
        self._content = False
        self._content_depth = 0
        self._skip = 0
        self._head = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "content" in (a.get("class") or "").split():
            self._content, self._content_depth = True, 0
        if self._content and tag == "div":
            self._content_depth += 1
        if tag in self.SKIP:
            self._skip += 1
        if tag == "h1" and not self._content and not self.title:
            self._in_h1 = 1
        if self._content and tag in ("h1", "h2", "h3") and a.get("id"):
            self._head = [a["id"], ""]
        if self._content and tag == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == "h1" and self._in_h1:
            self._in_h1 = 0
        if self._head and tag in ("h1", "h2", "h3"):
            self.heads.append((self._head[0], " ".join(self._head[1].split())))
            self._head = None
        if self._content and tag == "div":
            self._content_depth -= 1
            if self._content_depth == 0:
                self._content = False

    def handle_data(self, data):
        if self._in_h1:
            self.title += data
        if self._content and not self._skip:
            self.text.append(data)
            if self._head:
                self._head[1] += data


def parse(path):
    p = Page()
    p.feed(open(path, encoding="utf-8").read())
    p.title = " ".join(p.title.split())
    return p


def version():
    m = re.search(r'id="OS_Version_Label".*?<property name="label"[^>]*>([^<]+)</property>',
                  open(PANEL_UI, encoding="utf-8").read(), re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def contents_order(folder, pages):
    '''Local pages in the order the contents page first links them.'''
    order = []
    for href in pages["index.html"].links:
        if "/" in href or href.startswith(("http", "mailto", "#")):
            continue
        name = href.split("#")[0]
        if name.endswith(".html") and name != "index.html" and name in pages and name not in order:
            order.append(name)
    return order


def replace_block(text, marker, new):
    start, end = "<!--%s-->" % marker, "<!--/%s-->" % marker
    if start in text:
        return re.sub(re.escape(start) + ".*?" + re.escape(end), lambda m: start + new + end, text, flags=re.S)
    return None


def main():
    label = version()
    data = {}
    for folder, name in MANUALS:
        base = os.path.join(REPO, folder)
        data[folder] = {f: parse(os.path.join(base, f))
                        for f in sorted(os.listdir(base)) if f.endswith(".html")}

    for folder, name in MANUALS:
        base = os.path.join(REPO, folder)
        pages = data[folder]

        # --- search index (paths relative to this folder) ---
        entries = []
        for other, other_name in MANUALS:
            prefix = "" if other == folder else "../%s/" % other
            for f, p in data[other].items():
                text = " ".join(" ".join(p.text).split())
                entries.append({"u": prefix + f, "m": other_name, "t": p.title,
                                "h": p.heads, "x": text})
        js = ("// Made by docs/build_manuals.py - don't edit; run it again instead.\n"
              "window.ROSETTA_SEARCH = " + json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + ";\n")
        open(os.path.join(base, "search-index.js"), "w", encoding="utf-8").write(js)

        # --- previous / next, version line ---
        order = contents_order(folder, pages)
        for f in pages:
            path = os.path.join(base, f)
            text = open(path, encoding="utf-8").read()
            new = text
            if f in order:
                i = order.index(f)
                links = []
                if i > 0:
                    links.append('<a class="pager-prev" href="%s"><span>Previous</span>%s</a>'
                                 % (order[i - 1], html.escape(pages[order[i - 1]].title)))
                links.append('<a class="pager-contents" href="index.html"><span>%s</span>Contents</a>' % name)
                if i < len(order) - 1:
                    links.append('<a class="pager-next" href="%s"><span>Next</span>%s</a>'
                                 % (order[i + 1], html.escape(pages[order[i + 1]].title)))
                pager = '<nav class="pager" aria-label="Previous and next page">%s</nav>' % "".join(links)
            else:
                pager = ""
            if "<!--pager-->" not in new:
                new = new.replace("</main>", "<!--pager--><!--/pager-->\n</main>", 1)
            new = replace_block(new, "pager", pager)
            stamp = html.escape(label)
            if "<!--version-->" in new:
                new = replace_block(new, "version", stamp)
            if new != text:
                open(path, "w", encoding="utf-8").write(new)
        print("%s: %d pages, %d in contents order, search index %d KB"
              % (folder, len(pages), len(order), len(js) // 1024))
    print("Version line:", label or "(not found)")


if __name__ == "__main__":
    main()
