#!/usr/bin/env python3

import sys
import json

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, clamp, obtain_state, write_states, _convert_row
# from generalised import generalise_digi, wintilt_to_yaw_tilt
from digi_info import load_digiinfo_xml

def print_dft(d):
    def format_r(r):
        combs = [f"{r.real[i]: >4}, {r.imag[i]: >4}" for i in range(9)]
        v = " ".join(list(f"{comb: >20s}" for comb in combs))
        return v

    for i, r in enumerate(d.x):
        print(f"x[{i}]: {r.magnitude: >8d} {format_r(r)}")
    for i, r in enumerate(d.y):
        print(f"y[{i}]: {r.magnitude: >8d} {format_r(r)}")

if __name__ == "__main__":
    z = iptsd_read(sys.argv[1])
    report_types = set([IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure])
    reports = extract_reports(z, report_types)
    grouped = group_reports(reports, report_types)
    #for group in grouped:
    #    print(group.keys())
    states = obtain_state(grouped, insert_group = True)
    write_states("/tmp/button_states.json", states)
    # states = obtain_state(grouped, insert_group = True)

    for s in states:
        # del s["group"]
        # print(s.get("button", "-"))
        if s.get("button", False):
            button = s["group"][IptsDftWindowButton]
            print_dft(button)
            print()