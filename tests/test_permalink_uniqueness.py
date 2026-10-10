"""Repo-local falsifier for the da4710 permalink-collision cure.

Born-red before the cure: 34 sitemap locs were each claimed by two or
more ``pages/*.md`` documents (76 files total) — generic topic slugs like
``/causation/`` shared by a level-2 topic page and an unrelated leaf, and
the ``/improving-your-think-da4710/`` index slug shared by ten subtopic
index files. Jekyll last-write-wins left one document per URL live and
the rest shadowed out of navigation.

Post-cure law:

1. Every ``pages/*.md`` front-matter ``permalink`` is unique tree-wide.
2. The 34 previously-shared slugs still resolve to the same live-serving
   document (winner preserved — zero live-route breakage).
3. Every shadowed document carries a unique replacement permalink
   (topic-word suffix for index pages, stable basename fragment for
   content pages — the estate's established conventions).
4. Referential integrity: every ``parent_permalink`` equals the actual
   permalink of the file named by ``parent_basename``, and every
   basename-keyed ``permalink`` inside body link blocks equals the
   referenced file's actual permalink.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
_FIELD = {
    "permalink": re.compile(r'^permalink:\s*["\']?(/[^\s"\'#]*)["\']?\s*$', re.M),
    "parent_permalink": re.compile(
        r'^parent_permalink:\s*["\']?(/[^\s"\'#]*)["\']?\s*$', re.M
    ),
    "basename": re.compile(r"^basename:\s*(\S+)\s*$", re.M),
    "parent_basename": re.compile(r"^parent_basename:\s*(\S+)\s*$", re.M),
}
_BODY_ITEM = re.compile(
    r"basename:\s*(\S+)\s*\n(?:[^\n]*\n){0,6}?\s*permalink:\s*(/\S+?/)"
)

#: The shared slug -> the file that serves it live today (probed 2026-10-10:
#: HTTP title matched file front-matter title for all 34 groups).
WINNERS = {
    "/alternatives/": "improving_your_think_da4710_live_alternatives_e775b1",
    "/base-rates/": "improving_your_think_da4710_thinking_mistakes_7c70ba_base_rates_11f2c9",
    "/brain-dumps/": "improving_your_think_da4710_retrieval_practice_750003_brain_dumps_missing_7cd538",
    "/brier-scores/": "improving_your_think_da4710_feedback_calibration_8a35f0_brier_scores_limits_363784",
    "/causation/": "improving_your_think_da4710_critical_thinking_tr_28fa6d_correlation_causatio_db7bf3",
    "/checklists/": "improving_your_think_da4710_real_world_transfer_0cecd5_thinking_checklists_9f9fca",
    "/confidence/": "improving_your_think_da4710_prediction_habits_f0daf5_confidence_answer_ke_e67afb",
    "/domain-knowledge/": "improving_your_think_da4710_real_world_transfer_0cecd5_domain_knowledge_jud_286498",
    "/false-fluency/": "improving_your_think_da4710_intuition_vs_analysi_f4ec00_false_fluency_9ed854",
    "/feedback-loops/": "improving_your_think_da4710_real_problem_practic_466932_feedback_loops_fdc3b7",
    "/feedback/": "improving_your_think_da4710_feedback_loops_judgm_3e40b7",
    "/good-judgment/": "improving_your_think_da4710_feedback_calibration_8a35f0_good_judgment_lesson_ea91a6",
    "/health-claims/": "improving_your_think_da4710_health_claim_skeptic_4efb5d",
    "/improving-your-think-da4710-decision/": "improving_your_think_da4710_decision_stakes_7c2e2a_index",
    "/improving-your-think-da4710-feedback/": "improving_your_think_da4710_feedback_calibration_8a35f0_index",
    "/improving-your-think-da4710-intuition/": "improving_your_think_da4710_intuition_vs_analysi_f4ec00_index",
    "/improving-your-think-da4710-online/": "improving_your_think_da4710_online_confirmation_d4dd0f_index",
    "/improving-your-think-da4710-problem/": "improving_your_think_da4710_problem_framing_7f52a6_index",
    "/improving-your-think-da4710/": "improving_your_think_da4710_steelmanning_argumen_91444a_index",
    "/lateral-reading/": "improving_your_think_da4710_online_claims_3bbb25_lateral_reading_sour_b1df5f",
    "/low-stakes/": "improving_your_think_da4710_retrieval_practice_750003_low_stakes_retrieval_7a069a",
    "/metacognition/": "improving_your_think_da4710_metacognition_assump_b47334",
    "/opposite-test/": "improving_your_think_da4710_strong_objections_4a9a76_consider_the_opposit_d8b0ee",
    "/outcome-bias/": "improving_your_think_da4710_feedback_loops_judgm_3e40b7_outcome_bias_9d7f23",
    "/outcomes/": "improving_your_think_da4710_real_world_transfer_0cecd5_thinking_real_world_976b1b",
    "/prediction-logs/": "improving_your_think_da4710_prediction_habits_f0daf5_prediction_logs_feed_6ae798",
    "/premortems/": "improving_your_think_da4710_weakest_link_assumpt_7c77f4_premortem_failure_ca_2dbece",
    "/probabilities/": "improving_your_think_da4710_probabilities_tradeo_aa66d9",
    "/probability-words/": "improving_your_think_da4710_confidence_calibrati_3ec11e_probability_words_66fb37",
    "/retrieval/": "improving_your_think_da4710_retrieval_practice_750003",
    "/steelmanning/": "improving_your_think_da4710_strong_objections_4a9a76_steelman_rival_view_1716c5",
    "/sunk-costs/": "improving_your_think_da4710_thinking_mistakes_7c70ba_sunk_costs_8f2993",
    "/transfer-gap/": "improving_your_think_da4710_real_world_transfer_0cecd5_critical_thinking_tr_1f9f9e",
    "/transfer/": "improving_your_think_da4710_real_world_transfer_0cecd5",
}


def _front_matter(path: Path) -> str:
    match = _FRONT_MATTER.match(path.read_text(encoding="utf-8", errors="replace"))
    return match.group(1) if match else ""


def _field(front: str, name: str) -> str | None:
    match = _FIELD[name].search(front)
    return match.group(1) if match else None


def _inventory():
    """stem -> {permalink, basename, parent_permalink, parent_basename}."""
    out = {}
    for page in sorted((REPO_ROOT / "pages").glob("*.md")):
        front = _front_matter(page)
        out[page.stem] = {
            "permalink": _field(front, "permalink"),
            "basename": _field(front, "basename") or page.stem,
            "parent_permalink": _field(front, "parent_permalink"),
            "parent_basename": _field(front, "parent_basename"),
        }
    return out


def test_tree_wide_permalink_uniqueness():
    inv = _inventory()
    counts = Counter(v["permalink"] for v in inv.values() if v["permalink"])
    dups = {k: n for k, n in counts.items() if n > 1}
    assert dups == {}, f"colliding permalinks: {dups}"


def test_live_winners_preserved():
    """Each previously-shared slug still belongs to its live-serving file."""
    inv = _inventory()
    for slug, stem in WINNERS.items():
        assert inv[stem]["permalink"] == slug, (
            f"{stem} lost its live route {slug}"
        )


#: Shadowed file -> its cured permalink. Index pages take their parent's
#: topic words (estate index carrier convention); content pages take the
#: stable basename fragment (arnold-sighting disambiguation law).
CURED = {
    "improving_your_think_da4710_alternative_explanat_ee4fa0": "/alternatives-ee4fa0/",
    "improving_your_think_da4710_high_stakes_decision_b09c8f_reference_class_fore_cd7842": "/base-rates-cd7842/",
    "improving_your_think_da4710_practice_testing_35a599_reading_brain_dumps_1afd95": "/brain-dumps-1afd95/",
    "improving_your_think_da4710_confidence_calibrati_3ec11e_brier_scores_persona_4eff62": "/brier-scores-4eff62/",
    "improving_your_think_da4710_correlation_causatio_a505f2": "/causation-a505f2/",
    "improving_your_think_da4710_high_stakes_decision_b09c8f_surgical_checklist_l_3f76cd": "/checklists-3f76cd/",
    "improving_your_think_da4710_metacognition_74edbc_confidence_evidence_ef0c00": "/confidence-ef0c00/",
    "improving_your_think_da4710_domain_knowledge_96a03e": "/domain-knowledge-96a03e/",
    "improving_your_think_da4710_first_answer_traps_70dd40_fluency_false_confid_d29b93": "/false-fluency-d29b93/",
    "improving_your_think_da4710_intuition_second_pas_ed3df6_expert_intuition_fee_94296d": "/feedback-loops-94296d/",
    "improving_your_think_da4710_feedback_calibration_8a35f0": "/feedback-8a35f0/",
    "improving_your_think_da4710_confidence_calibrati_3ec11e_good_judgment_lesson_ea91a6": "/good-judgment-ea91a6/",
    "improving_your_think_da4710_evidence_standards_a40c69_health_claim_standar_92b60f": "/health-claims-92b60f/",
    "improving_your_think_da4710_decision_journals_44d9d9_index": "/improving-your-think-da4710-decision-journal/",
    "improving_your_think_da4710_feedback_loops_judgm_3e40b7_index": "/improving-your-think-da4710-feedback-3e40b7/",
    "improving_your_think_da4710_intuition_second_pas_ed3df6_index": "/improving-your-think-da4710-intuition-ed3df6/",
    "improving_your_think_da4710_online_claims_3bbb25_index": "/improving-your-think-da4710-online-claims/",
    "improving_your_think_da4710_problem_breakdown_59ff8f_index": "/improving-your-think-da4710-problem-parts/",
    "improving_your_think_da4710_alternative_explanat_ee4fa0_index": "/improving-your-think-da4710-alternatives/",
    "improving_your_think_da4710_confirmation_bias_dee5c3_index": "/improving-your-think-da4710-confirmation-bias/",
    "improving_your_think_da4710_correlation_causatio_a505f2_index": "/improving-your-think-da4710-causation/",
    "improving_your_think_da4710_distributed_practice_4a249b_index": "/improving-your-think-da4710-spacing/",
    "improving_your_think_da4710_familiarity_trap_82f724_index": "/improving-your-think-da4710-fluency-trap/",
    "improving_your_think_da4710_intellectual_humilit_ff42ae_index": "/improving-your-think-da4710-humility/",
    "improving_your_think_da4710_metacognition_74edbc_index": "/improving-your-think-da4710-metacognition/",
    "improving_your_think_da4710_metacognition_assump_b47334_index": "/improving-your-think-da4710-metacognition-b47334/",
    "improving_your_think_da4710_probabilities_tradeo_aa66d9_index": "/improving-your-think-da4710-probabilities/",
    "improving_your_think_da4710_lateral_reading_afeebc": "/lateral-reading-afeebc/",
    "improving_your_think_da4710_evidence_standards_a40c69_low_stakes_threshold_0a0b96": "/low-stakes-0a0b96/",
    "improving_your_think_da4710_metacognition_74edbc": "/metacognition-74edbc/",
    "improving_your_think_da4710_metacognition_assump_b47334_consider_opposite_bi_a65a23": "/opposite-test-a65a23/",
    "improving_your_think_da4710_decision_journals_44d9d9_outcome_bias_decisio_3bef10": "/outcome-bias-3bef10/",
    "improving_your_think_da4710_question_design_1265c2_better_outcome_measu_1d9ea7": "/outcomes-1d9ea7/",
    "improving_your_think_da4710_deliberate_practice_ac56e9_prediction_logs_scor_8d2137": "/prediction-logs-8d2137/",
    "improving_your_think_da4710_change_my_mind_f0f53e_premortem_change_sig_6c6f43": "/premortems-6c6f43/",
    "improving_your_think_da4710_decision_journals_44d9d9_prediction_probabili_0b0809": "/probabilities-0b0809/",
    "improving_your_think_da4710_confidence_calibrati_3ec11e_probabilities_not_wo_bcc6f4": "/probability-words-bcc6f4/",
    "improving_your_think_da4710_no_notes_explanation_891faf_retrieval_practice_n_ff145b": "/retrieval-f145b/",
    "improving_your_think_da4710_open_minded_thinking_b0c2ad_strongest_opposing_a_102f34": "/steelmanning-102f34/",
    "improving_your_think_da4710_framing_effects_b0667d_sunk_cost_commitment_31e4c5": "/sunk-costs-31e4c5/",
    "improving_your_think_da4710_real_problem_practic_466932_transfer_gap_3c6a00": "/transfer-gap-3c6a00/",
    "improving_your_think_da4710_practice_testing_35a599_transfer_questions_ad96de": "/transfer-ad96de/",
}


def test_shadowed_files_gained_unique_permalinks():
    """Every shadowed file carries its cured route; winners keep theirs."""
    inv = _inventory()
    for slug, winner in WINNERS.items():
        claimants = [s for s, v in inv.items() if v["permalink"] == slug]
        assert claimants == [winner], f"{slug} claimed by {claimants}"
    assert len(CURED) + len(WINNERS) == 76  # the full colliding file set
    for stem, expected in CURED.items():
        assert inv[stem]["permalink"] == expected, (
            f"{stem}: expected {expected}, got {inv[stem]['permalink']}"
        )


def test_parent_permalink_referential_integrity():
    inv = _inventory()
    by_basename = {v["basename"]: v["permalink"] for v in inv.values()}
    bad = []
    for stem, v in inv.items():
        parent = v["parent_basename"]
        if parent and parent in by_basename and v["parent_permalink"] != by_basename[parent]:
            bad.append((stem, v["parent_permalink"], by_basename[parent]))
    assert bad == [], f"stale parent_permalink refs: {bad[:5]}"


def test_body_link_blocks_match_referenced_permalinks():
    """Basename-keyed body link entries name the file's real permalink."""
    by_basename = {}
    for page in sorted((REPO_ROOT / "pages").glob("*.md")):
        front = _front_matter(page)
        name = _field(front, "basename") or page.stem
        permalink = _field(front, "permalink")
        if permalink:
            by_basename[name] = permalink
    bad = []
    for page in sorted((REPO_ROOT / "pages").glob("*.md")):
        text = page.read_text(encoding="utf-8", errors="replace")
        front = _FRONT_MATTER.match(text)
        body = text[front.end():] if front else text
        for basename, permalink in _BODY_ITEM.findall(body):
            actual = by_basename.get(basename)
            if actual and actual != permalink:
                bad.append((page.stem[:50], basename[:50], permalink, actual))
    assert bad == [], f"stale body permalink refs: {bad[:5]}"
