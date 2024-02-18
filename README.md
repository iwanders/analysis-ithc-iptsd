# Pen analysis

```
nix develop .
./analyse.py ./spiral_out.json.gz
```

# Microsoft docs

https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/windows-pen-states  describes the state diagram for pens in windows. Also describes area of palm rejection.

https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/haptic-pen-implementation-guide describes haptic things.


# FCC

https://fccid.io/C3K1962

But that only pertains to the BLE device in it.

# IRPMon

Enable logging:
```
.\IRPMonc.exe --input=D:\\.\irpmndrv --hook-driver=ICD:\Driver\IntelTHCBase --boot-log=1 --strip-data=0 --save-settings=1
```

On capturing IntelTHCBase in the gui, don't use the upp one, use one level up in the hierarchy.

Disable logging:

```
.\IRPMonc.exe --input=D:\\.\irpmndrv --unhook-driver=\Driver\IntelTHCBase --boot-log=0 --save-settings=1
```

# DigiInfo

From Microsoft's [additional-testing-tools](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/simultaneous-pen-and-touch-validation#additional-testing-tools), there's a tool called `DigiInfo.exe` that can be used for digitizer validation, it conveniently allows recording and exporting all touch events. [direct link](https://download.microsoft.com/download/C/8/7/c8729e82-feca-482b-801d-f65979615003/digiinfo-19h1.zip).


# Writeup

Current understanding;

- Linux data is 'wrong'; See linux time series plot of `pos` `REAL_0_0` and `IMAG_0_0`, this is always positive and jumps.
- Windows data is different, and there `pos_from_pos` looks great. `ring_pos_from_pos` still leaves much to be desired.
- Well, or so I thought, diagonal recording on windows; `2024_02_04_intelthcbase_bootlog_diagonal_wiggle_linux` also makse for wriggly lines.
- Metapen M1, without tilt doesn't have any of the wiggling issues, but the three with tilt do.


- We can extract the phase from `pos` and `pos2`, row 1;

```
        append(f"pos_iq_const_1:*", (pos.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
        append(f"pos2_iq_const_1:*", (pos2.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][REAL], pos2.x[i].iq[int(IPTS_DFT_PRESSURE_ROWS / 2)][IMAG]))
```
They jump, but they jump at different points in time.


# Tip & ring distance
Can we calculate the tip and ring distance using the estimated positions when we are in contact? If the positions are offset by the pen position, we should get a sphere?
