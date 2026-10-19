#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
BUILD_DIR="$ROOT/build-termux"

if [ ! -d "$ROOT/.git" ]; then
  echo "Run this from a cloned qemu-ios-4 repository." >&2
  exit 2
fi
if [ "$(uname -s)" != Linux ] || [ ! -d /data/data/com.termux/files/usr ]; then
  echo "This helper is for Termux on Android; use scripts/ios/bootstrap-macos.sh on macOS." >&2
  exit 2
fi

missing=""
for command_name in clang make ninja pkg-config python git; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    missing="$missing $command_name"
  fi
done
if [ -n "$missing" ]; then
  printf 'Missing commands:%s\n' "$missing" >&2
  echo "Install build tools with: pkg install clang make ninja pkg-config python git" >&2
  exit 2
fi

for package in libglib libpixman libslirp libusb libfdt; do
  if ! pkg list-installed 2>/dev/null | grep -q "^$package/"; then
    echo "Optional dependency may be missing: pkg install $package" >&2
  fi
done

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

"$ROOT/configure" \
  --target-list=arm-softmmu \
  --enable-tcg \
  --disable-cocoa \
  --disable-gtk \
  --disable-sdl \
  --disable-werror \
  --disable-docs \
  --prefix="$BUILD_DIR/install"

ninja
"$BUILD_DIR/qemu-system-arm" --version
"$BUILD_DIR/qemu-system-arm" -machine help | grep -i iphone3g
echo
echo "Build succeeded. This configuration is headless (no SDL/Cocoa display)."
echo "It does not make the iPhone 3GS/iOS 6 machine supported; the existing"
echo "iphone3g machine still targets iPhone 3G/N82AP and iOS 4."
