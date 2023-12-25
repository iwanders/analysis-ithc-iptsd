#!/usr/bin/env python3

import sys
import json
from collections import namedtuple
from enum import Enum

IPTS_DFT_NUM_COMPONENTS = 9
REAL = 0
IMAG = 1

class EntryType(Enum):
    IPTS_DFT_ID_POSITION = 6
    IPTS_DFT_ID_POSITION2 = 7
    METADATA = 999

DftWindow = namedtuple("Window", ["rows", "type", "x", "y"])
Row = namedtuple("Row", ['freq', 'mag', 'first', 'last', 'mid', 'zero', 'iq'])
Record = namedtuple("Record", ["type", "payload"])

MetadataSize = namedtuple("MetataSize", ["rows", "columns", "width", "height"])
MetataTransform = namedtuple("MetataTransform", ["xx", "yx", "tx", "xy", "yy", "ty"])
Metadata = namedtuple("Metadata", ["size", "transform"])


class Config:
    def __init__(self):
        self.dft_position_min_amp = 50
        self.dft_position_min_mag = 2000
        self.dft_position_exp = -0.7

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


import math
clamp = lambda x, y, z: max(min(x, z), y)

def cpp_interpolate_pos(row, config):

    # // assume the center component has the max amplitude
    maxi = int(IPTS_DFT_NUM_COMPONENTS / 2)

    # // off-screen components are always zero, don't use them
    mind = -0.5
    maxd = -0.5

    if (row.iq[maxi - 1][REAL] == 0 and row.iq[maxi - 1][IMAG] == 0):
        maxi += 1
        mind = -1.0
    elif (row.iq[maxi + 1][REAL] == 0 and row.iq[maxi +1][IMAG] == 0):
        maxi -= 1
        maxd = 1.0


    # // get phase-aligned amplitudes of the three center components
    amp = float(math.hypot(row.iq[maxi][REAL], row.iq[maxi][IMAG]))

    # print(f"amp: {amp}")
    # print(f"maxi: {maxi}")
    # print(f"maxd: {maxd}")
    
    if amp < config.dft_position_min_amp:
        return float("NaN")

    # const f64 sin = gsl::at(row.real, maxi) / amp;
    # const f64 cos = gsl::at(row.imag, maxi) / amp;
    f64_sin = float(row.iq[maxi][REAL] / amp)
    f64_cos = float(row.iq[maxi][IMAG] / amp)
    # print(f"f64_sin: {f64_sin}")
    # print(f"f64_cos: {f64_cos}")

    x = [
        f64_sin * row.iq[maxi - 1][REAL] + f64_cos * row.iq[maxi - 1][IMAG],
        amp,
        f64_sin * row.iq[maxi + 1][REAL] + f64_cos * row.iq[maxi + 1][IMAG],
    # ]
    # print(f"x[0]: {x[0]}")
    # print(f"x[1]: {x[1]}")
    # print(f"x[2]: {x[2]}")

    # // convert the amplitudes into something we can fit a parabola to
    try:
        x = [math.pow(abs(v), config.dft_position_exp) for v in x]
    except ValueError:
        return float("NaN")
        

    # print(f"x[0]: {x[0]}")
    # print(f"x[1]: {x[1]}")
    # print(f"x[2]: {x[2]}")

    # // check orientation of fitted parabola
    if (x[0] + x[2] <= (2.0 * x[1])):
        return float("NaN")

    # // find critical point of fitted parabola
    # const f64 d = (x[0] - x[2]) / (2 * (x[0] - 2 * x[1] + x[2]));
    f64_d = (x[0] - x[2]) / (2.0 * (x[0] - 2.0 * x[1] + x[2]))
    # print(f"f64_d: {f64_d}")


    return row.first + maxi + clamp(f64_d, mind, maxd)

def test_pos():
    iq = [(    -8,    -3),(    -6,    -3),(     3,     2),(   202,   103),(   260,   133),(    -3,     1),(   -15,    -7),(   -13,    -6),(   -10,    -7),]

    frequency = 1187205120;
    magnitude = 85289;
    first = 28;
    last = 36;
    mid = 32;
    row = Row(freq=frequency, mag=magnitude, first=first, last=last, mid=mid, zero=0, iq=iq)

    config = Config()
    x = cpp_interpolate_pos(row, config)
    print(x)
    sys.exit()

# test_pos()

if __name__ == "__main__":
    d = load(sys.argv[1])

    metadata = get_metadata(d)
    config = Config()

    for r in d:
        if r.type == EntryType.IPTS_DFT_ID_POSITION:
            payload = r.payload
            x = cpp_interpolate_pos(payload.x[0], config)
            y = cpp_interpolate_pos(payload.y[0], config)
            print(x,y)
