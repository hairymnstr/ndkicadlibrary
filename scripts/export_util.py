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

import logging
import os
import subprocess
import sys
import tempfile
import time
import string

from contextlib import contextmanager

electronics_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(electronics_root)
sys.path.append(repo_root)

from xvfbwrapper import Xvfb

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PopenContext(subprocess.Popen):
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()
        if self.stdin:
            self.stdin.close()
        if type:
            self.terminate()
        # Wait for the process to terminate, to avoid zombies.
        self.wait()

def xdotool(command):
    return subprocess.check_output(['xdotool'] + command)

def wait_for_window(name, window_regex, timeout=10):
    DELAY = 0.5
    logger.info('Waiting for %s window...', name)
    for i in range(int(timeout/DELAY)):
        try:
            xdotool(['search', '--name', window_regex])
            logger.info('Found %s window', name)
            return
        except subprocess.CalledProcessError:
            pass
        time.sleep(DELAY)
    raise RuntimeError('Timed out waiting for %s window' % name)

@contextmanager
def recorded_xvfb(video_filename, **xvfb_args):
    with Xvfb(**xvfb_args):
        if video_filename:
            with PopenContext([
                    'recordmydesktop',
                    '--no-sound',
                    '--no-frame',
                    '--on-the-fly-encoding',
                    '-o', video_filename], close_fds=True) as screencast_proc: 
                yield
                screencast_proc.terminate()
        else:
            yield

def _get_versioned_contents(filename):
    with open(filename, 'rb') as schematic:
        original_contents = schematic.read()
        return original_contents, original_contents \
            .replace('Date ""', 'Date "%s"' % "TODO") \
            .replace('Rev ""', 'Rev "%s"' % "TODO")

@contextmanager
def versioned_schematic(filename):
    original_contents, versioned_contents = _get_versioned_contents(filename)
    with open(filename, 'wb') as temp_schematic:
        logger.debug('Writing to %s', filename)
        temp_schematic.write(versioned_contents)
    try:
        yield
    finally:
        with open(filename, 'wb') as temp_schematic:
            logger.debug('Restoring %s', filename)
            temp_schematic.write(original_contents)

def _get_plottable_project(filename, plot_dir):
    with open(filename, 'r') as project:
        original_contents = project.read()
        new_contents = original_contents.splitlines()
        for i in range(len(new_contents)):
            if new_contents[i].split("=")[0] == "PlotDirectoryName":
                new_contents[i] = "PlotDirectoryName=" + plot_dir
        return original_contents, "\n".join(new_contents)

@contextmanager
def plottable_project(filename, plot_dir):
    original_contents, versioned_contents = _get_plottable_project(filename, plot_dir)
    with open(filename, 'w') as temp_project:
        logger.debug('Writing to %s', filename)
        temp_project.write(versioned_contents)
    try:
        yield
    finally:
        with open(filename, 'w') as temp_project:
            logger.debug('Restoring %s', filename)
            temp_project.write(original_contents)

def __parse_sexpr(s):
    assert s[0] == "("

    s = s[1:]
    k = ""
    while s[0] in string.ascii_letters + string.digits + "-_":
        k += s[0]
        s = s[1:]

    while s[0] in string.whitespace:
        s = s[1:]

    if s[0] == "(":
        v = {}
        while s[0] == "(":
            sk, sv, s = __parse_sexpr(s)
            if sk in v:
                if type(v[sk]) is list:
                    v[sk].append(sv)
                else:
                    v[sk] = [v[sk], sv]
            else:
                v[sk] = sv
    elif s[0] == "\"":
        v = ""
        s = s[1:]
        while s[0] != "\"":
            if s[0] == "\\":
                v += s[1]
                s = s[2:]
            else:
                v += s[0]
                s = s[1:]
        s = s[1:]
    else:
        v = ""
        while s[0] != ")":
            v += s[0]
            s = s[1:]
        v = v.strip()
    while s[0] in string.whitespace:
        s = s[1:]
    if s[0] != ")":
        print("k: {!r}, v: {!r}, s: {!r}".format(k,v,s))
    assert s[0] == ")"
    return k, v, s[1:].strip()

def sexpr_to_dict(s, fail_if_remainder=False):
    k, v, s = __parse_sexpr(s)
    if s and fail_if_remainder:
        raise Exception("Left over content after parsing s-expression")
    return {k: v}, s

def sexpr_needs_quote(v):
    if v == "":
        return True
    for c in v:
        if c not in string.letters + string.digits + "_.":
            return True
    return False

def sexpr_escaped(v):
    s = ""
    for c in v:
        if c in "\\\"":
            s += "\\" + c
        else:
            s += c
    return s

def __unparse_sexpr(d):
    s_lines = []
    for k, v in d.items():
        s = "("
        s += k
        if isinstance(v, dict):
            s_lines.append([s, 1])
            s_lines.extend(__unparse_sexpr(v))
            s_lines[-1][0] += ")"
            s_lines[-1][1] -= 1
        else:
            s += " "
            if sexpr_needs_quote(v):
                s += '"' + sexpr_escaped(v) + '"'
            else:
                s += v
            s += ")"
            s_lines.append([s, 0])
    return s_lines
    
def dict_to_sexpr(d, initial_indent):
    s = ""
    for line in __unparse_sexpr(d):
        s += "  " * initial_indent + line[0] + "\n"
        initial_indent += line[1]
    return s
    
def _get_plottable_contents(filename, plot_params):
    with open(filename, 'rb') as fr:
        original_contents = fr.read()
    plot_attrs, more = sexpr_to_dict(original_contents[original_contents.find("(pcbplotparams"):])
    plottable_contents = original_contents[:original_contents.find("(pcbplotparams")] + \
                            dict_to_sexpr(plot_params, 2).strip() + more
    return original_contents, plottable_contents
    
@contextmanager
def plottable_pcb(filename, plot_params):
    original_contents, plottable_contents = _get_plottable_contents(filename, plot_params)
    with open(filename, 'w') as temp_pcb:
        logger.debug('Writing to {}'.format(filename))
        temp_pcb.write(plottable_contents)
    try:
        yield
    finally:
        with open(filename, 'w') as temp_pcb:
            logger.debug('Restoring {}'.format(filename))
            temp_pcb.write(original_contents)
