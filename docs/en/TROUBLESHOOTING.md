# Troubleshooting and Support

Start with the simplest checks. If the problem began after a system update, consider using the previous deployment before making unrelated changes.

## Basic checks

- **No internet:** check Wi-Fi or Ethernet, airplane mode, and the router. Try another network if possible.
- **No sound:** check the selected output device, volume, mute state, and application-specific audio settings.
- **Wrong display resolution:** open System Settings → Display & Monitor and verify the active display and resolution.
- **Printer not detected:** check that the printer and computer are on the same network, then try adding it from System Settings. Some models require additional drivers.
- **Computer feels slow:** check free disk space, running applications, memory use, and whether an update is being applied.
- **Problem started after an update:** use System Settings → System Updates to roll back to the previous deployment if the desktop is available.

See [Hardware Compatibility](HARDWARE-COMPATIBILITY.md) for known limitations.

## Reset the desktop configuration

The **Reset desktop** tool restores the BinixX OS desktop layout, theme, shortcuts, and window behavior to their initial configuration.

According to the project documentation, it does not delete personal files, applications, language, keyboard, display configuration, saved passwords, or Firefox and Thunderbird profiles. Previous desktop settings are backed up in the user's local data directory so they can be reviewed or recovered.

Follow the tool's prompts. Do not manually delete configuration directories unless you understand the consequences.

## Repair changed system settings

The **Repair system** tool compares selected configuration files in /etc with defaults shipped in the system image. It can restore selected modified files, recreate deleted defaults, or remove added configuration files. It is designed to back up files before changing them and supports undoing the latest repair.

- Review each proposed change; nothing should be selected automatically.
- Do not use it as a full system reset.
- It deliberately excludes user accounts, passwords, network connections, Wi-Fi settings, disk mounts, SSH keys, and machine identity.
- It requires the original configuration reference in /usr/etc and may refuse to run in containers or development environments.

If unsure, create a diagnostic report and ask for help before restoring system files.

## Create a diagnostic report

Open **Get Help** from the application menu or the BinixX OS Welcome Center and choose **Create report**. The report is saved in your Documents folder and copied to the clipboard according to the project documentation.

Review the report before sharing it. Although the tool is designed to exclude passwords, file contents, IP addresses, and Wi-Fi network names, reports may still contain system and hardware details. Remove anything you do not want to make public.

## If the desktop will not start

1. Wait for automatic recovery to finish; it may restart the computer more than once after a failed update.
2. If the boot menu is visible, select the previous deployment if available.
3. If you can reach a terminal, collect relevant error messages and current system status.
4. Report the issue on [GitHub Issues](https://github.com/Nic69Han/BinixX-OS/issues) with the version, hardware details, and steps to reproduce it.

Never post passwords, encryption passphrases, disk recovery keys, personal files, or sensitive business logs.

## What to include in a bug report

- BinixX OS version and update channel (stable or testing)
- Computer model and relevant component models
- What you expected and what happened
- Exact steps to reproduce the problem
- Error messages or a reviewed diagnostic report
- Whether the issue began after an update or configuration change

Check existing issues before opening a new one. For security vulnerabilities, use the private reporting process in [SECURITY.md](../../SECURITY.md), not a public issue.
