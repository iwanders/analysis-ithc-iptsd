#!/usr/bin/env python3

# Written when taking a step back and re-evaluating all data interpretation.
# Allows dumping spectograms of the data.

import sys
import json

from ipts import iptsd_read, extract_reports, chunk_reports, report_lookup
from ipts import IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition2, IptsDftWindow0x08, IptsDftWindow0x0a, IPTS_DFT_NUM_COMPONENTS
from digi_info import load_digiinfo_xml
MID = int(IPTS_DFT_NUM_COMPONENTS / 2)

RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"
YELLOW = "\033[1;33m"


# https://stackoverflow.com/a/312464
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def bool_octet_to_byte(z):
    a = 0
    for i, v in enumerate(z):
        a |= (1 << 7 - i) if v else 0
    return a

def byte_to_bool_octet(z):
    a = []
    for i in range(8):
        a.append(bool(z & ((1 << 7 - i))))
    return a

if True:
    assert(1 == bool_octet_to_byte(byte_to_bool_octet(1)))
    assert(63 == bool_octet_to_byte(byte_to_bool_octet(63)))
    assert(0xaa == bool_octet_to_byte(byte_to_bool_octet(0xaa)))
    assert(0xf0 == bool_octet_to_byte(byte_to_bool_octet(0xf0)))

def hexdump(data, columns=64):
    for row in chunks(data, columns):
        print("".join(f"{z:0>2x} " for z in row))

def hexify(data):
    return "".join(f"{z:0>2x} " for z in data)

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


def run_print_report_types(args):
    z = iptsd_read(args.input)
    for frame_header, reports in z:
        frame_type = frame_header.type
        print(f"0x{frame_type:0>2x}  {hexify(bytes(frame_header))}")
        for report_header, report_data in reports:
            # print(report_data)
            frame_name = report_lookup.get(report_header.type, "")
            print(f"   0x{report_header.type:0>2x} {frame_name}  len: {report_header.size}")
            

def run_print_grouped(args):
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
    # grouped = grouped[10:-10]

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
            center_r = row.real[MID] 
            center_i = row.imag[MID]
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



def run_plot_iq(frames):
    import time
    grouped = load_relevant(args.input)

    import numpy as np
    import matplotlib.pyplot as plt

    def R(a):
        return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    result = {}
    def append(name, entry):
        if not name in result:
            result[name] = []
        result[name].append(entry)

    angle_pos = 0.0
    for i, group in enumerate(grouped):
        window0a_counter = 0
        for dft in group:
            if type(dft) == IptsDftWindowPosition2:
                angle_pos = np.arctan2(dft.x[1].imag[MID], dft.x[1].real[MID])
            if type(dft) == IptsDftWindowButton:
                pass
                index = 2 if dft.x[3].magnitude < dft.x[2].magnitude else 2
                z = R(angle_pos).T.dot(np.array((dft.x[index].imag[MID] , dft.x[index].real[MID])))
                # append(f"2or3rot:*", z)
                # append(f"2or3:*", (dft.x[index].imag[MID] , dft.x[index].real[MID]))
            if type(dft) == IptsDftWindow0x0a and window0a_counter == 0:
                # v = (dft.x[3].imag[MID] , dft.x[3].real[MID])
                # angle_pos = np.arctan2(dft.x[3].imag[MID], dft.x[3].real[MID])
                # z = R(-angle_pos).T.dot(np.array((dft.x[4].imag[MID] , dft.x[4].real[MID])))
                # append(f"0x0a[0]_3:*", v)
                # append(f"0x0a[0]_3_rot:*", z)
                window0a_counter += 1
            if type(dft) == IptsDftWindow0x0a and window0a_counter == 1:
                window0a_counter += 1




    def plot(name):
        p = np.array(result[name])
        if name.endswith("*"):
            plt.scatter(p[:, 0], p[:, 1], c=range(p.shape[0]), label=name)
            plt.plot(p[:, 0], p[:, 1], label=name, linewidth=0.3)
        else:
            plt.plot(p[:, 0], p[:, 1], label=name)

    for k in result.keys():
        plot(k)

    plt.legend()
    plt.show()





def run_plot_spectrogram(frames):
    import time
    import math
    grouped = load_relevant(args.input)

    import matplotlib.pyplot as plt

    def norms(r):
        return [math.sqrt((r.imag[i]**2 + r.real[i]**2)) for i in range(9)]

    def logrow(norm):
        return [math.log(x) if x != 0 else 0 for x in norm]
    rows = []

    entries  = 0

    windows_to_plot = set([
        IptsDftWindowPosition,
        IptsDftWindowPosition2,
        IptsDftWindowButton,
        IptsDftWindow0x0a,
        IptsDftWindow0x08,
    ])
    window_sizes = {
        IptsDftWindowPosition: 2 * 8,
        IptsDftWindowPosition2: 2 * 10,
        IptsDftWindowButton: 2 * 4,
        IptsDftWindow0x0a: 2 * 16 * 2,
        IptsDftWindow0x08: 2 * 10,
    }

    entries = 0
    for t in windows_to_plot:
        entries += window_sizes[t]

    for i, group in enumerate(grouped):
        window0a_counter = 0
        row = []
        for dft in group:
            if type(dft) in windows_to_plot:
                for i in range(dft.header.num_rows):
                    row.extend(norms(dft.x[i]))
                for i in range(dft.header.num_rows):
                    row.extend(norms(dft.y[i]))
        row.extend([0] * (entries * 9 - len(row)))

        row = logrow(row)

        rows.append(row)

    import matplotlib.pyplot as plt
    import scipy.misc
    scipy.misc.imsave(args.spectrogram, rows)
    # plt.imshow(rows, origin='lower')
    # plt.show()


