#!/usr/bin/env python3

import sys
import json

from ipts import iptsd_read, extract_reports, chunk_reports
from ipts import IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition2, IptsDftWindow0x08, IptsDftWindow0x0a
from digi_info import load_digiinfo_xml

RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"
YELLOW = "\033[1;33m"

def print_dft(d, row_limit=9999, row_colors={}):
    def format_r(r):
        combs = [f"{r.real[i]: >5}, {r.imag[i]: >5}" for i in range(9)]
        v = " ".join(list(f"{comb: >20s}" for comb in combs))
        return v

    def print_rows(rows, d):
        dim_colors = row_colors.get(d, {})
        for i, r in enumerate(rows):
            row_color = dim_colors.get(i)
            if i >= row_limit:
                continue
            print(f"{d}[{i: >2d}]: {row_color}{r.frequency: >12d} {r.magnitude: >8d} {format_r(r)}  f{r.first} l{r.last} m{r.mid} z{r.zero}{RESET}")

    print_rows(d.x, "x")
    print_rows(d.y, "y")


def load_relevant(fname):
    z = iptsd_read(fname)
    report_types = set([IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition2, IptsDftWindow0x08, IptsDftWindow0x0a])
    reports = extract_reports(z, report_types, with_data=True)
    grouped = chunk_reports(reports, report_types)
    # states = obtain_state(grouped, insert_group = True, config=config)
    return grouped

def run_print(args):
    grouped = load_relevant(args.input)

    # IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition2, IptsDftWindow0x08, IptsDftWindow0x0a
    def print_all(group):
        for z in group:
            print(type(z).__name__)
            print_dft(z)

    for i, group in enumerate(grouped):
        print(i)
        print_all(group)
        print("\n\n\n")


def run_single(args):
    import time
    grouped = load_relevant(args.input)
    grouped = grouped[10:-10]

    for i, group in enumerate(grouped):
        print("\n\n\n")
        for dft in group:
            if type(dft) == IptsDftWindow0x08:
                # dft.write_report(f"/tmp/dft_chunks/{i:0>5}_{type(dft).__name__}.bin")
                print_dft(dft)
        time.sleep(0.05)



def run_combined(args):
    import time
    grouped = load_relevant(args.input)
    grouped = grouped[10:-10]

    for i, group in enumerate(grouped):
        print("\n\n\n")
        for dft in group:
            if type(dft) == IptsDftWindowButton:
                # dft.write_report(f"/tmp/dft_chunks/{i:0>5}_{type(dft).__name__}.bin")
                print_dft(dft)
            if type(dft) == IptsDftWindow0x0a:
                # dft.write_report(f"/tmp/dft_chunks/{i:0>5}_{type(dft).__name__}.bin")
                print_dft(dft)
        time.sleep(0.1)


def run_row_comparison(args):
    import time
    grouped = load_relevant(args.input)

    def create_consistency_colors(dft):
        def row_consistent(row):
            if row.magnitude < 1000:
                return None
            #combs = [f"{r.real[i]: >5}, {r.imag[i]: >5}" for i in range(9)]
            mid = 4
            center_r = row.real[mid] 
            center_i = row.imag[mid]
            if row.magnitude == 0 or center_r == 0 or center_i == 0:
                return None
            reals = [(r if abs(r) > 20 else 0.0) for r in row.real]
            imags = [(r if abs(r) > 20 else 0.0) for r in row.imag]
            v = [(reals[i] / center_r, imags[i] / center_i) for i in range(9)]
            height = max([p[0] for p in v] + [p[1] for p in v])
            # print(f"row:  {v} {height}")
            return height >= 0.0
        colors = {"x":{}, "y":{}}
        for dim, l in [(dft.x, "x"), (dft.y, "y")]:
            for i, row in enumerate(dim):
                color_lookup = {
                    None: "",
                    True: GREEN,
                    False: RED,
                }
                color = color_lookup[row_consistent(row)]
                colors[l][i] = color
        return colors
            
            

    for i, group in enumerate(grouped):
        print("\n\n\n")
        for dft in group:
            if type(dft) == IptsDftWindowButton:
                # dft.write_report(f"/tmp/dft_chunks/{i:0>5}_{type(dft).__name__}.bin")
                row_colors = create_consistency_colors(dft)
                print_dft(dft, row_colors=row_colors)
            if type(dft) == IptsDftWindow0x0a:
                # dft.write_report(f"/tmp/dft_chunks/{i:0>5}_{type(dft).__name__}.bin")
                row_colors = create_consistency_colors(dft)
                print_dft(dft, row_colors=row_colors)
        time.sleep(0.1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser('print')
    compare_parser.add_argument("input", help="The iptsd dump file to open")
    compare_parser.set_defaults(func=run_print)

    single_parser = subparsers.add_parser('single')
    single_parser.add_argument("input", help="The iptsd dump file to open")
    single_parser.set_defaults(func=run_single)

    combined_parser = subparsers.add_parser('combined')
    combined_parser.add_argument("input", help="The iptsd dump file to open")
    combined_parser.set_defaults(func=run_combined)

    row_comparison_parser = subparsers.add_parser('row_comparison')
    row_comparison_parser.add_argument("input", help="The iptsd dump file to open")
    row_comparison_parser.set_defaults(func=run_row_comparison)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)
