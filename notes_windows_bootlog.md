# Notes from the IRPMon bootlog recording of the Windows driver


I'm disregarding the `PnP` messages, so the `function=<Function.PnP: 3>` style messages, I think they're part of the usb setup (but don't really know...)

This leaves `function=<Function.InternalDeviceControl: 9>`. I'm determining `request` or `response` by whether the `IrpType.IRP` or `IrpType.IRPComp` (complete) has data, if it is `IrpType.IRP` it is a request, if `IrpType.IRPComp` with data it must be a response. 

Trailing zero's may be truncated, denoted with `...`

Only copied one log here, from `2024_01_28_intelthcbase_bootlog_diagonal.log.gz`. This surprisingly does not contain the `0x6e` frame.


## Discoveries from a quick glance.
In `2024_01_28_intelthcbase_bootlog_diagonal_spiral_lots_of_touch.log.gz` we have the `0x6e` frame, but it does is not prior to the driver sending the digitizer ID to the hardware!

In fact:
```
Irp(index=181, irp_id=12429, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660541876512, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 1f 02 00 00 00 00 ad f7 d8 97 70 17 00 

Irp(index=182, irp_id=12431, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=None, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x6e
6e ad f7 d8 97 00 00 00 00 00 00 07 00 00 00 ff 00 00 0b 08 00 00 00 00 00 00 00 00 00 5f 00 10 00 4a 04 00 00 04 07 06 01 ff ff ff ff ff ff ff ff 80 00 64 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 cc 02 20 ff ff ff ff ff ff ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 80 59 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

But the digitizer is sent a while before that;

```
Irp(index=145, irp_id=12275, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539001120, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a1 00 00 00 00 00 00 00 00 00 00 00 00 00 

Irp(index=146, irp_id=12277, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660541876512, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 15 02 00 00 00 00 ad f7 d8 97 70 17 00 
```






## From top to bottom; Diagonal bootlog

Booted windows, made a diagonal line.

### id140
```
Irp(index=11, irp_id=140, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660296722592, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720899, irp_type=<IrpType.IRPComp: 7>)
response with 9 data, first byte: 0x09
09 21 00 01 00 01 22 8a 05 
```

### id142
```
Irp(index=12, irp_id=142, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660296722592, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720935, irp_type=<IrpType.IRPComp: 7>)
response with 32 data, first byte: 0x20
20 00 00 00 5e 04 52 0c 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
```

### id144
```
Irp(index=13, irp_id=144, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:45 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660296722592, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720903, irp_type=<IrpType.IRPComp: 7>)
response with 1418 data, first byte: 0x06
06 ff ff 09 01 a1 01 85 5c 95 01 09 05 75 20 b1 02 09 06 75 20 b1 02 75 10 09 07 b1 02 09 08 b1 02 09 09 b1 02 09 0a b1 02 09 0b b1 02 09 0c b1 02 75 20 09 0d b1 02 75 10 09 0f b1 02 09 0f b1 02 09 10 b1 02 09 11 b1 02 09 12 b1 02 09 13 b1 02 09 14 b1 02 09 15 b1 02 09 16 b1 02 09 17 75 10 95 14 b1 03 c0 06 ff ff 09 01 a1 01 85 5a 09 03 75 20 95 80 b1 02 85 5b 09 04 75 20 95 80 81 02 c0 75 08 15 00 26 ff 00 06 0b ff 09 0b a1 01 95 02 09 48 85 48 b1 02 95 0f 09 29 85 29 b1 02 95 1f 09 2a 85 2a b1 02 95 3e 09 2b 85 2b b1 02 95 fe 09 2c 85 2c b1 02 96 fe 01 09 2d 85 2d b1 02 95 0f 09 2e 85 2e 81 02 95 1f 09 2f 85 2f 81 02 95 3e 09 30 85 30 81 02 95 fe 09 31 85 31 81 02 96 fe 01 09 32 85 32 81 02 96 fe 03 09 33 85 33 81 02 96 fe 07 09 34 85 34 81 02 96 fe 0f 09 35 85 35 81 02 96 fe 0d 09 36 85 36 81 02 96 3f 1d 09 37 85 37 81 02 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 61 75 08 96 19 07 81 03 85 0d 09 56 95 01 75 10 81 02 09 61 75 08 96 cd 07 81 03 85 12 09 56 95 01 75 10 81 02 09 61 75 08 96 a9 0d 81 03 85 1a 09 56 95 01 75 10 81 02 09 61 75 08 96 f1 10 81 03 85 1c 09 56 95 01 75 10 81 02 09 61 75 08 96 3d 1d 81 03 85 06 09 63 75 08 95 77 b1 02 85 05 06 00 ff 09 c8 75 08 95 01 b1 02 85 09 09 c9 75 08 95 3f b1 02 85 11 09 59 95 3f b1 02 c0 06 0f ff 09 50 a1 01 85 1f 75 08 95 3c 15 00 26 ff 00 09 60 81 02 85 1f 75 08 95 3c 15 00 26 ff 00 09 61 91 02 85 21 75 20 95 01 17 00 00 00 80 27 ff ff ff 7f 09 66 81 02 09 67 81 02 09 68 81 02 09 69 81 02 85 22 75 20 95 01 17 00 00 00 80 27 ff ff ff 7f 09 72 81 02 09 73 81 02 09 74 81 02 09 75 81 02 85 22 75 20 95 01 17 00 00 00 80 27 ff ff ff 7f 09 7a b1 02 09 7b b1 02 09 7c b1 02 09 7d b1 02 85 23 75 20 95 01 17 00 00 00 80 27 ff ff ff 7f 09 86 b1 02 09 87 b1 02 09 88 b1 02 09 89 b1 02 c0 05 0d 09 04 a1 01 85 40 09 42 15 00 25 01 75 01 95 01 81 02 95 07 81 03 05 01 09 30 75 10 95 01 a4 55 0e 65 11 46 ab 0a 26 ff 7f 81 02 09 31 46 10 07 26 ff 7f 81 02 b4 c0 06 f4 ff 09 01 a1 01 09 07 a1 02 85 54 06 0f ff 09 50 75 08 95 04 15 00 25 ff 82 02 01 06 f4 ff 09 02 75 08 95 06 15 00 25 ff 82 02 01 09 08 75 01 95 01 15 00 25 01 81 02 75 07 95 01 81 01 c0 09 05 a1 02 85 55 06 0f ff 09 50 75 08 95 04 15 00 25 ff 92 02 01 06 f4 ff 09 02 75 08 95 06 15 00 25 ff 92 02 01 09 08 75 01 95 01 15 00 25 01 91 02 75 07 95 01 91 01 09 04 75 08 95 08 15 00 25 ff 92 02 01 c0 09 06 a1 02 85 56 09 03 75 08 95 06 15 00 25 ff b2 02 01 09 09 75 01 95 01 15 00 25 01 b1 02 75 07 95 01 b1 01 c0 09 13 a1 02 85 6e 06 0f ff 09 50 75 08 95 04 15 00 25 ff 82 02 01 06 f4 ff 09 02 75 08 95 06 15 00 25 ff 82 02 01 09 08 75 01 95 01 15 00 25 01 81 02 09 11 75 01 95 01 15 00 25 01 81 02 09 12 75 01 95 01 15 00 25 01 81 02 75 05 95 01 81 01 c0 09 15 a1 02 85 6f 06 0f ff 09 50 75 08 95 04 15 00 25 ff 92 02 01 06 f4 ff 09 02 75 08 95 06 15 00 25 ff 92 02 01 09 08 75 01 95 01 15 00 25 01 91 02 75 07 95 01 91 01 09 14 75 08 95 10 15 00 25 ff 92 02 01 c0 09 16 85 70 a1 02 09 10 75 01 95 01 15 00 25 01 b1 02 09 22 75 01 95 01 15 00 25 01 b1 02 75 06 95 01 b1 01 c0 09 21 85 73 75 08 95 02 15 00 25 ff b1 02 c0 06 0b ff 0a 01 01 a1 01 85 5f 75 08 95 3c 09 65 b1 02 85 60 75 08 95 3c 15 00 26 ff 00 09 60 81 02 85 60 75 08 95 3c 15 00 26 ff 00 09 61 91 02 85 60 75 08 95 3c 15 00 26 ff 00 09 62 b1 02 85 62 75 20 95 01 09 66 81 02 09 67 81 02 09 68 81 02 09 69 81 02 85 65 75 20 95 01 09 8e 91 02 09 8f 91 02 09 90 91 02 09 91 91 02 85 65 75 20 95 01 09 8a 81 02 09 8b 81 02 09 8c 81 02 09 8d 81 02 c0 05 0d 09 02 a1 01 85 01 09 20 35 00 a1 00 09 32 09 42 09 44 09 3c 09 45 15 00 25 01 75 01 95 05 81 02 95 03 81 03 05 01 09 30 75 10 95 01 a4 55 0e 65 11 46 b3 0a 26 80 25 81 02 09 31 46 22 07 26 20 1c 81 02 b4 05 0d 09 30 26 00 10 81 02 a4 55 0e 65 14 36 d8 dc 46 28 23 26 50 46 09 3d 81 02 09 3e 81 02 55 0c 66 01 10 35 00 47 ff ff 00 00 27 ff ff 00 00 09 56 81 02 b4 06 00 ff 09 01 75 08 95 01 81 02 81 03 c0 c0 06 a1 ff 09 60 a1 01 85 58 95 01 75 10 09 03 81 02 c0 06 0f ff 09 51 a1 01 85 66 75 08 95 01 09 01 b1 02 09 02 b1 02 75 20 95 0e 09 03 b1 02 c0
```

Lots of repeating patterns here.

### id257
```
Irp(index=38, irp_id=257, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:48 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660280448864, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 3 data, first byte: 0x73
73 fe ff 

Irp(index=40, irp_id=296, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:50 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660358782992, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 3 data, first byte: 0x73
Duplicate data with prior!
```

Sent twice.

### id617
```
Irp(index=41, irp_id=617, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:51 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660361669168, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720915, irp_type=<IrpType.IRPComp: 7>)
response with 512 data, first byte: 0x70
70 00 72 00 65 00 63 00 69 00 73 00 65 00 20 00 74 00 6f 00 75 00 63 00 68 00 00...

Irp(index=44, irp_id=799, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660360891600, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720915, irp_type=<IrpType.IRPComp: 7>)
response with 512 data, first byte: 0x70
Duplicate data with prior!
```

Sent twice.

### id1089

```
Irp(index=47, irp_id=1089, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660351456944, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 61 data, first byte: 0x60
60 01 00 00 04 89 11 00 22 40 11 5d 00 84 85 03 20 1c 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ef ef ef ef ee 0e 00 20 14 17 01 80 14 17 01 80 00 00 00 00 00 00 00 00 6c 2b 00 20
```

### id1094

```
Irp(index=48, irp_id=1094, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
65 00 00 00 a0 00 00 00 00 ff 00 00 00 01 00 00...

Irp(index=49, irp_id=1097, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
Duplicate data with prior!
```

Sent twice, likely first data?? `7488` as size of the frame.

### id1101

```
Irp(index=50, irp_id=1101, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660402923936, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 3 data, first byte: 0x73
73 fe ff 
```

Same as [#id257](#id257), but now only sent once.



### id1104
```
Irp(index=51, irp_id=1104, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
65 00 00 00 a0 00 00 00 00 00 00 00 00 02 00 00...
```
Looks similar to as [#id1094](#id1094).

### id1108
```
Irp(index=52, irp_id=1108, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
65 00 00 00 a0 00 00 00 00 ff 00 00 00 01 00 00 00

Irp(index=49, irp_id=1097, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
Duplicate data with prior!

```
Looks similar to as [#id1094](#id1094).

### id1101
```
Irp(index=50, irp_id=1101, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660402923936, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 3 data, first byte: 0x73
73 fe ff 
```


### id1104
```
Irp(index=51, irp_id=1104, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
65 00 00 00 a0 00 00 00 00 00 00 00 00 02 00 00 00 00 00...
```

### id1108
```
Irp(index=52, irp_id=1108, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720911, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x65
65 00 00 00 a0 00 00 00 00 ff 00 00 00 01 00 00 00 00 00 00 00 00 00 00...
```

### id1237
```
Irp(index=53, irp_id=1237, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660360480368, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720915, irp_type=<IrpType.IRPComp: 7>)
response with 512 data, first byte: 0x70
70 00 72 00 65 00 63 00 69 00 73 00 65 00 20 00 74 00 6f 00 75 00 63 00 68 00 00 00 00 00 00 00

Irp(index=54, irp_id=2374, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:52 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660410086208, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720915, irp_type=<IrpType.IRPComp: 7>)
response with 512 data, first byte: 0x70
Duplicate data with prior!

```
Hexview:
```
Hex View  00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F
 
00000000  70 00 72 00 65 00 63 00  69 00 73 00 65 00 20 00  p.r.e.c.i.s.e. .
00000010  74 00 6F 00 75 00 63 00  68 00 00 00 00 00 00 00  t.o.u.c.h.......
```
Device name in wide string.


### id2751
```
Irp(index=55, irp_id=2751, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660409934656, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 120 data, first byte: 0x06
06 77 00 00 00 00 00 00 70 00 00 00 00 02 01 2e 00 00 00 44 00 00 00 fd 6a 00 00 53 47 00 00 01 41 65 cc 43 00 00 00 00 00 00 00 00 00 00 00 00 b6 e0 ca 43 00 00 00 00 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3f 00 00 32 43 00 00 36 43 00 00 34 43 00 00 80 3f 00 00 b4 42 00 00 2b 43 00 00 c8 42 00 00 a0 41 00 00 2c 43 00 00 31 43 00 00 2f 43 00 00 00 40 
```

This could be frequencies, the values read like;
```
1127350272
1127612416
1127481344
1065353216
1127612416
...
1073741824
```
Sounds similar to the `freq` field from the dft windows.

### id2767
request

```
Irp(index=56, irp_id=2767, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660402932944, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 00 02 00 00 00 00 00 00 00 00 00 00 00
```

### id2779
request
```
Irp(index=57, irp_id=2779, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660410081296, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x05
05 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00
````
IPTSD does this!; https://github.com/linux-surface/iptsd/blob/405044af279d71352c4b53ad580e0d5af82868e9/src/ipts/device.cpp#L31-L43


### id2789

```
Irp(index=58, irp_id=2789, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=None, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 d1 2e 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 90 02 03 4a 76 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 90 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00...
```

<details>
  <summary>Frame and reports overview</summary>

```
Irp(index=59, irp_id=2797, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 49 2f 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 91 02 d9 78 76 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 91 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00...

Irp(index=60, irp_id=2803, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 c1 2f 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 92 02 b8 a7 76 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 92 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00...

Irp(index=61, irp_id=2823, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 39 30 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 93 02 99 d6 76 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 93 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00 00...

Irp(index=62, irp_id=2859, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 b1 30 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 94 02 78 05 77 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 94 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00 00 00 00...

Irp(index=63, irp_id=2883, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 29 31 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 95 02 58 34 77 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 95 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00...

Irp(index=64, irp_id=2894, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 a1 31 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 96 02 39 63 77 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 96 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00 00...

Irp(index=65, irp_id=2903, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 19 32 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 97 02 1a 92 77 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 97 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00...

Irp(index=66, irp_id=2910, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 91 32 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 98 02 f8 c0 77 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 98 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00...

Irp(index=67, irp_id=2928, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:53 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x08
08 09 33 9a 00 00 00 00 00 00 93 00 00 00 00 ff 00 00 08 08 00 08 00 99 02 d9 ef 77 00 03 08 08 00 2e 44 00 2d 00 43 07 00 04 08 44 00 10 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 08 04 00 00 00 00 00 07 08 04 00 00 00 00 00 32 04 08 00 e0 2e 00 00 00 5e 5e 5e 12 08 04 00 00 00 00 00 ff 08 04 00 99 02 08 00 c0 15 00 27 ff ff 00 00 05 0d 09 0f a1 01 85 07 09 56 95 01 75 10 81 02 09 61 75 08 95 3d 81 03 85 08 09 56 95 01 75 10 81 02 09 61 75 08 95 fd 81 03 85 0a 09 56 95 01 75 10 81 02 09 61 75 08 96 e5 03 81 03 85 0b 09 56 95 01 75 10 81 02 09 61 75 08 96 01 06 81 03 85 0c 09 56 95 01 75 10 81 02 09 00 00 00 00...
```

</details>


Now containing data in the 7488 long frame.


### id5076

```
Irp(index=68, irp_id=5076, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:54 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660430724048, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 3 data, first byte: 0x73
73 dc 03 
```

### id9154
```
Irp(index=69, irp_id=9154, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:58 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660530637152, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721298, irp_type=<IrpType.IRPComp: 7>)
response with 2 data, first byte: 0x70
70 02 
```

### id9155
request
```
Irp(index=70, irp_id=9155, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:58 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660273998544, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x70
70 01 00 00 00 00 00 00 37 00 35 00 32 00 45 00 
```

```
Hex View  00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F
 
00000000  70 01 00 00 00 00 00 00  37 00 35 00 32 00 45 00  p.......7.5.2.E.
```

Looks like a wide string, odd that this is sent to the device.

### id9157
request
```
Irp(index=71, irp_id=9157, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:29:58 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660533136416, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x56
56 b4 88 12 64 7a 68 00 00 00 00 00 00 00 00 00
```

This appears to be the last of the setup?

### id11980
We get real data now.
```
Irp(index=72, irp_id=11980, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:01 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=None, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x0c
0c 00 00 d6 06 00 00 00 00 00 cf 06 00 00 00 ff 00 00 0b 08 00 00 00 00 00 00 00 00 00 5f 00 10 00 3b 04 00 00 01 06 06 01 ff ff ff ff ff ff ff ff 57 00 40 00 4e ed f3 00 9a 99 99 41 3b 04 00 00 00 00 01 01 ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff 80 00 64 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 ed f3 00 ff ff ff ff ff ff ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 ff 59 00 40 00 13 00 13 00 13 00 13 00 13 00 13 00 13 00 13 00 13 00 22 00 24 00 00 00 00 00 00 00 00 00 00 00 15 00 15 00 15 00 15 00 15 00 15 00 15 00 15 00 15 00 24 00 00 00 00 00 00 00 00 00 00 00 00 00 5a 00 94 00 40 0f 00 00 f2 0f 00 00 0d 11 00 00 b9 11 00 00 a8 13 00 00 20 12 00 00 62 11 00 00 28 0f 00 00 d5 0e 00 00 00 00 00 00 00 00 00 00 0a 00 00 00 12 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 45 10 00 00 62 11 00 00 89 12 00 00 3d 13 00 00 40 15 00 00 a8 13 00 00 79 12 00 00 90 10 00 00 39 10 00 00 00 00 00 00 00 00 00 00 14 00 00 00 19 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 f1 df 00 00 8a e3 00 00 00 00 00 00 3c 04 3d 05 00 06 01 ff 5b 00 d0 01 3c 04 3d 05 01 ff ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 05 00 00 00 09 00 00 00 0d 00 00 00 3d 00 00 00 d0 00 00 00 90 02 00 00 94 07 00 00 62 11 00 00 52 0f 00 00 65 06 00 00 ca 01 00 00 88 00 00 00 28 00 00 00 14 00 00 00 0d 00 00 00 41 00 00 00 f4 00 00 00 28 03 00 00 b2 09 00 00 79 12 00 00 34 0d 00 00 21 05 00 00 5a 01 00 00 59 00 00 00 19 00 00 00 0a 00 00 00 09 00 00 00 01 00 00 00 01 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5e 00 1c 00 00 00 00 00 00 00 00 00 00 00 00 00 3b 04 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 5c 00 0c 03 44 be fc 00 08 01 01 01 04 06 ff ff 00 50 c3 46 62 11 00 00 fa ff f4 ff ec ff de ff cd ff cf ff e1 ff ef ff f6 ff 05 00 08 00 10 00 1c 00 2b 00 27 00 1a 00 0d 00 06 00 38 40 3c 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 36 bd 46 0a 00 00 00 00 00 00 00 01 00 01 00 03 00 01 00 01 00 ff ff ff ff ff ff ff ff 00 00 fd ff ff ff fe ff fe ff 00 00 ff ff 38 40 3c 00 00 6a c9 46 12 00 00 00 ff ff 01 00 01 00 03 00 03 00 03 00 02 00 01 00 ff ff 00 00 00 00 ff ff fd ff fd ff fb ff fe ff fe ff ff ff 38 40 3c 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 50 c3 46 79 12 00 00 f9 ff f4 ff ea ff d9 ff cc ff d4 ff e4 ff f1 ff f8 ff 04 00 0a 00 12 00 1f 00 2d 00 26 00 17 00 0b 00 05 00 00 08 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 36 bd 46 14 00 00 00 01 00 01 00 02 00 02 00 04 00 03 00 03 00 ff ff ff ff 00 00 ff ff ff ff ff ff fe ff fe ff 00 00 ff ff ff ff 00 08 04 00 00 6a c9 46 19 00 00 00 01 00 01 00 01 00 02 00 03 00 03 00 02 00 01 00 00 00 fe ff fe ff fd ff fd ff fc ff fc ff fc ff fe ff fe ff 00 08 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 62 00 10 00 14 16 00 00 94 13 00 00 01 00 03 00 00 01 06 80 ff 0b 04 00 00...

Irp(index=73, irp_id=11983, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:01 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x0b
0b 00 00 5e 05 00 00 00 00 00 57 05 00 00 00 ff 00 00 0b 08 00 00 00 00 00 00 00 00 00 5f 00 10 00 3b 04 00 00 04 07 06 01 ff ff ff ff ff ff ff ff 80 00 64 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 00 00 00 00 00 00 00 ff 00 00 00 00 2d 00 00 ff ff ff ff ff ff ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 80 59 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5a 00 94 00 a8 ca 00 00 6a 49 01 00 1a 1d 00 00 39 08 00 00 da 00 00 00 09 00 00 00 01 00 00 00 11 00 00 00 02 00 00 00 12 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 71 e9 00 00 99 84 01 00 c4 24 00 00 54 0b 00 00 e5 01 00 00 2d 00 00 00 59 00 00 00 0d 00 00 00 0a 00 00 00 20 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 e9 07 0a 00 04 b2 0b 00 00 00 01 01 3c 04 3d 05 00 07 04 ff 5c 00 cc 03 56 c9 fc 00 0a 04 01 01 04 07 ff ff 00 95 1d 48 a8 ca 00 00 16 00 28 00 4e 00 90 00 d6 00 c7 00 79 00 3e 00 1f 00 f3 ff eb ff de ff c7 ff b2 ff b6 ff ce ff e2 ff ee ff 38 40 3c 00 00 e6 2a 48 6a 49 01 00 4e 00 6b 00 89 00 9a 00 9f 00 8e 00 71 00 52 00 3a 00 7b ff 4e ff 27 ff 12 ff 0d ff 20 ff 48 ff 77 ff 9d ff 39 41 3d 00 40 8b 48 48 1a 1d 00 00 f7 ff f0 ff e2 ff c8 ff ab ff b2 ff cf ff e8 ff f5 ff 00 00 03 00 04 00 0b 00 0f 00 0c 00 06 00 02 00 ff ff 38 40 3c 00 00 d3 3f 48 39 08 00 00 04 00 06 00 07 00 0e 00 10 00 10 00 0c 00 07 00 08 00 04 00 07 00 10 00 1f 00 2b 00 28 00 17 00 0b 00 05 00 38 40 3c 00 c0 62 2e 48 da 00 00 00 04 00 04 00 07 00 07 00 07 00 05 00 04 00 04 00 03 00 02 00 04 00 09 00 0c 00 0d 00 07 00 04 00 01 00 01 00 39 41 3d 00 80 aa 25 48 09 00 00 00 01 00 02 00 01 00 fe ff 00 00 01 00 01 00 02 00 04 00 02 00 ff ff 02 00 04 00 03 00 02 00 00 00 ff ff 00 00 39 41 3d 00 80 f2 1c 48 01 00 00 00 01 00 01 00 02 00 01 00 00 00 ff ff 00 00 00 00 00 00 00 00 01 00 00 00 01 00 01 00 00 00 00 00 00 00 01 00 38 40 3c 00 c0 4e 21 48 11 00 00 00 ff ff fe ff 00 00 fe ff fc ff fd ff fd ff 00 00 fe ff 00 00 ff ff ff ff 00 00 ff ff 00 00 ff ff 01 00 00 00 38 40 3c 00 c0 06 2a 48 02 00 00 00 02 00 00 00 04 00 ff ff 01 00 ff ff 03 00 ff ff 01 00 00 00 fe ff 00 00 01 00 01 00 00 00 ff ff 00 00 ff ff 39 41 3d 00 c0 62 2e 48 12 00 00 00 04 00 05 00 05 00 02 00 03 00 03 00 05 00 04 00 05 00 04 00 03 00 01 00 03 00 03 00 04 00 02 00 04 00 03 00 39 41 3d 00 00 95 1d 48 71 e9 00 00 24 00 39 00 62 00 a9 00 e7 00 c7 00 79 00 42 00 25 00 e9 ff e2 ff d6 ff c3 ff b0 ff b6 ff c9 ff dc ff e7 ff 00 08 04 00 00 e6 2a 48 99 84 01 00 5b 00 77 00 93 00 a9 00 b4 00 a6 00 85 00 63 00 46 00 75 ff 4f ff 29 ff 0c ff fd fe 05 ff 2e ff 5e ff 89 ff 01 09 05 00 40 8b 48 48 c4 24 00 00 eb ff e3 ff d5 ff bb ff a2 ff ad ff cf ff e3 ff f1 ff 0b 00 0f 00 0e 00 14 00 18 00 15 00 15 00 0f 00 0b 00 00 08 04 00 00 d3 3f 48 54 0b 00 00 02 00 05 00 06 00 0a 00 0e 00 0c 00 0a 00 06 00 07 00 0b 00 10 00 19 00 26 00 34 00 2d 00 1d 00 12 00 0b 00 00 08 04 00 c0 62 2e 48 e5 01 00 00 fb ff fd ff fe ff 00 00 ff ff fe ff fc ff fe ff fb ff 0e 00 12 00 15 00 18 00 16 00 12 00 0e 00 0b 00 0a 00 01 09 05 00 80 aa 25 48 2d 00 00 00 02 00 ff ff 00 00 fe ff fd ff ff ff 00 00 01 00 ff ff 07 00 06 00 06 00 08 00 06 00 05 00 05 00 05 00 04 00 01 09 05 00 80 f2 1c 48 59 00 00 00 f9 ff f6 ff f8 ff f7 ff f8 ff f7 ff f8 ff f5 ff f8 ff 03 00 03 00 06 00 04 00 05 00 08 00 06 00 08 00 05 00 00 08 04 00 c0 4e 21 48 0d 00 00 00 fe ff 02 00 01 00 00 00 03 00 03 00 ff ff 00 00 04 00 02 00 03 00 01 00 03 00 02 00 00 00 03 00 02 00 02 00 00 08 04 00 c0 06 2a 48 0a 00 00 00 fb ff fc ff f9 ff fd ff fd ff f9 ff f8 ff f9 ff fa ff ff ff 03 00 00 00 01 00 01 00 02 00 03 00 03 00 02 00 01 09 05 00 c0 62 2e 48 20 01 00 00 0e 00 0d 00 0f 00 0a 00 0c 00 09 00 09 00 0b 00 06 00 f4 ff f3 ff f3 ff f4 ff f4 ff f6 ff f6 ff f7 ff f6 ff 01 09 05 00 62 00 10 00 3c f9 03 00 40 20 04 00 01 04 00 00 01 04 07 80 ff 0b 04 00 00 00 00 00...

Irp(index=74, irp_id=11985, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:01 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x1a
1a 00 00 de 10 00 00 00 00 00 d7 10 00 00 00 ff 00 00 0b 08 00 00 00 00 00 00 00 00 00 5f 00 10 00 3b 04 00 00 02 09 06 01 ff ff ff ff ff ff ff ff 59 00 40 00 13 00 13 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 15 00 15 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5a 00 94 00 08 00 00 00 0a 00 00 00 1a 00 00 00 01 3f 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 00 00 11 00 00 00 25 00 00 00 31 47 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 3f 00 00 31 47 00 00 ff ff 00 00 3c 04 00 00 00 09 02 ff 5c 00 8c 01 42 c1 fc 00 04 02 01 01 04 09 ff ff 00 50 c3 46 08 00 00 00 ff ff fe ff ff ff fe ff fe ff ff ff ff ff fe ff fe ff ff ff fe ff fe ff ff ff fe ff fe ff fe ff ff ff ff ff 38 40 3c 00 00 e6 aa 46 0a 00 00 00 fd ff fd ff fc ff fc ff fd ff fe ff fe ff fd ff fc ff 00 00 ff ff 00 00 00 00 ff ff 01 00 00 00 00 00 00 00 38 40 3c 00 00 b1 1e 47 1a 00 00 00 fd ff fd ff fe ff fc ff fb ff fb ff fc ff fc ff fe ff 00 00 01 00 ff ff ff ff ff ff 00 00 00 00 ff ff ff ff 38 40 3c 00 00 e6 2a 47 01 3f 00 00 fd ff fd ff fd ff 01 00 00 00 01 00 01 00 fe ff fe ff f0 ff e4 ff cf ff a8 ff 81 ff 88 ff b3 ff d7 ff e9 ff 38 40 3c 00 00 50 c3 46 08 00 00 00 fe ff fd ff fe ff fe ff fe ff fe ff fe ff fd ff fd ff fd ff fd ff fd ff fe ff fe ff fc ff fd ff fd ff ff ff 00 08 04 00 00 e6 aa 46 11 00 00 00 fb ff fc ff fb ff fb ff fc ff fb ff fb ff fc ff fa ff fe ff 00 00 fe ff fe ff 01 00 00 00 ff ff 00 00 01 00 00 08 04 00 00 b1 1e 47 25 00 00 00 fb ff fc ff fa ff fa ff fa ff fc ff f9 ff fb ff fa ff fe ff ff ff fe ff 00 00 ff ff ff ff fe ff 00 00 fe ff 00 08 04 00 00 e6 2a 47 31 47 00 00 fe ff fe ff ff ff ff ff 00 00 01 00 fd ff fd ff fa ff e9 ff db ff c3 ff 9d ff 79 ff 8a ff b8 ff d6 ff e9 ff 00 08 04 00 62 00 10 00 98 08 00 00 00 00 00 00 01 00 03 00 03 02 09 80 5f 00 10 00 3b 04 00 00 05 0a 06 01 ff ff ff ff ff ff ff ff 59 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5a 00 94 00 f5 50 00 00 f5 14 00 00 d0 33 00 00 82 1c 00 00 c9 01 00 00 d4 29 00 00 90 38 00 00 f4 13 00 00 25 19 00 00 82 21 00 00 aa 2c 00 00 34 21 00 00 3a 31 00 00 68 06 00 00 7a 30 00 00 3a 0f 00 00 c5 65 00 00 a1 19 00 00 b1 4d 00 00 a4 1f 00 00 ca 08 00 00 e4 35 00 00 80 36 00 00 b9 0e 00 00 10 27 00 00 82 1c 00 00 01 31 00 00 b4 1d 00 00 ba 5e 00 00 91 07 00 00 a8 5f 00 00 3d 15 00 00 f5 50 00 00 c5 65 00 00 ff ff 06 0e 3c 04 ff ff 00 0a 05 ff 5c 00 0c 06 75 cb fc 00 10 05 01 01 04 0a ff ff 40 8b 48 48 f5 50 00 00 ff ff 01 00 0a 00 18 00 29 00 27 00 14 00 09 00 03 00 e2 ff d8 ff c2 ff 9b ff 76 ff 7e ff a7 ff c6 ff d6 ff 38 40 3c 00 00 d3 3f 48 f5 14 00 00 01 00 fa ff f7 ff f2 ff ee ff ee ff f0 ff f6 ff fd ff e8 ff e5 ff dc ff cb ff b9 ff bb ff d0 ff dd ff e3 ff 38 40 3c 00 c0 62 2e 48 d0 33 00 00 f0 ff e6 ff dd ff d6 ff d8 ff de ff e7 ff f1 ff f8 ff bf ff b0 ff a0 ff 96 ff 94 ff 9e ff ac ff bc ff c7 ff 39 41 3d 00 80 aa 25 48 82 1c 00 00 25 00 30 00 3b 00 43 00 43 00 3a 00 2e 00 26 00 1d 00 1b 00 28 00 2f 00 34 00 35 00 33 00 28 00 1a 00 0e 00 39 41 3d 00 40 8b 48 48 c9 01 00 00 17 00 14 00 10 00 08 00 fc ff fe ff 0b 00 13 00 16 00 e4 ff e4 ff e6 ff e8 ff eb ff e8 ff e4 ff e1 ff df ff 38 40 3c 00 00 d3 3f 48 d4 29 00 00 1f 00 22 00 2a 00 39 00 44 00 40 00 35 00 26 00 1e 00 fb ff 04 00 14 00 30 00 4e 00 47 00 24 00 0b 00 fe ff 38 40 3c 00 c0 62 2e 48 90 38 00 00 c9 ff b3 ff 9c ff 8e ff 8c ff 99 ff b0 ff c8 ff d9 ff e6 ff e4 ff e2 ff e2 ff e0 ff df ff e0 ff e3 ff e5 ff 39 41 3d 00 80 aa 25 48 f4 13 00 00 e2 ff d5 ff c6 ff bd ff bc ff c3 ff d0 ff df ff ec ff 05 00 0c 00 11 00 16 00 16 00 10 00 09 00 00 00 fe ff 39 41 3d 00 40 8b 48 48 25 19 00 00 03 00 06 00 0a 00 14 00 1f 00 1d 00 11 00 0c 00 07 00 e1 ff db ff d2 ff c3 ff b6 ff b7 ff c4 ff d1 ff d9 ff 38 40 3c 00 00 d3 3f 48 82 21 00 00 02 00 fc ff f0 ff dc ff c7 ff cb ff e2 ff f4 ff fe ff fd ff 03 00 12 00 2b 00 49 00 41 00 20 00 07 00 fb ff 38 40 3c 00 c0 62 2e 48 aa 2c 00 00 22 00 25 00 2a 00 2b 00 2d 00 2b 00 27 00 22 00 1f 00 28 00 3e 00 53 00 5f 00 61 00 53 00 3f 00 28 00 17 00 39 41 3d 00 80 aa 25 48 34 21 00 00 25 00 31 00 3e 00 46 00 46 00 3d 00 31 00 25 00 1d 00 15 00 22 00 31 00 3b 00 3c 00 30 00 20 00 13 00 09 00 39 41 3d 00 40 8b 48 48 3a 31 00 00 20 00 22 00 24 00 2b 00 31 00 31 00 27 00 23 00 20 00 d9 ff d4 ff ca ff b6 ff 9b ff a1 ff bc ff cf ff d7 ff 38 40 3c 00 00 d3 3f 48 68 06 00 00 10 00 0a 00 05 00 fa ff ea ff ed ff 00 00 0a 00 0d 00 e7 ff e7 ff e4 ff e0 ff de ff de ff df ff e3 ff e3 ff 38 40 3c 00 c0 62 2e 48 7a 30 00 00 2c 00 35 00 3f 00 41 00 43 00 43 00 39 00 2d 00 24 00 c0 ff b8 ff ac ff a8 ff a7 ff ab ff b4 ff be ff c8 ff 39 41 3d 00 80 aa 25 48 3a 0f 00 00 f2 ff eb ff e4 ff df ff df ff e2 ff ec ff f1 ff f8 ff df ff d9 ff d0 ff ca ff cb ff cf ff d6 ff da ff e2 ff 39 41 3d 00 40 8b 48 48 c5 65 00 00 f4 ff f8 ff 03 00 14 00 21 00 1b 00 05 00 f7 ff f3 ff cb ff be ff a8 ff 84 ff 62 ff 72 ff 99 ff b7 ff c7 ff 00 08 04 00 00 d3 3f 48 a1 19 00 00 0e 00 0a 00 05 00 03 00 00 00 fd ff fd ff 02 00 09 00 df ff d9 ff d0 ff bf ff af ff b6 ff c9 ff d6 ff de ff 00 08 04 00 c0 62 2e 48 b1 4d 00 00 09 00 02 00 f7 ff ef ff ef ff f3 ff fc ff 05 00 0c 00 a2 ff 93 ff 83 ff 77 ff 74 ff 7a ff 8a ff 9b ff a7 ff 01 09 05 00 80 aa 25 48 a4 1f 00 00 2b 00 32 00 3d 00 47 00 48 00 42 00 37 00 2d 00 24 00 13 00 20 00 29 00 31 00 36 00 36 00 29 00 19 00 0e 00 01 09 05 00 40 8b 48 48 ca 08 00 00 34 00 33 00 2d 00 23 00 1b 00 20 00 2e 00 36 00 38 00 d6 ff d6 ff d6 ff d8 ff d9 ff d8 ff d3 ff d3 ff d0 ff 00 08 04 00 00 d3 3f 48 e4 35 00 00 33 00 38 00 41 00 4d 00 56 00 54 00 4a 00 40 00 39 00 ff ff 08 00 19 00 37 00 50 00 43 00 21 00 09 00 f9 ff 00 08 04 00 c0 62 2e 48 80 36 00 00 dc ff c8 ff b0 ff 9f ff 98 ff a5 ff b9 ff d1 ff e7 ff d2 ff cd ff cb ff cb ff c8 ff c8 ff c9 ff cf ff d2 ff 01 09 05 00 80 aa 25 48 b9 0e 00 00 ee ff e1 ff d5 ff c9 ff c4 ff cb ff d9 ff e9 ff f7 ff fe ff 02 00 07 00 0d 00 0d 00 09 00 03 00 fd ff f7 ff 01 09 05 00 40 8b 48 48 10 27 00 00 fd ff ff ff 09 00 13 00 1c 00 16 00 09 00 01 00 fc ff ca ff c5 ff bb ff ae ff a0 ff a5 ff b1 ff bc ff c6 ff 00 08 04 00 00 d3 3f 48 82 1c 00 00 0a 00 01 00 f7 ff df ff cb ff d3 ff e8 ff fb ff 06 00 fc ff 03 00 12 00 2c 00 43 00 37 00 16 00 03 00 f8 ff 00 08 04 00 c0 62 2e 48 01 31 00 00 39 00 3c 00 3f 00 41 00 44 00 41 00 3f 00 3a 00 36 00 1e 00 31 00 45 00 55 00 59 00 52 00 3b 00 24 00 0f 00 01 09 05 00 80 aa 25 48 b4 1d 00 00 27 00 32 00 3d 00 45 00 46 00 41 00 36 00 2c 00 22 00 09 00 19 00 27 00 31 00 34 00 28 00 18 00 0c 00 00 00 01 09 05 00 40 8b 48 48 ba 5e 00 00 4e 00 54 00 59 00 61 00 69 00 63 00 5d 00 55 00 53 00 cb ff c6 ff b8 ff a1 ff 8d ff 99 ff b2 ff c2 ff cb ff 00 08 04 00 00 d3 3f 48 91 07 00 00 23 00 21 00 19 00 0c 00 01 00 06 00 18 00 20 00 23 00 de ff dc ff d9 ff d4 ff d4 ff d2 ff d6 ff d8 ff d8 ff 00 08 04 00 c0 62 2e 48 a8 5f 00 00 45 00 4e 00 56 00 5b 00 62 00 63 00 58 00 4a 00 3f 00 a3 ff 9a ff 91 ff 8a ff 86 ff 88 ff 91 ff 9e ff a7 ff 01 09 05 00 80 aa 25 48 3d 15 00 00 fb ff f4 ff ed ff e9 ff e6 ff ea ff ef ff f6 ff fd ff d3 ff cd ff c3 ff bd ff bb ff bf ff c7 ff cf ff d5 ff 01 09 05 00 62 00 10 00 4a 97 00 00 50 92 00 00 01 00 00 00 04 05 0a 80 5f 00 10 00 3b 04 00 00 06 0a 06 01 ff ff ff ff ff ff ff ff 59 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5a 00 94 00 10 10 00 00 34 2a 00 00 31 1f 00 00 f5 05 00 00 b9 00 00 00 92 30 00 00 f5 21 00 00 34 12 00 00 74 27 00 00 b4 0e 00 00 fa 16 00 00 39 29 00 00 90 17 00 00 24 07 00 00 05 14 00 00 d9 13 00 00 54 1c 00 00 bd 3b 00 00 34 29 00 00 85 0a 00 00 b5 06 00 00 ba 3a 00 00 22 29 00 00 4a 23 00 00 ad 2f 00 00 45 0b 00 00 c9 1d 00 00 a9 24 00 00 71 45 00 00 cd 09 00 00 25 0d 00 00 89 32 00 00 92 30 00 00 71 45 00 00 ff ff 0b 0f 3c 04 ff ff 00 0a 06 ff 5c 00 0c 06 22 ce fc 00 10 06 01 01 04 0a ff ff 40 8b 48 48 10 10 00 00 11 00 17 00 1f 00 30 00 40 00 3b 00 29 00 19 00 0e 00 ec ff ee ff ef ff f5 ff fc ff fb ff f4 ff f0 ff f0 ff 38 40 3c 00 00 d3 3f 48 34 2a 00 00 ee ff e8 ff d8 ff b9 ff 9a ff a1 ff c4 ff dd ff e8 ff 01 00 ff ff fe ff f6 ff ec ff ed ff fa ff ff ff 02 00 38 40 3c 00 c0 62 2e 48 31 1f 00 00 37 00 47 00 53 00 59 00 59 00 57 00 47 00 36 00 29 00 03 00 02 00 04 00 06 00 08 00 05 00 05 00 03 00 02 00 39 41 3d 00 80 aa 25 48 f5 05 00 00 11 00 16 00 18 00 18 00 19 00 1a 00 16 00 0f 00 09 00 e6 ff e2 ff e2 ff e4 ff e2 ff df ff e2 ff e6 ff ed ff 39 41 3d 00 40 8b 48 48 b9 00 00 00 e8 ff ec ff f0 ff fa ff 08 00 02 00 f3 ff ea ff e4 ff 10 00 0f 00 0e 00 0b 00 0b 00 0c 00 0d 00 0e 00 10 00 38 40 3c 00 00 d3 3f 48 92 30 00 00 eb ff e8 ff df ff d5 ff c9 ff ca ff d6 ff df ff e5 ff f9 ff ee ff db ff bd ff 9f ff a3 ff c9 ff e2 ff f2 ff 38 40 3c 00 c0 62 2e 48 f5 21 00 00 d1 ff c6 ff be ff bc ff b7 ff b9 ff c3 ff ce ff d8 ff e6 ff d9 ff ce ff c6 ff c6 ff ce ff d8 ff e5 ff ec ff 39 41 3d 00 80 aa 25 48 34 12 00 00 d6 ff cb ff c3 ff bf ff bc ff bf ff c9 ff d2 ff db ff 08 00 07 00 08 00 07 00 06 00 0a 00 09 00 06 00 07 00 39 41 3d 00 40 8b 48 48 74 27 00 00 15 00 1c 00 28 00 3f 00 56 00 50 00 34 00 1e 00 12 00 fd ff 03 00 0e 00 22 00 34 00 31 00 1c 00 0c 00 04 00 38 40 3c 00 00 d3 3f 48 b4 0e 00 00 fc ff 00 00 09 00 20 00 3a 00 33 00 15 00 01 00 f9 ff f6 ff f5 ff f2 ff ef ff ec ff eb ff ee ff f1 ff f4 ff 38 40 3c 00 c0 62 2e 48 fa 16 00 00 1e 00 24 00 2d 00 31 00 31 00 2b 00 22 00 19 00 11 00 22 00 2b 00 35 00 39 00 3b 00 3a 00 2e 00 24 00 19 00 39 41 3d 00 80 aa 25 48 39 29 00 00 2c 00 3b 00 45 00 4b 00 4d 00 49 00 3b 00 29 00 1d 00 20 00 2c 00 3b 00 44 00 44 00 3d 00 2e 00 21 00 17 00 39 41 3d 00 40 8b 48 48 90 17 00 00 de ff dd ff e2 ff e8 ff f0 ff ef ff e4 ff de ff dc ff ef ff eb ff e3 ff cd ff b4 ff bc ff d8 ff ea ff f2 ff 38 40 3c 00 00 d3 3f 48 24 07 00 00 fd ff f8 ff f1 ff e4 ff d6 ff d8 ff e9 ff f3 ff f8 ff 02 00 02 00 ff ff fb ff f8 ff f8 ff fc ff 00 00 01 00 38 40 3c 00 c0 62 2e 48 05 14 00 00 1f 00 2a 00 31 00 33 00 36 00 34 00 29 00 1c 00 14 00 eb ff e1 ff d8 ff d2 ff d1 ff d6 ff df ff e9 ff f3 ff 39 41 3d 00 80 aa 25 48 d9 13 00 00 d7 ff d1 ff c9 ff c5 ff c5 ff c7 ff cf ff d4 ff db ff ed ff e5 ff df ff db ff d8 ff dd ff e4 ff ed ff f2 ff 39 41 3d 00 40 8b 48 48 54 1c 00 00 25 00 2e 00 36 00 48 00 54 00 4f 00 41 00 30 00 27 00 e1 ff e2 ff e4 ff e9 ff f2 ff ed ff e2 ff df ff dc ff 00 08 04 00 00 d3 3f 48 bd 3b 00 00 db ff d2 ff c1 ff a7 ff 8a ff 98 ff ba ff d1 ff de ff f4 ff f3 ff ee ff e4 ff db ff e2 ff ed ff f4 ff f7 ff 00 08 04 00 c0 62 2e 48 34 29 00 00 3c 00 48 00 57 00 5f 00 66 00 63 00 56 00 43 00 34 00 07 00 0c 00 0b 00 0d 00 0c 00 0d 00 0b 00 07 00 05 00 01 09 05 00 80 aa 25 48 85 0a 00 00 07 00 0d 00 0f 00 11 00 16 00 19 00 15 00 0c 00 03 00 da ff d6 ff d7 ff d6 ff d1 ff cd ff d0 ff d4 ff d9 ff 01 09 05 00 40 8b 48 48 b5 06 00 00 bb ff bc ff c4 ff cf ff d9 ff d2 ff bf ff b7 ff b7 ff 11 00 12 00 10 00 0f 00 0e 00 0f 00 12 00 12 00 15 00 00 08 04 00 00 d3 3f 48 ba 3a 00 00 d3 ff cc ff c8 ff bc ff b5 ff b8 ff bf ff c8 ff cd ff fa ff ed ff db ff ba ff 9f ff aa ff cd ff e9 ff f6 ff 00 08 04 00 c0 62 2e 48 22 29 00 00 cc ff c3 ff bc ff b5 ff af ff af ff b6 ff c3 ff d0 ff e2 ff d9 ff cc ff c4 ff c1 ff c7 ff d3 ff e2 ff eb ff 01 09 05 00 80 aa 25 48 4a 23 00 00 bf ff b6 ff ad ff a8 ff a1 ff a3 ff ac ff b7 ff c2 ff fc ff fb ff fc ff fa ff fd ff fe ff 00 00 fd ff fe ff 01 09 05 00 40 8b 48 48 ad 2f 00 00 25 00 2d 00 38 00 51 00 62 00 5c 00 44 00 30 00 23 00 f9 ff 00 00 0c 00 20 00 33 00 29 00 16 00 07 00 fa ff 00 08 04 00 00 d3 3f 48 45 0b 00 00 f1 ff f7 ff 04 00 1d 00 2f 00 25 00 07 00 f4 ff ed ff eb ff e8 ff e7 ff e5 ff e6 ff e4 ff e7 ff eb ff ea ff 00 08 04 00 c0 62 2e 48 c9 1d 00 00 1f 00 26 00 2f 00 35 00 38 00 31 00 2a 00 22 00 1a 00 24 00 30 00 36 00 3e 00 43 00 41 00 37 00 28 00 1e 00 01 09 05 00 80 aa 25 48 a9 24 00 00 1d 00 2a 00 36 00 3c 00 45 00 44 00 37 00 26 00 17 00 1c 00 28 00 36 00 40 00 44 00 3e 00 2f 00 21 00 15 00 01 09 05 00 40 8b 48 48 71 45 00 00 bb ff bb ff c1 ff c8 ff cf ff ca ff bd ff b6 ff b3 ff c3 ff bb ff af ff 9a ff 84 ff 92 ff ab ff bd ff c6 ff 00 08 04 00 00 d3 3f 48 cd 09 00 00 f1 ff ee ff e5 ff da ff ce ff d3 ff e3 ff ee ff f2 ff 07 00 05 00 04 00 fe ff fd ff 00 00 04 00 05 00 0a 00 00 08 04 00 c0 62 2e 48 25 0d 00 00 0e 00 18 00 22 00 26 00 2f 00 2e 00 24 00 14 00 09 00 f9 ff ef ff ea ff e2 ff de ff e0 ff e8 ff f3 ff fd ff 01 09 05 00 80 aa 25 48 89 32 00 00 b5 ff ad ff a9 ff a1 ff a0 ff a2 ff a9 ff b0 ff b5 ff d8 ff d2 ff ca ff c5 ff c3 ff ca ff cf ff d8 ff e0 ff 01 09 05 00 62 00 10 00 4a 97 00 00 50 92 00 00 01 00 00 00 04 06 0a 80 ff 0b 04 00 00 00...
```

### id11987
request
```
Irp(index=75, irp_id=11987, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:01 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539996448, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 01 02 00 00 00 00 00 00 00 00 70 17 00 
```

### id11990 onwards

- `0x0d` frame of 7448 long
- `0x0b` frame of 7488
- ```
  Irp(index=78, irp_id=11996, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:01 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660522121888, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
  REQUEST with 16 data, first byte: 0x09
  09 8e a5 02 02 00 00 00 00 00 00 00 00 70 17 0
  ```
- `0x0c` frame of 7448 long
- `0x0b` frame of 7448 long
- `0x1a` frame of 7448 long
- `0x0d` frame of 7448 long
- `0x0b` frame of 7448 long
- `0x0c` frame of 7448 long
- `0x0b` frame of 7448 long
- ```
  Irp(index=86, irp_id=12029, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660519598368, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
  REQUEST with 16 data, first byte: 0x09
  09 8e a5 03 02 00 00 00 00 00 00 00 00 70 17 00 

  Irp(index=87, irp_id=12033, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539996448, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
  REQUEST with 16 data, first byte: 0x09
  09 8e a5 04 02 00 00 00 00 00 00 00 00 70 17 00 
  ```
- `0x1a` frame of 7448 long
- `0x0d` frame of 7448 long
- ```
  Irp(index=90, irp_id=12040, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539660416, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
  REQUEST with 16 data, first byte: 0x09
  09 8e a5 05 02 00 00 00 00 00 00 00 00 70 17 00 
  ```
- `0x0b` frame of 7448 long
- ```
  Irp(index=92, irp_id=12047, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660421327648, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
  REQUEST with 16 data, first byte: 0x09
  09 8e a5 06 02 00 00 00 00 00 00 00 00 70 17 00 
  ```

... and so on

Interesting parts continue with;

```
Irp(index=143, irp_id=12270, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298778288, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x0b
0b 00 00 5e 05 00 00 00 00 00 57 05 00 00 00 ff 00 <more data>
Irp(index=144, irp_id=12272, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660298781504, data=[], previous_mode=<Mode.KernelMode: 1>, requestor_mode=<Mode.KernelMode: 1>, ioctl=720907, irp_type=<IrpType.IRPComp: 7>)
response with 7488 data, first byte: 0x1a
1a 00 00 de 10 00 00 00 00 00 d7 10 00 00 00 ff 00 00 0b 08 00 00 00 00 00 <more data>
```

and then, *without* the `0x6e` frame we've seen in other (nonboot) logs from Windows, we get the digitizer ID;
```
Irp(index=145, irp_id=12275, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660539001120, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a1 00 00 00 00 00 00 00 00 00 00 00 00 00 

Irp(index=146, irp_id=12277, function=<Function.InternalDeviceControl: 9>, time='2024-01-28 6:30:02 PM', status=<Status.STATUS_SUCCESS: 1>, address=18446694660541876512, data=[], previous_mode=<Mode.UserMode: 2>, requestor_mode=<Mode.UserMode: 2>, ioctl=721297, irp_type=<IrpType.IRP: 6>)
REQUEST with 16 data, first byte: 0x09
09 8e a5 15 02 00 00 00 00 ad f7 d8 97 70 17 00 
````



