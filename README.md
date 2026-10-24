# BinixX OS

**A Fedora-based Linux desktop designed to feel familiar to Windows users.**

BinixX OS is a customized, image-based desktop operating system built on Fedora Kinoite technology and KDE Plasma. It combines a Windows 11-inspired desktop layout with Linux applications, system updates designed for rollback, and tools to help users migrate from Windows.

> **Project status:** BinixX OS is an actively developed project. Hardware compatibility and application support vary. Back up your data and test the system before relying on it for everyday work.

## Highlights

- **Familiar desktop:** a Windows-inspired application menu, taskbar, settings categories, light and dark themes, and a custom visual identity.
- **Everyday applications:** discover and install supported applications through KDE Discover and Flathub.
- **Windows transition tools:** guidance for finding Linux alternatives and copying personal files from a Windows installation.
- **System updates with rollback:** the operating system is updated as an image, with the previous deployment available for recovery.
- **Security-conscious defaults:** SELinux enforcing, a read-only system image, a configured firewall, and automated checks for known Fedora security advisories during image builds.
- **Diagnostics and repair:** local diagnostic reports, desktop reset tools, and targeted repair of selected system configuration files.
- **Optional NVIDIA image:** a separate image is available for systems that need the proprietary NVIDIA driver.

These are project design goals and implemented features, not a guarantee that every device or use case will work. See the documentation for current limitations.

## Is BinixX OS right for you?

BinixX OS is intended for desktop users who want a Windows-familiar interface while using Linux software.

Before installing, check that:
- your essential applications are available for Linux or have a workable alternative;
- your computer's Wi-Fi, graphics, audio, Bluetooth, printer, and other hardware work as expected;
- you have backed up all important files.

Windows programs (.exe and .msi) do not run natively. Compatibility tools or a Windows virtual machine may help in some cases, but are not guaranteed to work with every application.

## Download and installation

1. Open the [GitHub Releases](https://github.com/Nic69Han/BinixX-OS/releases) page and check whether an installation image is available.
2. Read the release notes and any installation instructions for that version.
3. Back up your files to a separate drive or trusted backup service.
4. Create a bootable USB drive from the published image and boot your computer from it.
5. Follow the installer instructions.

**Important:** Installing an operating system can erase the target disk. BinixX OS installation is intended to replace the existing system on the selected disk. Do not continue unless your important data is backed up and you have verified which disk will be used.

If no installation image is published in Releases, the project may not yet provide a ready-to-install image for general users. Do not treat the container images in the package registry as bootable installation media.

## Standard and NVIDIA images

The project builds two system images from the same sources:

| Image | Intended use |
| --- | --- |
| 'ghcr.io/nic69han/binixx:stable' | Standard image, using the open-source graphics stack |
| 'ghcr.io/nic69han/binixx-nvidia:stable' | NVIDIA variant with NVIDIA drivers prepared by Universal Blue |

For most users, start with the standard image. Consider the NVIDIA variant only if you need its driver for gaming, 3D workloads, CUDA, or graphics compatibility. The NVIDIA variant has not been validated on every combination of physical hardware and Secure Boot configuration; consult the [NVIDIA documentation](docs/nvidia.md) before switching.

These registry references are primarily for the image-based update and deployment workflow. They are not ISO download links.

## Updates and recovery

BinixX OS uses image-based system updates. A new system image is downloaded and becomes active after reboot; the previous deployment can be used to roll back if necessary. Applications installed through Flatpak update separately.

- [Updates and rollback](docs/mises-a-jour.md)
- [Security design and known limitations](docs/securite.md)
- [Troubleshooting and diagnostic reports](docs/aide-depannage.md)

Do not disable security controls or interrupt an update unless the relevant instructions explain how to recover safely.

## Documentation

**English user documentation is now available:** [Open the English documentation index](docs/en/README.md).

- [Installation and first steps](docs/en/INSTALLATION.md)
- [Moving from Windows](docs/en/WINDOWS-MIGRATION.md)
- [Desktop and applications](docs/en/DESKTOP-AND-APPS.md)
- [Updates and recovery](docs/en/UPDATES-AND-RECOVERY.md)
- [Hardware compatibility](docs/en/HARDWARE-COMPATIBILITY.md)
- [NVIDIA graphics](docs/en/NVIDIA.md)
- [Security and privacy](docs/en/SECURITY-AND-PRIVACY.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md)

The original technical documentation is still maintained in French; some detailed implementation notes may not yet have an English equivalent.

French documentation:
- [Move from Windows](docs/migration-windows.md)
- [Welcome Center and applications](docs/centre-binixx.md)
- [Windows-style desktop theme](docs/theme-windows-11.md)
- [Visual identity](docs/identite-visuelle.md)
- [Boot experience](docs/demarrage.md)
- [NVIDIA graphics](docs/nvidia.md)
- [Security](docs/securite.md)


## Getting help

- **Questions and support:** [GitHub Issues](https://github.com/Nic69Han/BinixX-OS/issues)
- **Bug reports:** include the BinixX OS version, hardware details relevant to the problem, the steps to reproduce it, and any error messages.
- **Diagnostic report:** review the report before sharing it. The built-in report is designed to omit passwords, file contents, IP addresses, and Wi-Fi network names, but you should still inspect any information before posting it publicly.

Do not publish passwords, recovery keys, private logs, personal documents, or other sensitive information in issues.

## Privacy

BinixX OS's built-in diagnostic report is generated locally and is not automatically uploaded by the report tool. System and application updates require network access to their respective repositories and services. Refer to the documentation of those services for their own data practices.

Please review diagnostic reports and logs before sharing them. Do not assume that every third-party application included or installed on the system follows the same privacy practices.

## Contributing

Bug reports, documentation improvements, and code contributions are welcome. Before opening an issue or pull request, check the existing issues and read the relevant documentation. Keep reports focused and provide reproducible steps where possible.

## License

The BinixX OS project files are licensed under the [Apache License 2.0](LICENSE), unless a file or component states otherwise. The operating system also includes Fedora components, KDE software, and other third-party projects that remain subject to their own licenses and notices. The Apache license for this repository does not replace those third-party licenses.

## Acknowledgements

BinixX OS builds on the work of the Fedora, KDE, Universal Blue, and other upstream projects. Their names and trademarks remain the property of their respective owners. Their inclusion does not imply endorsement of BinixX OS.
