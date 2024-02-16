# Breakdown of messages from windows

First bytes of messages coming from the driver.

The multiple records on `0x1a` is not a bug in the parser, data actually contains this, and it appears to be unique.


This pattern, and the sizes of individual packets are identical between Slim Pen2, Metapen M1, Metapen M2.

```
0x1a: {'type': 26, 'unknown': 0, 'size': 4318, 'outer_size': 4311}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsDftWindowButton  0x5c, {'type': 92, 'flags': 0, 'size': 396}
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsDftWindow  0x5c, {'type': 92, 'flags': 0, 'size': 1548}, dft data type: 0x0a
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsDftWindow  0x5c, {'type': 92, 'flags': 0, 'size': 1548}, dft data type: 0x0a
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
0x0d: {'type': 13, 'unknown': 0, 'size': 1982, 'outer_size': 1975}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsReport  0x80, {'type': 128, 'flags': 0, 'size': 100}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsTouchedAntennas  0x5e, {'type': 94, 'flags': 0, 'size': 28}
    IptsDftWindowPressure  0x5c, {'type': 92, 'flags': 0, 'size': 1548}
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
0x0b: {'type': 11, 'unknown': 0, 'size': 1374, 'outer_size': 1367}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsReport  0x80, {'type': 128, 'flags': 0, 'size': 100}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsDftWindow  0x5c, {'type': 92, 'flags': 0, 'size': 972}, dft data type: 0x08
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
0x0c: {'type': 12, 'unknown': 0, 'size': 1750, 'outer_size': 1743}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsPenGeneral  0x57, {'type': 87, 'flags': 0, 'size': 64}
    IptsReport  0x80, {'type': 128, 'flags': 0, 'size': 100}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsMagnitude  0x5b, {'type': 91, 'flags': 0, 'size': 464}
    IptsTouchedAntennas  0x5e, {'type': 94, 'flags': 0, 'size': 28}
    IptsDftWindowPosition  0x5c, {'type': 92, 'flags': 0, 'size': 780}
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
0x0b: {'type': 11, 'unknown': 0, 'size': 1374, 'outer_size': 1367}
    IptsPenMetadata  0x5f, {'type': 95, 'flags': 0, 'size': 16}
    IptsReport  0x80, {'type': 128, 'flags': 0, 'size': 100}
    IptsNoiseMetricsOutput  0x59, {'type': 89, 'flags': 0, 'size': 64}
    IptsDataSelection  0x5a, {'type': 90, 'flags': 0, 'size': 148}
    IptsDftWindowPosition2  0x5c, {'type': 92, 'flags': 0, 'size': 972}
    IptsPenDetection  0x62, {'type': 98, 'flags': 0, 'size': 16}
```

In messages, following, let `----` denote never changes.

## IptsPenGeneral
64 bytes
```
 50 4e 4a 00 9a 99 99 41  49 9e 00 00 00 00 01 02 FF FF ...
|A          |------------|seq        |--------|  |------
```
A: 16 bit counter:
  - Slim pen 2 increments at 288207-288358
  - Metapen M1 increments at 287894-289429
  - Metapen M2 increments at 287894-288279
Seq; Counter only got below 16 bit counts in recording. Seq matches IptsPenMetadata.C


## IptsPenMetadata
16 bytes
```
 23 9d 00 00 01 06 06 01 ff ff ff ff ff ff ff ff
|C          |T |R |------------------------------
```
- C: Increments, but only every 7 entries, This matches seq from IptsPenGeneral.
- T: C increments if this is `0x01`, sequence is             `0x01, 0x04, 0x02, 0x05, 0x06, 0x0a, 0x0d`
- R: Follows C? T at `0x01` has this at `0x06`, sequence is: `0x06, 0x07, 0x09, 0x0a, 0x0a, 0x0b, 0x08`

No differences between the pens.

## IptsPenDetection
16 bytes
```
 10 0c 01 00 c8 13 01 00 01 00 00 00 02 0d 08 80 
| D1  |F1|--| D2  |F2|.... Fn...
```
D1 and D2 seem to be values relating to each other.
Unique D1 & D2 pairs, for Metapen M1:
```
  920    328 
 1100      0 
 2200      0 
 5652   5012 
12352  20256 
16561  23666 
19365  18728 
22608  20048 
32998  32850 
38730  37456 
63804   8256 
```

For Metapen M2 and Slim Pen 2:
```
  920    328 
 1100      0 
 2200      0 
 3088   5064 
 5652   5012 
12352  20256 
16561  23666 
19365  18728 
22608  20048 
32998  32850 
38730  37456 
63804   8256 
65103   2064 
```

## IptsMagnitude
```
 2A 13 29 14 01 FF FF FF 00 00 .. u32[n]?
|x1|y1|x2|y2|-----------|
```
- x1 and x2 are always one apart, order varies. They can go to 255 (pen raised?)
- y1 and y2 are always one apart, order varies. They can go to 255 (pen raised?)
- Are these measurement strength, one of the patents refers to ratio of the two hightest bins for positioning.
- Currently `y` is off by 5 values...?  Maybe the `FF` section is larger.

```
./irpmon_thcbase.py comparison  --limit 1000  ../irp_logs_thcbase/2024_02_11_irp_thcbase_diginfo_3pen/2024_02_11_irp_thcbase_slim_pen_2.log.gz ../irp_logs_thcbase/2024_02_11_irp_thcbase_diginfo_3pen/2024_02_11_irp_thcbase_metapen_m1.log.gz ../irp_logs_thcbase/2024_02_11_irp_thcbase_diginfo_3pen/2024_02_11_irp_thcbase_metapen_m2.log.gz
```
