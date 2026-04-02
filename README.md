# skill-evolution-skill

Runnable prototype for **passive AgentSkill evolution**:

1. consume hook events
2. normalize them into evolution reports
3. attribute a conservative recommended action
4. create candidate stubs
5. materialize candidates from parent skills when available
6. validate candidates structurally
7. generate promotion recommendations
8. write lineage records

This repository is intentionally small and conservative. It is **not** a full autonomous skill-evolution system yet; it is a file-based, replayable, reviewable prototype that proves the minimum loop can run end to end.

Detailed design documents are in `references/` (many are currently written in Chinese). The public README focuses on how to run the repository as a standalone project.

---

## Current scope

### Supported trigger types

- `skill_failure`
- `user_correction`
- `repeated_success_pattern`

### Current recommendation policy

- `user_correction` -> `patch`
- `repeated_success_pattern` -> `composition`
- `skill_failure` -> `patch` or `replacement`
- obvious environment-only failures may collapse to `no_change`

### Current promotion policy

- validation failed -> `reject`
- validation passed -> `review_required`
- validated candidates become `experimental`
- nothing is auto-promoted to `stable`

---

## Repository layout

```text
.
├── README.md
├── SKILL.md
├── config/
│   └── default.json
├── docs/
│   └── ROADMAP.md
├── references/
├── schemas/
├── scripts/
│   ├── common.py
│   ├── init_runtime_demo.py
│   ├── consume_hook_events.py
│   ├── emit_evolution_report.py
│   ├── attribute_candidate.py
│   ├── create_candidate_stub.py
│   ├── materialize_candidate_from_skill.py
│   ├── validate_candidate.py
│   ├── promote_candidate.py
│   ├── generate_promotion_review.py
│   └── write_lineage_record.py
└── tests/
    ├── test_p0_scripts.py
    └── test_p1_pipeline.py
```

### Directory roles

- `scripts/` - runnable prototype scripts
- `schemas/` - JSON contract files for report / transaction / candidate / validation / promotion review
- `references/` - design docs, boundaries, policy notes, implementation notes
- `config/default.json` - default logging and allowed status values
- `tests/` - script smoke tests plus end-to-end pipeline tests
- `docs/ROADMAP.md` - current status, next milestones, and what remains unfinished

---

## Requirements

- Python 3.10+
- no third-party Python package is required for the current prototype

---

## Quick start

### Option A: run the demo runtime

From the repository root:

```bash
python scripts/init_runtime_demo.py /tmp/skill-evolution-demo
python scripts/consume_hook_events.py /tmp/skill-evolution-demo
```

This will:

- create the runtime directory structure
- write `config.json`
- seed 3 example events
- process the inbox end to end
- produce reports, transactions, candidates, validation files, and lineage records

### What the demo assumes by default

`init_runtime_demo.py` assumes your parent skill lives in a **sibling repository**:

```text
../table-analysis-pro
```

So a common local layout is:

```text
workspace/
├── skill-evolution-skill/
└── table-analysis-pro/
```

If you do **not** have a sibling `table-analysis-pro` repo, the demo runtime still initializes, but candidate materialization from a parent skill will fail unless you update the runtime config or event payload.

---

## Using your own parent skill

After initializing a runtime, edit `/tmp/skill-evolution-demo/config.json`:

```json
{
  "skills_root": "/absolute/path/to/your/skills",
  "parent_skill_paths": {
    "your-skill-name": "/absolute/path/to/your-skill-name"
  }
}
```

Then make sure your event uses the same `skill_name`, for example:

```json
{
  "event_type": "skill_failure",
  "skill_name": "your-skill-name",
  "trace_id": "trace-001",
  "task_summary": "Summarize a failed workflow run",
  "error_summary": "Output omitted a required comparison section",
  "evidence": [
    "expected current-vs-previous comparison",
    "final answer skipped one requested section"
  ],
  "ts": "2026-04-03T00:00:00+08:00",
  "host_framework": "openclaw-like"
}
```

### Path resolution precedence

Parent skill resolution is intentionally conservative. The consumer checks, in order:

1. event-level path fields:
   - `skill_path`
   - `source_skill_path`
   - `parent_skill_path`
2. runtime `config.json` mappings
3. simple fallback guesses based on `skills_root` and local runtime neighbors

This means you can override the runtime config per event when needed.

---

## Runtime layout

A typical runtime tree looks like this:

```text
.skill-evolution/
├── inbox/
│   ├── hook-events.jsonl
│   └── hook-events.processed.jsonl
├── transactions/
├── reports/
├── candidates/
├── lineage/
├── examples/
└── config.json
```

### Output artifacts

For each processed event, the prototype can emit:

