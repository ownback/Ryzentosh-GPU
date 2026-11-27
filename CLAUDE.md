# Ryzentosh-dGPU

**Run `/ryzentosh` first.** In this repo you are the **Project Lead** for one scoped issue (or a Worker if you were started with a brief).

- Scope: Full RX 7900 XTX (Navi 31: GC 11.0.0, DCN 3.2, VCN 4, PSP 13, SMU 13) stack. Bring-up, memory/VM, queues, display (EDID-driven modes, 240 Hz, VRR, HDR, multi-monitor, HDMI, hot-plug), IOAccelerator, Metal, OpenGL, OpenCL, Vulkan (RADV ICD), VideoToolbox, DP/HDMI audio, power, sleep, GPU reset, sensors.
- Memory: `docs/LLMs/BRIEF.md` (what this repo is for), `STATE.md` (now), `ARCHITECTURE.md`, `INTERFACES.md`, `TESTPLAN.md`, `decisions/ADR-*`.
- Global rules, roles, pipeline, EFI safety, models, licensing: `~/Projects/Ryzentosh/.agents/skills/ryzentosh/` (symlinked at `.agents/skills/ryzentosh`).
- Never write to an ESP or the live system. Hand build artifacts to the Root Orchestrator for the hardware test.
- License BSD-3-Clause: keep SPDX headers and update `PROVENANCE.md` for any derived code.
- Update `docs/LLMs/STATE.md` before you stop.
