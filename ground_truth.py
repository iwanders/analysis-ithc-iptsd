#!/usr/bin/env python3

from digi_info import load_digiinfo_xml
from ipts import  IPTS_COLUMNS, IPTS_ROWS, IPTS_WIDTH, IPTS_HEIGHT
from iptsd import iptsd_json_load
import os
import copy
import math

# Generalised pen state.
from collections import namedtuple

PenState = namedtuple("PenState", ["x", "y", "proximity", "contact", "eraser", "button", "x_t", "y_t"])

# Yaw is x = 0, standard counter clockwise.
# Tilt is between screen and pen, not between perpendicular and pen.
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


def generalise_digi(events, rowcol=False):
    output = []
    x_scale = ((IPTS_COLUMNS - 1) / IPTS_WIDTH) if rowcol else 1.0
    y_scale = ((IPTS_ROWS - 1) / IPTS_HEIGHT) if rowcol else 1.0
    for e in events:
        updated = {
            "proximity": e.inrange,
            "contact": e.pressure != 0,
            "eraser": e.eraser,
            "button": e.barrel,
            "x": e.x * x_scale,
            "y": e.y * y_scale,
            # <property name="tiltx" logmin="0" logmax="18000" res="100" unit="deg" />
            # <property name="tilty" logmin="0" logmax="18000" res="100" unit="deg" />
            # tiltx and tilty appear to be in in an angle? 18000 / 100 = 180?
            # see https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/required-hid-top-level-collections#x-tilt
            "x_t": e.tiltx / 100.0,
            "y_t": e.tilty / 100.0,
        }
        output.append(PenState(**updated))
    return output

def generalise_iptsd_json(events, rowcol=False):
    output = []
    x_scale = ((IPTS_COLUMNS - 1) / IPTS_WIDTH) if rowcol else 1.0
    y_scale = ((IPTS_ROWS - 1) / IPTS_HEIGHT) if rowcol else 1.0
    def get_metadata(d):
        for z in d:
            if z.type == "METADATA":
                return z.payload
    metadata = get_metadata(events)
    for e in events:
        if (e.type == "STYLUS_DATA"):
            updated = {k: getattr(e.payload, {"eraser":"rubber"}.get(k, k)) for k in PenState._fields}
            updated["x"] = updated["x"] * metadata.size.width  * x_scale
            updated["y"] = updated["y"] * metadata.size.height * y_scale
            updated["x_t"] = updated["x_t"] * metadata.size.width* x_scale
            updated["y_t"] = updated["y_t"] * metadata.size.height * y_scale
        output.append(PenState(**updated))
    return output


def plot_trajectory(trajectories):
    import matplotlib.pyplot

    f = matplotlib.pyplot.figure()
    ax = f.add_subplot(111)

    def _mask_pos_by_fun(pos, events, f):
        z = copy.deepcopy(pos)
        for x, event in zip(z, events):
            # dsflkjdsflkjdsf = f(event)
            # print(bool(dsflkjdsflkjdsf))
            if not f(event):
                x[0] = float("nan")
                x[1] = float("nan")
        return z

    def _x(v):
        return [a[0] for a in v]
    def _y(v):
        return [a[1] for a in v]

    # Hover (or hover + contact), faint line
    # Contact; plus
    # Side: triangle
    # Eraser: square
    for name, spec in trajectories.items():
        events = spec["events"]
        color = spec.get("properties", {}).get("color", "black")
        # First, obtain the xy vectors.
        # print(events)
        xy = [[v.x, v.y] for v in events]
        # print(xy)
        xy_contact = _mask_pos_by_fun(xy, events, lambda a: a.contact)
        xy_proximity = _mask_pos_by_fun(xy, events, lambda a: a.proximity)

        xy_eraser = _mask_pos_by_fun(xy, events, lambda a: a.eraser)
        xy_button = _mask_pos_by_fun(xy, events, lambda a: a.button)

        ax.plot(_x(xy_contact), _y(xy_contact), color=color, label=f"{name}")
        ax.plot(_x(xy_proximity), _y(xy_proximity), color=color, label=f"{name}_prox", linewidth=0.2, alpha=0.5)
        ax.plot(_x(xy_eraser), _y(xy_eraser), color=color, label=f"{name}_eraser", linewidth=None, marker="s", alpha=0.5, markersize=4, markerfacecolor='none')
        ax.plot(_x(xy_button), _y(xy_button), color=color, label=f"{name}_button", linewidth=None, marker="v", alpha=1.0, markersize=4, markerfacecolor='none')    

        #xyt = [[v.x_t, v.y_t] for v in events]
        # ax.plot(_x(xyt), _y(xyt), color=color, label=f"{name}_tilt", linestyle=":", linewidth=1.0, alpha=1.0)
        # do something with tilt.
        tilts = []
        for v in events:
            if v.x_t == 0.0 and v.y_t == 0.0:
                continue
            yaw, tilt = wintilt_to_yaw_tilt(v.x_t, v.y_t)
            # print(f"{yaw: >.5f}  {tilt: >.5f} {v}")
            tilts.append([v.x, v.y])
            R = 1000
            length = math.cos(tilt) * R
            tilts.append([v.x + math.cos(yaw) * length, v.y + math.sin(yaw) * length])
            tilts.append([float("nan"), float("nan")])
        ax.plot(_x(tilts), _y(tilts), color=color, label=f"{name}_tilt", linewidth=0.5, linestyle="--", alpha=0.75)
        

    ax.set_xlim([0, IPTS_WIDTH])
    ax.set_ylim([0, IPTS_HEIGHT])
    ax.legend(loc="upper right")


    ax.set_aspect('equal', adjustable='box')
    ax.grid(visible=True, which='both', axis='both',
        data=(list(range(IPTS_COLUMNS + 1)), list(range(IPTS_ROWS + 1))))
    return f


