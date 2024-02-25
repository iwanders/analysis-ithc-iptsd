# Notes

This is the new dumping ground of discoveries and notes, such that the README.md file can stay clean.


## On Open questions

### Does the screen report which MPP version was used?

`IptsPenMetadata` Does not seem to carry this information it is pretty much identical between all three pens;


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
- C: Increments, but only every 7 entries, This matches seq from IptsPenGeneral. Oh, Quo filed a PR that includes this as group id. Makes sense as it only increments once for each group of frames.
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

The flags may indicate contact with the screen;
```
IptsPenDetection: 98 03 02 00 48 01 02 00 01 03 00 00 05 0a 0b 80 
IptsPenDetection: 40 30 04 00 20 4f 04 00 01 04 00 00 02 0d 08 80 
IptsPenDetection: 50 58 00 00 50 4e 00 00 01 03 00 00 00 01 06 80 
IptsPenDetection: 3c f9 03 00 40 20 04 00 04 03 03 00 07 04 07 80 
IptsPenDetection: 4c 04 00 00 00 00 00 00 01 03 03 00 03 02 09 80 
IptsPenDetection: 4a 97 00 00 50 92 00 00 04 00 00 00 04 05 0a 80 
IptsPenDetection: 4a 97 00 00 50 92 00 00 04 00 00 00 04 06 0a 80 
IptsPenDetection: 98 03 02 00 48 01 02 00 04 03 03 00 05 0a 0b 80 
                                         |c |
```
The `c` column does seem to switch from `01` to `04`, but not much else here.


## IptsMagnitude
```
 2A 13 29 14 01 FF FF FF 00 00 .. u32[n]?
|x1|y1|x2|y2|-----------| u32 x[IPTS_COLUMNS + 2] ... | u32[2] (0x00) | u32 y[IPTS_ROWS + 2]
```
- x1 and x2 are always one apart, order varies. They can go to 255 (pen raised?)
- y1 and y2 are always one apart, order varies. They can go to 255 (pen raised?)
- Are these measurement strength, one of the patents refers to ratio of the two hightest bins for positioning.

```
./irpmon_thcbase.py comparison  --limit 1000  ../irp_logs_thcbase/2024_02_11_irp_thcbase_diginfo_3pen/2024_02_11_irp_thcbase_slim_pen_2.log.gz ../irp_logs_thcbase/2024_02_11_irp_thcbase_diginfo_3pen/2024_02_11_irp_thcbase_metapen_m1.log.gz ../irp_logs_thcbase/2024_02_11_irp_thcbase_diginfo_3pen/2024_02_11_irp_thcbase_metapen_m2.log.gz
```

## IptsTouchedAntennas
All zeros in this, but my recordings have pure pen. Seems to again hold C =from IptsPenMetadata, perhaps packed bitmask?

## IptsDataSelection
Depends on the DFT window, third byte from the end is dft window type. From [imhex.md](./imhex.md):

For the majority of frames, the beginning holds the 16 magnitudes for x and y. The end block is always 12 bytes and holds the dft window type.



