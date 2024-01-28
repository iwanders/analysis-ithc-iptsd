# Pen analysis

```
nix develop .
./analyse.py ./spiral_out.json.gz
```


# FCC

https://fccid.io/C3K1962

But that only pertains to the BLE device in it.


# Writeup

Current understanding;

- Linux data is 'wrong'; See linux time series plot of `pos` `REAL_0_0` and `IMAG_0_0`, this is always positive and jumps.
- Windows data is different, and there `pos_from_pos` looks great. `ring_pos_from_pos` still leaves much to be desired.


