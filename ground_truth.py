#!/usr/bin/env python3

from digi_info import load_digiinfo_xml
from ipts import iptsd_read, extract_reports, IptsDftWindowPosition, IptsDftWindowButton, IptsPenGeneral

def print_data(data):
    for frame_header, reports in data:
        print(f"{frame_header}")
        for report in reports:
            print(f"  {report}")


def correlator(reports, events):
    # pen events don't increase monotonically.
    report_i = 0
    event_i = 0

    report_ctr = reports[report_i].seq
    event_ctr = events[event_i].time
    print(report_ctr)
    print(event_ctr)

    # Advance only the number less than the other one
    if report_ctr < event_ctr:
        while report_ctr < event_ctr:
            report_i += 1
            report_ctr = reports[report_i].seq
            event_ctr = events[event_i].time
        return (report_i, event_i)
    else:
        while report_ctr > event_ctr:
            event_i += 1
            report_ctr = reports[report_i].seq
            event_ctr = events[event_i].time
        return (report_i, event_i)

def aligner(reports, events, offsets):
    aligned = []
    current_reports = []
    current_events = []
    report_i, event_i = offsets
    while report_i < len(reports) and event_i < len(events):
        print(reports[report_i])
        print(reports[report_i + 1])
        print(events[event_i])
        report_i+=1
        event_i+=1

def run_initial(args):
    print("Reading")
    data = iptsd_read(args.data)
    print("parsing")
    records = extract_reports(data, report_types=set([IptsDftWindowPosition, IptsPenGeneral]))
    events = load_digiinfo_xml(args.truth)
    general_reports = [x for x in records if isinstance(x, IptsPenGeneral)]
    r = correlator(general_reports, events)
    print(r)

    d = aligner(records, events, r)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    def subparser_with_default(name):
        sub = subparsers.add_parser(name)
        sub.add_argument("data", help="The data file to read from.")
        sub.add_argument("truth", help="The ground truth file.")
        return sub


    initial_parser = subparser_with_default('initial')
    initial_parser.set_defaults(func=run_initial)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)

