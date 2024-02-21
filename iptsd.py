#!/usr/bin/env python3

# Holds python implementations of the algoritms implemented in iptsd.
# Some of them are unverified against c++.

import json
from collections import namedtuple
from enum import Enum
from ipts import DftType, IPTS_DFT_NUM_COMPONENTS, IPTS_DFT_PRESSURE_ROWS, IptsDftWindowPosition, IptsDftWindowPressure, IptsDftWindowButton


DftWindow = namedtuple("Window", ["rows", "type", "x", "y"])
Row = namedtuple("Row", ['freq', 'mag', 'first', 'last', 'mid', 'zero', 'iq'])
Record = namedtuple("Record", ["type", "payload"])

MetadataSize = namedtuple("MetataSize", ["rows", "columns", "width", "height"])
MetataTransform = namedtuple("MetataTransform", ["xx", "yx", "tx", "xy", "yy", "ty"])
Metadata = namedtuple("Metadata", ["size", "transform"])
StylusData = namedtuple("StylusData", ["timestamp", "proximity", "contact", "rubber", "button", "x", "y", "pressure", "altitude", "azimuth", "serial", "x_t", "y_t", "x_ring", "y_ring"])

REAL = 0
IMAG = 1

clamp = lambda x, y, z: max(min(x, z), y)

class IptsdConfig:
    def __init__(self):
        self.dft_position_min_amp = 50
        self.dft_position_min_mag = 2000
        self.dft_position_exp = -0.7
        self.dft_freq_min_mag = 10000
        self.dft_tilt_min_mag = 10000
        self.dft_button_min_mag = 1000

def iptsd_json_load(p):
    import gzip
    entries = []
    opener = gzip.open if p.endswith("gz") else open
    with opener(p) as f:
        d = json.load(f)
    for r in d:
        if r["type"] == "STYLUS_DATA":
                payload = r["payload"]
                data = StylusData(**payload)
                entries.append(Record(type=r["type"], payload=data))
        elif r["type"] == "METADATA":
                payload = r["payload"]
                size = MetadataSize(**payload["size"])
                transform = MetataTransform(**payload["transform"])
                metadata = Metadata(size=size, transform=transform)
                entries.append(Record(type=r["type"], payload=metadata))
        else:
            # DFT frame
            looked_up_type = DftType[r["type"]]
            if looked_up_type in (DftType.IPTS_DFT_ID_POSITION, DftType.IPTS_DFT_ID_POSITION2, DftType.IPTS_DFT_ID_BUTTON, DftType.IPTS_DFT_ID_PRESSURE):
                payload = r["payload"]
                x = [Row(**v) for v in payload["x"]]
                y = [Row(**v) for v in payload["y"]]
                window = DftWindow(rows=payload["rows"], type=payload["type"], x=x, y=y)
                entries.append(Record(type=looked_up_type, payload=window))
            
    return entries


def _convert_row(row):
    if hasattr(row, "real"):
        return Row(**dict(
            freq = row.frequency,
            mag = row.magnitude,
            first= row.first,
            last = row.last,
            mid = row.mid,
            zero = row.zero,
            iq = [(row.real[i], row.imag[i]) for i in range(IPTS_DFT_NUM_COMPONENTS)]
        ))
    return row
    

def cpp_interpolate_pos(row, config, maxi_override = None):
    import math

    row = _convert_row(row)

    # // assume the center component has the max amplitude
    maxi = int(IPTS_DFT_NUM_COMPONENTS / 2)
    # maxi = get_maxi(row)
    if maxi_override is not None:
        maxi = maxi_override

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
    # Sort of like quadterp from [1]?
    f64_d = float(x[0] - x[2]) / (2.0 * (x[0] - 2.0 * x[1] + x[2]))
    # print(f"f64_d: {f64_d}")
    # print(f"row.first: {row.first}")

    return row.first + maxi + clamp(f64_d, mind, maxd)


