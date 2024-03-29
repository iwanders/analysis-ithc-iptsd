#!/usr/bin/env python3

# Module to parse IrpMon log files and convert them to an binary dump like iptsd produces.


import sys
import codecs
import json
from collections import namedtuple
from enum import Enum
import gzip
import ctypes
import struct
import pickle
import os
import argparse


RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"
YELLOW = "\033[1;33m"
LIGHT_GRAY = "\033[0;37m"
DARK_GRAY = "\033[1;30m"

from ipts import *

# https://stackoverflow.com/a/312464
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def hexdump(data, columns=64):
    for row in chunks(data, columns):
        print("".join(f"{z:0>2x} " for z in row))

def hexify(data):
    return "".join(f"{z:0>2x} " if (z != 0) else f"{DARK_GRAY}{z:0>2x}{RESET} " for z in data)

# Helper to hold the relevant fields from the log records.
Irp = namedtuple("Irp", [
    # The index of this Irp record in the original file.
    "index",
    # The irp id, this seems to wrap around.
    "irp_id",
    # Major function
    "function",
    # Time string
    "time",
    # Status a reported in IOSB.Status constant
    "status",
    # IRP address, to track start and finish
    "address",
    # Data of the request.
    "data",
    # Previous processor mode for the current thread.
    "previous_mode",
    # Indicates the execution mode of the original requester of the operation, one of UserMode or KernelMode
    "requestor_mode",
    # Ioctl value associated with the irp
    "ioctl",
    # Irp type, IRP or IRPComp
    "irp_type",
])

Function = Enum('Function', [
    'Read',
    'Write',
    'PnP',
    'Create',
    'Cleanup',
    'Close',
    'DeviceControl',
    'SystemControl',
    'InternalDeviceControl',
    'Power',
    ])

IrpType = Enum('IrpType', [
    'AddDevice',
    'DeviceDetected',
    'DriverDetected',
    'FONameDeleted',
    'ImageLoad',
    'IRP',
    'IRPComp',
])

Mode = Enum('Mode', ['KernelMode', 'UserMode'])

Status = Enum('Status', [
    'STATUS_SUCCESS',
    'STATUS_NOT_SUPPORTED',
    'STATUS_PENDING',
    'STATUS_CANCELLED',
    'STATUS_INVALID_DEVICE_REQUEST',
    'STATUS_TIMEOUT'])


"""
    Parse the log file, returning a list of records that pertain to the 
    target driver.
"""
def parse_log_file(file, target_driver):
    major_function = 'NONE'
    irp_id = None
    irp_address = None
    curtime = None
    status = None
    address = None
    ioctl = None
    irp_type = None

    data = False
    lines = []
    discard = False

    records = []

    irp_index = 0
    for line_nr, line in enumerate(file):
        if line.startswith("ID ="):
            irp_id = int(line.split('=', 1)[1].strip())
        if line.startswith("IOCTL ="):
            ioctl = int(line.split('=', 1)[1].strip(), 0)
        elif line.startswith("Major function ="):
            function = Function[line.split('=', 1)[1].strip()]
        elif line.startswith("Previous mode = "):
            previous_mode = Mode[line.split('=', 1)[1].strip()]
        elif line.startswith("Requestor mode = "):
            requestor_mode = Mode[line.split('=', 1)[1].strip()]
        elif line.startswith("Type = "):
            irp_type = IrpType[line.split('=', 1)[1].strip()]
        elif line.startswith("IRP address ="):
            irp_address = int(line.split('=', 1)[1].strip(), 0)
        elif line.startswith("Driver name = "):
            discard = line.split('=', 1)[1].strip() != target_driver
        elif line.startswith("Type = "):
            discard = discard or line.split('=', 1)[1].strip() == "DriverDetected"
        elif line.startswith("Time = "):
            curtime = line.split('=', 1)[1].strip()
            # curtime = time.strptime(curtime, '%m/%d/%Y %I:%M:%S %p')
        elif line.startswith("IOSB.Status constant"):
            status_constant = Status[line.split('=', 1)[1].strip()]
        elif line.startswith("Data (Hexer)"):
            data = True
        elif data and line.startswith("  ") and line.strip():
            lines.append(line.strip())
        elif data:
            bytedata = []
            for l in lines:
                strdata = l.split("\t")[1]
                bytedata.extend([int(x, 16) for x in strdata.split()])
            if not discard:
                record = Irp(
                    index = irp_index,
                    irp_id = irp_id,
                    function = function,
                    time = curtime,
                    status = status_constant,
                    address = irp_address,
                    previous_mode = previous_mode,
                    requestor_mode = requestor_mode,
                    ioctl = ioctl,
                    irp_type = irp_type,
                    data = bytedata)
                records.append(record)


            data = False
            discard = False
            ioctl = None
            irp_type = None
            lines = []
            irp_index += 1

    return records

