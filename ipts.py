
import ctypes
import struct
from enum import Enum
from collections import namedtuple


class DftType(Enum):
    IPTS_DFT_ID_POSITION = 6
    IPTS_DFT_ID_POSITION2 = 7
    IPTS_DFT_ID_BUTTON   = 9
    IPTS_DFT_ID_PRESSURE = 11
    IPTS_DFT_ID_10 = 10
    IPTS_DFT_ID_8 = 8
    METADATA = 999
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
    def __lt__(self, o):
        self._value_ < o._value_


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


class ipts_pen_dft_window(Base):
    _fields_ = [("timestamp", ctypes.c_uint32),
                ("num_rows", ctypes.c_uint8),
                ("seq_num", ctypes.c_uint8),
                ("_reserved", ctypes.c_uint8 * 3),
                ("data_type", ctypes.c_uint8),
                ("_reserved2", ctypes.c_uint8 * 2),
               ]

IPTS_DFT_NUM_COMPONENTS = 9
IPTS_DFT_PRESSURE_ROWS  = 6

class ipts_pen_dft_window_row(Base):
    _fields_ = [("frequency", ctypes.c_uint32),
                ("magnitude", ctypes.c_uint32),
                ("real", ctypes.c_int16 * IPTS_DFT_NUM_COMPONENTS),
                ("imag", ctypes.c_int16 * IPTS_DFT_NUM_COMPONENTS),
                ("first", ctypes.c_uint8),
                ("last", ctypes.c_uint8),
                ("mid", ctypes.c_uint8),
                ("zero", ctypes.c_uint8),
               ]



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


class ipts_report_header(Base):
    _fields_ = [("type", ctypes.c_uint8),
                ("flags", ctypes.c_uint8),
                ("size", ctypes.c_uint16)
               ]


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
        assert(z._1 == 1)
        return IptsPenGeneral(ctr=z.ctr,seq=z.seq, something=z.something)
    

class IptsJNROutput(IptsReport):
    pass
class IptsNoiseMetricsOutput(IptsReport):
    pass
class IptsDataSelection(IptsReport):
    pass
class IptsMagnitude(IptsReport):
    pass

class IptsDftWindow(IptsReport):
    pass
class IptsDftWindowPressure(IptsDftWindow):
    pass
class IptsDftWindowPosition(IptsDftWindow):
    pass
class IptsDftWindowPosition2(IptsDftWindow):
    pass
class IptsDftWindowButton(IptsDftWindow):
    pass

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
        assert(z._6 == 6)
        assert(z._1 == 1)
        assert(z._ff == 0xffffffffffffffff)
        t_seq = (0x01, 0x04, 0x02, 0x05, 0x06, 0x0a, 0x0d)
        r_seq = (0x06, 0x07, 0x09, 0x0a, 0x0a, 0x0b, 0x08)
        assert(z.t in t_seq)
        assert(z.r == dict(zip(t_seq, r_seq))[z.t])
        return IptsPenMetadata(c=z.c, t=z.t, r=z.r)

class IptsPenDetection(IptsReport):
    pass
class IptsPenLift(IptsReport):
    pass

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
        dft_types = {
            DftType.IPTS_DFT_ID_POSITION._value_: IptsDftWindowPosition,
            DftType.IPTS_DFT_ID_POSITION2._value_: IptsDftWindowPosition2,
            DftType.IPTS_DFT_ID_BUTTON._value_: IptsDftWindowButton,
            DftType.IPTS_DFT_ID_PRESSURE._value_: IptsDftWindowPressure,
        }
        use_type = dft_types.get(header.data_type, IptsDftWindow)

        return use_type(header=header, x=xs, y=ys)

report_parsers = {
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
}

def interpret_report(header, data):
    p = report_parsers.get(header.type, IptsReport)
    return p.parse(header, data)
