#!/usr/bin/env bash
iface=$(basename "$(readlink -f /sys/class/tty/ttyUSB0/device)")   # e.g. 1-2:1.0
dev=${iface%%:*}                                                    # e.g. 1-2
echo -n "$dev" | sudo tee /sys/bus/usb/drivers/usb/unbind
sleep 1
echo -n "$dev" | sudo tee /sys/bus/usb/drivers/usb/bind
ls -l /dev/ttyUSB*     # confirm which node it comes back as

# NOTE cable problem. USB-A end very sensitive to movement.
# NOTE monitor with sudo dmesg -w
