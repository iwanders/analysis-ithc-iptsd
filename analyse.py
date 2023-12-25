#!/usr/bin/env python3

import sys
import json
from collections import namedtuple
from enum import Enum

DftWindow = namedtuple("Window", ["rows", "type", "x", "y"])
Row = namedtuple("Row", ['freq', 'mag', 'first', 'last', 'mid', 'zero', 'iq'])
Record = namedtuple("Record", ["type", "payload"])

MetadataSize = namedtuple("MetataSize", ["rows", "columns", "width", "height"])
MetataTransform = namedtuple("MetataTransform", ["xx", "yx", "tx", "xy", "yy", "ty"])
Metadata = namedtuple("Metadata", ["size", "transform"])

class EntryType(Enum):
    IPTS_DFT_ID_POSITION = 6
    IPTS_DFT_ID_POSITION2 = 7
    METADATA = 999

def load(p):
    entries = []
    with open(p) as f:
        d = json.load(f)
    for r in d:
        looked_up_type = EntryType[r["type"]]
        if looked_up_type in (EntryType.IPTS_DFT_ID_POSITION, EntryType.IPTS_DFT_ID_POSITION2):
            payload = r["payload"]
            x = [Row(**v) for v in payload["x"]]
            y = [Row(**v) for v in payload["y"]]
            window = DftWindow(rows=payload["rows"], type=payload["type"], x=x, y=y)
            entries.append(Record(type=looked_up_type, payload=window))
        if looked_up_type == EntryType.METADATA:
            payload = r["payload"]
            size = MetadataSize(**payload["size"])
            transform = MetataTransform(**payload["transform"])
            metadata = Metadata(size=size, transform=transform)
            entries.append(Record(type=looked_up_type, payload=metadata))
            
            
    return entries
    

def get_metadata(d):
    for z in d:
        if z.type == EntryType.METADATA:
            return z.payload


    


if __name__ == "__main__":
    d = load(sys.argv[1])

    metadata = get_metadata(d)

    for r in d:
        print(r)
