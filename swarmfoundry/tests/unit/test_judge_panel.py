from swarmfoundry.schema.judge import JudgeVerdict, aggregate_panel


def _v(jid, family, verdict):
    return JudgeVerdict(judge_id=jid, model_family=family, verdict=verdict, reasons="r")


def test_two_no_veto_passes():
    d = aggregate_panel([_v("j1", "famA", "no_veto"), _v("j2", "famB", "no_veto")], "famZ")
    assert not d.vetoed and d.counted == 2


def test_single_veto_blocks():
    d = aggregate_panel([_v("j1", "famA", "veto"), _v("j2", "famB", "no_veto")], "famZ")
    assert d.vetoed


def test_self_review_invalidated_and_fails_closed():
    d = aggregate_panel(
        [_v("j1", "famZ", "no_veto"), _v("j2", "famB", "no_veto"), _v("j3", "famC", "no_veto")],
        "famZ",
        min_valid=3,
    )
    assert d.invalidated == 1
    assert d.vetoed
    assert any("self-review" in r for r in d.reasons)


def test_abstain_not_counted_but_not_invalid():
    d = aggregate_panel([_v("j1", "famA", "abstain"), _v("j2", "famB", "no_veto"), _v("j3", "famC", "no_veto")], "famZ")
    assert d.abstained == 1 and d.counted == 2 and not d.vetoed


def test_insufficient_valid_verdicts_fails_closed():
    d = aggregate_panel([_v("j1", "famA", "no_veto")], "famZ", min_valid=2)
    assert d.vetoed
    assert any("fail-closed" in r for r in d.reasons)


def test_duplicate_judge_invalidated():
    d = aggregate_panel([_v("j1", "famA", "no_veto"), _v("j1", "famB", "no_veto"), _v("j2", "famC", "no_veto")], "famZ")
    assert d.invalidated == 1 and d.counted == 2
