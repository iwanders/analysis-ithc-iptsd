#!/usr/bin/env python3

#[1]: http://www.ericjacobsen.org/fe2/fe2.htm & http://www.ericjacobsen.org/FTinterp.pdf

# This could be relevant as well;
#https://ccrma.stanford.edu/~jos/sasp/Quadratic_Interpolation_Spectral_Peaks.html

# Cpp version looks very much like the quadratic method from:
# https://dspguru.com/dsp/howtos/how-to-interpolate-fft-peak/
# https://www.dsprelated.com/showarticle/1043.php

# Can we sniff the data on windows to see if it is actually the same with the phase spiking?
# Perhaps https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/how-to-capture-a-usb-event-trace
# Or wireshark with https://wiki.wireshark.org/CaptureSetup/USB#windows



import sys
import json
from collections import namedtuple
from enum import Enum
from ipts import DftType, IPTS_DFT_NUM_COMPONENTS, IPTS_DFT_PRESSURE_ROWS
from iptsd import iptsd_json_load, IptsdConfig, cpp_interpolate_pos, cpp_interpolate_frequency, REAL, IMAG, clamp

def comp_to_str(z):
    return {REAL: "REAL", IMAG: "IMAG"}[z]

def get_metadata(d):
    for z in d:
        if z.type == DftType.METADATA:
            return z.payload

def get_maxi(row):
    maxi = 0
    vi = -float("inf")
    for i, (real, imag) in enumerate(row.iq):
        if vi < abs(real):
            maxi = i
            vi = abs(real)
    return clamp(maxi, 1, 7)



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
    plt.grid(visible=True, which='both', axis='both',
        data=(list(range(69)), list(range(45))))
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

def changed_interpolate_polyfit(row, config):
    import numpy as np
    
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

def changed_interpolate_quinn_2nd(row, config):
    # https://dspguru.com/dsp/howtos/how-to-interpolate-fft-peak/
    from math import sqrt, log
    def tau(x):
        return 1/4 * log(3 * x**2 + 6*x + 1) - sqrt(6)/24 * log((x + 1 - sqrt(2/3))  /  (x + 1 + sqrt(2/3)))
    
    # // assume the center component has the max amplitude
    maxi = int(IPTS_DFT_NUM_COMPONENTS / 2)
    # maxi = get_maxi(row)

    # // off-screen components are always zero, don't use them
    mind = -0.5
    maxd = 0.5

    if (row.iq[maxi - 1][REAL] == 0 and row.iq[maxi - 1][IMAG] == 0):
        maxi += 1
        mind = -1.0
    elif (row.iq[maxi + 1][REAL] == 0 and row.iq[maxi +1][IMAG] == 0):
        maxi -= 1
        maxd = 1.0
    # k =  index of the max (possibly local) magnitude of an DFT.
    # X[i]  =  bin “i” of an DFT |X[i]| =  magnitude of DFT at bin “i”.
    # k’  =  the interpolated bin location.
    X = row.iq
    k = maxi
    # ap = (X[k + 1].r * X[k].r + X[k+1].i * X[k].i)  /  (X[k].r * X[k].r + X[k].i * X[k].i)
    denom = (X[k][REAL] * X[k][REAL] + X[k][IMAG] * X[k][IMAG])
    if denom == 0:
        return float('nan')
    ap = (X[k + 1][REAL] * X[k][REAL] + X[k+1][IMAG] * X[k][IMAG])  /  denom
    if ap == 1:
        return float('nan')
    dp = -ap / (1 - ap)
    # am = (X[k – 1].r * X[k].r + X[k – 1].i * X[k].i)  /  (X[k].r * X[k].r + X[k].i * X[k].i)
    am = (X[k - 1][REAL] * X[k][REAL] + X[k - 1][IMAG] * X[k][IMAG])  /  (X[k][REAL] * X[k][REAL] + X[k][IMAG] * X[k][IMAG])
    if am == 1:
        return float('nan')
    dm = am / (1 - am)
    d = (dp + dm) / 2 + tau(dp * dp) - tau(dm * dm)
    # k’ = k + d
    return row.first + maxi + clamp(d, mind, maxd)

def changed_interpolate(row, config):
    # return changed_interpolate_quinn_2nd(row, config)
    # print(row)
    # maxi_override = get_maxi(row)
    # return cpp_interpolate_pos(row, config)
    # print(row)
    return changed_interpolate_polyfit(row, config)

