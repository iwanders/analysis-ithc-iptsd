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
    import gzip
    entries = []
    opener = gzip.open if p.endswith("gz") else open
    with opener(p) as f:
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


clamp = lambda x, y, z: max(min(x, z), y)
def cpp_interpolate_pos(row, config):
    import math

    # // assume the center component has the max amplitude
    maxi = int(IPTS_DFT_NUM_COMPONENTS / 2)

    # // off-screen components are always zero, don't use them
    mind = -0.5
    maxd = 0.5

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
    ]
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
    f64_d = float(x[0] - x[2]) / (2.0 * (x[0] - 2.0 * x[1] + x[2]))
    # print(f"f64_d: {f64_d}")
    # print(f"row.first: {row.first}")

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
    """CPP:
        amp : 292.043
        maxi : 4
        maxd : 0.5
        sin : 0.89028
        cos : 0.455413
        x[0] : 226.744
        x[1] : 292.043
        x[2] : -2.21543
        x.at(: 0): 0.0224453
        x.at(: 1): 0.0188013
        x.at(: 2): 0.573033
        orient : 0
        d : -0.493468
        Res:31.5065

        here:
        amp: 292.04280508172087
        maxi: 4
        maxd: -0.5
        f64_sin: 0.8902804502485364
        f64_cos: 0.4554126918579051
        x[0]: 226.7441582115686
        x[1]: 292.04280508172087
        x[2]: -2.215428658887704
        x[0]: 0.02244526437831396
        x[1]: 0.01880128107859886
        x[2]: 0.5730329055304914
        f64_d: -0.4934681078557972
        31.5

    """
    print(x)
    sys.exit()

# test_pos()

def show_trajectory(traj, traj2=[]):
    import matplotlib.pyplot as plt
    x = [v[0] for v in traj]
    y = [v[1] for v in traj]
    x2 = [v[0] for v in traj2]
    y2 = [v[1] for v in traj2]

    plt.plot(x, y)
    plt.plot(x2, y2)
    plt.xlim([0, 68])
    plt.ylim([0, 44])
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')
    plt.show()


def changed_interpolate(row, config):
    import math
    maxi = int(IPTS_DFT_NUM_COMPONENTS / 2)
    mind = -0.5
    maxd = 0.5

    iq_mag = [math.hypot(I, Q) for I, Q in row.iq]
    print(iq_mag)
    ibest = 0
    vbest = -1000000
    for i, v in enumerate(iq_mag):
        if vbest < v:
            ibest = i 
            vbest = v

    maxi = ibest
    # // get phase-aligned amplitudes of the three center components
    amp = float(math.hypot(row.iq[maxi][REAL], row.iq[maxi][IMAG]))


    if amp < config.dft_position_min_amp:
        return float("NaN")


    f64_sin = float(row.iq[maxi][REAL] / amp)
    f64_cos = float(row.iq[maxi][IMAG] / amp)


    x = [
        f64_sin * row.iq[maxi - 1][REAL] + f64_cos * row.iq[maxi - 1][IMAG],
        amp,
        f64_sin * row.iq[maxi + 1][REAL] + f64_cos * row.iq[maxi + 1][IMAG],
    ]

    print(x)

    # if (x[0] + x[2] <= (2.0 * x[1])):
        # print("bail")
        # return float("NaN")

    f64_d = float(x[0] - x[2]) / (2.0 * (x[0] - 2.0 * x[1] + x[2]))
    return row.first + maxi + clamp(f64_d, mind, maxd)
    

def slanted_incontact_tip_loss_tip_y_row():
    row = Row(freq=1210480000, mag=510696, first=18, last=26, mid=22, zero=0, iq=[[33, 122], [53, 201], [94, 352], [150, 569], [186, 690], [230, 868], [159, 570], [89, 308], [49, 166]])
    print(row)
    config = Config()

    tipx = changed_interpolate(row, config)
    print("tipx Should be around 22")
    print("tipx", tipx)

    row = Row(freq=1187205120, mag=419413, first=24, last=32, mid=28, zero=0, iq=[[1, 0], [0, 0], [-4, 8], [-39, 81], [-282, 583], [-15, 26], [4, -14], [5, -13], [4, -11]])
    penx = changed_interpolate(row, config)
    print("penx", penx)

    

    sys.exit()
# slanted_incontact_tip_loss_tip_y_row()



Scenario = namedtuple("Scenario", ["filename", "max_index", "interp"])

test_scenarios = {
    "slanted_incontact_tip_loss_orig":Scenario("./slanted_incontact.json.gz", max_index=73, interp=cpp_interpolate_pos),
    "slanted_incontact_tip_loss_orig_full":Scenario("./slanted_incontact.json.gz", max_index=1e6, interp=cpp_interpolate_pos),
    "slanted_incontact_tip_loss_new":Scenario("./slanted_incontact.json.gz", max_index=73, interp=changed_interpolate),
    "slanted_incontact_tip_loss_new_full":Scenario("./slanted_incontact.json.gz", max_index=1e6, interp=changed_interpolate),
}

if __name__ == "__main__":
    # Metadata(size=MetataSize(rows=46, columns=68, width=27389, height=18259), transform=MetataTransform(xx=408.791, yx=0, tx=0, xy=0, yy=405.756, ty=0))
    default_interpolate = cpp_interpolate_pos
    scenario = test_scenarios.get(sys.argv[1], Scenario(sys.argv[1], max_index=None, interp=default_interpolate))

    d = load(scenario.filename)
    interpolate = scenario.interp

    metadata = get_metadata(d)
    print(metadata)
    config = Config()


    pos = []
    pos1 = []

    positions = []
    for r in d:
        if r.type == EntryType.IPTS_DFT_ID_POSITION:
            positions.append(r.payload)

    for i, r in enumerate(d):
        if scenario.max_index is not None and i > scenario.max_index:
            break
        if r.type == EntryType.IPTS_DFT_ID_POSITION2:
            payload = r.payload
            print("\n\n\n")
            # print("x")
            x = interpolate(payload.x[0], config)
            # print("y")
            y = interpolate(payload.y[0], config)
            pos.append([x,y])
            print("Pos", x,y)

            x = interpolate(payload.x[1], config)
            y = interpolate(payload.y[1], config)
            pos1.append([x,y])
            print("Tip", x,y)

            print("Rows: ")
            for r in range(payload.rows):
                print(f"x[{r}]", payload.x[r])
            print()
            for r in range(payload.rows):
                print(f"y[{r}]", payload.y[r])



    show_trajectory(pos, pos1)



