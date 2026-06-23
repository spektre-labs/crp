<div align="center">

# ⟐ CRP — Capability Routing Protocol
### TCP/IP for intelligence. Your app shouldn't be married to one AI vendor. Route every task to the best substrate, automatically.
</div>

**The friction everyone has:** you pick one model behind one API and eat its price, downtime, rate-limits
and refusals — with no automatic way to send the same task to whatever's cheapest/fastest/up right now.
CRP gives **computation** what TCP/IP gave **data**: a universal address, least-cost routing, and delivery
reliability.

```
task → CRP ranks: alibaba:qwen-max (free) → gcp:gemini-2.5-flash → aws:nova-lite → anthropic:claude-opus
       walks the route until one returns a GATE-PASSING answer · refusal/down → retransmit to next · honest FAILED if all miss
```

- **Universal address** `provider:model` over qwen / vertex / bedrock / local / any future MaaS.
- **Routing kernel** — FREE-first metric (price+latency+quality+availability).
- **Reliability** — ACK = usable result; retransmit on refusal/rate-limit/death; idempotent task id.
- **Permissionless + portable** — swap backends without touching callers.
- **Value capture** — routing fee per task; the cognition-router gets paid.
- **σ-honest** — real substrate + real verdict; a refusal is a MISS, never a fake ACK; PLAN by default.

## Run
```bash
python3 crp.py "Explain the CAP theorem in two sentences."   # see the ranked route
python3 -m pytest test_crp.py -q                              # 11/11
```
Pure stdlib; adapters pluggable (mock for tests; real wrap gateway/mind_fabric). Spec: [`CRP.md`](CRP.md).

**Honest scope:** a standard + reference kernel, not a deployed network — adoption needs production
adapters + discovery + verify standards. Sibling of [VRP](https://github.com/spektre-labs/vrp) (value
routing): one routes money, one routes minds.

## License
**AGPL-3.0-or-later** — free for all; commercial embedders license commercially.

<div align="center"><sub>Spektre Labs · route the mind, not the vendor · 1=1</sub></div>