- `reports/<txn>.event.json`
- `reports/<txn>.report.json`
- `transactions/<txn>.json`
- `candidates/<cand>/candidate.json`
- `candidates/<cand>/VALIDATION.json`
- `candidates/<cand>/PROMOTION_REVIEW.json`
- `candidates/<cand>/DIFF.md`
- `lineage/<skill>.json`

---

## Script-by-script usage examples

### Initialize a runtime

```bash
python scripts/init_runtime_demo.py /tmp/skill-evolution-demo
```

### Consume events

```bash
python scripts/consume_hook_events.py /tmp/skill-evolution-demo
```

### Generate an evolution report

```bash
python scripts/emit_evolution_report.py event.json report.json
```

### Attribute recommended action

```bash
python scripts/attribute_candidate.py report.json
```

### Create a candidate stub

```bash
python scripts/create_candidate_stub.py /tmp/candidates table-analysis-pro patch
```

### Validate a candidate

```bash
python scripts/validate_candidate.py /path/to/candidate_dir
```

### Generate a promotion recommendation

```bash
python scripts/promote_candidate.py /path/to/candidate_dir
python scripts/generate_promotion_review.py /path/to/candidate_dir
```

### Write lineage

```bash
python scripts/write_lineage_record.py /tmp/lineage table-analysis-pro /path/to/candidate.json
```

---

## Example event shapes

### `skill_failure`

```json
{
  "event_type": "skill_failure",
  "skill_name": "table-analysis-pro",
  "trace_id": "trace-demo-001",
  "task_summary": "Analyze sales table and produce metric summary",
  "error_summary": "Output missing comparison section and incomplete metric explanation",
  "evidence": [
    "Expected a comparison section between current and previous period",
    "Metric definition explanation was incomplete"
  ],
  "ts": "2026-03-26T14:40:00+08:00",
  "host_framework": "openclaw-like"
}
```

### `user_correction`

```json
{
  "event_type": "user_correction",
  "skill_name": "table-analysis-pro",
  "trace_id": "trace-demo-002",
  "task_summary": "Review table analysis output",
  "user_correction": "The skill should explicitly compare current period vs previous period before giving conclusions.",
  "evidence": [
    "User asked for more explicit before/after comparison"
  ],
  "ts": "2026-03-26T14:41:00+08:00",
  "host_framework": "openclaw-like"
}
```

### `repeated_success_pattern`

```json
{
  "event_type": "repeated_success_pattern",
  "workflow_summary": "Read table schema -> define metrics -> compare periods -> summarize risks",
  "participating_skills": ["table-analysis-pro"],
  "trace_ids": ["trace-demo-003", "trace-demo-004", "trace-demo-005"],
  "success_count_window": 3,
  "ts": "2026-03-26T14:42:00+08:00",
  "host_framework": "openclaw-like"
}
```

---

## Testing

Run the current test suite:

```bash
python -m unittest discover -s tests -v
```

Current coverage includes:

- report generation happy path
- invalid candidate type rejection
- user-correction attribution to `patch`
- stub candidate validation failure
- candidate metadata preservation
- promotion failure when validation artifacts are missing
- end-to-end demo pipeline
- skipping invalid JSONL / non-object inbox lines
- unresolved parent-skill path behavior
- schema rejection for invalid candidate payloads

The test suite is still compact, but it now covers both happy paths and several important abnormal paths.

---

## Known limitations

This version intentionally does **not** yet provide:

- high-quality autonomous candidate content generation
- true offline task-level regression evaluation
- automatic promotion into a production skill registry
- online canary / shadow evaluation
- strong candidate-vs-parent semantic scoring
- production-grade observability and alerting
- repo split between scaffold, sample artifacts, and promotion workflow

So: treat this as a conservative prototype, not a self-improving production platform.

---

## Roadmap and progress

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for:

- completed milestones
- the current phase focus
- next planned improvements
- what we intentionally postponed

Short version:

1. improve README / usage examples
2. expand tests, especially end-to-end and abnormal paths
3. harden schema enforcement in the runtime flow
4. strengthen candidate-vs-parent evaluation
5. split scaffold / sample artifacts / promotion workflow later

---

## Recommended reading order

If you are new to the project:

1. `README.md`
2. `SKILL.md`
3. `docs/ROADMAP.md`
4. `references/design-v0.1.md`
5. `references/passive-evolution-flow.md`
6. `references/state-model.md`
7. `references/runnable-prototype-v0.1.md`

If you are implementing the next engineering layer, continue with:

- `references/mvp-file-structure-v0.1.md`
- `references/evaluation-policy-v0.1.md`
- `references/rollback-policy-v0.1.md`

---

## Philosophy in one sentence

Do not rush to build a self-evolving empire. First make the tractor run without dropping a wheel.
