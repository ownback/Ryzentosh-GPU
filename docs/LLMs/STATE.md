# STATE: Ryzentosh-GPU

Updated: 2026-11-27 by the Project Lead (claude-opus-5-5 / high).

## Phase
Research, M1.0. RB-0004a (issue #1) is merged (PR #6, squash c63e4ee). The repo is now ownback/Ryzentosh-GPU: one driver, RyzentoshGPU.kext, for the RX 7900 XTX and the Raphael iGPU (rename/scope PR for issue #10).

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
- Issue #10, branch `docs/10-rename-scope`: README, BRIEF and CLAUDE.md scope for the rename (docs only).

## Next step (exact; the Orchestrator approved the M1.0 plan, run sequentially)
1. **Combined B/C gate check:** a new issue, one draft PR, a Fable review, then a report to the Orchestrator.
   - RB-0004c gate (#3): the ISA targets of the shader compilers in Apple's AMD bundles, including whether Apple's bundles could serve the RDNA2 Raphael iGPU (gfx1036).
   - RB-0004b gate (#2): whether AppleParavirtGPU refuses bare metal (VMM checks), and the size of the guest protocol.
2. Only after the Orchestrator confirms: the display-driver ADR.
3. The X1 boot (RB-0004a): send the Orchestrator the exact EFI candidate spec when needed. It is batched with other EFI work, and the owner does an F8 boot.
4. Later (M4 / RB-0003g, #5): Continuity Camera fails because VideoToolbox reports no H.264 hardware decode (from WIRELESS RB-W1).

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
