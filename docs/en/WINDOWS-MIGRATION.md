# Moving from Windows to BinixX OS

This guide helps you prepare for migration and recover personal files. It does not guarantee that every Windows application or peripheral will work on Linux.

## Before you switch

### Back up your data

Copy important files to an external drive or trusted cloud backup. Include Documents, Desktop, Pictures, Music, Videos, Downloads, browser bookmarks, email archives (especially Outlook PST files), project data, software license keys, and recovery information. Verify that your backup can be opened before installing.

The installation process may erase the selected disk.

### Check applications

Windows programs such as .exe and .msi files do not install natively on BinixX OS. For every essential program, look for a Linux version, a web application, or a suitable alternative. Wine and Windows virtual machines are not part of the project's baseline offering, and compatibility layers cannot guarantee that a specific program will work.

BinixX OS includes OnlyOffice for office documents. Test complex spreadsheets, specialist formatting, charts, and PowerPoint animations before migration. VBA macros are not supported by OnlyOffice; its macro system uses JavaScript.

### Email and browser data

- If you use Outlook with POP and PST archives, import messages into a supported mail client on Windows before migration, or preserve the PST file and follow the target application's import instructions.
- Export browser bookmarks to HTML or enable browser synchronization before switching.
- Browser passwords are not automatically copied by the Windows file recovery tool. Export them securely or enable browser sync in advance.
- Confirm that OneDrive and other cloud files have finished synchronizing before removing Windows.

## Recover files after installation

The **Recover my Windows files** tool can copy common personal folders and browser bookmarks from a Windows profile on an attached backup drive or, where available, a separate Windows disk.

The tool is designed to read the source and copy files into the usual destination folders without overwriting existing files. If a file with the same name has different content, the existing file is preserved and the imported file receives a distinguishing name. A report lists copied, skipped, or unreadable items.

Limitations:

- It does not convert Windows applications into working Linux applications.
- It does not automatically migrate browser passwords.
- Outlook PST files may be copied as data but still need to be imported into a compatible mail client.
- BitLocker-encrypted disks may require the password or 48-digit recovery key. Fully shut down Windows rather than hibernating or using Fast Startup.
- Never publish a BitLocker recovery key in an issue or send it to support.

## Familiar tasks

| Windows task | BinixX OS starting point |
| --- | --- |
| Start menu and application search | BinixX OS application menu; press the Windows key |
| File Explorer | Dolphin; press Windows + E |
| Word, Excel, PowerPoint | OnlyOffice; test complex files before relying on it |
| Email | Thunderbird |
| Web browsing | Firefox |
| Install applications | KDE Discover and supported Flathub applications |
| System updates | System Settings → System Updates |
| Find alternatives to Windows software | **My Windows application** in the Welcome Center |

Keep your backups and recovery credentials until you have confirmed that the new system meets your needs. Reinstalling Windows may require installation media, a valid license, device drivers, and your data backup.
