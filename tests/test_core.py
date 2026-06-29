import base64
import json
import os
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

from gemma_hack import server
from gemma_hack.agents import AGENT_ROLES, build_agent_prompt, summarize_agent_results
from gemma_hack.metrics import append_benchmark_record, extract_metrics, redact_secrets
from gemma_hack.provider import ProviderResult, _friendly_cerebras_error, build_messages, load_project_env
from gemma_hack.server import INDEX_HTML
from scripts import smoke


class AgentCouncilTests(unittest.TestCase):
    def test_agent_roles_cover_hackathon_judging_needs(self):
        self.assertIn("triage", AGENT_ROLES)
        self.assertIn("blast_radius", AGENT_ROLES)
        self.assertIn("remediation", AGENT_ROLES)
        self.assertIn("evidence", AGENT_ROLES)
        self.assertIn("security", " ".join(AGENT_ROLES["triage"].lower().split()))

    def test_build_agent_prompt_wraps_scenario_with_role_and_output_contract(self):
        prompt = build_agent_prompt("triage", "OAuth callback errors")
        self.assertIn("OAuth callback errors", prompt)
        self.assertIn("Agent role: triage", prompt)
        self.assertIn("Return exactly", prompt)
        self.assertIn("Demo soundbite", prompt)

    def test_summarize_agent_results_collects_outputs_and_metrics(self):
        results = [
            ProviderResult("cerebras", "gpt-oss-120b", "Triage says high", {"wall_ms": 100.0, "total_tokens": 20}),
            ProviderResult("cerebras", "gpt-oss-120b", "Remediate rollback", {"wall_ms": 150.0, "total_tokens": 30}),
        ]
        summary = summarize_agent_results(results)
        self.assertEqual(summary["agent_count"], 2)
        self.assertEqual(summary["total_wall_ms"], 250.0)
        self.assertEqual(summary["total_tokens"], 50)
        self.assertIn("Triage says high", summary["combined_brief"])

    def test_summarize_agent_results_rejects_empty_visible_agent_output(self):
        results = [
            ProviderResult("cerebras:triage", "gemma-4-31b", "   ", {"wall_ms": 12.0, "total_tokens": 42}),
        ]

        summary = summarize_agent_results(results)

        self.assertEqual(summary["combined_brief"], "")
        self.assertEqual(summary["errors"], ["Empty visible output from cerebras:triage/gemma-4-31b; not valid council evidence"])


class ProviderMessageTests(unittest.TestCase):
    def test_build_messages_text_only_uses_plain_user_content(self):
        messages = build_messages("triage this incident")
        self.assertEqual(messages, [{"role": "user", "content": "triage this incident"}])

    def test_build_messages_with_image_url_uses_openai_multimodal_shape(self):
        messages = build_messages("what is in this screenshot?", image_url="https://example.com/shot.png")
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"][0], {"type": "text", "text": "what is in this screenshot?"})
        self.assertEqual(
            messages[0]["content"][1],
            {"type": "image_url", "image_url": {"url": "https://example.com/shot.png"}},
        )

    def test_build_messages_rejects_two_image_sources(self):
        with self.assertRaises(ValueError):
            build_messages("bad", image_url="https://example.com/a.png", image_data_uri="data:image/png;base64,abc")

    def test_load_project_env_reads_dotenv_without_overriding_existing_env(self):
        with tempfile.TemporaryDirectory() as td:
            fake_cerebras_key = "csk" + "-demo-key"
            env_path = Path(td) / ".env"
            env_path.write_text(
                f"\ufeffCEREBRAS_API_KEY={fake_cerebras_key}\n"
                "EXISTING_VALUE=from-file\n"
                "QUOTED_VALUE='quoted text'\n",
                encoding="utf-8",
            )
            os.environ["EXISTING_VALUE"] = "already-set"
            os.environ.pop("CEREBRAS_API_KEY", None)
            try:
                loaded = load_project_env(env_path)
                self.assertEqual(os.environ["CEREBRAS_API_KEY"], fake_cerebras_key)
                self.assertEqual(os.environ["EXISTING_VALUE"], "already-set")
                self.assertEqual(os.environ["QUOTED_VALUE"], "quoted text")
                self.assertEqual(loaded["CEREBRAS_API_KEY"], "[REDACTED_CEREBRAS_KEY]")
            finally:
                for key in ("CEREBRAS_API_KEY", "EXISTING_VALUE", "QUOTED_VALUE"):
                    os.environ.pop(key, None)

    def test_friendly_cerebras_error_labels_model_access_instead_of_key_failure(self):
        err = Exception("Error code: 404 - {'code': 'model_not_found', 'message': 'Model gemma-4-31b does not exist or you do not have access to it.'}")
        self.assertIn("Gemma model access failed", _friendly_cerebras_error(err))

    def test_friendly_cerebras_error_labels_billing_required(self):
        err = Exception("Error code: 402 - {'code': 'payment_required', 'message': 'Payment required to access this resource.'}")
        self.assertIn("Cerebras billing required", _friendly_cerebras_error(err))


