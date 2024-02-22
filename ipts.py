
# Module to parse the ipts data frames and HID reports.
# Also contains some helpers for grouping.
# And loading binary iptsd data dumps.

import ctypes
import struct
from enum import Enum
from collections import namedtuple


# ------------------------------------------------------------------------
# 'Known' constants.
# ------------------------------------------------------------------------


class DftType(Enum):
    IPTS_DFT_ID_POSITION = 6
    IPTS_DFT_ID_POSITION2 = 7
    IPTS_DFT_ID_BUTTON   = 9
    IPTS_DFT_ID_PRESSURE = 11
    IPTS_DFT_ID_10 = 10
    IPTS_DFT_ID_8 = 8
    def __lt__(self, o):
        self._value_ < o._value_

class ReportType(Enum):
    IPTS_REPORT_TYPE_TIMESTAMP                = 0x00
    IPTS_REPORT_TYPE_DIMENSIONS               = 0x03
    IPTS_REPORT_TYPE_HEATMAP                  = 0x25
    IPTS_REPORT_TYPE_STYLUS_V1                = 0x10
    IPTS_REPORT_TYPE_STYLUS_V2                = 0x60
    IPTS_REPORT_TYPE_FREQUENCY_NOISE          = 0x04
    # ??                                      = 0x56
    # Comes in with IRP first byte of 10 (0x0a)
    # Only seen in 2024_02_11_irp_thcbase_metapen_m2.log
    IPTS_REPORT_TYPE_PEN_GENERAL              = 0x57
    IPTS_REPORT_TYPE_PEN_JNR_OUTPUT           = 0x58
    IPTS_REPORT_TYPE_PEN_NOISE_METRICS_OUTPUT = 0x59
    IPTS_REPORT_TYPE_PEN_DATA_SELECTION       = 0x5a
    IPTS_REPORT_TYPE_PEN_MAGNITUDE            = 0x5b
    IPTS_REPORT_TYPE_PEN_DFT_WINDOW           = 0x5c
    IPTS_REPORT_TYPE_PEN_MULTIPLE_REGION      = 0x5d
    IPTS_REPORT_TYPE_PEN_TOUCHED_ANTENNAS     = 0x5e
    IPTS_REPORT_TYPE_PEN_METADATA             = 0x5f
    IPTS_REPORT_TYPE_PEN_DETECTION            = 0x62
    IPTS_REPORT_TYPE_PEN_LIFT                 = 0x63

    # Added this for uniform handling.
    IPTS_REPORT_TYPE_TERMINATION              = 0xff
    def __lt__(self, o):
        self._value_ < o._value_


# ------------------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------------------


# Convenience mixin to allow construction of struct from a byte like object.
class Readable:
    @classmethod
    def read(cls, byte_object):
        a = cls()
        ctypes.memmove(ctypes.addressof(a), bytes(byte_object),
                       min(len(byte_object), ctypes.sizeof(cls)))
        return a

class Convertible:
    def as_dict(self):
        def convert(z):
            if isinstance(z, ctypes.Structure) or isinstance(z, IptsReport) or isinstance(z, dict):
                o = {}
                for k, t in z._fields_:
                    if k.startswith("_"):
                        continue
                    v = getattr(z, k)
                    o[k] = convert(v)
                return o
            elif isinstance(z, ctypes.Array) or isinstance(z, list):
                o = []
                for v in z:
                    o.append(convert(v))
                return o
            elif isinstance(z, (bool, str, int, float, type(None))):
                return z
            elif isinstance(z, bytes):
                return [v for v in z]
            else:
                raise BaseException(f"unhandled type {type(z)}")
                
        return convert(self)
    

class Base(ctypes.LittleEndianStructure, Readable, Convertible):
    _pack_ = 1

    def __repr__(self):
        return str(self.as_dict())

    @classmethod
    def pop_size(cls, data):
        header = cls.read(data)
        return header, data[ctypes.sizeof(header):ctypes.sizeof(header) + header.size], data[ctypes.sizeof(header) + header.size:]

    @classmethod
    def pop(cls, data):
        obtained = cls.read(data)
        return obtained, data[ctypes.sizeof(obtained):]


