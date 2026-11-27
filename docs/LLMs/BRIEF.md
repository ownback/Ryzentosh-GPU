# BRIEF: Ryzentosh-dGPU

**Scope:** Full RX 7900 XTX (Navi 31: GC 11.0.0, DCN 3.2, VCN 4, PSP 13, SMU 13) stack. Bring-up, memory/VM, queues, display (EDID-driven modes, 240 Hz, VRR, HDR, multi-monitor, HDMI, hot-plug), IOAccelerator, Metal, OpenGL, OpenCL, Vulkan (RADV ICD), VideoToolbox, DP/HDMI audio, power, sleep, GPU reset, sensors.

**Release artifact:** Boot kext(s) for EFI/OC/Kexts + user-space bundle installed by Ryzentosh-POST.

**Depends on:** [Ryzentosh-EFI]

**Parity targets:** see the rows for this project in the control plane's COMPATIBILITY_MATRIX.md.

**Out of scope:** anything another Ryzentosh repo owns (see projects.yaml).
