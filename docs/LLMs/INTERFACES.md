# INTERFACES: Ryzentosh-dGPU

External contracts: IOKit classes and properties, user-client selectors, plist keys, files installed, interfaces consumed from other Ryzentosh repos.

## Metal plugin contract (consumed by Metal.framework, 25G241)

Source: [re/RB-0004a-metal-loading-chain.md](re/RB-0004a-metal-loading-chain.md) Q1 and Q7. These are facts about Apple's code, not our design yet.

### Properties on the accelerator service

Metal finds the service through `IOServiceMatching("IOAccelerator")` plus `IOServicePublish` notifications. The service must therefore be an `IOAccelerator` subclass. On x86 both kernel families qualify: `IOGraphicsAccelerator2` (IOAcceleratorFamily2, which Apple's AMD and paravirt drivers use) and `IOGPU` (IOGPUFamily) both derive from `IOAccelerator` (RB-0004a §1.5).

| Key | Type | Consumer | Meaning |
|---|---|---|---|
| `MetalPluginName` | string | Metal, IOGPU | Bundle name without `.bundle`. `gpu_bundle_find_trusted` looks it up in `/Library/GPUBundles`, then `/System/Library/Extensions`, and the path must be SIP-trusted (`KernelExtensionManagement`) or in the shared cache. |
| `MetalPluginClassName` | string, optional | Metal, IOGPU | Class to instantiate. If missing or not found, Metal uses the bundle's principal class. |
| `IOGLBundleName` | string | OpenGL (libGFXShared) | OpenGL driver bundle, resolved the same way. |
| `IOVARendererID`, `IOVARendererSubID`, `IODVDBundleName`, `IOGVA*` | various | AppleGVA, AppleVA, AppleVPA | Video-decode bundle selection and capabilities. |
| `IOServiceCompatibility` | any | Metal | Metal skips a service that has it. |
| `Removable` | bool | Metal | Metal skips the service when it avoids removable GPUs. |
| `SafeEjectRequested` | bool | Metal | Metal stops setting the device up. |

### Device class

- It must be a subclass of `_MTLDevice`, which Metal checks with `isSubclassOfClass:`. It must also implement `-initWithAcceleratorPort:` (an `io_service_t`).
- It must override `-newArgumentEncoderWithLayout:`. The base class `MTLIOAccelDevice` implements it as a tail call to `-newIndirectArgumentEncoderWithLayout:`, which aborts. On 25G241 that is the only abort or `ud2` stub in Metal's IOAccel base classes. Apple's AMD driver overrides `-newArgumentEncoderWithLayout:` and `-newArgumentEncoderWithBufferBinding:` (TESTPLAN T-0001).

### Timing

- WindowServer chooses between the Metal and software compositors once per launch, after `IOKitWaitQuiet`. The accelerator must therefore be published during kext matching, before IOKit goes quiet (TESTPLAN T-0003).

### Signing and placement (the gate ADR-0004 is about)

- AMFI checks library validation only in processes with `CS_REQUIRE_LV`. Each such platform client maps only platform code: WindowServer, Safari, Finder, SystemUIServer, Messages and the WebKit GPU process (RB-0004a §2.1).
- The WebKit GPU process's sandbox maps executable code only from system-volume paths (`/System/Library/{Extensions,CoreServices,Frameworks,PrivateFrameworks,…}` and `/usr/lib`), not from `/Library/GPUBundles`.
- kext_tools stages companion bundles into `/Library/GPUBundles` only when they are Apple-anchored or NVIDIA Developer ID.