# ------------------------------------------------------------------------
# These are from iptsd
# ------------------------------------------------------------------------

IPTS_DFT_NUM_COMPONENTS = 9
IPTS_DFT_PRESSURE_ROWS  = 6
IPTS_COLUMNS = 68
IPTS_ROWS = 46
IPTS_WIDTH = 27389
IPTS_HEIGHT = 18259


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


class ipts_pen_dft_window(Base):
    _fields_ = [("timestamp", ctypes.c_uint32),
                ("num_rows", ctypes.c_uint8),
                ("seq_num", ctypes.c_uint8),
                ("_reserved", ctypes.c_uint8 * 3),
                ("data_type", ctypes.c_uint8),
                ("_reserved2", ctypes.c_uint8 * 2),
               ]


class ipts_pen_dft_window_row(Base):
    _fields_ = [("frequency", ctypes.c_uint32),
                ("magnitude", ctypes.c_uint32),
                ("real", ctypes.c_int16 * IPTS_DFT_NUM_COMPONENTS),
                ("imag", ctypes.c_int16 * IPTS_DFT_NUM_COMPONENTS),
                ("first", ctypes.c_int8),
                ("last", ctypes.c_int8),
                ("mid", ctypes.c_int8),
                ("zero", ctypes.c_int8),
               ]




class ipts_report_header(Base):
    _fields_ = [("type", ctypes.c_uint8),
                ("flags", ctypes.c_uint8),
                ("size", ctypes.c_uint16)
               ]

# This is from linux-surface ipts
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

# ------------------------------------------------------------------------
# What follows is high level data types that capture the previous stuff.
# ------------------------------------------------------------------------


class IptsReport(Convertible):
    def __init__(self, **kwargs):
        self._fields_ = []
        for k,v in kwargs.items():
            self._fields_.append((k, type(v)))
            setattr(self, k, v)

    def __repr__(self):
        return f"{self.__class__}: {str(self.as_dict())}"

    def original_data(self):
        if hasattr(self, "_original_data"):
            return self._original_data

    def original_header(self):
        if hasattr(self, "_original_header"):
            return self._original_header

    def write_report(self, fname):
        if not hasattr(self, "_original_data"):
            raise BaseException("need to have the original data stored, call extract_reports using with_data=True")
        with open(fname, "wb") as f:
            f.write(self._original_header)
            f.write(self._original_data)

    @classmethod
    def parse(cls, header, data):
        return cls(header=header, data=data)

class IptsTimestamp(IptsReport):
    pass
class IptsDimensions(IptsReport):
    pass
class IptsHeatmap(IptsReport):
    pass
class IptsNoiseStylusV1(IptsReport):
    pass
class IptsNoiseStylusV2(IptsReport):
    pass
class IptsFrequencyNoise(IptsReport):
    pass

class IptsPenGeneral(IptsReport):
    class ipts_pen_general(Base):
        _fields_ = [("ctr", ctypes.c_uint32),
                    ("_9a999941", ctypes.c_uint32),
                    ("seq", ctypes.c_uint32),
                    ("_0", ctypes.c_uint16), ("_1", ctypes.c_uint8), ("something", ctypes.c_uint8),
                   ]
    @staticmethod
    def parse(header, data):
        z = IptsPenGeneral.ipts_pen_general.read(data)
        assert(z._9a999941 == 0x4199999a)
        assert(z._0 == 0)
        # print(z)
        # print(z._1)
        assert(z._1 == 1 or z._1 == 0)
        return IptsPenGeneral(ctr=z.ctr,seq=z.seq, something=z.something)
    

class IptsJNROutput(IptsReport):
    pass
class IptsNoiseMetricsOutput(IptsReport):
    pass

