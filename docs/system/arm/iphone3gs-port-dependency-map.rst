iPhone 3GS porting backlog: upstream dependency map
==================================================

This file is a porting checklist, not a claim that these components are already
ported. The current N88AP prototype deliberately does not register fake NAND
or IOP devices that would accept MMIO writes without matching the real protocol.

Reference
---------

The S5L8920 reference implementation is in
https://github.com/samhenrigold/qemu-ios, especially `hw/arm/s5l8920.c`.
That board reuses parts of the S5L8930/A4 model family, but its complete board
initialization is not a drop-in replacement for the iPhone 3GS.

Required dependency order
-------------------------

1. **Storage image layer**
   - Port and review the NAND page-store helper and its geometry/overlay rules.
   - Establish N88AP NAND chip ID, bus count, CE population, page/spare geometry,
     pages per block, blocks per CE, and storage format from reliable evidence.
   - Keep base images read-only and writes in a separate overlay.
   - Add tests for erased pages, OOB/spare bytes, sparse holes, overlay precedence,
     persistence, and malformed geometry before attaching it to a guest-visible
     controller.

2. **IOP / NAND page-store owner**
   - Port the AP-visible IOP control/mailbox model and its page-store ownership
     contract, but do not assume the A4/N18 firmware ABI matches N88AP.
   - Determine whether the correct N88AP IOP firmware is available and which
     protocol revision it uses. High-level emulation and running the second core
     are separate approaches; do not mix their state ownership.
   - Wire the IOP IRQ output into the appropriate controller only after the N88AP
     interrupt map is verified.

3. **H2FMI controller**
   - Port the two H2FMI register windows and the FMC/ECC subwindows as one
     compatible implementation.
   - Reuse the same NAND page store as the IOP so iBoot and the kernel see
     consistent contents.
   - Wire CDMA FIFO pacing, completion/status bits, ECC status and IRQs. A
     register-only stub is not sufficient for boot.

4. **Interrupt controller**
   - Replace/validate the PL190 approximation against the S5L8920's three PL192
     controller windows and N88AP interrupt routing.
   - Verify priority, enable, software interrupt, FIQ and chained output behavior.
   - Test timer, SPI, NAND/H2FMI and IOP interrupts independently.

5. **Boot handoff**
   - Identify and validate each N88AP stage (LLB, iBoot/iBEC where applicable,
     device tree, kernelcache and restore ramdisk) from the exact iPhone2,1 iOS 6
     build.
   - Add a documented loader only after stage format, entry address, memory
     layout, boot arguments and signature/decryption requirements are understood.
   - Keep the optional external `-bios` interface explicitly separate from a
     genuine BootROM dump. An IPSW is not a silicon BootROM source.

6. **Board peripherals and validation**
   - Add only peripherals required by the selected boot path first: clock/power,
     GPIO, UART/debug, NAND/IOP, USB as needed, then display and baseband.
   - For every device, record address range, IRQ, reset behavior, source/license,
     tests, and known differences from N88AP.
   - Require Linux CI build + QEMU startup smoke test before calling a port complete;
     separately test the Termux build on-device.

Current status
--------------

The branch currently contains the initial machine, CHIPID, PMGR, SPI/NOR,
a preliminary VIC cascade, IPSW inventory tooling, and test scaffolding.
The NAND page store, N88AP IOP, H2FMI/FMC/ECC, validated PL192 behavior, and
complete iOS 6 boot path are still **not implemented**. Blank NOR files are
test fixtures only and must not be described as bootable storage.

Porting policy
--------------

Do not copy the full S5L8930 board initializer into the iPhone 3GS machine:
it creates many A4-specific devices and assumes a different board/firmware
environment. Port leaf devices with their required headers and dependencies,
adapt their addresses/IRQs, then integrate them into `iphone3gs.c` one at a
time. Preserve the iPhone 3G board and its existing boot path.
