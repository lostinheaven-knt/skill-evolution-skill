# Roadmap and Progress

_Last updated: 2026-04-03_

This document tracks where the project stands, what was completed recently, and what should happen next.

---

## Current status

The repository now has a **standalone public-repo baseline** with a runnable passive skill-evolution prototype.

### Completed

- [x] created standalone GitHub repository
- [x] moved the project out of unrelated repos
- [x] runnable script pipeline from hook event -> report -> candidate -> validation -> promotion review -> lineage
- [x] JSON-schema-backed contracts for core artifacts
- [x] end-to-end demo runtime initializer
- [x] candidate metadata preservation through materialization (`skill_name`, `trigger_type`, `derived_from_report_id`)
- [x] refreshed standalone README and usage examples
- [x] expanded abnormal-path tests (invalid inbox lines, unresolved parent path, missing validation artifact)

### Current maturity

This is still **v0.1 prototype / contract-first infrastructure**, not a production self-evolving skill platform.

What it proves today:

- the workflow can be replayed as files
- outputs are inspectable and reviewable
- promotion remains conservative
- failures in the flow can be observed and tested

What it does **not** prove yet:

- candidate quality is high
- candidate changes improve behavior on real workloads
- the evaluation policy is strong enough for automation
- the repo layout is final

---

## Phase plan

### Phase 1 - Usability and confidence

**Goal:** make the repo easy to run and harder to misuse.

Status:
- [x] README / usage examples refresh
- [x] abnormal-path test expansion
- [ ] add more sample runtime snapshots or fixture-based examples
- [ ] normalize older reference docs that still reflect the pre-standalone layout

### Phase 2 - Runtime contract hardening

**Goal:** make schema validation a true guardrail instead of a mostly-local check.

Planned work:
- [ ] validate more runtime handoff artifacts at every boundary
- [ ] make failures easier to diagnose from transaction state alone
- [ ] tighten error reporting for malformed reports / candidates / promotion artifacts

### Phase 3 - Candidate evaluation quality

**Goal:** improve how the system decides whether a candidate is actually better than its parent.

Planned work:
- [ ] stronger candidate-vs-parent structural comparison
- [ ] better patch-target coverage checks
- [ ] lightweight offline evaluation against curated examples
- [ ] clearer separation between “structurally valid” and “behaviorally better”

### Phase 4 - Repository and workflow split

**Goal:** reduce long-term maintenance mess once the behavior stabilizes.

Planned work:
- [ ] split scaffold / sample artifacts / promotion workflow concerns
- [ ] decide what belongs in repo root vs generated runtime output
- [ ] consider a cleaner fixture strategy for demo data and regression cases

---

## Recommended next moves

If continuing immediately, the best order is:

1. harden runtime-level schema enforcement
2. strengthen candidate-vs-parent evaluation
3. split scaffold / sample artifacts / promotion workflow only after the behavior settles

This order is deliberate: first make it safer, then make it smarter, then make it prettier.

---

## Progress log

### 2026-04-03

Completed in this round:

- rewrote the public README for standalone-repo usage
- added clearer quick-start and custom-parent examples
- documented runtime layout and output artifacts
- added roadmap/progress tracking
- expanded tests for abnormal runtime behavior
- corrected `init_runtime_demo.py` to use a standalone-repo sibling-parent assumption (`../table-analysis-pro`)

---

## Notes for future maintainers

A few reference documents still contain older path examples such as `Skill_evolution_skill/...` from the pre-standalone layout. The README is the current source of truth for how to run the public repo.

When updating docs later, prefer changing examples toward repo-root-relative commands like:

```bash
python scripts/init_runtime_demo.py /tmp/skill-evolution-demo
python scripts/consume_hook_events.py /tmp/skill-evolution-demo
```

rather than nested-path examples from the earlier workspace layout.
