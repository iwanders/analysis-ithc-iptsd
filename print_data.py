#!/usr/bin/env python3

# Written when taking a step back and re-evaluating all data interpretation.
# Allows dumping spectograms of the data.

import sys
import json
import os

from ipts import iptsd_read, extract_reports, chunk_reports, report_lookup, ithc_read, report_name_to_id
from ipts import IptsPenMetadata, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition2, IptsDftWindow0x08, IptsDftWindow0x0a, IPTS_DFT_NUM_COMPONENTS, IptsDftWindow
from digi_info import load_digiinfo_xml
MID = int(IPTS_DFT_NUM_COMPONENTS / 2)

RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"
YELLOW = "\033[1;33m"
LIGHT_GRAY = "\033[0;37m"
DARK_GRAY = "\033[1;30m"


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
def bool_list_to_byte(z):
    a = 0
    for i, v in enumerate(z):
        a |= (1 << (len(z) - 1) - i) if v else 0
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

def hexify(data):
    return "".join(f"{z:0>2x} " if (z != 0) else f"{DARK_GRAY}{z:0>2x}{RESET} " for z in data)

def hexdump(data, columns=64):
    for row in chunks(data, columns):
        print(hexify(row))

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


def load_relevant(fname, ithc=False, group=True, report_types = set([IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition, IptsDftWindowButton, IptsDftWindowPressure, IptsDftWindowPosition2, IptsDftWindow0x08, IptsDftWindow0x0a])):
    loader = ithc_read if ithc else iptsd_read
    z = loader(fname)
    reports = extract_reports(z, report_types, with_data=True)
    if group:
        grouped = chunk_reports(reports, report_types)
        return grouped
    return reports


def run_print_report_types(args):
    loader = ithc_read if args.ithc else iptsd_read
    z = loader(args.input)
    for frame_header, reports in z:
        frame_type = frame_header.type
        print(f"0x{frame_type:0>2x} size: {frame_header.size} hexdump: {hexify(bytes(frame_header))}")
        for report_header, report_data in reports:
            # print(report_data)
            frame_name = report_lookup.get(report_header.type, "")
            dft_type = ""
            if type(frame_name) != str and isinstance(frame_name(), IptsDftWindow):
                dft_type = IptsDftWindow.dft_type(report_header, report_data).__name__
            if frame_name:
                frame_name = frame_name.__name__
            print(f"   0x{report_header.type:0>2x} {frame_name}  len: {report_header.size} {dft_type}")
            # print(f"{hexify(bytes(report_data[0:32]))} ")
            

def run_print_grouped(args):
    grouped = load_relevant(args.input, ithc=args.ithc)

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
    grouped = load_relevant(args.input, ithc=args.ithc)
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
    grouped = load_relevant(args.input, ithc=args.ithc)
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

def run_print_reports(args):
    import time

    # Convert the reports into a set against which we can match the ids.
    report_name_to_id_local = dict(report_name_to_id.items())
    # Lets also just throw in the class names.
    additions = {report_lookup[z].__name__: z for z in report_name_to_id.values()}
    report_name_to_id_local.update(additions)

    relevant_ids = [report_name_to_id_local[z] for z in args.reports]
    relevant_types = set([report_lookup[z] for z in relevant_ids])
    reports = load_relevant(args.input, ithc=args.ithc, report_types=relevant_types, group=False)

    for i, report in enumerate(reports):
        print(f"{type(report).__name__}: {hexify(report.original_data())}")



def run_row_comparison(args):
    import time
    grouped = load_relevant(args.input, ithc=args.ithc)

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
    grouped = load_relevant(args.input, ithc=args.ithc)

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

def color_map(r):
    # color map that goes from green to red back to green for ratio [0.0, 1.0]
    mags = [1.0, 1.0, 1.0]
    if r <= 0.5:
        mags[0] = r*2
        mags[1] = 1-r*2
        mags[2] = 0
    else:
        mags[0] = 1-(r - 0.5)*2
        mags[1] = (r - 0.5)*2
        mags[2] = 0
    return mags

