#!/usr/bin/env python3

import sys
import math
import shelve

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, process_position, process_pressure, clamp
from ground_truth import generalise_digi
from digi_info import load_digiinfo_xml

def obtain_state(grouped):
    records = []
    for group in grouped:
        current = {}
        pos = process_position(group[IptsDftWindowPosition])
        if pos:
            current.update(pos)
        else:
            continue
        pressure = process_pressure(group[IptsDftWindowPressure])

        if pressure:
            current.update(pressure)

        records.append(current)
    return records

def euclid(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)

def naive_correlator(states, digi):
    def find_best_digi(sp, start=0):
        dist = float("inf")
        best_i = None
        for i in range(start, len(digi)):
            c = digi[i]
            dp = (c.x, c.y)
            newdist = euclid(sp, dp)
            if newdist < dist:
                best_i = i
                dist = newdist
        return best_i
        
    digi_i = 0
    for state in states:
        dx = state["xt"] - state["x"]
        dy = state["yt"] - state["y"]
        yaw = math.atan2(dy, dx)
        sp = (state["x"], state["y"])
        di = find_best_digi(sp, digi_i)
        if di:
            state["digi"] = digi[di]
            # digi_i = di
     
def add_edges(states, show=True):
    import matplotlib.pyplot as plt
    x = []
    y = []
    for state in states:
        if not "digi" in state:
            continue
        x.append(state["x"])
        x.append(state["digi"].x)
        x.append(float("nan"))
        y.append(state["y"])
        y.append(state["digi"].y)
        y.append(float("nan"))   

    plt.plot(x, y)
    if show:
        plt.show()

def cached_calc(args):
    v = 0
    key = f"{args.iptsd}_{args.digi}_{v}"
    with shelve.open('/tmp/distance_cache.shelf') as db:
        if key in db:
            return db[key]
        else:
            z = iptsd_read(args.iptsd)
            report_types = set([IptsDftWindowPosition, IptsDftWindowPressure])
            reports = extract_reports(z, report_types)
            truth = generalise_digi(load_digiinfo_xml(args.digi), rowcol=True)
            grouped = group_reports(reports, report_types)
            states = obtain_state(grouped)

            naive_correlator(states, truth)
            db[key] = states
            return states

def wintilt_to_yaw_tilt(xtilt_deg, ytilt_deg):
    # def R(a):
    #    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    xtilt = math.radians(xtilt_deg)
    ytilt = math.radians(ytilt_deg)
    # print(f"xtilt; {xtilt} ytilt {ytilt}")
    # Lets just calculate the normal vectors of the two planes

    # For xtilt, rotating the X axis by tiltx gives us the normal.
    xtilt_x = math.cos(xtilt)
    xtilt_y = -math.sin(xtilt)
    xtilt_z = 0

    # For ytilt, rotating the y axis by tilty gives us the normal
    ytilt_x = 0
    ytilt_y = math.cos(ytilt)
    ytilt_z = -math.sin(ytilt)

    # Now we can take the crossproduct to get the line vector.
    def cross(a, b):
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        ]

    a = [xtilt_x, xtilt_y, xtilt_z]
    b = [ytilt_x, ytilt_y, ytilt_z]
    
    linedir = cross(a, b)
    # print(linedir)

    # Which is a position in xyz, so now the yaw and tilt just drop out
    yaw = math.atan2(linedir[1], linedir[0])
    hypot = math.sqrt(linedir[0]**2 + linedir[1]**2)
    tilt = math.atan2(linedir[2], hypot)

    # print(f"yaw {yaw}  tilt {tilt}  ")
    return (yaw, tilt)

if False:
    def near(a, b, resolution=0.001):
        for i in range(1):
            if abs(a[i] - b[i]) > resolution:
                raise BaseException(f"Failed: {a[i]} differs from {b[i]} at dim {i}")
            else:
                print(f"Pass: {a[i]} equal to {b[i]} on dim {i}  ")
        print()

    near(wintilt_to_yaw_tilt(0, 0), (0, -math.pi / 2))
    near(wintilt_to_yaw_tilt(45, 0), (0, math.radians(45)))
    near(wintilt_to_yaw_tilt(0, 45), (math.radians(90), math.radians(45)))
    near(wintilt_to_yaw_tilt(45, 45), (math.radians(45), math.radians(45)))

    near(wintilt_to_yaw_tilt(-45, 0), (math.pi, -math.radians(45)))
    near(wintilt_to_yaw_tilt(0, -45), (-math.radians(90), math.radians(45)))
    near(wintilt_to_yaw_tilt(-45, -45), (-math.radians(45), math.radians(45)))
    sys.exit(1)

def run_estimate_distances(args):
    states = cached_calc(args)

    from analyse import show_trajectory
    xy_state = [(state["x"], state["y"]) for state in states if bool(state)]
    xy_truth = [(state["digi"].x, state["digi"].y) for state in states if "digi" in state]
    show_trajectory({'xy_state': xy_state, 'xy_truth': xy_truth})
    add_edges(states)


    pressed = []
    for state in states:
        if "pressure" in state and state["pressure"] != 0.0 and "yt" in state and abs(state["yt"]) < 1e6:
            pressed.append(state)


    L = 2.0
    for state in pressed:
        # Project to local frame
        print(state)
        xl = state["xt"] - state["x"]
        yl = state["yt"] - state["y"]
        state["xl"] = xl
        state["yl"] = yl

        yaw = math.atan2(yl, xl)
        hypot = math.sqrt(xl * xl + yl * yl)
        print(f"Hypot: {hypot}")

        if (hypot > L):
            hypot = float("nan")
        # hypot = clamp(hypot, 0, L)

        # We know that the actual length doesn't change
        alpha = math.acos(hypot / L)
        beta = math.sin(alpha) * L
        state["beta"] = beta
        
    xs = [p["xl"] for p in pressed]
    ys = [p["yl"] for p in pressed]
    zs = [p["beta"] for p in pressed]

    # print(xs)

    import matplotlib.pyplot as plt
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_aspect('equal')
    ax.scatter(xs, ys, zs)
    ax.set_xlim3d([-L, L])
    ax.set_ylim3d([-L, L])
    ax.set_zlim3d([0, 2*L])
    # fig.axis('equal')
    # ax.set_box_aspect([1,1,1])


    # We don't know height
    # We don't know the used angle ranges.
    # A meter long pole will only cause small 'd' shadows if used with
    # A small angle deviation.

    # In short, we need more data.

    draw_circle = False
    # draw_circle = True
    if draw_circle:
        import numpy as np
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x = L * np.outer(np.cos(u), np.sin(v))
        y = L * np.outer(np.sin(u), np.sin(v))
        z = L * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.scatter(x, y, z)

    plt.show()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser('estimate')
    compare_parser.add_argument("--digi", help="estimate ground truth digitizer file to open.")
    compare_parser.add_argument("--iptsd", help="The iptsd dump to use.")
    compare_parser.set_defaults(func=run_estimate_distances)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)


