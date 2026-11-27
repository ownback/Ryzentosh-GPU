# STATE: Ryzentosh-dGPU

Updated: 2026-11-27 by the Project Lead (claude-opus-5-5 / max), at the reboot checkpoint for RB-0004a.

## Phase
Research. RB-0004a (issue #1) is in progress on branch `research/1-metal-loading-chain`, as draft PR #6 (https://github.com/ownback/Ryzentosh-dGPU/pull/6).

## Done: RB-0004a, user-space half
Findings are in `docs/LLMs/re/RB-0004a-metal-loading-chain.md`.

| Q | State |
|---|---|
| 1 Discovery | Verified: Metal matching, the trusted-bundle resolver, every consumer of it, the live registry. |
| 2 Gates | User-space gates verified (path trust, sandbox, kext_tools staging, AMFI strings, host entitlements). AMFI's decision logic still needs the kernel (K1). |
| 3 Inventory | Verified live. LV is enforced only in `REQUIRE_LV` processes; kernel confirmation pending (K1). |
| 4 Seams | Answered. The IOGPU generic device is still open (K4). |
| 5 AMFIPass / VermilionTrust | Behaviour verified by observation. Hook layout and the AMFIPass mechanism are pending (K2, K5). |
| 6 No-Metal | Static path verified. The 2026-11-20 software-compositor session was observed. The catalogue of affected apps moves to TESTPLAN T-0002. |
| 7 Poster crash | Root cause verified; recorded as T-0001. MercuryPosterExtension crashes are iOS Simulator crashes. |

Also done:
- TESTPLAN T-0001 to T-0003.
- The Metal plugin contract in INTERFACES.md.
- Read-only RE helpers in `tools/re/`.

## In flight
The RB-0004a kernel half. KDK 25G241 is installed at `/Library/Developer/KDKs/KDK_26.7.1_25G241.kdk`. It has not started: the reboot checkpoint came first.

## Next step (exact)
1. **After the reboot, check the probe.**
   - The session scratchpad was in `/private/tmp` and is gone. Re-extract the shared cache only if user-space re-checks are needed (see `tools/re/README.md`).
   - The raw evidence from the 2026-11-27 boot is kept in `.private/rb-0004a/obs/`, which git ignores.
   - If the owner booted the USB known-good, the live stack may differ. Re-check `kmutil showloaded` and `sysctl debug.phxtrust_stat` before using it as a probe.
2. **Do the kernel half with REA on the KDK binaries.**
   - K1: library-validation decision logic in AppleMobileFileIntegrity.
   - K2: AMFI's `mac_policy_ops` layout.
   - K3: Sandbox.kext, covering `rootless_check_trusted_class` and how `file-map-executable` is evaluated.
   - K4: the IOAcceleratorFamily2 / IOGPUFamily class hierarchy and the entitlement checks at user-client creation.
   - K5: the AMFIPass mechanism.
   - Also list every `MTLIOAccelDevice` abort stub with `tools/re/abort_stubs.py`. This needs Metal's abort-stub VA.
3. **Finish.**
   1. Update the findings file.
   2. Run the reviewer subagent (claude-fable-5-2, high) on the citations.
   3. Finalise the recommendation and the exact X1 config.
   4. Send the summary to the Root Orchestrator.
   5. Mark the PR ready.

## REA
No session is open. It was closed on 2026-11-27 before the reboot, without a snapshot, because its target was in the scratchpad. Re-open targets from the KDK, or from a fresh shared-cache extraction.

## Blockers
None. The kernel half was blocked on the KDK until 2026-11-27 and is now unblocked.

## Corrections for the control plane (reported to the Root Orchestrator)
- The MercuryPosterExtension crashes are iOS Simulator processes (`MTLSimDriver`), not a dGPU problem.
- The live dyld shared cache has one page (in `AppleSystemInfo`) patched in memory by a Lilu user-space patcher, so `dsc_extractor` refuses the live cache.