def slanted_incontact_tip_loss_tip_y_row():
    row = Row(freq=1210480000, mag=510696, first=18, last=26, mid=22, zero=0, iq=[[33, 122], [53, 201], [94, 352], [150, 569], [186, 690], [230, 868], [159, 570], [89, 308], [49, 166]])
    print(row)
    config = IptsdConfig()

    tipx = changed_interpolate(row, config)
    print("tipx Should be around 22")
    print("tipx", tipx)

    row = Row(freq=1187205120, mag=419413, first=24, last=32, mid=28, zero=0, iq=[[1, 0], [0, 0], [-4, 8], [-39, 81], [-282, 583], [-15, 26], [4, -14], [5, -13], [4, -11]])
    penx = changed_interpolate(row, config)
    print("penx", penx)

    

    sys.exit()
# slanted_incontact_tip_loss_tip_y_row()



Scenario = namedtuple("Scenario", ["filename", "max_index", "interp", "min_index"])

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
        if r.type == DftType.IPTS_DFT_ID_POSITION2:
            x = interpolate(payload.x[0], config)
            y = interpolate(payload.y[0], config)
            pos_from_pos2.append([x,y])

            x = interpolate(payload.x[1], config)
            y = interpolate(payload.y[1], config)
            ring_pos_from_pos2.append([x,y])
            
        if r.type == DftType.IPTS_DFT_ID_POSITION:
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
    # print(m)

    pinv = np.linalg.pinv(m)
    # Perform Moore-Penrose pseudoinverse
    betas = pinv.dot(np.array(y))
    # print(betas)
    return betas

def make_poly(row, order):

    v = np.sqrt(square_iq(row))
    # v = np.power(np.sqrt(square_iq(row)), 0.7)

    maxi = get_maxi(row)


    # maxv = max(v)
    # weights = [np.power(z / maxv, 8) for z in v]
    # print("weights", weights)
    
    def gaussian(x, amplitude, mean, stddev):
        return amplitude * np.exp(-((np.array(x) - mean) / 4 / stddev)**2)

    # weights = [0, 0.3, 0.5,   1, 1, 1,  0.5, 0.3, 0]
    weights = list(gaussian(list(range(9)), 1.0, maxi, 0.7)) # ring
    # weights = np.hanning(9)
    
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
    pos_payload = frame[DftType.IPTS_DFT_ID_POSITION]
    pos2_payload = frame[DftType.IPTS_DFT_ID_POSITION2]
    pressure_payload = frame[DftType.IPTS_DFT_ID_PRESSURE]
    # print(pos_payload)

    freq = cpp_interpolate_frequency(pressure_payload, config)
    print(f"freq: {freq}")

    f_pos2 = cpp_interpolate_frequency(pos2_payload, config, maxi_override=1)
    print(f"f_pos2: {f_pos2}")

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


    if False:
        # Try the 'improve peak by ifft, zero pad, fft...'
        # do the fft shift to move center to [0]
        lshift = np.fft.ifftshift(pos_payload.x[0].iq)
        # Take the ifft
        data = np.fft.ifft(lshift)
        # print(data)
        # Now zero pad the data.
        # data.resize(data.size[0] * 2, data.size[1])
        data = np.vstack((data, np.zeros(data.shape)))
        # take the fft again
        bigfft = np.fft.fft(data)
        # print(bigfft)
        centered = np.fft.fftshift(bigfft)
        print(centered)

    show_plots(results, scatter)


