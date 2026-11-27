# ARCHITECTURE: Ryzentosh-GPU

Maintained by repo-cartographer. No code exists yet, so this is the **planned** layout from BRIEF.md and the control plane's layout decision of 2026-11-27. The real class names come from ADRs and RE of 25G241.

## Components (planned)

One kext, RyzentoshGPU.kext, with separate internal components. Each component has its own `os_log` category (`com.ryzentosh.gpu`).
- **Framebuffer:** display for both GPUs (DCN 3.2 and DCN 3.1.5). `IOFramebuffer`, EDID-driven modes, hot-plug, VRR, HDR, the DP/HDMI audio endpoints, and iGPU scanout with dGPU offload (ADR-0005).
- **HW services:** PSP/SMU firmware loading, power, clocks, sensors, sleep/wake, GPU reset, and idle dGPU power-down. The ACPI methods for power-down live in Ryzentosh-ACPI.
- **Accelerator:** the `IOAccelerator` family service, user clients, memory/VM, queues, and the VCN media engine.
- **Shared support:** IP discovery, register access, and firmware headers.

User space ships as separate bundles: Metal, OpenGL, OpenCL, the Vulkan (RADV) ICD and VideoToolbox. Ryzentosh-POST installs them. How they load with AMFI on is ADR-0004 (open).

## Entry points

## Build targets
