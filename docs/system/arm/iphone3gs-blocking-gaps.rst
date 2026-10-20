iPhone 3GS / iOS 6: blocking gaps and port map
================================================

Status
------

This document identifies the blockers that prevent the current iphone3gs
machine from booting iOS 6. It is intentionally explicit about what is not
implemented. The current board is a hardware bring-up skeleton, not a working
iPhone emulator.

The reference used for the S5L8920 register map is the public
samhenrigold/qemu-ios implementation of the S5L8920/S5L8922 family. That
code is useful as a porting reference, but it is not a drop-in source file:
it depends on many device models and QEMU APIs which are not currently present
in this branch. Each dependency must be ported and built before enabling it.

Blocking dependency order
-------------------------

1. NAND page-store format and real image geometry
   The upstream IOP owns the NAND page store; the H2FMI device reads and writes
   pages through that shared store. Its geometry.json describes page_bytes,
   spare_bytes, pages_per_block, blocks_per_ce, ce_per_bus, buses, chip_id
   and storage_format. Files are named bus<b>-ce<c>.pages. A blank image is
   erased flash, not a bootable filesystem. Do not guess the N88AP chip ID or
   geometry from a different board's image.

2. IOP device at 0x86300000
   Upstream reference: hw/arm/s5l8930_iop.c and declarations in
   hw/arm/s5l8930.h. It depends on the NAND image backend, block-backend
   handling, QEMU JSON parsing, a shared page store, and optionally the IOP
   core. The reference has an explicit fw-size-mask option for S5L8920.
   An empty IOP register stub cannot satisfy iBoot or the iOS NAND driver.

3. H2FMI controllers at 0x81200000 and 0x81300000
   Upstream reference: hw/arm/s5l8930_h2fmi.c. It depends on the IOP page
   store and CDMA. The reference exposes separate FMI, FMC and ECC windows;
   the board config also supplies FMC/ECC offsets and compatibility options.
   It must be connected to CPU-visible IRQ lines and the CDMA pacing interface.
   Merely mapping the address range would hide MMIO faults without making NAND reads work.

4. CDMA and its paced FIFO contracts
   The H2FMI reference calls into the S5L8930 CDMA implementation for DMA
   transfers. Port the CDMA model and helper interfaces before enabling H2FMI.
   Confirm the S5L8920 version/configuration and IRQ numbers rather than
   assuming the A4 defaults are identical.

5. IOP execution / firmware ABI
   The upstream reference can either emulate host-visible IOP behavior or run
   an IOP core, depending on firmware generation. iOS 6-era firmware cannot
   be assumed to work with an older ring-message HLE. Establish the actual
   N88AP IOP firmware ABI before choosing the execution path. An IPSW inventory
   script does not decrypt firmware or supply the immutable BootROM.

6. Boot chain
   A genuine BootROM (or a clearly documented replacement boot path), a
   compatible LLB/iBoot stage, correct NAND contents, DeviceTree and kernel
   handoff are still required. The -bios option only loads an externally
   supplied image; it does not create Apple's BootROM. Restore ramdisks and
   root filesystem images are not substitutes for the boot NAND.

7. Remaining board peripherals
   USB/DFU and restore flow, display, GPIO/PMU, clock/reset behavior, I2C,
   SDIO, baseband-facing interfaces and remaining interrupt routing must be
   implemented or deliberately stubbed with evidence that the selected boot
   stage does not need them.

Current branch inventory
-------------------------

Implemented as preliminary models:
* iPhone 3GS machine registration, Cortex-A8 CPU and memory map.
* CHIPID identity words and an optional external -bios image.
* PMGR timer registers and preliminary VIC wiring.
* SPI0 and a serial NOR model with an optional writable overlay.
* IPSW/bootchain inventory helpers and smoke-test scaffolding.

Not implemented as a functional iOS 6 boot path:
* S5L8920 IOP, NAND page store and H2FMI.
* S5L8920 CDMA integration and its DMA pacing contracts.
* Verified PL192 behavior and complete device IRQ map.
* N88AP boot NAND dump, real BootROM, working LLB/iBoot handoff.
* Display, USB/DFU restore, and complete peripheral set.
* Verified successful boot of the iOS 6 kernel.

Porting rule
------------

Port dependency clusters in this order: shared NAND image backend -> IOP page
store/device -> CDMA model and FIFO pacing -> H2FMI -> IRQ wiring -> tests with
a known-good NAND fixture -> firmware boot handoff. Do not copy just the IOP or
H2FMI C file and add it to Meson: that would leave missing symbols, incorrect
storage semantics, or a build that never reaches runtime.

Validation required for each stage
----------------------------------

* Compile the iphone3gs target with warnings treated as failures where practical.
* Unit-test NAND geometry validation, erased-page reads, page program/erase,
  spare/meta bytes and overlay persistence.
* Test H2FMI command/address/status and ECC register behavior against known
  traces or fixtures.
* Verify CDMA FIFO pacing and IRQ assertions independently.
* Only claim an iOS boot milestone after a reproducible log reaches the kernel
  entry point and shows progress beyond early MMIO initialization.
