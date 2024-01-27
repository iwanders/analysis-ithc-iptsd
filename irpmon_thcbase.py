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
    # Previous processor mode for the current thread.
    "previous_mode",
    # Indicates the execution mode of the original requester of the operation, one of UserMode or KernelMode
    "requestor_mode",
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

Mode = Enum('Mode', ['KernelMode', 'UserMode'])

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
        elif line.startswith("Previous mode = "):
            previous_mode = Mode[line.split('=', 1)[1].strip()]
        elif line.startswith("Requestor mode = "):
            requestor_mode = Mode[line.split('=', 1)[1].strip()]
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

from kernel;
desc.h
17:#define IPTS_HID_REPORT_DATA_SIZE 7485
That's really close to 7488

/*
 * Synthesize a HID report matching the devices that natively send HID reports
 */
temp[0] = IPTS_HID_REPORT_DATA;

frame = (struct ipts_hid_header *)&temp[3];
frame->type = IPTS_HID_FRAME_TYPE_RAW;
frame->size = header->size + sizeof(*frame);

memcpy(frame->data, header->data, header->size);

return hid_input_report(ipts->hid, HID_INPUT_REPORT, temp, IPTS_HID_REPORT_DATA_SIZE, 1);

Aha. so the first three bytes are 'bad'.

Yes!

For concat mid;

#define IPTS_DFT_NUM_COMPONENTS 9
#define i16 s16
#define i8 s8

struct ipts_hid_frame {
	u32 size;
	u8 reserved1;
	u8 type;
	u8 reserved2;
};


struct  ipts_report {
	u8 type;
	u8 flags;
	u16 size;
};


u8 IPTS_DFT_ID_POSITION = 6;
u8 IPTS_DFT_ID_POSITION2 = 7;
u8 IPTS_DFT_ID_BUTTON   = 9;
u8 IPTS_DFT_ID_PRESSURE = 11;

struct ipts_pen_dft_window_row {
	u32 frequency;
	u32 magnitude;
	i16 real[IPTS_DFT_NUM_COMPONENTS]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	i16 imag[IPTS_DFT_NUM_COMPONENTS]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	i8 first;
	i8 last;
	i8 mid;
	i8 zero;
};

struct ipts_pen_dft_window {
	u32 timestamp; // counting at approx 8MHz
	u8 num_rows;
	u8 seq_num;
	u8 reserved[3]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	u8 data_type;
	u8 reserved2[2]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	ipts_pen_dft_window_row x[num_rows];
		ipts_pen_dft_window_row y[num_rows];
};


struct combined {
    ipts_report header;
    
      match (header.type, header.size) {
        (0x5c, _): ipts_pen_dft_window window;
        (_, _): u8 data[header.size];
      }
    
};

combined first[7] @ 0x1d;
// from here it all breaks down?
//combined bar[1] @ 0x369;

combined second[7] @ 0xa1d;









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


