#!/usr/bin/env python3

#   Copyright 2016 Scott Bezek
#   Modified heavily by Nathan Dumont (Chronos Technology Ltd) 2019 to support KiCad v5
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

import logging
import os
import subprocess
import sys
import time
import argparse

from export_util import (
    PopenContext,
    plottable_project,
    versioned_schematic,
    xdotool,
    wait_for_window,
    recorded_xvfb,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def eeschema_plot_schematic():
    wait_for_window('kicad', 'KiCad.*')

    time.sleep(10)   # window exists but isn't ready to receive focus until the library tables have been loaded
    xdotool(['search', '--onlyvisible', '--class', 'kicad', 'windowfocus'])
    logger.info('Open the schematic')
    xdotool(['key', 'ctrl+e'])

    wait_for_window('eeschema', 'Eeschema.*')

    logger.info('Focus main eeschema window')
    xdotool(['search', '--name', 'Eeschema.*', 'windowfocus'])

    logger.info('Open File->Plot->Plot')
    xdotool(['key', 'alt+f'])
    xdotool(['key', 'l'])

    wait_for_window('plot', 'Plot')
    xdotool(['search', '--name', 'Plot', 'windowfocus'])

    logger.info('Plot using default settings')
    xdotool(['key', 'Tab', 'Tab', 'Return'])

    logger.info('Wait before shutdown')
    time.sleep(2)
    
    logger.info('Close KiCad')
    xdotool(['key', 'Escape'])
    
    xdotool(['search', '--name', 'Eeschema.*', 'windowfocus'])
    xdotool(['key', 'ctrl+q'])

    xdotool(['search', '--onlyvisible', '--class', 'kicad', 'windowfocus'])
    xdotool(['key', 'ctrl+q'])

def export_schematic(project_file, output_dir, name_tag, debug):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if debug:
        screencast_output_file = os.path.join(output_dir, 'export_schematic_screencast.ogv')
    else:
        screencast_output_file = None

    with recorded_xvfb(screencast_output_file, width=1920, height=1080, colordepth=24):
        with plottable_project(project_file, os.path.abspath(output_dir)):
            with PopenContext(['kicad', project_file], close_fds=True) as eeschema_proc:
                eeschema_plot_schematic()
                eeschema_proc.terminate()

    os.rename(os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + ".pdf"),
              os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + "-SCHEMATIC.pdf"))
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Command line tool to generate a PDF of a schematic from a KiCad project")
    parser.add_argument('profile', metavar='FILE', help='KiCad project file (*.pro)')
    parser.add_argument('--name-tag', help='An arbitrary tag to add after the project name in the output file', default='')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity.  May be entered multiple times.')
    parser.add_argument('--output-dir', '-d', help='The output directory.  Defaults to the directory the script is run from.', default='')
    parser.add_argument('--debug', action='store_true', help='Record a video of the automated GUI opreations')
    args = parser.parse_args()

    if args.verbose == 0:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    logger.debug('Parsed args {}'.format(args))

    export_schematic(args.profile, args.output_dir, args.name_tag, args.debug)
