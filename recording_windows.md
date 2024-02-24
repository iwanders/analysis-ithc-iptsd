# Recording Intel Precise touch data on Windows

Use [IRPMon](https://github.com/MartinDrab/IRPMon).

- The driver to capture is `\Driver\IntelTHCBase`
- Enable capturing data.
- Disable data stripping, there's a lot in each frame.
- When capturing IntelTHCBase in the gui, look for `\Driver\IntelTHCBase` then expand everything, but don't use the `UPP:` entry, use one level up in the hierarchy from that one.


## Boot logging

This can only be done from the CLI!

Enable logging:
```
.\IRPMonc.exe --input=D:\\.\irpmndrv --hook-driver=ICD:\Driver\IntelTHCBase --boot-log=1 --strip-data=0 --save-settings=1
```
Disable boot logging:

```
.\IRPMonc.exe --input=D:\\.\irpmndrv --unhook-driver=\Driver\IntelTHCBase --boot-log=0 --save-settings=1
```

# DigiInfo

From Microsoft's [additional-testing-tools](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/simultaneous-pen-and-touch-validation#additional-testing-tools), there's a tool called `DigiInfo.exe` that can be used for digitizer validation, it conveniently allows recording and exporting all touch events. [direct link](https://download.microsoft.com/download/C/8/7/c8729e82-feca-482b-801d-f65979615003/digiinfo-19h1.zip).

I'm not sure if tilt is correctly captured by this. Holding the pen in the middle, with the pen touching the screen at an angle and rotating with the wrist does result in mostly correct tiltx and tilty, except at the ends where tilty goes into the wrong sign.

The [digi_info.py](digi_info.py) file contains a parser for this xml format.