assert(color_map(0.0) == [0, 1.0, 0])
assert(color_map(0.5) == [1.0, 0.0, 0])
assert(color_map(0.0) == color_map(1.0))
    


def run_plot_spectrogram(frames):
    import time
    import math
    import numpy as np
    from PIL import Image, ImageDraw
    grouped = load_relevant(args.input, ithc=args.ithc)

    import matplotlib.pyplot as plt

    N = IPTS_DFT_NUM_COMPONENTS
    def norms(r):
        mags = [math.sqrt((r.imag[i]**2 + r.real[i]**2))  for i in range(N)]
        return [[a, a, a] for a in mags]

    def phase_calc(r):
        wrapped = [math.atan2(r.imag[i], r.real[i]) for i in range(N)]
        return [a + math.pi * 2 if a < 0 else a for a in wrapped]

    def logrow(norm, s=args.scale):
        return [list(math.log(x* s ) if x != 0 else 0 for x in p) for p in norm]
    rows = []

    entries  = 0

    plot_order = [
        IptsDftWindowButton,
        IptsDftWindow0x0a,
        IptsDftWindowPosition,
        IptsDftWindowPressure,
        IptsDftWindowPosition2,
        IptsDftWindow0x08,
    ]

    windows_to_plot = set(plot_order)
    window_sizes = {
        IptsDftWindowPosition: 2 * 8,
        IptsDftWindowPosition2: 2 * 10,
        IptsDftWindowButton: 2 * 4,
        IptsDftWindow0x0a: 2 * 16 * 2,
        IptsDftWindow0x08: 2 * 10,
        IptsDftWindowPressure: 2 * 16,
    }
    accumulated_window_pos = { }
    for w in plot_order:
        pos = 0
        for x in plot_order:
            if w == x:
                accumulated_window_pos[w] = pos * N
                break;
            pos += window_sizes[x]

    entries = 0
    for t in windows_to_plot:
        entries += window_sizes[t]

    max_seen = 0
    decoded_bits = None
    for i, group in enumerate(grouped):
        window0a_counter = 0
        row = []
        phases = []
        row.extend([[0, 0, 0]] * (entries * N))
        phases.extend([0] * (entries * N))
        for dft in group:
            if type(dft) in windows_to_plot:
                start = accumulated_window_pos[type(dft)]
                if window0a_counter == 1:
                    start += 2 * 16 * N
                if type(dft) == IptsDftWindowPressure and args.decode_pressure_digital:
                    decoded_bits, _discard = decode_pressure_digital(dft)
                for i in range(dft.header.num_rows):
                    window = norms(dft.x[i])
                    row[start + i * N:start + (i + 1) * N] = window
                    if args.color_phase:
                        windowp = phase_calc(dft.x[i])
                        phases[start + i * N:start + (i + 1) * N] = [phase / (math.pi * 2) for phase in windowp]
                    if type(dft) == IptsDftWindowPressure and args.decode_pressure_digital and i > 6:
                        phases[start + i * N:start + (i + 1) * N] = [0]*N if decoded_bits[i-7] else [0.5]*N
                        
                start += dft.header.num_rows * N
                for i in range(dft.header.num_rows):
                    window = norms(dft.y[i])
                    row[start + i * N:start + (i + 1) * N] = window
                    if args.color_phase:
                        windowp = phase_calc(dft.x[i])
                        phases[start + i * N:start + (i + 1) * N] = [phase / (math.pi * 2) for phase in windowp]
                    if type(dft) == IptsDftWindowPressure and args.decode_pressure_digital and i > 6:
                        row[start + i * N:start + (i + 1) * N] = [[10e3,10e3,10e3]] * len(window);
                        phases[start + i * N:start + (i + 1) * N] = [0]*N if decoded_bits[i-7] else [0.5]*N
            if type(dft) == IptsDftWindow0x0a:
                window0a_counter += 1
        if args.logarithm:
            row = logrow(row)
        max_seen = max(max_seen, max(z[0] for z in row))
        if args.color_phase or args.decode_pressure_digital:
            for mags, ratio in zip(row, phases):
                r, g, b = color_map(ratio)
                mags[0] *= r
                mags[1] *= g
                mags[2] *= b
                    
        rows.append(row)


    # Iterate over the values to scale and convert to bytes.
    for row in rows:
        for rgb in row:
            rgb[0] = int((rgb[0] / max_seen) * 255)
            rgb[1] = int((rgb[1] / max_seen) * 255)
            rgb[2] = int((rgb[2] / max_seen) * 255)

    height = len(rows)
    width = len(rows[0])
    font_height = 12

    text_rows = []
    if args.window_header:
        title = os.path.basename(args.input) if args.title is None else args.title
        text_rows.append([(0, title)])
    if args.window_header:
        def index_numbers(start, up_to):
            x = [(start + p * N, f"{p:x}") for p in range(up_to)]
            y = [(start + up_to * N + p * N, f"{p:x}") for p in range(up_to)]
            return x + y
        name_row = []
        index_row = []
        window0a_counter = 0
        for t in plot_order:
            start = accumulated_window_pos[t] + 1
            name = t.__name__.replace("IptsDftWindow", "")
            if t == IptsDftWindow0x0a:
                name_row.append((start, name))
                name_row.append((start + 2 * 16 * N, name))
                name_row.append((start + int(window_sizes[t] / 4) * N , "y"))
                index_row.extend(index_numbers(start, int(window_sizes[t]/4)))
                index_row.extend(index_numbers(start + 2 * 16 * N, int(window_sizes[t]/4)))
            else:
                name_row.append((start, name))
                name_row.append((start + int(window_sizes[t] / 2) * N , "y"))
                index_row.extend(index_numbers(start, int(window_sizes[t]/2)))
                
            
        text_rows.append(name_row)
        text_rows.append(index_row)

    seperator_height = 1
    text_height = font_height * len(text_rows)
    canvas = Image.new("RGB", (width,height + seperator_height + text_height), (0, 0, 0))
    drawable = ImageDraw.Draw(canvas)
    for ri, row_entries in enumerate(text_rows):
        for position, text in row_entries:
            drawable.text((position,(ri) * font_height), text, (255, 255, 255))

    drawable.line([(0, text_height), (width, text_height)], width=seperator_height, fill=(255, 255,255))
    spectrogram = Image.fromarray(np.asarray(rows, dtype=np.uint8))
    canvas.paste(spectrogram, (0,text_height + seperator_height,width,height + seperator_height + text_height))

    # Check if the image is greyscale only, if so make it grey, this saves half the disk space.
    if not (args.color_phase or args.decode_pressure_digital):
        canvas = canvas.convert('L')

    canvas.save(args.spectrogram)


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
    grouped = load_relevant(args.input, ithc=args.ithc)
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

