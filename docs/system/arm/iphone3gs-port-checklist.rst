iPhone 3GS board-port checklist
===============================

Status: an early iPhone3GS machine scaffold is registered; the S5L8920
peripherals and iOS boot flow are not implemented.

Identity and SoC
----------------

* Restore product: iPhone2,1.
* Board identifier: N88AP (case-insensitive spelling n88ap appears in firmware paths).
* SoC: Samsung/Apple S5L8920 family, not the S5L8900 used by the current iphone3g machine.
* CPU family: ARM Cortex-A8-class ARMv7, rather than the ARM1176 CPU selected by the current iPhone 3G board.
* iOS target in this branch: iOS 6.0, build 10A403.

The new hw/arm/iphone3gs.c registers a distinct machine, uses a Cortex-A8,
maps 256 MiB DRAM at 0x40000000, maps the first DRAM page at physical zero,
maps 256 KiB SRAM at 0x84000000, and marks the S5L8920 peripheral window as
unimplemented. It intentionally does not reuse S5L8900 peripherals. This is a
compile/initialization scaffold, not a working iOS emulator.

Implementation order
--------------------

1. Replace the broad unimplemented peripheral window with verified S5L8920
   devices, beginning with chip ID, PMGR/clock, interrupt controllers, and
   timers. Use the N88AP device tree and register-level evidence; do not guess
   register values from the iPhone 3G.
2. Implement board-specific NAND/NOR and the 3GS boot chain without assuming
   that 3G flash geometry is reusable. Add persistence and ECC/OOB tests.
3. Add required display, USB, GPIO, I2C/SPI, PMU, and other peripherals
   incrementally; distinguish implemented behavior from placeholders in logs.
4. Add firmware loading/restore stages for the iPhone2,1 iOS 6.0 build and
   test each stage separately before attempting the kernel.
5. Add qtests for reset behavior, MMIO IDs, flash persistence, interrupts, and
   firmware loading. Keep iphone3g and its existing tests unchanged.
6. Test Linux CI first, then the Termux/Bionic host separately. A successful
   QEMU compile alone is not evidence that iOS starts.

Reference implementation research
---------------------------------

The public samhenrigold/qemu-ios project contains S5L8920 and related device
models. The N88AP board data and device implementations are useful reference
material, but importing the complete implementation is a larger port because
this repository does not currently contain all of its dependent devices and
helpers. Any imported code must retain compatible licensing and be adapted to
this QEMU revision.

* https://github.com/samhenrigold/qemu-ios
* https://github.com/iDroid-Project/openiBoot/tree/master/plat-s5l8920

Firmware extraction boundary
----------------------------

The IPSW inspection script extracts firmware files actually present in the
restore package. It cannot extract the silicon BootROM, and it does not
synthesize a valid NAND or NOR image. The BootROM mapping required by a
machine must not be confused with possession of Apple's immutable ROM bytes.
