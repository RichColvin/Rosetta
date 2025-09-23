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
#   Rosetta_AxisZ.inc
#
# Purpose:
#   This is used to setup the Z axis for the configuration of LinuxCNC.
#
# End User Customisation:
#   The end user of the Rosetta system may modify this file to
#   accommodate their local configuration.  It is recommended that
#   a copy of this file be saved before changes are made.
#
#   Changes to this file are not supported by Colvin Tools nor
#   Brainwave Embedded.
#
# Version
#   1.0 - 27 Apr 2025, R. Colvin
#
# Copyright (c) 2025 Colvin Tools and Brainwave Embedded. 
#
# The following MIT/X Consortium License applies to the Rosetta system.
# Use of this system constitutes consent to the terms outlined below.
#
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files (the 
# "Software"), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to 
# the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of COPYRIGHT HOLDERS
# shall not be used in advertising or otherwise to promote the sale, 
# use or other dealings in this Software without prior written 
# authorization from COPYRIGHT HOLDERS.
#
# ********************************************************************
# Configuration values
#
#                                 Home   PCB
#  Axis  Joint  Channel   Type     Seq  Plug  Comments
#  ----  -----  -------  -------  ----  ----  ------------------------
#   Z      2       00    LINEAR     3    P11
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
#   Z      2       00    LINEAR     3

[AXIS_Z]

# pg 157
# machine units per second sq
MAX_ACCELERATION         = 30.0

# pg 157
MAX_LIMIT                = 9999.9

# pg 157
# machine units per second
MAX_VELOCITY             = 1.0

# pg 157
MIN_LIMIT                = -9999.9

# pg 157
TYPE                     = LINEAR

[JOINT_2]
# STEP_SCALE can be tuned for the specific device.  The value 
# represents the number of pulses required to move the 
# distance specified by ANGULAR_UNITS or LINEAR_UNITS in
# the [TRAJ] section.  The gearing of the stepper motor
# to the movement will set this.  (pg. 163 in the manual)
#
#             1 rev   25.4 mm
# LEADSCREW = ----- * ------- = 5.08 rev/in
#             5 mm     1 inch
#
#              6,600 step   5.08 rev
# STEP_SCALE = ---------- * --------
#                1 rev       inch
#
# STEP_SCALE = 33,528 steps/inch
#
STEP_SCALE               = 33528

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
# INPUT_SCALE            = 33528

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
# SCALE                  = 33528

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
