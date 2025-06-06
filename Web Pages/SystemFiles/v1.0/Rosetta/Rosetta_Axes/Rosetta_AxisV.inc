#######################################################################
#                                                                     #
#   RRRRRR     OOOOOO   SSSSSS  EEEEEEEE TTTTTTTT TTTTTTTT   AAAA     #
#   RR   RR   OO    OO SS    SS EE          TT       TT     AA  AA    #
#   RR    RR  OO    OO SS       EE          TT       TT    AA    AA   #
#   RR   RR   OO    OO  SS      EE          TT       TT    AA    AA   #
#   RRRRRR    OO    OO   SSSS   EEEEEE      TT       TT    AA    AA   #
#   RR   RR   OO    OO      SS  EE          TT       TT    AAAAAAAA   #
#   RR    RR  OO    OO       SS EE          TT       TT    AA    AA   #
#   RR    RR  OO    OO SS    SS EE          TT       TT    AA    AA   #
#   RR    RR   OOOOOO   SSSSSS  EEEEEEEE    TT       TT    AA    AA   #
#                                                                     #
#######################################################################
#
# LinuxCNC configuration for use with a Rose Engine
#
# File:
#   Rosetta_AxisV.inc
#
# Purpose:
#   This is used to setup the V axis for the configuration of LinuxCNC.
#
# End User Customisation:
#   The end user of the Rosetta system may modify this file to
#   accommodate their local configuration.  It is recommended that
#   a copy of this file be saved before changes are made.
#
#   Changes to this file are not supported by Colvin Tools.
#
# Version
#   1.0 - 27 Apr 2025, R. Colvin
#
# Copyright Colvin Tools
# ********************************************************************
# Configuration values
#
#                                 Home   PCB
#  Axis  Joint  Channel   Type     Seq  Plug  Comments
#  ----  -----  -------  -------  ----  ----  ------------------------
#   V      5       01    LINEAR     6    P12
# ********************************************************************
#
# Details about the fields are available in the 
#   LinuxCNC 2.9.4 System Manual, 
#   §4.4 INI Configuration, starting on pg. 140
#
# ********************************************************************


# ******************************************
# [AXIS_<letter>]
# Details about the fields are available in the 
#   LinuxCNC 2.9.4 System Manual, 
#   §4.4.2.12, starting on pg. 157

# [JOINT_<number>]
# Details about the fields are available in the 
#   LinuxCNC 2.9.4 System Manual, 
#   §4.4.2.13, starting on pg. 158

# ******************************************
#                                 Home
#  Axis  Joint  Channel   Type     Seq
#  ----  -----  -------  -------  ----
#   V      5       01    LINEAR     6

[AXIS_V]
MAX_ACCELERATION         = 30.0
MAX_LIMIT                = 9999.9
MAX_VELOCITY             = 1.0
MIN_LIMIT                = -9999.9
TYPE                     = LINEAR

[JOINT_5]
# STEP_SCALE can be tuned for the specific device.  The value 
# represents the number of pulses required to move the 
# distance specified by ANGULAR_UNITS or LINEAR_UNITS in
# the [TRAJ] section.  The gearing of the stepper motor
# to the movement will set this.  (pg. 163 in the manual)
#
#             1 rev   25.4 mm
# LEADSCREW = ----- * ------- = 12.7 rev/in
#             2 mm     1 inch
#
#              6,600 step   12.7 rev
# STEP_SCALE = ---------- * --------
#                1 rev       inch
#
# STEP_SCALE = 83,820 steps/inch
#
STEP_SCALE               = 83820

# pg 158
BACKLASH                 = 0.0000

# pg 161
BIAS                     = 0.0

# pg 161
DEADBAND                 = 0.0

# pg 140, 264-265, 269
DIRHOLD                  = 10000
DIRSETUP                 = 10000

# ENCODER_SCALE = STEP_SCALE
# pg 163, 164
# ENCODER_SCALE          = 325120

# pg 159
FERROR                   = 0.5

# pg 160
HOME                     = 0.0

# pg 160
HOME_OFFSET              = 0.0

# pg 160
HOME_SEQUENCE            = 3

# pg 163
# INPUT_SCALE = STEP_SCALE
# INPUT_SCALE            = 83820

# pg 160
# LOCKING_INDEXER            = 1

# pg 158
# machine units per second sq
MAX_ACCELERATION         = 30.0

# pg 159
MAX_LIMIT                = 9999.9

# pg 163
MAX_OUTPUT               = 0.0

# pg 158
# machine units per second
MAX_VELOCITY             = 0.25

# pg 159
MIN_FERROR               = 0.05

# pg 159
MIN_LIMIT                = -9999.9

# pg 163
# SCALE = STEP_SCALE
# SCALE                  = 83820

# pg 164
# STEPGEN_MAXACCEL should be 1%-10% < than MAX_ACCELERATION
STEPGEN_MAXACCEL         = 33.0

# pg 164
# STEPGEN_MAXVEL should be 1%-10% < than MAX_VELOCITY
STEPGEN_MAXVEL           = 0.275

# pg 140, 264-265, 269
STEPLEN                  = 5000
STEPSPACE                = 5000

# pg 158
TYPE                     = LINEAR

# pg 158
UNITS                    = inch

# pgs 161-162
P                        = 1000.0
I                        = 0.0
D                        = 0.0
FF0                      = 0.0
FF1                      = 1.0
FF2                      = 0.0