_datasel_types = {}
class IptsDataSelection(IptsReport):
    class ipts_data_all_mag(Base):
        _fields_ = [("mag", ctypes.c_uint32 * 16)]
    class ipts_data_select_end(Base):
        _fields_ = [("something_end", ctypes.c_uint32 * 2),
                    ("indices", ctypes.c_uint8 * 8),
                    ("_pad", ctypes.c_uint8),
                    ("dft_type", ctypes.c_uint8),
                    ("flag_u1", ctypes.c_int8),
                    ("flag_u2", ctypes.c_int8),
                   ]
    @staticmethod
    def parse(header, data):
        dft_type = data[-3]
        parser = _datasel_types.get(dft_type, None)
        if parser is not None:
            return parser(header, data)
        else:
            x, data = IptsDataSelection.ipts_data_all_mag.pop(data)
            y, data = IptsDataSelection.ipts_data_all_mag.pop(data)
            data_sel_end, data = IptsDataSelection.ipts_data_select_end.pop(data)
            assert(len(data) == 0)
            z = {}
            z.update({f"x_{k}": getattr(x, k) for k, t in x._fields_})
            z.update({f"y_{k}": getattr(y, k) for k, t in y._fields_})
            z.update(data_sel_end.as_dict())
            return IptsDataSelectionPos(**z)


class IptsDataSelectionPos(IptsDataSelection):
    class ipts_data_select_pos_dim(Base):
        _fields_ = [("something", ctypes.c_uint32 * 6),
                    ("mag_0", ctypes.c_uint32),
                    ("something", ctypes.c_uint32 * 2),
                    ("mag_1", ctypes.c_uint32 * 7),
                   ]
    @staticmethod
    def parse(header, data):
        x, data = IptsDataSelectionPos.ipts_data_select_pos_dim.pop(data)
        y, data = IptsDataSelectionPos.ipts_data_select_pos_dim.pop(data)
        data_sel_end, data = IptsDataSelection.ipts_data_select_end.pop(data)
        assert(len(data) == 0)
        z = {}
        z.update({f"x_{k}": getattr(x, k) for k, t in x._fields_})
        z.update({f"y_{k}": getattr(y, k) for k, t in y._fields_})
        z.update(data_sel_end.as_dict())
        return IptsDataSelectionPos(**z)
    pass
_datasel_types[DftType.IPTS_DFT_ID_POSITION._value_] = IptsDataSelectionPos.parse


class IptsMagnitude(IptsReport):
    class ipts_magnitude(Base):
        _fields_ = [("x1", ctypes.c_uint8),
                    ("y1", ctypes.c_uint8),
                    ("x2", ctypes.c_uint8),
                    ("y2", ctypes.c_uint8),
                    ("_min255", ctypes.c_int32),

                    ("x", ctypes.c_uint32 * IPTS_COLUMNS),
                    ("_mid1", ctypes.c_int32),
                    ("_mid2", ctypes.c_int32),
                    ("y", ctypes.c_uint32 * IPTS_ROWS),
                   ]
    @staticmethod
    def parse(header, data):
        v = IptsMagnitude.ipts_magnitude.read(data)
        assert(v._min255 == -255 or v._min255 == -256)
        # mid1 == 1 and mid2 == 2 seen in diagonal.bin
        # assert(v._mid1 == 0)
        # assert(v._mid2 == 0)
        return IptsMagnitude(x1=v.x1, x2=v.x2, y1=v.y1, y2=v.y2, x=v.x, y=v.y)

dft_lookup = {}
class IptsDftWindow(IptsReport):
    @staticmethod
    def parse(header, data):
        header, data = ipts_pen_dft_window.pop(data)
        xs = []
        ys = []
        for i in range(header.num_rows):
            row, data = ipts_pen_dft_window_row.pop(data)
            xs.append(row)
        for i in range(header.num_rows):
            row, data = ipts_pen_dft_window_row.pop(data)
            ys.append(row)
        
        use_type = dft_lookup.get(header.data_type, IptsDftWindow)

        return use_type(header=header, x=xs, y=ys)

    @staticmethod
    def dft_type(header, data):
        header = ipts_pen_dft_window.read(data)
        return dft_lookup.get(header.data_type, IptsDftWindow)
        

class IptsDftWindowPressure(IptsDftWindow):
    pass
class IptsDftWindowPosition(IptsDftWindow):
    pass