def discard_record_data(d):
    z = d._asdict()
    z["data"] = []
    return Irp(**z)


def data_record_truncator(data_records):
    # peek at the data, truncate appropriately.
    z = []
    for i, d in enumerate(data_records):
        if d[0] == 0x0c:
            z.append(d[0:1820])
        elif d[0] == 0x0b:
            z.append(d[0:1540])
        elif d[0] == 0x6e:
            z.append(d[0:1540]) # MADE UP!
        elif d[0] == 0x07:
            z.append(d[0:4320]) # MADE UP!
        elif d[0] == 0x0d:
            z.append(d[0:2000])
        elif d[0] == 0x1a:
            z.append(d[0:4340])
        # And from the boot log, whoa;
        elif d[0] in (0xa2, 0x40, 0x92, 0x80, 0xfa, 0x09, 0x20, 0x06, 0x50, 0x73, 0x70, 0x65, 0x08, 0x12):
            z.append(d[:])
        else:
            print(hexdump(d))
            raise RuntimeError(f"Unknown truncation size for type {d[0]:0>2x} at index {i}");
    return z

def filter_iptsd_frames(data_records):
    accepted = (0x0c, 0x0b, 0x6e, 0x07, 0x0d, 0x1a)
    z = []
    for i, d in enumerate(data_records):
        if d[0] in accepted:
            z.append(d)
    return z
    

def iptsd_dumper(out_path, data_records):
    metadata = Metadata.from_dump()
    device_info = DeviceInfo.from_dump()
    with open(out_path, "wb") as f:
        f.write(bytes(device_info))
        f.write(bytearray([1]))
        f.write(bytes(metadata))
        for r in data_records:
            size = len(r)
            z = struct.pack("Q", size)
            f.write(z)
            f.write(bytearray(r))
            f.write(bytearray([0] * (device_info.buffer_size - size)))
        
def concat(out_path, data_records):
    full = bytearray([])
    with open(out_path, "wb") as f:
        for r in data_records:
            f.write(bytearray(r))
            full += bytearray(r)
    return full
        
def chunk_writer(out_path, data_records):
    full = bytearray([])
    for i, d in enumerate(data_records):
        with open(out_path + f"_{i}.bin", "wb") as f:
            f.write(bytearray(d))
    return full
        

def load_file(in_file, limit=None):
    limit = None if limit is None else int(limit)
    limit_string = "" if limit is None else str(limit)
    cache_file = os.path.join("/tmp/", os.path.abspath(in_file).replace("/", "_").replace(".gz", f"{limit_string}.pickle"))
    cache_enabled = True
    if os.path.isfile(cache_file) and cache_enabled:
        with open(cache_file, "rb") as f:
            records = pickle.load(f)
    else:
        opener = gzip.open if in_file.endswith("gz") else open
        with opener(in_file, "rb") as f:
            records = parse_log_file(codecs.iterdecode(f, encoding='utf-8', errors='ignore'), target_driver="\Driver\IntelTHCBase")
        with open(cache_file, "wb") as f:
            pickle.dump(records[0:limit], f)
    return records[0:limit]

def discard_pnp(records):
    filtered = []
    for r in records:
        if r.function == Function.PnP:
            continue
        filtered.append(r)
    return filtered
    

def discard_outgoing(records):
    split_records = []
    for r in records:
        request = r.requestor_mode == Mode.UserMode
        split_records.append((request, r))
            
    request_records = []
    data_records = []
    for request, r in split_records:
        if request:
            request_records.append(r.data)
            continue
        data_records.append(r.data)
    return data_records
    

def run_convert(args):
    records = load_file(args.in_file, limit=args.limit)
    data = discard_outgoing(records)

    packets = []
    for i, d in enumerate(data):
        hid_header, reports = parse_hid_report(d)
        packets.append((hid_header, reports))

    iptsd_write(args.out_file, packets)

def run_print_setup(args):
    records = load_file(args.in_file, limit=args.limit)
    records = discard_pnp(records)
    prev_data = None
    # data = discard_outgoing(records)

    data_from_0x50 = bytearray([])
    for i, r in enumerate(records):
        print()
        print(discard_record_data(r))

        first = r.data[0]

        # type = f"{RED}REQUEST{RESET}" if r.requestor_mode == Mode.UserMode else f"{GREEN}response{RESET}"
        type = f"{RED}REQUEST{RESET}" if r.irp_type == IrpType.IRP else f"{GREEN}response{RESET}"
        print(f"{type} with {len(r.data)} data, first byte: 0x{first:0>2x}")
        # if r.data[0] == 0x65 and len(r.data) == 7488:
            # continue
        if (prev_data == r.data):
            print("Duplicate data with prior!")
        else:
            print(hexify(r.data))
        
        if r.data[0] == 0x6e:
            break;
        if first == 0x50:
            # data_from_0x50 += bytearray(r.data)
            print(" wide array: " + "".join(chr(z) for z in r.data[::2]))

        prev_data = r.data
        # if i > 75:
            # break;



