# BRIEF: Ryzentosh-GPU

**Scope:** One clean-room AMD GPU driver, **RyzentoshGPU.kext**, for the RX 7900 XTX (Navi 31: GC 11.0.0, DCN 3.2, VCN 4, PSP 13, SMU 13) and the Raphael iGPU (gfx1036, DCN 3.1.5). The two share the display core, PSP/SMU and memory code. Bring-up, memory/VM, queues, display (EDID-driven modes, 240 Hz, VRR, HDR, multi-monitor, HDMI, hot-plug), IOAccelerator, Metal, OpenGL, OpenCL, Vulkan (RADV ICD), VideoToolbox, DP/HDMI audio, power (including idle dGPU power-down), sleep, GPU reset, sensors, and iGPU display with dGPU offload (ADR-0005).

**Release artifact:** RyzentoshGPU.kext for EFI/OC/Kexts (it replaces VermilionBoot and VermilionAudio; see the control plane's docs/Architecture/EFI-END-STATE.md), plus user-space bundles installed by Ryzentosh-POST.

**Depends on:** Ryzentosh-EFI, Ryzentosh-ACPI

**History:** renamed from Ryzentosh-dGPU on 2026-11-27, when Ryzentosh-iGPU (now archived) was merged in. Its briefs RB-0005a/b/c are issues #7–#9.

**Parity targets:** see the rows for this project in the control plane's COMPATIBILITY_MATRIX.md.

**Out of scope:** anything another Ryzentosh repo owns (see projects.yaml).