def relator(iptsd, digi):
    # Digi is the ground truth and high res.
    digi_i = 0
    iptsd_i = 0

    def advance_digi_until(pred):
        nonlocal digi_i
        while digi_i < len(digi) and not pred(digi[digi_i]):
            digi_i += 1
    def advance_ipstd_until(pred):
        nonlocal iptsd_i
        while iptsd_i < len(iptsd) and not pred(iptsd[iptsd_i]):
            iptsd_i += 1

    # Find the first index where both declare contact.
    advance_digi_until(lambda z: z.contact)
    advance_ipstd_until(lambda z: z.contact)
    print(f"First contacts digi: {digi_i} iptsd: {iptsd_i}")

    def d(a, b):
        dx = b.x - a.x
        dy = b.y - a.y
        return dx * dx + dy * dy

    matched_indices = []

    distance_limit = 5000

    iptsd_advances_without_digi_i = 0;
    # Goal; for each iptsd, find the two indices into digid that surround it
    while digi_i < len(digi) and iptsd_i < len(iptsd):
        prev_digi_i = digi_i
        prev_iptsd_i = iptsd_i

        distance = d(digi[digi_i], iptsd[iptsd_i])
        ndistance = d(digi[digi_i + 1], iptsd[iptsd_i])
        if ndistance < distance:
            digi_i += 1
            iptsd_advances_without_digi_i = 0
        else:
            if distance < distance_limit:
                matched_indices.append((iptsd_i, digi_i))
            iptsd_advances_without_digi_i += 1
            iptsd_i += 1

        if iptsd_advances_without_digi_i > 5:
            # Well... problem here.
            digi_i += 1
            advance_digi_until(lambda z: z.contact or z.button)
            advance_ipstd_until(lambda z: z.contact or z.button)
            iptsd_advances_without_digi_i = 0

        # if (digi_i == 1964 and iptsd_i > 3600):
            # break;
        # if len(matched_indices) > 1000:
            # break
        

    # for d in matched_indices:
        # print(d)
    return matched_indices
        

def add_edges(fig, iptsd, digi, indices):
    x = []
    y = []
    for iptsd_i, digi_i in indices:
        if iptsd_i >= len(iptsd) or digi_i >= len(digi):
            break
        x.append(digi[digi_i].x)
        x.append(iptsd[iptsd_i].x)
        x.append(float("nan"))
        y.append(digi[digi_i].y)
        y.append(iptsd[iptsd_i].y)
        y.append(float("nan"))
    fig.axes[0].plot(x, y)
    

def run_compare(args):
    entries = {}

    digi_events = None
    iptsd_json = None

    if args.digi:
        digi_events = generalise_digi(load_digiinfo_xml(args.digi))
        entries[os.path.basename(args.digi)] = {
            "events":digi_events,
            "properties":{"color": "red"}
        }
    if args.json:
        iptsd_json = generalise_iptsd_json(iptsd_json_load(args.json))
        entries[os.path.basename(args.json)] = {
            "events":iptsd_json,
            "properties":{"color": "green"}
        }


    f = plot_trajectory(entries)
    if digi_events and iptsd_json:
        edges = relator(iptsd_json, digi_events)
        add_edges(f, iptsd_json, digi_events, edges)



    import matplotlib.pyplot as plt
    plt.show()

    
    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser('compare')
    compare_parser.add_argument("--digi", help="The ground truth digitizer file to open.")
    compare_parser.add_argument("--json", help="The iptsd json file to use.")
    compare_parser.set_defaults(func=run_compare)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)

