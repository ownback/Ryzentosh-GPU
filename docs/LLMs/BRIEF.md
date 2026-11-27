# BRIEF: Ryzentosh-GPU

**Scope:** one clean-room AMD GPU driver, **RyzentoshGPU.kext**, for two GPUs:
- the RX 7900 XTX (Navi 31: GC 11.0.0, DCN 3.2, VCN 4, PSP 13, SMU 13);
- the Raphael iGPU (gfx1036, DCN 3.1.5).

The two share the display core, PSP/SMU and memory code. The driver covers:
- bring-up, memory/VM, queues;
- display: EDID-driven modes, 240 Hz, VRR, HDR, multi-monitor, HDMI, hot-plug;
- IOAccelerator, Metal, OpenGL, OpenCL, Vulkan (RADV ICD), VideoToolbox (including the H.264 hardware decode Continuity Camera needs, M4);
- DP/HDMI audio, power (including idle dGPU power-down), sleep, GPU reset, sensors;
- iGPU display with dGPU offload (ADR-0005).

**Layout:** this follows the owner's layout decision of 2026-11-27 (control plane `README.md`, `docs/LLMs/DECISIONS.md` "Project layout and EFI end state", `docs/Architecture/EFI-END-STATE.md`): one Ryzentosh repo ships one kext, named after the repo.
- **One kext, RyzentoshGPU.kext,** in `EFI/OC/Kexts`. It replaces VermilionBoot and VermilionAudio.
- **Inside it, separate components,** mirroring the separation of responsibilities in Apple's AMD stack (`apple-driver-quality.md`). This repo writes its own code and copies nothing:

  | Component | Responsibility | Apple's counterpart |
  |---|---|---|
  | Framebuffer | Display | `AMDRadeonX6000Framebuffer` |
  | HW services | Firmware, PSP/SMU, power | `AMDRadeonX6000HWServices` |
  | Accelerator | `IOAccelerator` family, queues, memory | `AMDRadeonX6000` |
  | Shared support | Code common to the components | `AMDSupport` |

- **User-space drivers** (Metal, OpenGL, OpenCL, Vulkan ICD, VideoToolbox) are separate bundles built here and installed by Ryzentosh-POST, not the EFI. How they can load with AMFI fully on is ADR-0004's open decision (RB-0004a, RB-0004b/c gate).

**Release artifact:** RyzentoshGPU.kext for `EFI/OC/Kexts`, plus the user-space bundles, which Ryzentosh-POST packages and installs.

**Depends on:**
- Ryzentosh-EFI, which stages the kext.
- Ryzentosh-ACPI, which owns every ACPI table, including the GPU power-down methods (`SSDT-GPU-PM-B650EI.aml`) and the sleep/wake sources.
- Ryzentosh-POST, which installs the user-space drivers.

**History:**
- Renamed from Ryzentosh-dGPU on 2026-11-27, when Ryzentosh-iGPU (now archived) was merged in.
- Its briefs RB-0005a/b/c are issues #7–#9 here.
- Issues in this repo are filed by its Lead. The Root Orchestrator files only in ownback/Ryzentosh.

**Parity targets:** see this project's rows in the control plane's `COMPATIBILITY_MATRIX.md`.

**Out of scope:**
- ACPI tables (Ryzentosh-ACPI).
- EFI staging and `config.plist` (Ryzentosh-EFI).
- Installers and updaters (Ryzentosh-POST).
- Anything else another Ryzentosh repo owns (`projects.yaml`).