class IptsDftWindowPosition2(IptsDftWindow):
    pass
class IptsDftWindowButton(IptsDftWindow):
    pass
class IptsDftWindow0x08(IptsDftWindow):
    pass
class IptsDftWindow0x0a(IptsDftWindow):
    pass

dft_lookup.update({
    DftType.IPTS_DFT_ID_POSITION._value_: IptsDftWindowPosition,
    DftType.IPTS_DFT_ID_POSITION2._value_: IptsDftWindowPosition2,
    DftType.IPTS_DFT_ID_BUTTON._value_: IptsDftWindowButton,
    DftType.IPTS_DFT_ID_PRESSURE._value_: IptsDftWindowPressure,
    DftType.IPTS_DFT_ID_8._value_: IptsDftWindow0x08,
    DftType.IPTS_DFT_ID_10._value_: IptsDftWindow0x0a,
})

class IptsMultipleRegion(IptsReport):
    pass
class IptsTouchedAntennas(IptsReport):
    pass
class IptsPenMetadata(IptsReport):
    class ipts_pen_metadata(Base):
        _fields_ = [("c", ctypes.c_uint32),
                    ("t", ctypes.c_uint8),
                    ("r", ctypes.c_uint8),
                    ("_6", ctypes.c_uint8), ("_1", ctypes.c_uint8), ("_ff", ctypes.c_uint64),
                   ]
    @staticmethod
    def parse(header, data):
        z = IptsPenMetadata.ipts_pen_metadata.read(data)
        assert(z._6 == 6 or z._6 == 3) # Also seen with 3!?! in 2024_02_11_irp_thcbase_slim_pen_2
        assert(z._1 == 1)
        assert(z._ff == 0xffffffffffffffff)
        # Most order is this:
        t_seq = set([0x01, 0x04, 0x02, 0x05, 0x06, 0x0a, 0x0d, 0x00])
        r_seq = set([0x06, 0x07, 0x09, 0x0a, 0x0a, 0x0b, 0x08, 0x07])
        # t_seq found a new one here, 0 in  2024_02_11_irp_thcbase_slim_pen_2
        t_seq |= set([0x00, 0x02, 0x03])
        r_seq |= set([0x06, 0x07])
        assert(z.t in t_seq)
        assert(z.r in r_seq)
        return IptsPenMetadata(c=z.c, t=z.t, r=z.r)

class IptsPenDetection(IptsReport):
    """
     10 0c 01 00 c8 13 01 00 01 00 00 00 02 0d 08 80 
    | D1  |F1|--| D2  |F2|.... Fn...
    """
    class ipts_pen_detect(Base):
        _fields_ = [("d1", ctypes.c_uint16),
                    ("f1", ctypes.c_uint8),
                    ("_0", ctypes.c_uint8),
                    ("d2", ctypes.c_uint16),
                    ("f2", ctypes.c_uint8),
                    ("fn", ctypes.c_uint8 * 8),
                    ("_80", ctypes.c_uint8),
                   ]
    @staticmethod
    def parse(header, data):
        z = IptsPenDetection.ipts_pen_detect.read(data)
        assert(z._0 == 0)
        assert(z._80 == 0x80)
        return IptsPenDetection(d1=z.d1, f1=z.f1, d2=z.d2, f2=z.f2, fn=z.fn)

class IptsPenLift(IptsReport):
    pass

class IptsTermination(IptsReport):
    class ipts_termination(Base):
        _fields_ = [("_v", ctypes.c_uint32)]
    @staticmethod
    def parse(header, data):
        z = IptsTermination.ipts_termination.read(data)
        assert(z._v == 0 or z._v == 0x30000 or z._v == 1)
        return IptsTermination()

