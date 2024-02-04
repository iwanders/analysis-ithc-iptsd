# Pen analysis

```
nix develop .
./analyse.py ./spiral_out.json.gz
```


# FCC

https://fccid.io/C3K1962

But that only pertains to the BLE device in it.

# IRPMon

Enable logging:
```
.\IRPMonc.exe --input=D:\\.\irpmndrv --hook-driver=ICD:\Driver\IntelTHCBase --boot-log=1 --strip-data=0 --save-settings=1
```

Disable logging:

```
.\IRPMonc.exe --input=D:\\.\irpmndrv --unhook-driver=\Driver\IntelTHCBase --boot-log=0 --save-settings=1
```

# Writeup

Current understanding;

- Linux data is 'wrong'; See linux time series plot of `pos` `REAL_0_0` and `IMAG_0_0`, this is always positive and jumps.
- Windows data is different, and there `pos_from_pos` looks great. `ring_pos_from_pos` still leaves much to be desired.
- Well, or so I thought, diagonal recording on windows; `2024_02_04_intelthcbase_bootlog_diagonal_wiggle_linux` also makse for wriggly lines.


- We can extract the phase from `pos` and `pos2`, row 1;

```
        append(f"pos_iq_const_1:*", (pos.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        append(f"pos2_iq_const_1:*", (pos2.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
```
They jump, but they jump at different points in time.

