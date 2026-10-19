iPhone 3GS / iOS 6.0 firmware investigation
===========================================

Target IPSW: 'iPhone2,1_6.0_10A403_Restore.ipsw' (ProductType
'iPhone2,1', build '10A403').

Current board status
--------------------

The separate 'iphone3gs' QEMU machine is now registered behind CONFIG_IPHONE3GS.
It is an early hardware scaffold, not an iOS-capable emulator yet. It uses the
Cortex-A8 CPU model, 256 MiB DRAM at 0x40000000, a low alias of the first DRAM
page, 256 KiB SRAM at 0x84000000, and an unimplemented peripheral window.
It intentionally does not reuse the iPhone 3G's S5L8900 devices or ARM1176 CPU.

Implemented pieces now include the N88AP CHIPID fuse words, a 24 MHz
PMGR timebase with two event timers, SPI0, and a 1 MiB SPI-NOR command model
with an optional writable overlay. The two PMGR timer IRQ outputs are now routed to VIC inputs 6 and 5. The
three-VIC cascade remains a PL190 approximation and is not yet validated as a
faithful S5L8920 PL192 implementation; other device IRQs remain unconnected.

The remaining peripheral range logs as unimplemented. The NAND/IOP storage path,
flash controller, genuine BootROM, complete boot-chain loader, display, USB,
baseband, and iOS 6 kernel boot path are still missing. QEMU being able to create the machine is
only a registration/initialization test; it does not prove firmware
compatibility.

Create erased-flash test files (not bootable firmware) with::

   python3 scripts/ios/create-iphone3gs-nor.py ./nor-test

Then run with a separate read-only base and writable overlay::

   build/qemu-system-arm -machine iphone3gs,nor=./nor-test/nor.bin,nor-rw=./nor-test/nor-rw.bin -S -display none

Both files must be exactly 1 MiB. Do not point nor-rw at the same file as nor.
Blank images contain no NVRAM or boot firmware; use a compatible NOR dump only
if you have one obtained lawfully.

Inspect and extract firmware payloads
-------------------------------------

After downloading the IPSW from Apple's CDN, run::

   python3 scripts/ios/inspect-iphone3gs-ios6.py /path/to/iPhone2,1_6.0_10A403_Restore.ipsw

The script validates the IPSW ZIP and its Info.plist, checks the target
product/version/build, then extracts restore manifests and N88AP boot/NOR
payloads under .artifacts/firmware/iphone3gs-6.0-10A403/. It writes a
SHA-256 inventory. The IPSW is intentionally not committed to Git.

Experimental Termux build
-------------------------

In Termux, install the usual build tools and libraries if missing::

   pkg update
   pkg install clang make ninja pkg-config python git glib libpixman libslirp libusb libfdt

Then run::

   bash scripts/ios/build-termux.sh

This attempts a headless ARM system-emulator build. It is an experimental
host-compatibility check; Android/Bionic differs from desktop Linux, so a
successful build must be confirmed on the actual device. The headless
configuration does not provide a graphical display.

Firmware and storage boundaries
-------------------------------

* NAND is emulator-owned persistent storage. The IPSW does not contain a
  ready-to-use NAND dump; the N88AP geometry, ECC/OOB layout, controller, and
  initialization still need to be implemented.
* BootROM is immutable code in the physical device's silicon and is not
  present as an extractable IPSW file. Do not label a zero-filled placeholder
  as a real BootROM.
* NOR firmware payloads can be extracted from the IPSW's all_flash directory,
  but a usable NOR device still requires correct flash geometry, erase/write
  behavior, and boot-chain integration.
* The existing iphone3g-* restore and boot targets remain specific to the
  iPhone 3G. Do not use them to restore an N88AP firmware image.


Boot-chain inventory (read-only)
--------------------------------

To inventory the IPSW's candidate boot stages and record SHA-256 hashes::

   python3 scripts/ios/inspect-iphone3gs-bootchain.py /path/to/iPhone2,1_6.0_10A403_Restore.ipsw --json bootchain.json

The report lists candidate LLB, iBSS, iBEC, device-tree, kernel-cache and
restore/root-filesystem payloads when present, and marks the IMG3 magic where
visible. This is an inventory aid only: it does not decrypt IMG3 files, verify
Apple signatures, infer missing keys, or run the boot chain. The next boot-flow
implementation still needs a real reset-ROM handoff, verified stage-specific
loading/addressing, and the correct NAND/IOP storage semantics.

NAND/IOP and interrupt-controller status
----------------------------------------

The current VIC cascade is only a PL190-compatible approximation for three
controller windows; it is not yet a verified S5L8920 PL192 model, and no
NAND/IOP interrupt sources are connected. The iPhone 3GS NAND path is not
implemented. Do not treat a directory of synthetic pages or a blank flash
image as a real NAND dump: page geometry, OOB/ECC, bad-block handling, FTL/VFL
metadata, IOP ownership and persistence need a compatible implementation and
tests before firmware can use it.