report_lookup = {
    ReportType.IPTS_REPORT_TYPE_TIMESTAMP._value_:IptsTimestamp,
    ReportType.IPTS_REPORT_TYPE_DIMENSIONS._value_:IptsDimensions,
    ReportType.IPTS_REPORT_TYPE_HEATMAP._value_:IptsHeatmap,
    ReportType.IPTS_REPORT_TYPE_STYLUS_V1._value_:IptsNoiseStylusV1,
    ReportType.IPTS_REPORT_TYPE_STYLUS_V2._value_:IptsNoiseStylusV2,
    ReportType.IPTS_REPORT_TYPE_FREQUENCY_NOISE._value_:IptsFrequencyNoise,
    ReportType.IPTS_REPORT_TYPE_PEN_GENERAL._value_:IptsPenGeneral,
    ReportType.IPTS_REPORT_TYPE_PEN_JNR_OUTPUT._value_:IptsJNROutput,
    ReportType.IPTS_REPORT_TYPE_PEN_NOISE_METRICS_OUTPUT._value_:IptsNoiseMetricsOutput,
    ReportType.IPTS_REPORT_TYPE_PEN_DATA_SELECTION._value_:IptsDataSelection,
    ReportType.IPTS_REPORT_TYPE_PEN_MAGNITUDE._value_:IptsMagnitude,
    ReportType.IPTS_REPORT_TYPE_PEN_DFT_WINDOW._value_:IptsDftWindow,
    ReportType.IPTS_REPORT_TYPE_PEN_MULTIPLE_REGION._value_:IptsMultipleRegion,
    ReportType.IPTS_REPORT_TYPE_PEN_TOUCHED_ANTENNAS._value_:IptsTouchedAntennas,
    ReportType.IPTS_REPORT_TYPE_PEN_METADATA._value_:IptsPenMetadata,
    ReportType.IPTS_REPORT_TYPE_PEN_DETECTION._value_:IptsPenDetection,
    ReportType.IPTS_REPORT_TYPE_PEN_LIFT._value_:IptsPenLift,
    ReportType.IPTS_REPORT_TYPE_TERMINATION._value_:IptsTermination,
}


# Main function to actually interpret a report using the above data.
def interpret_report(report_header, data):
    p = report_lookup.get(report_header.type, IptsReport)
    return p.parse(report_header, data)

# Interpret a list of [(report_header, report_data), ...]
def interpret_reports(reports):
    output = []
    for report_header, report_data in reports:
        output.append(interpret_report(report_header, report_data))
    return output

# Interpret a frame; [frame_header, [(report_header, report_data), ...]]
def interpret_frame(frame):
    frame_header, reports = frame
    return frame_header, interpret_reports(reports)

# Interpret a list of frames; [[frame_header, [(report_header, report_data), ...]],...]
# This is the function to call on the result of iptsd_read.
def interpret_frames(frames):
    output = []
    for frame in frames:
        output.append(interpret_frame(frame))
    return output

def extract_reports(frames, report_types, with_data=False):
    output = []
    for frame_header, reports in frames:
        for report_header, report_data in reports:
            p = report_lookup.get(report_header.type, IptsReport)
            if p is IptsDftWindow:
                p = IptsDftWindow.dft_type(report_header, report_data)
            if p in report_types:
                parsed = p.parse(report_header, report_data)
                if with_data:
                    parsed._original_frame_header = frame_header
                    parsed._original_header = report_header
                    parsed._original_data = report_data
                output.append(parsed)
            # Bad hack here to allow a white line.
            #if HIDReportFrame0x6e in report_types and type(report_header) == HIDReportFrame0x6e:
            #    output.append(report_data)
    return output

# Clunky helper to group unique report types into dictionaries.
def group_reports(reports, report_types):
    grouped = []
    group = {}
    for r in reports:
        group[type(r)] = r
        if len(group) == len(report_types):
            grouped.append(group)
            group = {}
    return grouped

# Clunky helper to group unique report types into lists.
def chunk_reports(reports, report_types):
    grouped = []
    group = []
    for r in reports:
        group.append(r)
        if IptsDftWindowPosition2 in report_types and type(r) == IptsDftWindowPosition2:
            grouped.append(group)
            group = []
    return grouped
    
# ------------------------------------------------------------------------
# The base HID frame handling.
# ------------------------------------------------------------------------

