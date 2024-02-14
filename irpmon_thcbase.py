#!/usr/bin/env python3

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

# https://stackoverflow.com/a/312464
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def hexdump(data, columns=64):
    for row in chunks(data, columns):
        print("".join(f"{z:0>2x} " for z in row))

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


# Convenience mixin to allow construction of struct from a byte like object.
class Readable:
    @classmethod
    def read(cls, byte_object):
        a = cls()
        ctypes.memmove(ctypes.addressof(a), bytes(byte_object),
                       min(len(byte_object), ctypes.sizeof(cls)))
        return a


class Base(ctypes.LittleEndianStructure, Readable):
    _pack_ = 1

    def as_dict(self):
        z = {}
        for k, t in self._fields_:
            if k.startswith("_"):
                continue
            z[k] = getattr(self, k)
        return z

    def __repr__(self):
        return str(self.as_dict())

    @classmethod
    def pop(cls, data):
        header = cls.read(data)
        return header, data[ctypes.sizeof(header):ctypes.sizeof(header) + header.size], data[ctypes.sizeof(header) + header.size:]

class DeviceInfo(Base):
    _fields_ = [("vendor", ctypes.c_uint16),
                ("product", ctypes.c_uint16),
                ("padding", ctypes.c_uint8 * 4),
                ("buffer_size", ctypes.c_uint64),
               ]

    @staticmethod
    def from_dump():
        a = "5E 04 52 0C 00 00 00 00 3F 1D 00 00 00 00 00 00"
        a = bytearray([int(z, 16) for z in a.split()]);
        return DeviceInfo.read(a)

# Header: info, has_metadata(u8), metadata

class ipts_touch_metadata_size(Base):
    _fields_ = [("rows", ctypes.c_uint32),
                ("columns", ctypes.c_uint32),
                ("width", ctypes.c_uint32),
                ("height", ctypes.c_uint32),
               ]

class ipts_touch_metadata_transform(Base):
    _fields_ = [("xx", ctypes.c_float),
                ("yx", ctypes.c_float),
                ("tx", ctypes.c_float),
                ("xy", ctypes.c_float),
                ("yy", ctypes.c_float),
                ("ty", ctypes.c_float),
               ]

class ipts_touch_metadata_unknown(Base):
    _fields_ = [("unknown", ctypes.c_float * 16),]

class Metadata(Base):
    _fields_ = [("ipts_touch_metadata_size", ipts_touch_metadata_size),
                ("ipts_touch_metadata_transform", ipts_touch_metadata_transform),
                ("unknown_byte", ctypes.c_uint8),
                ("ipts_touch_metadata_unknown", ipts_touch_metadata_unknown),
               ]
    @staticmethod
    def from_dump():
        a =  """2E 00 00 00 44 00 00 00 FD 6A 00 00 53 47 00 00 41 65 CC 43
                00 00 00 00 00 00 00 00 00 00 00 00 B6 E0 CA 43 00 00 00 00
                01 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3F 00 00 32
                43 00 00 36 43 00 00 34 43 00 00 80 3F 00 00 B4 42 00 00 2B
                43 00 00 C8 42 00 00 A0 41 00 00 2C 43 00 00 31 43 00 00 2F
                43 00 00 00 40 1C"""
        a = bytearray([int(z, 16) for z in a.split()]);
        return Metadata.read(a)


# The actual IRP header.
class IRPStart(Base):
    _fields_ = [("type", ctypes.c_uint8),
                ("unknown", ctypes.c_uint16),
                ("size", ctypes.c_uint32),
                ("_pad", ctypes.c_uint8 * 3),
                ("outer_size", ctypes.c_uint32),
                ("_pad2", ctypes.c_uint8 * 15),
               ]

    # Function to clip data using the IRP header, resulting holds IPTS reports.
    def clip_data(self, data):
        return data[ctypes.sizeof(self):3+self.size]



class IPTSReport(Base):
    _fields_ = [("type", ctypes.c_uint8),
                ("flags", ctypes.c_uint8),
                ("size", ctypes.c_uint16)
               ]

def parse_irp(data):
    irp_header, remainder, discard = IRPStart.pop(data)
    # print(discard)
    reports = []
    while remainder:
        report_header, data, remainder = IPTSReport.pop(remainder)
        if report_header.type == 0:
            break
        reports.append((report_header, data))
    return irp_header, reports




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
        

def load_file(in_file):
    cache_file = os.path.join("/tmp/", os.path.abspath(in_file).replace("/", "_").replace(".bin.gz", ".pickle"))
    cache_enabled = True
    if os.path.isfile(cache_file) and cache_enabled:
        with open(cache_file, "rb") as f:
            records = pickle.load(f)
    else:
        opener = gzip.open if in_file.endswith("gz") else open
        with opener(in_file, "rb") as f:
            records = parse_log_file(codecs.iterdecode(f, encoding='utf-8', errors='ignore'), target_driver="\Driver\IntelTHCBase")
        with open(cache_file, "wb") as f:
            pickle.dump(records, f)
    return records

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
    records = load_file(args.in_file)
    data = discard_outgoing(records)
    iptsd_dumper(args.out_file, data_record_truncator(filter_iptsd_frames(data)))

RED = "\033[0;31m"
GREEN = "\033[0;32m"
RESET = "\033[0m"
def run_print_setup(args):
    records = load_file(args.in_file)
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
            print(hexdump(r.data))
        
        if first == 0x50:
            # data_from_0x50 += bytearray(r.data)
            print(" wide array: " + "".join(chr(z) for z in r.data[::2]))

        prev_data = r.data
        if i > 75:
            break;



def run_print_requests(args):
    records = load_file(args.in_file)
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
    records = load_file(args.in_file)
    data = discard_outgoing(records)
    upto = int(args.upto)
    mid = int(len(data)/2) if args.index is None else int(args.index)
    mid = concat(args.output, data[mid: mid+upto])


def run_things(args):
    records = load_file(args.in_file)
    data = discard_outgoing(records)

    for d in data:
        irp_header, reports = parse_irp(d)
        for (header, data) in reports:
            print(hex(header.type), header)

    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="irpmontool")
    subparsers = parser.add_subparsers(dest="command")

    def subparser_with_default(name):
        sub = subparsers.add_parser(name)
        sub.add_argument("in_file", help="The file to read from.")
        return sub

    convert_parser = subparser_with_default('convert')
    convert_parser.add_argument("out_file", help="Output file to write to, default: %(default)s", default="/tmp/out.bin", nargs="?")
    convert_parser.set_defaults(func=run_convert)



    things_parser = subparser_with_default('things')
    things_parser.set_defaults(func=run_things)

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
