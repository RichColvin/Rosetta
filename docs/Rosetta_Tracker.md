# Rosetta Tracker

The one list of open, untested and recently settled items for Rosetta
(the Rose Engine Butler until 02 November 2026 - entries from before
then use the old REB_* file names). It lives in the repo so every Claude
Code session (the Pi and the Mac) and everyone working on Rosetta sees
the same list after a `git pull`. Claude sessions keep their own per-machine notes, which the
other machine can't see - anything that matters goes here instead.

How to use it:

- Add an item when something is built but not yet run on a machine, a
  problem is found, or a follow-up is agreed. Give it a date.
- When an item is settled, move it to **Done** with the date and how it
  was settled (tested on which machine, fixed in which commit, dropped).
- Dates use a two-digit day: 08 October 2026.

Last reviewed: 11 October 2026.

## Untested on a machine

Built and committed, but not yet seen working on real hardware.

| Item | Since | What to check |
|---|---|---|
| Rosette Designer, stage 1 | 15 November 2026 | Built on branch `rosette-designer`, merged into `dev-rich` 15 November 2026, on `main` the same day (Beta 1.10). User Manual drafts updated for everything built that day. Checked off the machine: the shapes' maths (range, each turn closing, phase in both units, straight polygon sides at any phase, chord tolerance incl. sharp points); all 96 sample programs (4 shapes x rocking/pumping/both x face/side x passes/turns x inch/mm) run through the standalone `rs274` interpreter to the end, every move matching the maths; the window rendered off-screen for each kind of drawing; save/reopen round trip; reserved names refused; the menu step in a scratch home. Check on the machine: (1) **Lotus and Tudor** - redrawn 15 November 2026 after Rich found them wrong (the sine was right): now matched to the MDF Rose Engine's near-side paper-chuck pictures (lotus: polygon sides with a V notch mid-lobe; Tudor: round petals with a sharp barb at each join; comparison in `~/Downloads/Rosette_Shapes_vs_Paper_Chuck.png` on Rich's Pi). Check they look right in the Designer's drawing and on a paper chuck. The plain polygon was left alone - the photo's corners are slightly rounder, the rubber's doing (stage 3). (2) Applications > Rosetta > Rosette Designer appears (after an Update, or run `Rosetta_Setup/Rosetta_Add_Rosette_Designer.sh`). (3) Save a Sine 12, rocking, face; open it in Rosetta - AXIS's preview shows the pattern. (4) Air-cut it (cutter clear of the work), passes = 3: plunge, three turns, back out, C reading +1080, X/Z back where they started; one turn takes about the time the designer said. (5) Pumping on the face and on the side, and a lotus (sharp points - C should slow only slightly there). (5a) **Motion: Both** (added the same day at Rich's request - a rocking rosette for X and a pumping one for Z, side by side in the window; c8372ba): e.g. Lotus 8 rocking + Sine 24 pumping on the face - X and Z both move during each turn, plunges still on Z. (6) With Rosetta running, Save offers to open it in Rosetta. (7) **Radius is the Outside / Inside** (added the same day, Rich's request): with a Lotus 8 rocking on the face, the drawing's grey circle touches the petals' outer edges (Outside) or the points (Inside), and the note under the drawings gives where to start the cutter - air-cut from there and check X's furthest-out / closest-in reading is the Radius; Straight sides on a polygon gives straight sides with either. (8) **One copy only**: open Rosette Designer from the menu twice - the second brings the first window forward, no new window (also when it's behind Rosetta), with an "already open" message. (9) The window opens full screen, with notes on the right (Rich, same day); each User Manual button opens the Rosette Designer page at its section once the page is published (anchors Movement, Rosette, Depth, ObjectSize, Saving). (10) **Finishing pass and spring passes** (added the same day, Rich: rough fast, finish slow): Passes mode, Finishing pass ticked at 10%, Spring passes 1 - air-cut: the last pass and the spring pass turn C at a tenth of the speed, the spring pass stays at the final depth (no plunge), and the whole run takes about what the note under the drawings says. Checked off the machine: all 96 samples (now with a finishing and a spring pass) run to the end in `rs274`, finishing/spring feeds exactly 10% of the others. (11) **Pass counter** on the panel's progress bar ("Program 42% - pass 2 of 3", then finishing pass, spring pass; "turn 1 of 2" for Turns at one depth) - seen working on Rich's machine 15 November 2026 after a first version missed it; still to see: Turns mode, and that Stop leaves "Program stopped at N% - pass 2 of 3". User Manual drafts in `~/Downloads/Rosetta_UserManual_RosetteDesigner_2026-11-15` on Rich's Pi (new page Rosette Designer, home page link) - published 15 November 2026 with a screenshot of the window (Rich). |
| Script fixes from the Support Manual write-up | 18 October 2026 | On `dev-rich` (made 18 October 2026, lost in a merge on the Mac, re-applied 24 October 2026): `REB_Update.sh` and `REB_Install_Debian_13_Trixie.sh` are now marked runnable; the installer's first line is `#!/bin/bash` (was `#! /home/reuben/Downloads`), a failed step now exits with code 1 (`exit $?` after an `echo` always gave 0), it copies `REB_Update.sh` and `REBset_v1.ini` without `sudo`, so reuben owns them, and its Step 1 message no longer says "connectin"; `REB_Update.sh`'s "local changes" warning names the Support Manual page "Updating Rose Engine Butler" (it said "Updates and Branches", which doesn't exist); `REB_Settings.sh`/`REB_Launch.sh` header comments updated. Check: after an update the icon still runs `REB_Update.sh` and its warning text fits the box; on the next fresh install `ls -l ~/Documents/REBset_v1.ini ~/REB_Update.sh` shows reuben as owner. |
| Bench checkout (`REB_Checkout.sh`) | 18 October 2026 | Written on the `two-box` branch 18 October 2026 but left out of its merge; on `dev-rich` since 24 October 2026. First run on S/N REB003 with a labelled test motor on each channel: `./REB_Checkout.sh` in a terminal; check each channel's motor turns channel+1 times each way in both passes, the spindles index in quarter turns (`M19 R.. $n`), the all-together move finishes together, the program's `M0` pauses and `(MSG,...)` lines show in AXIS, and `~/Documents/REBset_v1.ini` is identical to the backup in `~/Documents/Checkout/<run>/` afterwards (also after a Ctrl+C part way). Assumes 6400 steps per turn (`--steps-per-rev` otherwise). |
| C top speed 30°/s | 07 October 2026 | A 360° G0 rewind of C takes about 12 s (was 36 s). Then time a full run of Roy's Pumping5Sides program - estimated about 46 minutes (was about 4 hours). |
| Threading tab | 24 September 2026 | C turns the right way for a right-hand thread, and outside threading feeds in toward -X. |
| EtherLab key refresh in `REB_Update.sh` | 08 October 2026 | Tested on its own (current key, stale key, server unreachable), not yet as part of a full update run. |
| Notes in REBset_v1.ini | 11 October 2026 | After an update (run twice on Chuck's and Roy's machines), `~/Documents/REBset_v1.ini` starts with the "Rose Engine Butler settings" notes and ends with the copyright, and the other settings/export files there have their notes too (not the `.bak-` backups); LinuxCNC and REB Settings still start, and Load Settings reads both a "Save All Settings As..." copy and a Save Subset export. |
| Folder shortcuts on other machines | 20 October 2026 | `REB_Setup/REB_Add_Shortcuts.sh` (265ca51): Thunar Places "RoseEngineButler" and "Gcode", plus Reuben-head launchers for them on the bottom bar right after File Manager (Gcode's icon has a "G" badge). Tested on Rich's Pi (from a clean state, re-run, `--force` - nothing doubled). Still to see: the Trixie installer's new Step 10 on a fresh install (the Bookworm installer wasn't changed), and S/N 1 and 2 getting them on their first update once `main` moves (via `REB_Update_Settings.py`) - their bottom bar may be laid out differently; with no File Manager launcher the launchers are skipped but Places is still added. |
| Startup gcode reserved-name check | 23 October 2026 | New REB Settings > Other tab > Startup File Check radios (Abort startup - default, or Warn but continue), plus a scan added to `REB_Setup/REB_Generate_Local_Ini.py` (`check_reserved_gcode_names`, run from `main()` before anything else): refuses, or warns, if `gcode/` holds a file starting with "reb"/"REB" (any case) or named M100-M199, since LinuxCNC's `PROGRAM_PREFIX` search would find such a file before REB's own subroutines/M-codes - see "Reserved names" in CLAUDE.md. REBset_v1.ini's `startup_file_check` ("abort"/"warn"), seeded in `REB_Setup/REBset_v1.ini`. Verified stand-alone on Rich's Pi 23 October 2026 (no LinuxCNC running): the Abort and Warn GTK dialogs both render correctly with the offending file(s) listed, the scan correctly matches `reb_test.ngc`/`REBrose.ngc`/`M105.ngc`/`m199` and excludes `m200.ngc`/`myprogram.ngc`/`M1.ngc`, and the Settings radios save/load round-trip. Not yet run through a real `REB_Launch.sh` -> `linuxcnc` start: check a reserved file in `gcode/` is caught at a real launch, Abort stops before LinuxCNC opens (and the dialog's wording is legible full-size), Warn shows the dialog then LinuxCNC starts normally, and a clean `gcode/` launches with no dialog at all. Also added the same day: Abort plays a new short "uh oh" sound (`REB_Display/Sounds/REB_Abort.wav`, two tones, raised an octave per Rich's ear) on the speaker - the fault siren was tried first and found too alarming for a renamed-file nag; not yet heard through a real launch, only the stand-alone test. |
| Sync Move changes, Beta 1.7 | 13 November 2026 | Agreed with Rich and built the same day (Rich's reason: users often ask for a large rotation, and need to stop a move part way - a broken cutter belt, a cutter about to hit the chuck; Roy finds limit switches a good option but rarely uses them). Checked off the machine only (LinuxCNC was running on Rich's Pi): the panel rendered off-screen (both tabs 880 px wide, 23 more than before - no shift between tabs), the comma/deg/rev handling on the real .ui, and Pause/Continue/Return run against a stand-in for LinuxCNC. Check on the machine, with LinuxCNC restarted: (1) A/B/C Distance takes `1,000,000` and `1000000`, shows `1,000,000.00`; deg/rev radios - 40 then rev sends `C14400` (console `print`), rev has 3 decimals, switching keeps the number; deg/rev comes back after a restart. (2) **Pause on a panel MDI move works on LinuxCNC 2.9.10** - Pause during a Sync Move: axes slow and stop, button reads Continue, progress bar "(paused)"; Continue resumes. If the console says "Sync Move didn't pause - stopping it instead", pause doesn't work in MDI and every Pause becomes a stop (Continue still finishes it, as a new move). (3) E-stop (or F2 off) while paused, back on, Continue: finishes along the same line, done beeps at the end. (4) Jog an axis while stopped, Continue: asks, naming that axis. (5) Return to Start while paused: stops, then goes back. (6) Pause button: set a limit jack to Pause button in Rosetta Settings (only one allowed - "Duplicate!"), plug in an NC push button; pressing pauses a Sync Move and a G-code program, not Cut Thread - 13 November 2026: Rich confirmed it pauses a program; a second press doesn't resume (by design - no debounce), so at Rich's request the panel's Continue (Sync Move tab) now resumes a paused program too, like AXIS's Resume - check that; with it pressed or unplugged, Sync Move and AXIS's Run refuse with "Pause button is pressed or disconnected". `halcmd show sig pause-button` shows it. User Manual: published by Rich 13 November 2026 (checked against the drafts: Synchronized Movement, Inputs, Outputs, and Sounds - with a Pause Button link on the home page - and Limit Switch Cabling, retitled "Cabling Limit Switches & Pause Buttons"). Sync Move screenshot replaced 13 November 2026 (Beta 1.8 running on Rich's Pi: deg / rev radios - C on rev showing 35.000 - and Pause, greyed while idle, render correctly); Rich reworded its Step 1 the same day so it no longer refers to the picture (whose ENAs are all off). |
| Pi temperature monitor, Beta 1.8 | 13 November 2026 | Agreed with Rich and built the same day (see CLAUDE.md, "Pi temperature monitor"). Checked off the machine only: the panel header and Rosetta Settings' Other page rendered off-screen (panel width unchanged), the monitor run against fake temperatures (warning, alarm, hysteresis, undervoltage, the record), and the version report in a scratch home with sending off. Check on the machine, after restarting LinuxCNC: `Raspberry Pi NN °C` beside the logo matches `cat /sys/class/thermal/thermal_zone0/temp`; set Warning/Alarm low in Rosetta Settings (e.g. 55/60) to see orange + notice, then red + box + the new alarm sound (speaker); Warning >= Alarm is refused with a red note; Measurement System still works, now one row lower; `~/.config/Rosetta/pi_health.json` appears; after an Update the report (`~/.config/Rosetta/report_log.jsonl`) has the `pi_*` fields and the file is gone. **Server: done 13 November 2026** - Rich uploaded the updated `reb_report.php` (it kept only the fields it knew, so the `pi_*` fields would have been dropped) and `reb_report_view.php`; pages answer as before (405 / 401, `.jsonl` and `.htpasswd` 403); a real report from Rich's Pi (59.5 °C now, 66.1 °C highest since 17:37, no undervoltage) was accepted (200), `pi_health.json` was cleared, and Rich saw the four new columns filled in correctly in the viewer. Still to see: a report from a machine updating through `Rosetta_Update.sh` (not run by hand). User Manual: published by Rich 13 November 2026 (Other, Main Screen, Troubleshooting - checked against the drafts). Main screen screenshot replaced 13 November 2026: `Raspberry Pi 66 °C` shows beside the logo on Rich's Pi - the readout works on the machine; warning/alarm colours, box and sound still to see. |
## Open items and follow-ups

| Item | Since | Notes |
|---|---|---|
| Phone alerts User Manual pages | 15 November 2026 | Drafts in `~/Downloads/Rosetta_UserManual_PhoneAlerts_2026-11-15` on Rich's Pi (full page sources as of 15 November 2026: Inputs, Outputs, and Sounds - new Phone Alerts section, #PhoneAlerts, which Rosetta Settings' "How Phone Alerts Work" button opens; home page link; Troubleshooting "Phone alerts don't arrive", #phonealerts). Publish now that it's on `main`, then replace the Inputs, Outputs, and Sounds screenshot (new Phone Alerts row). |
| Can't get Rosetta back after minimizing it (GitHub #23) | 08 November 2026 | Roy minimized Rosetta while a program ran (to edit another G-code file); the program ran a while then stopped, and he couldn't bring the window back, so he powered off. Rich's Pi has a window list on the top panel, where a minimized Rosetta should show. Waiting on Roy: does his screen have a bar listing open windows (or is it auto-hidden), and does his program have `M0`/`M1` (a pause waiting for Resume would look like it stopped)? Then either make sure the window can be brought back, or stop it being minimized. 10 November 2026: Roy's screenshot (repeated before updating to 15) shows a window list at the top left, not hidden, listing only the text editor and the file manager - Rosetta isn't on it. A minimized window would still be listed there, and the workspace switcher at the top right doesn't draw minimized windows, which is why clicking it did nothing. So most likely LinuxCNC had closed (crashed), not just been minimized, which would also explain the program running on for a few seconds and then stopping. Asked Roy: was the screenshot taken while the program was still running, or after it stopped (if it was still running and Rosetta still isn't listed, the window list is hiding it instead); did a "LinuxCNC terminated with an error" window appear; and next time, before starting LinuxCNC again, send `~/linuxcnc_print.txt` and `~/linuxcnc_debug.txt` (each launch overwrites them) - an "X Error" there would point at AXIS's preview being minimized. Also to try: minimize Rosetta during a long program on Rich's Pi. |
| Release Notes page in the user manual | 20 October 2026 | New manual page Main.ReleaseNotes ("What's New in Rose Engine Butler"), linked from the home page's right column under "Rose Engine Butler Versions"; published by Rich 20 October 2026 with one entry, "REB O/S 1.0 - 20 October 2026", the original version. Each entry's heading is written exactly as the screen label reads ("REB O/S x.y - dd Month yyyy"). **At release (about April 2027):** set Version 1.0's date (heading and the example label) to the release date and drop "beta 1" from the five REB O/S labels ("REB O/S 1.0 - <release date>"). **After release, every time `main` is moved:** add an "REB O/S x.y - date" entry at the top (New / Changed / Fixed - a hidden template is on the page) and raise the REB O/S labels to that version and date, so owners can match their screen to the page. |
| Move S/N 2 (Roy's) to 10.10.10.x | 16 October 2026 | 08 November 2026: S/N 1 is moved (Rich); Roy hasn't updated S/N 2 yet. Steps are now `./Rosetta_Change_Network.sh base` etc. (the script was renamed with the Rosetta rebranding). Rich's decision: every machine and the shipping boxes on 10.10.10.x (base card .10, expansion .11, Pi .100), so a customer can just add an expansion box. The two-box work is on `main` since 20 October 2026, so each owner: update, then `REB_Change_Network.sh base` (card already has REB firmware - answer no to writing it), shut down, move W5/W6, switch on, `check`. Order doesn't matter: the generator uses 192.168.1.121 while the Pi is still on 192.168.1.x (91ca961). 20 October 2026: Rich sent both owners the steps (`REB_Change_Network.sh base`, shut down, W5/W6, switch on, `check`) - waiting to hear they've done it. Rehearsed on S/N REB003 (one card) 20 October 2026 - see Done. |
| Tell Roy about the C speed-up | 07 October 2026 | Close LinuxCNC, run the update **twice** in a row before starting LinuxCNC again, and check the output shows C's new limits. |
| Roy's program: skip the C rewinds | 07 October 2026 | Optional, Roy's call: resetting C's coordinate to 0 after each pass instead of rapiding back 360° would save the rewind time entirely. |

## Planning

Ideas and designs not yet being built. Nothing here has code yet.

### Software-defined rosettes - Rosette Designer (since 15 November 2026)

**Stage 1 built 15 November 2026 on branch `rosette-designer`, merged into `dev-rich` the same day** - see
"Untested on a machine" and CLAUDE.md "Rosette Designer". Stages 2-4
below are still plans.

Rich's idea: a program in which the operator defines a rosette (the
rose engine's cam - https://otbok.info/index.php?n=Main.Rosette) and
saves it as a G-code program: C turns the work, X follows the rosette
for **rocking**, Z for **pumping**. Purpose: try a rosette before buying
or making a physical one; also to use one that would be needed too
rarely to be worth making.

Other software: Bill Ooms' COrnLathe (GPL-3) also models rosettes.
Bill was contacted on 16 November 2026 and asked that his software not
be used for this. **Nothing from COrnLathe - code, documentation or
design - is used or consulted for the Rosette Designer, now or in later
stages.** Rosetta is MIT-licensed and the Designer is a clean-room
implementation (see Provenance below).

**Decided by Rich, 15 November 2026:**

1. Cuts on the **face and on the side** of the work.
2. **The operator positions the cutter**, as with a traditional
   rosette - the design doesn't plan the cutter. So the program starts
   from wherever the machine is (reads X/Z/C from #5420/#5422/#5425) and
   every move is relative to that.
3. First shapes: **sine (Holtzapffel A), plain polygon (Holtzapffel P),
   lotus, Tudor**.
4. **Simulate the rubber** - start with a point (the ideal shape) and
   add rubber shapes over time.
5. Name: **Rosette Designer**.
6. Phase entered **either way**: as a fraction of a lobe or in degrees
   of spindle rotation (like Sync Move's deg / rev). **Changed 15
   November 2026 (Rich):** no phase for a single rosette - the operator
   phases the work by indexing on the Rosetta panel, as a physical
   rosette's phasing holes would. Only the pumping rosette in Both keeps
   a Phase, relative to the rocking rosette (indexing turns both
   together, so can't set that).
7. **Depth is the operator's choice per design:** (a) passes with
   incremental depths, like Threading - the cutter steps deeper between
   turns with C stopped at the start angle, and **backs out** to the
   starting depth at the end; or (b) **the same depth every turn** -
   the rosette motion repeats for the chosen number of turns, and the
   operator goes deeper between runs (traditional). The depth axis is
   Z on the face, X on the side (rocking is always X, pumping always Z).
8. **C is not unwound** at the end (it reads e.g. 1080 deg after 3
   turns - same place); the program works from wherever C is.

**Provenance (clean room, 16 November 2026):** every shape and setting
in the Rosette Designer comes from public ornamental-turning sources or
from Rich's own machines, never from other rosette software:

- Rosette, rubber, rocking, pumping, lobes, amplitude, phasing, invert
  (far-side cutting): standard rose-engine practice, as described in
  Holtzapffel and on OTBoK (https://otbok.info/index.php?n=Main.Rosette).
- Sine (Holtzapffel A) and plain polygon (Holtzapffel P): written from
  the geometry - a cosine curve, and the chord of a regular polygon.
- Lotus and Tudor: measured off the paper-chuck pictures of the MDF
  Rose Engine's rosettes (https://www.colvintools.com/MDF-RE%20-%20Rosettes.html).
- Later stages (more Holtzapffel shapes, rubber simulation, etc.): work
  only from published references and Rich's own rosettes, and cite the
  source here when each shape or feature is added.

**Proposed (not yet agreed):**

- A new standalone program (Python/GTK, like Rosetta Settings and
  Backup - no LinuxCNC needed), menu/desktop launcher; the rosette maths
  in a module of its own so the window, the G-code writer and later
  exports share it.
- Stage 1: one rosette - shape, lobes, amplitude (peak to peak, machine
  units), phase (fraction of a lobe or degrees), invert, rubber =
  point; rocking (X) or pumping (Z); face or side; C speed (rev/min)
  and direction; depth option (a) passes + depth per pass or (b) number
  of turns at one depth. Live preview of the
  cut. Saves `<name>.ngc` into gcode/ (never starting with "Rosetta" -
  reserved). The G-code: G93 timed segments so C turns at a steady
  speed, sized by a chord tolerance, G64 P blending; backs out to the
  starting depth; C not unwound; the design kept in a header comment so it can be
  reopened. Warns if C or the rocking/pumping axis isn't assigned.
- Stage 2: Holtzapffel series, masks, symmetry, compound rosettes
  (rock and pump together, or two combined), saved designs.
  **Next shapes, agreed 15 November 2026 (Rich):** the Holtzapffel
  series from https://www.colvintools.com/MDF-RE%20-%20Rosettes.html -
  **D** (convex lobes), **F** (heart / Cupid's bow), **J** (arcs of
  eccentric circles, each with a sine wave on it) and **M** (long lobes
  3x the length, separated by short ones). One shape per series: the
  number is just the lobes (D-12 and D-30 are one shape, 12 or 30
  lobes) - except **F-1**, a single heart, which needs its own
  treatment. J and M names carry two numbers (J6-36, M18-42), so check
  what each means; they may need a second setting. Then an **ellipse**
  with settings the operator can play with to reshape it (e.g. the
  distance between the foci), written from an ellipse's own geometry.
  **Not to be added:** Jon Magill's own designs (Archie, GDP-3,
  Shamrock, Snowflake, PF-9, Z-12/18, Bumpy Ellipse) - Jon is particular about
  his work being shared; and the Oval, a variation of the ellipse.
  Method, as for Lotus and Tudor: match the shape to the rosette's
  near-side paper-chuck picture on its MDF Rose Engine page (the
  rosette's own outline is only a guide - the picture is what that
  engine's rubber gives), and show Rich a side-by-side comparison.
  **Source for the series A to Z** (Rich, 15 November 2026): he will
  scan the Holtzapffel & Co. guide *Patterns of Rosettes for the
  Holtzapffel rosette cutting frame* (late 1800s - out of copyright, so
  free to work from, and its pictures could go in the User Manual
  beside each shape). It shows the patterns each rosette cuts - what
  the shapes are matched against - and may list the series better
  than Holtzapffel's Volume V. **Scans arrived 15 November 2026:**
  `~/Downloads/Holtz Rose Cutting Frame Rosettes.pdf` on Rich's Pi (21
  pages; Rich installed poppler-utils the same day, so the Read tool
  can show pages, or `pdftoppm -f N -l N -r 110 -png <pdf> pN`). Where
  things are: p1-2 title and introduction; p3 simple patterns from
  rosettes A-F; p4 (the original's page 135, compound
  patterns from D) - **ignore it** (Rich); **p5-14 the series, each rosette at its
  lobe counts** - A p5, B p6, C p6-7, D p7-8, E p8-9, F p9 (F 3/4/6/8),
  G p9-10, H p10, I p10-11, J p11, K p11, L p12, M p12, N p12, O p13,
  P p13, Q p14, R p14, S 32 p14 (a heart) - the series ends at S, not
  Z; p15-18 one rosette per letter (A10, B15, C10, D10, E30,
  F4, G8, H12, I24, J24, K4, L12, M18, N15, O18, P18, Q24, R18, S32) -
  a modern 3D simulation on the left, a paper drawing on the right;
  Rich says the paper drawings can be used (a clear single-pattern
  reference for each letter);
  p19 effects of pumping and phasing (A10, C10, D10, F3); p20-21 "The
  Rosette Designing Instrument" (de la Condamine, 1733, via Paul
  Ferraglio, SOT Bulletin 52; Jerry Decker's modern build). p1-14 are
  the old Holtzapffel guide; p15-21 are a modern write-up - its paper
  drawings (right-hand side of p15-18) can be used (Rich); keep its
  3D simulations and text as reference. Start with D, and C with it:
  **C is the inverse of D** (Rich, 15 November 2026). Invert already
  turns any rosette over, for pumping as well as rocking (on a rose
  engine only rocking can swap sides - near side / far side - which is
  why C exists as a rosette of its own), but list C as its own shape
  (D turned over) so it can be found by its Holtzapffel letter. Check
  each letter for being another one turned over before writing a new
  shape.
  **Bill Ooms' program:** Bill asked (16 November 2026) that his
  software not be used - don't look at it; see Provenance above. Work
  the profiles out from the PDF's drawings instead.
  **From p20-21, for stage 3/4** (Rich: de la Condamine's approach is
  still used today): the instrument works backwards - the pattern
  wanted at a small radius is traced, with a rubber on one side of a
  rail and a stylus on the other, into the rosette that cuts it, so
  the rosette has slower curves and the rubber runs smoothly (the
  rubber then has to be on the opposite side of centre to the cutter
  - our Invert). Use the same rubbers as the rose engine (chisel
  point or roller). A rosette can't make a backward loop, and the
  rubber jams on a steep radial rise unless the rosette turns the
  way that lets it climb the slow side; a "puffy" (convex-sided)
  polygon rosette cuts a straight polygon at a smaller radius, and a
  square one cut much smaller gives four leaves; cutting above or
  below centre distorts the pattern (Rosetta: cutter height). This is
  stage 4's "rosette from a design, rubber in reverse". **J6-36** (Rich): arcs of eccentric circles,
  each with a superimposed arc of sine waves - read as 6 arcs and 36
  sine waves around the whole rosette (6 per arc), so settings for
  arcs, waves and the waves' size against the arcs; confirm 36 is per
  rosette, not per arc, by counting the waves on one arc in a scan.
  M18-42 probably similar (two lobe counts) - check its page or scan.
  **Ellipse:** Rich has no concern about Jon here - an ellipse is a
  standard mathematical form; only the proportions of the one on
  ColvinTools are Jon's choice, so pick default proportions that look
  right to Rich.
  3D printing (stage 4, below) comes after these and after stage 3's
  rubbers.
- Stage 3: round rubber (radius r, needs the rosette's physical
  diameter - rounds points, can't reach narrow valleys), flat rubber.
  **Why a "sine" isn't simple** (Rich, 15 November 2026, from Jon
  Magill's 2018 OTI Symposium talk on designing rosettes,
  https://www.youtube.com/watch?v=TsBm2KsV0aI, and talking with him -
  details to get from Rich): stage 1 makes the cutter's motion an
  exact sine of the spindle angle (a point rubber following an ideal
  rosette). A physical rosette doesn't give that: the machine follows
  the rubber's centre, an offset of the rosette's edge, so a sine-edged
  rosette with a round rubber gives a non-sine motion (troughs
  narrowed, a rubber larger than a trough's curvature bridges it) - to
  get a true sine motion the rosette must be cut to the rubber's
  inverse offset (Lindow Rose Engine News: a true sine needs "the
  proper rubber"; a guilloche source: a touch half the lobe's radius
  gives a sine). Also: the rosette's own radius vs the cut's (the
  lever ratio, and the same angular wave looks different at another
  radius), and rocking moves in an arc about the pivot, not a straight
  line in X. Stage 3 should let the operator choose between "the
  motion I want" (today) and "what this physical rosette + rubber would
  do", and stage 4's rosette export needs the reverse.
  **Rosette size differs by machine** (Rich, 15 November 2026): the MDF
  Rose Engine's rosettes are about 7" across at their *smallest*
  (troughs), the Armbruster Mark II's about 7" at their *largest*
  (points), the Lindow's around 5". So wherever a rosette's diameter is
  entered (stage 3's rubber, stage 4's export, the machine ratio), let
  the operator say whether it's the largest or the smallest - as the
  Drawing Radius already does for the cut (Outside / Inside) - and
  offer these machines as starting values.
- Stage 4, making a physical rosette: export the rosette's outline
  (SVG/DXF) at a chosen diameter, with the rubber compensated in
  reverse; and for comparing with a bought rosette, a machine ratio
  (motion at the cut vs at the rosette).
  **3D printing** (Rich asked 15 November 2026): also save an STL of
  the rosette itself, written by the program (numpy only, nothing to
  install) - a rocking rosette as a disc whose edge follows the
  pattern; a pumping rosette as a ring whose face rises and falls with
  it. New settings, used only for this file: thickness, centre bore,
  and phasing holes (number, radius, size) - printed in, so the owner
  needn't drill them (see the Object Size note on phasing holes). Same
  rubber compensation in reverse as the outline, so it belongs after
  stage 3 (a point-rubber STL works, but cuts a little softer than
  designed). Printers hold about 0.1 mm (0.004 in) - fine for
  amplitudes of a few mm, marginal for very fine patterns - and plastic
  wears against the rubber, so it suits trying a design before making
  it in metal or wood.
  **Pumping rosettes - warn the user** (Rich, 15 November 2026), in
  the notes and when the STL is saved: a pumping rosette is printed
  lying flat, so its patterned face is built up in layers that leave
  ridges as the face rises and falls. Tell them (1) to set the
  printer for the smallest layer height it can print, and (2) to use a rubber that rides over what
  ridges remain, e.g. one with a roller bearing on its nose.
- Later: a main-panel tab that runs a saved rosette with phase/depth
  set on the panel, like Sync Move.
- Later, for depth option (b): LinuxCNC's external offsets (`eoffset`,
  `[AXIS_n]OFFSET_AV_RATIO`) let an axis be moved by hand (handwheel or
  panel buttons) while a program runs - the rosette could turn
  continuously while the operator feeds in, as on a physical rose
  engine. Needs Rosetta.ini/HAL changes.

### Rebranding: Rose Engine Butler -> Rosetta (since 02 November 2026)

Rose Engine Butler is being renamed **Rosetta**. Done so far: new images
(d733f26 - wallpaper, Reuben, Reuben-head launchers; the old ones kept in
`REB_Setup/Images/Saved Images/`), and on Rich's Pi, not yet committed,
REB Settings' page titles say "Rosetta". The website has started at
https://colvintools.com/Rosetta/UserManual/ and
https://colvintools.com/Rosetta/Support/ - a domain of its own may follow.

In the repo on 02 November 2026: "Rose Engine Butler" in 36 files,
"RoseEngineButler" (folder/repo name) in 23, "REB" as a word in 31, 107
files with REB in their name, and 13 web links to roseenginebutler.com.

**Decided by Rich, 02 November 2026:**

1. **File and program names: rename everything** `REB*` to `Rosetta*`
   (e.g. `Rosetta_Launch.sh`, `Rosetta_main.py`, `rosetta_thread.ngc`),
   on its own branch, before the April 2027 release. Some names need a
   new form, not a straight swap - to settle as the work starts:
   `REBset_v1.ini`, `reb_settings_io.py`, the `.REBset_v1.ini` export
   suffix, `REB.ini`/`REB.hal`, the `REB O/S` labels.
2. **GitHub: `RichColvin/Rosetta`** (from `RoseEngineButler/RoseEngineButler`
   - a transfer to Rich's account plus a rename). The machine folder
   becomes `~/linuxcnc/configs/Rosetta` to match. GitHub redirects a
   transferred/renamed repo's old address (including `git pull`) as long
   as nothing new is created at the old address - so don't reuse the
   `RoseEngineButler` organization's repo name - but each machine's
   remote should still be re-pointed by a one-time step rather than
   relying on the redirect. The name was taken by Rich's 2025 Rosetta
   project (CAD drawings, forum images - where `PIN_RosettaD_34` came
   from); Rich renamed it `RichColvin/Rosetta-2025` on 02 November 2026
   and archived it. **Done 02 November 2026:** Rich transferred this
   repo to his account and renamed it - it is now
   https://github.com/RichColvin/Rosetta (same repo, history and
   branches). The old address `RoseEngineButler/RoseEngineButler` still
   forwards: checked over both SSH and HTTPS (`git ls-remote` returns
   `dev-rich`), so built machines keep updating. Rich's Pi's remote now
   points at `git@github.com:RichColvin/Rosetta.git` (the remote is still
   named `RoseEngineButler`). The repo has left the organization, so
   anyone who had access through it (Chuck?) has to be added as a
   collaborator. Still to do: re-point the other machines and the Mac
   (`git remote set-url <remote> git@github.com:RichColvin/Rosetta.git`,
   or the one-time step in the file-rename work), and change any
   `git clone` address in the Support Manual's installation pages.
3. **Reuben is retired** - images, launcher icons, the "Reuben head"
   shortcuts. **The Pi login becomes `rosetta`** (was `reuben`). That
   path is in 52 lines across 18 tracked files (`/home/reuben/...`) -
   replace with `$HOME`/`~` or paths found from the script's own folder,
   so the code doesn't care what the login is. New installs create
   `rosetta`. Built machines: renaming a login (`usermod -l`/`-d -m`, the
   group, desktop auto-login, file ownership) has to be done while that
   user isn't logged in, so it can't run from the normal update - plan a
   separate, tested procedure (or a reinstall) per machine.
4. **Serial numbers use the prefix "Rosetta"** (e.g. Rosetta003; was
   REB003). The S/N is free text in `~/.config/REB/serial`, so built
   machines need it re-entered (or the one-time step rewrites a leading
   "REB"), plus new physical labels. The tracker's history keeps the old
   numbers.
5. **Web links go to colvintools.com/Rosetta/** (UserManual/ and
   Support/) for now. A Rosetta domain of its own may come later
   (rosetta.com isn't available) - keep every URL in one place per
   program so a later move is a one-line change. The old
   roseenginebutler.com links must keep working (redirects) for machines
   not yet updated.

Also noted: the Mesa pin file's package has been called `PIN_RosettaD_34`
since the first commit (from the 2025 Rosetta project), and `.axisrc`
already says "Rosetta" - nothing to change, noted so it isn't "fixed" by
mistake.

**Tasks - what the operator sees (low risk, can go to `main` early):**

- [x] Window titles, panel labels and licence text (02 November 2026,
      not yet run on a machine): Rich's Pi edits (REB Settings page
      titles "Rosetta", "O/S ..." labels without "REB") plus the panel's
      and Help tab's website label (colvintools.com/Rosetta), the Help
      tab's description, the Usage License tab (title, text, and its logo
      now the Turk's head `REBLogo-Sm-rev.png`), the Rosetta Settings window
      title and its "LinuxCNC is running" message, file-chooser names and
      errors, Back Up to USB's title and log, Checkout's messages.
      `REB_Report_Version.py` 1.2 reads the "O/S ..." label with or
      without "REB " (it found nothing once "REB " was taken off).
      Still "REB" on purpose until the file renames: the reserved-name
      rule ("never start a G-code file name with REB") in Rosetta Settings
      and the generator's message.
- [x] **The emblem is a Turk's head** (Rich, 04 November 2026): the
      eight-circle design is a Turk's head - an eccentric cutting frame
      pattern (https://otbok.info/index.php?n=Main.ECFOnFlatSurfaces).
      Call it that in the manual, notes and code, not "rosette" (a
      rose engine's cam). Code, CLAUDE.md and this tracker changed the
      same day (`SPLASH_TURKS_HEAD_*`); file names such as
      `RosettaLogo.png` unchanged.
- [x] **Startup image** (04 November 2026): `RosettaStartupImage.gif`
      (AXIS's `[DISPLAY]INTRO_GRAPHIC`, and its copy in
      `Rosetta_Setup/Images/`) redrawn by Claude: the Turk's head and
      "Rosetta" in Liberation Serif, the old image's grey on its dark
      background, same 640x180 size. Rich approved it.
- [x] **Help tab images** (04 November 2026, not yet seen in LinuxCNC):
      the User Manual, Gcode Library, Gcode Quick Reference and User
      Forum spines (`Rosetta-UserManualsm.png`, `Rosetta-Gcodesm.png`,
      `GCodeQuickRefsm.png`, `Rosetta-Forumsm.png`) and the header banner
      `Librarysm.png` (Reuben and "Rose Engine Butler" until then) cut
      from the bookshelf picture on https://rosetta.colvintools.com/
      (`Bookshelf/Rosetta-01.png`), at the old images' height (284 px;
      banner 420x75). `OTHandyBooksm.png` unchanged.
- [x] **Logos** (02 November 2026; artwork all replaced 04 November
      2026). Deleted 02 November 2026 at Rich's
      request, as nothing used them: `REBLogo-Sm.png`,
      `REBLogo-Sm-Panel*.png`, `REB-Forum.png`, `REB-Gcode.png`,
      `REB-UserForum.png`, `REB-UserManual.png`, `ReubenHeadSmall.png`,
      `Reuben.png`, `Reuben-rev.png` (in `REB_Display/Images/`),
      and `REB_Setup/Images/Reuben.gif` (Rich's copies of the old artwork
      stay in `REB_Setup/Images/Saved Images/`). Kept though unused:
      `RosettaLogo-Black-Sm.png`, and `REB_Setup/Images/Reuben.png` - the
      full-size Turk's head artwork despite its name (d733f26); rename it with
      the file renames. Already new:
      `REBLogo-Sm-rev.png` (panel/Settings/licence), the
      `ReubenHead*.png` launcher icons and `REBWallpaper.png` (d733f26).
- [x] Startup splash (02 November 2026, not yet seen in AXIS): the
      preview now draws the Turk's head (eight circles through one centre,
      like the logo - each one full `G2`) over "ROSETTA" (`SPLASH_GLYPHS`
      gained an "A"). Checked through LinuxCNC's own interpreter
      (`rs274`, no errors) and drawn as the lathe view shows it.
- [x] Web links (02 November 2026, not yet clicked on a machine): the
      panel's buttons now open colvintools.com/Rosetta/,
      .../UserManual/ and .../Forum/ (`WEBSITE_URL`, `USER_MANUAL_URL`,
      `USER_FORUM_URL`, `GCODE_LIBRARY_URL` at the top of `REB_main.py`),
      Rosetta Settings' manual buttons go to the new manual (every page
      they name exists there), the version report posts to
      colvintools.com/Rosetta/Support/reb_report.php. **Moved 04 November
      2026** (Rich) to rosetta.colvintools.com: website, User Manual
      (panel and Rosetta Settings' manual buttons), G-code library
      (`/Gcode/`, was gcode.RoseEngineButler.com), the version report and
      `README.md` - every page answers (the report script doesn't yet -
      see the next item). The forum stays at
      colvintools.com/Rosetta/Forum/: under rosetta.colvintools.com its
      users can't log in.
- [x] **Version report server - reports since the rebrand were lost**
      (found 04 November 2026): `reb_report.php` answers 404 at both
      colvintools.com/Rosetta/Support/ and rosetta.colvintools.com/Support/
      (it answered 405 on 02 November - gone in the site's move to
      rosetta.colvintools.com?), so the reports from Rich's Pi and S/N
      003's Rosetta updates went nowhere (each machine's own
      `~/.config/Rosetta/report_log.jsonl` still has them). `REPORT_URL`
      now points at rosetta.colvintools.com/Support/reb_report.php.
      Rich put `reb_report.php`, `reb_report_view.php`, `.htaccess` and
      `.htpasswd` there the same day: the script answers 405 to a GET,
      the view page asks for a login (401), `reb_reports.jsonl` and
      `.htpasswd` are blocked (403), and a real report from Rich's Pi
      was accepted (200, 12:43). Still to do: check it shows in the view
      page; S/N 003's lost report comes again at its next Update. The
      old address, support.roseenginebutler.com, still works for
      machines not yet on Rosetta. Machines not yet updated
      keep posting to support.roseenginebutler.com, so for a while
      reports land in two logs - either merge them in the view page or
      have the old address forward with a 307/308 (a 301/302 turns the
      POST into a GET and the report is lost).
- [ ] Desktop and menu entries on each machine (names, icons) and the
      Thunar bookmark/panel launcher names from `REB_Add_Shortcuts.sh` -
      the installer for new machines, a `ONE_TIME_STEPS` entry for built
      ones.
- [x] Messages printed by the installer, `REB_Update.sh`,
      `REB_Change_Network.sh`, `REB_Checkout.sh`, Rosetta Settings'
      name in the generator's and `REB_Update_Settings.py`'s messages,
      and the "REB" block letters at the top of `REB_Update.sh` and the
      Trixie installer, now "ROSETTA" (02 November 2026). Left for the
      file-rename work: `REB_Update.sh`'s pointer to the Support Manual
      page "Updating Rose Engine Butler" (rename that page first) and the
      "RoseEngineButler" folder shortcut name.
- [ ] Comment headers and the copyright/licence text in every file
      (including `SETTINGS_HEADER`/`SETTINGS_FOOTER`/`EXPORT_HEADER`, so
      every machine's settings file is re-noted on its next update),
      `LICENSE`, `README.md`.
- [ ] User manual and Support manual text (PmWiki), including the
      reserved-name rule ("never start a G-code file name with REB") -
      changes if the subroutines are renamed.
- [ ] Release Notes entry for the rename.

**Tasks - file and program names** - built 02 November 2026 on branch
`rosetta-rename`, merged into `dev-rich` 04 November 2026 (branch
deleted); on `main` since 04 November 2026:

- [x] Every `REB*` file, folder and reference renamed `Rosetta*`
      (96 files): `Rosetta.ini`, `Rosetta.hal`, `Rosetta_Launch.sh`,
      `Rosetta_Display/Rosetta_main.py`, `rosetta_settings_io.py`,
      `Rosetta_Subroutines/rosetta_thread.ngc`, the sounds, images, Mesa
      files (`7i92t_Rosetta.bin`/`.pin`, `PIN_Rosetta_34.vhd` - contents
      unchanged), `docs/Rosetta_Tracker.md`. Comment headers' block
      letters now spell ROSETTA. AXIS's title (`MACHINE`) is "Rosetta
      Mark 1". Comments naming files that no longer exist (e.g.
      `REB_Axes/*.inc`) were left as they were. The deprecated Bookworm
      installer kept its name and contents (it now sits in
      `Rosetta_Setup/`).
- [x] **Names Claude chose - Rich to confirm or change** (a script
      redoes them quickly): settings file `RosettaSet_v1.ini` (exports
      `*.RosettaSet_v1.ini`; Import still offers old `*.REBset_v1.ini`
      ones), `~/.config/Rosetta/`, shortcut icons `Rosetta_Folder.png` /
      `Rosetta_Folder-Gcode.png` (were ReubenHead*), the full-size Turk's head
      `Rosetta_Setup/Images/RosettaLogo.png` (was Reuben.png), USB backup
      folder `Rosetta_Backup/`, Thunar shortcut "Rosetta", reserved G-code
      prefix "rosetta" (files starting "reb" are no longer refused).
- [x] No fixed `/home/reuben` paths left (for the `rosetta` login):
      scripts find the repo from their own folder, Python from `~`;
      `Rosetta.ini`'s `PROGRAM_PREFIX` and `SHUTDOWN` are relative and
      the generator writes the full paths into `Rosetta.local.ini`.
- [x] **Moving built machines over** (`Rosetta_Setup/Rosetta_Renaming.py`,
      run at the end of every update, and `rosetta_settings_io.adopt_old_paths`,
      run whenever a Rosetta program starts): settings file (backup
      `REBset_v1.ini.pre-rosetta`), `~/.config/REB`, serial prefix
      (REB003 -> Rosetta003, before the version report), git remote ->
      `RichColvin/Rosetta`, old generated files removed, `~/REB_Update.sh`
      becomes a stand-in for a fresh `~/Rosetta_Update.sh`, desktop/menu/
      bottom-bar launchers, Thunar Places and the wallpaper repointed
      (a trusted desktop launcher stays trusted), and last the folder
      renamed `Rosetta` with a `RoseEngineButler` link. Stand-ins at the
      old paths: `REB_Setup/REB_Update_Settings.py` (what every machine's
      current update script runs after its pull), `REB_Launch.sh`,
      `REB_Settings.sh`, `REB_Update.sh`, `REB_Backup.sh`.
- [x] Tested 02 November 2026 on Rich's Pi **in a pretend home folder
      only** (cut off from the desktop session, panel and network): a
      clone of `dev-rich` set up like a built machine (copies of this
      Pi's launchers, Places, wallpaper setting, settings file, serial
      REB003, a trusted desktop launcher, a tool-table edit, a gcode
      program, `~/REB_Update.sh`), then the update's own steps (stash,
      pull, stash pop, the old script's call of
      `REB_Setup/REB_Update_Settings.py`). Everything moved as above; the
      tool-table edit and gcode program came through; every launcher's
      program and icon exists; launching through an old desktop launcher
      runs `Rosetta.local.ini` from the new folder; a second update
      changed nothing. Generated `.local.ini`/`.local.hal`/PostGUI/splash
      files match the old code's line for line apart from the names. All
      four windows' `.ui` files load with every image found. Not run:
      LinuxCNC itself on the branch.
- [x] **Run on Rich's Pi** 04 November 2026: switched to the branch;
      the settings file and `~/.config/REB` moved; ran the Update icon -
      folder renamed `Rosetta` with the `RoseEngineButler` link, desktop
      launchers rewritten with their trust marks renewed, menu and
      bottom-bar launchers, Places and wallpaper repointed, version report
      sent (serial "RichDev" has no REB prefix, so unchanged); LinuxCNC
      launched from the new folder and shut down cleanly, saving to
      `RosettaSet_v1.ini`. Found: an old `REB_Display/idx_debug.log` was
      left behind when Rosetta had run before the Update - fixed (joined
      onto the new log, 1b19b58). Claude's memory copied to
      `...-configs-Rosetta/`.
- [ ] **`main` fast-forwarded to `dev-rich` 04 November 2026** (91ea961,
      Rich's call) - the rename, Beta 1.3 labels and new artwork now
      reach every machine at its next Update, and new installs. Watch
      the report viewer: each machine should reappear with a
      "Rosetta..." serial (where it had "REB...") and 1.0 Beta 1.3; ask
      for the Update output of any that doesn't. Not yet run when it
      moved: (2), (4), (5) below and launching Rosetta on REB003.
- [ ] **Checklist (written for before fast-forwarding `main`):** (1) on Rich's Pi, check the
      desktop icons open without an "untrusted" question, Rosetta
      Settings' Save Subset suggests `*.RosettaSet_v1.ini`, Back Up to
      USB, jog and run a program; (2) Import an old `.REBset_v1.ini`
      export; (3) S/N REB003 (serial with an REB prefix and a
      `~/REB_Update.sh`): switch to `dev-rich`, run its Update icon -
      serial becomes Rosetta003, `~/REB_Update.sh` a stand-in, then
      launch; (4) a fresh install from
      `Rosetta_Install_Debian_13_Trixie.sh`; (5) Checkout dry run.
      Rich still to confirm the names chosen above.
      **(3) run 04 November 2026:** S/N REB003 pulled `dev-rich` and ran
      its Update icon - serial now Rosetta003 (the version report went
      out under it), `~/REB_Update.sh` a stand-in for
      `~/Rosetta_Update.sh`, `REBset_v1.ini` moved to
      `RosettaSet_v1.ini` (backup `.pre-rosetta`), remote
      `RichColvin/Rosetta`, folder renamed with the link, desktop
      launchers' names, programs and icon paths rewritten. Found: the
      desktop kept showing the old icons until `xfdesktop --reload`.
      Fixed in `Rosetta_Renaming.py` 1.2 (not yet run on a machine): the
      desktop is reloaded too, and both reloads (desktop and bottom bar)
      now come after the folder rename - before it, the new icon paths
      don't exist yet. Still to do on REB003: launch Rosetta.
- [ ] **Claude's memory on each machine** is kept per folder
      (`~/.claude/projects/-home-reuben-linuxcnc-configs-RoseEngineButler/`);
      once the folder is `Rosetta`, copy that folder to
      `...-configs-Rosetta/` (done on Rich's Pi 04 November 2026; again
      for the `rosetta` login).
- [x] **User Manual and Support Manual** (04 November 2026): every page
      redone for Rosetta by Claude and pasted in by Rich (names, files,
      folders, the reserved-name rule, launcher/menu names, addresses on
      rosetta.colvintools.com - forum stays at colvintools.com/Rosetta/Forum,
      its logins fail on the new address). User Manual page names kept;
      the Support Manual's REB* pages became Rosetta* (RosettaBackup,
      RosettaChangeNetwork, RosettaInstall, RosettaKeyPrograms,
      RosettaLaunch, RosettaSettings, RosettaUpdate,
      HardwareBuildWithRosettaPCB, LaunchingRosetta, UpdatingRosetta), the
      old ones redirecting. Install page: `git clone
      https://github.com/RichColvin/Rosetta`, hostname `rosetta`. Rich
      replaced the Support Manual's images and added MathJax to the new
      User Manual's config.php (formulas showed as raw code). Unused
      AxisScaling.Speed deleted.
- [ ] **Manuals, still to do:** (the twelve User Manual screenshots that
      showed the old name were retaken by Rich 04 November 2026) a
      Release Notes entry for the rename if wanted; the install page's "username MUST be reuben" once a
      `rosetta` login has been tried. How older machines move over is
      deliberately not documented (Rich, 04 November 2026: only the two
      test machines, nothing in production).
- [ ] **Later:** remove the old-path stand-ins and the `RoseEngineButler`
      folder link once every machine has updated; the `rosetta` login
      itself (a separate, tested procedure per machine, or a reinstall).

**Leave alone:** git history, dated entries in this tracker's Done table,
and the old serial numbers in past entries.

### Two-box hardware: base box + expansion box (since 11 October 2026)

Rich and Chuck's plan to split the hardware into two chassis: a **base
box** with the Raspberry Pi, an Ethernet switch, one Mesa 7i92TH and 6
DM542T channels, and an optional **expansion box** with a second 7i92TH
and 4 more channels - 10 in all, one for each of the 10 roles (8 axis
letters and 2 spindles). The two cards talk to the Pi through the switch.

Decided so far:

- **Development boxes:** the current 8-channel boxes are development
  units. They'll be replaced, or simply treated as a base box with
  channels 00-05 and their other two plugs ignored - so only one
  software design is needed.
- **Base box I/O stays:** limit jacks 1-3, the E-stop button and the
  signal tower stay in the base box. The expansion box may add **limit
  jacks 4-6**, read from the second card.
- **Channel labels:** base box 00 / 02 / 04 on the top row and 01 / 03 /
  05 on the bottom. Expansion box either 00-03 again or **06 / 08 over
  07 / 09** - Claude recommends 06-09, so every channel number names one
  plug on the whole machine (in the settings file, on the Axis Selection
  page and when talking to a customer), continuing the base box's
  even-top / odd-bottom pattern. Also recommended: wire each plug to the
  step generator with the same number, so labels and software agree
  (today's boxes don't - "Position 1" is Channel 02).
- **No fixed roles:** any role on any channel, as now.

Open questions:

- **Mesa (Rich has asked Peter there):** the 10.10.10.x address
  plan above, and is two 7i92s through an
  unmanaged switch at a 1 ms servo period on a Pi 5 a setup they've seen
  work; any switch they recommend; and firmware - a 6-channel base card
  and a 4-channel expansion card with the inputs/outputs wanted (custom
  pin files like today's `PIN_REB_34`, or something stock).
- **Bench test:** if Mesa agrees, borrow a card from a development box:
  two cards, the switch and a few drives, run for a long time watching
  for `hm2_eth` read errors and following errors. Order another card
  after.

Points to settle in the design:

- **Network: 10.10.10.x on every machine** (planned 12 October 2026,
  waiting on Peter at Mesa to confirm). Pi wired 10.10.10.100, base card
  10.10.10.10, expansion card 10.10.10.11, no gateway or DNS on the
  wired connection. Moves off 192.168.1.x because a customer's home
  Wi-Fi often uses it too, and the installer currently gives the wired
  connection gateway/DNS 192.168.1.1 (`REB_Install_Debian_13_Trixie.sh`
  line 100), which a card on .1 would collide with. Switch: standalone
  gigabit unmanaged, only the Pi and the two cards on it; CAT-8 cables
  (more than needed - the 7i92T is 100 Mbit - but fine).
- **Setting a card's address** (the cards need EEPROM addresses; check
  the 7i92T manual's W5/W6 table for which setting is "EEPROM", and
  whether one is fixed at 10.10.10.10, which would let the base card skip
  this). A new card always answers on 192.168.1.121, so do this with the
  Pi still on 192.168.1.120 and only that card connected:
  1. W5 and W6 down, power on.
  2. `mesaflash --device 7i92t --addr 192.168.1.121 --write 7i92t_REB.bin --reload`
  3. `mesaflash --device 7i92t --addr 192.168.1.121 --set ip=10.10.10.10`
     (`.11` for the expansion card) - the option is `--set ip=`, not
     `--setip`.
  4. Power off, move the jumpers to EEPROM, power on (jumpers are only
     read at power-up).
  5. Once both cards are set, move the Pi:
     `sudo nmcli con mod "Wired Ethernet" ipv4.method manual ipv4.addresses 10.10.10.100/24 ipv4.gateway "" ipv4.dns ""`
     then `sudo nmcli con up "Wired Ethernet"`, and check each card with
     `mesaflash --device 7i92t --addr 10.10.10.10 --readhmid`.
  Recovery: W5/W6 back down returns a card to 192.168.1.121.
- **HAL: one `loadrt hm2_eth` line for both cards** - a realtime module
  can only be loaded once, so two lines fail. Comma-separated lists:
  `board_ip="10.10.10.10,10.10.10.11"` and `config="...num_stepgens=6","...num_stepgens=4"`
  gives `hm2_7i92.0` and `hm2_7i92.1` in that order, each needing its
  own `read`/`write` `addf` and watchdog `setp`. Both cards can run the
  same `7i92t_REB.bin` (8 stepgens; asking for fewer is fine).
- **Existing 3 test machines:** only used for testing. Convert them with
  a script (`REB_Change_Network.sh`, not written yet) or by phone, or
  ship them back. Script plan: stop if LinuxCNC is running; check the
  card answers at .121 (else change nothing); write 10.10.10.10 to its
  EEPROM; pause for power off / jumper / power on; move the Pi's wired
  connection; check the card answers at 10.10.10.10. The new address in
  REB.hal (or the generator) must arrive at the same time as the script
  runs - e.g. the script does the `git pull` itself, or the address comes
  from settings. Installers change too (`nmcli` line, `mesaflash`
  address).
- Keep the switch private - nothing else (router, internet, file
  sharing) on that network, or the 1 ms timing suffers. The Pi's
  internet stays on Wi-Fi.
- Either card's watchdog (it stops that card's steps if it loses
  contact) should count as an E-stop fault, so a pulled cable can't leave
  half the machine running.
- Alternative considered: one 7i92 with new firmware running all ten
  channels, with step/direction signals cabled to the expansion box.
  Cheaper and easier on timing, but long signal cables pick up noise and
  it uses up the card's spare pins; the two-card design is more modular.

Screen layout - mock-up approved by Rich, 11 October 2026: REB Settings'
Axis Selection page shows **Base Box** (00 / 02 / 04 over 01 / 03 / 05)
stacked above **Expansion Box** (06 / 08 over 07 / 09) with an "Expansion
Box - Connected" checkbox, each box with its own Top / Bottom rows; the
Inputs, Outputs and Sounds page shows Limit Jacks 1-3 under Base Box over
Limit Jacks 4-6 under Expansion Box, the expansion side greyed out until
connected. Pictures: `docs/mockups/two_box_axis_selection.png` and
`docs/mockups/two_box_inputs_outputs_sounds.png`. The mock-up itself was
the `two-box-mockup` branch (display only), which the real screens were
built from; deleted 20 October 2026 at Rich's request (last commit
7de560f).

Progress (built on the `two-box` branch, merged into `dev-rich` 20 October 2026):

- **Step 1 - HAL side, done 14 October 2026 (8cfd0b7, not run on
  hardware):** ten channels in the shared settings module, the
  `expansion_box` setting, the startup generator pointing each role at
  its card, one `hm2_eth` line for one or both cards at 10.10.10.10 /
  .11 (fixed in the code - Rich's choice), the second card's read/write
  and timer/watchdog lines, and limit jacks 4-6 on the second card.
  Base box defaults (Rich, 14 October 2026): X Z B W Sp0 Sp1 on 00-05,
  then U V A C on 06-09. Existing settings need no conversion: 00-05
  keep their meaning, 08/09 get the unused roles. **Development boxes:**
  roles on 06/07 (Rich's box has Sp0/Sp1 there) go inactive without an
  expansion box - move them to base channels to test.
- **Step 2 - REB Settings, done 14 October 2026 (c6f1f5c, tested off
  screen against a copy of Rich's settings, not on the machine):** the
  approved mock-up made real - Base Box above Expansion Box on Axis
  Selection with a working "Expansion Box - Connected" checkbox (saved
  as `expansion_box`), Limit Jacks 1-3 over 4-6 on Inputs, Outputs and
  Sounds. The expansion side is greyed and ignored until connected; a
  greyed limit jack keeps its choice.
- **Step 3 - runtime programs, done 14 October 2026 (09b7fad, not run
  on the machine):** the main panel's code, the shutdown save and the
  startup restore use the same channel model and "active only on a
  channel in use" rule as the generator, so roles and joint numbers
  match (checked in four setups), and reach channels 06-09 on the second
  card. The panel's Axis Assignments tiles follow the new plug layout,
  with the expansion box's four tiles shown only when it's connected
  (Rich's choice).
- **Step 4 - network, written 14 October 2026 (tested with --dry-run
  only):** `REB_Change_Network.sh` sets a card up as the base (.10) or
  expansion (.11) card and moves the Pi to 10.10.10.100 (or back to
  192.168.1.120); the Debian 13 installer uses it and drops the
  192.168.1.1 gateway/DNS. **To test when Rich's new 7i92 arrives:**
  connect only the new card, run `REB_Change_Network.sh base` (or
  `expansion`), confirm which W5/W6 setting the 7i92 manual calls
  EEPROM, check it answers at its new address after power-up; then
  `git switch two-box`, move Sp0/Sp1 to base channels 00-05, and run
  LinuxCNC. Leave the current card at 192.168.1.121 until then, so
  `dev-rich` keeps working.
- **Rich's Pi moved to the two-box network, 14 October 2026:** its
  7i92 had 10.10.10.10 stored (no new firmware), the Pi's wired
  connection is 10.10.10.100 (autoconnect priority 10 - the Pi had three
  "Wired Ethernet" connections; fixed in the script and installer, 809510d
  on `two-box`), and the Pi is on `two-box`. Plugs 06/07 do nothing on a
  base box, so Sp0/Sp1 must be moved to channels 00-05 in REB Settings.
  Settings copied to `~/Documents/REBset_v1.ini.before-two-box`. To run
  `main`/`dev-rich` again: W5/W6 back to the factory setting,
  `REB_Change_Network.sh back`, copy that file back.
- **Expansion card set up on Rich's Pi, 16 October 2026:** the new card
  (a 7I92T - mesaflash only finds it with `--device 7i92t`, as the
  scripts already use) arrived with Mesa's stock firmware (10 stepgens,
  2 QCount). Claude ran `REB_Change_Network.sh expansion`'s commands by
  hand (the script's questions can't be answered from Claude's shell):
  a temporary 192.168.1.120 on eth0 to reach the factory address,
  `7i92t_REB.bin` written and verified (`--reload` then showed 8
  stepgens, InM, OutM), `--set ip=10.10.10.11`, then Rich moved W5/W6
  to EEPROM and powered it on. Both cards now answer on the switch -
  base 10.10.10.10 (MAC 00:60:1b:12:81:33), expansion 10.10.10.11
  (00:60:1b:12:81:97) - with REB firmware, also after Rich connected
  P1/P2 and mounted the board. The Pi's uptime was 6 minutes when the
  card came back, so the power-on restart (Open items) may have
  happened again; it came back on 10.10.10.100 on its own. The script
  itself still hasn't run on hardware.
- **Both cards run under LinuxCNC, 16 October 2026:** on `two-box` with
  Expansion Box Connected ticked, one `hm2_eth` line loaded both cards
  and channels 06-09 (W V A B on Rich's box) all move. A and B (08/09)
  didn't move at first although the card sent their steps (stepgen
  counts matched the commanded moves): the two new DM542T drives still
  had their side switch at the factory 24V - it must be at **5V** for
  the 7i92's signals. Ruled out on the way: firmware (`mesaflash
  --readhmid` gives the same pin map on both cards, matching the
  support page), HAL, motors. Jacks 4/5 (set to X/Z): tested - see below.
- **Servo thread time with two cards, 16 October 2026:** LinuxCNC showed
  "Unexpected realtime delay on task 0" (the 1 ms servo thread). The
  latency test was fine (worst 26.6 us, no isolcpus), but the thread's
  worst case was 859 us: each card's `read` sent a request and waited
  for the reply, one card after the other (394 + 341 us worst). The
  generator now adds both cards' `read-request`s before the reads
  (5c19d2e on `two-box`): worst 533 us while jogging on both cards. A
  busy web browser was also using about two of the Pi's four cores the
  first time - keep it closed while running. Then, per Peter Wallace at
  Mesa (order for two 7i92s: read-requests, reads, everything else,
  writes), both cards' writes moved to the end of REB.local.hal (on
  `two-box`, the commit after 5c19d2e), so each cycle sends fresh
  commands: worst 556 us jogging, no following errors. One card keeps
  REB.hal's read-then-write order - consider Peter's order there too.
  Watch for following errors with the new order. If the realtime
  message comes back: `isolcpus` for the realtime core.
- **Channel numbers on the panel's Axis Assignments tiles, 14 October
  2026 (6465a4d on `two-box`, not yet seen in AXIS):** each tile has a
  "Channel NN" label like REB Settings. Makes the panel 34 px taller -
  check it still fits a 1080-line screen.
- **User Manual for two-box, 14 October 2026:** REB Settings' new "How
  the Expansion Box Works" button (327b341 on `two-box`) opens
  `Main.AxisSelection#ExpansionBox`. Draft page text with that section
  was given to Rich (`~/Downloads/AxisSelection.pmwiki.txt`); publish it
  when `two-box` reaches `main`, and retake the
  `REBSettings-AxisSelection.png` and `SelectedAxes.png` screenshots then.
  Rich took the new SelectedAxes screenshot 14 October 2026 using
  `REB_SHOW_EXPANSION=1 ./REB_Launch.sh` (3037858 on `two-box`: the panel
  shows the expansion box as connected, display only, settings untouched -
  worked on the machine).
- **Lost card = E-stop - built and tested, 16 October 2026** (5cfd3a0,
  c44705b on `two-box`): pulling a card's cable while jogging, before
  this, left the machine on and the other box's axes running - after 5
  lost packets `hm2_eth` sets the card's `io_error` and stops talking to
  it, and nothing brought it back. Now each card's
  `packet-error-exceeded` and `watchdog.has_bit` (OR'd into net
  `card-fault`) latch E-stop with the E-stop button, light the tower's
  red and sound the siren; AXIS says "Expansion box (or Base box) lost
  contact"; while in E-stop `REB_main.py` clears `io_error` (at most
  every 5 s - each failed try prints "error finishing read") then
  `has_bit`, so F1 resets once the cable is back. Tested on Rich's box:
  expansion card - E-stop, red, buzzer, F1 refused while unplugged,
  recovered, red off at F2, W jogged; base card - same, but the tower
  stays dark (its outputs are on that card; very unlikely failure - Pi,
  switch and base card share a box).
- **Limit jacks 4, 5 and 6 on the expansion box tested, 16 October 2026:**
  jack 4 set to X and jack 5 to Z (both ends, NC), on the expansion
  card's I/O 002 and 006. Tripping each while jogging: the axis stopped,
  "joint 0 (1) on limit switch error", machine off, red latched, 3 s
  buzzer and panel siren; F2 brought the machine back and put red out.
  Jack 6 (I/O 010), set to Z with jack 5 cleared: the same, twice.
- **`two-box` merged into `dev-rich` and deleted, 20 October 2026**
  (Rich's call - one development branch instead of two). Commit ids
  above and below are still in `dev-rich`'s history. Rich's Pi runs
  `dev-rich`.
- **Hold lifted, 20 October 2026:** Rich finished the S/N REB003 hardware
  testing ("everything tested perfectly") after the IP address re-test,
  and `main` was fast-forwarded to `dev-rich` - the two-box work is on
  `main` now, so S/N 1 and S/N 2 get it at their next update.
- Next: S/N 1 and S/N 2 (Open items: "Move S/N 1 and S/N 2 to 10.10.10.x").

Software work once the design is fixed (not started):

1. Channels 00-09 across two cards (`hm2_7i92.0` for 00-05,
   `hm2_7i92.1` for 06-09). The channel table is repeated in
   `REB_Settings.py`, `REB_main.py`, `REB_Scale_Persist.py` and
   `REB_Generate_Local_Ini.py`; the generator builds the HAL from it.
2. An "Expansion box connected" setting (like Signal Tower's): off = one
   card and 6 channels, on = both cards and 10.
3. REB Settings' Axis Selection page laid out as the two boxes, with the
   expansion group greyed out when it isn't connected.
4. Limit jacks 4-6 on the second card, shown only with the expansion box.
5. Either card losing contact = E-stop.
6. The update step converting existing settings files' channel IDs.
7. New firmware/pin files for both cards.

## Done

Most recent first.

| Item | Settled | How |
|---|---|---|
| Phone alerts (ntfy app), Beta 1.9 (opened 15 November 2026) | 15 November 2026 | Built at Rich's request (ntfy, all five events, operator only; topic Rosetta-<S/N>, Rich's choice); tested by Rich on his Pi the same day. Merged from branch `phone-alerts` into `dev-rich` and `main`, branch deleted. User Manual pages still to publish - see Open items. |
| Rosetta Settings: one copy only; Rosetta won't start beside it, Beta 1.9 (opened 15 November 2026) | 15 November 2026 | Asked for by Rich (he could open two copies). Lock on `~/.config/Rosetta/Rosetta_Settings.lock`; a second start says so and raises the first window; `Rosetta_Launch.sh` refuses while Settings is open. Tested by Rich on his Pi the same day. |
| Axis not available for a program (opened 11 November 2026) | 11 November 2026 | Found by Rich: with C on expansion channel 08 and Expansion Box Connected off, opening `C_Accel_Test_One_Zone.ngc` gave only AXIS's "Bad character 'c' used", and AXIS would still have run the program up to that line. `Rosetta_Axis_Commands.py` 1.2 wraps AXIS's preview load (`o.load_preview`): when the interpreter stops on an axis letter this session doesn't have, Rosetta's own "<axes> not available" box replaces AXIS's, saying why for each axis (on the Expansion Box while it isn't connected / not assigned / Y not used) and what to change in Rosetta Settings, and Run/Step are refused with the same message until a program without them is opened. Other missing axes are found by a best-effort scan of the file, which only adds names to the message. Verified by Rich on the machine 11 November 2026: one box on opening, Run refused, other programs run normally. Released as O/S 1.0 Beta 1.6. |
| Mesa's HAL order on a one-card machine (opened 16 October 2026) | 09 November 2026 | (`two-box`, 10f3634.) With one card the servo thread is now read, everything else, write (Peter Wallace's order; the write used to follow the read straight away). Tested only with two cards. When Rich's single-card machine is rebuilt: LinuxCNC starts, axes jog and run a program with no following errors, and `halcmd show thread` stays well under 1000 us. 20 October 2026: LinuxCNC starts and runs on S/N REB003 (one card at 10.10.10.10); program run and thread time still to check. Rich confirmed 09 November 2026 that it is finished: S/N Rosetta003 has only the base card and runs this HAL order; his development box (RichDev) has two cards. |
| E-stop button (opened 28 September 2026) | 09 November 2026 | Pressing it (and unplugging it) latches E-stop; release then F1 resets. Needs "Connected" ticked in Rosetta Settings. Rich confirmed 09 November 2026 that this was verified on the machine. |
| NO limit switches (opened 08 October 2026) | 09 November 2026 | With Limit Switch Type set to Normally open, a tripped NO switch stops the axis (reads the jack's GPIO `.in_not`). NC is already verified - see Done. Rich confirmed 09 November 2026 that this was verified on the machine. |
| Spindle indexing PID I 0 / D 0 (opened 08 November 2026) | 09 November 2026 | An index finished on screen seconds after the spindle stopped: with the old indexing gains (P 2, I 1, D 1.2) a 90 degree index overshot 5.7 degrees and crept back, about 9 s in all. With I 0 / D 0 (traced on Rich's Pi the same day, Sp0 alone and Sp0+Sp1) every 90 degree index took 3.7 s, no overshoot, the screen finishing as the spindle stopped. New starting values in `rosetta_settings_io` and the seed; `Rosetta_Update_Settings.py` 1.6 changes a spindle still on exactly P 2 / I 1 / D 1.2 (a tuned one is left alone). Check: after Update on S/N 003 and Roy's machine, the update lists "Sp0 indexing PID: I 1 -> 0, D 1.2 -> 0" (and Sp1), and a 90 degree index takes about 3.7 s. Faster still (about 1.3 s) is possible with spindle Max Accel 4 and P 6 - not done, since Max Accel also sets the spindle's spin-up rate. Closed 09 November 2026 at Rich's request: verified with both spindles ticked 08 November 2026 (3.7 s for 90 degrees, no overshoot); one spindle on its own (the M19 path) not specifically seen. |
| Program progress bar (opened 20 October 2026) | 09 November 2026 | (`two-box`, 5d644c8; percentage only since 946709e - Rich found the time left kept changing, like an O/S upgrade's.) Bar left of Sync Move: "Program 42%", "(paused)", then "Program done in ..." / "stopped at 42%". First run 20 October 2026: the bar shows and moves, and `program-path` grew 11.924 over the run - the estimate's total exactly. But it lagged real progress by up to 30% (51% at 80% of the run), so the estimate now includes acceleration and is worked out as the program starts (044193e) - within 6% when replayed against that run's log. Second full run 20 October 2026 with that change: within 5% of real progress all the way (average 2%; 52% at the halfway point, 83% at 80%), `program-path` again matched the estimate (11.924), finished correctly at M30. Sync Move and Cut Thread now use the bar too (b49fcff, "Sync Move 42%" / "Threading 25%" counted in passes; not Run Operation, indexing or Return) - both verified 20 October 2026 (Sync Move climbed smoothly; a 1-start, 3 pass + 1 spring thread stepped 0/25/50/75/100%). Found then and fixed on `two-box`, both verified after a restart the same day: the pressed Sync Move / Cut Thread button went blank (disabled grey text on the dark background; now white, 9f124fe), and the startup splash cluttered the preview under a Sync Move or Cut Thread's tool path (now swapped for the empty preview first, df43721). Also still to check: Stop shows "stopped at", Run From Line shows "started part way", the panel doesn't change size on any tab. Same day, separate commits: the Settings gear note was removed and the library button moved up (565a351) - verified, the Sync Move tab now fits the screen; and AXIS's Open dialog starts in `gcode/` (`PROGRAM_PREFIX`, 4076f02). Closed 09 November 2026 at Rich's request: the estimate's total matched program-path on Rich's Pi 20 October 2026, and programs have run with it since. |
| Done / Pause beeps (opened 06 October 2026) | 09 November 2026 | 3 beeps when a program finishes normally, 2 at M0/M1/M60, none on an abort. 20 October 2026: no beeps at M30 on Rich's o-word program (`Geo1216Case12-10-13-26b.ngc`) - the old check wanted `motion_line` to reach the file's last axis move, which was in a skipped `If`. Rewritten on `two-box` (e7aacc3): finished = the interpreter read to the M2/M30 and LinuxCNC says `RCS_DONE` as the run goes idle (both logged on the machine at a finish and a Stop). Verified 20 October 2026: at M30 on that program the tower gave 3 beeps and the TV the new ta-da (`REB_Done.wav`, 897b2b3; the speaker's pause sound is now two rising notes, da22df3). Still to check: none after Stop or E-stop part way, the pause sound + 2 tower beeps at an M0, a simple program. Cherry-picked to `dev-rich` the same day (ddf0df8..cb6da15), so it reaches `main` with the next fast-forward. Closed 09 November 2026 at Rich's request: the end-of-program check for o-word programs was confirmed on the machine 20 October 2026. |
| Index counters on the Indexing tab (opened 11 October 2026) | 09 November 2026 | Each axis row and the spindle row show a count left of Distance: +1 per Fwd index, -1 per Rev (it can go negative). Resets to 0 at startup, on a distance or deg/div change, and on a double-click of the number. Check the count follows the on-screen Rev/Fwd columns, the spindle count works with Sp0, Sp1 and both, and the Distance column didn't get wider. Double-click reset verified by Rich, 11 October 2026 (after it was rebuilt on the button's "clicked" signal); still to check: the counting itself on real presses. Closed 09 November 2026 at Rich's request: in use during the 08-09 November indexing tests. |
| User Manual: Axis Not Enabled (opened 09 November 2026) | 09 November 2026 | Drafts in `~/Downloads/Rosetta_UserManual_AxisNotEnabled_2026-11-09/` (README lists each change): Other (General re-ordered to match the screen, new Axis Not Enabled section, anchor #AxisNotEnabled), Running Gcode Programs (new "If an axis is not enabled"), Main Screen (ENA section, anchor #ENA), and one line each on Indexing, Synchronized Movement (step 3a no longer says a following error results) and Threading. The Other page's screenshot (REBSettings-Other.png) needs retaking. Rich pasted them and uploaded a new REBSettings-Other.png 09 November 2026; checked the same day - all six live pages match the drafts (Rich widened the Other page's screenshot to 300px). |
| Axis Not Enabled: Enable and Run, or enable automatically (opened 09 November 2026) | 09 November 2026 | Rich's idea. The not-enabled warning (AXIS's Run, and the panel's index / Sync Move / Threading buttons) now offers "Enable <axes> and Run" ("... and Move" on the panel; the default) or Cancel - "Run Anyway" / "Move Anyway" removed at Rich's request. Enabling pulses `<role>-ena-flip.set`, as clicking ENA does; an axis Rosetta Settings' override still blocks stays off and the move is cancelled with a message. New Rosetta Settings > Other > **Axis Not Enabled**: Ask - recommended (default) or Enable it automatically (no box; AXIS shows a note "Enabled C for this program."). RosettaSet_v1.ini `not_enabled_action` ("ask"/"enable", in the seed), read at startup by `Rosetta_Axis_Commands.py` 1.1 and `Rosetta_main.py`. The Other page's General section is now Device Names, Startup File Check, Axis Not Enabled, then Measurement System (moved last - Rich: set once at setup). AXIS's box is a plain Tk dialog (nf_dialog's buttons are a fixed 10 characters). Tested with stand-ins only (both sides: ask/enable/cancel/blocked), and the Settings layout loaded (not shown). Check: Other page order and the new radios save; with Ask, C's ENA off: Run shows "C not enabled" - Enable C and Run turns the ENA light on and runs, Cancel doesn't; the same on C's index button, Sync Move and Cut Thread ("and Move"), and a ticked spindle with ENA off; with Enable it automatically: no box, ENA comes on, AXIS shows the note. 09 November 2026, on Rich's Pi: Enable X and Move on X's index button works; the ENA light first turned green only after the move (the move holds up the panel) - fixed in d52b5d8 (redraw right after enabling), and Rich confirmed the light now comes on straight away. Rich then confirmed everything works as expected. Same day, at his request, the Other page's General section was laid out in label / control / note columns so the controls line up (4040842). |
| User Manual: tuning page (opened 08 October 2026) | 09 November 2026 | Update for the new Max Speed / Max Acceleration rows, the Advanced settings twisties, the row notes and Restore Defaults, once the screen has been seen on the Pi. 09 November 2026: Rich had already added Max Speed, Max Acceleration and the Advanced twistie. Draft of the rest in `~/Downloads/Rosetta_UserManual_Tuning_2026-11-09/` (units and the 1 in/s cap, carry-along, the warnings line, advanced rows with their normal values, spindle indexing rows, Restore Defaults; replaces the out-of-date "a calculation is performed" lines). Rich pasted it 09 November 2026; the live page has the new sections (warnings line, Restore Defaults). |
| Back Up to USB (opened 06 October 2026) | 09 November 2026 | Insert a stick, run a backup, then check the dated `REB_Backup/` folder and `backup_log.txt` on another computer, and that the stick ejects with "Safe to remove". Also add the MenuLibre menu and desktop entries - Command `/home/reuben/linuxcnc/configs/RoseEngineButler/REB_Backup.sh`, Icon `REB_Setup/Images/REB_Backup.png`. Rich ran Back Up and Restore from USB on his Pi 09 November 2026 - both work (see the Restore from USB row). |
| File menu in Rosetta Settings (opened 07 October 2026) | 09 November 2026 | Ctrl+S / Shift+Ctrl+S / Ctrl+O / Ctrl+Q do the same as the buttons, including a half-typed value being saved. Closed 09 November 2026: Rich used the File menu that day (Back Up / Restore from USB); closed at his request. |
| Rosetta.ini / Rosetta.hal cleanup (opened 06 October 2026) | 09 November 2026 | LinuxCNC starts with no HAL errors, an axis jogs and moves, and an Sp0 M19 index works. Probably already exercised by the 08 October spindle and speed-limit testing - tick it off if so. Closed 09 November 2026 at Rich's request: a month of normal running (start-up, jogging, moves, Sp0 M19 indexing - incl. the 08 November spindle tests) has exercised it. |
| Version reporting (who's running what) (opened 23 October 2026) | 09 November 2026 | New `REB_Setup/REB_Report_Version.py`, run every update from `REB_Update_Settings.py`'s `main()`: builds a report of this Pi's own hardware serial (`/proc/cpuinfo`, unique with no coordination needed - Rich's call, so a self-built machine can never collide with a factory one), the friendly serial number from `~/.config/REB/serial` if set (for support calls only, doesn't need to be unique), and the version read straight out of `REB_Panel_v1.ui`'s "REB O/S ..." label. New `REB_Setup/REB_Set_Serial_Number.sh` asks for the friendly number (skippable, asks again next update until set) - added to `REB_Update_Settings.py`'s `ONE_TIME_STEPS` (runs every update, self-skips once set, same pattern as the folder shortcuts) and to the Trixie installer as Step 11. **The receiving side is live**: `reb_report.php`/`reb_report_view.php` on `support.roseenginebutler.com` (not in this repo - drafted into `~/Downloads` for Rich to deploy by hand), appending each report to a server-side `reb_reports.jsonl`; `reb_report_view.php` shows it as a table (one row per machine, latest wins, sorted newest-first), behind HTTP Basic Auth (user `REBmachines`, password known to Rich only - not recorded here). `.htaccess` blocks direct HTTP access to `reb_reports.jsonl` and `.htpasswd` themselves (403, confirmed). `REPORT_URL` in `REB_Report_Version.py` now points at the real endpoint - verified 23 October 2026 end-to-end: a real POST from this Pi landed in the server log, the view page requires login (401 without, 200 with correct credentials, confirmed by Rich), and the two direct-access blocks hold. `reb_reports.jsonl` currently has a handful of `test-*` hardware_id entries from this testing - harmless, but worth clearing out next time Rich is in the viewer. Not yet run through a real install or a real `REB_Update.sh` run on a second machine - check Step 11 prompts correctly on a fresh install, and that an existing machine gets asked on its next update and its report actually appears in the live table. Closed 09 November 2026: reports from Rich's Pi reach the server (a report sent that day returned 200 and carried Beta 1.5). |
| `~/REB_Update.sh` home-folder copy (opened 18 October 2026) | 09 November 2026 | The installer copies `REB_Update.sh` into the home folder, and updates never refresh that copy. Find out what the Update desktop icon and menu entry run: if it's the home-folder copy, point them at `/home/reuben/linuxcnc/configs/RoseEngineButler/REB_Update.sh` (with `bash` in front on machines installed before the 18 October 2026 fixes, when it wasn't marked runnable) and stop the installer making the copy. Closed 09 November 2026 at Rich's request: Rich's Pi has no home-folder copy, and its Update icon runs the repo's own Rosetta_Update.sh. Machines installed before the fix may still have an unused copy - harmless (the Support Manual's installer page says to ignore it). |
| Index buttons after a G-code program (GitHub #24) (opened 08 November 2026) | 09 November 2026 | Roy: after stopping a program, X moved once then not again, Z only went back and forth, C turned the same way for both arrows or 1/5 turn. Cause: the index buttons sent `G1 X+5` and relied on Rosetta.ini's startup `G91`, and a program leaves `G90` - so they made absolute moves. Each index move now sends `G20`/`G21 G91 G94 G8` itself and puts the operator's modes and F back after; Sync Move now also sends `G8`. Check: run a program that sets `G90` (and `G7`), stop it part way, then index X, Z and C twice each way - every press moves the set distance in its own direction; `G90`/`G7` are still in effect afterwards (AXIS's MDI tab). Closed 09 November 2026 at Rich's request; fix pushed 08 November 2026. Still to hear from Roy that it fixed his machine. |
| Leftover repo copy on the Mac (opened 06 October 2026) | 09 November 2026 | `~/Documents/GitHub/RoseEngineButler` is a stale duplicate (with one unpushed commit, now also in the real repo). Safe to delete; the working copy is iCloud Drive > Shared iCloud > Rich > GitHub > RoseEngineButler. Rich confirmed 09 November 2026 that this housekeeping is done. |
| Support Manual: key program pages (opened 18 October 2026) | 09 November 2026 | Published 18 October 2026; the 24 October review and the renaming are on the live pages. 09 November 2026 review against `dev-rich`: drafts in `~/Downloads/Rosetta_SupportManual_2026-11-09/` (README lists each change). Found the Overview page (RosettaKeyPrograms) has held a copy of the installer page since the 04 November renaming - the draft recreates it from the old REB overview in the wiki's history. The other drafts add today's work (Restore from USB, the File menu, Rosetta_Axis_Commands.py and the not-enabled warnings, the update's PID change and old-key removal) and soften the root-owned settings file note (saves now replace the file, so it fixes itself). Rich pasted them 09 November 2026; checked against the drafts the same day - all six live pages match (the Backup page first held the installer text by mistake, fixed). |
| User Manual pages for Backup, Sounds and Signal Tower (opened 07 October 2026) | 09 November 2026 | Rich confirmed they were pasted in. Checked the live wiki the same day: the Backing Up, Sounds and Signal Tower pages are there; the Home page links the Backing Up page with the `REB_Backup.png` icon; the manual's menu entry "Backup Rosetta" matches the launcher's name on Rich's Pi; the Sounds page covers the fault siren on the speaker; the Signal Tower page no longer makes the PNP / NPN claim. |
| Speed limits in Rosetta Settings (opened 08 October 2026) | 09 November 2026 | Max Speed / Max Acceleration / PID Max Output from REB Settings reach LinuxCNC; `REB_Update.sh` fills them in correctly on an existing machine. On the tuning page: each group shows four rows, a warnings line and a closed "Advanced settings" twistie with a note beside every row, nothing cut off; no warnings on a normal machine; changing C's Max Speed carries Stepgen Max Vel and PID Max Output along; linear Max Speed stops at 1.0 in/s; Restore Defaults resets an axis's advanced values. The window itself was never opened before commit (no GTK on the Mac). Closed 09 November 2026: Rich has used the tuning page and these limits on his Pi for a month with no problems. |
| Limit jack pin map (opened 28 September 2026) | 09 November 2026 | Rich made `LIMIT_JACK_INPUT` the Rosetta standard: limit jacks 1/2/3 on the base card's I/O 002/006/010 (P2 pins 3/7/13), jacks 4/5/6 on the same pins of the expansion card. The new circuit board has already been ordered wired to this map. Already proven on the current wiring: jacks 1-3 on 05 October 2026, jacks 4-6 on 16 October 2026. Noted as the standard in `Rosetta_Generate_Local_Ini.py` and CLAUDE.md. |
| Old keys removed from Rosetta.ini and settings files (were "REB.ini: possibly redundant keys" and "Old keys in settings files") | 09 November 2026 | Checked against LinuxCNC 2.9.10 on Rich's Pi. Rosetta.ini 1.2: removed `[FILTER]` (Rich: nobody opens pictures or Python scripts from AXIS), `[DISPLAY]MIN_VELOCITY` (AXIS uses it only when MIN_LINEAR/ANGULAR_VELOCITY are missing, and the generator always writes them) and the numbered `MAX/MIN_SPINDLE_0/1_OVERRIDE` (read only by other screens - gmoccapy, QtVCP). Kept the un-numbered `MAX_SPINDLE_OVERRIDE` (AXIS's spindle override slider top; without it 200%) and `MIN_SPINDLE_OVERRIDE` (halui, which Rosetta loads; gladevcp's override widget too), and fixed its comment (0.001 = 0.1%, not 1%). `Rosetta_Update_Settings.py` 1.7's `remove_old_keys` takes `channel_types`, `signal_tower_active_low` and the spindles' `pid_vel` out of the machine's own RosettaSet_v1.ini (after the usual backup; exports left alone - Import ignores them). Tested off the machine: the generator's Rosetta.local.ini, and the removal on a copy of Rich's file (only those keys changed; a second run removes nothing). Check: LinuxCNC starts with no new errors, AXIS's spindle override slider still tops out at 100%, AXIS's Open window offers only G-code files; the next Update prints "Removed 4 old setting(s)" on Rich's Pi and nothing about it the time after. Rich checked all of this on his Pi 09 November 2026 - it worked as expected. |
| Restore from USB (Back Up to USB too, in Rosetta Settings' File menu) | 09 November 2026 | (Idea from 06 October 2026.) Rosetta Settings' File menu has two new items, in their own group above Quit: Back Up to USB (the same window as the launcher, which stays) and Restore from USB - both in `Rosetta_Display/Rosetta_Backup.py` (1.1; `RestoreWindow`, `collect_restore`, `run_restore`, `setup_differences`), opened by `_open_backup`/`_open_restore` in `Rosetta_Settings.py`. Restore: pick the stick and a dated backup (newest first; also finds pre-rename `REB_Backup/` ones, mapping `REBset_v1.ini`/`REB_Custom/` to today's names); every file it replaces is first copied to `~/Documents/Before_Restore/YYYY-MM-DD_HHMM/`; files not in the backup are left alone; refuses while LinuxCNC runs; warns in red (doesn't block) when the backup's channel assignments or expansion box differ; ejects the stick; then Rosetta Settings closes without saving (`_closing_after_restore`), after first offering to save unsaved tuning. Tested only off the machine: back up and restore into a scratch home and fake stick (old REB backup too, difference warning, Before_Restore copies), and the windows built without showing them. Check: File > Back Up to USB works as the launcher does; File > Restore from USB lists the stick's backups, the confirm box and the Restore complete box appear, Rosetta Settings closes, and reopening it shows the restored settings; Documents/Before_Restore holds the replaced files. User Manual drafts in `~/Downloads/Rosetta_UserManual_2026-11-09/` (new Restoring page; Home, Backing Up and Saving and Sharing Settings pages updated) for Rich to paste. Rich tested both on his Pi 09 November 2026 - they work. He asked for the manual pages to explain, for owners new to Linux, that both eject the stick when they finish, so it has to be pulled out and put back to use it again - added to both drafts ("After the backup/restore finishes: the USB flash drive is ejected"). |
| Warning before running with an axis not enabled | 09 November 2026 | (Idea from 07 October 2026; Rich asked for it 08 November 2026.) New `Rosetta_Display/Rosetta_Axis_Commands.py`, loaded by AXIS from Rosetta.ini's new `[DISPLAY]USER_COMMAND_FILE`: adds to AXIS's own `run_warn` (the machine-limits check behind Run, Run From Line and Step) a look through the preview for every axis the program moves; if any has ENA off (`<letter>-ena-and.out`), a dialog says which and offers Cancel (default) or Run Anyway. AXIS reads USER_COMMAND_FILE instead of `~/.axisrc`, so the file runs `~/.axisrc` first. Tested only off the machine (a stand-in for AXIS). Check: LinuxCNC starts with the usual window size (i.e. `~/.axisrc` still applies) and no "Error in ~/.axisrc" box; with C's ENA off, Run on a program that moves C shows "C not enabled" and Cancel leaves it idle, Run Anyway runs; with every used axis enabled, Run starts with no box. Not covered: rapids before the first feed move (the preview skips them) and a program's spindles. 09 November 2026, at Rich's request: the panel's move buttons check too - `_confirm_roles_enabled` in `Rosetta_main.py` (same `<role>-ena-and.out` pins, incl. `sp0`/`sp1`) before each axis index, the spindle index (the ticked spindles), Sync Move Run Operation / Return to Start (the axes that move) and Cut Thread / Thread Return (X, Z, C); the box offers Cancel (default) or Move Anyway. Tested only with a stand-in for GTK/HAL. Check: with C's ENA off, C's index button, a Sync Move using C and Cut Thread each show "C not enabled" and Cancel moves nothing; with Sp0 ticked and its ENA off the spindle index shows "Sp0 not enabled"; with everything enabled, no box. Closed 09 November 2026 at Rich's request (both parts approved; not yet pushed when closed). |
| Spindle indexing always turns the button's way (opened 06 October 2026 as "Indexing direction for large angles") | 08 November 2026 | Rich chose one direction because of backlash: shortest path let an index of 180 degrees or more turn against the button, and Div 2 could flip from press to press. `Rosetta_main.py` now sets `orient.N.mode` before each index (`SPINDLE_INDEX_MODE`: on-screen Fwd = 1, Rev = 2 - found on Rich's Pi) and works each target out from the previous target (`_spindle_index_target`, `SPINDLE_INDEX_TRACK_DEGREES`), not from where the spindle stopped - it always stops about 0.08 degrees short, which used to add up. Verified on Rich's Pi the same day with both spindles ticked (the simultaneous path; Sp0 and Sp1 landed together every time): 90/270 degrees Fwd and Rev each turned the full way in its own direction, Div 2 the same, and Div 8 Fwd x8 landed on exact 45 degree targets every time (each 0.08 short, no build-up). User Manual Indexing page (Spindles section) drafted in `~/Downloads/Rosetta_UserManual_2026-11-08/` for Rich to paste. Not yet seen: one spindle on its own with the new code (the `M19` path), and a G-code program's own `M19` now turns the way of the last panel index rather than the shortest way. |
| Sp0 won't reverse on one box (opened 06 October 2026) | 08 November 2026 | Part of the same PCB problem on S/N 003 as its spindles not running (Rich). Left unfixed: a new PCB is being built. |
| Spindles don't run on the second machine (opened 08 October 2026) | 08 November 2026 | A wiring problem on S/N 003, probably in its PCB (Rich). Left unfixed: a new PCB is being built. The spindles work on the prototype. |
| No sound from the speaker on Rich's Pi (opened 16 October 2026) | 08 November 2026 | Sound now plays on Rich's Pi through its display, which has speakers (Rich). |
| Pi restarts when the 7i92 is switched on (opened 14 October 2026) | 08 November 2026 | Resolved by the hardware: the production boxes being scoped use a different, more powerful power supply (Rich). Until then, `Rosetta_Change_Network.sh` still offers a shutdown before the W5/W6 jumper change on today's boxes. |
| Settings file owned by root on installed machines? (opened 18 October 2026) | 08 November 2026 | No: on Rich's Pi `~/Documents/RosettaSet_v1.ini` belongs to reuben (Rich checked the file's properties). It can't stay root's on any machine either: `rosetta_settings_io.save_settings` writes a new file and renames it over the old one, so the first save - every LinuxCNC shutdown, and any update that adds a setting - makes reuben the owner. The installer has copied it without `sudo` since 18 October 2026. |
| Machine S/N on the "REB O/S ..." label; Beta 1.2 | 26 October 2026 | `REB_main.py` (main panel, `OS_Version_Label`) and `REB_Settings.py` (all four pages, `OS_Version_Label_Axis_Selection`/`_IO`/`_Tuning`/`_Other`) each gained a `_load_version_label` that appends ", Machine S/N <n>" at startup from `~/.config/REB/serial` - same friendly serial `REB_Report_Version.py` already reports. Same commit (ea6c16b, on `dev-rich` and `main`) bumped all five "REB O/S ..." labels to "REB O/S 1.0 Beta 1.2 - 26 October 2026" (capitalizing "Beta" per Rich's request going forward). Verified on S/N REB003: the suffix shows correctly on the main panel and all four REB Settings pages with no clipping. Still to confirm at some point: the label stays unchanged (no suffix) on a machine with no `~/.config/REB/serial` set. |
| `REB_Setup/lightdm.conf` deleted | 24 October 2026 | Nothing ever installed it (neither installer copied it to `/etc/lightdm/`), and it set `autologin-user=cnc`, so copying it in place would have stopped auto-login for `reuben`. The installation instructions already set desktop auto-login and no screen blanking with `raspi-config` (Step 2.4). |
| `main` fast-forwarded to `dev-rich` (two-box work released to the test machines) | 20 October 2026 | Hold lifted: Rich finished the S/N REB003 hardware testing ("everything tested perfectly") after re-testing the IP address change. S/N 1 and S/N 2 get the two-box code at their next update and stay on 192.168.1.x until moved (the generator uses 192.168.1.121 there). |
| S/N REB003 (one card): move to 10.10.10.x | 20 October 2026 | The rehearsal for S/N 1 and S/N 2. Card's address stored as 10.10.10.10, Pi's wired connection moved, W5/W6 moved to the EEPROM setting as `REB_Change_Network.sh` directs, machine switched back on. `REB_Change_Network.sh check`: Pi on 10.10.10.100/24, card answers at 10.10.10.10 (`mesaflash --readhmid` shows the REB firmware), nothing at .11 (no expansion box; Expansion Box unticked). LinuxCNC starts and runs fine (Rich), on `dev-rich` 9a08ca0. |
| Reserved G-code file names in the user manual | 20 October 2026 | Rich put a "Naming your Gcode programs" section on the Running Gcode Programs page (no names starting REB/reb, none M100-M199; rename when saving to the gcode directory) and changed step 2 to say the Open window starts in the gcode directory. That relies on `PROGRAM_PREFIX` = `gcode/` (4076f02), so it's true only on machines running `two-box` until it reaches `main`. REB's own subroutines stay `reb_...` (CLAUDE.md, "Reserved names"). |
| Fault siren on the speaker | 20 October 2026 | A following error (program run with an axis not enabled) sounded the siren on the tower and on the TV's speaker (HDMI) together, Fault Siren = Both. Needed the Pi's HDMI audio brought back first (see the speaker row in Open items). Fault Siren = Off / Speaker silencing the tower wasn't tried separately. |
| `7i92t_REB.pin` in the repo was incomplete | 16 October 2026 | It stopped after four P2 lines. Replaced with the full `mesaflash --device 7i92t --addr 10.10.10.10 --readhmid` output from Rich's Pi (the expansion card at .11 gives the same). |
| Signal tower relay polarity setting | 11 October 2026 | Dropped: the relays are on Chuck's REB circuit board, and home-built systems must follow the same active-low standard. The "Relays switch on when low" checkbox is gone; `SIGNAL_TOWER_ACTIVE_LOW` is fixed. |
| Startup splash drawing and fallback | 11 October 2026 | Verified by Rich: with X and Z assigned the preview shows "REB" over "ROSE ENGINE BUTLER", right way up, no error; X only, Z only, and neither all fall back to the empty splash; pressing Run with it loaded and the axes enabled moves nothing. |
| Items from the Mac session's list | 11 October 2026 | Copied into this file. |
| Sp0 / Sp1 running | 08 October 2026 | Verified by Rich on the prototype. |
| EtherLab "signing key is bad / expired" from apt update | 08 October 2026 | Key refreshed on the Pi; `REB_Update.sh` now refreshes it automatically (06549a8). |
| Update asking for the SSH key passphrase | 08 October 2026 | The Pi's `~/.ssh/config` uses the passphrase-free key for GitHub. Per-machine setting, not in the repo. |
| User Manual anchor for "How Limit Switches Work" | 08 October 2026 | Rich renamed it to `[[#LimitSwitches]]`. |
| Seed linear stepgen speed below the planner's | 08 October 2026 | Resolved by the speed-limits change (4835dbc): the seed plans X/Z at 0.167 in/s, below the 0.208 in/s stepgen ceiling. |
| Jog speed capping programs (C held at 10°/s) | 08 October 2026 | `[TRAJ]` caps now come from the fastest axis, not the jog setting (4835dbc). |
| Roy's program taking about 4 hours | 07 October 2026 | C acceleration 10 -> 320°/s². One-zone test 88 s -> 15.84 s, ran clean (0e860ae). Full-run time still to measure - see C top speed above. |
| Help tab making the window too wide | 05 October 2026 | Smaller title banner (e93eb18). |
| Signal tower red and green lights | 05 October 2026 | Verified on the prototype after the latch and spindle-activity fixes (e74f9c5). |
| NC limit switches | 05 October 2026 | Verified stopping motion on the prototype; red latches on a trip. |
| Mesa ground / +5V pins | 02 October 2026 | Settled by Rich on the support wiki's Mesa pin mapping page. |
