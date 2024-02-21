# On setup

```
Irp(index=55, irp_id=2751, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660409934656, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 120 data, first byte: 0x06
06 77 00 00 00 00 00 00 70 00 00 00 00 02 01 2e 00 00 00 44 00 00 00 fd 6a 00 00 53 47 00 00 01 41 65 cc 43 00 00 00 00 00 00 00 00 00 00 00 00 b6 e0 ca 43 00 00 00 00 00 00 32 43 00 00 36 43 
00 00 34 43 00 00 80 3f 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3f 00 00 b4 42 00 00 2b 43 00 00 c8 42 00 00 a0 41 00 00 2c 43 00 00 31 43 00 00 2f 43 00 00 00 40 
None

^ This could be frequencies.
1127350272
1127612416
1127481344
1065353216
1127612416
...
1073741824


Irp(index=25, irp_id=172, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298777472, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 292 data, first byte: 0x50

PCI\VEN_8086&DEV_51D0&SUBSYS_00641414&REV_01

Heh.

58-59;
08 D1 2E 9A 00 00 00 00 00 00 93 00 00 00 00 FF 00 00 08 08 00 08 00 90 02 03 4A 76 00 03 08 08 00 2E 44 00 2D 00 43 07 00 04 08 44 00 1
                                                                    |sq|timestamp  |


Irp(index=59, irp_id=2797, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
dimenions, frequency noise, type 7, type 50, type 18, 



First one:
Irp(index=0, irp_id=112, function=<Function.PnP: 3>, time='2024-01-28 6:29:44 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660292750352, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0xa2
a2 15 ad ff f8 a6 60 4e 99 c7 2b 92 62 4d dc 25 
None
gets: IOSB.Status constant = STATUS_NOT_SUPPORTED
Data (PnPInterface)
  Interface type: {FFAD15A2-A6F8-4E60-99C7-2B92624DDC25}
Payload is just a driver uuid.

Irp(index=1, irp_id=117, function=<Function.PnP: 3>, time='2024-01-28 6:29:44 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660292750352, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 64 data, first byte: 0x40
40 00 01 00 02 00 00 00 06 00 10 00 ff ff ff ff 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 04 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
None

Data (PnPDevCaps)
  Version: 1
  Size: 64
  DeviceD2: true

PnP types probably not relevant?

Irp(index=2, irp_id=120, function=<Function.PnP: 3>, time='2024-01-28 6:29:44 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660292750352, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0x92
92 4a 15 6c cf aa d0 11 8d 2a 00 a0 c9 06 b2 44 
None
gets: IOSB.Status constant = STATUS_NOT_SUPPORTED
Data (PnPInterface)
  Interface type: {6C154A92-AACF-11D0-8D2A-00A0C906B244}
  Interface name: GUID_TRANSLATOR_INTERFACE_STANDARD

Irp(index=3, irp_id=122, function=<Function.PnP: 3>, time='2024-01-28 6:29:44 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660292750352, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0x92
Duplicate data with prior!
Data (PnPInterface)
  Interface type: {6C154A92-AACF-11D0-8D2A-00A0C906B244}
  Interface name: GUID_TRANSLATOR_INTERFACE_STANDARD

Irp(index=4, irp_id=128, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298776656, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 64 data, first byte: 0x40
40 00 01 00 02 00 00 00 06 00 10 00 ff ff ff ff 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 04 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
None
Data (PnPDevCaps)
  Version: 1
  Size: 64
  DeviceD2: true

Irp(index=5, irp_id=130, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660298780688, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0x80
80 82 6b 49 25 6f d0 11 be af 08 00 2b e2 09 2f 
None
  Interface type: {496B8280-6F25-11D0-BEAF-08002BE2092F}
  Interface name: GUID_BUS_INTERFACE_STANDARD

Irp(index=6, irp_id=131, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298780688, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 64 data, first byte: 0x40
40 00 01 00 00 00 00 00 b0 34 0a 09 0f d3 ff ff 30 1f 66 09 00 f8 ff ff 20 1f 66 09 00 f8 ff ff e0 b9 6b 09 00 f8 ff ff 20 a5 6b 09 00 f8 ff ff 10 10 66 09 00 f8 ff ff c0 14 66 09 00 f8 ff ff 
None
Data (PnPInterface)
  Size: 64
  Version: 1
  Reference: 0xFFFFF80009661F30
  Dereference: 0xFFFFF80009661F20

Irp(index=7, irp_id=132, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660298780688, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0xfa
fa f7 20 b5 5a 8a 40 4e a3 f6 6b e1 e1 62 d9 35 
None
  Interface type: {B520F7FA-8A5A-4E40-A3F6-6BE1E162D935}
  Interface name: GUID_DMA_CACHE_COHERENCY_INTERFACE

Irp(index=8, irp_id=134, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660298780688, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0x80
80 82 6b 49 25 6f d0 11 be af 08 00 2b e2 09 2f 
None
Data (PnPInterface)
  Interface type: {496B8280-6F25-11D0-BEAF-08002BE2092F}
  Interface name: GUID_BUS_INTERFACE_STANDARD

Irp(index=9, irp_id=135, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298780688, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 64 data, first byte: 0x40
40 00 01 00 00 00 00 00 b0 34 0a 09 0f d3 ff ff 30 1f 66 09 00 f8 ff ff 20 1f 66 09 00 f8 ff ff e0 b9 6b 09 00 f8 ff ff 20 a5 6b 09 00 f8 ff ff 10 10 66 09 00 f8 ff ff c0 14 66 09 00 f8 ff ff 
None
Data (PnPInterface)
  Size: 64
  Version: 1
  Reference: 0xFFFFF80009661F30
  Dereference: 0xFFFFF80009661F20

Irp(index=10, irp_id=136, function=<Function.PnP: 3>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_NOT_SUPPORTED: 2>, address=18446694660298780688, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>)
response with 16 data, first byte: 0xfa
fa f7 20 b5 5a 8a 40 4e a3 f6 6b e1 e1 62 d9 35 
None
  Interface type: {B520F7FA-8A5A-4E40-A3F6-6BE1E162D935}
  Interface name: GUID_DMA_CACHE_COHERENCY_INTERFACE


Discarding pnp.
  Hardware ID: PCI\VEN_8086&DEV_51D0&SUBSYS_00641414&REV_01
  Hardware ID: PCI\VEN_8086&DEV_51D0&SUBSYS_00641414
  Hardware ID: PCI\VEN_8086&DEV_51D0&CC_090100
  Hardware ID: PCI\VEN_8086&DEV_51D0&CC_0901

Irp(index=41, irp_id=617, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:51 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660361669168, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720915)
response with 512 data, first byte: 0x70
70 00 72 00 65 00 63 00 69 00 73 00 65 00 20 00 74 00 6f 00 75 00 63 00 68 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
Data (Hexer)
  000:	70 00 72 00 65 00 63 00 69 00 73 00 65 00 20 00	p.r.e.c.i.s.e. .
  010:	74 00 6f 00 75 00 63 00 68 00 00 00 00 00 00 00	t.o.u.c.h.......
Requestor PID = 1240

rp(index=53, irp_id=1237, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660360480368, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720915)
response with 512 data, first byte: 0x70
more precise touch.

```


