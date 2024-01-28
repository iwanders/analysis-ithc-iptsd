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


