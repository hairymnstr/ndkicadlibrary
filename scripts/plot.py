#!/usr/bin/env python3
import argparse
import sys
import os
import logging
from pcbnew import *

"""drill.py
Adam Wolf, wayne@wayneandlayne.com
Wayne and Layne, LLC
May 5th, 2013

PRERELEASE

When completed, this script will use the Kicad scripting interface to generate 
plot/Gerber files.  If you do everything exactly like it expects, it will 
generate Gerber files.  Not all the options work.  Not much has been tested.

Based partially on printo.py from Lorenzo Marcantonio.

Updated 2018,2019
Nathan Dumont
Chronos Technology Ltd

Tweaked to work with KiCad 5.0, then 5.2.
Added more internal layers.
Doesn't work with page border because the page border is contained in the KiCad
*.pro file which isn't loaded by pcbnew.  No way around this at the moment, just don't pass
--plot-sheet-reference or it will segfault
"""

#TODO
# add rest of inner layers
# test if the PCB edges layer ends up being PCB_Edges.outline
# test "not in this directory support" (BE CAREFUL THIS HAS CRASHED MY STUFF)

# show a special warning if pcbnew import fails
# add other outputters

logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger()

plot_formats = {"gerber": PLOT_FORMAT_GERBER, "pdf": PLOT_FORMAT_PDF}
    
layers = {
        "F.Cu": (F_Cu, "Front Copper", "TOP_ETCH"),
        "Inner1.Cu": (In1_Cu, "Inner Copper #1", "INNER1"), 
        "Inner2.Cu": (In2_Cu, "Inner Copper #2", "INNER2"),
        "Inner3.Cu": (In3_Cu, "Inner Copper #3", "INNER3"),
        "Inner4.Cu": (In4_Cu, "Inner Copper #4", "INNER4"),
        "Inner5.Cu": (In5_Cu, "Inner Copper #5", "INNER5"),
        "Inner6.Cu": (In6_Cu, "Inner Copper #6", "INNER6"),
        "B.Cu": (B_Cu, "Back Copper", "BOTTOM_ETCH"),
        "F.Adhes": (F_Adhes, "Front Adhesive", "TOP_ADHESIVE"),
        "B.Adhes": (B_Adhes, "Back Adhesive", "BOTTOM_ADHESIVE"),
        "F.Paste": (F_Paste, "Front Solderpaste", "TOP_PASTE"),
        "B.Paste": (B_Paste, "Back Solderpaste", "BOTTOM_PASTE"),
        "F.SilkS": (F_SilkS, "Front Silkscreen", "TOP_SILK"),
        "B.SilkS": (B_SilkS, "Back Silkscreen", "BOTTOM_SILK"),
        "F.Mask": (F_Mask, "Front Soldermask", "TOP_MASK"),
        "B.Mask": (B_Mask, "Back Soldermask", "BOTTOM_MASK"),
        "Dwgs.User": (Dwgs_User, "Drawings", "DRAWINGS"),
        "Cmts.User": (Cmts_User, "Comments", "COMMENTS"),
        "Eco1.User": (Eco1_User, "ECO 1", "ECO1"),
        "Eco2.User": (Eco2_User, "ECO 2", "ECO2"),
        "Edge.Cuts": (Edge_Cuts, "Edges", "BOARD_EDGE"),
        "F.Fab": (F_Fab, "Front Fabrication", "TOP_FAB"),
        "B.Fab": (B_Fab, "Back Fabrication", "BOTTOM_FAB"),
        }

