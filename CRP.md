# CRP — Capability Routing Protocol · specification v0.1

> **TCP/IP for computation & intelligence.** One universal address for any capability over any provider;
> automatic least-cost routing of a task to the optimal substrate; end-to-end reliability (retry/fallback
> until a usable result); permissionless and portable. A standard, not a vendor wrapper.

## 1. The problem (global, known)
Intelligence/compute is siloed like pre-IP networks. You hard-pick ONE vendor's ONE model behind ONE
proprietary API — lock-in, its price, its downtime, its refusals — with no automatic way to send the SAME
task to whichever substrate is cheapest/fastest/capable/up right now. No universal capability address, no
cross-provider routing, no reliability when a model refuses, rate-limits, or dies. Every app re-builds
this badly. CRP is the routing layer for cognition.

## 2. Architecture
1. **Universal capability address** `provider:model` (`alibaba:qwen-max`, `gcp:gemini-2.5-flash`,
   `aws:nova-lite`, `local:ollama`) — one space over heterogeneous intelligence backends.
2. **Routing kernel** — rank substrates by `metric = price + latency + (1-quality) + availability-risk`,
   FREE-first; emit an ordered route. The right mind per task, automatically.
3. **Reliability (TCP analogue)** — walk the route until one substrate **ACKs**: non-empty, not a refusal,
   passes the caller's verify gate. Refuse/rate-limit/timeout → **retransmit** to the next. Idempotent
   task id → cacheable, exactly-once. A task returns a USABLE result, or an honest FAILED.
4. **Permissionless + portable** — swap/retire backends without touching callers.
5. **Value capture** — a tiny routing fee per carried task: the layer that routes cognition to the optimal
   mind gets paid (non-custodial, license-free).

## 3. σ-honesty (hard invariant)
Reports the REAL substrate that answered + the REAL verify verdict. An answer that fails the gate is a
MISS, never a fabricated ACK. Unknown availability = risk, not assumed-up. PLAN (rank) makes no calls;
EXECUTE calls real adapters; 0 usable = honest FAILED.

## 4. Reference implementation
`crp.py` — pure-stdlib kernel (capability address, metric routing, reliability/retransmit, idempotent id,
fee). Provider adapters pluggable: real adapters wrap the gateway / mind_fabric (qwen-max, Vertex, Bedrock,
local-GPU); mock adapters make it deterministic (`test_crp.py`, 11/11). `default_substrates()` is
illustrative; live deployments load real price/latency/availability.

## 5. Honest scope
A protocol + working reference kernel — not a deployed global network. Adoption needs production provider
adapters with live health, a capability-discovery layer, and verify-gate standards. We ship the standard +
reference, σ-honestly.

_Address any capability. Route to the optimal mind. Guarantee a usable result or an honest failure._ · AGPL-3.0
