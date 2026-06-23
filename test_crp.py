"""Deterministic, no-network tests for the CRP kernel: capability routing, reliability/retransmit,
idempotency, the σ-honesty invariant (a refusal/empty answer is a MISS, never a fabricated ACK)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from crp import CRPKernel, Substrate, CapAddr, TaskState, default_substrates


def test_addr_parse_reject():
    a = CapAddr.parse("alibaba:qwen-max")
    assert a.provider == "alibaba" and a.model == "qwen-max"
    for bad in ["noColon", "p:", ":m"]:
        try: CapAddr.parse(bad); assert False, bad
        except ValueError: pass


def test_route_free_first():
    k = CRPKernel(default_substrates())
    route = k.route("hi")
    # first candidate must be a free, available substrate (qwen-max; local is off→available 0 excluded)
    assert route[0].addr == "alibaba:qwen-max" and route[0].free


def test_route_excludes_unavailable():
    k = CRPKernel(default_substrates())
    addrs = [s.addr for s in k.route("hi")]
    assert "local:ollama" not in addrs   # available=0.0 → excluded (honest: don't route to a down node)


def test_route_respects_max_usd_and_quality():
    k = CRPKernel(default_substrates())
    cheap = [s.addr for s in k.route("hi", est_tokens=1000, max_usd=0.30)]
    assert "anthropic:claude-opus" not in cheap     # 15/1k*1k = $15 > cap
    hq = k.route("hi", min_quality=0.95)
    assert all(s.quality >= 0.95 for s in hq) and hq[0].addr == "anthropic:claude-opus"


def test_plan_only_no_calls():
    called = []
    k = CRPKernel(default_substrates(), call_fn=lambda a, p: called.append(a) or {"ok": True, "text": "x"})
    r = k.execute("hi", confirm=False)
    assert r.state == TaskState.ROUTED and not called   # PLAN: ranked, zero calls


def test_execute_acks_first_good():
    def call(addr, prompt): return {"ok": True, "text": "CAP: consistency, availability, partition.", "tokens": 50}
    k = CRPKernel(default_substrates(), call_fn=call)
    r = k.execute("explain CAP")
    assert r.state == TaskState.ACKED and r.via == "alibaba:qwen-max" and r.answer


def test_retransmit_on_refusal():
    # qwen refuses (gate miss) → must glide to the next candidate, NOT fabricate success
    def call(addr, prompt):
        if addr == "alibaba:qwen-max": return {"ok": True, "text": "I cannot help with that."}
        return {"ok": True, "text": "Real answer.", "tokens": 40}
    k = CRPKernel(default_substrates(), call_fn=call)
    r = k.execute("do it")
    assert r.state == TaskState.ACKED and r.via != "alibaba:qwen-max"
    assert any(not a["ok"] for a in r.attempts)   # the refusal was honestly recorded as a miss


def test_all_miss_is_honest_failure():
    k = CRPKernel(default_substrates(), call_fn=lambda a, p: {"ok": True, "text": "as an AI, I cannot"})
    r = k.execute("x")
    assert r.state == TaskState.FAILED and r.answer is None   # never a fabricated ACK


def test_idempotent_task_id():
    k = CRPKernel(default_substrates())
    assert k.task_id("t", {"a": 1}) == k.task_id("t", {"a": 1})
    assert k.task_id("t", {"a": 1}) != k.task_id("t", {"a": 2})


def test_fee_captured_on_paid_route():
    def call(addr, prompt): return {"ok": True, "text": "ok", "tokens": 1000}
    # only a paid substrate available → fee > 0
    subs = [Substrate("gcp:gemini-2.5-flash", 0.30, 1200, 0.9, False, 1.0)]
    k = CRPKernel(subs, call_fn=call)
    r = k.execute("hi")
    assert r.state == TaskState.ACKED and r.cost_usd > 0 and r.fee_usd > 0


def test_no_substrate_meets_constraints():
    k = CRPKernel(default_substrates())
    r = k.execute("hi", min_quality=1.1)   # impossible
    assert r.state == TaskState.FAILED


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