def main():

    cli_layer_list = sorted(layers.keys())
    cli_layer_list.insert(0, "all")
    parser = argparse.ArgumentParser(description="Eventually, this will be a slick way to generate plot files for Kicad from the command line.  Currently, it's untested and a proof-of-concept only, but it generates Gerbers.  Do not use this, really, for anything.  Do not use with files that aren't backed up.")
    parser.add_argument("--format", choices=plot_formats.keys(), help="Selects the plot format.  Only a single format per run is supported.  Only gerber is currently supported.", default='gerber')
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity. May be entered multiple times.")
    parser.add_argument("--exclude-edge-from-other-layers", action="store_true", help="Exclude PCB edge layer from other layers.")
    parser.add_argument("--plot-sheet-reference", action="store_true", help="Plot sheet reference on all layers.")
    parser.add_argument("pcbfile", metavar="FILE", help="Kicad board file (.kicad_pcb or .brd)")
    parser.add_argument("--plot-in-silk", choices=["pads", "module-value", "module-reference", "invisible-texts"], action='append', help="Plot pads on silkscreen.")
    parser.add_argument("--output-dir", "-d", help="The output directory, relative to the directory the board file is in.  Defaults to the same directory the board file is in.", default="")
    parser.add_argument("--layers", choices=cli_layer_list, action='append', help="Select layers to plot.")
    parser.add_argument("--mirror", action="store_true", help="Mirror the layer in plot (only on PDF)")
    parser.add_argument("--name-tag", help="An arbitrary tag to add between project name and layer name e.g. value tag will produce proj-tag-outline.gm1", default=None)
    #parser.add_argument("--do-not-tent-vias", action="store_true", help="Do not tent vias.")
    #line_width_group = parser.add_mutually_exclusive_group()
    #line_width_group.add_argument("--default-line-width-mils", help="Default line width in inches.  Defaults to Kicad's default (currently 6 IU)")
    #line_width_group.add_argument("--default-line-width-mm", help="Default line width in millimeters.")

    gerber_group = parser.add_argument_group('gerber options')
    gerber_group.add_argument("--use-auxiliary-axis-as-origin", action="store_true")
    gerber_group.add_argument("--subtract-soldermask-from-silk", action="store_true")

    args = parser.parse_args()
    
    if args.verbose == 0:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    elif args.verbose > 1:
        logger.setLevel(logging.DEBUG)
    #logger.info("sample info message")
    #logger.debug("sample debug message")
    logger.debug("Parsed args: %s" % args)

    if not args.plot_in_silk:
        args.plot_in_silk = []
    if not args.layers:
        args.layers = ["all"]

    if "all" in args.layers:
        args.layers = layers.keys()

    try:
        logger.debug("Loading board file %s" % args.pcbfile)
        pcb = LoadBoard(args.pcbfile)
        logger.debug("Successfully loaded board file.")
    except IOError:
        logger.error("Unable to load board file %s" % args.pcbfile)
        sys.exit(1)

    pctl = PLOT_CONTROLLER(pcb)

    popt = pctl.GetPlotOptions()

    if args.format == "gerber":
        popt.SetUseGerberProtelExtensions(True)
        popt.SetSubtractMaskFromSilk(args.subtract_soldermask_from_silk)
        popt.SetUseAuxOrigin(args.use_auxiliary_axis_as_origin)
    else:
        popt.SetMirror(bool(args.mirror))

    popt.SetPlotPadsOnSilkLayer("pads" in args.plot_in_silk)
    popt.SetPlotValue("module-value" in args.plot_in_silk)
    popt.SetPlotReference("module-reference" in args.plot_in_silk)
    #popt.SetPlotOtherText("other-module-texts" in args.plot_in_silk)
    popt.SetPlotInvisibleText("invisible-texts" in args.plot_in_silk)

    popt.SetExcludeEdgeLayer(args.exclude_edge_from_other_layers)
    popt.SetPlotFrameRef(bool(args.plot_sheet_reference))
    popt.SetOutputDirectory(args.output_dir) 

    # Anyway, remember that paper size it taken from the board and for all
    # plot purposes DXF and Gerber files have no paper size (so no
    # autoscaling for them). On the other hand DXF and Gerber *can* use the
    # auxiliary axis as origin.
    popt.SetLineWidth(FromMM(0.35))
    
    # PLEASE NOTE this is mostly equivalent to the default plot dialog loop!
    for layer_key in args.layers:
        layer_symbol, sheet_desc, layer_name = layers[layer_key]
        pctl.SetLayer(layer_symbol)
        fname = layer_name.replace(".", "_")
        if args.name_tag:
            fname = args.name_tag + "-" + fname
        pctl.OpenPlotfile(fname,
            plot_formats[args.format],
            sheet_desc)
        pctl.PlotLayer()

if __name__ == "__main__":
    main()
