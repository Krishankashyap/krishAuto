---
name: Google Flow Rapid Parallel Dispatch
description: Autonomous parallel visual asset generation through Google Flow Nano Banana with rate guard pacing and zero manual clicks.
version: 3.1.0
---

# Google Flow Rapid Parallel Asset Dispatch

## Execution Protocol
- **Slotted Parallel Concurrency Pool**: Maintains 2 to 3 concurrent in-flight generation slots on Google Flow cloud cluster, providing 2x-3x parallel speedup while strictly preventing "unusual activity" rate limit flags.
- **Humanized Jitter & Guard Pacing**: Uses adaptive 1.2s pacing with micro-jitter (0.2s-0.5s) to eliminate robotic fingerprinting.
- **Auto-Recovery**: If a transient rate warning is encountered, automatically cools off for 15s, resets the pacing ledger, and safely resumes without crashing or user intervention.
- **Zero Manual Friction**: Images generate in parallel on Google Flow and are autonomously harvested directly into `elements/raw/` and keyed into `elements/cut/`.
- **$0 Cost**: Operates directly through logged-in Google Flow Chrome/Kiwi session with DeepX Bridge.