def row_mag(dft, i):
    return dft.x[i].magnitude + dft.y[i].magnitude

def dimension_mag(dft):
    return [row_mag(dft, i) for i in range(dft.header.num_rows)]


def manchester_encode(data):
    encoded = []
    as_bits = []
    for b in data:
        as_bits.extend(byte_to_bool_octet(b))
    # Probably the IEEE one; It states that a logic 0 is represented by a high–low signal sequence and a logic 1 is represented by a low–high signal sequence.
    lookup = {False: (True, False), True:(False, True)}
    for bit in as_bits:
        encoded.extend(lookup.get(bit, False))
    return bytes([bool_octet_to_byte(octet) for octet in list(chunks(encoded, 8))])
    
def manchester_decode(data):
    decoded = []
    as_bits = []
    for b in data:
        as_bits.extend(byte_to_bool_octet(b))
    # Probably the IEEE one; It states that a logic 0 is represented by a high–low signal sequence and a logic 1 is represented by a low–high signal sequence.
    lookup = {(True, False): False, (False, True): True}
    for crumb in chunks(as_bits, 2):
        # print(crumb)
        decoded.append(lookup.get((crumb[0], crumb[1]), False))
    return bytes([bool_octet_to_byte(octet) for octet in list(chunks(decoded, 8))])

def bit_ratio(data):
    # Just add one to both to avoid division by zero.
    zeros = 1
    ones = 1
    for b in data:
        for x in byte_to_bool_octet(b):
            if x:
                ones += 1
            else:
                zeros += 1
    return zeros / ones


if True:
    orig = bytes([1])
    assert(orig == manchester_decode(manchester_encode(orig)))
    orig = bytes([1, 3, 4, 5])
    assert(orig == manchester_decode(manchester_encode(orig)))
    orig = bytes([0xaa, 0xff, 0x00, 63])
    assert(orig == manchester_decode(manchester_encode(orig)))

def run_decode_button(args):
    grouped = load_relevant(args.input)
    def get_button(group):
        for dft in group:
            if type(dft) == IptsDftWindowButton:
                return dft

    transmissions = []
    current = []
    for group in grouped:
        button = get_button(group)
        if not button:
            continue
        dims = dimension_mag(button)
        maxdim = max(dims)
        dims = [z == maxdim for z in dims]

        if dims[0]:
            #print("\nfirst row highest")
            # Sync, transmission starts for sure.
            if len(current):
                transmissions.append(current)
                current = []
        elif dims[1]:
            print("\nSync!")
            # Sync, transmission starts for sure.
            if len(current):
                transmissions.append(current)
                current = []
        elif dims[2]:
            # Lets say a 0
            print("1", end="")
            current.append(True)
        elif dims[3]:
            print("0", end="")
            current.append(False)

    print("Found transmissions")
    everything = bytearray([])
    uniq = set()
    for trans in transmissions:
        as_octets = list(chunks(trans, 8))
        with_bytes = bytes([bool_octet_to_byte(octet) for octet in as_octets])
        everything.extend(with_bytes)
        uniq.add(with_bytes)
        # print(hexify(with_bytes))

    

    print("uniques:")
    for trans in sorted(list(uniq)):
        #print(hexify(trans))
        average = sum(trans) / len(trans)
        print(f"{hexify(trans)} Avg: {average}, bit ratio: {bit_ratio(trans)}")
        # very... average, probably whitened?

    for trans in sorted(list(uniq)):
        decoded = manchester_decode(trans)
        print(hexify(trans), " -> ", hexify(decoded),  f"bit ratio {bit_ratio(decoded)}")


    print("Combined: ", hexify(everything))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    print_report_types_parser = subparsers.add_parser('print_report_types')
    print_report_types_parser.add_argument("input", help="The iptsd dump file to open")
    print_report_types_parser.set_defaults(func=run_print_report_types)

    print_grouped_parser = subparsers.add_parser('print_grouped')
    print_grouped_parser.add_argument("input", help="The iptsd dump file to open")
    print_grouped_parser.set_defaults(func=run_print_grouped)

    single_parser = subparsers.add_parser('single')
    single_parser.add_argument("input", help="The iptsd dump file to open")
    single_parser.set_defaults(func=run_single)

    combined_parser = subparsers.add_parser('combined')
    combined_parser.add_argument("input", help="The iptsd dump file to open")
    combined_parser.set_defaults(func=run_combined)

    row_comparison_parser = subparsers.add_parser('row_comparison')
    row_comparison_parser.add_argument("input", help="The iptsd dump file to open")
    row_comparison_parser.set_defaults(func=run_row_comparison)

    plot_iq_parser = subparsers.add_parser('plot_iq')
    plot_iq_parser.add_argument("input", help="The iptsd dump file to open")
    plot_iq_parser.set_defaults(func=run_plot_iq)

    plot_spectrogram_parser = subparsers.add_parser('plot_spectrogram')
    plot_spectrogram_parser.add_argument("input", help="The iptsd dump file to open")
    plot_spectrogram_parser.add_argument("spectrogram", help="Write histogram here", default="/tmp/spectrogram.png")
    plot_spectrogram_parser.set_defaults(func=run_plot_spectrogram)

    decode_button_parser = subparsers.add_parser('decode_button')
    decode_button_parser.add_argument("input", help="The iptsd dump file to open")
    decode_button_parser.set_defaults(func=run_decode_button)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)
