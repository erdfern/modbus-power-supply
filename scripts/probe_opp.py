from pyHM310T import PowerSupply

ps = PowerSupply(port="/dev/ttyUSB0", slave=1)
try:
    hi, lo = ps.read_register(0x0022), ps.read_register(0x0023)
    print(f"OPP regs 0x0022/0x0023 -> {hi!r} / {lo!r}")
    print(f"protection status 0x0002 -> {ps.read_register(0x0002):#06b}")
finally:
    ps.close()
