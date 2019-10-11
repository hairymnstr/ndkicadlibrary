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

import logging, os, subprocess, sys, time, shutil, argparse
from export_util import PopenContext, versioned_schematic, xdotool, wait_for_window, recorded_xvfb

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def eeschema_generate_bom(output_directory):
    wait_for_window('kicad', 'KiCad.*')

    time.sleep(10)   # window exists but isn't ready to receive focus until the library tables have been loaded
    xdotool(['search', '--onlyvisible', '--class', 'kicad', 'windowfocus'])

    logger.info('Open the schematic')
    xdotool(['key', 'ctrl+e'])

    wait_for_window('eeschema', 'Eeschema.*')
    logger.info('Focus main eeschema window')
    xdotool(['search', '--name', 'Eeschema.*', 'windowfocus'])

    logger.info('Open BOM Window')
    xdotool(['key', 'alt+t', 'm'])

    wait_for_window('bom', 'Bill of Material')
    xdotool(['search', '--name', 'Bill of Material', 'windowfocus'])

    logger.info('Add plugin')
    xdotool(['key', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab'])
    xdotool(['type', 'python3 "%P/library/scripts/bom_generator.py" "%I" "%O"'])
    xdotool(['key', 'Tab', 'Tab', 'Tab', 'Tab', 'Return'])

    logger.info('Wait before shutdown')
    time.sleep(2)

def export_bom(project_file, output_dir, name_tag, debug):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if debug:
        screencast_output_file = os.path.join(output_dir, 'export_bom_screencast.ogv')
    else:
        screencast_output_file = None

    with recorded_xvfb(screencast_output_file, width=1920, height=1080, colordepth=24):
        with PopenContext(['kicad', project_file], close_fds=True) as eeschema_proc:
            eeschema_generate_bom(os.path.abspath(output_dir))
            eeschema_proc.terminate()

    bom_file = os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + "-BOM.csv")
    os.rename(os.path.splitext(project_file)[0] + ".csv", bom_file)

    with open(bom_file, "r") as fr:
        d = fr.read()
    
    d = d.replace("%VER%", name_tag.strip("-"))

    with open(bom_file, "w") as fw:
        fw.write(d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool to generate a CSV BOM file from a KiCad schematic")
    parser.add_argument("profile", metavar="FILE", help="KiCad Project file (*.pro)")
    parser.add_argument("--output-dir", "-d", help="The output directory")
    parser.add_argument("--name-tag", help="An arbitrary tag to add after the project name in the output file", default="")
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

    export_bom(args.profile, args.output_dir, args.name_tag, args.debug)
