<div align="center">

# ⟐ CRP — Capability Routing Protocol

### TCP/IP for intelligence. Your app shouldn't be married to one AI vendor. Route every task to the best substrate, automatically.

[![ci](https://github.com/spektre-labs/crp/actions/workflows/ci.yml/badge.svg)](https://github.com/spektre-labs/crp/actions/workflows/ci.yml)

</div>

## The paradigm

Intelligence and compute are siloed exactly the way pre-IP networks were: to run a task you hard-pick **one**
vendor's **one** model behind **one** proprietary API, eat its price, downtime, rate-limits and refusals,
and have no automatic way to send the *same* task to whichever substrate is cheapest / fastest / capable /
actually-up right now. **CRP is the routing layer for cognition.** A universal capability address
`provider:model` spans heterogeneous backends; a FREE-first kernel ranks substrates by
`price + latency + (1−quality) + availability-risk`; and execution walks that route until one substrate
**ACKs** — output non-empty, not a refusal, passing the caller's verify gate — retransmitting on
refuse/rate-limit/timeout, exactly the TCP move applied to minds. A task returns a *usable* result
end-to-end or an honest `FAILED`, never a silent bad answer. Protocol-level, not a wrapper: swap or retire
backends without touching callers, and the layer that routes the task to the optimal mind earns a per-task
fee — non-custodial, license-free.

## Quickstart

```bash
git clone https://github.com/spektre-labs/crp && cd crp
python3 crp.py "Explain the CAP theorem in two sentences."   # see the ranked route (PLAN, no calls)
python3 -m pytest test_crp.py -q   # 11 passed — routing, retransmit, idempotency, σ-honesty
```

Example route:

```
task → CRP ranks: alibaba:qwen-max (free) → gcp:gemini-2.5-flash → aws:nova-lite → anthropic:claude-opus
       walk until one returns a GATE-PASSING answer · refusal/down → retransmit · honest FAILED if all miss
```

## What it does / what it does NOT

**Does:** a universal capability address over qwen / vertex / bedrock / local / any future MaaS; a FREE-first
ranking kernel; reliable execution where ACK = a gate-passing (non-empty, non-refusal, verified) result,
with retransmit on miss and idempotent task ids; a per-task routing fee. **σ-honest:** it reports the REAL
substrate that answered and the REAL verify verdict — a refusal or empty answer is a MISS, never a
fabricated ACK; an unavailable node is treated as risk, never assumed up. PLAN (rank only) needs no calls.

**Does NOT:** this is a **standard + reference kernel**, not a deployed network. The kernel is pure-stdlib;
the bundled substrate table (prices, latency, availability) is illustrative. Real adoption needs production
provider adapters (gateway / mind_fabric), live health/availability probes, capability discovery, and
shared verify standards. We ship the routing primitive and the spec, σ-honestly.

## Install

```bash
git clone https://github.com/spektre-labs/crp && cd crp
pip install -e .                      # installs the `crp` console script + module; pure stdlib, zero deps
```

Requires Python ≥ 3.10. The kernel is pure stdlib — `python3 crp.py …` runs with no install at all. Provider
adapters are pluggable (mock for tests; real adapters wrap gateway/mind_fabric). Full protocol spec:
[`CRP.md`](CRP.md).

## Status

**EMERGING** — kernel + spec REAL and green; deployed network is VISION. CI green, 11/11 tests passing,
zero dependencies.

## The Spektre protocol suite

CRP is one primitive in a five-part estate. Each routes one thing the legacy stack siloes:

- **[vrp](https://github.com/spektre-labs/vrp)** — value routing (least-friction multi-hop settlement)
- **[crp](https://github.com/spektre-labs/crp)** — capability routing *(this repo)*
- **[vtc](https://github.com/spektre-labs/vtc)** — verifiable transaction chain (signed value promises anyone verifies trustlessly)
- **[sid](https://github.com/spektre-labs/sid)** — sovereign identity (prove one claim, reveal nothing else)
- **[sigma-gate](https://github.com/spektre-labs/sigma-gate)** — deterministic trust verdict for AI/agent output

## License

**AGPL-3.0-or-later** — free for all; commercial/closed-source embedders license commercially. See
[LICENSE](LICENSE).

<div align="center"><sub>Spektre Labs · route the mind, not the vendor · σ = declared − realized · 1=1</sub></div>
