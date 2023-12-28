#!/usr/bin/env python3

#[1]: http://www.ericjacobsen.org/fe2/fe2.htm & http://www.ericjacobsen.org/FTinterp.pdf

# This could be relevant as well;
#https://ccrma.stanford.edu/~jos/sasp/Quadratic_Interpolation_Spectral_Peaks.html

import sys
import json
from collections import namedtuple
from enum import Enum

IPTS_DFT_NUM_COMPONENTS = 9
IPTS_DFT_PRESSURE_ROWS  = 6
REAL = 0
IMAG = 1

class EntryType(Enum):
    IPTS_DFT_ID_POSITION = 6
    IPTS_DFT_ID_POSITION2 = 7
    IPTS_DFT_ID_BUTTON   = 9
    IPTS_DFT_ID_PRESSURE = 11
    METADATA = 999
    def __lt__(self, o):
        self._value_ < o._value_



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
        self.dft_freq_min_mag = 10000

def load(p):
    import gzip
    entries = []
    opener = gzip.open if p.endswith("gz") else open
    with opener(p) as f:
        d = json.load(f)
    for r in d:
        looked_up_type = EntryType[r["type"]]
        if looked_up_type in (EntryType.IPTS_DFT_ID_POSITION, EntryType.IPTS_DFT_ID_POSITION2, EntryType.IPTS_DFT_ID_BUTTON, EntryType.IPTS_DFT_ID_PRESSURE):
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
    # Sort of like quadterp from [1]?
    f64_d = float(x[0] - x[2]) / (2.0 * (x[0] - 2.0 * x[1] + x[2]))
    # print(f"f64_d: {f64_d}")
    # print(f"row.first: {row.first}")

    return row.first + maxi + clamp(f64_d, mind, maxd)


def cpp_interpolate_frequency(window, config):
    rows = IPTS_DFT_PRESSURE_ROWS

    if rows < 3:
        return float("NaN")

    maxi = 0
    maxm = 0
    for i in range(rows):
        m = window.x[i].mag + window.y[i].mag 
        if m > maxm:
            maxm = m
            maxi = i

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
            rowx = window.x[maxi + i - 1]
            rowy = window.y[maxi + i - 1]
            real[i] += rowx.iq[j][REAL] + rowx.iq[j][REAL]
            imag[i] += rowx.iq[j][IMAG] + rowx.iq[j][IMAG]

    # // interpolate using Eric Jacobsen's modified quadratic estimator
    ra = real[0] - real[2]
    rb = 2 * real[1] - real[0] - real[2]
    ia = imag[0] - imag[2]
    ib = 2 * imag[1] - imag[0] - imag[2]

    d = (ra * rb + ia * ib) / (rb * rb + ib * ib)
    return (maxi + clamp(d, mind, maxd)) / (rows - 1)


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

def show_trajectory(trajectories={}):
    import matplotlib.pyplot as plt

    for n,t in trajectories.items():
        x = [v[0] for v in t]
        y = [v[1] for v in t]
        if n.endswith(":"):
            plt.plot(x, y, ":", label=n)
        elif n.endswith("*"):
            plt.plot(x, y, "*", label=n)
        else:
            plt.plot(x, y, label=n)
        
    plt.xlim([0, 68])
    plt.ylim([0, 44])
    plt.legend(loc="upper right")
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')
    plt.show()


def show_plots(trajectories={}, scatter={}):
    import matplotlib.pyplot as plt
    # print(trajectories)
    for n,t in trajectories.items():
        x = [v[0] for v in t]
        y = [v[1] for v in t]
        # print(x)
        linewidth = 1.0
        plt.plot(x, y, label=n, linewidth=linewidth)

    for n,t in scatter.items():
        plt.plot(t[0], t[1], "*", label=n)


    plt.legend(loc="upper right")
    ax = plt.gca()
    plt.show()


