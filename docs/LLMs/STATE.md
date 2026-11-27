# STATE: Ryzentosh-dGPU

Updated: 2026-11-27 by the Project Lead (claude-opus-5-5 / max). RB-0004a kernel half done; citation review in progress.

## Phase
Research. RB-0004a (issue #1) is on branch `research/1-metal-loading-chain`, as draft PR #6 (https://github.com/ownback/Ryzentosh-dGPU/pull/6).

## Done: RB-0004a, all seven questions
Findings are in `docs/LLMs/re/RB-0004a-metal-loading-chain.md`. The kernel half used KDK 25G241 (`/Library/Developer/KDKs/KDK_26.7.1_25G241.kdk`), whose kernel and kexts match the running build by LC_UUID.

| Q | State |
|---|---|
| 1 Discovery | Verified: Metal matching, the trusted-bundle resolver, every consumer of it, the live registry, and the kernel class chain (`IOGPU` and `IOGraphicsAccelerator2` both derive from `IOAccelerator`). |
| 2 Gates | Verified, including AMFI's library-validation rule order, the failure outcomes, amfid's `DisableLibraryValidation` (needs csr 0x10), the `amfi` boot-arg bits, and the WebKit GPU sandbox. |
| 3 Inventory | Verified live. `CS_REQUIRE_LV` comes from the CodeDirectory `library-validation` flag of exactly six processes. |
| 4 Seams | Answered. No AMFI-intact seam for third-party code. The x86 paravirt guest kext is IOAcceleratorFamily2-based (PCI 0xEEEE106B). |
| 5 AMFIPass / VermilionTrust | Hook slots verified against the KDK (+0x120, +0x200). AMFIPass is described at behaviour level only (its binary is on the ESP). |
| 6 No-Metal | Static path verified; the 2026-11-20 software-compositor session observed. T-0002 covers the rest. |
| 7 Poster crash | Verified: `newIndirectArgumentEncoderWithLayout:` is the only abort stub in Metal's IOAccel base classes. T-0001. |

Recommendation: A survives for research/alpha only (three relaxation mechanisms). B and C survive pending RB-0004c and RB-0004b. D is dead for parity. E has no DriverKit family. One boot experiment, X1 (known-good minus VermilionTrust and AMFIPass), confirms the AMFI-intact baseline and doubles as the RB-0004d FairPlay baseline. No additional Linux captures are needed.

Also done:
- TESTPLAN T-0001 to T-0003 (T-0001 now names the exact override).
- The Metal plugin contract in INTERFACES.md.
- RE helpers in `tools/re/`, now including `kext_superclass.py` and `dsc_fix_copy.py`.

## In flight
The citation review by the reviewer subagent (claude-fable-5-2 / high).

## Next step (exact)
1. Fix the review's findings, then commit and push.
2. Update the PR #6 body (kernel half, review result, models, skipped stages) and mark it ready.
3. Send the summary with the X1 config to the Root Orchestrator thread.

## REA
No session is open. Raw evidence lives in `.private/rb-0004a/obs/`, which git ignores. Thinned KDK binaries and the shared-cache extraction are in the session scratchpad and are disposable: re-create them with `lipo -thin x86_64` and `tools/re/dscx`.

## Blockers
None.

## Corrections for the control plane (reported to the Root Orchestrator)
- The MercuryPosterExtension crashes are iOS Simulator processes (`MTLSimDriver`), not a dGPU problem.
- On the first 2026-11-27 boot, one shared-cache page (in `AppleSystemInfo`) was patched in memory, so `dsc_extractor` refused the live cache. After the reboot, no page mismatched.