"""
from irpmon, len < 20; len == 16;
09 8e a5 39 02 01 00 90 01 ad f7 d8 97 43 15 00 
09 8e a5 3a 02 01 00 90 01 ad f7 d8 97 43 15 00 
09 8e a5 3b 02 01 00 90 01 00 00 00 00 43 15 00 
09 8e a5 3c 02 01 00 90 01 00 00 00 00 43 15 00 
09 8e a5 3d 02 01 00 90 01 00 00 00 00 43 15 00 

09 8e a5 e8 02 01 00 90 01 00 00 00 00 43 15 00 
09 8e a5 e9 02 01 00 90 01 00 00 00 00 43 15 00 
09 8e a5 ea 02 01 00 90 01 00 00 00 00 43 15 00 
09 8e a5 eb 02 01 00 90 01 00 00 00 00 0e 15 00 
09 8e a5 ec 02 01 00 90 01 00 00 00 00 0e 15 00 
09 8e a5 ed 02 01 00 90 01 00 00 00 00 0e 15 00 

09 8e a5 f9 02 01 00 90 01 00 00 00 00 0e 15 00 
09 8e a5 fa 02 01 00 90 01 00 00 00 00 0e 15 00 
09 8e a5 fb 02 01 00 90 01 00 00 00 00 0e 15 00 
09 8e a5 fc 02 01 00 90 01 00 00 00 00 0e 15 00 
09 8e a5 fd 02 01 00 90 01 00 00 00 00 d8 14 00 
09 8e a5 fe 02 01 00 90 01 00 00 00 00 d8 14 00 
09 8e a5 ff 02 01 00 90 01 00 00 00 00 d8 14 00 
09 8e a5 00 02 01 00 90 01 00 00 00 00 d8 14 00 

Lengths look like:
16
7488
7488
16
7488
7488
7488
16
7488
7488
16
7488
7488
7488
16
7488
7488
16
7488
7488
7488


Data from irpmon is a lot sparser?

    plt.xlim([0, 68])
    plt.ylim([0, 44])

are these even the same protocol packets? Or is this some preparsed version??


imhex, for concat mid;
#define  IPTS_DFT_NUM_COMPONENTS 9

struct  ipts_pen_dft_window {
	u32 timestamp; // counting at approx 8MHz
	u8 num_rows;
	u8 seq_num;
	u8 reserved[3]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	u8 data_type;
	u8 reserved2[2]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
};

struct ipts_pen_dft_window_row {
	u32 frequency;
	u32 magnitude;
	s16 real[IPTS_DFT_NUM_COMPONENTS]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	s16 imag[IPTS_DFT_NUM_COMPONENTS]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	s8 first;
	s8 last;
	s8 mid;
	s8 zero;
};

struct thing {
    u8 type @ 0x0;
    u16 length @ 0x03;
    u16 remainder @ 0x0a;
    u16 something @ 0x12;
    ipts_pen_dft_window z @ 0x106;
    ipts_pen_dft_window_row window[9] @ 0x8a0;
};



// This looks reasonable, is a button.
ipts_pen_dft_window winzz @ 0x1e51;
ipts_pen_dft_window_row zz[4] @ 0x01e5d;


// no timestamp, unknown data type, but frequencies look fine.
ipts_pen_dft_window winzx @ 0x7911;;
ipts_pen_dft_window_row zx[9] @ 0x791d;



ipts_pen_dft_window_row zzz[9] @ 0x17f;


requests;
#include <std/sys.pat>

struct things {
  u8 a;
  u8 x_always_8e;
  u8 x_always_a5;
  u8 seq;
  u8 other[8];
  u8 zz;
  u16 something;
  u8 zero;
};

std::assert(sizeof(things) == 16, "incorrect size");

things foo[1000] @ 0x00;



ex from diag;
"payload":{"rows":8,"type":6,"x":[
    {"freq":1187205120,"mag":250090,"first":9,"last":17,"mid":13,"zero":0,"iq":[[-3,-2],[0,-5],[3,3],[60,95],[257,429],[3,10],[-13,-15],[-10,-14],[-10,-12]]},
    {"freq":1210480000,"mag":497825,"first":9,"last":17,"mid":13,"zero":0,"iq":[[96,76],[159,134],[279,238],[435,373],[535,460],[677,589],[438,378],[232,200],[121,102]]},
    {"freq":1211061824,"mag":5,"first":9,"last":17,"mid":13,"zero":0,"iq":[[1,-1],[-5,0],[-4,0],[-5,1],[-2,-1],[0,0],[4,-1],[3,0],[4,1]]},
    {"freq":1186805248,"mag":26,"first":9,"last":17,"mid":13,"zero":0,"iq":[[-1,1],[0,-1],[1,-1],[0,0],[1,5],[1,1],[1,3],[1,1],[0,3]]},
    {"freq":1187604992,"mag":41,"first":9,"last":17,"mid":13,"zero":0,"iq":[[2,0],[5,1],[5,1],[5,0],[4,-5],[4,-1],[3,-2],[3,-1],[2,-3]]},
    {"freq":1210480000,"mag":9,"first":9,"last":17,"mid":13,"zero":0,"iq":[[2,-2],[2,-2],[2,-3],[2,-1],[3,0],[1,-3],[3,-2],[3,-2],[0,-2]]},
    {"freq":1211061824,"mag":45,"first":9,"last":17,"mid":13,"zero":0,"iq":[[-4,-9],[-2,-7],[-2,-6],[-2,-6],[-3,-6],[1,-5],[0,-5],[3,-5],[1,-4]]},
    {"freq":1210911744,"mag":128,"first":9,"last":17,"mid":13,"zero":0,"iq":[[2,-2],[3,-1],[3,-1],[1,-2],[-8,-8],[3,-2],[5,-1],[4,-1],[4,-1]]}


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
        
def concat(out_path, data_records):
    full = bytearray([])
    with open(out_path, "wb") as f:
        for r in data_records:
            f.write(bytearray(r))
            full += bytearray(r)
    return full
        


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

    split_records = []
    for r in records:
        request = r.requestor_mode == Mode.UserMode
        split_records.append((request, r))
            

    i = 0

    request_records = []
    data_records = []
    for request, r in split_records:
        if request:
            print(r)
            request_records.append(r.data)
            continue
        # print(r)
        # data_records.append(r.data)
        i += 1
        # if (len(r.data) < 1820):
            # continue
        # chunk1 = r.data[0:1820]
        print(len(r.data))
        print(hexdump(r.data[0:100]))
        data_records.append(r.data)
        # if (len(r.data) < 20):
            # print(hexdump(r.data))
        # if i > 2:
            # break;

    request, last = split_records[-1]
    print(len(last.data))
    print(hexdump(last.data))

    chunk_1_len = 1820
    chunk1 = last.data[0:1820]
    print("Chunk 1:")
    print(hexdump(chunk1))
    rem = last.data[1820:]
    print("rem:")
    print(hexdump(rem))
    

    iptsd_dumper("/tmp/out.bin", data_records)
    full = concat("/tmp/concat.bin", data_records)
    requests = concat("/tmp/request_records.bin", request_records)

    for i in range(len(full) - 4):
        (v, ) = struct.unpack_from("<I", full, i)
        #if (v == 1210480000):
        #    print(f"Found {v} at 0x{i:0>8x}")

    # let also output the middle chunks
    mid = int(len(data_records)/2)
    mid = concat("/tmp/concat_mid.bin", data_records[mid: mid+5])
    

    # z = Metadata.from_dump()
    # print(z.buffer_size) # weird number!
    # print(bytes(z))
    # print(len(bytes(Metadata())))
