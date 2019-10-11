#!/usr/bin/env python3

#   Copyright 2016 Scott Bezek
#   Copyright 2018 Chronos Technology Ltd
#   Copyright 2019 Nathan Dumont
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging, os, subprocess, sys, time, argparse

from export_util import PopenContext, xdotool, wait_for_window, recorded_xvfb

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def pcbnew_plot_fabnotes(output_directory):
    wait_for_window('kicad', 'KiCad.*')

    time.sleep(1)
    xdotool(['search', '--onlyvisible', '--class', 'kicad', 'windowfocus'])
    logger.info('Open the PCB')
    xdotool(['key', 'ctrl+p'])

    wait_for_window('pcbnew', 'Pcbnew.*')
    logger.info('Focus main Pcbnew window')
    xdotool(['search', '--name', 'Pcbnew.*', 'windowfocus'])

    # use the fabnotes plugin to export
    logger.info('Run Tools->External Plugins->Export Fabnotes')
    xdotool(['key', 'alt+t', 'e', 'Down', 'Return'])

    logger.info('Wait before shutdown')
    time.sleep(2)

def export_fabnotes(project_file, output_dir, name_tag, sides, debug):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if debug:
        screencast_output_file = os.path.join(output_dir, 'export_fabnotes_screencast.ogv')
    else:
        screencast_output_file = None

    with recorded_xvfb(screencast_output_file, width=1920, height=1080, colordepth=24):
        with PopenContext(['kicad', project_file], close_fds=True) as pcbnew_proc:
            pcbnew_plot_fabnotes(os.path.abspath(output_dir))
            pcbnew_proc.terminate()

    if sides in ("front", "both"):
        os.rename(os.path.splitext(project_file)[0] + "-TOP_FAB.pdf",
                  os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + "-TOP_FAB.pdf"))
    if sides in ("back", "both"):
        os.rename(os.path.splitext(project_file)[0] + "-BOTTOM_FAB.pdf",
                  os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + "-BOTTOM_FAB.pdf"))
                               
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Command line tool to generate fabrication notes from a KiCad PCBs Fab notes layer.")
    parser.add_argument("profile", metavar="FILE", help="KiCad project file (*.pro)")
    parser.add_argument("--name-tag", help="An arbitrary tag to add after the project name in the output file", default="")
    parser.add_argument("--sides", choices=["both", "front", "back"], default="both", help="Specify which sides to plot")
    parser.add_argument("--debug", action="store_true", help="Stores a video of the automated GUI operations")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity.  May be entered multiple times.")
    parser.add_argument("--output-dir", "-d", help="The output directory to store the result in", default="")
    args = parser.parse_args()

    if args.verbose == 0:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    logger.debug("Parsed args {}".format(args))

    export_fabnotes(args.profile, args.output_dir, args.name_tag, args.sides, args.debug)
