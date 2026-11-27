# Ryzentosh-GPU

**Run `/ryzentosh` first.** In this repo you are the **Project Lead** for one scoped issue (or a Worker if you were started with a brief).

- Scope: one clean-room AMD GPU driver, **RyzentoshGPU.kext**, for the RX 7900 XTX (Navi 31: GC 11.0.0, DCN 3.2, VCN 4, PSP 13, SMU 13) and the Raphael iGPU (gfx1036, DCN 3.1.5). The two share the display core, PSP/SMU and memory code. Bring-up, memory/VM, queues, display (EDID-driven modes, 240 Hz, VRR, HDR, multi-monitor, HDMI, hot-plug), IOAccelerator, Metal, OpenGL, OpenCL, Vulkan (RADV ICD), VideoToolbox, DP/HDMI audio, power (including idle dGPU power-down), sleep, GPU reset, sensors, and iGPU display with dGPU offload (ADR-0005).
- Layout (owner, 2026-11-27): one repo ships one kext. RyzentoshGPU.kext has internal framebuffer / HW-services / accelerator components. The user-space bundles are installed by Ryzentosh-POST. ACPI tables (GPU power-down) belong to Ryzentosh-ACPI. Issues here are filed by this repo's Lead. See `docs/LLMs/BRIEF.md`.
- Memory: `docs/LLMs/BRIEF.md` (what this repo is for), `STATE.md` (now), `ARCHITECTURE.md`, `INTERFACES.md`, `TESTPLAN.md`, `decisions/ADR-*`.
- Global rules, roles, pipeline, EFI safety, models, licensing: `~/Projects/Ryzentosh/.agents/skills/ryzentosh/` (symlinked at `.agents/skills/ryzentosh`).
- Never write to an ESP or the live system. Hand build artifacts to the Root Orchestrator for the hardware test.
- License BSD-3-Clause: keep SPDX headers and update `PROVENANCE.md` for any derived code.
- Update `docs/LLMs/STATE.md` before you stop.