def run_print_requests(args):
    records = load_file(args.in_file, limit=args.limit)
    records = discard_pnp(records)
    # data = discard_outgoing(records)
    for i, r in enumerate(records):
        # if r.requestor_mode != Mode.UserMode:
        if r.irp_type != IrpType.IRP:
            continue;
        print()
        print(discard_record_data(r))
        type = f"{RED}REQUEST{RESET}" if r.requestor_mode == Mode.UserMode else f"{GREEN}response{RESET}"
        print(f"{type} with {len(r.data)} data, first byte: 0x{r.data[0]:0>2x}")
        if r.data[0] == 0x65 and len(r.data) == 7488:
            continue
        print(hexdump(r.data))

def run_extract_data(args):
    records = load_file(args.in_file, limit=args.limit)
    data = discard_outgoing(records)
    upto = int(args.upto)
    mid = int(len(data)/2) if args.index is None else int(args.index)
    mid = concat(args.output, data[mid: mid+upto])


def run_decomposition(args):
    records = load_file(args.in_file, limit=args.limit)
    data = discard_outgoing(records)

    def write(i, n, data):
        if i < args.start_index:
            return
        if args.end_index is not None and i >= args.end_index:
            return
        os.makedirs(args.dump_chunks, exist_ok=True) 
        if args.dump_chunks:
            with open(os.path.join(args.dump_chunks, f"{i:0>8d}_{n}.bin"), "wb") as f:
                f.write(bytearray(data))

    for i, d in enumerate(data):
        irp_header, reports = parse_hid_report(d)
        print(f"0x{irp_header.type:0>2x}: {irp_header}")
        write(i, f"i0x{irp_header.type:0>2x}_000_full", d)

        previous_data_selection = []
        for ri, (header, data) in enumerate(reports):
            z = interpret_report(header, data)

            if isinstance(z, IptsDataSelection):
                previous_data_selection = data
                write(i, f"i0x{irp_header.type:0>2x}_{ri:0>2d}_t0x{header.type:0>2x}_{type(z).__name__}", data)
                print(f"    {type(z).__name__}  {hex(header.type)}, {header}")
            elif issubclass(type(z), IptsDftWindow):
                data_sel_with_dft = bytearray(previous_data_selection) + bytearray(data)
                data_sel_with_dft.extend([0x0] * (2000 - len(data_sel_with_dft)))
                write(i, f"i0x{irp_header.type:0>2x}_datasel_dft", data_sel_with_dft)
                write(i, f"i0x{irp_header.type:0>2x}_{ri:0>2d}_t0x{header.type:0>2x}_{type(z).__name__}_d0x{z.header.data_type:0>2x}", data)
                print(f"    {type(z).__name__}  {hex(header.type)}, {header}, dft data type: 0x{z.header.data_type:0>2x}")
            else:
                write(i, f"i0x{irp_header.type:0>2x}_{ri:0>2d}_t0x{header.type:0>2x}_{type(z).__name__}", data)
                print(f"    {type(z).__name__}  {hex(header.type)}, {header}")



