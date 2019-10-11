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

import logging, os, sys, time, argparse
from export_util import PopenContext, xdotool, wait_for_window, recorded_xvfb

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def pcbnew_gencad(output_filename):
    wait_for_window('kicad', 'KiCad.*')

    time.sleep(1)
    xdotool(['search', '--onlyvisible', '--class', 'kicad', 'windowfocus'])
    logger.info('Open the PCB')
    xdotool(['key', 'ctrl+p'])

    time.sleep(10)
    wait_for_window('pcbnew', 'Pcbnew.*')

    logger.info('Focus main pcbnew window')
    xdotool(['search', '--name', 'Pcbnew.*', 'windowfocus'])

    logger.info('Open File->Export->Gencad')
    xdotool(['key', 'alt+f', 'x', 'g'])

    wait_for_window('gencad', 'Export to GenCAD.*')
    xdotool(['search', '--name', 'Export to GenCAD.*', 'windowfocus'])

    logger.info('Set output file')
    xdotool(['key', 'Tab', 'Tab'])
    xdotool(['type', output_filename])
    
    logger.info('Generate output')
    xdotool(['key', 'Return'])

    logger.info('Wait before shutdown')
    time.sleep(2)

def export_gencad(project_file, output_dir, name_tag, debug):
    output_filename = os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + ".cad")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if debug:
        screencast_output_file = os.path.join(output_dir, 'export_gencad_screencast.ogv')
    else:
        screencast_output_file = None

    with recorded_xvfb(screencast_output_file, width=1920, height=1080, colordepth=24):
        with PopenContext(['kicad', project_file], close_fds=True) as kicad_proc:
            pcbnew_gencad(os.path.abspath(output_filename))
            kicad_proc.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool to generate a GenCAD file from a KiCad project")
    parser.add_argument("profile", metavar="FILE", help="KiCad Project file (*.pro)")
    parser.add_argument("--output-dir", "-d", help="The output directory", default="")
    parser.add_argument("--name-tag", help="An arbitrary tag to add after the projcet name in the output file", default="")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity.  May be entered multiple times.")
    parser.add_argument("--debug", action="store_true", help="Record a video of the automated GUI operations")
    args = parser.parse_args()

    if args.verbose == 0:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    logger.debug("Parsed args {}".format(args))

    export_gencad(args.profile, args.output_dir, args.name_tag, args.debug)
