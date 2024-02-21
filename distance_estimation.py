#!/usr/bin/env python3

# Attempt at using the DigiInfo together with the two position estimates to
# actually calculate the distance between the tip emitter and tilt emitter.
# Didn't really pan out as the DigiInfo tilt data seems to be updating
# infrequently.

import sys
import math
import shelve


from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, clamp, obtain_state
from ground_truth import generalise_digi, wintilt_to_yaw_tilt
from digi_info import load_digiinfo_xml


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

def run_estimate_distances(args):
    states = cached_calc(args)


    # from analyse import show_trajectory
    # xy_state = [(state["x"], state["y"]) for state in states if bool(state)]
    # xy_truth = [(state["digi"].x, state["digi"].y) for state in states if "digi" in state]
    # show_trajectory({'xy_state': xy_state, 'xy_truth': xy_truth})
    # add_edges(states)


    pressed = []
    for state in states:
        if "pressure" in state and state["pressure"] != 0.0 and "yt" in state and abs(state["yt"]) < 1e6:
            pressed.append(state)

    if args.skip_start:
        pressed = pressed[args.skip_start:]
    if args.skip_end:
        # print(args.skip_end)
        # print(len(states))
        pressed = pressed[:-args.skip_end]
        # print(len(pressed))
        # lj

    # L = 2.0
    for state in pressed:
        # Project to local frame

        digi_yaw, digi_tilt = wintilt_to_yaw_tilt(state["digi"].x_t, state["digi"].y_t)


        # print(state)
        xl = state["xt"] - state["x"]
        yl = state["yt"] - state["y"]
        state["xl"] = xl
        state["yl"] = yl

        yaw = math.atan2(yl, xl)
        hypot = math.sqrt(xl * xl + yl * yl)
        # print(f"Yaw: {yaw}  digi yaw: {digi_yaw}")

        # if (hypot > L):
            # hypot = float("nan")
        # hypot = clamp(hypot, 0, L)

        # We know that the actual length doesn't change
        # alpha = math.acos(hypot / L)
        L = hypot / math.cos(digi_tilt)
        print(L)
        alpha = digi_yaw
        # beta = math.sin(alpha) * L
        state["beta"] = digi_tilt
        
    xs = [p["xl"] for p in pressed]
    ys = [p["yl"] for p in pressed]
    zs = [p["beta"] for p in pressed]

    # print(xs)

    # sys.exit(0)
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
    compare_parser.add_argument("--skip-start", help="Indicies to skip at the start", type=int, default=0)
    compare_parser.add_argument("--skip-end", help="Indicies to skip at the end", type=int, default=None)
    compare_parser.add_argument("--digi", help="estimate ground truth digitizer file to open.")
    compare_parser.add_argument("--iptsd", help="The iptsd dump to use.")
    compare_parser.set_defaults(func=run_estimate_distances)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)


