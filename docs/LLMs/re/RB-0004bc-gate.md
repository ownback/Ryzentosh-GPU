# RB-0004b/c gate check: Apple's AMD shader ISA targets, and the paravirt guest stack on bare metal

Status: done 2026-11-27. Issue ownback/Ryzentosh-GPU#12. A cheap gate run before the full RB-0004b (#2) and RB-0004c (#3) briefs, per the M1.0 plan the Root Orchestrator approved. Briefs: control plane `docs/Research/briefs/RB-0004b-paravirt-graphics-on-bare-metal.md` and `RB-0004c-x6000-bundle-asic-assumptions.md`.

Citation review: claude-fable-5-2 / high at f420730. It requested changes: one blocking finding on the C "disguise" premise, plus count and citation fixes. All of them are applied in this version.

**Evidence rules:** the same as RB-0004a ([conventions](RB-0004a-metal-loading-chain.md#conventions)). [V] means verified, [I] means inferred.
- Shared-cache images come from the 25G241 cache (UUID 31374756-…), extracted with `tools/re/dscx`.
- Kexts come from KDK 25G241.
- `strings -t x` offsets are file offsets in the extracted image or in the thinned KDK binary.
- Mesa (MIT) is cited as repo @ commit + path:line from the local clone.
- Only names, offsets and behaviour are recorded.

## Verdicts

| Option | Verdict | Why (details below) |
|---|---|---|
| **B for the RX 7900 XTX (Navi 31, gfx11)** | **Dead in practice** | Apple's AMD stack on 25G241 has no gfx11 path at all. Of the 1053 opcode entries valid on GFX10, 64% are renumbered or removed on GFX11. The interpolation instructions change format, RADV forces NGG, and the NGG lowering stores vertex outputs to an attribute ring in memory. Making Apple's gfx10.3 output run on gfx11 would take a recompiler, not a patch. |
| **B for the Raphael iGPU (gfx1036, RDNA2)** | **Proceed to the full RB-0004c, scoped to the iGPU** | Raphael is in the GFX10.3 generation, the same one Apple's compiler emits. But Apple has no Raphael support: no device ID, no per-ASIC table, and no UMA (shared-memory) layout. Whether those can be supplied honestly is exactly what the full brief must measure. |
| **C, the paravirt guest stack, without Apple's paravirt kext** | **Technically possible and AMFI-intact, but rejected on cost and on parity** | Our kext can publish its own `IOAccelerator` service that names Apple's guest bundle, so no faked PCI device is needed. But the guest serializes all of Metal to a host. Our side would have to be a full Metal implementation plus an AIR→RDNA3 compiler, in the kernel or in a daemon. Apps would likely see the device name "Paravirtual device". |

**Consequence for ADR-0004:**
- B is dead for gfx11, and D was already dead (RB-0004a).
- [I] So no AMFI-intact dGPU Metal path survives *the parity rule and a sane cost* on 25G241.
- C remains technically possible. It is a native-driver-sized effort, outside the normal user-space driver shape, and visibly a virtual GPU.
- Choosing between the options listed under [Options this leaves](#options-this-leaves) is an owner-level call for ADR-0004 and ADR-0005.

## B gate (RB-0004c): which ISA Apple's AMD stack targets

### Binaries (25G241, x86_64)

| Image | LC_UUID |
|---|---|
| `AMDShared.bundle/Contents/PlugIns/libSC.dylib` (AMD shader compiler) | F0360193-F51A-3AC3-BA3C-EDDDC84FF9BC |
| `AMDShared.bundle/Contents/PlugIns/libGCNASM.dylib` | E7861072-5C10-38A6-A83A-5FD8B11B70FC |
| `AMDShared.bundle/Contents/PlugIns/libAMDIL902.dylib` | 48049D0F-8200-3177-948B-F014CB3AFF89 |
| `AMDRadeonX6000GLDriver.bundle/Contents/MacOS/ATIRadeonX6000SCLib.dylib` | C112BAF1-B120-3292-B701-452DAE23D31E |
| `AMDRadeonX6000MTLDriver.bundle` | BBB186ED-C8E3-3641-BDED-1B0202AA2173 |
| KDK `AMDRadeonX6000.kext` | DCD61202-702C-339A-840E-6E590CA6D74C |

### Findings

- [V] **No gfx11 path exists.** 18 files were searched, case-insensitively, for any gfx11 or RDNA3 marker, with zero matches.
  - Files: every AMD file in the extracted cache's `/System/Library/Extensions` (bundles, compiler plugins, AMDMTLBronzeDriver), plus the KDK kexts AMDRadeonX5000, AMDRadeonX6000, AMDRadeonX6000HWServices and AMDRadeonX6000Framebuffer.
  - Patterns: `gfx_?11`, `gfx110[0-3]`, `navi_?3[0-9]`, `gc_?11_`, `nv3[0-9]`, `rdna3`, the RDNA3 codenames, and `phoenix`. The reviewer also searched for the Navi 31 device ID 0x744C, as text and as the little-endian match word 0x744C1002.
  - Command: `strings -a <file> | grep -ciE '…'`.
- [V] **The compiler is built per generation, and GFX10.3 is the newest.** libSC has these emitter and target classes:
  - `SCGfx10Emitter` (0x874b90), `SCGfx101Emitter` (0x874ba1) and `SCGfx103Emitter` (0x8764ec).
  - `SCGfx10Info`, `SCGfx101Info`, `SCGfx103Info` (0x8764fe), `SCGfx10B0Info` and `SCGfx10C0Info`.
  - No `Gfx11` string at all.
- [V] **The kernel driver covers only Navi 10, 12, 14, 21 and 23.** The `IOClass` → `IOPCIMatch` pairs in `/System/Library/Extensions/AMDRadeonX6000.kext/Contents/Info.plist` (`PlistBuddy -c Print`), all vendor 0x1002:

  | Class (`AMDRadeonX6000_AMD…GraphicsAccelerator`) | Device IDs |
  |---|---|
  | `Navi10…` | 0x7310, 0x7312, 0x7318, 0x7319, 0x731A, 0x731B, 0x731F |
  | `Navi12…` | 0x7360 |
  | `Navi14…` | 0x7340, 0x7341, 0x7343, 0x7347, 0x734F |
  | `Navi21…` | 0x73A2, 0x73A3, 0x73AB, 0x73BF |
  | `Navi23…` | 0x73E0, 0x73E3, 0x73FF |

  - The SDMA engine classes are `GC_10_1_0`, `GC_10_1_1`, `GC_10_1_2`, `GC_10_3_0` and `GC_10_3_4` (0x10b354…0x10e6fc).
  - There is no Navi 22 or Navi 24 class, and no APU device ID. Raphael's 0x164E is absent, both as text and as a binary match word.
- [V] **The MTL driver's per-ASIC tables match the kext list exactly.**
  - The named tables are `AMD_GFX10_NAVI10_P_A0`, `…NAVI10_P`, `…NAVI12_P`, `…NAVI14_M`, `…NAVI21_P` and `…NAVI23_P` (0x393cd5–0x393d37).
  - A processor table at 0x3a1009–0x3a104c, followed by `Processor` and `CUCount`, lists `gfx803`, `gfx900`, `gfx906`, `gfx908`, `gfx90a`, `gfx1010`, `gfx1011`, `gfx1012`, `gfx1030` and `gfx1032`. Its RDNA parts are exactly the five kext classes.
  - A separate generic target-name table (0x3a498d–0x3a4cac) also names `gfx1031` and `gfx1033` and the `:xnack±` variants.
  - No `gfx1034`–`gfx1036` string appears anywhere in the 18 files.

### Why Apple's gfx10.3 output can't just be translated to gfx11

Sources: Mesa @ dcf1989.

- [V] **Encoding.** `src/amd/compiler/aco_opcodes.py` has 1391 live opcode entries, counting non-comment `op(…)` entries and applying the file's own inheritance from older to newer generations. Of the 1053 entries valid on GFX10:
  - 523 have a different opcode on GFX11.
  - 153 are removed on GFX11 (`gfx11=-1`).
  - Together that is 64%.
  - Another 126 entries exist only on GFX11.
  -
- [V] **Interpolation.** The fragment-shader input interpolation instructions change format. `v_interp_p1_f32`, `v_interp_p2_f32` and `v_interp_mov_f32` (lines 1279–1281) and the f16 forms (lines 1392–1393 and 1395–1396) are removed. The `v_interp_*_inreg` forms (lines 1289–1294) replace them.
- **NGG.**
  - [V] RADV forces NGG for `gfx_level >= GFX11`, ignoring the `NO_NGG` debug option (`src/amd/vulkan/radv_physical_device.c:2845–2847`).
  - [V] The NGG lowering stores vertex outputs to the attribute ring (`src/amd/common/nir/ac_nir_lower_ngg.c:1775`, `ac_nir_store_parameters_to_attr_ring`). It is gated by `has_attr_ring = gfx_level >= GFX11` (`src/amd/common/ac_gpu_info.c:368`).
  - [I] The legacy VS/GS hardware path is gone on GFX11. Mesa states no such comment; this is inferred from the forced setting.

[I] A translator would have to:
- re-encode most instructions;
- rebuild fragment-shader interpolation;
- convert any legacy VS/GS output to NGG;
- move parameter exports to attribute-ring stores.

That is a recompiler from gfx10.3 machine code: fragile, hard to make correct, and no longer "Apple's code unchanged".

The kernel-side PM4/MES differences (RB-0004c question 4) were not assessed, because the ISA gap already decides the outcome.

### The iGPU inference

- [V] Mesa groups Raphael with Navi 21:
  - `src/amd/common/amd_family.h:115–124` lists NAVI21 through RAPHAEL_MENDOCINO under `/* GFX10.3 (RDNA 2) */`, and GFX11 starts with NAVI31.
  - `ac_gpu_info.c:809–810` maps IP version 10.3 to `GFX10_3`.
  - Mesa does special-case Raphael in places, for example a MEC firmware bug threshold (`ac_gpu_info.c:1071`).
- [I] Code from `SCGfx103Emitter` for gfx1030 should be ISA-compatible with gfx1036. To confirm: LLVM's `gfx10-3-generic` definition, which is not cloned locally.
- What would block B on the iGPU (the full RB-0004c):
  1. **ASIC selection.** How the bundle picks its per-ASIC configuration. Navi 21 and Navi 23 tables exist, and no Raphael table does. Can a Raphael configuration be supplied honestly, without claiming to be a Navi 21?
  2. **Memory layout.** UMA means no VRAM, while Apple's heaps assume a dGPU layout.
  3. **Kernel↔user interface.** The `AMDRadeonX6000` user-client interface our kext would have to implement.
  4. **Other engines.** VCN and DCN differences, which our kext owns anyway.

## C gate (RB-0004b): the paravirt guest stack on bare metal

### Binaries (25G241, x86_64)

| Image | LC_UUID |
|---|---|
| KDK `AppleParavirtGPU.kext`, x86_64 slice. Installed only inside the kernel collection. | 0CAE9E29-BC33-315D-82A7-A7D30E9B971E |
| `/System/Library/Extensions/AppleParavirtGPUMetal.bundle/Contents/MacOS/AppleParavirtGPUMetal`. On disk; x86_64 + arm64e; platform binary, CodeDirectory flags none. | 65A3F37C-145D-385B-8E4A-52ED3086CCA9 (x86_64) |
| `AppleParavirtGPUMetal.bundle/Contents/Resources/libAppleParavirtCompilerPlugin.dylib`, in the shared cache | 85D559AC-7ADD-3642-B59A-371F02D4B69C |
| `ParavirtualizedGraphics.framework` (host side), in the x86_64 shared cache | 08DB4699-8798-362C-81E9-2BE5A7643C16 |

### Findings

- **VMM checks.**
  - [V] Neither the kext nor the guest bundle imports `hv_*` or `sysctl*` (`nm -u`). Neither contains `hv_vmm` or `kern.hv` strings. Neither contains a `cpuid` instruction (`otool -tV … | grep -c cpuid`: 0 and 0).
  - [V] The kext's only platform-related import is `_PE_parse_boot_argn`.
  - [I] So there is no runtime VMM check. The kext's `start` was not disassembled.
- [V] **Apple's kext matches only the virtual device.** Its PCI personality matches `IOPCIMatch 0xEEEE106B`: vendor 0x106B (Apple), device 0xEEEE (RB-0004a §4). It names itself `Apple Paravirtualized Graphics Device` (0x156c7).
- [I] **Reusing Apple's kext would require faking that device, which is a disguise.** But nothing forces us to reuse it:
  - [V] The guest bundle does no service matching of its own. Its only IOKit import is `_IOConnectCallMethod`.
  - [V] Metal finds the device through any `IOAccelerator` service that names a `MetalPluginName` / `MetalPluginClassName` (RB-0004a §1.1).
  - [I] So our kext, matched on the real AMD device, could publish an `IOAccelerator` service naming `AppleParavirtGPUMetal` / `AppleParavirtDevice`. It would then implement the kernel end of the guest bundle's user-client ABI.

  This is the same mechanism B relies on. Not checked: whether anything on the Metal side validates the service class beyond those properties.
- [V] **The guest is a complete Metal front end that serializes to a host.**
  - The guest bundle has 22 `AppleParavirt*` classes (counted from the class-name strings; `nm` exports 21, without `AppleParavirtState`). They include:
    - the device, command queue and command buffer;
    - the blit and parallel-render encoders;
    - render and compute pipeline states;
    - heap, descriptor heap, descriptor buffer, texture, buffer, fence and sampler state;
    - function variant and container function.
  - The x86_64 slice is 380,688 bytes.
  - Its capability structure includes `DeserializerVersion`, `HostGPUFamilies`, `HostGPUFamilyClamped`, `GpuCoreCount` and `MaxMetalShaderVersion` (from an ObjC type-encoding string).
  - The host side, `ParavirtualizedGraphics.framework`, is 1,175,552 bytes with 1534 ObjC methods.
- **Shader path.**
  - [V] The guest compiler plugin (12,288 bytes) imports `_MTLGPUCompilerCreate`, `_MTLDowngradeAIRModule`, `_MTLMetalFunctionCreate`, `_MTLMetalLibCreateExecutableWithTriple`, `_MTLMetalLibInsertFunction` and `_MTLWriteMetalLibToMemoryBuffer`. Its strings name only the AIR stages (`air.vertex`, `air.fragment`, `air.kernel`).
  - [V] It packages AIR into a metallib and generates no native machine code.
  - [I] So the host compiles the shaders.
- [I] **Protocol size: essentially the whole Metal API surface, serialized.** On bare metal, the "host" would be our kext, or a user-space service the kext forwards to. It would have to implement:
  - deserialization of the stream;
  - Metal semantics on RDNA3;
  - an AIR→RDNA3 shader compiler.

  That is all the work of a native Metal driver, plus a protocol layer. It runs either in the kernel or as a daemon that executes every app's GPU work. The brief's question 3 flags exactly that background-daemon shape.
- [V] The guest bundle carries the string `Paravirtual device` (0x3d80a), next to vendor and product name strings. [I] It is likely the `MTLDevice.name` that apps see, unlike a real Mac's `AMD Radeon …`. That fails the brief's question 4: is it visibly a virtual GPU? We would control the host-reported feature families, so the families are not a blocker; the name likely is.

## Options this leaves

These are inferences, for the Orchestrator and the owner. Nothing here decides them.

1. **dGPU stable = display only.** Metal on the dGPU stays an A-path research/alpha build with AMFI relaxed. Honest, but a real Mac Pro gets Metal from its AMD GPU.
2. **iGPU Metal via B, if the full RB-0004c passes.** Stable gets AMFI-intact Metal from the iGPU through Apple's own gfx10.3 bundles, while the dGPU drives displays or sleeps (ADR-0005). A weaker GPU, but the only parity-clean acceleration path found.
3. **dGPU Metal via C.** Apple's signed guest bundle, with our kext (plus a compiler service) as the host. AMFI stays intact. Cost: a full Metal implementation and an AIR→RDNA3 compiler, more than option A's native driver. Apps likely see "Paravirtual device". Needs an owner ruling on whether naming Apple's paravirt bundle from our own service is itself a disguise.
4. **Wait for Apple to ship gfx11 support.** There is none on 25G241, and macOS is pinned. Not actionable.

## Cost of the next steps (Lead sessions at high, rough)

- **Full RB-0004c scoped to the iGPU: 2–3 sessions.** It covers:
  - ASIC selection in the bundle;
  - UMA;
  - the `AMDRadeonX6000` user-client interface;
  - gfx1036 compatibility.
- **Full RB-0004b: only if the owner keeps option 3 open, about 2 sessions.** It covers:
  - the guest user-client ABI;
  - the serialization format;
  - whether Metal validates the service class.
- **Display-driver ADR: 1–1.5 sessions, unchanged.** Display-only works without Metal (RB-0004a Q6).
- **ADR-0004 decision: about ½ session,** once the owner has chosen among the options above.

## Not checked

- LLVM's `gfx10-3-generic` processor definition, which would confirm that gfx1030 code runs on gfx1036.
- PM4/MES differences (RB-0004c question 4). Not needed for the Navi 31 verdict.
- The paravirt kext's `start`, beyond static imports and the absence of `cpuid`.
- Whether Metal or `IOAccelerator.framework` validates anything beyond the plugin properties before `AppleParavirtDevice` gets the port.
