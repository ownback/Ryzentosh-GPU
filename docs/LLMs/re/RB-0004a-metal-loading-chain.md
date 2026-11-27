# RB-0004a: Metal driver loading chain and library validation on 25G241

Status: **all seven questions answered** (2026-11-27).
- User-space half: done.
- Kernel half: done on KDK 25G241. K1, K2 and K4 are verified. K3 and K5 are answered as far as the decision needs; see [What is left open](#what-is-left-open).
- Citation review by the reviewer subagent (claude-fable-5-2): see the PR.

Brief: control plane `docs/Research/briefs/RB-0004a-metal-driver-loading-chain.md`. Issue: ownback/Ryzentosh-dGPU#1. ADR: control plane `.agents/decisions/ADR-0004-user-space-driver-delivery.md`.

## Conventions

- **[V] verified**: seen directly, either in a 25G241 binary (symbol, import, string, offset, instruction) or on the live system (the command is given).
- **[I] inferred**: follows from verified facts but was not observed directly. The reasoning is given.
- User-space citations give the image, its LC_UUID and the unslid shared-cache VM address. The addresses come from `nm -m` on images extracted with `tools/re/dscx`.
- Kernel citations give the KDK kext, its LC_UUID and the kext-relative address. Addresses come from `nm` on the KDK binary (they are unstripped) and from Ghidra 12.2 via REA, or from `otool -tV`. The KDK UUIDs match the loaded kexts (`kmutil showloaded --list-only`), and the KDK kernel UUID matches the running kernel (`sysctl kern.uuid`).
- `+N` is a byte offset from a symbol, taken from crash-report frames.
- Study-only sources (Vermilion, nullarc, nvidia-macos-driver) are cited as repo + commit + path, as facts only. No code was copied.
- Observations are read-only and sanitized: the home directory is `~`, and host names, volume names, third-party team IDs, serials and Mac UUIDs are left out.
- Only names, offsets and behaviour are recorded. There are no decompiled listings (licensing.md §7).

### Binaries (macOS 26.7.1, build 25G241, x86_64)

Shared cache: `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h` (+ `.01`–`.06`), cache UUID `31374756-89B4-34E8-A34F-56C5D57216A1`.

| Image | LC_UUID |
|---|---|
| `Metal.framework/Versions/A/Metal` | 1EFC99EB-0C56-3592-8090-C533B987E870 |
| `/usr/lib/system/libsystem_sandbox.dylib` | 67D9F15F-C05C-3C42-A251-A8239A5BAEB1 |
| `SkyLight.framework/Versions/A/SkyLight` | 038F2E24-7102-302E-B90F-0AA2CC349717 |
| `IOGPU.framework/Versions/A/IOGPU` | A919AFA3-39D4-3D7A-88AC-01BA820C207A |
| `OpenGL.framework/Versions/A/Libraries/libGFXShared.dylib` | F1352CD7-0BE6-39B5-B216-7364772068DA |
| `OpenCL.framework/Versions/A/Libraries/libcl2module.dylib` | C915E5F5-B964-3862-B7A0-D3680F0D909F |
| `AppleGVA.framework/Versions/A/AppleGVA` | CA5414F3-6937-3C05-9EA2-D82B35AFD4F0 |
| `AppleGVACore` / `AppleVA` / `AppleVPA` | AE432F34-E493-30A0-B817-39F12EBF6AA9 / 7533F787-2CA5-3A96-8DC5-FA34F9035E37 / BF48FDCA-8143-3BE6-B0B1-D574E7A1D0E2 |
| `MTLCompiler.framework/Versions/32024/MTLCompiler` | 889C9859-73F9-369A-9E65-E06DEFB79D32 |
| `QuartzCore.framework/Versions/A/QuartzCore` | 2E3324AE-9637-3251-A7A2-01E19865C6A5 |
| `CoreImage.framework/Versions/A/CoreImage` | 652E6F5E-0AD1-3468-A159-02434C36B73B |
| `/System/Library/Extensions/AMDRadeonX6000MTLDriver.bundle` | BBB186ED-C8E3-3641-BDED-1B0202AA2173 |
| `/System/Library/Extensions/AMDRadeonX6000Shared.bundle` | D283E650-58E1-3852-8554-0636A6FEC8A0 |
| `/System/Library/Extensions/AMDShared.bundle` | AF9E7C89-03AC-3220-9EDE-5694BC124C75 |
| `/usr/libexec/amfid` (on disk, x86_64 slice, stripped) | 548660AE-97D9-3B6A-BC69-73A848FE197C |
| `/System/Library/KernelCollections/BootKernelExtensions.kc` (file) | sha256 `21d6da1c4c3e7b72dddf5144da8a4c4b48e294249a16018a5006b61bb2155ccc` |
| KDK `kernel` (release) | 1291D44A-C0CD-3AC7-A9E4-CA2749B33959 (= running kernel) |
| KDK `AppleMobileFileIntegrity.kext` 1.0.5 | 40346830-00EF-3293-98B1-AE32CC6C5AD0 (= loaded) |
| KDK `Sandbox.kext` 300.0 | B1758144-A0DD-3D1D-A974-9F15549847CC (= loaded) |
| KDK `IOAcceleratorFamily2.kext` 487.4.4 | 6C4A16B1-66DC-3A8B-9F0B-D3E027B16EB1 (= loaded) |
| KDK `IOGraphicsFamily.kext` 600 | 74AA6483-8AB4-3A94-8143-5E306C16D7DA (= loaded) |
| KDK `IOGPUFamily.kext` | 9A5D9AAA-9682-3BF4-859B-7839A205C2FD (not loaded on this machine) |
| KDK `AMDRadeonX6000.kext` | DCD61202-702C-339A-840E-6E590CA6D74C (not loaded) |
| KDK `AppleParavirtGPU.kext` (x86_64 slice) | 0CAE9E29-BC33-315D-82A7-A7D30E9B971E |

Extraction note: Apple's `dsc_extractor.bundle` refused the live cache during the 2026-11-27 boot, because page 67726 of the main file (VM 0x7ff81088e000, `AppleSystemInfo.framework` text +0x4000) no longer matched its CodeDirectory slot. It was the only mismatch in all seven cache files (`tools/re/dsc_cs_check.py`). The file's ctime had not changed. [I] A Lilu user-space patcher (RestrictEvents) patched that page in memory, and the change was visible through the unified buffer cache. That extraction used a copy with the slot recomputed. After the reboot, `tools/re/dsc_fix_copy.py` found no mismatching page, and the cache extracted cleanly.

## Answers in brief

1. **Discovery.** Metal matches `IOAccelerator` services only and reads `MetalPluginName`. It resolves the name with `gpu_bundle_find_trusted`, which searches `/Library/GPUBundles` first and then `/System/Library/Extensions` and requires a SIP-trusted path. Metal then loads the bundle and instantiates `MetalPluginClassName`, falling back to the principal class. The class must subclass `_MTLDevice`. If any step fails, Metal skips the service without a word, and there is no software Metal device on x86. GL, CL, video decode, MTLCompiler and Apple's own AMD and Intel bundles use the same trusted-path helper.
   - In the kernel, `IOGPU` and `IOGraphicsAccelerator2` both derive from `IOAccelerator`, so both families are visible to that matching.
2. **Signature gates.** There are three gates:
   - **Path trust:** the SIP storage class `KernelExtensionManagement`, or the path is in the shared cache.
   - **Sandbox:** the `file-map-executable` rules. The WebKit GPU process can map executable code only from system-volume paths.
   - **AMFI library validation:** applies at mmap and `F_CHECK_LV` time, only in processes with `CS_REQUIRE_LV`.

   The six LV processes (WindowServer, Safari, Finder, SystemUIServer, Messages, the WebKit GPU process) carry `CS_REQUIRE_LV` because their CodeDirectory sets `library-validation`. AMFI's rule for a platform process is strict: **the mapped file must be platform**. The exceptions all need Apple-private entitlements, Apple-internal or SIP-relaxed configurations, or a boot-arg. None exists for GPU bundles. Staging a bundle into `/Library/GPUBundles` accepts only Apple-anchored or NVIDIA Developer ID bundles.
3. **Process inventory.** 22 distinct process names own user clients on the accelerator, and Dock maps the plugin without one. AMFI enforces LV in exactly the six processes above. This boot it logged 126 rejections there, and VermilionTrust overrode all 126. All other clients, including VTDecoderXPCService and DynamicBackgroundPosterExtension, have CodeDirectory flags 0x0 and map the plugin without any LV check.
4. **Seams.** No Apple seam lets third-party code serve Metal to platform clients while AMFI stays intact:
   - MTLCompilerService is platform, hardened and limited to trusted paths.
   - VTDecoderXPCService (platform, `disable-library-validation`) hosts only video decoders.
   - AMFI's compilation-service channel needs Apple-private entitlements on both sides.
   - IOGPU's generic `IOGPUMetalDevice` has no x86 driver built on it.

   The only Apple-signed Metal client halves that could serve the 7900 XTX are Apple's AMD bundles (B) and the paravirt guest bundle (C).
5. **AMFIPass and VermilionTrust.** The current boot has no `amfi=` boot-args, and AMFI rejects the plugin every time. VermilionTrust swaps AMFI's hook slots `mpo_file_check_mmap` (+0x120) and `mpo_file_check_library_validation` (+0x200), which are confirmed against the KDK. It turns refusals into success for 18 listed cdhashes. AMFIPass 1.4.1 is loaded but is not what admits the plugin.

   Two other relaxations exist in Apple's code:
   - `amfi=0x80` / `amfi_get_out_of_my_way` makes AMFI mark every signature as platform, if SIP allows the kernel debugger.
   - amfid's `DisableLibraryValidation` preference turns every LV failure into "would have failed (but is disabled)", if SIP allows `APPLE_INTERNAL`.
6. **No-Metal behaviour.** SkyLight decides once per WindowServer launch, after IOKit quiesces. If there is no non-headless Metal device, it activates the software compositor. A 25G241 boot on 2026-11-20 did exactly that and ran a normal desktop session for 30+ minutes. A display-only M1 build is bootable. The catalogue of affected apps is TESTPLAN T-0002.
7. **Poster crash.** DynamicBackgroundPosterExtension aborts in `-[MTLIOAccelDevice newIndirectArgumentEncoderWithLayout:]`. This is the only abort or trap stub in Metal's IOAccel base classes. The plugin's device class does not override `newArgumentEncoderWithLayout:`, and Apple's AMD driver does. It is a driver API gap, recorded as TESTPLAN T-0001. The MercuryPosterExtension reports are iOS Simulator crashes.

---

## Q1. Discovery: from IORegistry service to loaded bundle

### 1.1 Metal.framework (Metal, LC_UUID 1EFC99EB)

- [V] `-[MTLIOAccelServiceGlobalContext init]` @ 0x7ff80f641be6:
  - Creates the IOKit main port and a notification port on the dispatch queue `com.Metal.DeviceDispatch`.
  - Registers `IOServiceAddMatchingNotification("IOServicePublish", IOServiceMatching("IOAccelerator"), __mtlIOAccelDeviceMatched)`. The callback `__mtlIOAccelDeviceMatched` is @ 0x7ff80f641ae0.
  - Walks the services that are already published.
  - The only matching dictionary on this path is the class name `IOAccelerator` (kernel class hierarchy in §1.5).
- [V] `getMetalPluginClassForService` @ 0x7ff80f641947 (imports `_gpu_bundle_find_trusted`):
  1. Reads the property `MetalPluginName` as a CFString, converted to UTF-8 (at most 255 bytes).
  2. Calls `gpu_bundle_find_trusted(name, path, 0x400)` (§1.2).
  3. Calls `+[NSString stringWithUTF8String:]`, then `+[NSBundle bundleWithPath:]`.
  4. Reads `MetalPluginClassName` and calls `-[NSBundle classNamed:]`. If the key is missing or not a string, or the class is not found, it falls back to `-[NSBundle principalClass]`.
  5. Accepts the class only if `+[cls isSubclassOfClass:_MTLDevice]` holds.

  Any failure yields no class, and the caller skips the service with no log line.
- [V] `-[MTLIOAccelService initWithAcceleratorPort:deviceClass:]` @ 0x7ff80f6422e1:
  - Skips services that carry `IOServiceCompatibility`.
  - Adds an `IOGeneralInterest` notification.
  - Skips a `Removable` service when `_mtlAvoidRemovable` (@ 0x7ff80f46a7ac) says so.
  - Gives up when `SafeEjectRequested` is set.
  - Otherwise calls `[[cls alloc] initWithAcceleratorPort:service]`, then `-_setAcceleratorService:`, then `MTLAddDevice` (@ 0x7ff80f46b3b0).
- [V] `MTLDeviceArrayInitialize` (`__ZL24MTLDeviceArrayInitializev` @ 0x7ff80f59790a) runs once. It installs the capture and HUD interposers when enabled, then calls `MTLRegisterDevices` (@ 0x7ff80f642759).
- [V] `MTLCreateSystemDefaultDevice` @ 0x7ff80f480a91 takes CoreGraphics' `CGSCreateDefaultMetalDevice` (found through dlsym) when present, and the device array otherwise. `MTLCopyAllDevices` @ 0x7ff80f46a632 returns the array.
- [V] There is no software fallback. `MTLCreateSimulatorDevice` (@ 0x7ff80f597854) exists, but nothing inside Metal calls it (REA cross-references).
- Principal-class contract [V]: subclass `_MTLDevice` and implement `-initWithAcceleratorPort:` (an `io_service_t`). Q7 adds a third requirement: override `-newArgumentEncoderWithLayout:`. See [INTERFACES.md](../INTERFACES.md).

### 1.2 The trusted-bundle resolver (libsystem_sandbox, LC_UUID 67D9F15F)

- [V] `gpu_bundle_find_trusted` @ 0x7ff810883270:
  - Walks `GPU_STANDARD_BUNDLE_PATHS` (@ 0x7ff84141c8d0) in order: `/Library/GPUBundles`, then `/System/Library/Extensions`.
  - For each directory it formats `"%s/%s.bundle"` and `stat()`s the result, which must be a directory. It then asks `gpu_bundle_is_path_trusted`, and the first trusted hit wins.
  - Return values: 0 = found, 1 = nothing trusted, −1 = error.
- [V] The name is not sanitized. The live service publishes `MetalPluginName = "../../../Library/GPUBundles/NVMTLDriver"` (§1.4), and it resolves. [I] Because `/Library/GPUBundles` is searched first, a plain name would already reach that directory.
- [V] `gpu_bundle_is_path_trusted` @ 0x7ff81088343b trusts a path when either of these holds:
  - `rootless_check_trusted_class(path, "KernelExtensionManagement")` succeeds (@ 0x7ff810883429), or
  - `_dyld_shared_cache_contains_path(path)` is true.
- [V] `/Library/GPUBundles` belongs to that storage class: `/System/Library/Sandbox/rootless.conf` line 7, and `ls -ldO /Library/GPUBundles` shows `restricted` with xattr `com.apple.rootless: KernelExtensionManagement`.
- [V] The class's write entitlements appear as strings in Sandbox.kext (B1758144): `com.apple.rootless.storage.KernelExtensionManagement` and `com.apple.private.security.storage.KernelExtensionManagement`. So does the staging path `/private/var/db/kernelextensionmanagement/staging`.
- [I] With SIP on, only holders of those entitlements, the kext-management daemons, can write into the class, and they stage only Apple- or NVIDIA-signed bundles (Q2). The kernel's trust decision under csr 0x0A03 was not traced. It does not affect the decision, because the live plugin passes it (§1.4) and a stable build cannot use this path at all.

### 1.3 Other consumers of the same resolver

[V] Imports and strings below are from `nm -m` and `strings` on the extracted images:

| Image | Resolver import | Bundle keys and paths in strings |
|---|---|---|
| IOGPU | `gpu_bundle_find_trusted` | `MetalPluginName` / `MetalPluginClassName`; generic device `-[IOGPUMetalDevice initWithAcceleratorPort:]` @ 0x7ff906a28461, `…options:]` @ 0x7ff906a28475 |
| libGFXShared (OpenGL) | `gpu_bundle_find_trusted` | `IOGLBundleName` |
| libcl2module (OpenCL) | `gpu_bundle_find_trusted` | key not traced |
| AppleGVA, AppleGVACore, AppleVA, AppleVPA | `gpu_bundle_is_path_trusted` | `IOVARendererID`, `IOVARendererSubID`, `IODVDBundleName`, `IOGVA*`; `GPUBundles`, `/System/Library/Extensions/` |
| MTLCompiler (versions 32023 and 32024) | `gpu_bundle_is_path_trusted` | `GPUBundles`, `/System/Library/Extensions/AppleMetalOpenGLRenderer.bundle` |
| AMDShared, AMDRadeonX5000Shared, AMDRadeonX6000Shared, AppleIntel{ICL,KBL}Graphics{GL,MTL}Driver | `gpu_bundle_find_trusted` | Apple's own driver bundles resolve their sub-bundles the same way |
| SkyLight, QuartzCore, CoreImage | none | they consume devices from Metal (`MTLCreateSystemDefaultDevice` / `MTLCopyAllDevices` imports) |

- [I] Every Apple GPU component in user space resolves driver code through the same two directories and the same SIP trust test.
- [I] OpenCL's CPU engine is `libcldcpuengine`. Its GPU path probably goes through the GL bundle. Not traced.

### 1.4 The live registry (the probe)

- [V] `ioreg -l -w0 -r -c IOAccelerator`, sanitized:
  - `IOClass = "NMXAccel"` from `org.vermilion.accel` 0.1.1 (Aux KC fileset entry, `/Library/Extensions/VermilionAccel.kext`), on `IOPCIDevice`.
  - `MetalPluginName = "../../../Library/GPUBundles/NVMTLDriver"` and `MetalPluginClassName = "NVMTLDevice"`.
  - `IOGLBundleName = "AppleMetalOpenGLRenderer"` and `IOCFPlugInTypes = {ACCF0000-…="IOAccelerator2D.plugin"}`.
- [V] `ioreg -l -w0 -r -c IOGPU` returns nothing, and IOGPUFamily is not loaded.
- [V] `ls -la /Library/GPUBundles`:
  - `NVMTLDriver.bundle` is a symlink to `/System/Library/CoreServices/CoreTypes.bundle/Contents/Library/PhxGPU/NVMTLDriver.bundle`.
  - The directory also holds `nvmtl-allow.txt`.
  - `codesign -dvvv` shows the bundle is ad-hoc signed, bundle id `com.nullmoth.NVMTLDriver`.

### 1.5 Kernel class hierarchy (K4)

[V] Superclasses come from the relocation on each class's `X::superClass` pointer (`tools/re/kext_superclass.py` on the KDK x86_64 binaries):

| Class | Kext (LC_UUID) | Superclass |
|---|---|---|
| `IOAccelerator` | IOGraphicsFamily (74AA6483) | `IOService` |
| `IOGraphicsAccelerator2` | IOAcceleratorFamily2 (6C4A16B1) | `IOAccelerator` |
| `IOGPU` | IOGPUFamily (9A5D9AAA) | `IOAccelerator` |
| `AMDRadeonX6000_AMDGraphicsAccelerator` | AMDRadeonX6000 (DCD61202) | `IOGraphicsAccelerator2` |
| `AppleParavirtAccelerator` | AppleParavirtGPU x86_64 (0CAE9E29) | `IOGraphicsAccelerator2` |
| `IOAccelDevice2`, `IOAccelSharedUserClient2` | IOAcceleratorFamily2 | `IOUserClient` |
| `IOGPUDeviceUserClient` | IOGPUFamily | `IOUserClient` |

- [I] On x86, both IOAcceleratorFamily2 services and IOGPU services are visible to Metal's `IOAccelerator` matching.
- [V] User-client entitlements, as strings:
  - IOAcceleratorFamily2: `com.apple.private.allow-explicit-graphics-priority`, `com.apple.private.graphics-restart-no-kill`, `com.apple.private.hid.client.event-monitor`, `com.apple.private.ioaccelmemoryinfo`.
  - IOGPUFamily: `com.apple.private.gpu-restricted`, `com.apple.developer.gpu-restricted`, `com.apple.private.ggdsw.GPUProcessProtectedContent`, `com.apple.private.agx.rt-priority-spi`, `com.apple.private.ioaccelmemoryinfo`, `com.apple.private.iogpu.disable_wired_collector`.
- [I] Nothing in IOAcceleratorFamily2 gates opening an accelerator user client in general. This matches the 22 unprivileged client processes in Q3. The WebKit GPU process's `gpu-restricted` entitlement is only consumed by IOGPUFamily.

## Q2. Signature gates per step

| Step | Gate | Enforced by | Evidence |
|---|---|---|---|
| Resolve the name | The path must lie under `/Library/GPUBundles` or `/System/Library/Extensions` and be SIP-trusted (`KernelExtensionManagement`) or in the shared cache | libsystem_sandbox, then Sandbox.kext | [V] §1.2 |
| Stage into `/Library/GPUBundles` | kext_tools copies a kext's `GPUCompanionBundles` / `GPUOptionalCompanionBundles` there only if the bundle satisfies `anchor apple or (Developer ID CA … and leaf subject.OU = NVIDIA's team ID)` | kext-management daemons (kext_tools staging) | [V] Apple OSS kext_tools-779 @ 3343f4b7, `staging.m` lines 21–35 (`GPU_BUNDLE_STAGING_REQUIREMENT`, `SECURE_GRAPHICS_BUNDLE_STAGING_PATH`), `gpuBundleValidates` (`SecStaticCodeCheckValidity` with `kSecCSStrictValidate`). `pathIsSecure()` treats every path as secure when `csr_check(CSR_ALLOW_UNTRUSTED_KEXTS) == 0`. |
| Read the bundle | Sandbox `file-read*`: `/Library/GPUBundles` is readable to every process that uses `system.sb`, and to the WebKit GPU process | Sandbox | [V] `/System/Library/Sandbox/Profiles/system.sb` lines 256–259; `WebKit.framework/Versions/A/Resources/com.apple.WebKit.GPUProcess.sb` lines 336–337 |
| Map executable pages | Sandbox `file-map-executable` | Sandbox | [V] `system.sb` lines 43–56 allow only `/System/Library/Extensions`, `/System/Library/{Frameworks,PrivateFrameworks,SubFrameworks}`, `iOSSupport` and `/usr/lib`. `com.apple.WindowServer.sb` lines 29–35 add `/System/Library/CoreServices`, `/System/Library/Extensions` and `/Library/GPUBundles`. **`com.apple.WebKit.GPUProcess.sb` lines 208–212 and 247–250 allow only `/System/Library/{Components,CoreServices,Extensions,Video/Plug-Ins,Frameworks,PrivateFrameworks}` and `/usr/lib`, plus cryptex paths (lines 97–105). `/Library/GPUBundles` is not mappable there.** `com.apple.mtlcompilerservice.sb` lines 63–70 allow `/Library/GPUBundles` only on apple-internal systems. |
| Map executable pages | AMFI library validation | AMFI | [V] §2.1 |
| Signature of the mapped file | Code-signing enforcement and trust caches | AMFI, kernel | [V] `sysctl security.mac.amfi`: `exec_requires_trustcache: 0`, `allow_only_platform_code: 0`, `launch_constraints_enforced: 0`, `developer_mode_status: 1`, `qa_root_certs_allowed: 1`. The kernel log at boot reports no external trust caches. |
| SSV seal | The live system has `Sealed: Broken` and runs from a bless snapshot with Authenticated Root disabled (csr 0x0A03 = `ALLOW_UNTRUSTED_KEXTS`, `ALLOW_UNRESTRICTED_FS`, `ALLOW_UNAPPROVED_KEXTS`, `ALLOW_UNAUTHENTICATED_ROOT`) | APFS, iBoot/OpenCore | [V] `diskutil apfs list` (sanitized: `Sealed: Broken`, `Snapshot Sealed: Broken`), `csrutil authenticated-root status` (`disabled`), `nvram csr-active-config` (`%03%0a%00%00`). The plugin's real path is on the system volume, which is possible only because the seal is broken. |
| TCC | Not a gate | – | [I] Nothing on the Metal, IOKit or NSBundle path consults TCC |

### 2.1 AMFI library validation (K1), AppleMobileFileIntegrity 40346830

**When it runs.**
- [V] Both hooks call the same check: `_file_check_mmap` @ 0x7d04, only for `PROT_EXEC` mappings, and `_file_check_library_validation` @ 0x8fac (dyld's `F_CHECK_LV`).
- [V] Each hook first evaluates library load constraints (`evaluateLibraryLoadConstraintOnLibrary` @ 0x7ef5, `…OnProcess` @ 0x816b). It then calls `library_validation` @ 0x8979 **only if `cs_require_lv(proc)` is true**.
- [V] For a non-exec mapping in an LV process, `_file_check_mmap` clears `PROT_EXEC` from `maxprot`.
- [I] `cs_require_lv()` is xnu's check of `CS_REQUIRE_LV` or the system-wide LV switch (xnu open source, `bsd/kern/kern_cs.c`).

**Who has `CS_REQUIRE_LV`.**
- [V] By `codesign -dv`, exactly WindowServer, Safari, Finder, SystemUIServer (`hard,library-validation`), Messages and `com.apple.WebKit.GPU` carry the CodeDirectory flag `library-validation` (0x2000).
- [V] NotificationCenter, loginwindow, Dock, VTDecoderXPCService and DynamicBackgroundPosterExtension have flags `0x0(none)`.
- [V] `platformHardenFlags` @ 0x14f7b can add a hardening mask of 0x3310 (`REQUIRE_LV|ENFORCEMENT|KILL|HARD|FORCED_LV`) to platform binaries at exec. A per-identity exception list narrows it, the entitlements `com.apple.security.cs.disable-library-validation` and `com.apple.private.cs.automator-plugins` remove `REQUIRE_LV` and `FORCED_LV`, and it is applied only when `macOSPolicyConfig::hardeningEnabled()` holds.
- [V] On this boot no other platform process carries `REQUIRE_LV` (csops, Q3). [I] So the hardening path does not add it here: it is either off or masked. Which switch controls it was not traced.
- [V] `_cred_label_update_execve` @ 0xe228 does two things for an LV process. It requires dyld itself to be platform, killing with "dyld signature cannot be verified …" unless a relaxation flag is set and `csr_check(0x8)` passes (instructions 0xe39c–0xe3d7). It also adds `CS_KILL`.

**The rule** (`library_validation` @ 0x8979, in order) [V]. Each reason string is referenced inside the function at the instruction given:
1. The mapped file must have a signature. A "legacy VPN plugin" signer type is rejected.
2. Out-of-process JIT code (validation category 9) has its own linkage-hash check (`com.apple.private.oop-jit.runner`).
3. Ad-hoc non-platform code may map into ad-hoc non-platform code only if the allow-any-signature flag is set (boot-arg, below) and `csr_check(0x8)` passes.
4. A non-platform file without a Team ID is rejected: "mapped file has no Team ID and is not a platform binary …" (0x8d53).
5. A file in a trust cache of type 0x19 goes to `_checkSMACLibraryValidation` @ 0x951e.
6. **A platform file is accepted.**
7. A non-platform process without a Team ID is rejected: "mapping process has no Team ID and is not a platform binary" (0x8db9).
8. **A platform process is rejected: "mapping process is a platform binary, but mapped file is not" (0x8e9f).**
9. A Team ID mismatch is rejected: "… (non-platform) have different Team IDs" (0x8ef4).
10. Incompatible validation categories are rejected: "not allowing mapping of development code into production process" (0x8f84).

**What a failure turns into** (`_library_validation_failure` @ 0x917c, in order) [V]:
1. Apple-internal system and a root-installed file: "Bypassing Library Validation for installed root" → allowed.
2. The file's cdhash, or its supplemental linkage hash, is in the compilation-service set, and the process has `com.apple.private.amfi.can-execute-cdhash`: "Library Validation overridden …" → allowed. The set is filled only through `AppleMobileFileIntegrityUserClient::loadCompilationServiceCodeDirectoryHash` @ 0xe64, which checks `com.apple.private.amfi.can-load-cdhash` (string reference at 0xec9).
3. Otherwise the kernel asks amfid (`_check_lv_denial`, the reply token must come from amfid). If amfid says LV is disabled, the result is "Library Validation would have failed (but is disabled) …" or "overridden" → allowed.
4. Otherwise: "Library Validation failed: Rejecting …" → denied, and the reason is copied out to dyld.

**amfid's part** (`/usr/libexec/amfid` 548660AE; stripped, Ghidra addresses) [V]:
- The `check_lv_denial` handler @ 0x100001dd3 accepts only kernel requests (all-zero audit token). It answers "disabled" for **every** library and process when a global flag is set, logging "library validation is globally disabled". It does not distinguish platform processes.
- The flag is set @ 0x1000049f0 from `/Library/Preferences/com.apple.security.libraryvalidation.plist`, key `DisableLibraryValidation`.
- The preference is read **only if `csr_check(CSR_ALLOW_APPLE_INTERNAL 0x10) == 0`** (once-block @ 0x1000051d5). csr 0x0A03 does not include 0x10.

**Boot-args** (`_initializeAppleMobileFileIntegrity` @ 0xeb09, instructions 0xeb9a–0xed9a) [V]. The `amfi` value is a bit field:

| `amfi` bit | Named boot-arg | Effect |
|---|---|---|
| 0x1 | `amfi_unrestrict_task_for_pid` | unrestricted task_for_pid |
| 0x2 | `amfi_allow_any_signature` | "signature enforcement disabled" (flag @ 0x3f5f2, read by rule 3 above) |
| 0x4 | – | "library validation will not mark external binaries as platform" |
| 0x80 | `amfi_get_out_of_my_way` | sets both the allow-any-signature flag and the get-out-of-my-way flag (`movw $0x101` @ 0xecb0) |

  Also parsed: `amfi_unrestricted_local_signing` and `cs_enforcement_disable` (the latter gated by `csr_check`).
- [V] Effect of get-out-of-my-way in `_vnode_check_signature` @ 0xf55d (0xfa20–0xfa3a, 0xfd6a–0xfd82): when the flag is set and `csr_check(0x8)` (`CSR_ALLOW_KERNEL_DEBUGGER`) passes, AMFI ORs `CS_PLATFORM_BINARY` into the validated signature and sets its validation category to platform, with the reason "amfi_get_out_of_my_way".
- [I] Every file then counts as platform, so rule 6 accepts the plugin in WindowServer. That is how nullarc's `amfi=0x80` works. On csr 0x0A03, which lacks 0x8, the branch is not taken.

**No GPU exception.**
- [V] The LV path above has no path-based, Team-ID-based or GPU-bundle exception.
- [V] A byte search of the boot KC finds neither `GPUBundles` nor NVIDIA's team ID.
- [V] None of the 11 probed hosts carries any `com.apple.private.amfi.*` entitlement or `clear-library-validation` (`codesign -d --entitlements`).

### AMFI strings in the boot KC (file offsets, sha256 above)

These match the KDK kext's strings and confirm that the loaded AMFI is the one analysed.

[V] Library-validation outcomes and reasons:

| Offset | String |
|---|---|
| 0x1aaacc0 | `Library Validation failed: Rejecting …` |
| 0x1aaac30 | `Library Validation overridden …` |
| 0x1aaab90 | `Library Validation would have failed (but is disabled) …` |
| 0x1aaab50 | `Bypassing Library Validation for installed root …` |
| 0x1a9def8 | `mapping process is a platform binary, but mapped file is not` |
| 0x1a9df35 | `mapping process and mapped file (non-platform) have different Team IDs` |
| 0x1a9dd67 | `mapped file has no Team ID and is not a platform binary …` |
| 0x1a9debc | `mapping process has no Team ID …` |

[V] Entitlements and boot-args:

| Offset | String |
|---|---|
| 0xab766c | `com.apple.security.cs.disable-library-validation` |
| 0xab76c4 | `com.apple.private.security.clear-library-validation` |
| 0x1aa0bc5 | `amfi_get_out_of_my_way` |
| 0x1aa0b7c | `amfi_allow_any_signature` |
| 0xaa71f6 | `cs_enforcement_disable` |
| 0x1aa0aaa | `amfi_unrestrict_task_for_pid` |
| 0x1aa0c20 | `amfi_unrestricted_local_signing` |

### Host processes and LV-relevant entitlements

[V] Columns come from `codesign -d --entitlements - --xml <binary>`, `codesign -dv` and `tools/re/csprobe <pid>` (csops `CS_OPS_STATUS`, validation category):

| Host | Platform | CodeDirectory flags | `REQUIRE_LV` (csops) | LV-relevant entitlements |
|---|---|---|---|---|
| WindowServer | yes | `library-validation` | yes (0x26016a01) | `com.apple.private.gpuwrangler`; no disable-LV |
| com.apple.WebKit.GPU | yes | `library-validation` | yes (0x26016a01) | `com.apple.private.gpu-restricted`, `com.apple.developer.hardened-process`, `com.apple.security.cs.jit-write-allowlist` |
| Safari | yes | `library-validation` | yes (0x26016a01) | `com.apple.security.app-sandbox` |
| Finder | yes | `library-validation` | yes (0x26016a01) | none |
| SystemUIServer | yes | `hard,library-validation` | yes (0x26016b01) | not dumped |
| Messages | yes | `library-validation` | not running at probe time | not dumped |
| VTDecoderXPCService | yes | none | no (0 AMFI rejections while it maps the plugin, Q3) | **`com.apple.security.cs.disable-library-validation`**, `com.apple.developer.hardened-process` |
| MTLCompilerService | yes | not checked | not running at probe time | `com.apple.developer.hardened-process` |
| DynamicBackgroundPosterExtension | yes | none | not running at probe time | `com.apple.security.app-sandbox` |
| NotificationCenter, loginwindow, Dock | yes | none | no (0x26014a01 class) | none |
| A Developer ID Electron app and its GPU helper | no (category developer-id; 0x22014201 / 0x22010001) | – | no | `disable-library-validation`, `allow-jit`, `allow-unsigned-executable-memory` |

## Q3. Process inventory (live boot, 2026-11-27)

Method:
- [V] `ioreg -l -w0 -r -c IOAccelerator`: `IOUserClientCreator` of every user client, reduced to process names. Kernel names are truncated to 16 characters.
- [V] `lsof -p <pid> | grep NVMTLDriver` for processes owned by the same user. For `_windowserver`-owned processes, the evidence is the plugin's own log lines from their pids plus AMFI's mmap lines, because `vmmap` and `lsof` need root there.
- [V] `tools/re/csprobe <pid>` for csops flags.
- [V] The AMFI log via `/usr/bin/log show --last boot --predicate 'eventMessage CONTAINS "Library Validation"' | python3 -I tools/re/lv_timeline.py`. In zsh, `log` is a builtin, so call `/usr/bin/log`.

| Process | Accelerator user clients | Maps the plugin | LV enforced | AMFI rejections this boot (files) |
|---|---|---|---|---|
| WindowServer (2 instances: first at 12:52:44, second at 12:52:49) | 11: `IOAccelDevice2`, `IOAccelSharedUserClient2`, `IOAccelDisplayPipeUserClient2`, `NMX2DContext`, 7× `NMXSurface` | yes | yes | 3: NVMTLDriver, libnvmtl_translate, libvulkan_radeon |
| com.apple.WebKit.GPU | 3 | yes | yes | 8 (adds libLLVM, libzstd) |
| Safari | 3 | yes | yes | 6 |
| Finder | 2 | yes | yes | 5 |
| SystemUIServer | 2 | yes | yes | 5 |
| Messages (not running at probe time) | – | yes, per the AMFI log | yes | 6 |
| VTDecoderXPCService | 3 | yes | no (disable-LV, flags none) | 0 |
| avconferenced, NeptuneOneWallpaper, iconservicesagent, NotificationCenter, openAndSavePanelService, UserNotificationCenter, DockHelper, TextInputSwitcher, TextInputMenuAgent, SafeEjectGPUService, CursorUIViewService, com.apple.dock.extra, AccessibilityUIServer, ControlCenter, loginwindow | 2–3 each | yes | no (platform, `RUNTIME` without `REQUIRE_LV`) | 0 |
| Dock | 0 | yes | no | 0. The plugin declines to make a device in Dock (`-Dock` in `/Library/GPUBundles/nvmtl-allow.txt`). |
| A Developer ID Electron app and its GPU helper | 5 | yes | no | 0 |
| DynamicBackgroundPosterExtension | not running at probe time | yes: it crashes inside the plugin's device (Q7) | no (flags none) | – |
| MTLCompilerService | not running at probe time | – | – | – |
| MercuryPosterExtension | not a macOS process on this system (Q7) | – | – | – |

- [V] All 126 rejections carry the same reason: `mapping process is a platform binary, but mapped file is not`. The first is at 12:52:44.467, in WindowServer (first instance). After the reboot, a fresh boot shows the same pattern: `debug.phxtrust_stat` reports `libval_denied=16 mmap_exec_denied=16 overrides=32 denied_unlisted=0`.
- [V] Platform processes without `REQUIRE_LV` map the ad-hoc plugin with no AMFI check at all (§2.1, "When it runs").
- [V, study-only facts] The legacy stack restarts WindowServer once, by design. `~/gpu/phxboot-navi31.sh` lines 4–5 and 19 (run by `/Library/LaunchDaemons/local.phxboot.plist`) arm the display and then do one `killall -9 WindowServer`, "so WindowServer enumerates Metal fresh". [I] This matches SkyLight deciding once per launch (Q6). A real Mac publishes its accelerator during kext matching, before IOKit goes quiet, so its first WindowServer already sees Metal. Parity requirement (T-0003): the Ryzentosh accelerator must publish before IOKit quiesces, and no WindowServer restart is allowed.

## Q4. Out-of-process seams

| Seam | Who loads what | Can third-party code sit behind it with AMFI intact on the client? |
|---|---|---|
| MTLCompilerService (XPC) | Metal sends compile requests. The service dlopens the compiler plugin at a client-supplied `pluginPath`, accepts sandbox extension tokens, and resolves paths with `gpu_bundle_is_path_trusted`. Platform binary, `com.apple.developer.hardened-process`. | No [I]. Its sandbox maps from `/Library/GPUBundles` only on apple-internal systems [V]. Either way the Metal device class must still load inside each client. |
| VTDecoderXPCService | Platform binary with `disable-library-validation` and no CodeDirectory LV flag [V]. | [I] It can map non-platform code (no `REQUIRE_LV`, §2.1), but it hosts VideoToolbox decoders, not Metal devices for other clients. That makes it a real seam for a third-party video decoder (VideoToolbox scope, later brief). |
| AMFI compilation-service channel | A process with `com.apple.private.amfi.can-load-cdhash` registers cdhashes. A process with `com.apple.private.amfi.can-execute-cdhash` may then map that code despite LV [V §2.1]. | No: both ends need Apple-private entitlements that only Apple can grant. |
| IOGPU generic device | `IOGPUMetalDevice` (IOGPU.framework) is an Apple-signed generic Metal front end, and `IOGPU : IOAccelerator` on x86 [V §1.5]. | Not on its own [I]. No image in the extracted 25G241 cache (`/System/Library/Extensions` bundles and PrivateFrameworks) other than IOGPU.framework references the class, so there is no x86 driver class or shader compiler built on it. |
| ParavirtualizedGraphics guest (option C) | On x86_64, `AppleParavirtGPU.kext` (0CAE9E29) is IOAcceleratorFamily2-based (`AppleParavirtAccelerator : IOGraphicsAccelerator2`). It matches PCI `IOPCIMatch 0xEEEE106B` and publishes `MetalPluginName = AppleParavirtGPUMetal` (KDK `Info.plist`) [V]. The IOGPUFamily-based paravirt kexts (`AppleParavirtGPUIOGPUFamily`, `AppleParavirtIOSurface`, `AppleVideoToolboxParavirtualization`, `AppleM2ScalerParavirtDriver`) are **arm64e only** (`lipo -archs`) [V]. | Yes for the client half: the bundle is Apple-signed and passes every gate [I]. Bare-metal viability and the protocol belong to RB-0004b. |
| kext_tools GPU companion staging | Copies a kext's companion bundles into `/Library/GPUBundles`. | No. Only Apple-anchored or NVIDIA Developer ID bundles are accepted [V]. |
| Kernel-side work | Any kext can drive the GPU in the kernel. | [I] It does not remove the need for a user-space `_MTLDevice` subclass in every Metal client. |

## Q5. What AMFIPass and VermilionTrust change

- [V] Current boot-args (`sysctl -n kern.bootargs`, the same before and after the reboot): `-v keepsyms=1 debug=0x100 pci=0x8000000 amtk_awdl_offchan=0 ipc_control_port_options=0 phxdebug=1`. There is no `amfi=…` and no `amfi_get_out_of_my_way`. csr-active-config is 0x0A03.
- [V] `kmutil showloaded --list-only`: Lilu 1.7.2, RestrictEvents 1.1.6, `com.dhinakg.AMFIPass` 1.4.1 and `org.vermilion.trust` 1.0.4 are loaded.
- [V] AMFI itself still says no: 126 `Library Validation failed: Rejecting …` lines in six processes (Q3). There are no `overridden` or `would have failed (but is disabled)` lines.
- [V] The plugin runs anyway. Its `+load` log line from WindowServer (first instance) is at 12:52:44.469, 2 ms after the first rejection.
- [V] `sysctl debug.phxtrust_stat`: `state=installed mode=enforce list=18 libval_calls=71333 libval_denied=63 mmap_exec=71349 mmap_exec_denied=63 overrides=126 denied_unlisted=0`.
- [V] Hook slots (K2), from the KDK kernel DWARF via `lldb` (`&((struct mac_policy_ops *)0)->…`): `mpo_file_check_mmap_downgrade` +0x118, `mpo_file_check_mmap` +0x120, `mpo_file_check_library_validation` +0x200, and `mpc_ops` +0x20 in `mac_policy_conf`.
- [V] AMFI's `mac_ops` table (@ 0x3f618) is zero in the file and filled at run time by `_initializeAppleMobileFileIntegrity`. It stores `_file_check_library_validation` at `mac_ops+0x200` (instruction 0xef58) and `_file_check_mmap` at `mac_ops+0x120` (instruction 0xf069).
- [I] VermilionTrust (study-only: vermilion-xtx @ 40b4f411, `src/vermilion-trust/README.md`):
  - It replaces AMFI's `mpo_file_check_library_validation`, `mpo_file_check_mmap` and `mpo_file_check_mmap_downgrade` in `mac_policy_list`. Its documented 25G241 offsets (+0x20, +0x120, +0x200) match the kernel layout above.
  - Each wrapper calls AMFI first, then turns a refusal into success when the file's cdhash is on its compiled-in list of 18.
  - The counters match: 63 LV refusals + 63 mmap refusals = 126 overrides, and zero refusals of unlisted code.
  - Process flags keep `REQUIRE_LV`, so the bypass works per file at check time and does not disable LV for the process.
- [I] AMFIPass does not admit the plugin, for two reasons. The Vermilion README states that AMFIPass "only trusts code signed with Dortania's key". And AMFI's own rejections still appear with AMFIPass loaded. In nullarc's setup, AMFIPass keeps apps that check AMFI working while `amfi=0x80` relaxes AMFI (nullarc @ 3497d87, `hardware/REQUIRED_KEXTS.md` line 17). Its binary is injected from the ESP, which is out of bounds, so it was not inspected (K5, behaviour level only).
- [V, docs] nullarc @ 3497d87, `docs/INSTALL.md` lines 24 and 30–31: boot-args `amfi=0x80 amfi_get_out_of_my_way=0x1 -amfipassbeta phxdebug=1`. The same file says FairPlay stops working, which RB-0004d measures. [V code, §2.1] Mechanically, `amfi=0x80` makes AMFI mark every signature as platform, if `csr_check(0x8)` passes.
- [V] A third relaxation exists in amfid (§2.1): the `DisableLibraryValidation` preference, honoured only with `CSR_ALLOW_APPLE_INTERNAL`. It needs no third-party kernel code.
- [V, docs] nvidia-macos-driver @ 45040e9:
  - `README.md` lines 37, 51 and 100: the plugin lives at `/Library/GPUBundles/NVMTLDriver.bundle`, and the AMFI boot-args "let WindowServer load the driver bundle".
  - `docs/SAFARI-WEBGL.md` lines 5–11: Safari's sandbox blocked `mmap()` of the plugin under `/Library/GPUBundles`. This matches the WebKit GPU profile [V, Q2].
  - Also `docs/MAC-PARITY.md` lines 68–69 and `SECURITY.md` line 21.
- [V] The plugin's placement is explained. Its real path under `/System/Library/CoreServices/CoreTypes.bundle/…` is map-executable for both WindowServer (`com.apple.WindowServer.sb` line 31) and the WebKit GPU process (`com.apple.WebKit.GPUProcess.sb` line 210). nullarc @ 3497d87, `README.md` lines 65 and 73, describes the same placement. It requires a broken seal.

## Q6. No-Metal behaviour

- [V] Static path in SkyLight (LC_UUID 038F2E24):
  1. At WindowServer start, `WSWaitForIOKitReady` (once; block @ 0x7ff8092de148) waits for `IOKitWaitQuiet`, with 60 s and then 240 s timeouts.
  2. `WSSystemCanCompositeWithMetal` (once; block @ 0x7ff8094511df; statics `…E4once`, `…E11metal_lovin`) returns true if any device from `MTLCopyAllDevices` has `isHeadless == NO`.
  3. If true, WindowServer calls `activate_compositor_metal(false)` (@ 0x7ff8093a4f7b). Otherwise it calls `activate_compositor_sw(false)` (@ 0x7ff8093a501e), which logs `Software compositor activated.`

  The decision is made once per WindowServer launch.
- [V] Limits of the software path, as strings:
  - SkyLight: `The software renderer does not support 10-bit or YUV DisplayStream output.`
  - QuartzCore: `%d by %d image is too large for software renderer`
- [V] Observation: on 2026-11-20, `WindowServer[200]` logged `Software compositor activated.` at 19:19:19.279. The system has been on 25G241 since 2026-11-18 (`/var/log/install.log`, sanitized). This line appears only once in the retained log archive. Query: `/usr/bin/log show --style compact --predicate 'process == "WindowServer" AND eventMessage CONTAINS "Software compositor activated"'`.
- [V] The session came up and ran:
  - loginwindow and WallpaperAgent worked, and NotificationCenter rendered widgets (Calendar, Weather, Photos).
  - The WebKit GPU process checked in at 19:19:38.
  - The user logged out at 19:51:13.
  - No crash report on disk has an mtime between 19:19 and 19:55 (`find ~/Library/Logs/DiagnosticReports /Library/Logs/DiagnosticReports -newermt …`). The next report is an unrelated `siriinferenced` at 20:02.
- [I] 25G241 reaches a usable desktop with no Metal device. **A display-only M1 build is bootable.**
- Not established:
  - Whether that boot had an accelerator at all. The kernel log for it is no longer retained.
  - Which apps refuse to run or degrade without Metal.
  - How the poster and wallpaper extensions behave.
  - Whether HDR, 10-bit or high-resolution modes are refused.

  The first M1.0 display-only candidate answers these directly (TESTPLAN T-0002).

## Q7. Poster-extension crash: the first dGPU parity regression test

- [V] There are 46 reports `~/Library/Logs/DiagnosticReports/DynamicBackgroundPosterExtension-*.ips`, all on macOS 26.7.1 (25G241): 45 on 2026-11-26 and 1 on 2026-11-27. Command: `python3 -I tools/re/ips_summary.py ~/Library/Logs/DiagnosticReports/DynamicBackgroundPosterExtension-*.ips`.
  - Exception: `EXC_CRASH` / `SIGABRT` ("Abort trap: 6"), on queue `com.apple.transcriptBackgroundPoster.loadingQueue`.
  - Binary: `/System/Library/ExtensionKit/Extensions/DynamicBackgroundPosterExtension.appex` (platform, app-sandbox, CodeDirectory flags none, so no LV and the plugin loads).
- [V] The crashed thread is the same in all 46, innermost first:
  1. `abort` +126
  2. `Metal -[MTLIOAccelDevice newIndirectArgumentEncoderWithLayout:]` +9
  3. `Metal -[_MTLDevice newArgumentEncoderWithBufferBinding:]` +106
  4. VFX (iOSSupport, stripped), 9 frames
- [V] `-[MTLIOAccelDevice newIndirectArgumentEncoderWithLayout:]` @ 0x7ff80f66d4ec is `push rbp; mov rbp,rsp; call` Metal's `abort` stub (0x7ff80f676562, in `__stubs`). `-[MTLIOAccelDevice newArgumentEncoderWithLayout:]` @ 0x7ff80f596a9a tail-calls it, which is why the abort frame sits directly under `newArgumentEncoderWithBufferBinding:`.
- [V] It is the **only** method body of the abort or `ud2` shapes across `MTLIOAccelDevice` (93 methods), `_MTLDevice` (720), `MTLIOAccelCommandQueue`, `MTLIOAccelCommandBuffer`, `MTLIOAccelResource`, `MTLIOAccelTexture` and `MTLIOAccelBuffer` (`tools/re/abort_stubs.py` and a `ud2` scan on Metal 1EFC99EB). Other failure shapes, such as nil returns, were not scanned.
- [V] Apple's AMD driver overrides the method: `-[GFXAAMD_MtlDevice newArgumentEncoderWithLayout:]` @ 0x7ffb110f4f78, plus `-newArgumentEncoderWithBufferBinding:` @ 0x7ffb110f4dd5 (AMDRadeonX6000MTLDriver, BBB186ED). It does not override `newIndirectArgumentEncoderWithLayout:`. The live plugin's `NVMTLDevice` has 148 method symbols, including `newArgumentEncoderWithArguments:`, but neither layout method (`nm -m` on the plugin).
- [I] Root cause: a device class that does not override `newArgumentEncoderWithLayout:`. VFX (the poster renderer) calls `newArgumentEncoderWithBufferBinding:`, which reaches the base-class abort stub. This is a driver API gap, not an AMFI or loading problem.
- [V] MercuryPosterExtension: 32 reports, all from 2026-11-23.
  - Exception: `EXC_ARITHMETIC` / `SIGFPE` in `MTLSimDriver -[MTLSimBlitCommandEncoder copyFromBuffer:…toTexture:…]` +1921, via `MetalSerializer`.
  - The binary ran from a mounted simulator runtime volume, under launchd_sim, SimulatorTrampoline and dyld_sim.
  - These are **iOS Simulator** processes and have nothing to do with the dGPU. No simulator runtime is installed now.
  - The control-plane STATE lists them as a dGPU crash and should be corrected.
- Regression test: TESTPLAN **T-0001**.

## Recommendation for ADR-0004

| Option | Status | Why |
|---|---|---|
| A: third-party bundle + AMFI relaxation | **Survives, research/alpha only** | Three mechanisms exist, all relaxations (list below). Independently of AMFI, the WebKit GPU process can map executable code only from system-volume paths, so a third-party driver that serves Safari also needs a broken seal. A can never be stable (accepted bar). |
| B: reuse Apple's AMD bundles | **Survives, pending RB-0004c** | Platform code in the shared cache, which passes every gate including the WebKit GPU sandbox. `AMDRadeonX6000_AMDGraphicsAccelerator : IOGraphicsAccelerator2` shows the kernel interface those bundles expect. Feasibility (ASIC assumptions) is RB-0004c. |
| C: paravirt guest stack | **Survives, pending RB-0004b** | On x86 the guest side is the IOAcceleratorFamily2-based `AppleParavirtGPU` (PCI `0xEEEE106B`, `MetalPluginName = AppleParavirtGPUMetal`), Apple-signed and passing every gate. The IOGPUFamily paravirt variants are arm64e-only and irrelevant here. Bare-metal checks and the protocol are RB-0004b. |
| D: Developer ID bundle for non-platform apps only | **Dead for parity** | All six LV platform clients would reject it (rule 8). The resolver looks only in two SIP-protected directories, and staging admits only Apple or NVIDIA. The WebKit GPU process cannot map from `/Library/GPUBundles`. WindowServer would composite in software (Q6). |
| E: DriverKit | **No path** | The DriverKit 25.5 SDK families are Audio, BlockStorage, HID, MIDI, Networking, PCI, SCSIController, SCSIPeripherals, Serial, USB, USBSerial and Video (`xcrun --sdk driverkit --show-sdk-path`). There is no GPU or IOAccelerator family. |
| IOGPU generic device | **Not a path on its own** | `IOGPU : IOAccelerator` on x86, so Metal would enumerate it, but no Apple x86 driver class or compiler builds on `IOGPUMetalDevice`. |

The three option-A mechanisms:
- **A1, VermilionTrust (today):** a per-cdhash override of AMFI's hooks. Works with csr 0x0A03.
- **A2, `amfi=0x80` / `amfi_get_out_of_my_way`:** every signature counts as platform. Needs `CSR_ALLOW_KERNEL_DEBUGGER`.
- **A3, amfid `DisableLibraryValidation`:** every LV failure is allowed. Needs `CSR_ALLOW_APPLE_INTERNAL`. A3 needs no third-party kernel code, but its system-wide side effects are not assessed.

So the surviving AMFI-intact paths are **B and C only**. RB-0004b and RB-0004c decide between them by reverse engineering. RB-0004a needs no boot to separate them.

**One-shot boot experiment (B-manual, one owner-assisted boot)**, to confirm the AMFI-intact baseline. It also serves RB-0004d:
- **X1: "AMFI intact, legacy plugin present."**
  - Config: the USB known-good EFI with `Kernel → Add → VermilionTrust.kext → Enabled = false` and `Kernel → Add → AMFIPass.kext → Enabled = false`. Everything else stays the same: boot-args unchanged (no `amfi=…`), SIP 0x0A03 unchanged, Lilu, RestrictEvents and all other kexts unchanged. No live-system change.
  - Expected [I]:
    - AMFI rejects the plugin in the six LV processes with no override, and `debug.phxtrust_stat` is absent.
    - WindowServer has no Metal device and logs `Software compositor activated.` (the legacy daemon still restarts it once).
    - Non-LV clients (NotificationCenter, VTDecoderXPCService, the poster extension) still load the plugin, so T-0001 may still fire.
  - Observe, read-only after login:
    - The AMFI log (`/usr/bin/log show --last boot --predicate 'eventMessage CONTAINS "Library Validation"'`).
    - The compositor line of each WindowServer instance.
    - Which pids log the plugin's `+load`.
    - New `.ips` reports since boot.
    - `tools/re/csprobe` flags.
    - Whether the owner sees a desktop.
    - The RB-0004d FairPlay checklist.
- No separate framebuffer-only boot: the first M1.0 display-only candidate covers T-0002.

**Linux captures needed for RB-0004a:** none. The loading chain and AMFI are macOS-only questions. The bridge captures (EDID, DCN, firmware, idle power) feed M1.0, M1.5 and ADR-0005, not this brief.

## What is left open

- **Safari's main process.** Which sandbox rule lets it map the plugin from `CoreTypes.bundle` was not identified; its profile is not under `/System/Library/Sandbox/Profiles`. Low priority: the WebKit GPU process, which does Safari's GPU work, is explained.
- **Sandbox trust decision.** How Sandbox.kext's `rootless_check_trusted_class` decides under csr 0x0A03, and how it treats symlinks, was not traced. It is not decision-relevant (§1.2).
- **Platform hardening switch.** Which setting enables or masks `platformHardenFlags` for platform binaries on this boot was not traced (§2.1).
- **AMFIPass internals.** The binary lives on the ESP, which is out of bounds. The behaviour is recorded (Q5).
- **OpenCL GPU path.** Not traced (§1.3).
