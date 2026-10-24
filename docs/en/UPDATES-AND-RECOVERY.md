# Updates and Recovery

BinixX OS updates the operating system as a complete system image. A downloaded image becomes active after reboot, and the previous deployment is retained for rollback where supported. Flatpak applications update separately.

## Update channels

| Channel | Purpose |
| --- | --- |
| testing | Builds from the development branch; intended for volunteer testers |
| stable | An image promoted after passing the project's virtual-machine checks; intended for regular installations |
| latest | Alias for stable, retained for compatibility with existing commands |

The project tests installation, startup, updates, and rollback in a virtual machine. These tests reduce risk but do not prove that every physical computer or peripheral will work.

## Update from the desktop

Open **System Settings → System Updates** to view the installed version, check for updates, and apply an available system update. A system update normally takes effect after restarting. Flatpak applications update separately.

Save your work before restarting and reboot regularly so downloaded system updates can take effect.

## Command-line status and rollback

These commands are intended for users comfortable with a terminal:

~~~bash
binixx-mises-a-jour etat
binixx-mises-a-jour verifier
rpm-ostree status
sudo bootc rollback
~~~

After requesting a rollback, reboot to start the previous deployment. Command availability may vary by image version; check the release documentation if a command is unavailable.

Advanced users can switch to the testing image:

~~~bash
sudo bootc switch ghcr.io/nic69han/binixx:testing
~~~

Return to stable with:

~~~bash
sudo bootc switch ghcr.io/nic69han/binixx:stable
~~~

Testing is not recommended for users who need maximum stability.

## Automatic rollback after a failed boot

The system includes a recovery mechanism intended to detect a failure that prevents the graphical login service from starting after an update. It retries startup and can return to the previous deployment after repeated failures.

The check is deliberately narrow: network connectivity is not required for a successful boot, because a computer must be able to start offline. Automatic rollback is not a substitute for backups and may not detect every kind of failure.

## If an update causes a problem

1. Restart and check whether the previous deployment is available in the boot menu.
2. Use **System Settings → System Updates** to roll back if the desktop is accessible.
3. If the graphical login fails repeatedly, allow automatic recovery to finish.
4. If the problem persists, create a diagnostic report if possible and file an issue with the version, hardware details, and steps to reproduce the problem.

System rollback is not a replacement for personal-file backups.
