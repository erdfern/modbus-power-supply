#!/usr/bin/env python3
"""One-shot: set the Hanmatek HM310T to precise V / I / OVP / OCP / OPP.

Output is forced OFF while set-points change, then every value is read
back and verified. The serial port is always released on exit.
"""

from pyHM310T import PowerSupply

PORT  = "/dev/ttyUSB0"
SLAVE = 1

# ---- targets -- edit these -----------------------------------------
VOLTAGE = 12.00    # V   0.01 V steps
CURRENT = 0.300    # A   0.001 A steps
OVP     = 12.50    # V   0.01 V steps
OCP     = 0.500     # A   0.001 A steps
OPP     = 320.000   # W   0.001 W steps  (keep above your intended V x I)
# --------------------------------------------------------------------

# (name, registers [high word first], counts-per-unit) for this unit.
# OCP and OPP scaling is x1000, verified on-device -- the OEM doc's
# "2 decimal places" is wrong for both. OPP is a 32-bit value split
# across two registers, mirroring the 3-decimal power display.
# Protections are written first so the operating point lands inside them.
TARGETS = [
    ("OVP",     [0x0020],         100,  OVP),
    ("OCP",     [0x0021],         1000, OCP),
    ("OPP",     [0x0022, 0x0023], 1000, OPP),   # 32-bit: high word, then low
    ("Voltage", [0x0030],         100,  VOLTAGE),
    ("Current", [0x0031],         1000, CURRENT),
]

ps = PowerSupply(port=PORT, slave=SLAVE)
try:
    ps.disable_output()          # never move set-points into a live output

    for _, regs, scale, value in TARGETS:
        # round(), NOT int(): int(12.35*100) == 1234 -> 12.34 V. round() is exact.
        raw = round(value * scale)
        for i, reg in enumerate(regs):                 # split into 16-bit words,
            shift = 16 * (len(regs) - 1 - i)           # high word first
            ps.write_register(reg, (raw >> shift) & 0xFFFF)

    # read back and verify
    print(f"{'param':<9}{'target':>9}{'readback':>10}")
    all_ok = True
    for name, regs, scale, value in TARGETS:
        raw, failed = 0, False
        for reg in regs:
            word = ps.read_register(reg)               # None if the read errored out
            if word is None:
                failed = True
                break
            raw = (raw << 16) | word                   # recombine high..low
        if failed:
            all_ok = False
            print(f"{name:<9}{value:>9.3f}{'--':>10}   <-- NO READ")
            continue
        actual    = raw / scale
        quantized = round(value * scale) / scale          # best the grid allows
        ok        = abs(actual - quantized) < 0.5 / scale  # within one LSB == exact
        all_ok   &= ok
        print(f"{name:<9}{value:>9.3f}{actual:>10.3f}{'' if ok else '   <-- DIFFERS'}")

    print("\nAll values programmed as requested."
          if all_ok else
          "\nSome values differ -- device clamped them or a write was dropped.")
finally:
    ps.close()                   # release /dev/ttyUSB0 for the next run
