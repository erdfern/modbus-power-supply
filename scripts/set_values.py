"""One-shot: set the Hanmatek HM310T to precise V / I / OVP / OCP.

Output is forced OFF while set-points change, then every value is read
back and verified. The serial port is always released on exit.
"""

from pyHM310T import PowerSupply

PORT  = "/dev/ttyUSB0"
SLAVE = 1

# ---- targets -- edit these -----------------------------------------
VOLTAGE = 12.00    # V   0.01 V steps
CURRENT = 0.300    # A   0.001 A steps
OVP     = 12.20    # V   0.01 V steps
OCP     = 0.50     # A   0.01 A steps  (10 mA grid -- coarser than I set-point)
# --------------------------------------------------------------------

# (name, register, counts-per-unit) straight from the HM310T modbus map.
# Protections are written first so the operating point lands inside them.
TARGETS = [
    ("OVP",     0x0020, 100,  OVP),
    ("OCP",     0x0021, 100,  OCP),
    ("Voltage", 0x0030, 100,  VOLTAGE),
    ("Current", 0x0031, 1000, CURRENT),
]

ps = PowerSupply(port=PORT, slave=SLAVE)
try:
    ps.disable_output()          # never move set-points into a live output

    for _, reg, scale, value in TARGETS:
        # round(), NOT int(): int(12.35*100) == 1234 -> 12.34 V. round() is exact.
        ps.write_register(reg, round(value * scale))

    # read back and verify
    print(f"{'param':<9}{'target':>9}{'readback':>10}")
    all_ok = True
    for name, reg, scale, value in TARGETS:
        raw = ps.read_register(reg)       # None if the read errored out
        if raw is None:
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
