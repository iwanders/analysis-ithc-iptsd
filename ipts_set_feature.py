#!/usr/bin/env python3

# Attempt to set hid features through python.
# So far not sure if this even does anything... it was kind of a blind
# implementation without a way to test whether it works... mostly a;
# throw mud, see if it sticks approach here.


# from https://github.com/vpelletier/python-hidraw/tree/master

import argparse

"""
 syscalls::ioctl(m_fd, HIDIOCSFEATURE(report.size()), report.data());
90:inline int ioctl(const int fd, const unsigned long rq, T data = nullptr)
91-{
92-	// NOLINTNEXTLINE(cppcoreguidelines-pro-type-vararg)
93:	const int ret = ::ioctl(fd, rq, data);
"""


import fcntl
import ctypes
# import ioctl_opt
IOC_WRITE = 1
IOC_READ = 2

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

def IOC(dir, type, nr, size):
    """
    dir
        One of IOC_NONE, IOC_WRITE, IOC_READ, or IOC_READ|IOC_WRITE.
        Direction is from the application's point of view, not kernel's.
    size (14-bits unsigned integer)
        Size of the buffer passed to ioctl's "arg" argument.
    """
    assert dir <= _IOC_DIRMASK, dir
    assert type <= _IOC_TYPEMASK, type
    assert nr <= _IOC_NRMASK, nr
    assert size <= _IOC_SIZEMASK, size
    return (dir << _IOC_DIRSHIFT) | (type << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


_HIDIOCSFEATURE = lambda len: IOC(IOC_WRITE|IOC_READ, ord('H'), 0x06, len)
class HIDRaw(object):
    """
    Provides methods to access hidraw device's ioctls.
    """
    def __init__(self, device):
        """
        device (file, fileno)
            A file object or a fileno of an open hidraw device node.
        """
        self._device = open(device, "w")

    def _ioctl(self, func, arg, mutate_flag=False):
        result = fcntl.ioctl(self._device, func, arg, mutate_flag)
        if result < 0:
            raise IOError(result)

    def sendFeatureReport(self, report, report_num=0):
        """
        Send a feature report.
        """
        length = len(report) + 1
        buf = bytearray(length)
        buf[0] = report_num
        buf[1:] = report
        self._ioctl(
            _HIDIOCSFEATURE(length),
            (ctypes.c_char * length).from_buffer(buf),
            True,
        )




def hexblob(a):
    a = a.strip().split()
    return [int(z, 16) for z in a]

def run_set_multitouch_parser(args):
    # print(args)
    h = HIDRaw(args.device)
    value = 0x01 if args.state == "on" else 0x00
    payload = [0x05, value, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    h.sendFeatureReport(payload)

def run_set_freqs(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("06 77 00 00 00 00 00 00 70 00 00 00 00 02 01 2e 00 00 00 44 00 00 00 fd 6a 00 00 53 47 00 00 01 41 65 cc 43 00 00 00 00 00 00 00 00 00 00 00 00 b6 e0 ca 43 00 00 00 00 00 00 32 43 00 00 36 43")
    h.sendFeatureReport(payload)

def run_set_pen(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("09 8e a5 15 02 00 00 00 00 ad f7 d8 97 70 17 00")
    h.sendFeatureReport(payload)

def run_set_06(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("06 77 00 00 00 00 00 00 70 00 00 00 00 02 01 2e 00 00 00 44 00 00 00 fd 6a 00 00 53 47 00 00 01 41 65 cc 43 00 00 00 00 00 00 00 00 00 00 00 00 b6 e0 ca 43 00 00 00 00 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3f 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3f 00 00 b4 42 00 00 2b 43 00 00 c8 42 00 00 a0 41 00 00 2c 43 00 00 31 43 00 00 2f 43 00 00 00 40 ")
    h.sendFeatureReport(payload)

def run_set_60(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("60 01 00 00 04 89 11 00 22 40 11 5d 00 84 85 03 20 1c 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ef ef ef ef ee 0e 00 20 14 17 01 80 14 17 01 80 00 00 00 00 00 00 00 00 6c 2b 00 20 ")
    h.sendFeatureReport(payload)

def run_set_7002(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("70 02 ")
    h.sendFeatureReport(payload)

def run_set_7001(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("70 01 00 00 00 00 00 00 37 00 35 00 32 00 45 00")
    h.sendFeatureReport(payload)

def run_set_56(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("56 b4 88 12 64 7a 68 00 00 00 00 00 00 00 00 00 ")
    h.sendFeatureReport(payload)


def run_set_098ea1(args):
    # print(args)
    h = HIDRaw(args.device)
    payload = hexblob("09 8e a1 00 00 00 00 00 00 00 00 00 00 00 00 00  ")
    h.sendFeatureReport(payload)

def run_set_pen_loop(args):
    import time
    h = HIDRaw(args.device)
    seq = 0
    while True:
        d = [0x09, 0x8e, 0xa5, seq, 0x02, 0x00, 0x00, 0x00, 0x00, 0xad, 0xf7, 0xd8, 0x97, 0x70, 0x17, 0x00]
        print(d)
        h.sendFeatureReport(d)
        seq = (seq + 1) % 255
        time.sleep(0.01)
    
    
def run_set_touch_loop(args):
    import time
    h = HIDRaw(args.device)
    seq = 0
    while True:
        d = [0x09, 0x8e, 0xa5, seq, 0x02, 0x01, 0x00, 0x90, 0x01, 0x00, 0x00, 0x00, 0x00, 0xe5, 0x14, 0x00]
        print(d)
        h.sendFeatureReport(d)
        seq = (seq + 1) % 255
        time.sleep(0.01)
    
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="ipst_set_feature")
    parser.add_argument("device", help="The device to write to")
    subparsers = parser.add_subparsers(dest="command")

    set_multitouch_parser = subparsers.add_parser('multitouch')
    set_multitouch_parser.add_argument("state", help="off/on: %(default)s", default="on")
    set_multitouch_parser.set_defaults(func=run_set_multitouch_parser)

    set_freqs_parser = subparsers.add_parser('set_freqs')
    set_freqs_parser.set_defaults(func=run_set_freqs)

    set_pen_parser = subparsers.add_parser('set_pen')
    set_pen_parser.set_defaults(func=run_set_pen)

    set_pen_loop_parser = subparsers.add_parser('set_pen_loop')
    set_pen_loop_parser.set_defaults(func=run_set_pen_loop)
    set_touch_loop_parser = subparsers.add_parser('set_touch_loop')
    set_touch_loop_parser.set_defaults(func=run_set_touch_loop)

    set_60_parser = subparsers.add_parser('set_60')
    set_60_parser.set_defaults(func=run_set_60)

    set_06_parser = subparsers.add_parser('set_06')
    set_06_parser.set_defaults(func=run_set_06)

    set_0702_parser = subparsers.add_parser('set_7002')
    set_0702_parser.set_defaults(func=run_set_7002)

    set_0701_parser = subparsers.add_parser('set_7001')
    set_0701_parser.set_defaults(func=run_set_7001)

    set_56_parser = subparsers.add_parser('set_56')
    set_56_parser.set_defaults(func=run_set_56)

    set_098ea1_parser = subparsers.add_parser('set_098ea1')
    set_098ea1_parser.set_defaults(func=run_set_098ea1)

    args = parser.parse_args()
    if (args.command is None):
        parser.print_help()
        parser.exit()

    args.func(args)

