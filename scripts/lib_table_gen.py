#!/usr/bin/env python3
"""
NAME
    lib_table_gen.py - generates sym-lib-table and fp-lib-table as project local tables

SYNOPSIS
    lib_table_gen.py [OPTIONS]

DESCRIPTION
    Since KiCad 5.0 it has been possible to store a sym-lib-table and fp-lib-table in the directory
    with the .pro file.  This file defines "project local libraries" rather than global libraries.
    This is often preferable in version control as the libraries can be captured at a specific
    point along with the schematic and PCB layout files in the same source control system.  This
    script just automates the procedure of generating the library tables for the project when
    creating a new project to avoid having to manually add all the libraries to the project via the
    library management dialog.
    
    To use it, simply add your custom libraries (e.g. as a git submodule or svn external) such that
    schematic libraries are in <PROJECT FOLDER>/library/library and PCB footprints are in
    <PROJECT FOLDER>/library/modules then run
    
        ./lib_table_gen
    
    From a console in the <PROJECT FOLDER>.

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
import os, getopt, sys

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ("help"))
except getopt.GetoptError as err:
    print("lib_table_gen: {}".format(str(err)))
    print("Try 'lib_table_gen --help' for more information")
    sys.exit(-2)

for o, a in opts:
    if o in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

libs = [l for l in os.listdir("library/library") if os.path.splitext(l)[1] == ".lib"]
libs.sort()

with open("sym-lib-table", "w") as fw:
    print("(sym_lib_table", file=fw)
    for f in libs:
        print('  (lib (name {})(type Legacy)(uri ${{KIPRJMOD}}/library/library/{})(options "")(descr ""))'.format(os.path.splitext(f)[0], f), file=fw)
    print(")", file=fw)

libs = [l for l in os.listdir("library/modules") if os.path.splitext(l)[1] == ".pretty"]
libs.sort()

with open("fp-lib-table", "w") as fw:
    print("(fp_lib_table", file=fw)
    for f in libs:
        print('  (lib (name {})(type KiCad)(uri ${{KIPRJMOD}}/library/modules/{})(options "")(descr ""))'.format(os.path.splitext(f)[0], f), file=fw)
    print(")", file=fw)