def decode_pressure_digital(button):
    dims = dimension_mag(button)
    digital_active = dims[6]
    minimum = min(dims[7:])
    maximimum = max(dims[7:])
    # digital = [dims[x] > digital_active/2.0 for x in range(7, button.header.num_rows)]
    # digital = [dims[x] > ((maximimum - minimum)/2.0 + minimum) for x in range(7, button.header.num_rows)]
    digital = [dims[x] > ((maximimum - minimum)/3.0 + minimum) for x in range(7, button.header.num_rows)]
    v = bool_list_to_byte(digital)
    # print(f"{digital_active: > 8} " + "  ".join(list((GREEN if digital[z] else "") + f"{v: >7d}{RESET}" for z, v in enumerate(dims[7:]))))
    return digital, v

def run_decode_pressure_digital(args):
    grouped = load_relevant(args.input, ithc=args.ithc)
    def get_pressure(group):
        for dft in group:
            if type(dft) == IptsDftWindowPressure:
                return dft

    transmissions = []
    current = []
    coords = []
    for i, group in enumerate(grouped):
        button = get_pressure(group)
        if not button:
            continue
        # print_dft(button)

        # collapse the dimensions, just obtain the magnitude.
        digital, v = decode_pressure_digital(button)
        # print(digital)
        # print(thresholded)
        # assert(digital == thresholded)
        # Check if it is a parity
        ones = digital.count(True)
        # Doesn't seem to be parity... :(
        # digital.reverse()
        print("".join("1" if x else "0" for x in digital))
        print(f"parity: {ones % 2}")
        p = (i, v)
        print(p)
        coords.append(p)


    print('{' + ",".join(f"({i}, {v})" for i,v in coords) + "}")
    
    import matplotlib.pyplot as plt
    plt.plot([a[0] for a in coords], [a[1] for a in coords])
    plt.show()