def changed_interpolate(row, config):
    
    
    v = sum(np.sqrt(square_iq(row)))
    if v < 100:
        return float("nan")

    x1_fit, x1_data, coeff = make_poly(row, 3)
    # results["x1_fit"] = x1_fit
    # results["x1_data"] = x1_data

    # results["x1_fit"] = make_poly(pos_payload.x[1], 3)

    
    
    peak = find_peak(coeff)
    peak[0] += row.first
    return peak[0]
    

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

def process_data(d, interpolate):
    result = {}
    
    pos_from_pos = []
    ring_pos_from_pos = []
    pos_from_pos2 = []
    ring_pos_from_pos2 = []

    for i, r in enumerate(d):
        payload = r.payload
        if scenario.max_index is not None and i > scenario.max_index:
            break
        if r.type == EntryType.IPTS_DFT_ID_POSITION2:
            x = interpolate(payload.x[0], config)
            y = interpolate(payload.y[0], config)
            pos_from_pos2.append([x,y])

            x = interpolate(payload.x[1], config)
            y = interpolate(payload.y[1], config)
            ring_pos_from_pos2.append([x,y])
            
        if r.type == EntryType.IPTS_DFT_ID_POSITION:
            x = interpolate(payload.x[0], config)
            y = interpolate(payload.y[0], config)
            pos_from_pos.append([x,y])

            x = interpolate(payload.x[1], config)
            y = interpolate(payload.y[1], config)
            ring_pos_from_pos.append([x,y])

    result["pos_from_pos"] = pos_from_pos
    result["ring_pos_from_pos"] = ring_pos_from_pos
    result["pos_from_pos2"] = pos_from_pos2
    result["ring_pos_from_pos2"] = ring_pos_from_pos2
    return result

def process_single_frame(frame, interpolate):
    # Unpack the frame... :/
    entries = []
    for n, v in frame.items():
        r = Record(n, v)
        entries.append(r)

    return process_data(entries, interpolate)

import numpy as np

def row_plottable(r, index, s=1.0):
    return [(r.first + i, r.iq[i][index] * s) for i in range(9)]
def square_iq(r):
    return [r.iq[i][0] * r.iq[i][0] + r.iq[i][1] * r.iq[i][1] for i in range(9)]

# Do everything in the window frame.
# https://en.wikipedia.org/wiki/Polynomial_regression#Matrix_form_and_calculation_of_estimates
# Perform a weighted least squares fit using the vandermonde matrix.
def fit(data, order, weights):
    idx = list(range(len(data)))
    m = np.vander(idx, order) # https://numpy.org/doc/stable/reference/generated/numpy.vander.html
    y = data

    if weights is not None:
        m = np.diag(weights).dot(m)
        y = np.diag(weights).dot(y)

    pinv = np.linalg.pinv(m)
    # Perform Moore-Penrose pseudoinverse
    betas = pinv.dot(np.array(y))
    return betas

def make_poly(row, order):

    v = np.sqrt(square_iq(row))

    maxv = max(v)
    # weights = [z / maxv for z in v]
    # print("weights", weights)
    
    def gaussian(x, amplitude, mean, stddev):
        return amplitude * np.exp(-((np.array(x) - mean) / 4 / stddev)**2)

    # weights = [0, 0.3, 0.5,   1, 1, 1,  0.5, 0.3, 0]
    weights = list(gaussian(list(range(9)), 1.0, 4, 0.7)) # ring
    # weights = [0, 0.0, 0.5,   1, 1, 1,  0.5, 0.0, 0] # tip
    # print(weights)

    b = fit(v, order, weights)

    x_nice = [i / 10.0 for i in range(9 * 10)]
    res = np.polyval(b, x_nice)
    # print(res)
    return list(zip([z+ row.first for z in x_nice], [z for z in res])), list(zip([z+ row.first for z in range(9)], v)), b

