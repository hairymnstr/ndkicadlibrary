#!/usr/bin/env python3

"""
KiCAD XML to CSV BOM processing script

USAGE
    python3 bom_generator.py INPUT.xml OUTPUT

    Or from within KiCad:
    
    python3 "%P/library/scripts/bom_generator.py" "%I" "%O"

DESCRIPTION

This script will read a KiCad BOM XML file and convert it to a grouped CSV suitable for most
assembly services.  It uses the custom fields of components to store manufacturer and ordering
information within the schematic itself and thus avoid manually editing the BOM after board changes.

It also provides a column indicating whether components are SMD, Through-Hole or Virtual (i.e.
no-fit or purely mechanical features) which can be used to cross check the *.pos files later on.

Parts are grouped based on their value, Part number and whether or not they are a "No Fit".  So
if you have 3 1M resistors with the same Part number but one is "No Fit" two CSV lines will be
produced, one with both the fitted references and one with the "No Fit" part.

CUSTOM FIELDS

These are the custom fields that are handled, note the names are case-sensitive.

Part number
    A text string which can uniquely identify the part to be used for this ref.  Typically this
    should take the form "Manufacturer part-number" e.g. "ST STM32F103RBT6".  It should contain all
    speed grade/package format/temperature range values so as to indicate a specific variant of the
    part.  "STM32F103" is not sufficient to identify the right part.
Supplier
    Optionally specifies a distributor or OEM supplier from which the part may be sourced.  If you
    leave purchasing up to your CEM this may not be necessary.  This should just be the supplier
    name e.g. "DigiKey" or "Farnell"
Order code
    The supplier's order code for the part specified.  Relates to the Supplier field referenced
    above.
Alternative part
    A duplicate of "Part number" in content and format but allows for second-source to be included
    even if it is a different part number (e.g. SN74HC00 vs. MM74HC00)
Alternative supplier
    Can be used to store either another supplier (e.g. if the "Part number" is available from
    DigiKey and Farnell) or may have the same supplier but the order code will reference a different
    part number.  Always used as a pair with Alternative order code.
Alternative order code
    The order code part of the alternative supplier or part information.
No Fit
    (Note the case of the field name).  Used to indicate that a footprint is not populated at
    manufacturing.  By convention the content of this field should also be the words "No Fit".  Its
    presence is all that is checked by this script, content is ignored but if you make it visible
    then you will see the "No Fit" message in the schematic.  Note this field also implies the
    "Is Virtual" field (see below).
Is SMT
    Informs the pick and place file checker that this part is intended to be fitted by a pick and
    place machine.  If the library name the component is from contains "SMT" this field is implied
    but may be overridden.  The content of the field is ignored normally I add "True".  Can't
    override the "Is Virtual" field either explicit or implied (by "No Fit").
Is THT
    Informs the pick and place file checker this part is intended to be fitted manually.  See Is SMT
    above.  Whichever of these fields is last will be the one that "sticks".  Can't override the
    "Is Virtual" field either explicit or implied (by "No Fit").
Is Virtual
    Informs the pick and place file checker this schematic symbold doesn't have a part to fit.
    Useful for mounting holes, fiducials or other non-component features.  Don't use this for
    unpopulated footprints, use "No Fit" above.
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

import xml.parsers.expat, sys, os, time

# defines all comparison operations relative to __lt__ so classes only need to provide the __lt__
# definition to be fully comparable.
class Comparable:
    def __eq__(self, other):
        return not self<other and not other<self
    def __ne__(self, other):
        return not self==other
    def __gt__(self, other):
        return other<self
    def __ge__(self, other):
        return not self<other
    def __le__(self, other):
        return not other<self

class entity(Comparable):
    ref = ""
    package = ""
    value = ""
    fp_type = "unknown"
    mfpn = ""
    supplier = ""
    order_code = ""
    mfpn2 = ""
    supplier2 = ""
    order_code2 = ""
    nofit = False
    
    def __init__(self, ref):
        self.ref = ref
        self._refkey = "%s%06d" % (ref.strip("0123456789"), int(ref.strip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
    
    def __setitem__(self, idx, val):
        if idx == "Part number":
            self.mfpn = val
        elif idx == "Supplier":
            self.supplier = val
        elif idx == "Order code":
            self.order_code = val
        elif idx == "Alternative part":
            self.mfpn2 = val
        elif idx == "Alternative supplier":
            self.supplier2 = val
        elif idx == "Alternative order code":
            self.order_code2 = val
        elif idx == "No Fit":
            self.nofit = True
            self.fp_type = "Virtual"
        elif idx == "Is SMT":
            if self.fp_type != "Virtual":
                self.fp_type = "SMT"
        elif idx == "Is Virtual":
            self.fp_type = "Virtual"
        elif idx == "Is THT":
            if self.fp_type != "Virtual":
                self.fp_type = "THT"

    def __lt__(self, other):
        if not isinstance(other, entity):
            raise TypeError
        
        return self._refkey < other._refkey
    
    def get_nofit(self):
        if self.nofit:
            return "No Fit"
        return ""

class BOMLine(Comparable):
    def __init__(self, component):
        self.package = component.package
        self.value = component.value
        self.fp_type = component.fp_type
        self.mfpn = component.mfpn
        self.supplier = component.supplier
        self.order_code = component.order_code
        self.mfpn2 = component.mfpn2
        self.supplier2 = component.supplier2
        self.order_code2 = component.order_code2
        self.nofit = component.nofit
        self.components = [component]
        
    def add_component(self, component):
        self.components.append(component)
        self.components.sort()
        
    def __getitem__(self, idx):
        if idx == "Designator":
            return "\"" + ",".join(map(lambda x: x.ref, self.components)) + "\""
        elif idx == "Package":
            return self.package.split(":")[1]
        elif idx == "Quantity":
            return str(len(self.components))
        elif idx == "Value":
            val = "\"" + self.value + "\""
            for i in range(len(self.components)):
                if self.components[i].value != self.value:
                    val = "\"" + ",".join(map(lambda x: x.value, self.components)) + "\""
                    break
            return val
        elif idx == "Type":
            return self.fp_type
        elif idx == "Part number":
            return "\"" + self.mfpn + "\""
        elif idx == "Supplier":
            return self.supplier
        elif idx == "Order code":
            return self.order_code
        elif idx == "Alternative part":
            return self.mfpn2
        elif idx == "Alternative supplier":
            return self.supplier2
        elif idx == "Alternative order code":
            return self.order_code2
        elif idx == "No Fit":
            return self.components[0].get_nofit()
        
    def __lt__(self, other):
        if not isinstance(other, BOMLine):
            raise TypeError
        
        return self.components[0] < other.components[0]

def find_similar(lines, component):
    for i in range(len(lines)):
        if ((lines[i].supplier == component.supplier) and 
            (component.supplier != "") and 
            (lines[i].order_code == component.order_code) and
            (component.order_code != "") and
            (component.nofit == lines[i].nofit)):
            return i
        if (lines[i].package == component.package) and (lines[i].value == component.value) and (lines[i].nofit == component.nofit) and (lines[i].mfpn == component.mfpn):
            return i
    return -1

class KiXMLParser:
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        
        self.parser.StartElementHandler = self._start_element
        self.parser.EndElementHandler = self._end_element
        self.parser.CharacterDataHandler = self._char_data
        
    def convert(self, xml_data):
        self.in_component = None
        self.components = []
        self.char_buffer = ""
        self.parser.Parse(xml_data)
        
        lines = []
        for c in self.components:
            line_no = find_similar(lines, c)
            if line_no == -1:
                lines.append(BOMLine(c))
            else:
                lines[line_no].add_component(c)
        
        lines.sort()
        alternatives = bool(sum(map(lambda x: len(x['Alternative part']) + len(x['Alternative supplier']) + len(x['Alternative order code']), lines)))
        
        if alternatives:
            csv = "Id,Designator,Package,Quantity,Value,Type,\"Manufacturer/part number\",Supplier,\"Order code\",\"Alternative part\",\"Alternative supplier\",\"Alternative order code\",\"No Fit\"\n"
        else:
            csv = "Id,Designator,Package,Quantity,Value,Type,\"Manufacturer/part number\",Supplier,\"Order code\",\"No Fit\"\n"
        n = 1
        for l in lines:
            csv += str(n) + ","
            csv += l['Designator'] + ","
            csv += l['Package'] + ","
            csv += l['Quantity'] + ","
            csv += l['Value'] + ","
            csv += l['Type'] + ","
            csv += l['Part number'] + ","
            csv += l['Supplier'] + ","
            csv += l['Order code'] + ","
            if alternatives:
                csv += l['Alternative part'] + ","
                csv += l['Alternative supplier'] + ","
                csv += l['Alternative order code'] + ","
            csv += l['No Fit'] + "\n"
            n += 1
        return csv
    
    def _start_element(self, name, attrs):
        if name == "comp":
            self.components.append(entity(attrs["ref"]))
            self.in_component = attrs["ref"]
        elif name == "field":
            self.in_field = attrs["name"]
    
    def _end_element(self, name):
        if name == "comp":
            self.in_component = None
        elif self.in_component != None:
            if name == "value":
                self.components[-1].value = self.char_buffer.strip()
            elif name == "footprint":
                self.components[-1].package = self.char_buffer.strip()
                if self.components[-1].fp_type == "unknown":
                    if "SMT" in self.char_buffer:
                        self.components[-1].fp_type = "SMT"
                    elif "THT" in self.char_buffer:
                        self.components[-1].fp_type = "THT"
                    elif "Mechanical" in self.char_buffer:
                        self.components[-1].fp_type = "Virtual"
            elif name == "field":
                if self.in_field != None:
                    self.components[-1][self.in_field] = self.char_buffer.strip()
                self.in_field = None
                
        self.char_buffer = ""
    
    def _char_data(self, data):
        self.char_buffer += data

if __name__=="__main__":
    if len(sys.argv) != 3:
        print("Unexpected number of arguments, was expecting <input> <output>")
        sys.exit(1)
        
    with open(sys.argv[1], "r") as fr:
        d = fr.read()
        
    kip = KiXMLParser()
    
    csv = ', "Product: {0}", '.format(os.path.basename(sys.argv[2]))
    csv += '"Version: %VER%",'
    csv += '"Date: {0}"\n'.format(time.strftime("%Y-%m-%d"))
    csv += '\n'
    
    csv += kip.convert(d)
    
    csv += "\n\n"
    csv += ', "Where parts are labelled GENERIC the specifications are a minimum"\n'
    csv += ', "For example a resistor labelled \'GENERIC 0603 5% 0.063W\' may be"\n'
    csv += ', "replaced by a 1% 0.1W part if that simplifies line setup"'
    
    with open(sys.argv[2] + ".csv", "w") as fw:
        fw.write(csv)
    
