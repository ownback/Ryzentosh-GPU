# RB-0004b/c gate check: Apple's AMD shader ISA targets, and the paravirt guest stack on bare metal

Status: done 2026-11-27. Issue ownback/Ryzentosh-GPU#12. This is a cheap yes/no gate before the full RB-0004b (#2) and RB-0004c (#3) briefs; the Root Orchestrator approved the M1.0 plan.

Evidence rules are the same as RB-0004a ([RB-0004a-metal-loading-chain.md](RB-0004a-metal-loading-chain.md#conventions)):
- **[V]** means verified. **[I]** means inferred, and the reasoning is given.
- Shared-cache images were extracted from the 25G241 cache (UUID 31374756-…) with `tools/re/dscx`. Kexts come from KDK 25G241, and their UUIDs match the loaded or installed builds.
- `strings -t x` offsets are file offsets in the extracted image or the thinned KDK binary.
- Mesa (MIT) is cited as repo @ commit + path:line from the local clone. Only names, offsets and behaviour are recorded.

## Verdicts

| Option | Verdict | Why (details below) |
|---|---|---|
| **B for the RX 7900 XTX (Navi 31, gfx11)** | **Dead in practice** | Apple's AMD stack on 25G241 has no gfx11 code path at all. Making Apple's gfx10.3 output run on gfx11 would need a full recompiler, not a patch: about 57% of the ISA opcode entries are renumbered or removed, FS interpolation instructions are gone, and NGG becomes mandatory with attributes passed through memory. |
| **B for the Raphael iGPU (gfx1036, RDNA2)** | **Proceed to the full RB-0004c, scoped to the iGPU** | Raphael belongs to the same ISA generation (GFX10.3) that Apple's compiler emits. Apple doesn't support it today (no APU device IDs, UMA memory). Whether per-ASIC tables and the kernel interface can be satisfied honestly is exactly what the full brief must measure. |
| **C, the paravirt guest stack, on bare metal** | **Dead for parity** | The guest stack matches only a PCI device with Apple's vendor ID and the virtual device ID `0xEEEE`, so we would have to fake that device: a disguise. Every Metal call is serialized to a "host" that must run it, including compiling AIR shaders. On bare metal that host would be a full Metal implementation with an AIR→RDNA3 compiler in our kext or a daemon. That is a native driver plus a serialization layer. Apps would also see "Paravirtual device" with host-clamped families. |

**Consequence for ADR-0004 [I].** On 25G241 no AMFI-intact path to Metal on the 7900 XTX survives:
- B is dead for gfx11.
- C is dead for parity.
- D was already dead (RB-0004a).

The only Metal path left for the dGPU is A, which is research/alpha only and needs an AMFI relaxation. The only possible AMFI-intact Metal path at all is B on the iGPU. This is an owner-level decision for ADR-0004 and ADR-0005: what "stable" means for dGPU acceleration. See [Options this leaves](#options-this-leaves).

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

- [V] **No gfx11 path exists.** I searched 18 files, case-insensitive, for `gfx_?11`, `navi_?3[0-9]`, `gc_?11_`, `gfx1100`, `nv3[0-9]` and the RDNA3 codenames (`plum`, `wheat`, `hotpink`), with zero matches. The files are every AMD file in the extracted cache's `/System/Library/Extensions` (the bundles, the compiler plugins, and AMDMTLBronzeDriver) plus the KDK kexts AMDRadeonX5000, AMDRadeonX6000, AMDRadeonX6000HWServices and AMDRadeonX6000Framebuffer. Command: `strings -a <file> | grep -ciE '…'`.
- [V] **The compiler is per generation, and the newest is GFX10.3.** libSC's emitter and target classes are:
  - `SCGfx10Emitter` (0x874b90), `SCGfx101Emitter` (0x874ba1), `SCGfx103Emitter` (0x8764ec);
  - `SCGfx10Info`, `SCGfx101Info`, `SCGfx103Info` (0x8764fe), `SCGfx10B0Info` and `SCGfx10C0Info`.

  There is no `SCGfx11*` class (0 matches for `Gfx11`).
- [V] **The kernel driver supports only Navi 10, 12, 14, 21 and 23.** The `IOClass` and `IOPCIMatch` pairs in `AMDRadeonX6000.kext/Contents/Info.plist` (`PlistBuddy -c Print`):

  | IOClass | IOPCIMatch device IDs |
  |---|---|
  | `AMDRadeonX6000_AMDNavi10GraphicsAccelerator` | 0x7310, 0x7312, 0x7318, 0x7319, 0x731A, 0x731B, 0x731F |
  | `…Navi12…` | 0x7360 |
  | `…Navi14…` | 0x7340, 0x7341, 0x7343, 0x7347, 0x734F |
  | `…Navi21…` | 0x73A2, 0x73A3, 0x73AB, 0x73BF |
  | `…Navi23…` | 0x73E0, 0x73E3, 0x73FF |

  All are vendor 0x1002. The kext's SDMA engines are `GC_10_1_0`, `_1`, `_2` and `GC_10_3_0` (strings at 0x10b354…0x10e528). There are no Navi 22 or Navi 24 classes, and no APU device ID (Raphael 0x164E is absent).
- [V] The MTL driver contains the LLVM-style target names `gfx1010`–`gfx1012` with `:xnack±` variants, plus `gfx1030`–`gfx1033` (0x3a102c–0x3a4cac). Its per-ASIC tables are named `AMD_GFX10_NAVI10_P`, `…NAVI12_P` and `…NAVI14_M` (0x393cd5–0x393d11). [I] The target names form a generic target-name table, not a support list: the kext matches no gfx1031 or gfx1033 part.

### Why Apple's gfx10.3 output can't simply be translated to gfx11

All three points are [V] from Mesa @ dcf1989.

- **Encoding.** `src/amd/compiler/aco_opcodes.py` lists 1395 opcode entries. 803 of them carry an explicit `gfx11=` value: 650 get a different GFX11 opcode number than on GFX10, and 153 are removed on GFX11 (`gfx11=-1`). The count came from a script comparing each entry's `gfx11=` value with its `gfx10=` value (or the nearest older one). The removed ones include `v_interp_p1_f32`, `v_interp_p2_f32` and `v_interp_mov_f32` (lines 1279–1281) and the `v_interp_*_f16` forms (lines 1392–1393), which are the fragment-shader input interpolation instructions.
- **Geometry pipeline.** `src/amd/vulkan/radv_physical_device.c:2844–2846`: NGG is forced on for `gfx_level >= GFX11`, with no opt-out. That means no legacy VS/GS path.
- **Attributes.** `src/amd/common/ac_gpu_info.c:368`: `has_attr_ring = gfx_level >= GFX11`. Vertex attributes go through a memory ring instead of parameter exports.

[I] A translator would therefore have to rewrite instruction encodings, rebuild FS interpolation, convert any legacy VS/GS output to NGG, and move parameter exports to attribute-ring stores. That is a recompiler from gfx10.3 machine code: fragile, hard to make correct, and outside "Apple's code unchanged". The kernel-side PM4/MES differences (brief Q4) were not assessed, because the ISA gap already decides this option.

### The iGPU inference

- [V] Mesa places Raphael in the same ISA generation as Navi 21:
  - `src/amd/common/amd_family.h:115–122` groups NAVI21…RAPHAEL_MENDOCINO under `/* GFX10.3 (RDNA 2) */`, with GFX11 starting at NAVI31.
  - `ac_gpu_info.c:809–810` maps IP version 10.3 to `GFX10_3` for all of them.
- [V] Mesa does treat Raphael specially in places. For example, `ac_gpu_info.c:1071` applies a MEC firmware bug threshold specific to Raphael.
- [I] Code emitted by `SCGfx103Emitter` for gfx1030 should therefore be ISA-compatible with gfx1036. That still needs checking, against LLVM's `gfx10-3-generic` processor definition, which isn't cloned locally.
- What would block B on the iGPU, all for the full RB-0004c:
  1. How the bundle picks per-ASIC configuration (device-ID tables like `AMD_GFX10_NAVI1x_*`, or properties from the kernel), and whether a Raphael configuration can be given honestly, without claiming to be a Navi 21.
  2. UMA memory. There is no VRAM, so Apple's heaps assume a dGPU layout.
  3. The `AMDRadeonX6000` kernel↔user interface our kext would have to implement.
  4. VCN and DCN differences, which belong to our kext anyway.

## C gate (RB-0004b): the paravirt guest stack on bare metal

### Binaries (25G241, x86_64)

| Image | LC_UUID |
|---|---|
| KDK `AppleParavirtGPU.kext` (x86_64 slice; installed only inside the kernel collection) | 0CAE9E29-BC33-315D-82A7-A7D30E9B971E |
| `/System/Library/Extensions/AppleParavirtGPUMetal.bundle/Contents/MacOS/AppleParavirtGPUMetal` (on disk; x86_64 + arm64e; platform, CodeDirectory flags none) | 65A3F37C-145D-385B-8E4A-52ED3086CCA9 (x86_64) |
| `AppleParavirtGPUMetal.bundle/Contents/Resources/libAppleParavirtCompilerPlugin.dylib` (in the shared cache) | 85D559AC-7ADD-3642-B59A-371F02D4B69C |
| `ParavirtualizedGraphics.framework` (host side, in the x86_64 shared cache) | 08DB4699-8798-362C-81E9-2BE5A7643C16 |

### Findings

- [V] **No runtime VMM check exists in the guest stack.** Neither the kext nor the guest bundle imports `cpuid`, `hv_*` or `sysctl*` (`nm -u`), and neither contains `hv_vmm` or `kern.hv` strings. The kext's only platform-related import is `_PE_parse_boot_argn`.
- [V] **The gate is the match itself.** The kext matches only `IOPCIMatch 0xEEEE106B` (RB-0004a §4), which is vendor 0x106B (Apple) and device 0xEEEE, the virtual device. It names itself `Apple Paravirtualized Graphics Device` (string at 0x156c7).
- [I] On bare metal, our kext would have to publish an `IOPCIDevice` with Apple's vendor ID for hardware that doesn't exist. That is a disguise, and RB-0004b's question 2 says the parity rule forbids it.
- [V] **The guest is a complete Metal front end that serializes to the host.**
  - The guest bundle has 22 `AppleParavirt*` classes, including Device, CommandQueue, CommandBuffer, Blit and ParallelRender encoders, Render and Compute pipeline states, Heap, DescriptorHeap, DescriptorBuffer, Texture, Buffer, Fence, SamplerState, FunctionVariant and ContainerFunction. The x86_64 slice is 380,688 bytes.
  - Its capability structure carries `DeserializerVersion`, `HostGPUFamilies`, `HostGPUFamilyClamped`, `GpuCoreCount` and `MaxMetalShaderVersion` (ObjC type-encoding string). So the guest advertises whatever the host's Metal device reports.
  - The host side, `ParavirtualizedGraphics.framework`, is 1,175,552 bytes with 1534 ObjC methods.
- [V] **Shaders are compiled on the host.** The guest compiler plugin is 12,288 bytes. Its only shader-related strings are the AIR stage names (`air.vertex`, `air.fragment`, `air.kernel`), `AppleParavirtCompiler::init(const AppleParavirtCompilerTargetInfo *)` and `_gpuCompiler`. [I] It forwards AIR to the host and compiles nothing itself.
- [I] **Protocol size.** It is essentially the whole Metal API surface, serialized: the 22 guest classes against 1534 host methods. On bare metal, the "host" (our kext, or a user-space service that the kext talks to) would have to implement all of it:
  - deserialization;
  - Metal semantics on RDNA3;
  - an AIR→RDNA3 shader compiler.

  That is all the work of a native Metal driver, plus a protocol layer, plus a disguise. A user-space service that runs every app's GPU work is also exactly the background-daemon pattern that brief question 3 flags.
- [V] **Apps would see a virtual GPU.** The guest bundle carries the string `Paravirtual device` (0x3d80a). [I] That is the device name apps would see, unlike a real Mac's `AMD Radeon …`. Its families are clamped to the host's (`HostGPUFamilyClamped`), which fails brief question 4 (parity of `MTLDevice.name` and the feature sets).

## Options this leaves

These are inferences, for the Orchestrator and the owner. They are not decided here.

1. **dGPU stable = display only.** The dGPU stays display-only in stable, and Metal on the dGPU stays an A-path research/alpha build with AMFI relaxed. That is honest, but a real Mac Pro gets Metal from its AMD GPU.
2. **iGPU Metal via B (if the full RB-0004c passes).** Stable gets AMFI-intact Metal from the iGPU through Apple's own gfx10.3 bundles. The dGPU drives displays or sleeps (ADR-0005). That is a weaker GPU, but it is the only parity-clean acceleration path found.
3. **Wait for Apple.** Apple ships gfx11 support in macOS: there is none on 25G241, and macOS is pinned. Not actionable.

## Cost of the next steps (Lead sessions at high, rough)

- **Full RB-0004c scoped to the iGPU:** 2–3 sessions. Covers ASIC selection in the bundle, UMA, the `AMDRadeonX6000` user-client interface, and the gfx1036 compatibility check.
- **Full RB-0004b:** none. The gate kills C. Optionally, ½ session to record the guest↔host transport (BAR and virtual-channel layout), only if the Orchestrator wants it for the record.
- **Display-driver ADR:** unchanged, 1–1.5 sessions. Unaffected, because display-only works without Metal (RB-0004a Q6).
- **ADR-0004 decision:** ½ session, after the owner picks among the options above.

## Not checked

- LLVM's `gfx10-3-generic` definition, which would confirm gfx1030 code runs on gfx1036. LLVM isn't cloned locally.
- PM4 and MES differences (RB-0004c question 4). Not needed for the Navi 31 verdict.
- Whether the paravirt kext checks anything at `start` beyond the PCI match, such as BAR layout or a version handshake with the host. Static imports show no VMM check, but `start` was not disassembled. A handshake would only add work, since the disguise already decides C.
