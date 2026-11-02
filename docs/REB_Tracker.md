# Rose Engine Butler Tracker

The one list of open, untested and recently settled items for the Rose
Engine Butler. It lives in the repo so every Claude Code session (the Pi
and the Mac) and everyone working on REB sees the same list after a
`git pull`. Claude sessions keep their own per-machine notes, which the
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
| Script fixes from the Support Manual write-up | 18 October 2026 | On `dev-rich` (made 18 October 2026, lost in a merge on the Mac, re-applied 24 October 2026): `REB_Update.sh` and `REB_Install_Debian_13_Trixie.sh` are now marked runnable; the installer's first line is `#!/bin/bash` (was `#! /home/reuben/Downloads`), a failed step now exits with code 1 (`exit $?` after an `echo` always gave 0), it copies `REB_Update.sh` and `REBset_v1.ini` without `sudo`, so reuben owns them, and its Step 1 message no longer says "connectin"; `REB_Update.sh`'s "local changes" warning names the Support Manual page "Updating Rose Engine Butler" (it said "Updates and Branches", which doesn't exist); `REB_Settings.sh`/`REB_Launch.sh` header comments updated. Check: after an update the icon still runs `REB_Update.sh` and its warning text fits the box; on the next fresh install `ls -l ~/Documents/REBset_v1.ini ~/REB_Update.sh` shows reuben as owner. |
| Bench checkout (`REB_Checkout.sh`) | 18 October 2026 | Written on the `two-box` branch 18 October 2026 but left out of its merge; on `dev-rich` since 24 October 2026. First run on S/N REB003 with a labelled test motor on each channel: `./REB_Checkout.sh` in a terminal; check each channel's motor turns channel+1 times each way in both passes, the spindles index in quarter turns (`M19 R.. $n`), the all-together move finishes together, the program's `M0` pauses and `(MSG,...)` lines show in AXIS, and `~/Documents/REBset_v1.ini` is identical to the backup in `~/Documents/Checkout/<run>/` afterwards (also after a Ctrl+C part way). Assumes 6400 steps per turn (`--steps-per-rev` otherwise). |
| E-stop button | 28 September 2026 | Pressing it (and unplugging it) latches E-stop; release then F1 resets. Needs "Connected" ticked in REB Settings. |
| NO limit switches | 08 October 2026 | With Limit Switch Type set to Normally open, a tripped NO switch stops the axis (reads the jack's GPIO `.in_not`). NC is already verified - see Done. |
| Done / Pause beeps | 06 October 2026 | 3 beeps when a program finishes normally, 2 at M0/M1/M60, none on an abort. 20 October 2026: no beeps at M30 on Rich's o-word program (`Geo1216Case12-10-13-26b.ngc`) - the old check wanted `motion_line` to reach the file's last axis move, which was in a skipped `If`. Rewritten on `two-box` (e7aacc3): finished = the interpreter read to the M2/M30 and LinuxCNC says `RCS_DONE` as the run goes idle (both logged on the machine at a finish and a Stop). Verified 20 October 2026: at M30 on that program the tower gave 3 beeps and the TV the new ta-da (`REB_Done.wav`, 897b2b3; the speaker's pause sound is now two rising notes, da22df3). Still to check: none after Stop or E-stop part way, the pause sound + 2 tower beeps at an M0, a simple program. Cherry-picked to `dev-rich` the same day (ddf0df8..cb6da15), so it reaches `main` with the next fast-forward. |
| Speed limits in REB Settings | 08 October 2026 | Max Speed / Max Acceleration / PID Max Output from REB Settings reach LinuxCNC; `REB_Update.sh` fills them in correctly on an existing machine. On the tuning page: each group shows four rows, a warnings line and a closed "Advanced settings" twistie with a note beside every row, nothing cut off; no warnings on a normal machine; changing C's Max Speed carries Stepgen Max Vel and PID Max Output along; linear Max Speed stops at 1.0 in/s; Restore Defaults resets an axis's advanced values. The window itself was never opened before commit (no GTK on the Mac). |
| C top speed 30°/s | 07 October 2026 | A 360° G0 rewind of C takes about 12 s (was 36 s). Then time a full run of Roy's Pumping5Sides program - estimated about 46 minutes (was about 4 hours). |
| Threading tab | 24 September 2026 | C turns the right way for a right-hand thread, and outside threading feeds in toward -X. |
| EtherLab key refresh in `REB_Update.sh` | 08 October 2026 | Tested on its own (current key, stale key, server unreachable), not yet as part of a full update run. |
| Back Up to USB | 06 October 2026 | Insert a stick, run a backup, then check the dated `REB_Backup/` folder and `backup_log.txt` on another computer, and that the stick ejects with "Safe to remove". Also add the MenuLibre menu and desktop entries - Command `/home/reuben/linuxcnc/configs/RoseEngineButler/REB_Backup.sh`, Icon `REB_Setup/Images/REB_Backup.png`. |
| REB.ini / REB.hal cleanup | 06 October 2026 | LinuxCNC starts with no HAL errors, an axis jogs and moves, and an Sp0 M19 index works. Probably already exercised by the 08 October spindle and speed-limit testing - tick it off if so. |
| Index counters on the Indexing tab | 11 October 2026 | Each axis row and the spindle row show a count left of Distance: +1 per Fwd index, -1 per Rev (it can go negative). Resets to 0 at startup, on a distance or deg/div change, and on a double-click of the number. Check the count follows the on-screen Rev/Fwd columns, the spindle count works with Sp0, Sp1 and both, and the Distance column didn't get wider. Double-click reset verified by Rich, 11 October 2026 (after it was rebuilt on the button's "clicked" signal); still to check: the counting itself on real presses. |
| Notes in REBset_v1.ini | 11 October 2026 | After an update (run twice on Chuck's and Roy's machines), `~/Documents/REBset_v1.ini` starts with the "Rose Engine Butler settings" notes and ends with the copyright, and the other settings/export files there have their notes too (not the `.bak-` backups); LinuxCNC and REB Settings still start, and Load Settings reads both a "Save All Settings As..." copy and a Save Subset export. |
| Mesa's HAL order on a one-card machine | 16 October 2026 | (`two-box`, 10f3634.) With one card the servo thread is now read, everything else, write (Peter Wallace's order; the write used to follow the read straight away). Tested only with two cards. When Rich's single-card machine is rebuilt: LinuxCNC starts, axes jog and run a program with no following errors, and `halcmd show thread` stays well under 1000 us. 20 October 2026: LinuxCNC starts and runs on S/N REB003 (one card at 10.10.10.10); program run and thread time still to check. |
| Program progress bar | 20 October 2026 | (`two-box`, 5d644c8; percentage only since 946709e - Rich found the time left kept changing, like an O/S upgrade's.) Bar left of Sync Move: "Program 42%", "(paused)", then "Program done in ..." / "stopped at 42%". First run 20 October 2026: the bar shows and moves, and `program-path` grew 11.924 over the run - the estimate's total exactly. But it lagged real progress by up to 30% (51% at 80% of the run), so the estimate now includes acceleration and is worked out as the program starts (044193e) - within 6% when replayed against that run's log. Second full run 20 October 2026 with that change: within 5% of real progress all the way (average 2%; 52% at the halfway point, 83% at 80%), `program-path` again matched the estimate (11.924), finished correctly at M30. Sync Move and Cut Thread now use the bar too (b49fcff, "Sync Move 42%" / "Threading 25%" counted in passes; not Run Operation, indexing or Return) - both verified 20 October 2026 (Sync Move climbed smoothly; a 1-start, 3 pass + 1 spring thread stepped 0/25/50/75/100%). Found then and fixed on `two-box`, both verified after a restart the same day: the pressed Sync Move / Cut Thread button went blank (disabled grey text on the dark background; now white, 9f124fe), and the startup splash cluttered the preview under a Sync Move or Cut Thread's tool path (now swapped for the empty preview first, df43721). Also still to check: Stop shows "stopped at", Run From Line shows "started part way", the panel doesn't change size on any tab. Same day, separate commits: the Settings gear note was removed and the library button moved up (565a351) - verified, the Sync Move tab now fits the screen; and AXIS's Open dialog starts in `gcode/` (`PROGRAM_PREFIX`, 4076f02). |
| Folder shortcuts on other machines | 20 October 2026 | `REB_Setup/REB_Add_Shortcuts.sh` (265ca51): Thunar Places "RoseEngineButler" and "Gcode", plus Reuben-head launchers for them on the bottom bar right after File Manager (Gcode's icon has a "G" badge). Tested on Rich's Pi (from a clean state, re-run, `--force` - nothing doubled). Still to see: the Trixie installer's new Step 10 on a fresh install (the Bookworm installer wasn't changed), and S/N 1 and 2 getting them on their first update once `main` moves (via `REB_Update_Settings.py`) - their bottom bar may be laid out differently; with no File Manager launcher the launchers are skipped but Places is still added. |
| File menu in REB Settings | 07 October 2026 | Ctrl+S / Shift+Ctrl+S / Ctrl+O / Ctrl+Q do the same as the buttons, including a half-typed value being saved. |
| Startup gcode reserved-name check | 23 October 2026 | New REB Settings > Other tab > Startup File Check radios (Abort startup - default, or Warn but continue), plus a scan added to `REB_Setup/REB_Generate_Local_Ini.py` (`check_reserved_gcode_names`, run from `main()` before anything else): refuses, or warns, if `gcode/` holds a file starting with "reb"/"REB" (any case) or named M100-M199, since LinuxCNC's `PROGRAM_PREFIX` search would find such a file before REB's own subroutines/M-codes - see "Reserved names" in CLAUDE.md. REBset_v1.ini's `startup_file_check` ("abort"/"warn"), seeded in `REB_Setup/REBset_v1.ini`. Verified stand-alone on Rich's Pi 23 October 2026 (no LinuxCNC running): the Abort and Warn GTK dialogs both render correctly with the offending file(s) listed, the scan correctly matches `reb_test.ngc`/`REBrose.ngc`/`M105.ngc`/`m199` and excludes `m200.ngc`/`myprogram.ngc`/`M1.ngc`, and the Settings radios save/load round-trip. Not yet run through a real `REB_Launch.sh` -> `linuxcnc` start: check a reserved file in `gcode/` is caught at a real launch, Abort stops before LinuxCNC opens (and the dialog's wording is legible full-size), Warn shows the dialog then LinuxCNC starts normally, and a clean `gcode/` launches with no dialog at all. Also added the same day: Abort plays a new short "uh oh" sound (`REB_Display/Sounds/REB_Abort.wav`, two tones, raised an octave per Rich's ear) on the speaker - the fault siren was tried first and found too alarming for a renamed-file nag; not yet heard through a real launch, only the stand-alone test. |
| Version reporting (who's running what) | 23 October 2026 | New `REB_Setup/REB_Report_Version.py`, run every update from `REB_Update_Settings.py`'s `main()`: builds a report of this Pi's own hardware serial (`/proc/cpuinfo`, unique with no coordination needed - Rich's call, so a self-built machine can never collide with a factory one), the friendly serial number from `~/.config/REB/serial` if set (for support calls only, doesn't need to be unique), and the version read straight out of `REB_Panel_v1.ui`'s "REB O/S ..." label. New `REB_Setup/REB_Set_Serial_Number.sh` asks for the friendly number (skippable, asks again next update until set) - added to `REB_Update_Settings.py`'s `ONE_TIME_STEPS` (runs every update, self-skips once set, same pattern as the folder shortcuts) and to the Trixie installer as Step 11. **The receiving side is live**: `reb_report.php`/`reb_report_view.php` on `support.roseenginebutler.com` (not in this repo - drafted into `~/Downloads` for Rich to deploy by hand), appending each report to a server-side `reb_reports.jsonl`; `reb_report_view.php` shows it as a table (one row per machine, latest wins, sorted newest-first), behind HTTP Basic Auth (user `REBmachines`, password known to Rich only - not recorded here). `.htaccess` blocks direct HTTP access to `reb_reports.jsonl` and `.htpasswd` themselves (403, confirmed). `REPORT_URL` in `REB_Report_Version.py` now points at the real endpoint - verified 23 October 2026 end-to-end: a real POST from this Pi landed in the server log, the view page requires login (401 without, 200 with correct credentials, confirmed by Rich), and the two direct-access blocks hold. `reb_reports.jsonl` currently has a handful of `test-*` hardware_id entries from this testing - harmless, but worth clearing out next time Rich is in the viewer. Not yet run through a real install or a real `REB_Update.sh` run on a second machine - check Step 11 prompts correctly on a fresh install, and that an existing machine gets asked on its next update and its report actually appears in the live table. |
## Open items and follow-ups

| Item | Since | Notes |
|---|---|---|
| `REBset_v1.ini` owned by root on installed machines? | 18 October 2026 | The installer used `sudo cp`, so on a machine installed with it `~/Documents/REBset_v1.ini` may belong to root. Check S/N 1, 2 and REB003 with `ls -l ~/Documents/REBset_v1.ini`; fix with `sudo chown reuben:reuben ~/Documents/REBset_v1.ini`. (Saving may still have worked if the file is replaced rather than written in place - check before assuming a problem.) |
| `/home/reuben/REB_Update.sh` copy | 18 October 2026 | The installer copies `REB_Update.sh` into the home folder, and updates never refresh that copy. Find out what the Update desktop icon and menu entry run: if it's the home-folder copy, point them at `/home/reuben/linuxcnc/configs/RoseEngineButler/REB_Update.sh` (with `bash` in front on machines installed before the 18 October 2026 fixes, when it wasn't marked runnable) and stop the installer making the copy. |
| Support Manual: key program pages | 18 October 2026 | Published on support.roseenginebutler.com 18 October 2026 (REB Key Programs and one page per script). A review against `main` on 24 October 2026 drafted updates as PmWiki source in `~/Downloads/REB_SupportManual_Review_2026-10-24` on the Mac (folder shortcuts, serial number, version report, reserved-name check; GladeVCP page restored) - paste each into its page. The pages still describe the scripts before the 18 October fixes (e.g. "run REB_Update.sh with bash", the root-owned settings file) - trim those notes once the fixes reach `main`. |
| Pi restarts when the 7i92 is switched on | 14 October 2026 | Every REB box (S/N 1, 2 and REB003) powers the Pi and the 7i92 from one 24V -> 5V module; switching the card on while the Pi runs restarts the Pi without a shutdown (risk to the SD card). In normal use both come on together, so it only bites during the W5/W6 jumper change. Handled in the procedure, not the hardware (16 October 2026, 91ca961 on `two-box`): `REB_Change_Network.sh` now stores the card's address, moves the Pi, then offers to shut the Pi down - switch the machine off, move W5/W6, switch on, run `REB_Change_Network.sh check`. The installer does the same at its end (`--no-shutdown` in its Step 2). Used for real on S/N REB003, 20 October 2026: W5/W6 moved, switched back on, `check` passed and LinuxCNC ran (see Done). Spare "Wired Ethernet" profiles: the other machine still has three - the script offers to delete them. |
| Release Notes page in the user manual | 20 October 2026 | New manual page Main.ReleaseNotes ("What's New in Rose Engine Butler"), linked from the home page's right column under "Rose Engine Butler Versions"; published by Rich 20 October 2026 with one entry, "REB O/S 1.0 - 20 October 2026", the original version. Each entry's heading is written exactly as the screen label reads ("REB O/S x.y - dd Month yyyy"). **At release (about April 2027):** set Version 1.0's date (heading and the example label) to the release date and drop "beta 1" from the five REB O/S labels ("REB O/S 1.0 - <release date>"). **After release, every time `main` is moved:** add an "REB O/S x.y - date" entry at the top (New / Changed / Fixed - a hidden template is on the page) and raise the REB O/S labels to that version and date, so owners can match their screen to the page. |
| Move S/N 1 and S/N 2 to 10.10.10.x | 16 October 2026 | Rich's decision: every machine and the shipping boxes on 10.10.10.x (base card .10, expansion .11, Pi .100), so a customer can just add an expansion box. The two-box work is on `main` since 20 October 2026, so each owner: update, then `REB_Change_Network.sh base` (card already has REB firmware - answer no to writing it), shut down, move W5/W6, switch on, `check`. Order doesn't matter: the generator uses 192.168.1.121 while the Pi is still on 192.168.1.x (91ca961). 20 October 2026: Rich sent both owners the steps (`REB_Change_Network.sh base`, shut down, W5/W6, switch on, `check`) - waiting to hear they've done it. Rehearsed on S/N REB003 (one card) 20 October 2026 - see Done. |
| No sound from the speaker on Rich's Pi | 16 October 2026 | The Pi's audio output was "Dummy Output" (`wpctl status`), so the fault siren and done/pause beeps played into nothing. 20 October 2026: the TV (Philips 40PFL6533 on HDMI 0) does take HDMI audio - `aplay` straight to `hdmi:CARD=vc4hdmi0` was heard - but PipeWire had offered no HDMI output since the 16 October boot (probably the TV not ready at boot). `systemctl --user restart wireplumber` brought "Built-in Audio Digital Stereo (HDMI)" back as the default, and `pw-play` (the panel's player here) was then heard. The TV also cut off the first beep, so each `.wav` now starts with 0.5 s of silence (`two-box`, a9e1604). Watch whether it comes back as Dummy Output after a reboot - if so, the fix is in the boot order (TV on first) or a WirePlumber setting, not the panel. Then retest the fault siren on the speaker. |
| Spindles on the second machine | 08 October 2026 | Sp0/Sp1 don't run there. They work on the prototype, so this is that machine's wiring - check its cables, plugs and drives first. |
| Limit jack pin map | 28 September 2026 | `LIMIT_JACK_INPUT` (jacks 1/2/3 -> I/O 002/006/010) is a placeholder until the PCB wiring is final. Space is left on the Axis Selection page for a Limit Jack 4. |
| Tell Roy about the C speed-up | 07 October 2026 | Close LinuxCNC, run the update **twice** in a row before starting LinuxCNC again, and check the output shows C's new limits. |
| Roy's program: skip the C rewinds | 07 October 2026 | Optional, Roy's call: resetting C's coordinate to 0 after each pass instead of rapiding back 360° would save the rewind time entirely. |
| Warn when running with an axis not enabled | 07 October 2026 | Idea: a program started with an axis's ENA off ends in a "following error"; a plain "C is not enabled" warning before the run would be clearer. Not started. |
| Sp0 won't reverse on one box | 06 October 2026 | Run Operation Rev and index Rev both turned Sp0 forward; Sp1 reversed fine. Not caused by the 06 October cleanup (Sp0's speed path is unchanged). Suspected hardware: Sp0 DIR is P1 pin 11 (I/O 026), right next to the tower buzzer on P1 pin 13 (I/O 027) - a bridge would pin DIR whenever the tower is enabled. Checks: retest on the known-good prototype; `halcmd show sig spindle.0-vel-cmd-final` in Fwd and Rev (sign should flip); untick Signal Tower and retry; swap Sp0/Sp1 channels or plugs. May be the same box as "Spindles on the second machine". |
| Indexing direction for large angles | 06 October 2026 | `orient.0`/`orient.1` mode is hardwired to 0 (shortest path), so an index of 180° or more can turn the opposite way from the button pressed. Decide whether to make Fwd/Rev always turn the requested way. |
| User Manual pages for Backup, Sounds and Signal Tower | 07 October 2026 | PmWiki pages Main.BackUpToUSB, Main.Sounds and Main.SignalTower were drafted on the Mac but never committed, and the folder they were in is gone - confirm they were pasted into the wiki, or ask Claude to redraft them. Also: upload `REB_Backup.png` to `UserManual/Images/`, add the pages to the sidebar, and confirm the menu entry is named "Back Up to USB". The Signal Tower page says towers must be PNP / common-negative (NPN won't work with the standard cabling) - confirm. The Sounds page predates the fault siren on the speaker and needs that added. |
| User Manual: tuning page | 08 October 2026 | Update for the new Max Speed / Max Acceleration rows, the Advanced settings twisties, the row notes and Restore Defaults, once the screen has been seen on the Pi. |
| Restore from USB | 06 October 2026 | Idea, not started: a matching program to copy a dated backup back onto the Pi. Check how it should fit with the existing `REB_Display/REB_Settings_Restore.py` first. |
| REB.ini: possibly redundant keys | 06 October 2026 | Left in during the cleanup because how AXIS uses them wasn't certain: `[FILTER]` (opens .png/.gif/.jpg and .py files through image-to-gcode - remove if never used), `[DISPLAY]MIN_VELOCITY` and the un-numbered `MAX_SPINDLE_OVERRIDE`/`MIN_SPINDLE_OVERRIDE`. |
| Old keys in settings files | 08 October 2026 | Machines' REBset_v1.ini may still hold an inert `pid_vel` block from the removed spindle velocity PID, and (since 11 October 2026) a `signal_tower_active_low` value from the removed relay-polarity checkbox. Nothing reads either; harmless. Could be removed by `REB_Update_Settings.py` some day. |
| Leftover repo copy on the Mac | 06 October 2026 | `~/Documents/GitHub/RoseEngineButler` is a stale duplicate (with one unpushed commit, now also in the real repo). Safe to delete; the working copy is iCloud Drive > Shared iCloud > Rich > GitHub > RoseEngineButler. |

## Planning

Ideas and designs not yet being built. Nothing here has code yet.

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
      now the rosette `REBLogo-Sm-rev.png`), the Rosetta Settings window
      title and its "LinuxCNC is running" message, file-chooser names and
      errors, Back Up to USB's title and log, Checkout's messages.
      `REB_Report_Version.py` 1.2 reads the "O/S ..." label with or
      without "REB " (it found nothing once "REB " was taken off).
      Still "REB" on purpose until the file renames: the reserved-name
      rule ("never start a G-code file name with REB") in Rosetta Settings
      and the generator's message.
- [ ] **Logos - need new artwork from Rich** (02 November 2026). Still
      showing Reuben or "Rose Engine Butler": `REBStartupImage.gif` (the
      AXIS splash, `[DISPLAY]INTRO_GRAPHIC` in REB.ini - the name in
      text plus Reuben), the Help tab's three book-spine buttons
      `REB-UserManualsm.png`, `REB-Forumsm.png`, `REB-Gcodesm.png` (the
      name plus Reuben at the foot). Deleted 02 November 2026 at Rich's
      request, as nothing used them: `REBLogo-Sm.png`,
      `REBLogo-Sm-Panel*.png`, `REB-Forum.png`, `REB-Gcode.png`,
      `REB-UserForum.png`, `REB-UserManual.png`, `ReubenHeadSmall.png`,
      `Reuben.png`, `Reuben-rev.png` (in `REB_Display/Images/`),
      and `REB_Setup/Images/Reuben.gif` (Rich's copies of the old artwork
      stay in `REB_Setup/Images/Saved Images/`). Kept though unused:
      `RosettaLogo-Black-Sm.png`, and `REB_Setup/Images/Reuben.png` - the
      full-size rosette artwork despite its name (d733f26); rename it with
      the file renames. Already new:
      `REBLogo-Sm-rev.png` (panel/Settings/licence), the
      `ReubenHead*.png` launcher icons and `REBWallpaper.png` (d733f26).
- [x] Startup splash (02 November 2026, not yet seen in AXIS): the
      preview now draws the rosette (eight circles through one centre,
      like the logo - each one full `G2`) over "ROSETTA" (`SPLASH_GLYPHS`
      gained an "A"). Checked through LinuxCNC's own interpreter
      (`rs274`, no errors) and drawn as the lathe view shows it.
- [x] Web links (02 November 2026, not yet clicked on a machine): the
      panel's buttons now open colvintools.com/Rosetta/,
      .../UserManual/ and .../Forum/ (`WEBSITE_URL`, `USER_MANUAL_URL`,
      `USER_FORUM_URL`, `GCODE_LIBRARY_URL` at the top of `REB_main.py`),
      Rosetta Settings' manual buttons go to the new manual (every page
      they name exists there), the version report posts to
      colvintools.com/Rosetta/Support/reb_report.php. **Still on the old
      address:** the G-code library (gcode.RoseEngineButler.com - no
      Rosetta home yet), and `README.md`'s image.
- [ ] Version report server: the script is on the new site (answers
      405 to a plain GET, as the old one does). Machines not yet updated
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

**Tasks - file and program names (own branch):**

- [ ] Rename the files and every reference (scripts, `.ini`/`.hal`
      paths, `-u REB_Display/REB_main.py`, `EMBED_TAB_COMMAND`,
      `SUBROUTINE_PATH`, `.gitignore`'d `*.local.*` names).
- [ ] Subroutines `reb_thread.ngc` / `reb_thread_return.ngc` -> new
      prefix, and the `o<...> call`s in `REB_main.py`.
- [ ] Settings file: new name in `~/Documents`, the generator, every
      program and the seed; existing machines' file moved by a one-time
      step (keep a backup); Load Settings still reads old
      `.REBset_v1.ini` exports.
- [ ] `~/.config/REB/` (serial, shortcuts marker, report log) -> new
      folder, moved by a one-time step.
- [ ] **Updating built machines safely.** The `~/REB_Update.sh` copy
      that runs the update was written before the rename and calls
      `.../RoseEngineButler/REB_Setup/REB_Update_Settings.py` by full
      path after its `git pull`. Leave a small stand-in at that old path
      (and at the old launch/settings script paths the launchers use)
      for a release or two, and have the one-time step re-point the
      launchers. If the folder itself is renamed, the stand-in has to be
      the old folder name (a symlink) - test this on a spare card first.
- [ ] Backup folder name on USB sticks (`REB_Backup/`) and Checkout run
      folder.
- [ ] Mesa firmware `7i92t_REB.bin`/`.pin` and `PIN_REB_34.vhd`: probably
      leave as they are (cards already flashed don't care; it's Mesa's
      file) - or rename the copies only.
- [ ] `CLAUDE.md`, this tracker's name (`docs/REB_Tracker.md`) and the
      docs folder.
- [ ] Test: fresh install from the Trixie installer, an update on a
      machine built before the rename (S/N 1/2-style), Load of an old
      export, the version report reaching the server, Back Up to USB,
      Checkout.

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