def cpp_interpolate_frequency(window, config, maxi_override=None):
    rows = IPTS_DFT_PRESSURE_ROWS

    if rows < 3:
        return float("NaN")

    maxi = 0
    maxm = 0
    maxi_pairs = []
    for i in range(rows):
        m = _convert_row(window.x[i]).mag + _convert_row(window.y[i]).mag
        maxi_pairs.append((m, i))
        if m > maxm:
            maxm = m
            maxi = i

    if maxi_override is not None:
        maxi_pairs = sorted(maxi_pairs)[::-1]
        maxi = maxi_pairs[maxi_override][1]
        # print(maxi)
    
    if maxm < 2.0 * config.dft_freq_min_mag:
        return float("NaN")

    mind = -0.5
    maxd = 0.5

    if maxi < 1:
        maxi = 1
        mind = -1
    elif maxi > rows - 2:
        maxi = rows - 2
        maxd = 1

    real = [0, 0, 0]
    imag = [0, 0, 0]

    # /*
    # * all components in a row have the same phase, and corresponding x and y rows also
    # * have the same phase, so we can add everything together
    # */
    for i in range(3):
        for j in range(IPTS_DFT_NUM_COMPONENTS):
            rowx = _convert_row(window.x[maxi + i - 1])
            rowy = _convert_row(window.y[maxi + i - 1])
            real[i] += rowx.iq[j][REAL] + rowx.iq[j][REAL]
            imag[i] += rowx.iq[j][IMAG] + rowx.iq[j][IMAG]

    # // interpolate using Eric Jacobsen's modified quadratic estimator
    ra = real[0] - real[2]
    rb = 2 * real[1] - real[0] - real[2]
    ia = imag[0] - imag[2]
    ib = 2 * imag[1] - imag[0] - imag[2]

    denom =  (rb * rb + ib * ib)
    if denom == 0:
        return float("nan")
    d = (ra * rb + ia * ib) / denom
    return (maxi + clamp(d, mind, maxd)) / (rows - 1)


def cpp_handle_button(dft_button, dft_position, config=IptsdConfig()):
    if dft_button.header.num_rows <= 0:
        return None

    # Skip the group check, it doesn't affect the issues on our side.
    button = False
    eraser = False

    mid = int(IPTS_DFT_NUM_COMPONENTS / 2)

    prowx = _convert_row(dft_position.x[0])
    prowy = _convert_row(dft_position.y[0])
    m_real = prowx.iq[mid][REAL] + prowy.iq[mid][REAL]
    m_imag = prowx.iq[mid][IMAG] + prowy.iq[mid][IMAG]

    rowx = _convert_row(dft_button.x[0])
    rowy = _convert_row(dft_button.y[0])
    if (rowx.mag > config.dft_button_min_mag and rowy.mag > config.dft_button_min_mag):
        real = rowx.iq[mid][REAL] + rowy.iq[mid][REAL]
        imag = rowx.iq[mid][IMAG] + rowy.iq[mid][IMAG]
        # same phase as position signal = eraser, opposite phase = button
        val = m_real * real + m_imag * imag
        button = val < 0
        rubber = val > 0

    return (button, eraser)
    

def process_button(dft_button, dft_position, config=IptsdConfig()):

    if dft_button is None or dft_position is None:
        return None
    res = {}

    z = cpp_handle_button(dft_button,dft_position, config)
    if z is not None:
        res["button"] = z[0]
        res["eraser"] = z[1]
    return res

def process_position(dft, config = IptsdConfig()):
    if dft is None or dft.header.num_rows <= 1:
        return None
    res = {}

    if dft.x[0].magnitude <= config.dft_position_min_mag or dft.y[0].magnitude <= config.dft_position_min_mag:
        return None

    x = cpp_interpolate_pos(dft.x[0], config)
    y = cpp_interpolate_pos(dft.y[0], config)

    res["x"] = x
    res["y"] = y

    res["x_t"] = float("nan")
    res["y_t"] = float("nan")

    if dft.x[1].magnitude > config.dft_tilt_min_mag and dft.y[1].magnitude > config.dft_tilt_min_mag:
        xt = cpp_interpolate_pos(dft.x[1], config)
        yt = cpp_interpolate_pos(dft.y[1], config)
        res["x_t"] = xt
        res["y_t"] = yt
    return res

def process_pressure(dft, config = IptsdConfig()):
    if dft is None or dft.header.num_rows <= 1:
        return None

    res = {}
    p = cpp_interpolate_frequency(dft, config)
    p = 1.0 - p
    if p > 0:
        res["contact"] = True
        res["pressure"] = clamp(p, 0.0, 1.0)
    else:
        res["contact"] = False
        res["pressure"] = 0.0
    return res


def obtain_state(grouped, insert_group=False, config = IptsdConfig()):
    records = []
    for group in grouped:
        current = {}
        pos = process_position(group.get(IptsDftWindowPosition, None), config=config)
        if pos:
            current.update(pos)

        pressure = process_pressure(group.get(IptsDftWindowPressure, None), config=config)
        if pressure:
            current.update(pressure)

        button = process_button(group.get(IptsDftWindowButton, None), group.get(IptsDftWindowPosition, None), config=config)
        if button:
            current.update(button)

        if insert_group:
            current["group"] = group
        records.append(current)
    return records

def write_states(fname, records):
    import json
    import copy
    clean_records = []
    for r in records:
        clean_records.append({k:r[k] for k in r.keys() if k != "group"})
    with open(fname, "w") as f:
        json.dump(clean_records, f)


if __name__ == "__main__":
    import sys
    z = iptsd_load(sys.argv[1])
    for r in z:
        print(r)