def run_comparison(args):
    clean_data = {}
    all_files = [args.in_file] + args.in_files
    for f in all_files:
        records = load_file(f, limit=args.limit)
        data = discard_outgoing(records)
        # Advance all to an 0x1a
        for i in range(len(data)):
            if data[i][0] == 0x1a:
                break;
        data = data[i:]
        # Filter a few weird IRP data entries on the first byte.
        data = [x for x in data if x[0] != 110 and x[0] != 7 and x[0] != 10]
        clean_data[os.path.basename(f)] = data

    i = 0
    max_i = min(len(x) for x in clean_data.values())
    keys = sorted(list(clean_data.keys()))

    lp = 0
    prevs = {k: 0 for k in keys}
    uniques = {k: set() for k in keys}
    for i in range(max_i):
        if (lp % 20 == 0 and i != 0):
            lp += 1
            print("".join(f"{x: >50s}" for x in keys))

        l = {k: [] for k in keys}
        for k in keys:
            irp_header, reports = parse_hid_report(clean_data[k][i])
            for ri, (header, data) in enumerate(reports):
                z = interpret_report(header, data)
                if isinstance(z, IptsPenGeneral) and False:
                    d = z.ctr - prevs[k]
                    prevs[k] = z.ctr
                    l[k].append(f"{d}  {z.ctr}  {RED}{z.seq}{RESET}   {z.something}")
                if isinstance(z, IptsPenMetadata) and False:
                    # d = z.ctr - prevs[k]
                    # prevs[k] = z.ctr
                    l[k].append(f"{z.c}  {z.t}  {z.r}")
                if isinstance(z, IptsPenDetection) and False:
                    # l[k].append(f"{z.d1}  {z.d2} {z.d1 - z.d2}  {z.f1} {z.f2}")
                    # tl = f"{z.d1: >5d}  {z.d2: >5d} "
                    tl = f"{z.f1}  {z.f2} {list(z.fn)} "
                    l[k].append(tl)
                    # uniques[k].add(hexify(data))
                    uniques[k].add(tl)
                if isinstance(z, IptsMagnitude) and False:
                    ignore = z.x1 == 255 or z.x2 == 255 or z.y1 == 255 or z.y2 == 255
                    ignore = ignore or z.x1 >= len(z.x) or z.x2 >= len(z.x) or z.y1 >= len(z.y) or z.y2 >= len(z.y) 
                    if ignore:
                        tl = "no"
                    else:
                        # print(z)
                        # Why this inverted index?
                        tl = f"{z.x1} {z.x2}  l{list(z.x)[z.x1]} r{list(z.x)[z.x2]}  {z.y1} {z.y2}   l{list(z.y)[z.y1]} r{list(z.y)[z.y2]} "
                    # Check if x1 and x2 are the highest two values.
                    l[k].append(tl)
                    # uniques[k].add(hexify(data))
                    # uniques[k].add(tl)
                if isinstance(z, IptsTouchedAntennas) and False:
                    tl = str(z.data)
                    l[k].append(tl)
                    # uniques[k].add(hexify(data))
                    # uniques[k].add(tl)
                if isinstance(z, IptsDataSelection) and True:
                    # tl = str(z)
                    if (z.dft_type  == DftType.IPTS_DFT_ID_POSITION._value_):
                        # print(z)
                        tl = f"{z.flag_u1}  {z.flag_u2}"
                    else:
                        tl = " "
                    l[k].append(tl)
                    # uniques[k].add(hexify(data))
                    # uniques[k].add(tl)
        if l:
            lp += 1
            for r, l in enumerate(zip(*l.values())):
                if (r != 0):
                    print("--")
                print("".join(f"{x: >50s}" for x in l))

    for k in keys:
        print(k)
        print("\n".join(x for x in sorted(list(uniques[k]))))

        
def run_things(args):
    records = load_file(args.in_file)
    data = discard_outgoing(records)
    pass



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="irpmontool")
    subparsers = parser.add_subparsers(dest="command")

    def subparser_with_default(name, help=None):
        sub = subparsers.add_parser(name, help=help)
        sub.add_argument("in_file", help="The file to read from.")
        sub.add_argument("--limit", default=None, help="Limit files records to this value")
        return sub

    convert_parser = subparser_with_default('convert', help="Convert a irp THCBase log to an iptsd binary dump.")
    convert_parser.add_argument("out_file", help="Output file to write to, default: %(default)s", default="/tmp/out.bin", nargs="?")
    convert_parser.set_defaults(func=run_convert)



    things_parser = subparser_with_default('things')
    things_parser.set_defaults(func=run_things)

    decomposition_parser = subparser_with_default('decomposition')
    decomposition_parser.add_argument("--dump-chunks", help="Write chunks to this directory", default=None, nargs="?")
    decomposition_parser.add_argument("--start-index", help="Start writing from this index", default=0, type=int)
    decomposition_parser.add_argument("--end-index", help="Stop writing at this index", default=None, type=int)
    decomposition_parser.set_defaults(func=run_decomposition)


    comparison_parser = subparser_with_default('comparison')
    comparison_parser.add_argument("in_files", help="The file to read from.", nargs="+")
    comparison_parser.set_defaults(func=run_comparison)

    print_setup = subparser_with_default('print_setup')
    print_setup.set_defaults(func=run_print_setup)

    print_requests = subparser_with_default('print_requests')
    print_requests.set_defaults(func=run_print_requests)

    extract_data_parser = subparser_with_default('extract_data')
    extract_data_parser.add_argument("--index", nargs="?", default=None, help="Index to extract to, defaults to midpoint.")
    extract_data_parser.add_argument("--upto", nargs="?", default=1, help="Number of messages to convert, defaults to %(default)s.")
    extract_data_parser.add_argument("--output", nargs="?", default="/tmp/concact_data.bin", help="Output to write to, defaulst to %(default)s")
    
    extract_data_parser.set_defaults(func=run_extract_data)



    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)
