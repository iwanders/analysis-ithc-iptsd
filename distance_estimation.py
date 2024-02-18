#!/usr/bin/env python3

import sys
import math

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, process_position, process_pressure, clamp
from ground_truth import 
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


if __name__ == "__main__":
    z = iptsd_read(sys.argv[1])
    report_types = set([IptsDftWindowPosition, IptsDftWindowPressure])
    reports = extract_reports(z, report_types)


    grouped = group_reports(reports, report_types)
    states = obtain_state(grouped)

    # from analyse import show_trajectory
    # xy = [(state["x"], state["y"]) for state in states if bool(state)]
    # show_trajectory({'xy': xy})

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

    print(xs)

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


