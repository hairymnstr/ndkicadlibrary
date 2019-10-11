KiCad Automation Scripts
========================

Most of the scripts in this folder are designed to work together to automate
generation of common manufacturing outputs from KiCad in a scripted fashion.

Outputs include:
* BOM (as csv)
* Fabnotes (as PDF)
* Schematic (as PDF)
* Gerber files
* Drill files
* Pick and place (KiCad pos files)

The scripts support including wild-cards in your PCB/schematic files to add
date and version information centrally in just one Makefile to simplify
keeping version information consistent.

Setup
-----

The scripts work on Ubuntu 18.04, they rely on xvfb to work even on
headless systems (see Automating the automation later on for use in
Docker).  To run the scripts on Ubuntu 18.04 without using Docker later:

    sudo apt install xdotool recordmydesktop xvfb python3-pip
    sudo -H pip3 install xvfbwrapper

Usage
-----

To specify the details of the outputs you need to write a basic Makefile
which calls the various scripts to generate the right number of copper
layers for example.  An example of this Makefile can be found at
<...> copy and modify this to suit your project.

Once the Makefile is created you need to use the make_manufacturing_data.py
script from this folder to wrap the Makefile and set up environment and
return everything after running.

The scripts all expect to be located in PROJECT_DIR/library/scripts/.  By
adding them as an external or submodule you can keep track of the version
of scripts that were used to build the manufacturing files for a given
project.

Automating the automation
-------------------------

These scripts are usable inside a Docker container!

They were originally written to help get PCB designs into a continuous
integration environment.  Under jenkins a job which runs the
make_manufacturing_data.py script inside a Docker container was used.
