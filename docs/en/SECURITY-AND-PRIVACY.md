# Security and Privacy

This page summarizes security measures documented for BinixX OS and the responsibilities that remain with users and administrators. Security features reduce specific risks; they do not make a computer immune to compromise.

## Built-in protections

The project documents the following controls:

- The system image is mounted read-only in normal operation, and SELinux is configured in enforcing mode.
- The boot path uses signed components and is tested with Secure Boot in a virtual machine.
- System updates are tested in a virtual machine before promotion to stable; rollback to the previous deployment is supported.
- Image builds check Fedora security advisories and produce a software bill of materials (SBOM) and build provenance.
- System and application updates are downloaded automatically; system updates take effect after reboot.
- The firewall blocks unsolicited incoming connections by default, with selected local-network discovery exceptions.
- Firefox is configured with uBlock Origin, HTTPS-only mode, and telemetry disabled.
- Windows executables do not run natively as desktop applications.

**Known limitation:** the project's security documentation states that image signing for installed systems is not yet implemented. Build provenance helps identify how an image was produced, but is not the same as cryptographic verification of the image by the installed computer. Check the current release notes for changes.

## Protect your data

### Disk encryption

During installation, enable **Encrypt my data** if available and appropriate. Store the encryption passphrase securely. If it is lost and no working recovery method exists, encrypted data may be unrecoverable.

The project documents a recovery-key tool for supported LUKS2 volumes. A recovery key may be displayed only once; store it offline in a secure location separate from the computer. Never post a recovery key publicly or send it to support.

TPM-based automatic unlocking has hardware-specific security considerations. The project's French security documentation warns against TPM unlocking on AMD Ryzen Zen 1–3 systems because of the faulTPM vulnerability. If you use affected hardware, keep passphrase-based unlocking or follow updated project guidance.

### Backups and accounts

- Use a backup tool such as Déjà Dup to back up important files to an external drive or trusted cloud service.
- Disconnect external backup media after a backup where practical.
- Reboot regularly so downloaded system updates can be applied.
- Use unique passwords and consider a reputable password manager.
- Enable remote-access services only when needed and only on trusted networks.
- Keep recovery keys and administrator credentials private.

## Build security information

The project documents CI checks for an SBOM listing image packages, outstanding Fedora security advisories above a configured severity threshold, and build provenance linking a published image digest to the repository, workflow, and commit that produced it.

These checks have limits. Flatpak applications installed separately are not part of the operating-system image SBOM. New advisories may not be available in upstream repositories immediately, and a successful build is not proof that an image contains no vulnerabilities.

## Privacy and diagnostic reports

The built-in diagnostic tool is documented as generating a report locally rather than automatically uploading it. The report is intended to omit passwords, file contents, IP addresses, and Wi-Fi network names. Nevertheless, inspect reports and logs before sharing them publicly.

System and application updates connect to their respective repositories and services. Third-party applications may have their own telemetry, account requirements, and privacy policies. Review those policies directly.

## Report a security vulnerability

Do not publish an unpatched vulnerability or sensitive exploit details in a public issue. Follow the private reporting instructions in the repository's [SECURITY.md](../../SECURITY.md). Do not include passwords, recovery keys, personal documents, or unrelated private information.
