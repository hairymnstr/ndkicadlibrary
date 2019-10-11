#!/usr/bin/env python

"""
NAME
    set_temp_version.py - Backs up then modifies KiCad schematics/PCB files with version data

SYNOPSIS
    set_temp_version.py [OPTIONS] <PROJECT DIR>

DESCRIPTION
    First copies all kicad_pcb and sch files in a folder by adding a .unver extension.
    Opens each one and replaces wildcard pattern %VER% with a major.minor version format and
    %DATE% with the current date.  Can be called with --restore to remove the extensions
    thus restoring the files with their wildcard variables.

    -r, --restore
        Restore the backups
    --major=VAL
        Specify the major version number
    --minor=VAL
        Specify the minor version number
    -h, --help
        Show this help and exit
"""

"""
Copyright 2018 Chronos Technology Ltd
Copyright 2019 Nathan Dumont

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
   and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
   and the following disclaimer in the documentation and/or other materials provided with the
   distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import getopt, os, sys, shutil, time, logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def error_exit(msg, code):
    print("{}: {}".format(sys.argv[0], msg))
    print("Try '{} --help' for more information".format(sys.argv[0]))
    sys.exit(code)

# generate a date string once up here in case the build job happens around midnight for some reason
date_string = time.strftime("%Y-%m-%d")

try:
    opts, args = getopt.getopt(sys.argv[1:], "rh", ("restore", "major=", "minor=", "help"))
except getopt.GetoptError as err:
    error_exit(str(err), -2)

restore = False
major = None
minor = None
for o, a in opts:
    if o in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    elif o in ("-r", "--restore"):
        restore = True
    elif o in ("--major"):
        major = a
    elif o in ("--minor"):
        minor = a

if restore == False and (major == None or minor == None):
    error_exit("If not restoring you need to specify the major and minor revisions", -2)

if len(args) != 1:
    error_exit("You must specify exactly 1 project directory", -2)

if not os.path.isdir(args[0]):
    error_exit("Project path must be a directory", -2)

if restore:
    file_list = os.listdir(args[0])
    for f in file_list:
        if f.endswith(".unver"):
            os.rename(os.path.join(args[0], f), os.path.join(args[0], f[:-6]))

else:
    file_list = os.listdir(args[0])
    for f in file_list:
        if f.endswith(".sch") or f.endswith(".kicad_pcb"):
            logging.info("Setting date/version in {}".format(f))
            shutil.copy(os.path.join(args[0], f), os.path.join(args[0], f + ".unver"))
            with open(os.path.join(args[0], f), "r") as fr:
                d = fr.read()
            
            d = d.replace("%VER%", "{}v{}".format(major, minor))
            d = d.replace("%DATE%", date_string)

            with open(os.path.join(args[0], f), "w") as fw:
                fw.write(d)
