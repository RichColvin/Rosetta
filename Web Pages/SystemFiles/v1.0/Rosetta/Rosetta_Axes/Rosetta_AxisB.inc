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
#   Rosetta_AxisB.inc
#
# Purpose:
#   This is used to setup the B axis for the configuration of LinuxCNC.
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
#   B      3       06    ANGULAR    4    P17
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

[AXIS_B]
# machine units per second sq
MAX_ACCELERATION         = 30.0
# for unlimited rotation, set this to 1e99
MAX_LIMIT                = 9999.0
# machine units per second
MAX_VELOCITY             = 1.0
# for unlimited rotation, set this to -1e99
MIN_LIMIT                = -9999.0
TYPE                     = ANGULAR
WRAPPED_ROTARY           = 1

[JOINT_3]
# STEP_SCALE can be tuned for the specific device.  The value 
# represents the number of pulses required to move the 
# distance specified by ANGULAR_UNITS or LINEAR_UNITS in
# the [TRAJ] section.  The gearing of the stepper motor
# to the movement will set this.  (pg. 163 in the manual)
#
#              1 rev
# LEADSCREW = ------- = 0.2 rev/deg of device movement
#              5 deg
#
#              32 steps   360 deg   0.2 rev
# STEP_SCALE = -------- * ------- * -------
#               1.8 deg     1 rev     1 deg
#
# STEP_SCALE = 1,280 steps/deg
#
STEP_SCALE               = 1280

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
# ENCODER_SCALE          = 1280

# pg 159
FERROR                   = 0.5

# pg 160
HOME                     = 0.0

# pg 160
HOME_OFFSET              = 0.0

# pg 160
HOME_SEQUENCE            = 4

# pg 163
# INPUT_SCALE = STEP_SCALE
# INPUT_SCALE            = 1280

# pg 160
# LOCKING_INDEXER            = 1

# pg 158
# machine units per second sq
MAX_ACCELERATION         = 30.0

# pg 159
# for unlimited rotation, set this to 1e99
MAX_LIMIT                = 9999.9

# pg 163
MAX_OUTPUT               = 10.0

# pg 158
# machine units per second
MAX_VELOCITY             = 1.0

# pg 159
MIN_FERROR               = 0.05

# pg 159
# for unlimited rotation, set this to -1e99
MIN_LIMIT                = -9999.9

# pg 163
# SCALE = STEP_SCALE
# SCALE                  = 1280

# pg 164
# STEPGEN_MAXACCEL should be 1%-10% < than MAX_ACCELERATION
STEPGEN_MAXACCEL         = 37.50

# pg 164
# STEPGEN_MAXVEL should be 1%-10% < than MAX_VELOCITY
STEPGEN_MAXVEL           = 1.25

# pg 140, 264-265, 269
STEPLEN                  = 5000
STEPSPACE                = 5000

# pg 158
TYPE                     = ANGULAR

# pg 158
UNITS                    = degree

# pgs 161-162
P                        = 1000.0
I                        = 0.0
D                        = 0.0
FF0                      = 0.0
FF1                      = 1.0
FF2                      = 0.0