def do_things_on_2_frame(before, after, interpolate_fun):

    print_things = False
    ri = 1

    print_things = True
    if print_things:
        print("Before:")
        these = (DftType.IPTS_DFT_ID_POSITION,)
        for k, v in sorted(before.items()):
            if not k in these:
                continue
            print(k)
            print_dft_rows(v)
        print("After:")
        for k, v in sorted(after.items()):
            if not k in these:
                continue
            print(k)
            print_dft_rows(v)

    pos_1 = before[DftType.IPTS_DFT_ID_POSITION]
    pos_2 = after[DftType.IPTS_DFT_ID_POSITION]
    # interpolator = changed_interpolate_quinn_2nd
    interpolator = changed_interpolate
    # interpolator = cpp_interpolate_pos
    x_1 = interpolator(pos_1.x[1], config)
    x_2 = interpolator(pos_2.x[1], config)
    print(x_1)
    print(x_2)
    y_1 = interpolator(pos_1.y[1], config)
    y_2 = interpolator(pos_2.y[1], config)
    print(y_1)
    print(y_2)

    results = {}
    scatter = {}
    scatter["x_cpp1"] = [cpp_interpolate_pos(pos_1.x[ri], config), 300]
    scatter["x_chng1"] = [changed_interpolate(pos_1.x[ri], config), 300]

    scatter["x_cpp2"] = [cpp_interpolate_pos(pos_2.x[ri], config), 300]
    scatter["x_chng2"] = [changed_interpolate(pos_2.x[ri], config), 300]

    def series(row):
        v = np.sqrt(square_iq(row))
        return list(zip([z+ row.first for z in range(9)], v))
    results["pos_1.x[ri]_data"] = series(pos_1.x[ri])
    results["pos_2.x[ri]_data"] = series(pos_2.x[ri])

    def series_iq(row, index):
        return list((z + row.first, row.iq[z][index]) for z in range(9))
    results["pos_1.x[ri].real"] = series_iq(pos_1.x[ri], REAL)
    results["pos_2.x[ri].real"] = series_iq(pos_2.x[ri], REAL)
    results["pos_1.x[ri].imag"] = series_iq(pos_1.x[ri], IMAG)
    results["pos_2.x[ri].imag"] = series_iq(pos_2.x[ri], IMAG)

    show_plots(results, scatter)


def test_pos():
    iq = [(    -8,    -3),(    -6,    -3),(     3,     2),(   202,   103),(   260,   133),(    -3,     1),(   -15,    -7),(   -13,    -6),(   -10,    -7),]

    frequency = 1187205120;
    magnitude = 85289;
    first = 28;
    last = 36;
    mid = 32;
    row = Row(freq=frequency, mag=magnitude, first=first, last=last, mid=mid, zero=0, iq=iq)

    config = IptsdConfig()
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

    z = changed_interpolate(row, config)
    sys.exit()

# test_pos()

def process_frames(frames, interpolate):
    result = {}
    def append(name, entry):
        if not name in result:
            result[name] = []
        result[name].append(entry)

    total_frames = len(frames)
    dx = 50.0 / total_frames
    y_offset = 20.0
    dy = 10.0

    for i, frame in enumerate(frames):
        if len(frame.items()) < 4:
            continue
        pos = frame[DftType.IPTS_DFT_ID_POSITION]
        pos2 = frame[DftType.IPTS_DFT_ID_POSITION2]
        pres = frame[DftType.IPTS_DFT_ID_PRESSURE]
        but = frame[DftType.IPTS_DFT_ID_BUTTON]

        def coord_interp(row, index):
            x = interpolate(row.x[index], config)
            y = interpolate(row.y[index], config)
            return [x,y]

        def coord_interp_cpp(row, index):
            x = cpp_interpolate_pos(row.x[index], config)
            y = cpp_interpolate_pos(row.y[index], config)
            return [x,y]


        append("pos_[0]", coord_interp(pos, 0))
        append("pos_[1]", coord_interp(pos, 1))
        append("cpp_pos_[1]", coord_interp_cpp(pos, 1))
        # append("pos_[4]", coord_interp(pos, 4))


        # append("pos2_[0]", coord_interp(pos2, 0))
        # append("pos2_[1]", coord_interp(pos2, 1))
        # append("pos2_[3]", coord_interp(pos2, 3))
        # append("pos2_[5]", coord_interp(pos2, 5))

        append("but_[3]", coord_interp(but, 3))


        # f_pos2 = cpp_interpolate_frequency(but, config, maxi_override=0)
        # append("f_pos2", [i * dx, f_pos2 * dy + y_offset])

        # append("pres_[2]", coord_interp(pres, 2))
        # append("pres_[3]", coord_interp(pres, 3))

    return result