class MetricsTests(unittest.TestCase):
    def test_extract_metrics_reads_usage_and_time_info_from_object_response(self):
        completion = SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=22, total_tokens=33),
            time_info=SimpleNamespace(
                queue_time=0.01,
                prompt_time=0.02,
                completion_time=0.03,
                total_time=0.06,
                time_to_first_token=0.025,
                tokens_per_second=733.3,
            ),
        )
        metrics = extract_metrics(completion, wall_ms=71.2)
        self.assertEqual(metrics["prompt_tokens"], 11)
        self.assertEqual(metrics["completion_tokens"], 22)
        self.assertEqual(metrics["total_tokens"], 33)
        self.assertEqual(metrics["wall_ms"], 71.2)
        self.assertEqual(metrics["time_info"]["total_time"], 0.06)
        self.assertEqual(metrics["time_info"]["tokens_per_second"], 733.3)

    def test_append_benchmark_record_writes_jsonl_without_secret_leak(self):
        with tempfile.TemporaryDirectory() as td:
            fake_cerebras_key = "csk" + "-demo-key"
            path = Path(td) / "bench.jsonl"
            append_benchmark_record(
                path,
                {
                    "provider": "cerebras",
                    "api_key": fake_cerebras_key,
                    "output": "safe",
                },
            )
            row = json.loads(path.read_text().strip())
            self.assertEqual(row["provider"], "cerebras")
            self.assertEqual(row["api_key"], "[REDACTED_CEREBRAS_KEY]")
            self.assertEqual(row["output"], "safe")
            self.assertIn("timestamp_utc", row)

    def test_redact_secrets_handles_cerebras_keys_inside_nested_text(self):
        text = "Authorization: Bearer " + "csk" + "-demo-key"
        self.assertNotIn("csk" + "-", redact_secrets(text))
        self.assertIn("[REDACTED_CEREBRAS_KEY]", redact_secrets(text))


class SmokeCliTests(unittest.TestCase):
    def test_run_smoke_rejects_empty_visible_output_as_failed_product_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "smoke.jsonl"
            printed: list[str] = []

            def fake_call(prompt, *, reasoning_effort, model):
                self.assertEqual(prompt, "Reply with exactly OK")
                self.assertEqual(reasoning_effort, "none")
                self.assertEqual(model, "gemma-4-31b")
                return ProviderResult("cerebras", "gemma-4-31b", "   ", {"wall_ms": 12.3}, None)

            rc = smoke.run_smoke(
                "Reply with exactly OK",
                reasoning="none",
                model="gemma-4-31b",
                log_path=log_path,
                call_provider=fake_call,
                emit=printed.append,
            )

            self.assertEqual(rc, 3)
            self.assertTrue(any("empty visible output" in line.lower() for line in printed))
            row = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(row["model"], "gemma-4-31b")
            self.assertIn("empty visible output", row["error"].lower())


