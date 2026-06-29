import json
import threading
import unittest
import urllib.request

from gemma_hack import server
from gemma_hack.defender import (
    DATASHIELD_DEMO_SIGNALS,
    DATASHIELD_TELEMETRY_SOURCES,
    DEFENDER_ROLES,
    build_defender_prompt,
    draft_enterprise_defense_plan,
    get_datashield_product_brief,
    load_blue_team_scenario,
)
from gemma_hack.server import INDEX_HTML


class BlueTeamDefenderTests(unittest.TestCase):
    def test_datashield_product_brief_matches_user_pitch(self):
        brief = get_datashield_product_brief()
        self.assertEqual(brief["name"], "Gemma Aegis")
        self.assertIn("Always-on blue-team defender swarm", brief["tagline"])
        self.assertIn("Static virus detectors are too slow for modern data breaches", brief["core_pitch"])
        self.assertEqual(DATASHIELD_TELEMETRY_SOURCES, ["identity", "DLP", "endpoint", "SaaS", "storage"])
        self.assertEqual(
            [agent["name"] for agent in brief["agents"]],
            ["Data Sentinel", "Identity Guardian", "Endpoint Hunter", "Response Orchestrator"],
        )
        self.assertIn("finance admin impossible travel", DATASHIELD_DEMO_SIGNALS)
        self.assertIn("malicious OAuth grant", DATASHIELD_DEMO_SIGNALS)
        self.assertIn("S3 export spike", DATASHIELD_DEMO_SIGNALS)
        self.assertIn("DLP payroll/bank-account staging", DATASHIELD_DEMO_SIGNALS)
        self.assertIn("PowerShell download cradle", DATASHIELD_DEMO_SIGNALS)
        self.assertIn("lateral RDP with service account", DATASHIELD_DEMO_SIGNALS)

    def test_defender_roles_cover_enterprise_data_and_red_team_pressure(self):
        self.assertIn("data_sentinel", DEFENDER_ROLES)
        self.assertIn("identity_guardian", DEFENDER_ROLES)
        self.assertIn("endpoint_hunter", DEFENDER_ROLES)
        self.assertIn("response_orchestrator", DEFENDER_ROLES)
        joined = " ".join(DEFENDER_ROLES.values()).lower()
        self.assertIn("enterprise data", joined)
        self.assertIn("red team", joined)

    def test_build_defender_prompt_wraps_telemetry_as_always_on_blue_team_agent(self):
        prompt = build_defender_prompt("data_sentinel", "S3 object export spike from finance bucket")
        self.assertIn("Product: Gemma Aegis", prompt)
        self.assertIn("Agent name: Data Sentinel", prompt)
        self.assertIn("Agent role: data_sentinel", prompt)
        self.assertIn("always-on blue team defender", prompt)
        self.assertIn("Enterprise telemetry", prompt)
        self.assertIn("S3 object export spike", prompt)
        self.assertIn("red team", prompt.lower())
        self.assertIn("Containment", prompt)
        identity_prompt = build_defender_prompt("identity_guardian", "malicious OAuth grant after impossible travel")
        self.assertIn("Agent name: Identity Guardian", identity_prompt)
        self.assertIn("OAuth", identity_prompt)

    def test_static_defense_plan_flags_data_exfiltration_and_identity_abuse(self):
        plan = draft_enterprise_defense_plan(
            "Impossible travel for finance admin, malicious OAuth grant, S3 export spike, "
            "DLP payroll and bank-account staging, EDR flags powershell download cradle, "
            "lateral RDP succeeds with service account svc-reporting."
        )
        self.assertEqual(plan["risk_level"], "critical")
        self.assertIn("data_exfiltration", plan["signals"])
        self.assertIn("identity_abuse", plan["signals"])
        self.assertIn("endpoint_execution", plan["signals"])
        self.assertIn("lateral_movement", plan["signals"])
        self.assertIn("payroll/bank-account data", plan["data_at_risk"])
        self.assertEqual(plan["telemetry_sources"], DATASHIELD_TELEMETRY_SOURCES)
        self.assertIn("finance admin impossible travel", plan["kill_chain"])
        self.assertIn("malicious OAuth grant", plan["kill_chain"])
        self.assertTrue(any("quarantine" in action.lower() for action in plan["containment_actions"]))
        self.assertTrue(any("revoke" in action.lower() for action in plan["containment_actions"]))
        self.assertIn("before breach", plan["executive_brief"].lower())
        self.assertIn("enterprise data", plan["business_impact"].lower())

    def test_blue_team_scenario_loader_and_ui_are_present(self):
        self.assertIn("Gemma Aegis", INDEX_HTML)
        self.assertIn("Static virus detectors are too slow for modern data breaches", INDEX_HTML)
        self.assertIn("Data Sentinel", INDEX_HTML)
        self.assertIn("Identity Guardian", INDEX_HTML)
        self.assertIn("Endpoint Hunter", INDEX_HTML)
        self.assertIn("Response Orchestrator", INDEX_HTML)
        self.assertIn('id="loadBlueTeamScenario"', INDEX_HTML)
        self.assertIn("/api/blue-team-scenario", INDEX_HTML)
        self.assertIn("/api/datashield-brief", INDEX_HTML)
        self.assertIn('<option value="defender">Aegis defender swarm</option>', INDEX_HTML)
        self.assertIn("Run Aegis swarm", INDEX_HTML)
        scenario = load_blue_team_scenario()
        self.assertIn("Gemma Aegis", scenario)
        self.assertIn("finance admin impossible travel", scenario.lower())
        self.assertIn("malicious oauth grant", scenario.lower())
        self.assertIn("s3 export spike", scenario.lower())
        self.assertIn("dlp payroll/bank-account staging", scenario.lower())
        self.assertIn("powershell download cradle", scenario.lower())
        self.assertIn("lateral rdp with service account", scenario.lower())
        self.assertNotIn("```", scenario)

    def test_blue_team_scenario_endpoint_serves_enterprise_telemetry(self):
        httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            scenario_url = f"http://127.0.0.1:{httpd.server_address[1]}/api/blue-team-scenario"
            brief_url = f"http://127.0.0.1:{httpd.server_address[1]}/api/datashield-brief"
            with urllib.request.urlopen(scenario_url, timeout=5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            with urllib.request.urlopen(brief_url, timeout=5) as resp:
                brief = json.loads(resp.read().decode("utf-8"))
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
            httpd.server_close()
        self.assertIn("Gemma Aegis", payload["scenario"])
        self.assertIn("data exfiltration", payload["scenario"].lower())
        self.assertEqual(brief["name"], "Gemma Aegis")
        self.assertEqual(len(brief["agents"]), 4)
        self.assertIn("S3 export spike", brief["demo_signals"])


if __name__ == "__main__":
    unittest.main()

