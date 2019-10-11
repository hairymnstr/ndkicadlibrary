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

def pcbnew_pos_files(output_dir):
    wait_for_window('kicad', 'KiCad.*')

    time.sleep(1)
    xdotool(['search', '--onlyvisible', '--class', 'kicad', 'windowfocus'])
    logger.info('Open the PCB')
    xdotool(['key', 'ctrl+p'])

    wait_for_window('pcbnew', 'Pcbnew.*')

    logger.info('Focus main pcbnew window')
    xdotool(['search', '--name', 'Pcbnew.*', 'windowfocus'])

    logger.info('Open File->Fabrication outputs->Pos file')
    xdotool(['key', 'alt+f', 'f', 'p'])

    wait_for_window('position', 'Generate Footprint Position.*')
    xdotool(['search', '--name', 'Generate Footprint Position.*', 'windowfocus'])

    logger.info('Set output file to {}'.format(output_dir))
    xdotool(['type', output_dir])
    
    logger.info('Generate output')
    xdotool(['key', 'Return'])

    logger.info('Wait before shutdown')
    time.sleep(2)

def export_pos_files(project_file, output_dir, name_tag, debug):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if debug:
        screencast_output_file = os.path.join(output_dir, 'export_pos_screencast.ogv')
    else:
        screencast_output_file = None

    with recorded_xvfb(screencast_output_file, width=1920, height=1080, colordepth=24):
        new_env = os.environ.copy()
        new_env['GTK2_RC_FILES'] = '/usr/share/themes/Raleigh/gtk-2.0/gtkrc'
        with PopenContext(['kicad', project_file], close_fds=True, env=new_env) as kicad_proc:
            pcbnew_pos_files(os.path.abspath(output_dir))
            kicad_proc.terminate()

    os.rename(os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + "-top.pos"),
              os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + "-TOP.pos"))
    os.rename(os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + "-bottom.pos"),
              os.path.join(output_dir, os.path.splitext(os.path.basename(project_file))[0] + name_tag + "-BOTTOM.pos"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool to generate *.pos pick-and-place files from a KiCad project")
    parser.add_argument("profile", metavar="FILE", help="KiCad Project file (*.pro)")
    parser.add_argument("--output-dir", "-d", help="The output directory", default="")
    parser.add_argument("--name-tag", help="An arbitrary tag to add after the project name in the output file", default="")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity. May be entered multiple times.")
    parser.add_argument("--debug", action="store_true", help="Record a video of the autmoate GUI operations")
    args = parser.parse_args()
    
    if args.verbose == 0:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    logger.debug("Parsed args {}".format(args))

    export_pos_files(args.profile, args.output_dir, args.name_tag, args.debug)