def time_series_frames(frames):
    import matplotlib.pyplot as plt
    result = {}
    def append(name, entry):
        if not name in result:
            result[name] = []
        result[name].append(entry)

    total_frames = len(frames)
    dx = 50.0 / total_frames
    y_offset = 20.0
    dy = 10.0


    for i, frame in enumerate(frames):
        if len(frame.items()) < 4:
            continue
        pos = frame[DftType.IPTS_DFT_ID_POSITION]
        pos2 = frame[DftType.IPTS_DFT_ID_POSITION2]
        pres = frame[DftType.IPTS_DFT_ID_PRESSURE]
        but = frame[DftType.IPTS_DFT_ID_BUTTON]
        # print(pos.x)

        msg = pos
        # element = IMAG

        # append("phase_pos2_0", (i, pos2.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        # append("real_pos2_0", (i, pos2.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL]))
        # append("real_pos2_1", (i, pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL]))


        for element in (REAL, IMAG):
            for r in range(min(len(msg.x), 1)):
                # maxi = get_maxi(msg.x[r])
                maxi = int(IPTS_DFT_PRESSURE_ROWS / 2)
                #append(f"{comp_to_str(element)}_{element}_{r}", (i, msg.x[r].iq[maxi][element]))

        # append(f"{comp_to_str(element)}_real_{r}", (i, msg.x[r].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL]))
        # append(f"{comp_to_str(element)}_imag_{r}", (i, msg.x[r].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))

        r = 0
        # append(f"iq_const_{r}:*", (pos.x[r].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[r].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))

        # This is very circular.
        # append(f"pos_iq_const_0:*", (pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        # So is this;
        # append(f"pos2_iq_const_1:*", (pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))


        # This is surprisingly in the top half plane.
        # append(f"pos_0_iq:*", (pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))


        # This spirals...
        # append(f"pos2_0_iq:*", (pos2.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))

        # append(f"{comp_to_str(element)}_const:*", (msg.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG], msg.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        # append(f"{comp_to_str(element)}_const:*", (msg.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG], msg.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL]))


        # append(f"pos_0_iq:*", (pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))

        i = 1
        append(f"pos_iq_const_1:*", (pos.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        append(f"pos2_iq_const_1:*", (pos2.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))


    def plot(name):
        p = np.array(result[name])
        if name.endswith("*"):
            plt.scatter(p[:, 0], p[:, 1], c=range(p.shape[0]), label=name)
            plt.plot(p[:, 0], p[:, 1], label=name, linewidth=0.3)
        else:
            plt.plot(p[:, 0], p[:, 1], label=name)

    for k in result.keys():
        plot(k)

    plt.legend()
    plt.show()



def print_data(d):
    for i, r in enumerate(d):
        payload = r.payload
        if r.type in (DftType.IPTS_DFT_ID_POSITION, DftType.IPTS_DFT_ID_POSITION2,  DftType.IPTS_DFT_ID_BUTTON,  DftType.IPTS_DFT_ID_PRESSURE):
            print(r.type)
            print("Rows: ")
            for r in range(payload.rows):
                print(f"x[{r}]", payload.x[r])
            print()
            for r in range(payload.rows):
                print(f"y[{r}]", payload.y[r])

def print_frame(frame):
    for k, v in sorted(frame.items()):
        print(k)
        print_dft_rows(v)


def make_frames(d):
    frames = []
    frame = { }
    for z in d:
        frame[z.type] = z.payload
        # if z.type == DftType.IPTS_DFT_ID_BUTTON:
        # if z.type == DftType.IPTS_DFT_ID_POSITION2:
        if z.type == DftType.IPTS_DFT_ID_POSITION:
        # if z.type == DftType.IPTS_DFT_ID_PRESSURE:
            frames.append(frame)
            frame = {}
    return frames


test_scenarios = {
    "slanted_incontact_tip_loss_orig":Scenario("./slanted_incontact.json.gz", max_index=73, interp=cpp_interpolate_pos, min_index=0),
    "slanted_incontact_tip_loss_orig_full":Scenario("./slanted_incontact.json.gz", max_index=1e6, interp=cpp_interpolate_pos, min_index=0),
    "slanted_incontact_tip_loss_new":Scenario("./slanted_incontact.json.gz", max_index=73, interp=changed_interpolate, min_index=0),
    "slanted_incontact_tip_loss_new_full":Scenario("./slanted_incontact.json.gz", max_index=1e6, interp=changed_interpolate, min_index=0),
    "spiral_out_loss_full":Scenario("./spiral_out.json.gz", max_index=1e6, interp=cpp_interpolate_pos, min_index=0),
    "spiral_out_full":Scenario("./spiral_out.json.gz", max_index=1e6, interp=cpp_interpolate_pos, min_index=0),
    "spiral_out_new_full":Scenario("./spiral_out.json.gz", max_index=1e6, interp=changed_interpolate, min_index=0),
    "diagonal":Scenario("./diagonal.json.gz", max_index=1e6, interp=changed_interpolate, min_index=0),
    "diagonal_quin":Scenario("./diagonal.json.gz", max_index=1e6, interp=changed_interpolate_quinn_2nd, min_index=0),
    "diag_win":Scenario("../irp_logs_thcbase/2024_02_04_intelthcbase_bootlog_diagonal_wiggle_linux.json.gz", min_index=900, max_index=1302, interp=changed_interpolate),
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
    

def perform_signal_processing(frames):
    import numpy as np
    import matplotlib.pyplot as plt
    result = {}
    def append(name, entry):
        if not name in result:
            result[name] = []
        result[name].append(entry)

    total_frames = len(frames)
    dx = 50.0 / total_frames
    y_offset = 20.0
    dy = 10.0

    for i, frame in enumerate(frames):
        if len(frame.items()) < 4:
            continue
        if (i == 115):
            print_frame(frame)

        pos = frame[DftType.IPTS_DFT_ID_POSITION]
        pos2 = frame[DftType.IPTS_DFT_ID_POSITION2]
        pres = frame[DftType.IPTS_DFT_ID_PRESSURE]
        but = frame[DftType.IPTS_DFT_ID_BUTTON]


        # These are definitely circular.
        # append(f"pos_iq_const_1:*", (pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        # append(f"pos_iq_const_1_+1:*", (pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2) + 1][REAL], pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2) + 1][IMAG]))
        # append(f"pos_iq_const_1_-1:*", (pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2) - 1][REAL], pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2) - 1][IMAG]))
        # append(f"pos2_iq_const_1:*", (pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))

        # From that we can extract a wrapped phase;
        angle_pos = np.arctan2(pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG], pos.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL])
        angle_pos2 = np.arctan2(pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG], pos2.x[1].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL])
        append(f"angle_pos1:*", (i, angle_pos))
        append(f"angle_pos2:*", (i, angle_pos2))

        spiralling_pos2_zero = (pos2.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG])
        # What happens if we rotate that by the pos2 phase?
        # {\displaystyle R={\begin{bmatrix}\cos \theta &-\sin \theta \\\sin \theta &\cos \theta \end{bmatrix}}}
        def R(a):
            return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        z = R(angle_pos2).T.dot(np.array(spiralling_pos2_zero))
        # append(f"pos2_0_iq_rot:*", z)
        # Coincidence?! I think not.
        # append(f"pos_0_iq:*", (pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[0].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
    

        def row_manip(row):
            # Lets rotate the iq by angle.
            for r in range(IPTS_DFT_PRESSURE_ROWS):
                c_p = [row.iq[r][IMAG], row.iq[r][REAL]]
                n = R(-angle_pos).T.dot(c_p)
                print(n)
                row.iq[r][IMAG] = n[0]
                row.iq[r][REAL] = n[1]

        def coord_interp(row, index):
            x_z = row.x[index]
            y_z = row.y[index]
            # row_manip(x_z)
            # row_manip(y_z)
            x = interpolate(x_z, config)
            y = interpolate(y_z, config)
            return [x,y]

        # lets make that line straight.
        # Goes through
        top_left = (8.916, 41.388)
        bottom_right = (22.8, 30.43)
        dx = top_left[0] - bottom_right[0]
        dy = top_left[1] - bottom_right[1]
        l_angle = np.arctan2(dx, dy)
        p = coord_interp(pos, 0)
        v = R(l_angle  +np.pi / 2).dot(p)
        # append(f"position", v)
        append(f"position_rot", (i, (v[1] - 37) * 10.0) )
        append(f"position", p)
        append(f"coord_interp(pos2, 1)", coord_interp(pos2, 1))
        append(f"coord_interp(pos, 1)", coord_interp(pos, 1))
        append(f"coord_interp(pos, 0)", coord_interp(pos, 0))


    # calculate delta of phase
    

    def plot(name):
        p = np.array(result[name])
        if name.endswith("*"):
            plt.scatter(p[:, 0], p[:, 1], c=range(p.shape[0]), label=name)
            plt.plot(p[:, 0], p[:, 1], label=name, linewidth=0.3)
        else:
            plt.plot(p[:, 0], p[:, 1], label=name)

    for k in result.keys():
        plot(k)

    plt.legend()
    plt.show()

