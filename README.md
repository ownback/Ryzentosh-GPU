# Ryzentosh-GPU

One clean-room AMD GPU driver, **RyzentoshGPU.kext**, for the RX 7900 XTX (Navi 31: GC 11.0.0, DCN 3.2, VCN 4, PSP 13, SMU 13) and the Raphael iGPU (gfx1036, DCN 3.1.5). The two share the display core, PSP/SMU and memory code. Bring-up, memory/VM, queues, display (EDID-driven modes, 240 Hz, VRR, HDR, multi-monitor, HDMI, hot-plug), IOAccelerator, Metal, OpenGL, OpenCL, Vulkan (RADV ICD), VideoToolbox, DP/HDMI audio, power (including idle dGPU power-down), sleep, GPU reset, sensors, and iGPU display with dGPU offload (ADR-0005).

Part of [Ryzentosh](https://github.com/ownback/Ryzentosh): macOS Tahoe on an AMD PC, built to behave like a Mac Apple designed and
supports. Written by AI agents. Apple is not involved in this project.

**Status:** research. Nothing here is ready to install yet. See [docs/Humans](docs/Humans/) and the
[compatibility matrix](https://github.com/ownback/Ryzentosh/blob/main/docs/Hardware/COMPATIBILITY_MATRIX.md).

**Releases:** RyzentoshGPU.kext for EFI/OC/Kexts (it replaces VermilionBoot and VermilionAudio; see the control plane's docs/Architecture/EFI-END-STATE.md), plus user-space bundles installed by Ryzentosh-POST.

## Reference hardware
AMD Ryzen 9 7900X3D · Radeon RX 7900 XTX (XFX) · ASUS ROG STRIX B650E-I · macOS 26.7.1 (25G241) · OpenCore 1.0.8.

## Contributing
See [CONTRIBUTING.md](https://github.com/ownback/Ryzentosh/blob/main/CONTRIBUTING.md). AI agents: read [AGENTS.md](AGENTS.md).

License: BSD-3-Clause. Third-party code and its origins are listed in [PROVENANCE.md](PROVENANCE.md).
