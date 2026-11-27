# RB-0004a: Metal driver loading chain and library validation on 25G241

Status: **work in progress, checkpoint of 2026-11-27.** The user-space half is done. The kernel half (AMFI, Sandbox, IOAcceleratorFamily2/IOGPUFamily) was waiting for the KDK. KDK 25G241 is now installed, so the kernel half is the next step (list in [Kernel half](#kernel-half-pending-kdk-installed)). The reviewer subagent has not yet checked the citations.

Brief: control plane `docs/Research/briefs/RB-0004a-metal-driver-loading-chain.md`. Issue: ownback/Ryzentosh-dGPU#1. ADR: control plane `.agents/decisions/ADR-0004-user-space-driver-delivery.md`.

## Conventions

- **[V] verified**: seen directly, either in a 25G241 binary (symbol, import, string, offset) or on the live system (the command is given).
- **[I] inferred**: follows from verified facts but was not observed directly. The reasoning is given.
- **[K]**: needs the kernel binaries (KDK). Listed at the end.
- Binary citations give the image, its LC_UUID and the unslid shared-cache VM address. The addresses come from `nm -m` on images extracted with `tools/re/dscx`. `+N` is a byte offset from a symbol, taken from crash-report frames.
- Study-only sources (Vermilion, nullarc, nvidia-macos-driver) are cited as repo + commit + path, as facts only. No code was copied.
- Observations are read-only and sanitized: the home directory is `~`, and host names, volume names, third-party team IDs, serials and Mac UUIDs are left out.
- Only names, offsets and behaviour are recorded. There are no decompiled listings (licensing.md §7).

### Binaries (macOS 26.7.1, build 25G241, x86_64)

Shared cache: `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h` (+ `.01`–`.06`), cache UUID `31374756-89B4-34E8-A34F-56C5D57216A1`.

| Image (in the shared cache unless noted) | LC_UUID |
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
| `/System/Library/KernelCollections/BootKernelExtensions.kc` (file) | sha256 `21d6da1c4c3e7b72dddf5144da8a4c4b48e294249a16018a5006b61bb2155ccc` |

Extraction note: Apple's `dsc_extractor.bundle` refuses the live cache. Page 67726 of the main file (VM 0x7ff81088e000, `AppleSystemInfo.framework` text offset 0x4000) no longer matches its CodeDirectory slot. That page is the only mismatch in all seven cache files (`tools/re/dsc_cs_check.py`). The file's ctime has not changed since installation. [I] A Lilu user-space patcher (RestrictEvents) patches that page in memory, and the change is visible through the unified buffer cache. The extraction therefore used a scratch copy of the main file with that one slot recomputed. All other code pages are byte-identical to the signed cache.

## Answers in brief

1. **Discovery.** Metal matches `IOAccelerator` services only and reads `MetalPluginName`. It resolves that name with `gpu_bundle_find_trusted`, which searches `/Library/GPUBundles` first and then `/System/Library/Extensions`. Metal then loads the bundle with NSBundle and instantiates `MetalPluginClassName`, falling back to the principal class. The class must subclass `_MTLDevice`. If any step fails, Metal skips the service without a word. There is no software Metal device on x86. GL, CL, the video decoders, MTLCompiler and Apple's own AMD and Intel bundles all use the same trusted-path helper.
2. **Signature gates.** There are three gates:
   - **Path trust:** the SIP storage class `KernelExtensionManagement`, or the path is in the shared cache.
   - **Sandbox:** the `file-map-executable` rules.
   - **AMFI library validation at mmap:** applies to processes that carry `CS_REQUIRE_LV`.

   WindowServer, Safari, Finder, SystemUIServer, Messages and the WebKit GPU process are platform binaries with `REQUIRE_LV`. For them AMFI accepts **only platform code** ("mapping process is a platform binary, but mapped file is not"). Staging a bundle into `/Library/GPUBundles` (kext_tools `GPUCompanionBundles`) accepts only Apple-anchored or NVIDIA Developer ID bundles.
3. **Process inventory.** 22 distinct process names own user clients on the accelerator, and Dock maps the plugin without one. Six of these processes enforce LV. Between them they logged 126 rejections this boot, and VermilionTrust overrode all 126. The rest are platform binaries without `REQUIRE_LV` and map the plugin with no check at all.
4. **Seams.** No Apple seam lets third-party code serve Metal to platform clients while AMFI stays intact. MTLCompilerService is platform, hardened and limited to trusted paths. VTDecoderXPCService is the only platform host with `disable-library-validation`, and it is a video-decode host. The only Apple-signed generic Metal front ends are IOGPU's `IOGPUMetalDevice` and the paravirt guest bundles (RB-0004b/c).
5. **AMFIPass and VermilionTrust.** The current boot has no `amfi=` boot-args. AMFI rejects the plugin every time. VermilionTrust wraps AMFI's LV and mmap hooks and turns refusals into success for 18 listed cdhashes. AMFIPass 1.4.1 is loaded but is not what admits the plugin.
6. **No-Metal behaviour.** SkyLight decides once per WindowServer launch, after IOKit quiesces. If there is no non-headless Metal device, it activates the software compositor. A 25G241 boot on 2026-11-20 did exactly that and ran a normal desktop session for 30+ minutes. A display-only M1 build is bootable. Which apps degrade without Metal is not catalogued yet.
7. **Poster crash.** DynamicBackgroundPosterExtension aborts in the base class's abort stub `-[MTLIOAccelDevice newIndirectArgumentEncoderWithLayout:]`. The plugin's device class does not override `newArgumentEncoderWithLayout:`, and Apple's AMD driver does. This is a driver API gap, not a loading problem. It is recorded as TESTPLAN T-0001. The MercuryPosterExtension reports are iOS Simulator crashes and have nothing to do with the dGPU.

---

## Q1. Discovery: from IORegistry service to loaded bundle

### 1.1 Metal.framework (Metal, LC_UUID 1EFC99EB)

- [V] `-[MTLIOAccelServiceGlobalContext init]` @ 0x7ff80f641be6:
  - Creates the IOKit main port and a notification port on the dispatch queue `com.Metal.DeviceDispatch`.
  - Registers `IOServiceAddMatchingNotification("IOServicePublish", IOServiceMatching("IOAccelerator"), __mtlIOAccelDeviceMatched)`. The callback `__mtlIOAccelDeviceMatched` is @ 0x7ff80f641ae0.
  - Walks the services that are already published.
  - The only matching dictionary on this path is the class name `IOAccelerator`. Whether IOGPU-family services are `IOAccelerator` subclasses on x86 is a kernel question [K4].
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
- [V] The name is not sanitized. The live service publishes `MetalPluginName = "../../../Library/GPUBundles/NVMTLDriver"` (§1.4), and it resolves. [I] Because `/Library/GPUBundles` is searched first, a plain name would already reach that directory. The `../` form also resolves from the `/System/Library/Extensions` candidate.
- [V] `gpu_bundle_is_path_trusted` @ 0x7ff81088343b trusts a path when either of these holds:
  - `rootless_check_trusted_class(path, "KernelExtensionManagement")` succeeds (@ 0x7ff810883429), or
  - `_dyld_shared_cache_contains_path(path)` is true.
- [V] `/Library/GPUBundles` belongs to that storage class: `/System/Library/Sandbox/rootless.conf` line 7, and `ls -ldO /Library/GPUBundles` shows `restricted` with xattr `com.apple.rootless: KernelExtensionManagement`.
- [K3] Two decisions belong to Sandbox.kext: what `rootless_check_trusted_class` returns under csr 0x0A03 (which includes `CSR_ALLOW_UNRESTRICTED_FS`), and how it treats a symlink that leaves the protected directory.

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

- [I] Every Apple GPU component in user space (Metal, GL, CL, video decode, the shader compiler, and Apple's own driver bundles) resolves driver code through the same two directories and the same SIP trust test. A user-space GPU driver can live in only two places: `/Library/GPUBundles` and `/System/Library/Extensions`.
- [I] OpenCL's CPU engine is `libcldcpuengine`. Its GPU path probably goes through the GL bundle. Not traced.

### 1.4 The live registry (the probe)

- [V] `ioreg -l -w0 -r -c IOAccelerator`, sanitized:
  - `IOClass = "NMXAccel"` from `org.vermilion.accel` 0.1.1 (Aux KC fileset entry, `/Library/Extensions/VermilionAccel.kext`), on `IOPCIDevice`.
  - `MetalPluginName = "../../../Library/GPUBundles/NVMTLDriver"` and `MetalPluginClassName = "NVMTLDevice"`.
  - `IOGLBundleName = "AppleMetalOpenGLRenderer"` and `IOCFPlugInTypes = {ACCF0000-…="IOAccelerator2D.plugin"}`.
- [V] `ioreg -l -w0 -r -c IOGPU` returns nothing: no IOGPU-class service exists.
- [V] `ls -la /Library/GPUBundles`:
  - `NVMTLDriver.bundle` is a symlink to `/System/Library/CoreServices/CoreTypes.bundle/Contents/Library/PhxGPU/NVMTLDriver.bundle`.
  - The directory also holds `nvmtl-allow.txt`.
  - `codesign -dvvv` shows the bundle is ad-hoc signed, bundle id `com.nullmoth.NVMTLDriver`.

## Q2. Signature gates per step

| Step | Gate | Enforced by | Evidence |
|---|---|---|---|
| Resolve the name | The path must lie under `/Library/GPUBundles` or `/System/Library/Extensions` and be SIP-trusted (`KernelExtensionManagement`) or in the shared cache | libsystem_sandbox, then Sandbox.kext | [V] §1.2; kernel decision [K3] |
| Stage into `/Library/GPUBundles` | kext_tools copies a kext's `GPUCompanionBundles` / `GPUOptionalCompanionBundles` there only if the bundle satisfies `anchor apple or (Developer ID CA … and leaf subject.OU = NVIDIA's team ID)` | kernelmanagerd / kext_tools staging | [V] Apple OSS kext_tools-779 @ 3343f4b7, `staging.m` lines 21–35 (`GPU_BUNDLE_STAGING_REQUIREMENT`, `SECURE_GRAPHICS_BUNDLE_STAGING_PATH`), `gpuBundleValidates` (`SecStaticCodeCheckValidity` with `kSecCSStrictValidate`). `pathIsSecure()` treats every path as secure when `csr_check(CSR_ALLOW_UNTRUSTED_KEXTS) == 0`. |
| Read the bundle | Sandbox `file-read*`: `/Library/GPUBundles` is readable to every process that uses `system.sb` | Sandbox | [V] `/System/Library/Sandbox/Profiles/system.sb` lines 256–259 |
| Map executable pages | Sandbox `file-map-executable` | Sandbox | [V] `system.sb` lines 43–56 allow only `/System/Library/Extensions`, `/System/Library/{Frameworks,PrivateFrameworks,SubFrameworks}`, `iOSSupport` and `/usr/lib`. `com.apple.WindowServer.sb` lines 29–35 add `/System/Library/CoreServices`, `/System/Library/Extensions` and `/Library/GPUBundles`. `com.apple.mtlcompilerservice.sb` lines 63–70 allow `/Library/GPUBundles` only on apple-internal systems. |
| Map executable pages | AMFI library validation (`file_check_mmap`, `file_check_library_validation`) for processes with `CS_REQUIRE_LV` | AMFI | [V] strings below, plus the live log in Q5. Exact decision logic [K1]. |
| Signature of the mapped file | Code-signing enforcement and trust caches | AMFI, kernel | [V] `sysctl security.mac.amfi`: `exec_requires_trustcache: 0`, `allow_only_platform_code: 0`, `launch_constraints_enforced: 0`, `developer_mode_status: 1`, `qa_root_certs_allowed: 1`. The kernel log at boot reports no external trust caches. |
| SSV seal | The live system has `Sealed: Broken` and runs from a bless snapshot with Authenticated Root disabled (csr 0x0A03 = `ALLOW_UNTRUSTED_KEXTS`, `ALLOW_UNRESTRICTED_FS`, `ALLOW_UNAPPROVED_KEXTS`, `ALLOW_UNAUTHENTICATED_ROOT`) | APFS, iBoot/OpenCore | [V] `diskutil apfs list` (sanitized: `Sealed: Broken`, `Snapshot Sealed: Broken`), `csrutil authenticated-root status` (`disabled`), `nvram csr-active-config` (`%03%0a%00%00`). The plugin's real path is on the system volume, which is possible only because the seal is broken. |
| TCC | Not a gate | – | [I] Nothing on the Metal, IOKit or NSBundle path consults TCC |

### AMFI strings in the boot KC (file offsets, sha256 above)

[V] Library-validation outcomes and reasons:

| Offset | String |
|---|---|
| 0x1aaacc0 | `Library Validation failed: Rejecting '%s' (Team ID: %s, platform: %s) for process '%s(%d)' …, reason: %s` |
| 0x1aaac30 | `Library Validation overridden for '%s' … overridden failure: %s` |
| 0x1aaab90 | `Library Validation would have failed (but is disabled): …` |
| 0x1aaab50 | `Bypassing Library Validation for installed root: '%s'.` |
| 0x1a9def8 | `mapping process is a platform binary, but mapped file is not` |
| 0x1a9df35 | `mapping process and mapped file (non-platform) have different Team IDs` |
| 0x1a9dd67 | `mapped file has no Team ID and is not a platform binary (signed with custom identity or adhoc?)` |
| 0x1a9debc | `mapping process has no Team ID and is not a platform binary` |

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

- [V] A byte search of the whole boot KC finds neither the string `GPUBundles` nor NVIDIA's team ID. [I] AMFI has no visible path or team exception for staged GPU bundles. An exception keyed some other way (cdhash, trust cache) is not excluded [K1].
- [I] Rule set, as the reason strings imply:
  - A platform process with `REQUIRE_LV` may map platform code only.
  - A non-platform process may map code with the same Team ID.
  - `disable-library-validation` relaxes the check for its holder.
  - `clear-library-validation` lets a process drop LV for itself.
  - The precise order and the exceptions are [K1].

### Host processes and LV-relevant entitlements

[V] `codesign -d --entitlements - --xml <binary>` and `tools/re/csprobe <pid>` (csops `CS_OPS_STATUS`, validation category):

| Host | Platform | `REQUIRE_LV` (csops) | LV-relevant entitlements |
|---|---|---|---|
| WindowServer | yes | yes (0x26016a01), CodeDirectory flag `library-validation` | `com.apple.private.gpuwrangler`; no disable-LV |
| com.apple.WebKit.GPU | yes | yes (0x26016a01) | `com.apple.private.gpu-restricted`, `com.apple.developer.hardened-process`, `com.apple.security.cs.jit-write-allowlist` |
| Safari | yes | yes (0x26016a01) | `com.apple.security.app-sandbox` |
| Finder | yes | yes (0x26016a01) | none |
| SystemUIServer | yes | yes (0x26016b01) | not dumped |
| VTDecoderXPCService | yes | no (0 AMFI rejections while it maps the plugin, Q3) | **`com.apple.security.cs.disable-library-validation`**, `com.apple.developer.hardened-process` |
| MTLCompilerService | yes | not running at probe time | `com.apple.developer.hardened-process` |
| DynamicBackgroundPosterExtension | yes | not running at probe time; CodeDirectory flags none | `com.apple.security.app-sandbox` |
| NeptuneOneWallpaper | yes | no (0x26014a01) | `com.apple.security.app-sandbox` |
| Dock | yes | no | none |
| A Developer ID Electron app and its GPU helper | no (category developer-id; 0x22014201 / 0x22010001) | no | `disable-library-validation`, `allow-jit`, `allow-unsigned-executable-memory` |

- [V] None of the probed hosts carries `com.apple.private.security.clear-library-validation`.

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
| VTDecoderXPCService | 3 | yes | no (disable-LV) | 0 |
| avconferenced, NeptuneOneWallpaper, iconservicesagent, NotificationCenter, openAndSavePanelService, UserNotificationCenter, DockHelper, TextInputSwitcher, TextInputMenuAgent, SafeEjectGPUService, CursorUIViewService, com.apple.dock.extra, AccessibilityUIServer, ControlCenter, loginwindow | 2–3 each | yes | no (platform, `RUNTIME` without `REQUIRE_LV`) | 0 |
| Dock | 0 | yes | no | 0. The plugin declines to make a device in Dock (`-Dock` in `/Library/GPUBundles/nvmtl-allow.txt`). |
| A Developer ID Electron app and its GPU helper | 5 | yes | no | 0 |
| DynamicBackgroundPosterExtension | not running at probe time | crashes in the plugin's device (Q7) | not observed | – |
| MTLCompilerService | not running at probe time | – | – | – |
| MercuryPosterExtension | not a macOS process on this system (Q7) | – | – | – |

- [V] All 126 rejections carry the same reason: `mapping process is a platform binary, but mapped file is not`. The first is at 12:52:44.467, in WindowServer (first instance).
- [I] AMFI checks library validation only in processes with `CS_REQUIRE_LV`. Platform processes without it (most of the UI agents above) map the ad-hoc plugin with no AMFI check at all, even with VermilionTrust's hooks counted out. Confirm in the kernel [K1].
- [V, study-only facts] The legacy stack restarts WindowServer once, by design. `~/gpu/phxboot-navi31.sh` lines 4–5 and 19 (run by `/Library/LaunchDaemons/local.phxboot.plist`) arm the display and then do one `killall -9 WindowServer`, "so WindowServer enumerates Metal fresh". [I] This matches SkyLight deciding once per launch (Q6). A real Mac publishes its accelerator during kext matching, before IOKit goes quiet, so its first WindowServer already sees Metal. Parity requirement: the Ryzentosh accelerator must publish before IOKit quiesces, and no WindowServer restart is allowed.

## Q4. Out-of-process seams

| Seam | Who loads what | Can third-party code sit behind it with AMFI intact on the client? |
|---|---|---|
| MTLCompilerService (XPC) | Metal sends compile requests. The service dlopens the compiler plugin at a client-supplied `pluginPath`, accepts sandbox extension tokens, and resolves paths with `gpu_bundle_is_path_trusted`. Platform binary, `com.apple.developer.hardened-process`. | No [I]. Its sandbox maps from `/Library/GPUBundles` only on apple-internal systems [V]. It is platform, so the platform-only rule applies [K1 for whether it has `REQUIRE_LV`]. Either way the Metal device class must still load inside each client. |
| VTDecoderXPCService | Platform binary with `disable-library-validation` [V]. | [I] It can map non-platform code, but it hosts VideoToolbox decoders, not Metal devices for other clients. That makes it a real seam for a third-party video decoder (VideoToolbox scope, later brief). Whether disable-LV applies to platform processes is [K1]. |
| IOGPU generic device | `IOGPUMetalDevice` is an Apple-signed, generic Metal front end. On x86 it resolves `MetalPluginName` through the same resolver [V]. | Open. It could be the Apple-signed client half if a kernel service can present the IOGPU interface and Metal's `IOAccelerator` matching sees it [K4]. It does not compile shaders. A backend compiler would still be needed [I]. |
| ParavirtualizedGraphics guest | Apple-signed `AppleParavirtGPU*` bundles in `/System/Library/Extensions` (principal class `AppleParavirtDevice`). The kernel side is `AppleParavirtGPUIOGPUFamily` (in the KDK). | Yes for the client half: the bundles are platform code and pass every gate [I]. Bare-metal viability and the protocol belong to RB-0004b (option C). |
| kext_tools GPU companion staging | Copies a kext's companion bundles into `/Library/GPUBundles`. | No. Only Apple-anchored or NVIDIA Developer ID bundles are accepted [V]. |
| Kernel-side work | Any kext can drive the GPU in the kernel. | [I] It does not remove the need for a user-space `_MTLDevice` subclass in every Metal client. |

- [I] Conclusion: no Apple seam lets a third-party binary provide Metal to platform clients with AMFI intact. The candidates that keep AMFI intact are all Apple-signed client halves: Apple's AMD bundles (B), the paravirt guest bundles (C) and IOGPU's generic device (new; RB follow-up).

## Q5. What AMFIPass and VermilionTrust change

- [V] Current boot-args (`sysctl -n kern.bootargs`): `-v keepsyms=1 debug=0x100 pci=0x8000000 amtk_awdl_offchan=0 ipc_control_port_options=0 phxdebug=1`. There is no `amfi=…` and no `amfi_get_out_of_my_way`. csr-active-config is 0x0A03.
- [V] `kmutil showloaded --list-only`: `com.dhinakg.AMFIPass` 1.4.1, `org.vermilion.trust` 1.0.4 and Lilu are loaded.
- [V] AMFI itself still says no: 126 `Library Validation failed: Rejecting …` lines in six processes (Q3). There are no `overridden` or `would have failed (but is disabled)` lines.
- [V] The plugin runs anyway. Its `+load` log line from WindowServer (first instance) is at 12:52:44.469, 2 ms after the first rejection.
- [V] `sysctl debug.phxtrust_stat`: `state=installed mode=enforce list=18 libval_calls=71333 libval_denied=63 mmap_exec=71349 mmap_exec_denied=63 overrides=126 denied_unlisted=0`.
- [I] VermilionTrust (study-only: vermilion-xtx @ 40b4f411, `src/vermilion-trust/README.md`):
  - It replaces AMFI's `mpo_file_check_library_validation`, `mpo_file_check_mmap` and `mpo_file_check_mmap_downgrade` in `mac_policy_list`.
  - Each wrapper calls AMFI first, then turns a refusal into success when the file's cdhash is on its compiled-in list of 18.
  - The counters match: 63 LV refusals + 63 mmap refusals = 126 overrides, and zero refusals of unlisted code.
  - Process flags keep `REQUIRE_LV` (csprobe), so the bypass works per file at check time and does not disable LV for the process.
  - The README gives the 25G241 vector offsets as `mpc_ops` +0x20, mmap +0x120, LV +0x200 [K2 to confirm].
- [I] AMFIPass does not admit the plugin, for two reasons. The Vermilion README states that AMFIPass "only trusts code signed with Dortania's key". And AMFI's own rejections still appear, which would not happen if AMFIPass made AMFI accept the plugin. In nullarc's setup, AMFIPass keeps apps that check AMFI working while `amfi=0x80` relaxes AMFI (nullarc @ 3497d87, `hardware/REQUIRED_KEXTS.md` line 17). Its mechanism is [K5].
- [V, docs] nullarc @ 3497d87, `docs/INSTALL.md` lines 24 and 30–31: boot-args `amfi=0x80 amfi_get_out_of_my_way=0x1 -amfipassbeta phxdebug=1`. The same file says FairPlay stops working. That claim is measured by RB-0004d.
- [V, docs] nvidia-macos-driver @ 45040e9:
  - `README.md` lines 37, 51 and 100: the plugin lives at `/Library/GPUBundles/NVMTLDriver.bundle`, and the AMFI boot-args "let WindowServer load the driver bundle".
  - `docs/SAFARI-WEBGL.md` lines 5–11: Safari's sandbox blocked `mmap()` of the plugin under `/Library/GPUBundles`. This matches the `system.sb` map-executable rules [V].
  - Also `docs/MAC-PARITY.md` lines 68–69 and `SECURITY.md` line 21.
- Open point [K3]: Safari and the WebKit GPU process map the plugin from its real path under `/System/Library/CoreServices/CoreTypes.bundle/…`, even though `system.sb` does not list that path for map-executable. The rule that admits it (WebKit's own GPU-process profile, or Sandbox.kext path handling) is not identified yet. nullarc @ 3497d87, `README.md` lines 65 and 73, describes this placement (bundle in `CoreTypes.bundle/Contents/Library/PhxGPU`, linked from `/Library/GPUBundles`).

## Q6. No-Metal behaviour

- [V] Static path in SkyLight (LC_UUID 038F2E24):
  1. At WindowServer start, `WSWaitForIOKitReady` (once; block @ 0x7ff8092de148) waits for `IOKitWaitQuiet`, with 60 s and then 240 s timeouts.
  2. `WSSystemCanCompositeWithMetal` (once; block @ 0x7ff8094511df; statics `…E4once`, `…E11metal_lovin`) returns true if any device from `MTLCopyAllDevices` has `isHeadless == NO`.
  3. If true, WindowServer calls `activate_compositor_metal(false)` (@ 0x7ff8093a4f7b). Otherwise it calls `activate_compositor_sw(false)` (@ 0x7ff8093a501e), which logs `Software compositor activated.`

  The decision is made once per WindowServer launch.
- [V] Limits of the software path, as strings:
  - SkyLight: `The software renderer does not support 10-bit or YUV DisplayStream output.`
  - QuartzCore: `%d by %d image is too large for software renderer`
- [V] Observation: on 2026-11-20, `WindowServer[200]` logged `Software compositor activated.` at 19:19:19.279. The system has been on 25G241 since 2026-11-18 (`/var/log/install.log`, sanitized). This line appears only once in the whole retained log archive. Query: `/usr/bin/log show --style compact --predicate 'process == "WindowServer" AND eventMessage CONTAINS "Software compositor activated"'`.
- [V] The session came up and ran:
  - loginwindow and WallpaperAgent worked, and NotificationCenter rendered widgets (Calendar, Weather, Photos).
  - The WebKit GPU process checked in at 19:19:38.
  - The user logged out at 19:51:13.
  - No crash report on disk has an mtime between 19:19 and 19:55 (`find ~/Library/Logs/DiagnosticReports /Library/Logs/DiagnosticReports -newermt …`). The next report is an unrelated `siriinferenced` at 20:02.
- [I] 25G241 reaches a usable desktop with no Metal device. **A display-only M1 build is bootable.**
- Not established:
  - Whether that boot had an accelerator at all. The kernel log for it is no longer retained.
  - Which apps refuse to run or degrade without Metal (anything that treats a nil `MTLCreateSystemDefaultDevice` as fatal).
  - How the poster and wallpaper extensions behave. No crash was seen in that window.
  - Whether HDR, 10-bit or high-resolution modes are refused. The strings above suggest some are.

  The first M1.0 display-only candidate answers these directly (TESTPLAN T-0002), so no separate boot is needed.

## Q7. Poster-extension crash: the first dGPU parity regression test

- [V] There are 46 reports `~/Library/Logs/DiagnosticReports/DynamicBackgroundPosterExtension-*.ips`, all on macOS 26.7.1 (25G241): 45 on 2026-11-26 and 1 on 2026-11-27. Command: `python3 -I tools/re/ips_summary.py ~/Library/Logs/DiagnosticReports/DynamicBackgroundPosterExtension-*.ips`.
  - Exception: `EXC_CRASH` / `SIGABRT` ("Abort trap: 6"), on queue `com.apple.transcriptBackgroundPoster.loadingQueue`.
  - Binary: `/System/Library/ExtensionKit/Extensions/DynamicBackgroundPosterExtension.appex` (platform, app-sandbox).
- [V] The crashed thread is the same in all 46, innermost first:
  1. `abort` +126
  2. `Metal -[MTLIOAccelDevice newIndirectArgumentEncoderWithLayout:]` +9
  3. `Metal -[_MTLDevice newArgumentEncoderWithBufferBinding:]` +106
  4. VFX (iOSSupport, stripped), 9 frames
- [V] `-[MTLIOAccelDevice newIndirectArgumentEncoderWithLayout:]` @ 0x7ff80f66d4ec is an abort stub (`push rbp; mov rbp,rsp; call abort`, found with `tools/re/abort_stubs.py`). `-[MTLIOAccelDevice newArgumentEncoderWithLayout:]` @ 0x7ff80f596a9a tail-calls it, which is why the abort frame sits directly under `newArgumentEncoderWithBufferBinding:`.
- [V] Apple's AMD driver overrides the method: `-[GFXAAMD_MtlDevice newArgumentEncoderWithLayout:]` @ 0x7ffb110f4f78 (AMDRadeonX6000MTLDriver, BBB186ED). The live plugin's `NVMTLDevice` has 148 method symbols, including `newArgumentEncoderWithArguments:`, but neither layout method (`nm -m` on the plugin).
- [I] Root cause: a device class that does not override `newArgumentEncoderWithLayout:`. VFX (the poster renderer) calls `newArgumentEncoderWithBufferBinding:`, which reaches the base-class abort stub. This is a driver API gap, not an AMFI or loading problem. A Ryzentosh device class must override every `MTLIOAccelDevice` method that is an abort stub. The full list is still to be extracted with `tools/re/abort_stubs.py` (next step).
- [V] MercuryPosterExtension: 32 reports, all from 2026-11-23.
  - Exception: `EXC_ARITHMETIC` / `SIGFPE` in `MTLSimDriver -[MTLSimBlitCommandEncoder copyFromBuffer:…toTexture:…]` +1921, via `MetalSerializer`.
  - The binary ran from a mounted simulator runtime volume, under launchd_sim, SimulatorTrampoline and dyld_sim.
  - These are **iOS Simulator** processes and have nothing to do with the dGPU. No simulator runtime is installed now.
  - The control-plane STATE lists them as a dGPU crash and should be corrected.
- Regression test: TESTPLAN **T-0001**.

## Recommendation (draft; final after the kernel half)

| ADR-0004 option | Status after RB-0004a | Why |
|---|---|---|
| A: third-party bundle + AMFI relaxation | **Survives, research/alpha only** | Works today. The relaxation in use is VermilionTrust's per-cdhash override of AMFI's LV and mmap hooks, not `amfi=0x80`. It can never ship as stable (accepted bar). |
| B: reuse Apple's AMD bundles | **Survives, pending RB-0004c** | The bundles are platform code in the shared cache and pass every gate. Feasibility depends on the bundles' ASIC assumptions (RB-0004c). |
| C: paravirt guest stack | **Survives, pending RB-0004b** | The guest bundles are Apple-signed and pass every gate. Bare-metal checks and the protocol are RB-0004b. |
| D: Developer ID bundle for non-platform apps only | **Survives only as a degraded mode, not parity** | The resolver only looks in two SIP-protected directories, and kext_tools stages only Apple or NVIDIA bundles there. Every LV-enforcing platform client (WindowServer, Safari, Finder, SystemUIServer, Messages, WebKit GPU) would lose Metal, and WindowServer would composite in software (Q6). |
| E: DriverKit | **No path today** | No GPU or IOAccelerator DriverKit family exists [I; check the 25G241 DriverKit SDK in the kernel half]. |
| New: IOGPU's generic `IOGPUMetalDevice` | **Investigate** | An Apple-signed generic client half that resolves through the same path [V]. Whether x86 can present an IOGPU service that Metal enumerates is [K4]. |

One-shot boot experiment (B-manual, one owner-assisted boot). The draft is to be finalised after the kernel half:

- **X1: "AMFI intact, legacy plugin present"** decides D and shows what 25G241 does when WindowServer cannot load the GPU plugin while other clients can.
  - Config: USB known-good EFI with `Kernel → Add → VermilionTrust.kext → Enabled = false` and `Kernel → Add → AMFIPass.kext → Enabled = false`. Everything else stays the same: boot-args unchanged (no `amfi=…`), SIP 0x0A03 unchanged, other kexts unchanged.
  - Observe, read-only after login:
    - The AMFI `Library Validation failed` lines, with `debug.phxtrust_stat` absent.
    - The compositor message of each WindowServer instance.
    - Which pids log the plugin's `+load`.
    - New crash reports since boot.
    - csprobe flags.
    - Whether the owner sees a desktop.
  - The RB-0004d FairPlay checklist can be batched into the same boot.
- No separate framebuffer-only boot: the first M1.0 display-only candidate covers the open Q6 items (T-0002).

## Kernel half (pending, KDK installed)

KDK: `/Library/Developer/KDKs/KDK_26.7.1_25G241.kdk`, with `kernel`, `kernel.development` and `kernel.kasan`, dSYMs, and the GPU kexts.

- **K1. AMFI library validation.** Work out:
  - The decision order behind `failed`, `overridden`, `would have failed (but is disabled)` and `Bypassing … installed root`.
  - Whether `CS_REQUIRE_LV` is the only trigger.
  - Whether `disable-library-validation` applies to platform processes (VTDecoderXPCService).
  - Any exception for GPU bundles: trust cache, cdhash or path.
- **K2.** AMFI's `mac_policy_ops` layout on 25G241. Confirm VermilionTrust's +0x120 / +0x200 slots.
- **K3. Sandbox.kext.**
  - `rootless_check_trusted_class` under csr 0x0A03 and with symlinks.
  - How `file-map-executable` is evaluated for the plugin's real path in Safari and the WebKit GPU process.
- **K4. IOAcceleratorFamily2 / IOGPUFamily.**
  - Class hierarchy: does an IOGPU service match `IOServiceMatching("IOAccelerator")` on x86?
  - Entitlement checks at user-client creation (`com.apple.private.gpuwrangler`, `com.apple.private.gpu-restricted`).
- **K5.** AMFIPass mechanism (third-party kext, facts only).
- Out of scope here, noted for RB-0004b: `AppleParavirtGPUIOGPUFamily` is in the KDK.