class HIDReportFrame(Base):
    _fields_ = [("type", ctypes.c_uint8),
                ("unknown", ctypes.c_uint16),
                ("size", ctypes.c_uint32),
                ("_pad", ctypes.c_uint8 * 3),
                ("outer_size", ctypes.c_uint32),
                ("_pad2", ctypes.c_uint8 * 15),
               ]
# 6e ad f7 d8 97 00 00 00 00 00 00 07 00 00 00 ff 00 00 0b 08 00 00 00 00 00 00 00 00 00
class HIDReportFrame0x6e(Base): # CANNOT SUBCLASS FROM HIDReportFrame, size changes!
    _fields_ = [("type", ctypes.c_uint8),
                ("digitizer", ctypes.c_uint32),
                ("_pad6", ctypes.c_uint8 * 6),
                ("_07", ctypes.c_uint32),
                ("_0xff", ctypes.c_uint8),
                ("_pad2", ctypes.c_uint8 * 2),
                ("something", ctypes.c_uint16),
                ("_pad3", ctypes.c_uint8 * 9),
               ]
    # Size doesn't actually be in this entry!? Should it just parse frames to
    # determine length? :/
    size = 1348
assert(ctypes.sizeof(HIDReportFrame0x6e) == 29)

def parse_hid_report(data):
    irp_header, remainder, discard = HIDReportFrame.pop_size(data)
    reports = []
    if irp_header.type == 0x6e:
        # This is one special snowflake...
        irp_header, remainder, discard = HIDReportFrame0x6e.pop_size(data)
        #reports.append((irp_header, irp_header)) # Terrible hack!

    while remainder:
        report_header, data, remainder = ipts_report_header.pop_size(remainder)
        if report_header.type == 0xff: # seems to be termination
            # print(report_header, data)
            reports.append((report_header, data))
            break
        reports.append((report_header, data))
    return irp_header, reports

# ------------------------------------------------------------------------
# IPTSD binary format helpers.
# ------------------------------------------------------------------------

# Write an ipstd file, hid_frames is [[hid_header, [[report_header, report_data],...],...]
def iptsd_write(out_path, hid_frames):
    metadata = Metadata.from_dump()
    device_info = DeviceInfo.from_dump()
    with open(out_path, "wb") as f:
        f.write(bytes(device_info))
        f.write(bytearray([1]))
        f.write(bytes(metadata))
        for hid_header, reports in hid_frames:
            frame_bytes = bytearray(hid_header)
            
            for report_header, report_data in reports:
                frame_bytes += bytes(report_header)
                frame_bytes += bytes(report_data)

            size = len(frame_bytes)
            z = struct.pack("Q", size)
            f.write(z)
            f.write(frame_bytes)

                
            f.write(bytearray([0] * (device_info.buffer_size - size)))

# Read an ipstd file, return is [[hid_header, [[report_header, report_data],...],...]
# This return can be passed into interpret_frames to get the parsed data.
def iptsd_read(in_path):
    with open(in_path, "rb") as f:
        data = f.read()
    device_info, data = DeviceInfo.pop(data)
    has_metadata, data = data[0], data[1:]
    metadata = None
    if has_metadata:
        metadata, data = Metadata.pop(data)

    packets = []
    i = 0
    while (len(data) - i) >= device_info.buffer_size:
        record_len = struct.unpack_from("Q", data, i)[0]
        si = i + struct.calcsize("Q")
        record_data = data[si:si + record_len]
        hid_header, reports = parse_hid_report(record_data)
        i += struct.calcsize("Q") + device_info.buffer_size
        packets.append((hid_header, reports))

    return packets

if __name__ == "__main__":
    # Test iptsd roundtrip.
    import sys
    records1 = iptsd_read(sys.argv[1])
    t1 = "/tmp/tmp_iptsd_write_test.bin"
    t2 = "/tmp/tmp_iptsd_write_test2.bin"
    iptsd_write(t1, records1)
    records2 = iptsd_read(t1)
    iptsd_write(t2, records2)
    with open(t1, "rb") as f:
        d1 = f.read()
    with open(t2, "rb") as f:
        d2 = f.read()
    assert(d1 == d2)
