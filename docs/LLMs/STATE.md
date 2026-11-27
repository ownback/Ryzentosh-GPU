# STATE: Ryzentosh-dGPU

Updated: 2026-11-27 by the Project Lead (claude-opus-5-5 / high since the resume; max before). RB-0004a is complete and reviewed; PR #6 is ready for the squash merge.

## Phase
Research. RB-0004a (issue #1) is on branch `research/1-metal-loading-chain`, as PR #6, ready for review (https://github.com/ownback/Ryzentosh-GPU/pull/6).

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
Nothing is running. The citation review (claude-fable-5-2 / high, at cfb3316) re-derived about 70 [V] citations and approved, with no blocking findings. Its two wording nits are fixed. PR #6 is marked ready, and the Root Orchestrator does the squash merge.

## Next step (exact)
1. After the merge: delete the branch, and record the merge in this file on `main`.
2. Wait for the Root Orchestrator to pick the next M1.0 item. The Lead's proposal, sent to the Orchestrator 2026-11-27: RB-0004c, then RB-0004b, then the ADR-0004 decision, with the display-driver ADR in parallel.
3. When convenient, a small separate PR for the repo rename (ownback/Ryzentosh-GPU, one RyzentoshGPU.kext for the RX 7900 XTX and the Raphael iGPU): README, BRIEF and CLAUDE.md scope. Target tree: control plane `docs/Architecture/EFI-END-STATE.md`. RB-0005a/b/c are issues #7–#9 (later).

## REA
- No target is open (checked 2026-11-27 before the reboot).
- The session's 34 evidence records are exported to `.private/rb-0004a/rea/rb-0004a-kernel-evidence.json`, which git ignores. It is for local reference only and must never be committed, because it contains decompiled output.
- Raw observations are in `.private/rb-0004a/obs/`; the kernel tool outputs are in `obs/kernel/`.
- Thinned KDK binaries and the shared-cache extraction are disposable; re-create them as in step 1.

## Blockers
None.

## Corrections for the control plane (reported to the Root Orchestrator)
- The MercuryPosterExtension crashes are iOS Simulator processes (`MTLSimDriver`), not a dGPU problem.
- On the first 2026-11-27 boot, one shared-cache page (in `AppleSystemInfo`) was patched in memory, so `dsc_extractor` refused the live cache. After the reboot, no page mismatched.
