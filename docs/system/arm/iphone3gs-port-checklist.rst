iPhone 3GS board-port checklist
===============================

Status: research notes; no iPhone 3GS board is registered by this document.

Identity and SoC
----------------

* Restore product: iPhone2,1.
* Board identifier: N88AP (case-insensitive spelling n88ap appears in firmware paths).
* SoC: Samsung/Apple S5L8920 family, not the S5L8900 used by the current iphone3g machine.
* CPU family: ARM Cortex-A8-class ARMv7, rather than the ARM1176 CPU selected by the current iPhone 3G board.
* iOS target in this branch: iOS 6.0, build 10A403.

The current hw/arm/iphone3g.c directly instantiates S5L8900 peripherals, its 64 KiB boot-ROM mapping, and an ARM1176 CPU. Reusing that machine unchanged and only changing the machine description would not model the 3GS correctly.

Implementation order
--------------------

1. Add and test S5L8920 CPU/SoC memory map and interrupt/timer/clock controllers.
2. Model board-specific NAND/NOR and the 3GS boot chain without assuming that 3G flash geometry is reusable.
3. Add required display, USB, GPIO, I2C/SPI, PMU, and other peripherals incrementally; distinguish implemented behavior from placeholders in logs and documentation.
4. Register a separate iphone3gs machine and Kconfig symbol. Keep iphone3g and its existing tests unchanged.
5. Add qtests for reset vectors, MMIO IDs, flash persistence, interrupts, and firmware loading before attempting the iOS kernel.
6. Run the build/test workflow, then test IPSW-specific boot stages. A successful QEMU compile alone is not evidence that iOS starts.

Reference implementation research
---------------------------------

The public samhenrigold/qemu-ios project contains separate S5L8920 device implementations, including DART, PMGR, and PWM models. These can inform a future port, but should not be copied blindly: their interfaces, device coverage, licenses, and QEMU revision must be checked against this repository before integration.

* https://github.com/samhenrigold/qemu-ios
* https://github.com/iDroid-Project/openiBoot/tree/master/plat-s5l8920
* https://github.com/axi0mX/ipwndfu

Firmware extraction boundary
----------------------------

The IPSW inspection script extracts firmware files actually present in the restore package. It cannot extract the silicon BootROM, and it does not synthesize a valid NAND or NOR image. The BootROM mapping required by a machine is a model of the address space; it must not be confused with possession of Apple's immutable ROM bytes.
