#!/usr/bin/env python3

from digi_info import load_digiinfo_xml
from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowButton, IptsPenGeneral, IPTS_COLUMNS, IPTS_ROWS, IPTS_WIDTH, IPTS_HEIGHT
from iptsd import iptsd_json_load
import os

# Generalised pen state.
from collections import namedtuple

PenState = namedtuple("PenState", ["x", "y", "proximity", "contact", "rubber", "button", "x_t", "y_t"])

def generalise_digi(events):
    output = []
    for e in events:
        updated = {
            "proximity": e.inrange,
            "contact": e.down,
            "rubber": e.eraser,
            "button": e.barrel,
            "x": e.x,
            "y": e.y,
            "x_t": e.tiltx,
            "y_t": e.tilty,
        }
        output.append(PenState(**updated))
    return output

def generalise_iptsd_json(events):
    output = []
    def get_metadata(d):
        for z in d:
            if z.type == "METADATA":
                return z.payload
    metadata = get_metadata(events)
    print(metadata)
    for e in events:
        if (e.type == "STYLUS_DATA"):
            updated = {k: getattr(e.payload, k) for k in PenState._fields}
            updated["x"] = updated["x"] * metadata.size.width
            updated["y"] = updated["y"] * metadata.size.height
        output.append(PenState(**updated))
    return output


def plot_trajectory(trajectories):
    import matplotlib.pyplot

    f = matplotlib.pyplot.figure()
    ax = f.add_subplot(111)

    def _mask_pos_by_fun(pos, events, f):
        z = pos[:]
        for x, event in zip(z, events):
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
        ax.plot(_x(xy_contact), _y(xy_contact), color=color, label=name)
    


    ax.set_xlim([0, IPTS_WIDTH])
    ax.set_ylim([0, IPTS_HEIGHT])
    ax.legend(loc="upper right")


    ax.set_aspect('equal', adjustable='box')
    ax.grid(visible=True, which='both', axis='both',
        data=(list(range(IPTS_COLUMNS + 1)), list(range(IPTS_ROWS + 1))))
    return f


def run_compare(args):
    entries = {}

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

