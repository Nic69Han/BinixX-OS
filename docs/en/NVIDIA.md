# NVIDIA Graphics

BinixX OS provides two system images built from the same project sources.

| Image | Graphics driver | Intended use |
| --- | --- | --- |
| ghcr.io/nic69han/binixx:stable | Open-source nouveau driver | General desktop use, browsing, office work, video, and video calls |
| ghcr.io/nic69han/binixx-nvidia:stable | Proprietary NVIDIA driver prepared by Universal Blue | Gaming, 3D workloads, CUDA, demanding multi-display setups, or problems with nouveau |

For most users, start with the standard image. Choose the NVIDIA variant only when you have a specific need for the proprietary driver.

## Switch to the NVIDIA image

Before switching, read the release notes and make sure you have a recovery path if the graphics driver does not start.

If Secure Boot is enabled, the relevant Universal Blue module-signing key may need to be enrolled through MOK (Machine Owner Key). Without the required key enrollment, the kernel may refuse the NVIDIA modules and the system may fall back to the open-source driver. Follow the current [Universal Blue documentation](https://universal-blue.org/) for the correct procedure.

To switch to the NVIDIA image:

~~~bash
sudo bootc switch ghcr.io/nic69han/binixx-nvidia:stable
~~~

Then reboot. To return to the standard image:

~~~bash
sudo bootc switch ghcr.io/nic69han/binixx:stable
~~~

Check that the driver is active with nvidia-smi when the NVIDIA tools are available.

## Current limitations

Virtual-machine tests can check image installation, boot, update, and rollback. They cannot validate graphics output on every physical NVIDIA card or verify Secure Boot enrollment on every firmware implementation.

Treat the NVIDIA variant as hardware-dependent. If the desktop does not start after switching, use the boot menu or rollback instructions in [Updates and Recovery](UPDATES-AND-RECOVERY.md).
