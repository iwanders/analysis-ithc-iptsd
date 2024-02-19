#!/usr/bin/env python3

import sys
import json

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, clamp, obtain_state, write_states, _convert_row
# from generalised import generalise_digi, wintilt_to_yaw_tilt
from digi_info import load_digiinfo_xml

def print_dft(d, row_limit=9999):
    def format_r(r):
        combs = [f"{r.real[i]: >4}, {r.imag[i]: >4}" for i in range(9)]
        v = " ".join(list(f"{comb: >20s}" for comb in combs))
        return v

    for i, r in enumerate(d.x):
        if i >= row_limit:
            continue
        print(f"x[{i}]: {r.frequency: >12d} {r.magnitude: >8d} {format_r(r)}")
    for i, r in enumerate(d.y):
        if i >= row_limit:
            continue
        print(f"y[{i}]: {r.frequency: >12d} {r.magnitude: >8d} {format_r(r)}")


RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"
YELLOW = "\033[1;33m"
def load_relevant(fname, config=IptsdConfig()):
    z = iptsd_read(fname)
    report_types = set([IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure])
    reports = extract_reports(z, report_types)
    grouped = group_reports(reports, report_types)
    states = obtain_state(grouped, insert_group = True, config=config)
    return states

def run_compare_button(args):
    config = IptsdConfig()
    config.dft_button_min_mag = 1000
    full_button = load_relevant(args.full_button, config=config)
    no_button = load_relevant(args.no_button, config=config)

    write_states("/tmp/full_button.json", full_button)
    write_states("/tmp/no_button.json", no_button)
    # states = obtain_state(grouped, insert_group = True)

    # Drop any states that are not in contact with something.
    full_button = [v for v in full_button]
    no_button = [v for v in no_button]

    print(len(no_button))
    print(len(full_button))

    for i, state in enumerate(no_button):
        print("no_button")
        state_dft = state["group"][IptsDftWindowButton]
        state_pos_dft = state["group"][IptsDftWindowPosition]
        print("pos")
        print_dft(state_pos_dft, 1)
        print("button")
        print_dft(state_dft)
        

    for i, (held_state, normal_state) in enumerate(zip(full_button, no_button)):
        print(i)
        # Print on misclassification of any type
        if not held_state.get("button", False) or normal_state.get("button", True):
            # print(f"Normal: {normal_state['button']}  full state: {held_state['button']}")
            c = RED if not held_state.get("button", False) else ""
            print(f"{c}Held-> button : {held_state['button']} contact: {held_state['contact']} {RESET}")
            c = RED if normal_state.get("button", True) else ""
            print(f"{c}Norm-> button : {normal_state['button']} contact: {normal_state['contact']} {RESET}")

            print(YELLOW)
            print("held")
            held_dft = held_state["group"][IptsDftWindowButton]
            held_pos_dft = held_state["group"][IptsDftWindowPosition]
            print("pos")
            print_dft(held_pos_dft, 1)
            print("button")
            print_dft(held_dft)

            print(GREEN)
            print("normal")
            normal_dft = normal_state["group"][IptsDftWindowButton]
            normal_pos_dft = normal_state["group"][IptsDftWindowPosition]
            print("pos")
            print_dft(normal_pos_dft, 1)
            print("button")
            print_dft(normal_dft)


            print(RESET)
            print()
            print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser('compare_button')
    compare_parser.add_argument("--full-button", help="The ground truth digitizer file to open.")
    compare_parser.add_argument("--no-button", help="The iptsd json file to use.")
    compare_parser.set_defaults(func=run_compare_button)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)
