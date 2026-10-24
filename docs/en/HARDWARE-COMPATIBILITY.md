# Hardware and Application Compatibility

**Status: early alpha.** Virtual-machine tests are not the same as testing on physical computers. Unless a result is explicitly marked as verified on named hardware, treat it as an expectation based on included software, not a guarantee.

## Suggested minimum configuration

The project's virtual-machine test configuration is a 64-bit x86_64 computer with UEFI, 2 CPU cores, 4 GB RAM, and 64 GB of disk space. This is a test baseline, not a promise of acceptable performance on every physical machine. More memory and storage are recommended for everyday use.

## Hardware

| Component | Current expectation | Notes |
| --- | --- | --- |
| Intel and AMD graphics | Linux open-source graphics stack | Physical hardware testing is still required |
| NVIDIA graphics | Standard image uses nouveau; a separate NVIDIA image is available | Support varies by GPU generation and Secure Boot setup |
| Wi-Fi and Bluetooth | Depends on Linux kernel and firmware support | Check the exact adapter model |
| Webcam and audio | Depends on Linux driver support | Test microphone, speakers, camera, and suspend/resume |
| Network printers | Recent IPP Everywhere / AirPrint devices are expected to work | Not every model has been verified |
| USB printers | Support depends on protocol and model | Some devices require vendor drivers |
| Scanners | Network eSCL/WSD or SANE support may be available | Some models require proprietary drivers |
| Secure Boot | Boot path tested in a virtual machine | Additional NVIDIA modules may require MOK enrollment |
| VPN | KDE network settings support common VPN types | Verify with your organization's server |

## Applications

| Task | Application or approach | Known limitation |
| --- | --- | --- |
| Word, Excel, PowerPoint files | OnlyOffice | Test complex formatting, charts, animations, and large workbooks |
| VBA macros | Not supported by OnlyOffice | OnlyOffice macros use JavaScript |
| PDF viewing and annotation | Okular | Test specialized forms and workflows |
| Email | Thunderbird | On-premises Exchange support depends on server and client configuration |
| Microsoft 365 online | Browser-based web apps | Features may differ from desktop applications |
| Teams, Zoom, Slack | Web applications | Some desktop-specific features may be missing |
| OneDrive | Open-source OneDrive client | No Files On-Demand equivalent in the documented setup |
| Remote desktop to Windows | Remmina | Validate with your host and authentication policy |
| Video playback | Haruna and included codecs | Specific formats may vary |
| Windows software | No native support for .exe or .msi installers | Look for a web version, Linux release, or alternative |

## Before replacing Windows

Test the tasks that matter to you using copies of real files where possible. Confirm that Wi-Fi, Bluetooth, sound, camera, external displays, printers, scanners, sleep/resume, and specialist equipment work. If a required application depends on Windows-only drivers, macros, plug-ins, or licensing systems, do not assume it will work.

Report compatibility results with the computer model, relevant hardware details, BinixX OS version, and test date. Do not post serial numbers, personal identifiers, or sensitive business information.
