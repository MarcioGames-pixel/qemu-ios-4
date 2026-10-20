# iPhone 3GS Android app (development)

This is a separate Android application project in the `android-iphone3gs-app` branch. It provides the first UI prototype: a centered, original vector-drawn iPhone silhouette with an iOS 6-inspired placeholder screen.

**Important:** this is not yet an iPhone emulator. The QEMU CPU/device runtime is not linked into the APK, and the button explicitly reports that limitation. No Apple firmware is included.

## Build locally

Install JDK 17, Android SDK platform 35 and Gradle 8.9 or newer, then run from this directory:

```sh
gradle assembleDebug
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`.

## Next integration milestones

1. Build the relevant QEMU ARM softmmu target for Android/NDK and resolve unsupported host features.
2. Add a JNI bridge for QEMU lifecycle, CPU execution, memory, serial logs and shutdown.
3. Replace the placeholder screen with a framebuffer surface fed by the emulated display.
4. Add user-selected firmware/NAND files and persistence; do not bundle copyrighted Apple firmware.
5. Validate boot stages progressively and expose logs in the app.

The device preview is drawn with Android Canvas and original shapes; it does not copy the linked Wikipedia SVG or Apple icons.