# Requests

```
Requests aren't actually that shocking;
Irp(index=47, irp_id=1089, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660351456944, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 61 data, first byte: 0x60
60 01 00 00 04 89 11 00 22 40 11 5d 00 84 85 03 20 1c 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ef ef ef ef ee 0e 00 20 14 17 01 80 14 17 01 80 00 00 00 00 00 00 00 00 6c 2b 00 20 
None

Irp(index=55, irp_id=2751, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660409934656, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 120 data, first byte: 0x06
06 77 00 00 00 00 00 00 70 00 00 00 00 02 01 2e 00 00 00 44 00 00 00 fd 6a 00 00 53 47 00 00 01 41 65 cc 43 00 00 00 00 00 00 00 00 00 00 00 00 b6 e0 ca 43 00 00 00 00 00 00 32 43 00 00 36 43 
00 00 34 43 00 00 80 3f 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3f 00 00 b4 42 00 00 2b 43 00 00 c8 42 00 00 a0 41 00 00 2c 43 00 00 31 43 00 00 2f 43 00 00 00 40 
None

This is that one that could be frequencies.

Irp(index=56, irp_id=2767, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660402932944, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 00 02 00 00 00 00 00 00 00 00 00 00 00 
None
Shares the '09 8e a5' with the later status type requests.

Irp(index=57, irp_id=2779, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660410081296, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x05
05 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
None
IPTS does this!; https://github.com/linux-surface/iptsd/blob/405044af279d71352c4b53ad580e0d5af82868e9/src/ipts/device.cpp#L31-L43

Irp(index=69, irp_id=9154, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:58 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660530637152, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 2 data, first byte: 0x70
70 02 
None

Irp(index=70, irp_id=9155, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:58 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660273998544, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x70
70 01 00 00 00 00 00 00 37 00 35 00 32 00 45 00 
None

Irp(index=71, irp_id=9157, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:58 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660533136416, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x56
56 b4 88 12 64 7a 68 00 00 00 00 00 00 00 00 00 
None

Irp(index=75, irp_id=11987, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:01 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539996448, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 01 02 00 00 00 00 00 00 00 00 70 17 00 

...
Irp(index=145, irp_id=12275, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539001120, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a1 00 00 00 00 00 00 00 00 00 00 00 00 00 
None


Irp(index=146, irp_id=12277, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660541876512, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 15 02 00 00 00 00 ad f7 d8 97 70 17 00 
None

...
Irp(index=2706, irp_id=19229, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:07 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660544420832, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 f0 02 01 00 90 01 00 00 00 00 52 15 00 
None
...

Irp(index=6335, irp_id=15648, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:32:08 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446604998442064160, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 8c 02 00 00 00 00 ad f7 d8 97 70 17 00 
None
..
Irp(index=7879, irp_id=18838, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:32:12 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446604998452066976, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 45 02 01 00 90 01 00 00 00 00 79 15 00 
None

... 
09 8e a5 45 02 01 00 90 01 00 00 00 00 79 15 00 
        |sq|

sq is sequency number.
Message is resent every two or three receipts.

It's this; when pen is used;
09 8e a5 15 02 00 00 00 00 ad f7 d8 97 70 17 00 

It's this; when touch is used:
09 8e a5 cd 02 01 00 90 01 00 00 00 00 e5 14 00



# All entries;

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

```


That `f7 d8 97 70` sent to the hardware is the transducer serial for my slim pen!