def find_peak(coeff):
    # standard cubic function, take derivative, find root of that
    # then plug that back in.
    assert len(coeff) == 3
    # f(x) = ax*x + bx + c
    # f'(x) = 2ax + b
    # 0 = 2ax + b
    # x = -b / 2a
    x_peak = -coeff[1] / (2.0 * coeff[0])
    return [x_peak, np.polyval(coeff, x_peak)]

def print_dft_rows(dft_data):
    for i in range(dft_data.rows):
        print(f"x[{i}]", dft_data.x[i])
    for i in range(dft_data.rows):
        print(f"y[{i}]", dft_data.y[i])
    

def do_things_on_frame(frame, interpolate_fun):

    print_things = False

    print_things = True
    if print_things:
        for k, v in sorted(frame.items()):
            print(k)
            print_dft_rows(v)



    # [[-2, -6], [-3, -5], [-2, 1], [28, 61], [327, 707], [30, 64], [4, 8], [1, 3], [0, 1]]
    pos_payload = frame[EntryType.IPTS_DFT_ID_POSITION]
    pos2_payload = frame[EntryType.IPTS_DFT_ID_POSITION2]
    pressure_payload = frame[EntryType.IPTS_DFT_ID_PRESSURE]
    # print(pos_payload)

    freq = cpp_interpolate_frequency(pressure_payload, config)
    print(freq)

    x = interpolate(pos_payload.x[0], config)
    y = interpolate(pos_payload.y[0], config)

    # make IQs into plottables.

    I = 0
    Q = 1

    results = {
        # "x0_I": row_plottable(pos_payload.x[0], I),
        # "x0_Q": row_plottable(pos_payload.x[0], Q),
        # "x1_I": row_plottable(pos_payload.x[1], I),
        # "x1_Q": row_plottable(pos_payload.x[1], Q),
    }
    

    print("Interestting here")
    x0_fit, x0_data, coeff = make_poly(pos_payload.x[0], 3)
    results["x0_fit"] = x0_fit
    results["x0_data"] = x0_data


    # print("x0_data: ", x0_data)


    x1_fit, x1_data, coeff2 = make_poly(pos_payload.x[1], 3)
    results["x1_fit"] = x1_fit
    results["x1_data"] = x1_data

    x3_fit, x3_data, coeff2 = make_poly(pos2_payload.x[3], 3)
    results["x3_fit"] = x3_fit
    results["x3_data"] = x3_data

    x5_fit, x5_data, coeff2 = make_poly(pos2_payload.x[5], 3)
    results["x5_fit"] = x5_fit
    results["x5_data"] = x5_data

    # results["x1_fit"] = make_poly(pos_payload.x[1], 3)

    
    
    peak = find_peak(coeff)
    peak[0] += pos_payload.x[0].first
    scatter = {
        "peak": peak
    }
    show_plots(results, scatter)


def process_frames(frames, interpolate):
    result = {}
    def append(name, entry):
        if not name in result:
            result[name] = []
        result[name].append(entry)

    for frame in frames:
        if len(frame.items()) < 4:
            continue
        pos = frame[EntryType.IPTS_DFT_ID_POSITION]
        pos2 = frame[EntryType.IPTS_DFT_ID_POSITION2]
        pres = frame[EntryType.IPTS_DFT_ID_PRESSURE]
        but = frame[EntryType.IPTS_DFT_ID_BUTTON]

        def coord_interp(row, index):
            x = interpolate(row.x[index], config)
            y = interpolate(row.y[index], config)
            return [x,y]


        append("pos_[0]", coord_interp(pos, 0))
        append("pos_[1]", coord_interp(pos, 1))
        # append("pos_[4]", coord_interp(pos, 4))


        append("pos2_[0]", coord_interp(pos2, 0))
        append("pos2_[1]", coord_interp(pos2, 1))
        append("pos2_[3]", coord_interp(pos2, 3))
        append("pos2_[5]", coord_interp(pos2, 5))

        append("but_[3]", coord_interp(but, 3))

        # append("pres_[2]", coord_interp(pres, 2))
        # append("pres_[3]", coord_interp(pres, 3))

    return result