class ServerUiTests(unittest.TestCase):
    def test_index_html_warns_non_gemma_runs_are_health_checks_only(self):
        self.assertIn('id="contestPrimaryBanner"', INDEX_HTML)
        self.assertIn("gemma-4-31b is the only product evidence", INDEX_HTML)
        self.assertIn("Non-Gemma runs are SDK/key health checks only", INDEX_HTML)
        self.assertIn("BLOCKED_ON_GEMMA_ACCESS", INDEX_HTML)
        self.assertIn("updateModelModeBanner", INDEX_HTML)

    def test_index_html_has_one_click_curated_demo_scenario_loader(self):
        self.assertIn('id="loadScenario"', INDEX_HTML)
        self.assertIn("/api/demo-scenario", INDEX_HTML)
        self.assertTrue(hasattr(server, "load_demo_scenario"))
        scenario = server.load_demo_scenario()
        self.assertIn("Production auth incident", scenario)
        self.assertIn("Triage severity", scenario)
        self.assertNotIn("```", scenario)

    def test_index_html_shows_sixty_second_recording_checklist(self):
        self.assertIn('id="recordingChecklist"', INDEX_HTML)
        self.assertIn("60-second recording checklist", INDEX_HTML)
        self.assertIn("0-5s", INDEX_HTML)
        self.assertIn("5-20s", INDEX_HTML)
        self.assertIn("20-35s", INDEX_HTML)
        self.assertIn("35-50s", INDEX_HTML)
        self.assertIn("50-60s", INDEX_HTML)
        self.assertIn("demo video", INDEX_HTML)

    def test_index_html_has_one_click_sanitized_multimodal_asset_loader(self):
        self.assertIn('id="loadDemoImage"', INDEX_HTML)
        self.assertIn("/api/demo-image", INDEX_HTML)
        self.assertIn("sampleImageDataUri", INDEX_HTML)
        self.assertIn("sanitized demo screenshot", INDEX_HTML)
        payload = server.load_demo_image_payload()
        self.assertEqual(payload["mime_type"], "image/png")
        self.assertTrue(payload["image_data_uri"].startswith("data:image/png;base64,"))
        encoded = payload["image_data_uri"].split(",", 1)[1]
        decoded = base64.b64decode(encoded)
        self.assertTrue(decoded.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(decoded), 1000)

    def test_index_html_can_clear_attached_demo_image(self):
        self.assertIn('id="clearDemoImage"', INDEX_HTML)
        self.assertIn("clearDemoImageAttachment", INDEX_HTML)
        self.assertIn("sampleImageDataUri = null", INDEX_HTML)
        self.assertIn("preview.style.display = 'none'", INDEX_HTML)
        self.assertIn("$('imageFile').value = ''", INDEX_HTML)

    def test_classic_ui_is_editable_from_web_folder(self):
        classic_path = server.PROJECT_ROOT / "web" / "classic" / "index.html"
        self.assertTrue(classic_path.is_file())
        html = server.load_classic_index_html()
        self.assertIn("Aegis Input", html)
        self.assertIn('id="loadBlueTeamScenario"', html)
        self.assertEqual(server.INDEX_HTML, html)

    def test_v6_ui_routes_classic_slash_command_locally(self):
        html = server.load_v6_index_html()
        self.assertIn("/^\\/classic\\/?$/.test(low)", html)
        self.assertIn("window.location.href = '/classic'", html)

    def test_index_html_surfaces_top_level_api_errors(self):
        self.assertIn("if (!res.ok || data.error)", INDEX_HTML)
        self.assertIn("data.error || `HTTP ${res.status}`", INDEX_HTML)
        self.assertIn("request error", INDEX_HTML)

    def test_index_html_javascript_is_syntax_valid(self):
        marker_start = "<script>"
        marker_end = "</script>"
        script = INDEX_HTML.split(marker_start, 1)[1].split(marker_end, 1)[0]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as js_file:
            js_file.write(script)
            js_path = js_file.name
        try:
            result = subprocess.run(["node", "--check", js_path], capture_output=True, text=True, timeout=10)
        finally:
            Path(js_path).unlink(missing_ok=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_v6_ui_is_wired_to_server_side_datashield_backend(self):
        html = server.load_v6_index_html()
        self.assertIn("Gemma Aegis", html)
        self.assertIn("/v6/support.js", html)
        self.assertIn("/v6/assets/aegis-core.png", html)
        self.assertIn("/api/datashield-chat", html)
        self.assertIn("/api/datashield-state", html)
        self.assertNotIn("https://api.cerebras.ai", html)
        self.assertNotIn("localStorage.cerebras_key", html)

    def test_datashield_state_endpoint_exposes_real_product_pages(self):
        state = server.build_datashield_state()
        self.assertEqual(state["product"]["name"], "Gemma Aegis")
        self.assertEqual(len(state["agents"]), 4)
        self.assertIn("swarm", state["pages"])
        self.assertIn("containment", state["pages"])
        self.assertIn("evidence", state["pages"])
        self.assertIn("critical", state["pages"]["brief"]["sub"].lower())
        self.assertEqual(state["meta"]["swarm"]["stats"][0][0], "AGENTS")
        self.assertEqual(state["meta"]["swarm"]["stats"][0][1], "4")

    def test_datashield_chat_uses_backend_provider_and_preserves_nav_tokens(self):
        calls = []

        def fake_provider(prompt, **kwargs):
            calls.append({"prompt": prompt, "kwargs": kwargs})
            return ProviderResult("fake", "gemma-4-31b", "Opening the vault. [[NAV:evidence]]", {"wall_ms": 12.0, "total_tokens": 9})

        result = server.run_datashield_chat("open evidence vault", call_provider=fake_provider)
        self.assertEqual(result["reply"], "Opening the vault. [[NAV:evidence]]")
        self.assertEqual(result["metrics"]["wall_ms"], 12.0)
        self.assertEqual(calls[0]["kwargs"]["model"], "gemma-4-31b")
        self.assertIn("server-side", calls[0]["prompt"])
        self.assertNotIn("csk-", json.dumps(result))

    def test_v6_static_routes_serve_ui_runtime_and_assets(self):
        httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{httpd.server_address[1]}"
            with urllib.request.urlopen(base + "/", timeout=5) as resp:
                html = resp.read().decode("utf-8")
            with urllib.request.urlopen(base + "/v6/support.js", timeout=5) as resp:
                support_prefix = resp.read(80).decode("utf-8", "replace")
                support_type = resp.headers.get("Content-Type")
            with urllib.request.urlopen(base + "/v6/assets/aegis-core.png", timeout=5) as resp:
                png_prefix = resp.read(8)
                png_type = resp.headers.get("Content-Type")
            with urllib.request.urlopen(base + "/api/datashield-state", timeout=5) as resp:
                state = json.loads(resp.read().decode("utf-8"))
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
            httpd.server_close()
        self.assertIn("Gemma Aegis", html)
        self.assertIn("GENERATED from dc-runtime", support_prefix)
        self.assertIn("javascript", support_type)
        self.assertEqual(png_prefix, b"\x89PNG\r\n\x1a\n")
        self.assertEqual(png_type, "image/png")
        self.assertEqual(state["product"]["name"], "Gemma Aegis")

    def test_demo_image_endpoint_serves_sanitized_data_uri(self):
        httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{httpd.server_address[1]}/api/demo-image"
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                self.fail(f"/api/demo-image should return 200, got HTTP {exc.code}")
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
            httpd.server_close()
        self.assertEqual(payload["mime_type"], "image/png")
        self.assertTrue(payload["image_data_uri"].startswith("data:image/png;base64,"))
        self.assertIn("sanitized demo screenshot", payload["alt_text"])


if __name__ == "__main__":
    unittest.main()

