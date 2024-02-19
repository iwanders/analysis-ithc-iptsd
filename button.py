#!/usr/bin/env python3

import sys
import json

from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, group_reports
from iptsd import IptsdConfig, clamp, obtain_state, write_states
# from generalised import generalise_digi, wintilt_to_yaw_tilt
from digi_info import load_digiinfo_xml

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
        print(s.get("button", "-"))
        # if s.get("button", False):
            # print(s["group"][IptsDftWindowButton])