def print_data(d):
    for i, r in enumerate(d):
        payload = r.payload
        if r.type in (EntryType.IPTS_DFT_ID_POSITION, EntryType.IPTS_DFT_ID_POSITION2,  EntryType.IPTS_DFT_ID_BUTTON,  EntryType.IPTS_DFT_ID_PRESSURE):
            print(r.type)
            print("Rows: ")
            for r in range(payload.rows):
                print(f"x[{r}]", payload.x[r])
            print()
            for r in range(payload.rows):
                print(f"y[{r}]", payload.y[r])


def make_frames(d):
    frames = []
    frame = { }
    for z in d:
        frame[z.type] = z.payload
        if z.type == EntryType.IPTS_DFT_ID_POSITION:
            frames.append(frame)
            frame = {}
    return frames


test_scenarios = {
    "slanted_incontact_tip_loss_orig":Scenario("./slanted_incontact.json.gz", max_index=73, interp=cpp_interpolate_pos),
    "slanted_incontact_tip_loss_orig_full":Scenario("./slanted_incontact.json.gz", max_index=1e6, interp=cpp_interpolate_pos),
    "slanted_incontact_tip_loss_new":Scenario("./slanted_incontact.json.gz", max_index=73, interp=changed_interpolate),
    "slanted_incontact_tip_loss_new_full":Scenario("./slanted_incontact.json.gz", max_index=1e6, interp=changed_interpolate),
    "spiral_out_loss_full":Scenario("./spiral_out.json.gz", max_index=1e6, interp=cpp_interpolate_pos),
    "spiral_out_full":Scenario("./spiral_out.json.gz", max_index=1e6, interp=cpp_interpolate_pos),
    "spiral_out_new_full":Scenario("./spiral_out.json.gz", max_index=1e6, interp=changed_interpolate),
}

def compare_scenario(data, interp_1, interp_2, keys):
    res1 = process_data(data, interp_1)
    res2 = process_data(data, interp_2)
    print(res1.keys())

    res = {}
    for k in keys:
        res[k + "_" + interp_1.__name__] = res1[k]
        res[k + "_" + interp_2.__name__] = res2[k]
        # for v1, v2 in zip(res1[k], res2[k]):
            # print(v1, v2)

    show_trajectory(res)
    


if __name__ == "__main__":
    # Metadata(size=MetataSize(rows=46, columns=68, width=27389, height=18259), transform=MetataTransform(xx=408.791, yx=0, tx=0, xy=0, yy=405.756, ty=0))
    default_interpolate = cpp_interpolate_pos
    scenario = test_scenarios.get(sys.argv[1], Scenario(sys.argv[1], max_index=None, interp=default_interpolate))

    d = load(scenario.filename)
    interpolate = scenario.interp


    frames = make_frames(d)

    metadata = get_metadata(d)
    print(metadata)
    config = Config()

    do_full = False
    do_full_frames = False
    do_on_frame = False
    do_comparison = False


    # do_full = True
    if do_full:
        res = process_data(d, interpolate)
        # print_data(d)
        s = process_single_frame(frames[190], interpolate)
        res["OURMARKER*"] = s["pos_from_pos"]
        show_trajectory(res)


    # do_comparison = True
    if do_comparison:
        keys = [
            "pos_from_pos",
            "ring_pos_from_pos",
            "pos_from_pos2",
            "ring_pos_from_pos2",
        ]
        compare_scenario(d, cpp_interpolate_pos, changed_interpolate, keys)




    do_on_frame = True
    if do_on_frame:
        # print("Frames: ", len(frames))
        f = frames[190]
        # print(f)

        res = do_things_on_frame(f, interpolate)

    # do_full_frames = True
    if do_full_frames:
        res = process_frames(frames, interpolate)
        # print_data(d)
        # s = process_single_frame(frames[190], interpolate)
        # res["OURMARKER*"] = s["pos_from_pos"]
        show_trajectory(res)
        


