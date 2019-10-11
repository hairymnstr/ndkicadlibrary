#!/usr/bin/env python3
"""
NAME
    make-manufacturing-data.py - one step manufacturing data exporter for KiCad projects

SYNOPSIS
    make-manufacturing-data.py [OPTIONS]

DESCRIPTION
    Sets up the environment for running an automated export of KiCad manufacturing files,
    runs the export and cleans up.  Assumes there is a Makefile which wraps the specifics
    for the project.

    -h, --help
        Show this help and exit
    -d, --debug
        Do a debug build
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

import os, sys, getopt, shutil, re, subprocess, logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def error_exit(msg, code):
    print("{}: {}".format(sys.argv[0], msg))
    print("Try '{} --help' for more information".format(sys.argv[0]))
    sys.exit(code)

try:
    opts, args = getopt.getopt(sys.argv[1:], "hd", ("help", "debug", "kicad-clean"))
except getopt.GetoptError as err:
    error_exit(str(err), -1)

makefile_debug = False
kicad_clean = False
for o, a in opts:
    if o in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    elif o in ("-d", "--debug"):
        makefile_debug = True
    elif o in ("--kicad-clean"):
        kicad_clean = True

#
# Check if kicad is already running...
#

if not subprocess.call("ps aux | grep kicad | grep -v grep", shell=True):
    logging.warning('If KiCad is already running this will fail')

#
# If requested delete any stale KiCad process locks
#

if kicad_clean and os.path.exists(os.path.expanduser("~/.cache/kicad")):
    shutil.rmtree(os.path.expanduser("~/.cache/kicad"))

#
# Setup the environment stuff
#

if not os.path.exists(os.path.expanduser("~/.config")):
    logging.info("Creating ~/.config")
    os.mkdir(os.path.expanduser("~/.config"))

conf_dirs = os.listdir(os.path.expanduser("~/.config"))

temp_dir = None
if "kicad" in conf_dirs:
    logging.info("Found ~/.config/kicad, need to backup")
    temp_dir = "~/.config/kicad_temp{}".format(max([int(x[10:]) for x in conf_dirs if re.match(r'kicad_temp\d+', x)] + [0]) + 1)
    logging.info("Backing up ~/.config/kicad to {}".format(temp_dir))
    os.rename(os.path.expanduser("~/.config/kicad"), os.path.expanduser(temp_dir))

logging.info("Create ~/.config/kicad")
os.mkdir(os.path.expanduser("~/.config/kicad"))

logging.info("Create blank footprint library table")
with open(os.path.expanduser("~/.config/kicad/fp-lib-table"), "w") as fw:
    fw.write("(fp_lib_table\n)\n")

logging.info("Create blank symbol library table")
with open(os.path.expanduser("~/.config/kicad/sym-lib-table"), "w") as fw:
    fw.write("(sym_lib_table\n)\n")

logging.info("Set initial toolset")
with open(os.path.expanduser("~/.config/kicad/pcbnew"), "w") as fw:
    fw.write("""canvas_type=1
PcbFrameMaximized=1
PcbFramePos_x=-4
PcbFramePos_y=0
PcbFrameSize_x=1928
PcbFrameSize_y=1048""")

logging.info("Turn off menu icons")
with open(os.path.expanduser("~/.config/kicad/kicad_common"), "w") as fw:
    fw.write("UseIconsInMenus=0\n")

script_dirs = os.listdir(os.path.expanduser("~/"))

logging.info("Set PDF as default schematic plot format")
with open(os.path.expanduser("~/.config/kicad/eeschema"), "w") as fw:
    fw.write("PlotFormat=4\n")

temp_script_dir = None
if ".kicad_plugins" in script_dirs:
    logging.info("Found ~/.kicad_plugins, need to backup")
    temp_script_dir = "~/.kicad_plugins_temp{}".format(max([int(x[19:]) for x in script_dirs if re.match(r'.kicad_plugins_temp\d+', x)] + [0]) + 1)
    logging.info("Backing up ~/.kicad_plugins to {}".format(temp_script_dir))
    os.rename(os.path.expanduser("~/.kicad_plugins"), os.path.expanduser(temp_script_dir))

logging.info("Create ~/.kicad_plugins")
os.mkdir(os.path.expanduser("~/.kicad_plugins"))

logging.info("Install the fabnotes export plugin")
shutil.copy(os.path.join(os.path.dirname(__file__), "export_fabnotes_plugin.py"), os.path.expanduser("~/.kicad_plugins/"))

#
# Use makeutils to modify the schematic/PCB replacing wildcards with SVN data
#
# This is done out here so that the recovery step is carried out regardless of whether the main build succeded or not
#
logging.info("Setting the version numbers to match SVN")
subprocess.check_call(["make", "setversion"])

#
# Run the make
#
logging.info("Run the actual make process")
if makefile_debug:
    rv = subprocess.call(["make", "DEBUG=\"--debug\"", "manufacturing"])
else:
    rv = subprocess.call(["make", "manufacturing"])

#
# Restore the version wildcards (essential if this is a working copy)
#
logging.info("Restoring version number wildcards")
subprocess.check_call(["make", "restoreversion"])

#
# Do clean up
#

if temp_script_dir:
    shutil.rmtree(os.path.expanduser("~/.kicad_plugins"))
    logging.info("Restore ~/.kicad_plugins from {}".format(temp_script_dir))
    os.rename(os.path.expanduser(temp_script_dir), os.path.expanduser("~/.kicad_plugins"))

if temp_dir:
    shutil.rmtree(os.path.expanduser("~/.config/kicad"))
    logging.info("Restore ~/.config/kicad from {}".format(temp_dir))
    os.rename(os.path.expanduser(temp_dir), os.path.expanduser("~/.config/kicad"))

#
# Finally exit with the return code of the Makefile to propagate that code back up to the higher layers
#

sys.exit(rv)
