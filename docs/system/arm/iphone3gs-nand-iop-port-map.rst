S5L8920 NAND/IOP port map for iPhone 3GS
=========================================

Status
------

This document records the dependency audit for the next implementation phase. It
does not claim that NAND/IOP has been ported or that iOS 6 boots.

The reference implementation is in `samhenrigold/qemu-ios`. Its S5L8920
machine reuses much of the S5L8930/A4 peripheral implementation, but the iPhone
3GS is an S5L8920/N88AP device. Reusing code is safe only after validating
register maps, NAND geometry/chip IDs, IRQ assignments, firmware ABI, and the
QEMU APIs in this checkout.

Upstream components and dependencies
------------------------------------

1. `include/hw/arm/s5l8930.h`
   - Shared register/IRQ constants and device declarations.
   - It is not a drop-in header: it contains A4/K48AP-specific addresses and
     includes other device interfaces. Define a small S5L8920/N88AP header in
     this tree rather than importing all A4 constants blindly.

2. `hw/arm/s5l8930_iop.c`
   - AP-visible IOP control block, mailbox/ring handling, NAND page-store
     ownership, geometry validation, and persistence.
   - Depends on QEMU BlockBackend APIs, QOM properties, JSON/QObject parsing,
     NAND image helpers, and optionally the emulated IOP core.
   - Upstream supports multiple firmware generations. The iOS 6 path must use
     the appropriate IOP firmware ABI; the old HLE ring protocol documented
     for iOS 3.2-4.2 must not be assumed to work for iOS 6.

3. `hw/arm/s5l8930_h2fmi.c`
   - H2FMI/FMC/ECC register windows used by iBoot to identify, read, program,
     erase, and query NAND.
   - Depends on the IOP-owned NAND page store and CDMA FIFO pacing. A fake
     register bank or a flat raw NAND file alone will not satisfy these
     accesses.

4. CDMA and NAND image storage
   - The H2FMI implementation depends on the shared CDMA engine and the
     `nand-image` storage helper. These need to be ported and built before
     H2FMI can be linked and exercised.
   - Keep base NAND images read-only and writes in a separate overlay. Validate
     the manifest, geometry, chip ID, page/spare sizes, and erase/program
     semantics before accepting an image.

5. Firmware/boot flow
   - The IPSW is a package of update/restore payloads, not a silicon BootROM
     dump or a ready-made NAND image. Inventorying IPSW files is not decryption,
     NAND reconstruction, or execution of iBoot.
   - BootROM, iBoot, NAND contents, device tree/boot arguments, and the kernel
     handoff are separate milestones with separate tests.

Required port sequence
----------------------

- [ ] Audit current QEMU API differences for QOM, IRQ, BlockBackend, JSON,
      trace events, migration state, and build-system registration.
- [ ] Port the NAND image storage helper and its geometry/format tests.
- [ ] Port the CDMA behavior required by H2FMI FIFO/DMA transfers.
- [ ] Port the AP-visible IOP and NAND page-store interface with a dedicated
      S5L8920/N88AP configuration (not A4 constants copied without review).
- [ ] Port H2FMI/FMC/ECC windows and wire their IRQs to the correct VIC/IOP
      inputs based on N88AP evidence.
- [ ] Add tests for NAND ID, erased-page status, page read/program, block erase,
      overlay isolation, and malformed geometry rejection.
- [ ] Only then attempt the iBoot NAND discovery/read path, followed by kernel
      boot support.

Acceptance criteria
-------------------

The port is not considered complete until the build passes on the project's
supported host/Android build path and tests demonstrate NAND read/program/erase
and overlay behavior. An iOS 6 boot claim additionally requires a trace showing
the real boot chain progressing beyond the current placeholder reset ROM.

Current implementation in this branch remains a preliminary board model:
CPU/RAM, CHIPID, PMGR timers, early VIC wiring, SPI NOR model, and IPSW inventory
tools. NAND/IOP/H2FMI, a genuine BootROM, and full iOS 6 boot remain outstanding.
