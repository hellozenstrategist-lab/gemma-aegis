import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gemma_hack.summary import format_submission_benchmark_summary, load_jsonl_records


class BenchmarkSummaryTests(unittest.TestCase):
    def test_format_submission_benchmark_summary_counts_only_gemma_as_product_evidence(self):
        fake_cerebras_key = "csk" + "-abc123shouldnotleak"
        records = [
            {
                "timestamp_utc": "2026-06-27T03:43:00+00:00",
                "model": "gpt-oss-120b",
                "eval_packet": {
                    "agent_count": 2,
                    "total_wall_ms": 728.0,
                    "total_tokens": 986,
                    "errors": [],
                    "combined_brief": "fallback SDK health-check output",
                    "agents": [
                        {"provider": "cerebras:triage", "model": "gpt-oss-120b"},
                        {"provider": "cerebras:remediation", "model": "gpt-oss-120b"},
                    ],
                },
            },
            {
                "timestamp_utc": "2026-06-27T03:43:30+00:00",
                "model": "gemma-4-31b",
                "eval_packet": {
                    "agent_count": 4,
                    "total_wall_ms": 815.4,
                    "total_tokens": 1234,
                    "errors": [],
                    "combined_brief": "Gemma visible incident-command output",
                    "agents": [
                        {"provider": "cerebras:triage", "model": "gemma-4-31b"},
                        {"provider": "cerebras:blast_radius", "model": "gemma-4-31b"},
                        {"provider": "cerebras:remediation", "model": "gemma-4-31b"},
                        {"provider": "cerebras:evidence", "model": "gemma-4-31b"},
                    ],
                },
            },
            {
                "timestamp_utc": "2026-06-27T03:44:00+00:00",
                "model": "gemma-4-31b",
                "eval_packet": {
                    "agent_count": 2,
                    "total_wall_ms": 652.9,
                    "total_tokens": 1041,
                    "errors": [],
                    "combined_brief": "",
                    "agents": [
                        {"provider": "cerebras:triage", "model": "gemma-4-31b", "output": ""},
                        {"provider": "cerebras:remediation", "model": "gemma-4-31b", "output": ""},
                    ],
                },
            },
            {
                "timestamp_utc": "2026-06-27T03:45:00+00:00",
                "mode": "single",
                "cerebras": {
                    "model": "gpt-oss-120b",
                    "metrics": {"wall_ms": 201.395, "total_tokens": 168},
                    "output": "OK",
                    "error": None,
                },
                "prompt_preview": f"secret {fake_cerebras_key}",
            },
            {
                "timestamp_utc": "2026-06-27T03:46:00+00:00",
                "model": "gemma-4-31b",
                "eval_packet": {
                    "agent_count": 2,
                    "total_wall_ms": 0,
                    "total_tokens": 0,
                    "errors": ["preview not enabled"],
                    "combined_brief": "",
                },
            },
        ]

        summary = format_submission_benchmark_summary(records, limit=2)

        self.assertIn("Product model: gemma-4-31b", summary)
        self.assertIn("Successful Gemma 4 product runs: 1/3", summary)
        self.assertIn("Non-Gemma successful SDK/key health checks: 2 (not submission evidence)", summary)
        self.assertIn("Fastest Gemma 4: gemma-4-31b council (4 agents) in 815.4 ms wall for 1,234 tokens", summary)
        self.assertIn("Submission line:", summary)
        self.assertNotIn("Fastest: gpt-oss-120b", summary)
        self.assertNotIn("201.4 ms", summary)
        self.assertNotIn("652.9 ms", summary)
        self.assertNotIn("csk" + "-", summary)

    def test_load_jsonl_records_skips_blank_and_malformed_lines(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "benchmarks.jsonl"
            path.write_text(
                '{"ok": true, "model": "gpt-oss-120b"}\n'
                '\n'
                'not json\n'
                '{"ok": true, "model": "gemma-4-31b"}\n',
                encoding="utf-8",
            )

            records = load_jsonl_records(path)

        self.assertEqual([record["model"] for record in records], ["gpt-oss-120b", "gemma-4-31b"])

    def test_benchmark_summary_cli_prints_submission_copy(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "eval_demo.jsonl"
            path.write_text(
                '{"timestamp_utc":"2026-06-27T03:43:00+00:00","model":"gemma-4-31b",'
                '"eval_packet":{"agent_count":2,"total_wall_ms":728.0,"total_tokens":986,"errors":[],"combined_brief":"safe",'
                '"agents":[]}}\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "benchmark_summary.py"), str(path), "--limit", "1"],
                cwd=root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Benchmark summary for submission:", result.stdout)
        self.assertIn("Successful Gemma 4 product runs: 1/1", result.stdout)
        self.assertIn("gemma-4-31b council (2 agents)", result.stdout)


if __name__ == "__main__":
    unittest.main()

