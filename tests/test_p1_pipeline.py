from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class PipelineP1Tests(unittest.TestCase):
    def run_script(self, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
        script_path = SCRIPTS_DIR / script_name
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

    def create_parent_skill(self, root: Path, name: str = "table-analysis-pro") -> Path:
        parent = root / name
        (parent / "references").mkdir(parents=True, exist_ok=True)
        (parent / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            "description: Analyze tables conservatively and explain metrics clearly\n"
            "---\n\n"
            "# Table Analysis Pro\n\n"
            "## Core rules\n"
            "- Read schema before analysis.\n"
            "- Define metrics before computing them.\n"
            "- Compare current and previous periods when requested.\n\n"
            "### 5. Validate before concluding\n"
            "- Check completeness before returning.\n\n"
            "## Gotchas\n"
            "- Be explicit about assumptions.\n",
            encoding="utf-8",
        )
        (parent / "references" / "notes.md").write_text("Parent skill helper notes\n", encoding="utf-8")
        return parent

    def repoint_runtime_to_parent(self, runtime_dir: Path, parent_skill_dir: Path) -> None:
        config_path = runtime_dir / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["skills_root"] = str(parent_skill_dir.parent)
        config["parent_skill_paths"] = {"table-analysis-pro": str(parent_skill_dir)}
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

        inbox_events: list[dict] = []
        inbox_path = runtime_dir / "inbox" / "hook-events.jsonl"
        for line in inbox_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            event["skill_path"] = str(parent_skill_dir)
            inbox_events.append(event)
        inbox_path.write_text(
            "\n".join(json.dumps(event, ensure_ascii=False) for event in inbox_events) + "\n",
            encoding="utf-8",
        )

        for example_path in (runtime_dir / "examples").glob("*.json"):
            event = json.loads(example_path.read_text(encoding="utf-8"))
            event["skill_path"] = str(parent_skill_dir)
            example_path.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_consume_hook_events_end_to_end_demo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runtime_dir = tmp_path / "runtime"
            parent_skill_dir = self.create_parent_skill(tmp_path)

            init_result = self.run_script("init_runtime_demo.py", str(runtime_dir))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            self.repoint_runtime_to_parent(runtime_dir, parent_skill_dir)

            consume_result = self.run_script("consume_hook_events.py", str(runtime_dir))
            self.assertEqual(consume_result.returncode, 0, consume_result.stderr)
            self.assertIn("Processed 3 event(s)", consume_result.stdout)

            processed_path = runtime_dir / "inbox" / "hook-events.processed.jsonl"
            self.assertTrue(processed_path.exists())
            self.assertEqual(len(processed_path.read_text(encoding="utf-8").splitlines()), 3)

            txns = sorted((runtime_dir / "transactions").glob("*.json"))
            self.assertEqual(len(txns), 3)
            for txn_path in txns:
                txn = json.loads(txn_path.read_text(encoding="utf-8"))
                self.assertIn(txn["status"], {"review_required", "rejected", "finalized"})
                self.assertIn("transaction_id", txn)

            candidates = sorted((runtime_dir / "candidates").glob("*/candidate.json"))
            self.assertEqual(len(candidates), 3)
            seen_trigger_types = set()
            for candidate_path in candidates:
                candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
                self.assertIn(candidate["candidate_type"], {"patch", "replacement", "composition"})
                self.assertIn(candidate["promotion_status"], {"draft", "experimental", "stable", "deprecated", "archived"})
                self.assertEqual(candidate["skill_name"], "table-analysis-pro")
                self.assertEqual(candidate["parent_skill_id"], "table-analysis-pro")
                self.assertIn(candidate["trigger_type"], {"skill_failure", "user_correction", "repeated_success_pattern"})
                self.assertTrue(candidate["derived_from_report_id"].startswith("report-"))
                self.assertEqual(candidate["parent_skill_path"], str(parent_skill_dir))
                seen_trigger_types.add(candidate["trigger_type"])

            self.assertEqual(seen_trigger_types, {"skill_failure", "user_correction", "repeated_success_pattern"})

    def test_schema_validation_rejects_bad_candidate_type_written_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            init_result = self.run_script("init_runtime_demo.py", str(runtime_dir))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            report_path = runtime_dir / "examples" / "skill_failure.json"
            generated_report_path = runtime_dir / "bad.report.json"
            emit_result = self.run_script("emit_evolution_report.py", str(report_path), str(generated_report_path))
            self.assertEqual(emit_result.returncode, 0, emit_result.stderr)

            candidates_dir = runtime_dir / "candidates"
            bad_create = self.run_script("create_candidate_stub.py", str(candidates_dir), "table-analysis-pro", "patch")
            self.assertEqual(bad_create.returncode, 0, bad_create.stderr)
            candidate_dir = Path(bad_create.stdout.strip())

            candidate_json_path = candidate_dir / "candidate.json"
            candidate = json.loads(candidate_json_path.read_text(encoding="utf-8"))
            candidate["candidate_type"] = "banana"
            candidate_json_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")

            validate_result = self.run_script("promote_candidate.py", str(candidate_dir))
            self.assertNotEqual(validate_result.returncode, 0)
            self.assertIn("Schema validation failed", validate_result.stderr)

    def test_consume_hook_events_skips_invalid_jsonl_and_non_object_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            init_result = self.run_script("init_runtime_demo.py", str(runtime_dir))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            inbox_path = runtime_dir / "inbox" / "hook-events.jsonl"
            inbox_path.write_text(
                "{bad json}\n"
                "123\n"
                + json.dumps({
                    "event_type": "skill_failure",
                    "skill_name": "table-analysis-pro",
                    "trace_id": "trace-valid-001",
                    "task_summary": "Analyze sales table",
                    "error_summary": "Missing comparison section",
                    "evidence": ["comparison section missing"],
                    "ts": "2026-04-03T00:00:00+08:00",
                    "host_framework": "openclaw-like",
                    "parent_skill_path": "/definitely/missing/table-analysis-pro"
                }, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )

            consume_result = self.run_script("consume_hook_events.py", str(runtime_dir))
            self.assertEqual(consume_result.returncode, 0, consume_result.stderr)
            self.assertIn("Processed 1 event(s)", consume_result.stdout)

            processed_path = runtime_dir / "inbox" / "hook-events.processed.jsonl"
            self.assertTrue(processed_path.exists())
            self.assertEqual(len(processed_path.read_text(encoding="utf-8").splitlines()), 1)

            txns = sorted((runtime_dir / "transactions").glob("*.json"))
            self.assertEqual(len(txns), 1)
            txn = json.loads(txns[0].read_text(encoding="utf-8"))
            self.assertEqual(txn["status"], "rejected")
            self.assertEqual(txn["recommended_action"], "patch")
            self.assertEqual(txn["decision_summary"], "Failed candidate validation")

            candidates = sorted((runtime_dir / "candidates").glob("*/candidate.json"))
            self.assertEqual(len(candidates), 1)
            candidate = json.loads(candidates[0].read_text(encoding="utf-8"))
            self.assertEqual(candidate["promotion_status"], "draft")
            self.assertEqual(candidate["parent_skill_id"], "table-analysis-pro")
            self.assertIn("/definitely/missing/table-analysis-pro", candidate["skill_resolution_checked_paths"])
            self.assertNotIn("parent_skill_path", candidate)

            validation = json.loads((candidates[0].parent / "VALIDATION.json").read_text(encoding="utf-8"))
            self.assertFalse(validation["passed"])
            self.assertIn("skill_name_stub_or_missing", validation["failed_checks"])


if __name__ == "__main__":
    unittest.main()
