#!/usr/bin/env python3

# It's xml... but we can absolutely parse this in a more performant way
# by just using strings.

from collections import namedtuple

"""
<packet logtime="75658144700" wnd="0" digitizer="3" tabletcontextid="-1" cursorid="-1" name="INK" cu="1" x="17892" y="12996" inverted="true" eraser="true" time="75658" scantime="192" pressure="40287" tiltx="504" tilty="893" inrange="true" 
<packet logtime="35075686900" wnd="0" digitizer="3" tabletcontextid="-1" cursorid="-1" name="INK" cu="1" x="7434" y="7312" time="35076" scantime="24682" pressure="0" tiltx="0" tilty="0" inrange="true" />
<packet logtime="35075702700" wnd="0" digitizer="3" tabletcontextid="-1" cursorid="-1" name="INK" cu="1" x="7434" y="7312" down="true" time="35076" scantime="24683" pressure="6447" tiltx="1905" tilty="1590" inrange="true" />
"""

# These values are always constant, so lets discard them, the values are:
# wnd="0" digitizer="3" tabletcontextid="-1" cursorid="-1" name="INK" cu="1" 
_discard = set(("wnd", "digitizer", "tabletcontextid", "cursorid", "name", "cu"))

# Named tuple to convey all the information
PenEvent = namedtuple("PenEvent", [
    "time",
    "logtime",
    "scantime",
    "x",
    "y",
    "inverted",
    "eraser",
    "pressure",
    "tiltx",
    "tilty",
    "inrange",
    "down",
    "barrel",
])

"""
    <property name="x" logmin="0" logmax="9600" res="350.480072" unit="cm" />
    <property name="y" logmin="0" logmax="7200" res="394.2828674" unit="cm" />
    <property name="pressure" logmin="0" logmax="4096" res="1.#INF" unit="DEFAULT" />
    <property name="tiltx" logmin="0" logmax="18000" res="100" unit="deg" />
    <property name="tilty" logmin="0" logmax="18000" res="100" unit="deg" />
    <property name="unknown" logmin="0" logmax="65535" res="10000" unit="cm" />
    <property name="unknown" logmin="0" logmax="1" res="1.#INF" unit="DEFAULT" />
    <property name="inverted" logmin="0" logmax="1" res="1.#INF" unit="DEFAULT" />
    <property name="barrel" logmin="0" logmax="1" res="1.#INF" unit="DEFAULT" />
    <property name="unknown" logmin="0" logmax="1" res="1.#INF" unit="DEFAULT" />
    <property name="inrange" logmin="0" logmax="1" res="1.#INF" unit="DEFAULT" />
"""


# Some type wrangling
def _boolcaster(v):
    return v == "true"

_type_handlers = {
    "time":int,
    "logtime":int,
    "scantime":int,
    "x":int,
    "y":int,
    "inverted":_boolcaster,
    "eraser":_boolcaster,
    "pressure":int,
    "tiltx":int,
    "tilty":int,
    "inrange":_boolcaster,
    "down":_boolcaster,
    "barrel":_boolcaster,
}

def load_digiinfo_xml(path):
    with open(path) as f:
        d = f.readlines()

    # We only care about the events, the rest is constants.
    d = d[d.index("  <events>\n") + 1:d.index("  </events>\n")]
    
    entries = []
    for l in d:
        # Drop the junk, split into list of attributes
        attributes = l[len("    <packet "):-4].split(" ")

        # Split individual attributes
        attributes = [x.split("=") for x in attributes]
        
        # Remove the quotes
        attributes = {k: v[1:-1] for (k,v) in attributes}

        # Perform discarding of things we don't care about.
        for k in _discard:
            del attributes[k]

        # Perform type wrangling
        tmp = {}
        for k in PenEvent._fields:
            v = attributes.get(k, None)
            if v is not None:
                v = _type_handlers[k](v)
                del attributes[k]
            tmp[k] = v

        # Verify attributes is empty now, ensuring we didn't lose any
        # data in the conversion.
        assert(len(attributes) == 0)

        # Use tmp to instantiate the named tuple for our event
        entries.append(PenEvent(**tmp))

    return entries

if __name__ == "__main__":
    import sys
    d = load_digiinfo_xml(sys.argv[1])
    for e in d:
        print(e)

