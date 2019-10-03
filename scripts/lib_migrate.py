#!/usr/bin/env python3
"""
NAME
    lib_migrate.py - migrate KiCad schematic from legacy to table library in a more convenient way

SYNOPSIS
    lib_migrate.py [OPTIONS] SCHEMATIC

DESCRIPTION
    Does a slightly smarter remap of schematic symbols to the new table based library format.
    Modifies SCHEMATIC in place so make sure it is checked-in or backed up elsewhere first.  Expects
    to find a project specific schematic library table (sym-lib-table) in the project folder and
    attempts to map all components in the schematic to use these project-local libraries.

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

import re, sys, getopt, string, json

def error_exit(msg, code):
    print("lib_migrate.py: {}".format(msg))
    print("Try 'lib_migrate.py --help' for more information")
    sys.exit(code)

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
    return {k: v}

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ("help"))
except getopt.GetoptError as err:
    error_exit(str(err), -2)

for o, a in opts:
    if o in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

if len(args) < 1:
    error_exit("SCHEMATIC is a required argument", -1)

with open("sym-lib-table", "r") as fr:
    lib_table = sexpr_to_dict(fr.read())["sym_lib_table"]["lib"]

symbols = {}
all_syms = []
for lib in lib_table:
    symbols[lib['name']] = []
    with open(lib['uri'].replace("${KIPRJMOD}", "."), "r") as fr:
        for l in fr:
            m = re.match(r'DEF\s+(\S+).+', l)
            if m:
                symbols[lib['name']].append(m.group(1))
                if m.group(1) in all_syms:
                    print("Found conflict in name {}, second occurrence is in {}".format(m.group(1), lib['name']))
                all_syms.append(m.group(1))
            else:
                m = re.match(r'ALIAS\s+(.+)', l)
                if m:
                    symbols[lib['name']].extend(m.group(1).split())
                    for s in m.group(1).split():
                        if s in all_syms:
                            print("Found conflict in alias {}, second occurrence is in {}".format(s, lib['name']))
                        all_syms.append(s)

with open(args[0], "r") as fr:
    op_lines = []
    for l in fr:
        m = re.match(r'(L\s+)(\S+)(.*)', l)
        if m:
            #print(l, m.groups())
            new_lib = "not found!"
            for lib in symbols:
                if m.group(2) in symbols[lib]:
                    new_lib = "{}:{}".format(lib, m.group(2))
            if new_lib == "not found!":
                print(m.group(2), new_lib)
                op_lines.append(l)
            else:
                # need to use l[m.start(3):] instead of just m.group(3) here because the group can't
                # contain a newline character (re won't match past \n) but otherwise we're loosing
                # whitespace from the input file
                op_lines.append(m.group(1) + new_lib + l[m.start(3):])
        else:
            m = re.match(r'EESchema Schematic File Version (\d+)', l)
            if m:
                op_lines.append(l[:m.start(1)] + "4" + l[m.end(1):])
            else:
                m = re.match(r'LIBS:.*', l)
                if not m:
                    op_lines.append(l)

with open(args[0], "w") as fw:
    fw.write("".join(op_lines))
