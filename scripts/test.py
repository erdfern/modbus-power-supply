#!/usr/bin/env python3
"""Rigorous round-trip test of the HM310T protection registers (OVP / OCP / OPP).

For each protection it:
  1. saves the current setting,
  2. writes a battery of integer counts (OPP includes the 16-bit word boundary),
  3. reads them back and demands an EXACT count match,
  4. always restores the original setting.

Output is kept OFF throughout and no load is required -- these are just
setting registers. Counts are the device's native units, verified on-device:
  OVP  x100  (cV)        register 0x0020
  OCP  x1000 (mA)        register 0x0021
  OPP  x1000 (mW)        registers 0x0022/0x0023, 32-bit, high word first
"""

from pyHM310T import PowerSupply

PORT, SLAVE = "/dev/ttyUSB0", 1

# name -> (registers [high word first], counts-per-unit, test set-points)
PROTECTIONS = {
    "OVP": ([0x0020],         100,  [0.00, 0.01, 5.55, 12.34, 12.345, 29.99, 30.00]),
    "OCP": ([0x0021],         1000, [0.000, 0.001, 0.555, 2.345, 9.999, 10.000]),
    "OPP": ([0x0022, 0x0023], 1000, [0.000, 0.001, 12.345, 65.535,   # stays in low word
                                     65.536, 66.000, 150.000, 300.000]),  # needs high word
}


def read_raw(ps, regs):
    """Read the (possibly 32-bit) register group; None if any word fails."""
    raw = 0
    for r in regs:
        word = ps.read_register(r)
        if word is None:
            return None
        raw = (raw << 16) | word
    return raw


def write_raw(ps, regs, raw):
    """Write an integer across the register group, high word first."""
    for i, r in enumerate(regs):
        ps.write_register(r, (raw >> (16 * (len(regs) - 1 - i))) & 0xFFFF)


def main():
    ps = PowerSupply(port=PORT, slave=SLAVE)
    npass = nfail = 0
    try:
        ps.disable_output()

        for name, (regs, scale, points) in PROTECTIONS.items():
            hexregs = " ".join(f"0x{r:04X}" for r in regs)
            original = read_raw(ps, regs)
            if original is None:
                print(f"\n== {name} ({hexregs}) ==  !! could not read; SKIPPED")
                nfail += 1
                continue
            print(f"\n== {name}  regs[{hexregs}]  x{scale}  saved={original / scale:g} ==")

            try:
                for sp in points:
                    expected = round(sp * scale)          # the device's integer grid
                    write_raw(ps, regs, expected)
                    got = read_raw(ps, regs)
                    ok = (got == expected)
                    npass += ok
                    nfail += not ok
                    got_s = "--" if got is None else str(got)
                    val_s = "--" if got is None else f"{got / scale:.3f}"
                    print(f"   {sp:>9.3f} -> {expected:>7} cnt | "
                          f"read {got_s:>7} cnt = {val_s:>9} [{'PASS' if ok else 'FAIL'}]")
            finally:
                write_raw(ps, regs, original)             # always restore
                ok = (read_raw(ps, regs) == original)
                npass += ok
                nfail += not ok
                print(f"   restored {original / scale:g} "
                      f"[{'OK' if ok else 'RESTORE FAILED'}]")

        print(f"\n=== {npass} passed, {nfail} failed ===")
        return nfail == 0
    finally:
        ps.close()                                        # release /dev/ttyUSB0


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
