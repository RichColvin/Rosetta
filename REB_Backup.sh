#!/bin/bash
# Stand-in left by the Rosetta renaming (02 November 2026): desktop and
# menu launchers made before then run this file. Runs Rosetta_Backup.sh instead.
# Remove once every machine has been updated (its update points the
# launchers at the new name) - see the tracker's Rosetta renaming items.
exec bash "$(dirname "${BASH_SOURCE[0]}")/Rosetta_Backup.sh" "$@"
