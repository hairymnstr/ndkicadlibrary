#!/usr/bin/env python3

"""
NAME
    export_fabnotes_plugin.py - a KiCad plugin to plot the two fabnotes layers
    
DESCRIPTION
    The fabnotes layers in KiCad are typically exported as PDF to assist in manufacturing with
    dimensions, notes on layer stack up etc.  Normally these PDFs should include the page border
    however, because the page border is handled by the KiCad project, not the KiCad_PCB file you
    can't invoke the CLI scripting interface and produce PDF output with the page border (if you
    try it will segfault).  Using GUI automation to configure the plot dialog is extremely difficult
    due to the complexity of the dialog, so a plugin script which automates plotting from within
    PCBNew (launched from KiCad project view) is relatively easy to trigger via GUI automation and
    doesn't segfault like a script launched outside KiCad.
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

import sys
import os
import logging
import pcbnew
    
layers = {
        "F.Fab": (pcbnew.F_Fab, "Front Fabrication", "TOP_FAB"),
        "B.Fab": (pcbnew.B_Fab, "Back Fabrication", "BOTTOM_FAB"),
        }

class ExportFabnotePlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Automatic export of fabnotes"
        self.category = "Export tools"
        self.description = "Automatic export of fabnotes as PDF"

    def Run(self):
        args_format = pcbnew.PLOT_FORMAT_PDF
        args_output_dir = ""

        pcb = pcbnew.GetBoard()

        pctl = pcbnew.PLOT_CONTROLLER(pcb)

        popt = pctl.GetPlotOptions()

        popt.SetMirror(False)

        popt.SetPlotPadsOnSilkLayer(False)
        popt.SetPlotValue(True)
        popt.SetPlotReference(True)
        popt.SetPlotInvisibleText(False)

        popt.SetExcludeEdgeLayer(False)
        popt.SetPlotFrameRef(True)
        popt.SetOutputDirectory(args_output_dir) 

        # Anyway, remember that paper size it taken from the board and for all
        # plot purposes DXF and Gerber files have no paper size (so no
        # autoscaling for them). On the other hand DXF and Gerber *can* use the
        # auxiliary axis as origin.
        popt.SetLineWidth(pcbnew.FromMM(0.35))
        
        layer_symbol, sheet_desc, layer_name = layers["F.Fab"]
        pctl.SetLayer(layer_symbol)
        fname = layer_name.replace(".", "_")
        pctl.OpenPlotfile(fname, args_format, sheet_desc)
        pctl.PlotLayer()

        popt.SetMirror(True)
        layer_symbol, sheet_desc, layer_name = layers["B.Fab"]
        pctl.SetLayer(layer_symbol)
        fname = layer_name.replace(".", "_")
        pctl.OpenPlotfile(fname, args_format, sheet_desc)
        pctl.PlotLayer()

ExportFabnotePlugin().register()
