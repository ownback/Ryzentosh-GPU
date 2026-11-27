# STATE: Ryzentosh-dGPU

Updated: 2026-11-27 by the Project Lead (claude-opus-5-5 / max), at the second reboot checkpoint. The RB-0004a kernel half is done and pushed (15e13e0). The citation review was stopped unfinished for the reboot, with no findings recorded.

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
Nothing is running. The citation review by the reviewer subagent (claude-fable-5-2 / high) was started at 15e13e0 and stopped for the owner reboot before it reported.

## Next step (exact; there is no kernel analysis left to resume)
1. **Re-create the review inputs.** The new session scratchpad needs the thinned KDK kexts and amfid, `amfi.otool.txt`, and a fresh shared-cache extraction. The commands are at the top of `.private/rb-0004a/review-brief.md` (git ignores it).
2. **Re-run the citation review.** Use the Agent type `reviewer` (Fable 5.2 / high, read-only), with the brief in that file and `<S>` replaced by the new scratchpad path.
3. **Fix its findings** in the findings file, TESTPLAN and INTERFACES. Run a privacy scan, then commit and push.
4. **Update the PR #6 body.** Cover the kernel half, the review result, the models (Opus 5.5 / max lead, Fable 5.2 / high review) and why the build and hardware-test stages are skipped (research only). Then mark the PR ready.
5. **Send the summary to the Root Orchestrator thread.** Include the surviving ADR-0004 options, the X1 config (findings file, "Recommendation"), "no additional Linux captures needed" and the control-plane corrections below.

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
