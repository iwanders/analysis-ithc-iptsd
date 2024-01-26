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

"""
https://github.com/search?q=repo%3AMartinDrab%2FIRPMon%20DataStripThreshold&type=code

May be able to change strip length or disable stripping all together;
    DataStripThreshold : Cardinal;
    StripData : ByteBool;

boolean in register;

https://github.com/MartinDrab/IRPMon/blob/983d656a53c4a2085a33f3b08c184d3b79537265/kbase/driver-settings.c#L169-L170

from a real dump;

Reading size: 1820
Reading size: 1540
Reading size: 4340
Reading size: 2000
Reading size: 1540
Reading size: 64

"""
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


Status = Enum('Status', [
    'STATUS_SUCCESS',
    'STATUS_NOT_SUPPORTED',
    'STATUS_PENDING',
    'STATUS_CANCELLED',
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

    data = False
    lines = []
    discard = False

    records = []

    irp_index = 0
    for line_nr, line in enumerate(file):
        if line.startswith("ID ="):
            irp_id = int(line.split('=', 1)[1].strip())
        elif line.startswith("Major function ="):
            function = Function[line.split('=', 1)[1].strip()]
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
                    data = bytedata)
                records.append(record)


            data = False
            discard = False
            lines = []
            irp_index += 1

    return records



# iptsd binary format;
"""
void on_start() override
{
        if (m_out.empty())
                return;

        m_writer.exceptions(std::ios::badbit | std::ios::failbit);
        m_writer.open(m_out, std::ios::out | std::ios::binary);

        // NOLINTNEXTLINE(cppcoreguidelines-pro-type-reinterpret-cast)
        m_writer.write(reinterpret_cast<char *>(&m_info), sizeof(m_info));

        const char has_meta = m_metadata.has_value() ? 1 : 0;
        m_writer.write(&has_meta, sizeof(has_meta));

        if (m_metadata.has_value()) {
                const ipts::Metadata m = m_metadata.value();

                // NOLINTNEXTLINE(cppcoreguidelines-pro-type-reinterpret-cast)
                m_writer.write(reinterpret_cast<const char *>(&m), sizeof(m));
        }
}

void on_data(const gsl::span<u8> data) override
{
        if (m_out.empty())
                return;

        const u64 size = casts::to<u64>(data.size());

        // NOLINTNEXTLINE(cppcoreguidelines-pro-type-reinterpret-cast)
        m_writer.write(reinterpret_cast<const char *>(&size), sizeof(size));

        // NOLINTNEXTLINE(cppcoreguidelines-pro-type-reinterpret-cast)
        m_writer.write(reinterpret_cast<char *>(data.data()),
                       casts::to<std::streamsize>(size));

        // Pad the data with zeros, so that we always write a full buffer.
        std::fill_n(std::ostream_iterator<u8>(m_writer), m_info.buffer_size - size, '\0');
}

With device info; 
struct [[gnu::packed]] DeviceInfo {
	u16 vendor;
	u16 product;
	u8 padding[4]; // NOLINT(cppcoreguidelines-avoid-c-arrays,modernize-avoid-c-arrays)
	u64 buffer_size;
};

From a dump, start is; 5E 04 52 0C 00 00 00 00 3F 1D 00 00 00 00 00 00
"""

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

"""
struct Metadata {
	struct ipts_touch_metadata_size size {};
	struct ipts_touch_metadata_transform transform {};
	u8 unknown_byte = 0;
	struct ipts_touch_metadata_unknown unknown {};
};

struct [[gnu::packed]] ipts_touch_metadata_transform {
	f32 xx, yx, tx;
	f32 xy, yy, ty;
};

struct [[gnu::packed]] ipts_touch_metadata_unknown {
	f32 unknown[16]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
};

struct [[gnu::packed]] ipts_touch_metadata_size {
	u32 rows;
	u32 columns;
	u32 width;
	u32 height;
};
"""

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
        

if __name__ == '__main__':
    in_file = sys.argv[1]

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

    i = 0
    data_records = []
    for r in records:
        # print(r)
        data_records.append(r.data)
        i += 1
        print(len(r.data))
        print(hexdump(r.data))
        # if i > 2:
            # break;

    iptsd_dumper("/tmp/out.bin", data_records)

    # z = Metadata.from_dump()
    # print(z.buffer_size) # weird number!
    # print(bytes(z))
    # print(len(bytes(Metadata())))
