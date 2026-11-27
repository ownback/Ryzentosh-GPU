# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Release stages: research → alpha → beta → stable.

## [Unreleased]
- Repository created from the Ryzentosh skeleton (2026-11-27).
- Renamed to Ryzentosh-GPU, with Ryzentosh-iGPU merged in: one RyzentoshGPU.kext for the RX 7900 XTX and the Raphael iGPU (2026-11-27).
- RB-0004b/c gate check: Apple's AMD stack has no gfx11 path, and the paravirt guest stack needs a faked Apple PCI device (`docs/LLMs/re/RB-0004bc-gate.md`, 2026-11-27).
- RB-0004a research findings, user-space and kernel halves: the Metal driver loading chain and library validation on 25G241 (`docs/LLMs/re/RB-0004a-metal-loading-chain.md`). Also adds RE helpers in `tools/re/` (including `kext_superclass.py` and `dsc_fix_copy.py`), TESTPLAN T-0001 to T-0003, and the Metal plugin contract in INTERFACES.md (2026-11-27).
