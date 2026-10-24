# Installation and First Steps

Follow the instructions for the exact release you download; installer screens and requirements may change between versions.

## Before installing

1. Check the [GitHub Releases page](https://github.com/Nic69Han/BinixX-OS/releases) for an installation ISO.
2. Read the release notes and [hardware compatibility guide](HARDWARE-COMPATIBILITY.md).
3. Check that your essential applications have Linux versions or acceptable alternatives.
4. Back up Documents, Desktop, Pictures, Music, Videos, Downloads, browser bookmarks, email archives, and application-specific data to a separate drive or trusted cloud service.
5. Keep any Windows product key and BitLocker recovery key if you may need them later.

**Warning:** Installing BinixX OS may erase the selected disk. Verify the target disk and confirm that your backup is complete before proceeding.

## Create installation media

Use a trusted USB imaging tool to write the downloaded ISO to a USB drive. Writing an ISO usually erases the USB drive. Follow the imaging tool's instructions and safely eject the drive when finished.

Container images in the GitHub Container Registry are used by the image-based update workflow; they are not bootable ISO downloads.

## Boot and install

1. Connect the USB drive.
2. Open the computer's one-time boot menu or firmware settings and select the USB device.
3. Follow the installer prompts to select a language, keyboard layout, time zone, and target disk.
4. If offered, enable **Encrypt my data** unless you have a specific reason not to.
5. Review the proposed disk changes carefully before confirming.

Firmware menus vary by manufacturer. Consult your computer manufacturer's documentation if the USB device does not appear.

## First start

Complete the initial desktop setup and connect to your network. Then:

- Open **System Settings** and check display, sound, keyboard, language, Wi-Fi, and Bluetooth.
- Open KDE Discover to install supported applications.
- Open **Welcome to BinixX OS** for first-run guidance, application alternatives, migration help, and support tools.
- Check for system updates and reboot when an update is ready to apply.
- Create a backup before moving important work onto the new system.

## If something does not work

Check [Hardware Compatibility](HARDWARE-COMPATIBILITY.md), then [Troubleshooting](TROUBLESHOOTING.md). A virtual-machine test cannot prove that Wi-Fi, graphics, audio, sleep, fingerprint readers, or other devices will work on every physical computer.

Review the release status and known limitations before using the system for critical work.
