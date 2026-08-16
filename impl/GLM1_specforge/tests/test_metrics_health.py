"""WP9 tests: health metrics, degradation triggers, human report hygiene."""
from specforge.metrics import (
    HealthTracker,
    WaveMetrics,
    collect_proposals,
    evaluate_degradation,
    render_human_report,
)
from specforge.metrics.health import HealthReport


def _wm(verdict, admitted=True, cost=1.0, escape=False, kappa=None):
    return WaveMetrics(wave_id="w", spec_id="u", n_instances=3,
                       measurement_verdict=verdict, admitted=admitted,
                       cost_usd=cost, escape_suspected=escape, judge_kappa=kappa)


def test_closure_and_entropy():
    t = HealthTracker()
    for v in ["CLOSED", "CLOSED", "CLOSED", "SILENCE", "AMBIGUOUS"]:
        t.record_wave(_wm(v))
    rep = t.snapshot(clause_coverage=0.95)
    assert rep.closure == 0.6
    assert rep.spec_entropy == 0.4
    assert rep.degradations == []  # entropy exactly at threshold 0.4 not >


def test_escape_rate_triggers_degradation():
    t = HealthTracker()
    for _ in range(10):
        t.record_wave(_wm("CLOSED", escape=True))
    rep = t.snapshot()
    assert rep.escape_rate == 1.0
    assert any("escape" in d for d in rep.degradations)


def test_kappa_below_gate_disables_soft():
    rep = HealthReport(judge_kappa=0.4, waves=1)
    trigs = evaluate_degradation(rep)
    assert any("kappa" in d for d in trigs)


def test_cost_without_closure_triggers():
    rep = HealthReport(waves=5, admissions=1, closures=1, total_cost_usd=100.0)
    assert rep.cost_per_admission == 100.0
    assert rep.closure == 0.2
    assert any("cost" in d for d in evaluate_degradation(rep))


def test_human_report_omits_forbidden_content():
    rep = HealthReport(clause_coverage=0.9, judge_kappa=0.8)
    text = render_human_report(
        rep,
        l1_l2_matters=["L2 contract change: adder API rename (needs approval)"],
        proposals=["proposal: bind 2 unverifiable clauses"])
    assert "health score" in text
    assert "L1/L2" in text
    for banned in ("diff --git", "instance b2 selected", "RU upgrade"):
        assert banned not in text
    assert "code diffs" in text  # explicit disclaimer


def test_proposal_channel():
    rep = HealthReport(unverifiable_clauses=3, waves=2, silence_events=2)  # entropy=1.0
    assert rep.spec_entropy == 1.0
    props = collect_proposals(rep)
    assert any("unverifiable" in p for p in props)
    assert any("don't-care" in p or "fanout" in p for p in props)


def test_health_score_bounds():
    rep = HealthReport()
    assert 0.0 <= rep.health_score <= 1.0
    rep_bad = HealthReport(judge_kappa=0.0, clause_coverage=0.1,
                           escape_rate=1.0)
    rep_bad.degradations = ["d1", "d2"]
    assert rep_bad.health_score < rep.health_score
