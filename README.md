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

I'm not sure if tilt is correctly captured by this. Holding the pen in the middle, with the pen touching the screen at an angle and rotating with the wrist does result in mostly correct tiltx and tilty, except at the ends where tilty goes into the wrong sign.


# Writeup

Current understanding;

- Linux data is 'wrong'; See linux time series plot of `pos` `REAL_0_0` and `IMAG_0_0`, this is always positive and jumps.
- Windows data is different, and there `pos_from_pos` looks great. `ring_pos_from_pos` still leaves much to be desired.
- Well, or so I thought, diagonal recording on windows; `2024_02_04_intelthcbase_bootlog_diagonal_wiggle_linux` also makse for wriggly lines.
- Metapen M1, without tilt doesn't have any of the wiggling issues, but the three with tilt do.
- For barrel button, seems when button depressed only has row 0's at high magnitude, rest at zero. While not pressed 2 or 3 are high. But this results in too many buttons pressed.


# Other data dumps

Should probably figure out how to load the dumps from [here](https://github.com/quo/iptsd/issues/5#issuecomment-1193124454), to compare against Slim Pen 1, but the `DeviceInfo` in that reports a `buffer_size` of `18374686479679160320`, format probably changed?