def run_test_button_0x0a(args):
    events = load_relevant(args.input, ithc=args.ithc, report_types=set([IptsDftWindow0x0a, IptsPenMetadata]), group=False)
    from iptsd import ButtonGlitchFixUsing0x0a
    button_state = ButtonGlitchFixUsing0x0a()
    for z in events:
        button_state.feed_report(z)
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ithc", help="Use the ithc loader instead of iptsd", default=False, action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    print_report_types_parser = subparsers.add_parser('print_report_types')
    print_report_types_parser.add_argument("input", help="The iptsd dump file to open")
    print_report_types_parser.set_defaults(func=run_print_report_types)

    print_reports_parser = subparsers.add_parser('print_reports')
    print_reports_parser.add_argument("input", help="The iptsd dump file to open")
    print_reports_parser.add_argument("reports", nargs="+", help=f"The reports to print, pick from {report_name_to_id.keys()} or {list(report_lookup[z].__name__ for z in report_name_to_id.values())}")
    print_reports_parser.set_defaults(func=run_print_reports)

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

    plot_spectrogram_parser = subparsers.add_parser('spectrogram')
    plot_spectrogram_parser.add_argument("input", help="The iptsd dump file to open")
    plot_spectrogram_parser.add_argument("spectrogram", help="Write histogram here", default="/tmp/spectrogram.png")
    plot_spectrogram_parser.add_argument("--no-logarithm", dest="logarithm", default=True, action="store_false", help="Whether or not to take the logarithm of the norm.")
    plot_spectrogram_parser.add_argument("--no-header", dest="window_header", default=True, action="store_false", help="Don't render the header.")
    plot_spectrogram_parser.add_argument("--title", dest="title", default=None, help="A single line of text to put in the first row of the header if none, defaults to basename.")
    plot_spectrogram_parser.add_argument("--color-phase", default=False, action="store_true", help="Whether to color by phase.")
    plot_spectrogram_parser.add_argument("--decode-pressure-digital", default=False, action="store_true", help="Whether to color the decoded pressure bits.")
    plot_spectrogram_parser.add_argument("--scale", default=1.0, type=float, help="Multiply values by this before taking the log.")
    plot_spectrogram_parser.set_defaults(func=run_plot_spectrogram)

    decode_button_parser = subparsers.add_parser('decode_button')
    decode_button_parser.add_argument("input", help="The iptsd dump file to open")
    decode_button_parser.set_defaults(func=run_decode_button)

    decode_pressure_digital_parser = subparsers.add_parser('decode_pressure_digital')
    decode_pressure_digital_parser.add_argument("input", help="The iptsd dump file to open")
    decode_pressure_digital_parser.set_defaults(func=run_decode_pressure_digital)


    button_0x0a_parser = subparsers.add_parser('test_button_0x0a')
    button_0x0a_parser.add_argument("input", help="The iptsd dump file to open")
    button_0x0a_parser.set_defaults(func=run_test_button_0x0a)


    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)
