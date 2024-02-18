#!/usr/bin/env python3

import sys
import math

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, process_position, process_pressure

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

        # We know that the actual length doesn't change
        L = 2.0
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
    ax.scatter(xs, ys, zs)
    plt.show()


