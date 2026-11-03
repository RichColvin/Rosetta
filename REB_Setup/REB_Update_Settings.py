#!/usr/bin/env python3
# Stand-in left by the Rosetta renaming (02 November 2026).
#
# A machine built before then runs its old update script, which pulls
# the new files and then runs this file by its old full path
# (.../RoseEngineButler/REB_Setup/REB_Update_Settings.py). It hands
# over to Rosetta_Update_Settings.py, which also moves the machine over
# to the new names. Remove once every machine has been updated (see the
# tracker's Rosetta renaming items).
import os
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = os.path.join(REPO_DIR, "Rosetta_Setup", "Rosetta_Update_Settings.py")
os.execv(sys.executable, [sys.executable, NEW] + sys.argv[1:])
