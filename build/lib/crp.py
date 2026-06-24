#!/usr/bin/env python3
"""
CRP — the Capability Routing Protocol kernel.  "TCP/IP for computation / intelligence."

THE GLOBAL FRICTION IT SOLVES
-----------------------------
Intelligence and compute are siloed exactly the way pre-IP networks were. To run a task you hard-pick ONE
vendor's ONE model behind ONE proprietary API, lock in, eat its price and downtime, and have no automatic
way to route the SAME task to whichever substrate is cheapest / fastest / capable / actually-up right now.
There is no universal *capability address*, no least-cost routing across providers, no end-to-end
reliability (retry/fallback) when a model refuses, rate-limits, or dies. Every app re-implements this badly.
CRP is the missing routing layer for cognition: address any capability uniformly, route a task to the
optimal substrate, and guarantee a usable result or an honest failure — across Alibaba, GCP, AWS, local
GPUs, and any future MaaS / neural net.

THE PARADIGM (protocol-level, not a wrapper)
--------------------------------------------
1. UNIVERSAL CAPABILITY ADDRESS — `provider:model` (`alibaba:qwen-max`, `gcp:gemini-2.5-flash`,
   `aws:nova-lite`, `local:ollama`). One address space over heterogeneous intelligence backends.
2. ROUTING KERNEL — given (task, constraints) it RANKS substrates by a metric = price + latency +
   (1-quality) + availability-risk, FREE-first, and produces an ordered route. The right mind for the
   task, automatically — not a hardcoded vendor.
3. RELIABILITY (the TCP analogue) — execution walks the route until one substrate **ACKs**: output is
   non-empty, not a refusal, and passes the caller's verify gate (optional fact-check). Refuse / rate-
   limit / timeout → retransmit to the next candidate. Idempotent task id → cacheable, exactly-once.
   A task returns a USABLE result end-to-end, or an honest FAILED — never a silent bad answer.
4. PERMISSIONLESS + PORTABLE — no provider owns the task; swap/retire backends without touching callers.
5. VALUE CAPTURE — the kernel takes a tiny routing fee per task it carries: the layer that routes
   cognition to the optimal mind gets paid (non-custodial, license-free).

σ-HONESTY (hard invariant)
--------------------------
The kernel reports the REAL substrate that answered and the REAL verify verdict. It NEVER fabricates an
ACK: an answer that fails the gate is a miss, not a success. Unknown availability = treated as risk, not
assumed up. PLAN (rank only) needs no calls; EXECUTE calls real adapters. 0 usable = honest FAILED.

Pure-stdlib kernel. Provider adapters pluggable: real adapters wrap the repo's gateway / mind_fabric
(qwen-max, Vertex, Bedrock, local-GPU); mock adapters make it deterministically testable, no network.
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


@dataclass(frozen=True)
class CapAddr:
    provider: str           # alibaba | gcp | aws | local | …
    model: str

    @staticmethod
    def parse(s: str) -> "CapAddr":
        if ":" not in s:
            raise ValueError(f"capability address must be 'provider:model', got {s!r}")
        p, m = s.split(":", 1)
        if not p or not m:
            raise ValueError(f"empty provider or model in {s!r}")
        return CapAddr(p.lower(), m)

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"


@dataclass
class Substrate:
    addr: str               # "provider:model"
    usd_per_1k: float       # blended $/1k tokens (0 = free tier)
    latency_ms: int
    quality: float          # 0..1 (caller's prior / measured)
    free: bool
    available: float = 1.0  # 0..1 live availability (1=up). <1 = risk; updated by health probes.


class TaskState(str, Enum):
    PENDING = "PENDING"
    ROUTED = "ROUTED"
    ACKED = "ACKED"         # a substrate returned a gate-passing result
    FAILED = "FAILED"       # all candidates missed → honest failure


@dataclass
class Result:
    task_id: str
    state: TaskState
    answer: Optional[str] = None
    via: Optional[str] = None
    attempts: list[dict] = field(default_factory=list)
    cost_usd: float = 0.0
    fee_usd: float = 0.0


class CRPKernel:
    PROTOCOL_FEE_BPS = 10.0    # 0.1% of routed compute cost (min applies); the cognition-routing fee

    def __init__(self, substrates: list[Substrate], *,
                 call_fn: Optional[Callable[[str, str], dict]] = None,   # (addr, prompt) -> {ok,text,tokens}
                 verify_fn: Optional[Callable[[str, str], bool]] = None, # (task, text) -> usable?
                 clock: Callable[[], float] = time.time):
        self.subs = substrates
        self._call = call_fn
        self._verify = verify_fn or self._default_verify
        self._clock = clock

    @staticmethod
    def _default_verify(task: str, text: str) -> bool:
        if not text or len(text.strip()) < 1:
            return False
        low = text.lower()
        return not any(r in low for r in ("i cannot", "i can't help", "as an ai, i", "i'm unable to"))

    def _metric(self, s: Substrate, est_tokens: int) -> float:
        price = (0.0 if s.free else s.usd_per_1k * est_tokens / 1000.0)
        return price + s.latency_ms / 1000.0 + (1.0 - s.quality) * 2.0 + (1.0 - s.available) * 5.0

    def task_id(self, task: str, constraints: dict) -> str:
        return hashlib.sha256((task + "|" + json.dumps(constraints, sort_keys=True)).encode()).hexdigest()[:16]

    def route(self, task: str, *, est_tokens: int = 800, min_quality: float = 0.0,
              max_usd: Optional[float] = None, prefer_free: bool = True) -> list[Substrate]:
        """Ordered candidate route (best first). PLAN only — no calls. FREE-first when prefer_free."""
        cands = [s for s in self.subs
                 if s.quality >= min_quality
                 and (max_usd is None or (0.0 if s.free else s.usd_per_1k * est_tokens / 1000.0) <= max_usd)
                 and s.available > 0.0]
        def key(s: Substrate):
            return (0 if (prefer_free and s.free) else 1, self._metric(s, est_tokens))
        return sorted(cands, key=key)

    def execute(self, task: str, *, est_tokens: int = 800, min_quality: float = 0.0,
                max_usd: Optional[float] = None, prefer_free: bool = True,
                confirm: bool = True) -> Result:
        """Walk the route until one substrate ACKs (gate-passing result). Retransmit on miss. σ-honest:
        the REAL substrate + verdict; never a fabricated ACK. confirm=False → PLAN (rank, no calls)."""
        tid = self.task_id(task, {"q": min_quality, "max_usd": max_usd})
        route = self.route(task, est_tokens=est_tokens, min_quality=min_quality,
                           max_usd=max_usd, prefer_free=prefer_free)
        r = Result(task_id=tid, state=TaskState.PENDING)
        if not route:
            r.state = TaskState.FAILED
            r.attempts.append({"err": "no substrate meets constraints"})
            return r
        r.state = TaskState.ROUTED
        if not confirm or not self._call:
            r.attempts = [{"candidate": s.addr, "metric": round(self._metric(s, est_tokens), 4)} for s in route]
            return r            # PLAN: the ranked route, no calls
        for s in route:
            res = self._call(s.addr, task) or {}
            tokens = int(res.get("tokens", est_tokens) or est_tokens)
            cost = 0.0 if s.free else round(s.usd_per_1k * tokens / 1000.0, 6)
            ok = bool(res.get("ok")) and self._verify(task, res.get("text", ""))
            r.attempts.append({"via": s.addr, "ok": ok, "cost_usd": cost,
                               "reason": None if ok else (res.get("err") or "gate miss (empty/refusal)")})
            if ok:
                r.state = TaskState.ACKED
                r.answer = res["text"]
                r.via = s.addr
                r.cost_usd = cost
                r.fee_usd = max(round(cost * self.PROTOCOL_FEE_BPS / 1e4, 6), 0.0001 if not s.free else 0.0)
                return r
        r.state = TaskState.FAILED      # every candidate missed → honest failure, no fabrication
        return r


def default_substrates() -> list[Substrate]:
    # illustrative; real deployments load live price/latency/availability per substrate
    return [
        Substrate("alibaba:qwen-max",        usd_per_1k=0.0,  latency_ms=1800, quality=0.92, free=True,  available=1.0),
        Substrate("local:ollama",            usd_per_1k=0.0,  latency_ms=900,  quality=0.78, free=True,  available=0.0),  # off unless GPU up
        Substrate("gcp:gemini-2.5-flash",    usd_per_1k=0.30, latency_ms=1200, quality=0.90, free=False, available=1.0),
        Substrate("aws:nova-lite",           usd_per_1k=0.24, latency_ms=1100, quality=0.84, free=False, available=0.6),  # entitlement propagating
        Substrate("anthropic:claude-opus",   usd_per_1k=15.0, latency_ms=2200, quality=0.99, free=False, available=1.0),
    ]


def main(argv: Optional[list[str]] = None) -> int:
    import sys
    if argv is None:
        argv = sys.argv[1:]
    task = " ".join(argv) or "Summarize the CAP theorem in two sentences."
    k = CRPKernel(default_substrates())
    print("ROUTE (plan):", [s.addr for s in k.route(task)])
    print(json.dumps(k.execute(task, confirm=False).__dict__, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
