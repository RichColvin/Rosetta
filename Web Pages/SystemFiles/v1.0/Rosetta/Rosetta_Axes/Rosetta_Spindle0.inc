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
#   Rosetta_Spindle0.inc
#
# Purpose:
#   This is used to setup the Spindle 0 axis for the configuration of 
#   LinuxCNC.
#
#   Spindle 0 is used for the main system spindle.
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
#  Sp0     7       05      n/a     n/a   P16
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

# [SPINDLE_<number>]
# Details about the fields are available in the 
#   LinuxCNC 2.9.4 System Manual, 
#   §4.4.2.14, starting on pg. 164

# ******************************************
#                                 Home
#  Axis  Joint  Channel   Type     Seq
#  ----  -----  -------  -------  ----
#  Sp0     7       05      n/a     n/a
#  Sp1     6       07      n/a     n/a

# [JOINT_7]
# SPINDLE                    = 0
# TYPE                   = ANGULAR

[SPINDLE_0]
# The values represent the number of pulses required to move the 
# distance specified by ANGULAR_UNITS or LINEAR_UNITS in
# the [TRAJ] section.  The gearing of the stepper motor
# to the movement will set this.  (pg. 163 in the manual)
#
# Values based on 
# 1. stepper motors with 1.8 deg / step.
#
# 2. DM542T set to Microsteps  = 32
#                  Steps / rev = 6,400
#
#   32 pulses   1 step    360 deg         pulses
#   --------- * ------- * ------- = 6,400 ------
#      step     1.8 deg    1 rev           rev
#
# 3. Spindle gear:Spindle motor gear ratio is 108:12 = 9
#

# pg 161
BIAS                     = 0.0

# pg 161
DEADBAND                 = 0.000015

# pg 140, 264-265, 269
DIRHOLD                  = 10000
DIRSETUP                 = 10000

# pg 163, 164
#
#                 32 pulses
# ENCODER_SCALE = ---------
#                  1.8 deg
#
# ENCODER_SCALE = 17.778 pulses / deg
ENCODER_SCALE            = 17.778

# pg 164
INCREMENT                = 0.1

# INPUT_SCALE = ENCODER_SCALE
# pg 163
INPUT_SCALE              = 17.778

JOINT                    = 4

# pg 160
LOCKING_INDEXER          = 1

# pg 158
# MAX_ACCELERATION = 30 deg / sec2
MAX_ACCELERATION         = 30

# rpm, pg 158
#
#                         20 Sp rev   9 motor rev
# MAX_FORWARD_VELOCITY = ---------- * -----------  
#                           1 min       1 Sp rev
#
# MAX_FORWARD_VELOCITY = 180 rpm
MAX_FORWARD_VELOCITY     = 180

# MAX_LIMIT              = 1e99

# pg 159, 163
MAX_OUTPUT               = 10.0

# MAX_REVERSE_VELOCITY = MAX_FORWARD_VELOCITY
# MAX_REVERSE_VELOCITY   = 180

# pg 158
# MAX_VELOCITY = MAX_FORWARD_VELOCITY
# MAX_VELOCITY           = 180

# rpm, pg. 164
MIN_FORWARD_VELOCITY     = 0.0

# MIN_LIMIT              = -1e99
# rpm, pg 158
MIN_REVERSE_VELOCITY     = 0.0

OUTPUT_TYPE              = angular

# SCALE = ENCODER_SCALE
# pg 163
SCALE                    = 17.778

# 1%-10% higher than MAX_ACCELERATION
# pg 164
STEPGEN_MAXACCEL         = 33

# 1%-10% higher than MAX_VELOCITY
# pg 164
STEPGEN_MAXVEL           = 0.25

# pg 140, 264-265, 269
STEPLEN                  = 5000
STEPSPACE                = 5000

# pg 163
#
#               32 pulses   360 deg   9 motor rev
# STEP_SCALE = ---------- * ------- * -----------
#               1.8 deg      1 rev     1 Sp rev
#
# STEP_SCALE = 57,600 pulses / deg
STEP_SCALE               = 57600

TYPE                     = angular

# pgs 161-162
P                        = 1000.0
I                        = 0.0
D                        = 0.0
FF0                      = 1.0
FF1                      = 0.0
FF2                      = 0.0
