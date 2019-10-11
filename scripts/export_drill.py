#!/usr/bin/env python3

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

import logging, os, sys, time, argparse
from pcbnew import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Command line drill file generation tool for KiCad v5.  Generates the standard drill files from a board file without having to launch the GUI.")
parser.add_argument("pcbfile", metavar="FILE", help="KiCad board file (.kicad_pcb)")
parser.add_argument("--name-tag", help="An arbitrary tag to add after the project name in the output file", default="")
parser.add_argument("--use-auxiliary-axis-as-origin", action="store_true", help="Use the auxiliary axis origin instead of global 0,0")
parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity.  May be entered multiple times.")
parser.add_argument("--output-dir", "-d", help="The output directory, relative to the deirectory the board file is in.  Defaults to the same directory the board file is in.", default="")
args = parser.parse_args()

if args.verbose == 0:
    logger.setLevel(logging.WARNING)
elif args.verbose == 1:
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.DEBUG)

logger.debug("Parsed args {}".format(args))

try:
    logger.debug("Loading board file {}".format(args.pcbfile))
    pcb = LoadBoard(args.pcbfile)
    logger.debug("Successfully loaded board file.")
except IOError:
    logger.error("Unable to load board file {}".format(args.pcbfile))
    sys.exit(1)

xc = EXCELLON_WRITER(pcb)
xc.SetFormat(True)  # use metric
if args.use_auxiliary_axis_as_origin:
    xc.SetOptions(False, False, pcb.GetAuxOrigin(), False)  # mirror, minimal_header, origin, merge NPTH & PTH
xc.SetMapFileFormat(4)  # plot PDF map file
xc.CreateDrillandMapFilesSet(args.output_dir, True, True)    # output directory, gen drill, gen map

file_name_base = os.path.splitext(os.path.basename(args.pcbfile))[0]
output_location = args.output_dir

kicad_files = ["-NPTH.drl", "-NPTH-drl_map.pdf", "-PTH.drl", "-PTH-drl_map.pdf"]
ctl_files = ["-DRILL_NPTH.txt", "-DRILL_NPTH_MAP.pdf", "-DRILL_PTH.txt", "-DRILL_PTH_MAP.pdf"]

for i in range(len(kicad_files)):
    os.rename(os.path.join(output_location, file_name_base + kicad_files[i]),
              os.path.join(output_location, file_name_base + args.name_tag + ctl_files[i]))
