#!/usr/bin/env python3

# First attempt at a different button detection, but without all the insights
# from the spectrograms. So probably useless now.

import sys
import json

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, group_reports, IPTS_DFT_NUM_COMPONENTS
from iptsd import IptsdConfig, clamp, obtain_state, write_states, _convert_row

def load_relevant(fname, config=IptsdConfig()):
    z = iptsd_read(fname)
    report_types = set([IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure])
    reports = extract_reports(z, report_types)
    grouped = group_reports(reports, report_types)
    states = obtain_state(grouped, insert_group = True, config=config)
    return states


# This glitches between eraser and barrel.
def changed_button_detection(dft_button, dft_position, config=IptsdConfig()):
    res = {}
    return res
    if dft_button.header.num_rows <= 0:
        return None


    mid = int(IPTS_DFT_NUM_COMPONENTS / 2)

    # prowx = _convert_row(dft_position.x[0])
    # prowy = _convert_row(dft_position.y[0])
    m_real = dft_position.x[0].real[mid] + dft_position.y[0].real[mid]
    m_imag = dft_position.x[0].imag[mid] + dft_position.y[0].imag[mid]

    # Find the highest magnitude in all the rows.
    print()
    rows = dft_button.header.num_rows
    xmags = [dft_button.x[i].magnitude for i in range(rows)]
    ymags = [dft_button.y[i].magnitude for i in range(rows)]

    real = dft_position.x[0].real[mid] + dft_position.y[0].real[mid]
    imag = dft_position.x[0].imag[mid] + dft_position.y[0].imag[mid]

    print(xmags)
    print(ymags)
    highest = max(xmags + ymags)
    half = highest / 2
    as_bits = [xmags[i] > half for i in range(rows)]
    print(as_bits)

    val = m_real * real + m_imag * imag
    active = as_bits[0] and not as_bits[2] and not as_bits[3]

    res["button"] = False
    res["eraser"] = False
    if (dft_button.x[0].magnitude > config.dft_button_min_mag and dft_button.y[0].magnitude > config.dft_button_min_mag):
        if active:
            if val > 0:
                res["button"] = True
                res["eraser"] = False
            else:
                res["button"] = False
                res["eraser"] = True

    return res

def changed_button(groups, config):
    res = {}
    res.update(changed_button_detection(groups[IptsDftWindowButton], groups[IptsDftWindowPosition], config))
    return res

def run_changes(states, config):
    z = []
    for state in states:
        state.update(changed_button(state["group"], config))
        z.append(state)
    return z

def run_changed(args):
    config = IptsdConfig()
    config.dft_button_min_mag = 1000
    states = load_relevant(args.input, config=config)

    write_states(args.output_orig, states)

    modified_states = run_changes(states, config=config)

    write_states(args.output, modified_states)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser('changed')
    compare_parser.add_argument("input", help="The input binary data.")
    compare_parser.add_argument("--output-orig", help="The orginal data to write.", default="/tmp/unmodified_states.json")
    compare_parser.add_argument("--output", help="The output to write.", default="/tmp/modified_states.json")
    compare_parser.set_defaults(func=run_changed)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)
