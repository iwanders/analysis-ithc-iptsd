# Breakdown of messages from windows

First bytes of messages coming from the driver.

The multiple records on `0x1a` is not a bug in the parser, data actually contains this, and it appears to be unique.

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