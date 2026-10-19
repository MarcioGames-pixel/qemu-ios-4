iPhone 3GS / iOS 6.0 firmware investigation
===========================================

Target IPSW: 'iPhone2,1_6.0_10A403_Restore.ipsw' (ProductType
'iPhone2,1', build '10A403').

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
   pkg install clang make ninja pkg-config python git glib pixman libslirp libusb libfdt

Then run::

   bash scripts/ios/build-termux.sh

This attempts a headless ARM system-emulator build. It is an experimental
host-compatibility check; Android/Bionic differs from desktop Linux, so a
successful build must be confirmed on the actual device. The headless
configuration does not provide a graphical display.

Important implementation boundary
---------------------------------

This extraction step does not make the existing iPhone 3G machine compatible
with the 3GS. The current machine is for iPhone1,2 / N82AP and iOS 4.2.1; the
3GS needs a separate iPhone2,1 / N88AP machine model, including its SoC and
peripherals, boot sequence, storage geometry, and firmware-specific restore
flow. The Linux workflow is only a compile smoke test, not proof that iOS 6
boots.

* NAND is an emulator-owned persistent storage image. The IPSW does not
  contain a ready-to-use NAND dump; its geometry and initialization must be
  implemented for the target board.
* BootROM is immutable code in the physical device's silicon and is not
  present as an extractable IPSW file. Do not label a zero-filled placeholder
  as a real BootROM.
* NOR firmware payloads can be extracted from the IPSW's all_flash directory,
  but a usable NOR image still requires the target machine's correct flash
  geometry and programming behavior.
* The existing iphone3g-* make targets remain specific to the iPhone 3G. Do
  not use them to restore an N88AP firmware image.