if __name__ == "__main__":
    # Metadata(size=MetataSize(rows=46, columns=68, width=27389, height=18259), transform=MetataTransform(xx=408.791, yx=0, tx=0, xy=0, yy=405.756, ty=0))
    default_interpolate = changed_interpolate
    # default_interpolate = changed_interpolate_quinn_2nd
    # default_interpolate = cpp_interpolate_pos
    scenario = test_scenarios.get(sys.argv[1], Scenario(sys.argv[1], max_index=None, min_index=None, interp=default_interpolate))

    d = iptsd_json_load(scenario.filename)
    interpolate = scenario.interp
    print(interpolate.__name__)


    frames = make_frames(d)
    print(f"Total frames: {len(frames)}")
    if scenario.max_index is not None:
        frames = frames[:int(scenario.max_index)]
    if scenario.min_index is not None:
        frames = frames[int(scenario.min_index):]
    print(f"Final frames: {len(frames)}")

    metadata = get_metadata(d)
    print(metadata)
    config = IptsdConfig()

    do_full = False
    do_full_frames = False
    do_on_frame = False
    do_comparison = False
    print_kernels = False
    do_on_two_frame = False
    plot_time_series = False
    do_on_cpp_interpolate = False
    do_signal_processing = False


    # do_full = True
    if do_full:
        res = process_data(d, interpolate)
        # print_data(d)
        s = process_single_frame(frames[190], interpolate)
        res["OURMARKER*"] = s["ring_pos_from_pos"]
        show_trajectory(res)

    # do_on_cpp_interpolate = True
    if do_on_cpp_interpolate:
        res = process_data(d, cpp_interpolate_pos)
        z = {}
        z["pos_from_pos"] = res["pos_from_pos"]
        z["ring_pos_from_pos"] = res["ring_pos_from_pos"]
        show_trajectory(z)


    # do_comparison = True
    if do_comparison:
        keys = [
            "pos_from_pos",
            "ring_pos_from_pos",
            # "pos_from_pos2",
            # "ring_pos_from_pos2",
        ]
        compare_scenario(d, cpp_interpolate_pos, interpolate, keys)


    f1_diag_centerchange = 188
    f2_diag_centerchange = f1_diag_centerchange + 1

    f1_diag_erratic = 158
    f2_diag_erratic = f1_diag_erratic + 1

    f1_not_diagonal = 129
    f2_not_diagonal = f1_not_diagonal + 1

    # in diag_win
    f1_not_diagonal = 124
    f2_not_diagonal = f1_not_diagonal + 1

    f1 = f1_not_diagonal
    f2 = f1_not_diagonal


    # do_on_frame = True
    if do_on_frame:
        # print("Frames: ", len(frames))
        f = frames[f1]
        # print(f)

        res = do_things_on_frame(f, interpolate)


    # do_on_two_frame = True
    if do_on_two_frame:
        # print("Frames: ", len(frames))
        before = frames[f1]
        after = frames[f2]
        # print(f)

        res = do_things_on_2_frame(before, after, interpolate)


    # do_full_frames = True
    if do_full_frames:
        res = process_frames(frames, interpolate)
        # print_data(d)
        s = process_single_frame(frames[f1], interpolate)
        # print(s)
        res["OURMARKER*"] = s["ring_pos_from_pos"]
        s = process_single_frame(frames[f2], interpolate)
        res["MARK2*"] = s["ring_pos_from_pos"]
        res["MARK3*"] = s["pos_from_pos"]
        show_trajectory(res)

    # print_kernels = True
    if print_kernels:
        def gaussian(x, amplitude, mean, stddev):
            return amplitude * np.exp(-((np.array(x) - mean) / 4 / stddev)**2)

        print("static constexpr Weights gaussian_at_4_stddev_0_4 {{{}}};".format(", ".join(f"{x}" for x in gaussian(list(range(9)), 1.0, 4, 0.4))))
        print("static constexpr Weights gaussian_at_4_stddev_0_7 {{{}}};".format(", ".join(f"{x}" for x in gaussian(list(range(9)), 1.0, 4, 0.7))))


    # plot_time_series = True
    if plot_time_series:
        # Maybe we need to extract out some modulation that the now-active pen does?
        time_series_frames(frames)

    do_signal_processing = True
    if do_signal_processing:
        perform_signal_processing(frames)
    
        

