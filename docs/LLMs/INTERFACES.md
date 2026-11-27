# INTERFACES: Ryzentosh-dGPU

External contracts: IOKit classes and properties, user-client selectors, plist keys, files installed, interfaces consumed from other Ryzentosh repos.

## Metal plugin contract (consumed by Metal.framework, 25G241)

Source: [re/RB-0004a-metal-loading-chain.md](re/RB-0004a-metal-loading-chain.md) Q1 and Q7. These are facts about Apple's code, not our design yet.

### Properties on the accelerator service

Metal finds the service through `IOServiceMatching("IOAccelerator")` plus `IOServicePublish` notifications. The service must therefore be an `IOAccelerator` subclass.

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
- It must override every abort stub of the base class `MTLIOAccelDevice`. The first known one is `-newArgumentEncoderWithLayout:`, whose base implementation tail-calls the abort stub `-newIndirectArgumentEncoderWithLayout:` (TESTPLAN T-0001).

### Timing

- WindowServer chooses between the Metal and software compositors once per launch, after `IOKitWaitQuiet`. The accelerator must therefore be published during kext matching, before IOKit goes quiet (TESTPLAN T-0003).

### Signing and placement (the gate ADR-0004 is about)

- Every LV-enforcing platform client accepts only platform (Apple-signed, trust-cached) code: WindowServer, Safari, Finder, SystemUIServer, Messages and the WebKit GPU process.
- kext_tools stages companion bundles into `/Library/GPUBundles` only when they are Apple-anchored or NVIDIA Developer ID.
