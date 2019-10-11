#!/usr/bin/env python

"""
NAME
    check_pos_files.py - Verifies all SMT parts are in pick and place data

SYNOPSIS
    check_pos_files.py [OPTIONS] <GERBER FOLDER>

DESCRIPTION
    Reads the BOM and the top/bottom .pos files to verify that all SMT parts (unless
    they are specified as No Fit) are present in the .pos files somewhere.  This can
    pick up errors where SMT parts are not set as SMT in the library, or where parts
    that are meant to be No Fit have not been set to Virtual.

    -h, --help
        Print this help and exit
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

import os, sys, getopt, csv

def error_exit(msg, code):
    print("{}: {}".format(sys.argv[0], msg))
    print("Try '{} --help' for more information".format(sys.argv[0]))
    sys.exit(code)

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ("help"))
except getopt.GetoptError as err:
    error_exit(str(err), -2)

for o, a in opts:
    if o in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

if len(args) != 1:
    error_exit("The directory containing the manufacturing files must be passed", -2)

if not os.path.isdir(args[0]):
    error_exit("The path passed is not a directory", -2)

files = os.listdir(args[0])
posfiles = []
bomfile = None
for f in files:
    if f.endswith("-BOM.csv"):
        bomfile = os.path.join(args[0], f)
    elif f.endswith(".pos"):
        posfiles.append(os.path.join(args[0], f))

if not bomfile:
    error_exit("Could not find the BOM in the output directory", -2)

if len(posfiles) < 1:
    error_exit("Could not find any .pos files in the output directory", -2)

smt_parts = []
with open(bomfile, "r") as fr:
    csvr = csv.reader(fr)
    for row in csvr:
        try:
            id = int(row[0])
        except:
            continue
        for ref in row[1].split(","):
            if row[5] not in ("SMT", "THT", "Virtual"):
                raise Exception("Your BOM file does not have complete footprint type information")
            if row[5] == "SMT":
                smt_parts.append(ref)

smt_parts.sort()

pos_parts = []
for pos_file in posfiles:
    with open(pos_file, "r") as fr:
        for line in fr:
            if line.startswith("#"):
                continue
            pos_parts.append(line.split()[0])

pos_parts.sort()

if smt_parts == pos_parts:
    print("SUCCESS")
    sys.exit(0)

print("The following references should not be in pick and place files, but are:")
print("\n".join(map(lambda x: "  {}".format(x), list(set(pos_parts) - set(smt_parts)))))
print("")
print("The following references should be in the pick and place files, but are missing:")
print("\n".join(map(lambda x: "  {}".format(x), list(set(smt_parts) - set(pos_parts)))))
print("")
print("FAILED")
sys.exit(1)
